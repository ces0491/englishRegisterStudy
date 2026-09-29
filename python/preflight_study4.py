"""Study 4's pre-flight: does each new checkpoint load, and does it score text sensibly?

Nothing here generates study text or counts a frame. Each checkpoint scores one
fixed public-domain passage, and its perplexity shows whether the weights
loaded under the configuration used.

Three of the checkpoints, the midtraining runs started from a 2T-token stage-1
checkpoint, declare a pre-release architecture (`olmo2-retrofit`) that neither
transformers nor vLLM recognises, and carry no modelling code of their own.
Their configuration otherwise matches Olmo 3's, apart from a sliding window of
4097 against 4096, which never binds at the study's 2,048-token limit. They are
loaded from a local copy whose config names the Olmo 3 architecture, with
exactly the weight files their own index lists: each branch also carries a
second, unindexed set of shards.

Usage:
  modal run python/preflight_study4.py
"""

from __future__ import annotations

import json
import math

import modal

BASE_REPO = "allenai/Olmo-3-1025-7B"
MAX_MODEL_LEN = 2048

# The opening of Pride and Prejudice (1813), in the public domain.
PASSAGE = (
    "It is a truth universally acknowledged, that a single man in possession "
    "of a good fortune, must be in want of a wife. However little known the "
    "feelings or views of such a man may be on his first entering a "
    "neighbourhood, this truth is so well fixed in the minds of the "
    "surrounding families, that he is considered the rightful property of "
    "some one or other of their daughters. \"My dear Mr. Bennet,\" said his "
    "lady to him one day, \"have you heard that Netherfield Park is let at "
    "last?\" Mr. Bennet replied that he had not. \"But it is,\" returned she; "
    "\"for Mrs. Long has just been here, and she told me all about it.\" Mr. "
    "Bennet made no answer."
)

# name: (revision, loaded as Olmo 3 from a patched local copy)
CHECKPOINTS = {
    "stage1-end": ("373bad25002f1624757a73235c5ca844c6375c25", False),
    "stage2-end": ("c3c800dc900f3fecc112e8cd6b2a13edabc096e1", False),
    "gen-mc-from-2T": ("45786899c6c427d17f9291f3d97c7e4fcbd4962b", True),
    "math-code-from-2T": ("ab9f4b070e9125de257bfbe31bf8cc777daadfb4", True),
    "round5-from-2T": ("34e13d5fae4d1aacf4aa019c377a332ed09ff136", True),
}

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("vllm==0.30.0", "transformers==5.17.0",
                 "huggingface_hub==1.33.0")
    .env({"VLLM_USE_FLASHINFER_SAMPLER": "0"})
)
app = modal.App("englishregisterstudy-preflight4", image=image)
hf_cache = modal.Volume.from_name("englishregisterstudy-hf-cache",
                                  create_if_missing=True)


def patched_copy(revision: str) -> str:
    """Download the indexed weights and a config naming Olmo 3; return the path."""
    from huggingface_hub import hf_hub_download, snapshot_download

    index_path = hf_hub_download(BASE_REPO, "model.safetensors.index.json",
                                 revision=revision)
    with open(index_path, encoding="utf-8") as handle:
        shards = sorted(set(json.load(handle)["weight_map"].values()))
    local = f"/root/.cache/huggingface/patched/{revision}"
    snapshot_download(
        BASE_REPO, revision=revision, local_dir=local,
        allow_patterns=shards + ["model.safetensors.index.json", "config.json",
                                 "generation_config.json", "tokenizer*",
                                 "special_tokens_map.json", "vocab.json",
                                 "merges.txt"])
    with open(f"{local}/config.json", encoding="utf-8") as handle:
        config = json.load(handle)
    original = {key: config[key] for key in ("architectures", "model_type")}
    config["architectures"] = ["Olmo3ForCausalLM"]
    config["model_type"] = "olmo3"
    with open(f"{local}/config.json", "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
    print(f"patched {revision[:8]}: {original} -> Olmo3ForCausalLM/olmo3, "
          f"{len(shards)} indexed shards")
    return local


@app.function(gpu="L40S", timeout=60 * 60,
              volumes={"/root/.cache/huggingface": hf_cache})
def score(name: str) -> dict:
    from vllm import LLM, SamplingParams

    revision, patch = CHECKPOINTS[name]
    if patch:
        llm = LLM(model=patched_copy(revision), dtype="bfloat16", seed=0,
                  max_model_len=MAX_MODEL_LEN)
    else:
        llm = LLM(model=BASE_REPO, revision=revision, tokenizer_revision=revision,
                  dtype="bfloat16", seed=0, max_model_len=MAX_MODEL_LEN)
    hf_cache.commit()
    output = llm.generate([PASSAGE], SamplingParams(max_tokens=1, prompt_logprobs=0),
                          use_tqdm=False)[0]
    logprobs = []
    for token_id, position in zip(output.prompt_token_ids, output.prompt_logprobs):
        if position:
            logprobs.append(position[token_id].logprob)
    return {"checkpoint": name, "revision": revision, "patched": patch,
            "scored_tokens": len(logprobs),
            "perplexity": round(math.exp(-sum(logprobs) / len(logprobs)), 2)}


@app.local_entrypoint()
def main() -> None:
    calls = [score.spawn(name) for name in CHECKPOINTS]
    for call in calls:
        print(json.dumps(call.get()))
