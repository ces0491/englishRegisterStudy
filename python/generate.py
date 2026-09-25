"""Study 2's generation run, on Modal.

Four conditions, as registered at https://osf.io/qjgtc and specified in
docs/generation-protocol.md: Olmo 3 7B base and Instruct, each at unmodified
sampling (temperature 1.0, top-p 1.0) and at deployment settings (0.7, 0.9).
Every condition generates on the same 4,000 topics from data/topics.csv until
its text reaches two million words.

Everything that could make a run unreproducible is recorded with the text: the
checkpoint's resolved commit, the seed of each generation, the sampling
settings, and the versions of the libraries that produced it.

Usage:
  modal run python/generate.py                      # all four conditions
  modal run python/generate.py --condition base-1.0 # one of them
  modal volume get englishregisterstudy /generated ./data/generated

The pure functions below carry no Modal dependency so that
python/test_generate.py can check them without a GPU.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

WORD_TARGET = 2_000_000
MAX_NEW_TOKENS = 1024
PROMPT_TEMPLATE = "Write a blog post titled: {topic}"
BASE_MODEL = "allenai/Olmo-3-1025-7B"
INSTRUCT_MODEL = "allenai/Olmo-3-7B-Instruct"

# A run may need more than one pass over the topics to reach the word target.
# The registration fixes the order: topics are reused in topic_id order with
# the seed advanced, never reshuffled.
MAX_PASSES = 4


@dataclass(frozen=True)
class Condition:
    name: str
    model: str
    instruct: bool
    temperature: float
    top_p: float


CONDITIONS = (
    Condition("base-1.0", BASE_MODEL, False, 1.0, 1.0),
    Condition("base-0.7", BASE_MODEL, False, 0.7, 0.9),
    Condition("instruct-1.0", INSTRUCT_MODEL, True, 1.0, 1.0),
    Condition("instruct-0.7", INSTRUCT_MODEL, True, 0.7, 0.9),
)

CONFIRMATORY = "base-1.0"


def load_topics(path: str | Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_prompt(topic: str) -> str:
    """The prompt, identical across conditions.

    It names no variety, no register and no style: asking for "British English"
    or "a punchy blog post" would measure instruction-following rather than
    default register.
    """
    return PROMPT_TEMPLATE.format(topic=topic)


def seed_for(condition: str, topic_id: str, pass_number: int) -> int:
    """A generation's seed, fixed by what it is rather than by when it ran.

    Deterministic and independent of ordering, so a rerun of one condition, or
    of one topic within it, reproduces the same text.
    """
    digest = 0
    for piece in (condition, topic_id, str(pass_number)):
        for char in piece:
            digest = (digest * 131 + ord(char)) % (2**31 - 1)
    return digest


@dataclass
class Generation:
    condition: str
    topic_id: str
    pass_number: int
    seed: int
    prompt: str
    text: str
    finish_reason: str
    model: str
    revision: str
    temperature: float
    top_p: float
    max_new_tokens: int


def words_so_far(records: list[Generation], word_count, tokenise) -> int:
    """Total words generated, counted the way Study 2 counts them.

    Both functions come from framecount, so the stopping rule uses the same
    definition of a word as the analysis does.
    """
    return sum(word_count(tokenise(record.text)) for record in records)


# --- Modal ------------------------------------------------------------------
#
# Imported lazily so the functions above can be tested without Modal, and so
# the heavy libraries live only in the remote image.

try:
    import modal
except ImportError:  # pragma: no cover - local testing without Modal
    modal = None

if modal is not None:
    REPO = Path(__file__).resolve().parent.parent

    image = (
        modal.Image.debian_slim(python_version="3.11")
        .pip_install("vllm", "huggingface_hub", "transformers")
        .add_local_file(REPO / "python" / "framecount.py", "/root/framecount.py")
        .add_local_file(REPO / "data" / "topics.csv", "/root/topics.csv")
        .add_local_file(REPO / "data" / "frames.csv", "/root/frames.csv")
    )

    app = modal.App("englishregisterstudy-generate", image=image)
    volume = modal.Volume.from_name("englishregisterstudy", create_if_missing=True)
    OUT = Path("/data/generated")

    @app.function(gpu="A10G", timeout=60 * 60 * 6, volumes={"/data": volume})
    def generate_condition(condition_name: str) -> dict:
        """Generate one condition's text and write it to the volume."""
        import importlib.metadata as metadata

        from huggingface_hub import HfApi
        from vllm import LLM, SamplingParams

        import framecount

        condition = next(c for c in CONDITIONS if c.name == condition_name)
        topics = load_topics("/root/topics.csv")

        # Pin what actually ran: a Hugging Face repository can be updated in
        # place, so the tag alone does not identify the weights.
        revision = HfApi().model_info(condition.model).sha
        versions = {
            package: metadata.version(package)
            for package in ("vllm", "transformers", "huggingface_hub")
        }

        llm = LLM(model=condition.model, revision=revision, dtype="bfloat16",
                  seed=0)
        tokenizer = llm.get_tokenizer()

        records: list[Generation] = []
        for pass_number in range(1, MAX_PASSES + 1):
            if words_so_far(records, framecount.word_count,
                            framecount.tokenise) >= WORD_TARGET:
                break

            prompts, meta = [], []
            for topic in topics:
                prompt = build_prompt(topic["topic"])
                if condition.instruct:
                    prompt = tokenizer.apply_chat_template(
                        [{"role": "user", "content": prompt}],
                        tokenize=False, add_generation_prompt=True)
                prompts.append(prompt)
                meta.append((topic["topic_id"],
                             seed_for(condition.name, topic["topic_id"],
                                      pass_number)))

            outputs = llm.generate(
                prompts,
                [SamplingParams(temperature=condition.temperature,
                                top_p=condition.top_p,
                                max_tokens=MAX_NEW_TOKENS, seed=seed)
                 for _, seed in meta])

            for prompt, (topic_id, seed), output in zip(prompts, meta, outputs):
                completion = output.outputs[0]
                records.append(Generation(
                    condition=condition.name, topic_id=topic_id,
                    pass_number=pass_number, seed=seed, prompt=prompt,
                    text=completion.text,
                    finish_reason=completion.finish_reason or "",
                    model=condition.model, revision=revision,
                    temperature=condition.temperature, top_p=condition.top_p,
                    max_new_tokens=MAX_NEW_TOKENS))

        OUT.mkdir(parents=True, exist_ok=True)
        text_path = OUT / f"{condition.name}.jsonl"
        with open(text_path, "w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(asdict(record)) + "\n")

        manifest = {
            "condition": condition.name,
            "model": condition.model,
            "revision": revision,
            "temperature": condition.temperature,
            "top_p": condition.top_p,
            "max_new_tokens": MAX_NEW_TOKENS,
            "generations": len(records),
            "passes": records[-1].pass_number if records else 0,
            "words": words_so_far(records, framecount.word_count,
                                  framecount.tokenise),
            "word_target": WORD_TARGET,
            "topics": len(topics),
            "confirmatory": condition.name == CONFIRMATORY,
            "versions": versions,
        }
        with open(OUT / f"{condition.name}.manifest.json", "w",
                  encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)
        volume.commit()
        return manifest

    @app.local_entrypoint()
    def main(condition: str = "") -> None:
        names = [condition] if condition else [c.name for c in CONDITIONS]
        for name in names:
            manifest = generate_condition.remote(name)
            print(f"{name}: {manifest['generations']} generations, "
                  f"{manifest['words']:,} words over "
                  f"{manifest['passes']} pass(es)")
