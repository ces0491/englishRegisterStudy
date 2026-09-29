"""Study 4's generation run, on Modal.

Nine checkpoints of Olmo 3 7B, as registered at https://osf.io/d79u4 and
specified in docs/study4-protocol.md, each write one text for each of the
4,000 topics in data/topics.csv, under Study 2's settings: temperature 1.0,
top-p 1.0, at most 1,024 new tokens, a 2,048-token context.

The generation is Study 2's. Its pure functions are repeated here rather than
imported, because importing python/generate.py inside a Modal container would
also run that module's own Modal definitions; python/test_generate_study4.py
checks that every repeated function behaves exactly as Study 2's does. What
differs is the checkpoints: each is pinned to a commit, and three of them
load only through a configuration naming Olmo 3.

Usage:
  modal run python/generate_study4.py --trial 8       # all nine, briefly
  modal run --detach python/generate_study4.py        # all nine, in parallel
  modal run --detach python/generate_study4.py --arm B1
  modal volume get --force englishregisterstudy /study4/ ./data/

A trial draws its seeds from a separate namespace and writes to
/study4-trial on the volume, never to /study4.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

# --- Study 2's generation, repeated -------------------------------------------
#
# Each of these matches python/generate.py exactly, which the tests check.

MAX_NEW_TOKENS = 1024
MAX_MODEL_LEN = 2048
PROMPT_TEMPLATE = "Write a blog post titled: {topic}"
CHUNK = 500


def load_topics(path: str | Path) -> list[dict[str, str]]:
    """The topics in topic_id order."""
    with open(path, newline="", encoding="utf-8") as handle:
        return sorted(csv.DictReader(handle), key=lambda row: row["topic_id"])


def build_prompt(topic: str) -> str:
    return PROMPT_TEMPLATE.format(topic=topic)


def seed_for(condition: str, topic_id: str, pass_number: int) -> int:
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


def read_records(path: Path) -> list[Generation]:
    """Records written by an interrupted run; a cut-off last line is dropped."""
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


def run_arm(topics, generate, existing=(), *, chunk=CHUNK,
            on_batch=None) -> list[Generation]:
    """One generation per topic, in topic_id order, in chunks.

    Study 2's first pass, with no word target and so no second pass. Records
    in `existing`, from an interrupted run, are kept and not generated again.
    """
    records = list(existing)
    done = {record.topic_id for record in records}
    todo = [topic for topic in topics if topic["topic_id"] not in done]
    for start in range(0, len(todo), chunk):
        new = generate(todo[start:start + chunk], 1)
        records.extend(new)
        if on_batch is not None:
            on_batch(new)
    return records

BASE_REPO = "allenai/Olmo-3-1025-7B"
TEMPERATURE = 1.0
TOP_P = 1.0


@dataclass(frozen=True)
class Arm:
    name: str
    description: str
    repo: str
    revision: str
    chat: bool = False
    # Declares the pre-release architecture olmo2-retrofit and is loaded from
    # a local copy whose config names Olmo 3 (docs/study4-protocol.md).
    patched: bool = False


ARMS = (
    Arm("B1", "end of stage 1", BASE_REPO,
        "373bad25002f1624757a73235c5ca844c6375c25"),
    Arm("B2", "end of midtraining", BASE_REPO,
        "c3c800dc900f3fecc112e8cd6b2a13edabc096e1"),
    Arm("B3", "final base", BASE_REPO,
        "a81bae42db3975be1671e27b9c9a56da1a9f980f"),
    Arm("N1", "Gen-QA mix from 2T", BASE_REPO,
        "45786899c6c427d17f9291f3d97c7e4fcbd4962b", patched=True),
    Arm("N2", "math-code-thinking mix from 2T", BASE_REPO,
        "ab9f4b070e9125de257bfbe31bf8cc777daadfb4", patched=True),
    Arm("N3", "Round 5 mix from 2T", BASE_REPO,
        "34e13d5fae4d1aacf4aa019c377a332ed09ff136", patched=True),
    Arm("P1", "SFT", "allenai/Olmo-3-7B-Instruct-SFT",
        "e1452fc572d51966ff4aaeb25118b891eb93e549", chat=True),
    Arm("P2", "DPO", "allenai/Olmo-3-7B-Instruct-DPO",
        "b33130b7de49f0c2553b5c2b3bc8409ff3e627d1", chat=True),
    Arm("P3", "final instruct", "allenai/Olmo-3-7B-Instruct",
        "6e5971d9eba42665f5bd5a0fcf047f299ce1dccc", chat=True),
)


def arm_named(name: str) -> Arm:
    for arm in ARMS:
        if arm.name == name:
            return arm
    raise ValueError(f"no arm {name!r}; arms are {[a.name for a in ARMS]}")


def seed_name(arm: str, trial: int) -> str:
    """The namespace an arm's seeds come from: "study4:" and the arm, as
    registered, or a trial namespace no study text is drawn from."""
    return f"trial:study4:{arm}" if trial else f"study4:{arm}"


def check_resumable(records: list[Generation], arm: Arm) -> None:
    """Refuse to continue a run made with anything else."""
    expected = (arm.name, arm.repo, arm.revision, TEMPERATURE, TOP_P,
                MAX_NEW_TOKENS)
    for record in records:
        found = (record.condition, record.model, record.revision,
                 record.temperature, record.top_p, record.max_new_tokens)
        if found != expected:
            raise RuntimeError(f"cannot resume {arm.name}: existing text was "
                               f"made with {found}, this run would use {expected}")


# --- Modal ------------------------------------------------------------------

try:
    import modal
except ImportError:  # pragma: no cover - local testing without Modal
    modal = None

if modal is not None:
    REPO = Path(__file__).resolve().parent.parent

    image = (
        modal.Image.debian_slim(python_version="3.11")
        .pip_install("vllm==0.30.0", "transformers==5.17.0",
                     "huggingface_hub==1.33.0")
        .env({"VLLM_USE_FLASHINFER_SAMPLER": "0"})
        .add_local_file(REPO / "python" / "framecount.py", "/root/framecount.py")
        .add_local_file(REPO / "data" / "topics.csv", "/root/topics.csv")
        .add_local_file(REPO / "data" / "frames.csv", "/root/frames.csv")
    )

    app = modal.App("englishregisterstudy-study4-generate", image=image)
    volume = modal.Volume.from_name("englishregisterstudy", create_if_missing=True)
    hf_cache = modal.Volume.from_name("englishregisterstudy-hf-cache",
                                      create_if_missing=True)
    OUT = Path("/data/study4/generated")
    TRIAL_OUT = Path("/data/study4-trial")

    def patched_copy(arm: Arm) -> str:
        """A local copy of the indexed weights, with a config naming Olmo 3.

        The branch also carries a second, unindexed set of shards, which is
        not downloaded.
        """
        from huggingface_hub import hf_hub_download, snapshot_download

        index_path = hf_hub_download(arm.repo, "model.safetensors.index.json",
                                     revision=arm.revision)
        with open(index_path, encoding="utf-8") as handle:
            shards = sorted(set(json.load(handle)["weight_map"].values()))
        local = f"/root/.cache/huggingface/patched/{arm.revision}"
        snapshot_download(
            arm.repo, revision=arm.revision, local_dir=local,
            allow_patterns=shards + [
                "model.safetensors.index.json", "config.json",
                "generation_config.json", "tokenizer*",
                "special_tokens_map.json", "vocab.json", "merges.txt"])
        with open(f"{local}/config.json", encoding="utf-8") as handle:
            config = json.load(handle)
        config["architectures"] = ["Olmo3ForCausalLM"]
        config["model_type"] = "olmo3"
        with open(f"{local}/config.json", "w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)
        return local

    @app.function(gpu="L40S", timeout=60 * 60 * 6,
                  volumes={"/data": volume, "/root/.cache/huggingface": hf_cache})
    def generate_arm(name: str, trial: int = 0) -> dict:
        """Generate one arm's text and write it to the volume."""
        import importlib.metadata as metadata
        import os
        import time

        import torch
        from huggingface_hub import HfApi
        from vllm import LLM, SamplingParams

        import framecount

        arm = arm_named(name)
        # The pinned commit must still be what the repository serves.
        resolved = HfApi().model_info(arm.repo, revision=arm.revision).sha
        if resolved != arm.revision:
            raise RuntimeError(f"{arm.name}: {arm.revision} resolves to {resolved}")

        topics = load_topics("/root/topics.csv")
        if trial:
            topics = topics[:trial]
        out = TRIAL_OUT if trial else OUT
        versions = {package: metadata.version(package)
                    for package in ("vllm", "torch", "transformers",
                                    "huggingface_hub")}

        if arm.patched:
            llm = LLM(model=patched_copy(arm), dtype="bfloat16", seed=0,
                      max_model_len=MAX_MODEL_LEN)
        else:
            llm = LLM(model=arm.repo, revision=arm.revision,
                      tokenizer_revision=arm.revision, dtype="bfloat16",
                      seed=0, max_model_len=MAX_MODEL_LEN)
        hf_cache.commit()
        tokenizer = llm.get_tokenizer()
        names = seed_name(arm.name, trial)

        def prompt_for(topic: str) -> str:
            prompt = build_prompt(topic)
            if arm.chat:
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
                [SamplingParams(temperature=TEMPERATURE, top_p=TOP_P,
                                max_tokens=MAX_NEW_TOKENS, seed=seed)
                 for seed in seeds],
                use_tqdm=False)
            new = []
            for topic, prompt, seed, output in zip(batch, prompts, seeds, outputs):
                completion = output.outputs[0]
                tokens += len(completion.token_ids)
                new.append(Generation(
                    condition=arm.name, topic_id=topic["topic_id"],
                    pass_number=pass_number, seed=seed, prompt=prompt,
                    text=completion.text,
                    finish_reason=completion.finish_reason or "",
                    model=arm.repo, revision=arm.revision,
                    temperature=TEMPERATURE, top_p=TOP_P,
                    max_new_tokens=MAX_NEW_TOKENS))
            return new

        out.mkdir(parents=True, exist_ok=True)
        text_path = out / f"{arm.name}.jsonl"
        if trial:
            text_path.unlink(missing_ok=True)
        existing = read_records(text_path)
        check_resumable(existing, arm)

        def write(new):
            with open(text_path, "a", encoding="utf-8") as handle:
                for record in new:
                    handle.write(json.dumps(asdict(record)) + "\n")
            volume.commit()

        def count_words(text: str) -> int:
            return framecount.word_count(framecount.tokenise(text))

        started = time.time()
        records = run_arm(topics, generate, existing, on_batch=write)
        seconds = time.time() - started

        manifest = {
            "arm": arm.name,
            "description": arm.description,
            "model": arm.repo,
            "revision": arm.revision,
            "loaded_as_olmo3_from_patched_config": arm.patched,
            "chat_template": arm.chat,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "max_new_tokens": MAX_NEW_TOKENS,
            "max_model_len": MAX_MODEL_LEN,
            "generations": len(records),
            "topics": len(topics),
            "words": sum(count_words(r.text) for r in records),
            "finish_reasons": dict(Counter(r.finish_reason for r in records)),
            "resumed_from": len(existing),
            "seconds_this_run": round(seconds),
            "tokens_this_run": tokens,
            "gpu": torch.cuda.get_device_name(0),
            "flashinfer_sampler": os.environ.get("VLLM_USE_FLASHINFER_SAMPLER"),
            "seed_namespace": names,
            "trial": trial,
            "versions": versions,
        }
        if trial:
            manifest["rendered_prompt_example"] = records[0].prompt
            manifest["text_starts"] = [r.text[:300] for r in records[:2]]
        with open(out / f"{arm.name}.manifest.json", "w",
                  encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)
        volume.commit()
        return manifest

    # Spawned together, as Study 2's conditions were, so under --detach every
    # arm keeps running if this machine disconnects.
    @app.local_entrypoint()
    def main(arm: str = "", trial: int = 0) -> None:
        names = [arm] if arm else [a.name for a in ARMS]
        calls = [(name, generate_arm.spawn(name, trial)) for name in names]
        for name, call in calls:
            manifest = call.get()
            if trial:
                print(json.dumps(manifest, indent=2))
                continue
            print(f"{name}: {manifest['generations']} generations, "
                  f"{manifest['words']:,} words")
