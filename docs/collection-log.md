# Collection log

## Study 1

What each GloWbE query session did, including the queries that failed. Counts
that fit the registered grid go in `data/counts.csv`. This log keeps what does
not fit it yet.

### Constraints of a free account

Each was found during collection. The interface states them only when a query
is refused.

- **Section rule.** A search restricted to a section (General or Blog) is
  refused when every slot in the string occurs 1,500,000 times or more in the
  corpus: "(Except in COCA) You cannot search for high frequency multi-word
  strings, when you have also selected a SECTION." The unrestricted search
  still works.
- **Five-word limit.** "Unless you have a premium license, your search string
  must not be longer than five words in length." Tokens count as words, so
  `it 's not * , it 's` (F06) is seven.
- **Query limit.** 20 searches per rolling 24 hours. A premium licence gives
  200.

### Session 1 — 22 September 2026

Chart display throughout. "Combined" is the unrestricted search (section box
set to IGNORE).

| Frame | Section split | US | GB | IE | AU | ZA | All 20 | Note |
|---|---|---:|---:|---:|---:|---:|---:|---|
| F01 | works | 1109 | 440 | 134 | 211 | 62 | 2728 | general + blog = combined in all five |
| F02 | works | 192 | 69 | 22 | 23 | 10 | 481 | general + blog = combined in all five |
| F03 | refused, General and Blog | 4052 | 1977 | 503 | 810 | 202 | 11772 | section rule |
| F04 | works | 2542 | 2613 | 520 | 973 | 237 | 10808 | general + blog = combined in all five |
| F05 | works | 198 | 143 | 15 | 30 | 9 | 552 | general + blog = combined in all five |
| F06 | refused, unrestricted too | | | | | | | five-word limit: no count possible on a free account |
| F07 | refused, General | 4379 | 4735 | 817 | 1575 | 271 | 16882 | section rule |

The session ended at the query limit (21 queries) before F08. Section word
counts were also taken this session (see D1 in `docs/deviations.md`).

### Session 2 — 23 September 2026

| Frame | Section split | US | GB | IE | AU | ZA | All 20 | Note |
|---|---|---:|---:|---:|---:|---:|---:|---|
| F08 | refused, General | 747 | 882 | 183 | 294 | 59 | 3828 | section rule |
| F09 | refused, General | 3201 | 2654 | 385 | 805 | 161 | 10237 | section rule |
| F10 | refused, General | 9246 | 6828 | 1370 | 2648 | 763 | 33443 | section rule; interface flagged SLOW QUERY |
| F11 | works | 229 | 150 | 41 | 52 | 7 | 616 | general + blog = combined in all five |
| F12 | works | 86 | 58 | 17 | 30 | 1 | 275 | general + blog = combined in all five; ZA blog is the first zero cell |
| F13 | refused, General | 24330 | 19265 | 3958 | 7492 | 1558 | 84253 | section rule; roughly ten times any other frame |
| F14 | works | 12073 | 7642 | 1449 | 2965 | 614 | 36702 | general + blog = combined in all five |
| F15 | combined 23 Sep, sections 25 Sep | 696 | 354 | 53 | 136 | 37 | 1763 | general + blog = combined in all five |

The limit is a rolling 24-hour window and counts refused queries too, which is
why a survey of eight frames exhausted it.

### Which frames the interface allows

| Split by section | Combined only | Not countable |
|---|---|---|
| F01, F02, F04, F05, F11, F12, F14, F15 | F03, F07, F08, F09, F10, F13 | F06 |

The blocked set is not arbitrary: the section rule catches the frames built
entirely from very common words, which is the whole contrastive family
(F06-F10) plus F03 and F13. What follows from it is deviation D2.

### Session 3 — 25 September 2026

F15's General and Blog runs, the two the second session ran out of queries
before reaching. Both grids are now complete: 70 combined cells in
`data/counts-combined.csv` and 80 section cells in `data/counts.csv`.

Three cells were then re-queried as a reproduction check, chosen from different
parts of the grid: F11 General GB, F09 unrestricted IE, and F15 Blog ZA. All
three matched what the repository holds, as did every other variety in those
three charts.

## Study 2

The generation run for the protocol registered at <https://osf.io/qjgtc>.

**28 September 2026, trial.** Before any of the study's text was generated,
`generate.py --trial 128` ran the pipeline on the first 128 topics with the
base and instruct models at temperature 1.0, on an L40S with vLLM 0.30.0.
Trial seeds come from a separate namespace, so the trial previewed none of the
study's text. It wrote to `trial/` on the volume, its text was not counted, and
it is not part of the data. What it established:

- The first attempt failed to start: vLLM's default FlashInfer sampler compiles
  a CUDA kernel on first use, and the image has no CUDA compiler. The run uses
  vLLM's PyTorch sampler, which applies the same temperature and top-p.
- All 256 texts are non-empty and free of special tokens and invented chat
  turns. About a third reached the 1,024-token limit (42 base, 41 instruct);
  the rest stopped on their own.
- Words per generation averaged 585 for the base model and 656 for the instruct
  model, so 4,000 topics come to about 2.3 and 2.6 million words at
  temperature 1.0, above the 2 million target. The 0.7 settings were not tried.
- Generation ran at about 1,450 to 1,500 tokens a second, so the four
  conditions need about 2.5 hours on an L40S.
- A generation run again alone, with the same seed, did not reproduce its
  text. The seed fixes the sampling request, and vLLM's arithmetic varies with
  the batch around it, so the recorded seeds document how each text was
  sampled without guaranteeing the same text on a rerun.
- The instruct checkpoint's chat template adds a system prompt whenever the
  conversation has none: `You are a helpful function-calling AI assistant.
  You do not currently have access to any functions. <functions></functions>`

**28 September 2026, pre-flight.** After the library versions were pinned, a
second trial ran 8 topics in each of the four conditions, in parallel on four
L40S GPUs, with trial seeds as before. It ran cleanly on the rebuilt image,
including the two 0.7 settings, which the first trial had not tried.

**28 September 2026, the run.** `modal run --detach python/generate.py` was
launched after commit `454e557`, and the four conditions ran in parallel on one
L40S each. Generation began at about 17:55 UTC, and the conditions finished
between 18:17 and 18:32 UTC. The text was downloaded and checked on 29
September before any frame was counted.

| Condition | Generations | Words | Reached 1,024 tokens | Empty |
|---|---:|---:|---:|---:|
| `base-1.0` | 4,000 | 2,426,034 | 1,503 | 2 |
| `base-0.7` | 4,000 | 2,327,984 | 1,050 | 0 |
| `instruct-1.0` | 4,000 | 2,680,977 | 1,284 | 0 |
| `instruct-0.7` | 4,000 | 2,614,894 | 918 | 0 |

- Each condition passed two million words on its first pass, so no topic was
  reused. Each file holds the 4,000 topics once, in `topic_id` order, with the
  seed `seed_for` gives the condition on pass 1 and none from the trial's
  namespace. No run was interrupted or resumed.
- Every generation records the checkpoint revisions the trial used: base
  `a81bae42db3975be1671e27b9c9a56da1a9f980f` and instruct
  `6e5971d9eba42665f5bd5a0fcf047f299ce1dccc`, under vLLM 0.30.0, torch 2.13.0,
  transformers 5.17.0 and huggingface_hub 1.33.0 with the PyTorch sampler.
- Base prompts are the raw template. Every instruct prompt is the same
  rendered template around it, carrying the default system prompt S2-D1
  describes.
- The two empty generations, `T0940` and `T3516` in `base-1.0`, are texts the
  model ended at once. They are kept with zero words, as registered.
- Two `base-1.0` texts, `T2413` and `T2937`, contain `<|im_start|>` or
  `<|im_end|>` among invented markup such as `<|im_title|>` and `<|eot_id|>`.
  Base prompts carry no template, so this is the model writing chat markup it
  has seen, and it is counted as generated. No other condition's text contains
  a special token or an invented chat turn.
- Each manifest's word count and finish reasons match a recount of its text.

The text is in `data/generated/`, which git ignores. The counts taken from it
are in `data/counts-generated.csv` and the run's totals in
`data/generated-run.csv`.

## Study 3

The Dolma 3 draw, run on Modal against the sampling frame registered at
<https://osf.io/ngt3m> and the update described in `docs/deviations.md`.

**Study 2's text when Study 3 was registered.** None had been generated, and
none was until after the draw: the Modal volume the generation run writes to
held no `generated/` folder until Study 2's run began at about 17:55 UTC on 28
September 2026, eleven hours after the last subset finished. The trial
described under Study 2 wrote only to `trial/`.

**25 September 2026.** The first `count_dolma.py --list-only` run found the
corpus stored as JSON Lines, where the registration said parquet. Settling the
format meant reading documents from 68 shards and counting words, but no
frames, in six of them. Deviations S3-D1 and S3-D2 record what changed.

**27 September 2026.** The OSF update filing S3-D1 and S3-D2 was approved at
19:00 UTC. `common_crawl` was counted in about 50 minutes, finishing at 19:55
UTC: 200 files, 200,443,988 words.

**28 September 2026.** The other five subsets finished between 06:30 and 06:54
UTC.

| Subset | Files | Words | Short of a million | Redacted documents |
|---|---:|---:|---:|---:|
| `common_crawl` | 200 | 200,443,988 | 0 | 0 |
| `olmocr_science_pdfs` | 40 | 20,066,104 | 26 | 174 of 3,124 |
| `stack_edu` | 20 | 20,281,855 | 0 | 0 |
| `finemath-3plus` | 20 | 20,116,321 | 0 | 0 |
| `rpj-proofpile-arxiv` | 20 | 20,105,467 | 0 | 0 |
| `dolma1_7-wiki-en` | 20 | 20,018,046 | 0 | 0 |

Each subset's drawn files are the start of the registered shuffle, recomputed
from the pinned listing, and each file either reached its million words or ran
out. Three drawn files recounted on a second machine matched the run's records
exactly, frame counts included.

olmOCR's 40 files reached 15 of its 21 topics. Health and education, 23.5% of
the subset's bytes between them, drew no file, so neither the olmOCR rate nor
its byte-reweighted version covers them. olmOCR carries 4.7% of the whole-mix
rate, so halving or doubling its rate would move that figure by between -2.3%
and +4.7%.

## Study 4

The follow-up designed on 29 September 2026 and specified in
`docs/study4-protocol.md`.

**29 September 2026, pre-flight.** Before registration. Nothing was generated
from the study's prompts and no frame was counted.

- Every checkpoint and dataset was pinned to a commit, listed in the protocol.
- The chat templates of the SFT, DPO and final instruct checkpoints rendered
  byte-identical prompts with no tools passed, matching the prompts Study 2
  recorded.
- At its pinned commit the midtraining mix holds 71,090 files in 24 sources,
  all JSON Lines compressed with zstd. The SFT set is 15 parquet files and the
  DPO set 4.
- The three midtraining runs from the 2T checkpoint declare a pre-release
  architecture, `olmo2-retrofit`. Each branch carries two sets of weight
  shards, and its index lists the six-shard set, 29.2 GB of float32 weights.
- `python/preflight_study4.py` loaded the five new base-model checkpoints on
  L40S GPUs, the three runs from 2T through a configuration naming Olmo 3, and
  each scored the opening of *Pride and Prejudice*:

| Checkpoint | Loaded | Perplexity |
|---|---|---:|
| End of stage 1 | natively | 1.19 |
| End of midtraining | natively | 1.26 |
| Gen-QA mix from 2T | as Olmo 3 | 1.17 |
| Math-code-thinking mix from 2T | as Olmo 3 | 1.23 |
| Round 5 mix from 2T | as Olmo 3 | 1.22 |

The passage is famous enough that every checkpoint predicts it almost exactly,
so the check shows the weights load and compute correctly and says nothing
about fluency. The run above is the second. The first run's output was cut
short by a display filter, and its two surviving results, 1.24 and 1.22 for
the last two checkpoints, agree with the second run's to within vLLM's
run-to-run variation.

`R/calibrate-ratio.R` checked the family outcome's estimator on Studies 2 and
3's data: across 30 scenarios, 95% intervals covered the true ratio 93.5% to
95.6% of the time. An earlier version of the design weighted 24 midtraining
sources of 40 files each and checked 28 scenarios, covering 93.5% to 95.7%;
the design now draws the midtraining sample in proportion to token shares,
and the composite uses the model Studies 2 and 3 used.

**29 September 2026, registration.** Filed at 10:16 UTC as
<https://osf.io/d79u4>, public from filing, with no embargo. Every filed
answer matches `docs/osf-study4-registration.md` word for word, checked
against OSF's API the same day. The filed *Context* answer links the
repository but not a commit; GitHub then held `f6b09d9`, committed and pushed
at 09:08 UTC. The filed text includes three corrections made before filing and
committed after it: the option-list answers, H4's description of the two
midtraining mixes, and the protocol's label for contrast 4.
