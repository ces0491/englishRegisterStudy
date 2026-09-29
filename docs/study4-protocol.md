# Study 4 protocol: where the excess enters

What Study 4 generates, what it counts, and how it compares them. The design
and its reasons are in `RESEARCH-PLAN.md` under *Study 4*; this document is
the specification the registration pins. Nothing below has been generated or
counted.

## The question

Olmo 3's base model uses the contrastive frames at about five times the rate
of its stage-1 web input, and the instruct model at about three times the base
model's (Studies 2 and 3, exploratory). Olmo 3 was trained in six published
stages, and Ai2 released a checkpoint after each and the data for each. Study 4
sets each stage's input rate against the rate of the checkpoint it produced,
to find where the excess enters.

## Outcomes

Two, co-primary:

- **family**: the contrastive frames F06, F07, F08 and F09, the ones not
  marked partial in `data/frames.csv`, as a summed rate: each unit's hits over
  its words. With four frames there are too few to serve as the replication
  unit, so the units of text are.
- **composite**: all fifteen frozen frames, as the source effect in the model
  Studies 2 and 3 used (`R/model.R`). Frames are the replication unit, and each
  frame's ratio counts equally however common the frame is, so the composite
  means what it meant in Studies 1 to 3.

Frames and words are counted by `python/framecount.py`, frozen since Study 1
and unchanged.

## Output side: nine checkpoints

Each generates one text for each of the 4,000 topics in `data/topics.csv`,
with Study 2's settings: temperature 1.0, top-p 1.0, at most 1,024 new tokens,
a 2,048-token context, bfloat16 weights, vLLM 0.30.0 with its PyTorch sampler,
transformers 5.17.0 and huggingface_hub 1.33.0, on an L40S.

| Arm | Checkpoint | Repository and branch | Commit | Prompt |
|---|---|---|---|---|
| B1 | end of stage 1 | `allenai/Olmo-3-1025-7B`, `stage1-step1413814` | `373bad25002f1624757a73235c5ca844c6375c25` | raw |
| B2 | end of midtraining | `allenai/Olmo-3-1025-7B`, `stage2-step47684` | `c3c800dc900f3fecc112e8cd6b2a13edabc096e1` | raw |
| B3 | final base | `allenai/Olmo-3-1025-7B`, `main` | `a81bae42db3975be1671e27b9c9a56da1a9f980f` | raw |
| N1 | Gen-QA mix from 2T | `allenai/Olmo-3-1025-7B`, `stage2-step47684-mix-gen-mc-only-from-2T-ckpt` | `45786899c6c427d17f9291f3d97c7e4fcbd4962b` | raw |
| N2 | math-code-thinking mix from 2T | `allenai/Olmo-3-1025-7B`, `stage2-step47684-mix-math-code-reasoning-web-from-2T-ckpt` | `ab9f4b070e9125de257bfbe31bf8cc777daadfb4` | raw |
| N3 | Round 5 mix from 2T | `allenai/Olmo-3-1025-7B`, `stage2-step47684-mix-round5-from-2T-ckpt` | `34e13d5fae4d1aacf4aa019c377a332ed09ff136` | raw |
| P1 | SFT | `allenai/Olmo-3-7B-Instruct-SFT`, `main` | `e1452fc572d51966ff4aaeb25118b891eb93e549` | chat template |
| P2 | DPO | `allenai/Olmo-3-7B-Instruct-DPO`, `main` | `b33130b7de49f0c2553b5c2b3bc8409ff3e627d1` | chat template |
| P3 | final instruct | `allenai/Olmo-3-7B-Instruct`, `main` | `6e5971d9eba42665f5bd5a0fcf047f299ce1dccc` | chat template |

- **Prompts.** A raw prompt is `Write a blog post titled: {topic}`, as in
  Study 2. A chat-template prompt is the same text as the user turn, rendered
  with the checkpoint's own template. All three chat templates insert the
  default system prompt Study 2's S2-D1 describes, and with no tools they
  render byte-identical prompts, which match the prompts Study 2 recorded.
- **N1 to N3** declare a pre-release architecture, `olmo2-retrofit`, which the
  pinned transformers and vLLM do not recognise, and ship no modelling code.
  Their configuration otherwise matches Olmo 3's, apart from a sliding window
  of 4097 against 4096, which never binds at a 2,048-token context. They are
  loaded from a local copy of the files their own `model.safetensors.index.json`
  lists, whose `config.json` names `Olmo3ForCausalLM` and model type `olmo3`.
  Each branch also carries a second set of weight shards the index does not
  list, and those are not used.
- **Seeds.** Each generation's seed is `seed_for("study4:" + arm, topic_id, 1)`
  from `python/generate.py`, a namespace no earlier run has used, so B3 and P3
  are new draws from the checkpoints Study 2 used. Study 2's text for those
  checkpoints serves as a replication check.
- **Stopping.** Exactly 4,000 generations per arm, one per topic in `topic_id`
  order, with no word target and no reuse of topics. Every generation is kept
  with its arm, topic, commit, settings, seed, prompt, text and finish reason.

## Input side

### Stage 1: reused

Study 3's registered sample of `common_crawl`, 200 files of about a million
words each, with per-file counts in `data/dolma/common_crawl.json`. The unit is
the file.

### Midtraining: `allenai/dolma3_dolmino_mix-100B-1025`

At commit `f23942ae8a8114af6e992efe8188ce8c531acd16`, 71,090 files of JSON Lines
compressed with zstd, in 24 sources that match the rows of the dataset card.
The sample is 240 million words, allocated across the sources in proportion
to their shares of the card's token counts, so the pooled sample is the mix
as the model saw it and enters the analysis as one source. For each source:

1. List its files at the pinned commit, sorted by path.
2. Order them by a random key proportional to compressed size: each file gets
   `u ** (1 / size)`, with `u` uniform from NumPy's
   `default_rng([20260929, k])` for the source's number `k` in the table
   below, and files are taken in descending order of key. Drawing by size
   keeps small files from supplying more than their share of the text, which
   is what happened to Study 3's olmOCR draw (deviation S3-D2).
3. Read the files in that order, each from its first document, whole
   documents at a time, taking at most 250,000 words from any one file.
   Reading stops after the document that brings the source to its allocation.
4. Record, per file: path, documents read, words, and hits per frame.

The unit is the file: at least 973 of them, since no file supplies more than
250,000 words. Shares are in tokens and rates are per word, so the sample
matches the mix's composition only approximately, and the write-up says so.
The smallest source gets under 400,000 words, so rates by source are
imprecise for the smallest; rates by category rest on at least 11.9 million
words each.

| k | Source | Directory | Category | Tokens (B) | Share | Words drawn |
|---:|---|---|---|---:|---:|---:|
| 1 | TinyMATH Mind | `tinymath-mind` | Math (synth) | 0.898 | 0.0090 | 2,157,271 |
| 2 | TinyMATH PoT | `tinymath-pot` | Math (synth) | 0.241 | 0.0024 | 578,956 |
| 3 | CraneMath | `cranemath` | Math (synth) | 5.620 | 0.0563 | 13,500,961 |
| 4 | MegaMatt | `megamatt` | Math (synth) | 1.730 | 0.0173 | 4,155,990 |
| 5 | Dolmino Math | `dolmino-math` | Math (synth) | 10.700 | 0.1071 | 25,704,676 |
| 6 | StackEdu (FIM) | `stack_edu-fim-*` | Code | 10.000 | 0.1001 | 24,023,062 |
| 7 | CraneCode | `cranecode` | Python (synth) | 10.000 | 0.1001 | 24,023,062 |
| 8 | Reddit To Flashcards | `reddit_to_flashcards` | QA (synth) | 5.900 | 0.0591 | 14,173,607 |
| 9 | Wiki To RCQA | `wiki_to_rcqa-part*` | QA (synth) | 3.000 | 0.0300 | 7,206,919 |
| 10 | Nemotron Synth QA | `nemotron-synth-qa` | QA (synth) | 5.000 | 0.0500 | 12,011,531 |
| 11 | Math Meta-Reasoning | `math-meta-reasoning` | Thinking (synth) | 0.381 | 0.0038 | 915,279 |
| 12 | Code Meta-Reasoning | `code-meta-reasoning` | Thinking (synth) | 0.459 | 0.0046 | 1,102,659 |
| 13 | Program-Verifiable | `program_verifiable` | Thinking (synth) | 0.159 | 0.0016 | 381,967 |
| 14 | OMR Rewrite FullThoughts | `omr-rewrite-fullthoughts` | Thinking (synth) | 0.850 | 0.0085 | 2,041,960 |
| 15 | QWQ Reasoning Traces | `qwq-reasoning-traces` | Thinking (synth) | 1.870 | 0.0187 | 4,492,313 |
| 16 | General Reasoning Mix | `general_reasoning_mix` | Thinking (synth) | 1.870 | 0.0187 | 4,492,313 |
| 17 | Gemini Reasoning Traces | `gemini-reasoning-traces` | Thinking (synth) | 0.246 | 0.0025 | 590,967 |
| 18 | Llama Nemotron Reasoning Traces | `llama_nemotron-reasoning-traces` | Thinking (synth) | 1.250 | 0.0125 | 3,002,883 |
| 19 | OpenThoughts2 Reasoning Traces | `openthoughts2-reasoning-traces` | Thinking (synth) | 1.250 | 0.0125 | 3,002,883 |
| 20 | Tulu 3 SFT | `tulu-3-sft` | Instruction (synth) | 1.100 | 0.0110 | 2,642,537 |
| 21 | Dolmino 1 Flan | `dolmino_1-flan` | Instruction (synth) | 5.000 | 0.0500 | 12,011,531 |
| 22 | OLMOCR Science PDFs (High Q.) | `olmocr*` | PDFs | 4.990 | 0.0499 | 11,987,508 |
| 23 | STEM-Heavy Crawl | `stem-heavy-crawl` | Web pages | 4.990 | 0.0499 | 11,987,508 |
| 24 | Common Crawl (High Q.) | `common_crawl-high-quality_*` | Web pages | 22.400 | 0.2242 | 53,811,659 |
| | Total | | | 99.90 | 1.0000 | 240,000,002 |

The card's own total is 99.95 billion tokens; the rows sum to 99.90, and the
shares use the rows. Allocations are rounded to the nearest word.

### SFT: `allenai/dolci-instruct-sft`

At commit `bd3c8f3a9b2cc5a9682e44b96ddd0bb2ff027221`, all 2,152,112
conversations, from 15 parquet files. The unit is the conversation, and its
text is the `content` of every message whose role is `assistant`, joined by
newlines. A conversation with no assistant content counts as zero words.
Recorded per conversation: `id`, `source_dataset`, words and hits per frame.

### DPO: `allenai/dolci-3-instruct-dpo-with-metadata`

At commit `aed155cf32e809b590490b6c3577ee4b0d0a5019`, all 260,000 pairs, from 4
parquet files. The unit is the pair. Its two texts are the `content` of the
last message whose role is `assistant` in `chosen` and in `rejected`; earlier
turns are context the pair shares. Recorded per pair: row number,
`chosen_model`, `rejected_model`, and words and hits per frame for each side.

### Not counted

The long-context mix, two-thirds of which is midtraining data, and the RLVR
set, `allenai/Dolci-Instruct-RL-7B`, which holds 169,964 prompts with
reference answers and none of the model's responses. RLVR is measured on the
output side only.

## Analysis

**Family.** `R/ratio.R`. Each source's rate is its total hits over its total
words, with a variance from the variation between its units, the ratio
estimator's linearisation. Two sources are compared as a log ratio with a Wald
interval from the normal reference; the DPO comparison is paired, using each
pair's contribution to both rates. `R/calibrate-ratio.R` checked these
intervals on data Studies 2 and 3 already hold: across 30 scenarios matching
the contrasts, 95% intervals covered the true ratio 93.5% to 95.6% of the
time.

**Composite.** `R/model.R`, as in Studies 2 and 3: one Poisson mixed model
over all fourteen sources,

    hits ~ frame_id + source + (1 | frame:source),  offset log(words)

fitted with bobyqa and, on a convergence failure, Nelder-Mead. The sources are
the nine output arms, the stage-1 sample, the pooled midtraining sample, the
SFT responses, and the chosen and the rejected DPO responses. Each contrast is
a difference of source effects, with a t reference on one degree of freedom
per frame less one; on synthetic grids in Study 1's calibration, that
reference covered a known ratio 92% of the time. A frame with no hits in any source leaves the
model and is reported. The chosen and rejected responses enter as two sources,
so the model ignores their pairing; the family's contrast for H7 is the
paired one.

### Confirmatory contrasts

Nine contrasts, each on both outcomes: eighteen tests, Holm-corrected together.

| # | Contrast | Explanation it tests | Predicted |
|---|---|---|---|
| 1 | B1 against stage-1 input | pretraining amplifies by itself | B1 higher |
| 2 | midtraining sample against stage-1 input | midtraining data carries it | midtraining higher |
| 3 | B2 against B1 | midtraining raises the model's rate | B2 higher |
| 4 | N1 against N2 | instruction data or reasoning traces | N1 higher if instruction data, N2 higher if reasoning traces |
| 5 | SFT responses against B3 | fine-tuning data carries it | SFT data higher |
| 6 | P1 against B3 | fine-tuning raises the model's rate | P1 higher |
| 7 | chosen against rejected, paired | preference data pushes it | chosen higher |
| 8 | P2 against P1 | preference tuning raises the model's rate | P2 higher |
| 9 | P3 against P2 | reinforcement learning raises the model's rate | P3 higher |

A contrast supports its explanation when the ratio is in the predicted
direction and its Holm-adjusted p is below 0.05. A ratio in the opposite
direction with an adjusted p below 0.05 is evidence against it. Contrast 4
supports whichever explanation its significant direction favours.

### Secondary, with intervals and no correction

- B3 against B2, the long-context stage, for which no direction is predicted.
- N3 against N1 and against N2.
- Each checkpoint against its own stage's data: B2 against the midtraining
  sample, and P1 against the SFT responses.
- Replication: B3 and P3 against Study 2's `base-1.0` and `instruct-1.0` text.
- Midtraining rates by category, and by source where the source's sample
  allows; SFT rates by `source_dataset`, with the GPT-4.1 WildChat responses reported separately;
  DPO rates by `chosen_model` and `rejected_model`.
- The family outcome with the partial F10 added.

### Exploratory

Per-frame rates, and generation length against frame rate, as in Study 2.

## Pre-flight

Run on 29 September 2026, before registration, with `python/preflight_study4.py`
and recorded in `docs/collection-log.md`. It generated nothing from the
study's prompts and counted no frame. The five new base-model checkpoints all
loaded, the three runs from 2T through the Olmo 3 configuration described
above, and each scored the opening of *Pride and Prejudice* with a perplexity
between 1.17 and 1.26. The passage is famous enough that every checkpoint
predicts it almost exactly, so this shows the weights load and compute
correctly and nothing about fluency.

## If something cannot be run

If a pinned checkpoint or dataset revision can no longer be downloaded or
loaded, its arm and every contrast that uses it are dropped and reported, and
nothing is substituted. Any other departure from this document is a declared
deviation, filed before the analysis runs.
