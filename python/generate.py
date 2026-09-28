"""Study 2's generation run, on Modal.

Four conditions, as registered at https://osf.io/qjgtc and specified in
docs/generation-protocol.md: Olmo 3 7B base and Instruct, each at unmodified
sampling (temperature 1.0, top-p 1.0) and at deployment settings (0.7, 0.9).
Every condition generates once on each of the 4,000 topics in data/topics.csv,
and reuses topics only if that falls short of two million words.

Everything that could make a run unreproducible is recorded with the text: the
checkpoint's resolved commit, the seed of each generation, the sampling
settings, the GPU, and the versions of the libraries that produced it.

Usage:
  modal run python/generate.py --trial 8            # all four, briefly
  modal run --detach python/generate.py             # all four, in parallel
  modal run --detach python/generate.py --condition base-1.0  # one
  modal volume get --force englishregisterstudy /generated/ ./data/

A trial draws its seeds from a separate namespace, so it previews none of the
study's text, and writes to /trial on the volume, never to /generated.

The pure functions below carry no Modal dependency so that
python/test_generate.py can check them without a GPU.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
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

# Both checkpoints declare a 65,536-token context, and vLLM reserves key-value
# cache for one sequence of that length unless told otherwise, which a 7B
# model with full key-value heads cannot fit beside its weights on a 24 GB
# card. A prompt and 1,024 new tokens need a small fraction of it.
MAX_MODEL_LEN = 2048

# The first pass is generated in chunks so each is written to the volume as it
# finishes; reuse goes in smaller batches so the run stops close to the target.
CHUNK = 500
REUSE_BATCH = 64


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
    """The topics in topic_id order, the order the registration fixes."""
    with open(path, newline="", encoding="utf-8") as handle:
        return sorted(csv.DictReader(handle), key=lambda row: row["topic_id"])


def build_prompt(topic: str) -> str:
    """The prompt, identical across conditions.

    It names no variety, no register and no style: asking for "British English"
    or "a punchy blog post" would measure instruction-following rather than
    default register.
    """
    return PROMPT_TEMPLATE.format(topic=topic)


def seed_for(condition: str, topic_id: str, pass_number: int) -> int:
    """A generation's seed, fixed by what it is rather than by when it ran.

    Deterministic and independent of ordering, so a rerun asks for the same
    sampling. Whether vLLM then returns the same text regardless of what else
    is in the batch is measured by the trial and recorded in its manifest.
    """
    digest = 0
    for piece in (condition, topic_id, str(pass_number)):
        for char in piece:
            digest = (digest * 131 + ord(char)) % (2**31 - 1)
    return digest


def seed_name(condition: str, trial: int) -> str:
    """The name a condition's seeds are derived from.

    A trial uses its own, so it samples differently from the study's run and
    shows none of the text the study will count.
    """
    return f"trial:{condition}" if trial else condition


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


def run_condition(topics, generate, count_words, existing=(), *,
                  word_target=WORD_TARGET, chunk=CHUNK,
                  reuse_batch=REUSE_BATCH, max_passes=MAX_PASSES,
                  on_batch=None) -> list[Generation]:
    """Drive one condition to the registered stopping rule.

    The first pass generates every topic once, whatever the word count, so
    that all four conditions cover the same 4,000 topics. If that leaves the
    condition short of the target, topics are reused in topic_id order with
    the pass number, and so the seed, advanced, `reuse_batch` at a time, and
    generation stops after the batch that brings the total to the target.

    `generate(batch, pass_number)` returns one Generation per topic in the
    batch. Records in `existing`, from an interrupted run, are kept and not
    generated again. `on_batch` receives each batch's new records, so they can
    be written out as they finish.
    """
    records = list(existing)
    done = {(record.topic_id, record.pass_number) for record in records}
    words = sum(count_words(record.text) for record in records)
    for pass_number in range(1, max_passes + 1):
        if pass_number > 1 and words >= word_target:
            break
        todo = [topic for topic in topics
                if (topic["topic_id"], pass_number) not in done]
        size = chunk if pass_number == 1 else reuse_batch
        for start in range(0, len(todo), size):
            if pass_number > 1 and words >= word_target:
                break
            new = generate(todo[start:start + size], pass_number)
            records.extend(new)
            words += sum(count_words(record.text) for record in new)
            if on_batch is not None:
                on_batch(new)
    return records


def read_records(path: Path) -> list[Generation]:
    """Records already written by an interrupted run of the same condition.

    A final line cut short by the interruption is dropped, and its generation
    is made again; a malformed line anywhere else is an error.
    """
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    records = []
    for number, line in enumerate(lines, start=1):
        try:
            records.append(Generation(**json.loads(line)))
        except (json.JSONDecodeError, TypeError):
            if number == len(lines):
                break
            raise
    return records


def check_resumable(records: list[Generation], condition: Condition,
                    revision: str) -> None:
    """Refuse to continue a run made with anything else.

    A Hugging Face repository can be updated in place, so text from an earlier
    revision must not be topped up with text from a later one.
    """
    expected = (condition.name, condition.model, revision,
                condition.temperature, condition.top_p, MAX_NEW_TOKENS)
    for record in records:
        found = (record.condition, record.model, record.revision,
                 record.temperature, record.top_p, record.max_new_tokens)
        if found != expected:
            raise RuntimeError(
                f"cannot resume {condition.name}: existing text was made with "
                f"{found}, this run would use {expected}")


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

    # vLLM's default FlashInfer sampler compiles a CUDA kernel on first use,
    # and the slim image has no CUDA compiler, so the engine fails to start.
    # vLLM's PyTorch sampler applies the same temperature and top-p.
    image = (
        modal.Image.debian_slim(python_version="3.11")
        .pip_install("vllm==0.30.0", "transformers==5.17.0",
                     "huggingface_hub==1.33.0")
        .env({"VLLM_USE_FLASHINFER_SAMPLER": "0"})
        .add_local_file(REPO / "python" / "framecount.py", "/root/framecount.py")
        .add_local_file(REPO / "data" / "topics.csv", "/root/topics.csv")
        .add_local_file(REPO / "data" / "frames.csv", "/root/frames.csv")
    )

    app = modal.App("englishregisterstudy-generate", image=image)
    volume = modal.Volume.from_name("englishregisterstudy", create_if_missing=True)
    # The weights, kept between runs so each condition does not download
    # 15 GB again. The revision is pinned, so the cache cannot go stale.
    hf_cache = modal.Volume.from_name("englishregisterstudy-hf-cache",
                                      create_if_missing=True)
    OUT = Path("/data/generated")
    TRIAL_OUT = Path("/data/trial")

    # With full key-value heads, a 24 GB A10G holds only a handful of
    # sequences beside the weights; a 48 GB L40S holds several times as many.
    @app.function(gpu="L40S", timeout=60 * 60 * 6,
                  volumes={"/data": volume, "/root/.cache/huggingface": hf_cache})
    def generate_condition(condition_name: str, trial: int = 0) -> dict:
        """Generate one condition's text and write it to the volume."""
        import importlib.metadata as metadata
        import os
        import time

        import torch
        from huggingface_hub import HfApi
        from vllm import LLM, SamplingParams

        import framecount

        condition = next(c for c in CONDITIONS if c.name == condition_name)
        topics = load_topics("/root/topics.csv")
        if trial:
            topics = topics[:trial]
        out = TRIAL_OUT if trial else OUT

        # Pin what actually ran: a Hugging Face repository can be updated in
        # place, so the tag alone does not identify the weights.
        revision = HfApi().model_info(condition.model).sha
        versions = {
            package: metadata.version(package)
            for package in ("vllm", "torch", "transformers", "huggingface_hub")
        }

        llm = LLM(model=condition.model, revision=revision,
                  tokenizer_revision=revision, dtype="bfloat16", seed=0,
                  max_model_len=MAX_MODEL_LEN)
        hf_cache.commit()
        tokenizer = llm.get_tokenizer()
        names = seed_name(condition.name, trial)

        def prompt_for(topic: str) -> str:
            prompt = build_prompt(topic)
            if condition.instruct:
                prompt = tokenizer.apply_chat_template(
                    [{"role": "user", "content": prompt}],
                    tokenize=False, add_generation_prompt=True)
            return prompt

        tokens = 0

        def generate(batch, pass_number):
            nonlocal tokens
            prompts = [prompt_for(topic["topic"]) for topic in batch]
            seeds = [seed_for(names, topic["topic_id"], pass_number)
                     for topic in batch]
            outputs = llm.generate(
                prompts,
                [SamplingParams(temperature=condition.temperature,
                                top_p=condition.top_p,
                                max_tokens=MAX_NEW_TOKENS, seed=seed)
                 for seed in seeds],
                use_tqdm=False)
            new = []
            for topic, prompt, seed, output in zip(batch, prompts, seeds, outputs):
                completion = output.outputs[0]
                tokens += len(completion.token_ids)
                new.append(Generation(
                    condition=condition.name, topic_id=topic["topic_id"],
                    pass_number=pass_number, seed=seed, prompt=prompt,
                    text=completion.text,
                    finish_reason=completion.finish_reason or "",
                    model=condition.model, revision=revision,
                    temperature=condition.temperature, top_p=condition.top_p,
                    max_new_tokens=MAX_NEW_TOKENS))
            return new

        out.mkdir(parents=True, exist_ok=True)
        text_path = out / f"{condition.name}.jsonl"
        if trial:
            text_path.unlink(missing_ok=True)
        existing = read_records(text_path)
        check_resumable(existing, condition, revision)

        def write(new):
            with open(text_path, "a", encoding="utf-8") as handle:
                for record in new:
                    handle.write(json.dumps(asdict(record)) + "\n")
            volume.commit()

        def count_words(text: str) -> int:
            return framecount.word_count(framecount.tokenise(text))

        started = time.time()
        records = run_condition(topics, generate, count_words, existing,
                                max_passes=1 if trial else MAX_PASSES,
                                on_batch=write)
        seconds = time.time() - started

        manifest = {
            "condition": condition.name,
            "model": condition.model,
            "revision": revision,
            "temperature": condition.temperature,
            "top_p": condition.top_p,
            "max_new_tokens": MAX_NEW_TOKENS,
            "max_model_len": MAX_MODEL_LEN,
            "generations": len(records),
            "generations_per_pass": dict(sorted(
                Counter(r.pass_number for r in records).items())),
            "passes": max((r.pass_number for r in records), default=0),
            "words": sum(count_words(r.text) for r in records),
            "word_target": WORD_TARGET,
            "topics": len(topics),
            "finish_reasons": dict(Counter(r.finish_reason for r in records)),
            "resumed_from": len(existing),
            "seconds_this_run": round(seconds),
            "tokens_this_run": tokens,
            "tokens_per_second": round(tokens / seconds) if seconds else 0,
            "gpu": torch.cuda.get_device_name(0),
            "flashinfer_sampler": os.environ.get("VLLM_USE_FLASHINFER_SAMPLER"),
            "confirmatory": condition.name == CONFIRMATORY,
            "trial": trial,
            "versions": versions,
        }
        if trial:
            # The first topic again, alone and with the same seed: does vLLM
            # return the same text when the batch around it differs?
            again = generate(topics[:1], 1)[0]
            manifest["same_text_when_regenerated_alone"] = \
                again.text == records[0].text
            manifest["rendered_prompt_example"] = records[0].prompt
            manifest["text_starts"] = [r.text[:400] for r in records[:3]]
        with open(out / f"{condition.name}.manifest.json", "w",
                  encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)
        volume.commit()
        return manifest

    # The conditions are spawned together rather than called in turn, so under
    # `modal run --detach` every one of them keeps running if this machine
    # disconnects. Each needs its own GPU, and each writes its own files.
    @app.local_entrypoint()
    def main(condition: str = "", trial: int = 0) -> None:
        names = [condition] if condition else [c.name for c in CONDITIONS]
        calls = [(name, generate_condition.spawn(name, trial)) for name in names]
        for name, call in calls:
            manifest = call.get()
            if trial:
                print(json.dumps(manifest, indent=2))
                continue
            print(f"{name}: {manifest['generations']} generations, "
                  f"{manifest['words']:,} words over "
                  f"{manifest['passes']} pass(es)")
