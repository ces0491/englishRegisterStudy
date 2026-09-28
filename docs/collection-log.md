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

## Study 3

The Dolma 3 draw, run on Modal against the sampling frame registered at
<https://osf.io/ngt3m> and the update described in `docs/deviations.md`.

**Study 2's text when Study 3 was registered.** None had been generated, and
none has been since: the Modal volume the generation run writes to held no
`generated/` folder on 28 September 2026. The trial described under Study 2
wrote only to `trial/`.

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
