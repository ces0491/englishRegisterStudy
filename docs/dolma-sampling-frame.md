# Study 3: the Dolma 3 sampling frame

Registered at <https://osf.io/ngt3m> on 25 September 2026, before any document
was drawn, pinned to commit `381703b`.

Study 3 counts the frozen frames in the corpus Olmo 3 was trained on and sets
that against the rates in Olmo 3's own output. A model producing American
register proves nothing on its own: if the training data was full of these
frames, a model reproducing them is a model working correctly. The question is
whether the output rate matches the input rate or exceeds it.

The sampling frame has to be fixed before a single document is drawn, and
registered with it. "A few million words" is a target, not a sampling frame.

## The corpus

`allenai/dolma3_mix-6T-1025`, the stage-1 pretraining mix for Olmo 3, 5.93
trillion tokens over 3.87 billion documents, stored as parquet. Its published
composition:

| Component | Tokens | Share |
|---|---|---|
| `common_crawl` | 4.51T | 76.07% |
| `olmocr_science_pdfs` | 805B | 13.57% |
| `stack_edu` | 409B | 6.89% |
| `finemath-3plus` | 151B | 2.56% |
| `rpj-proofpile-arxiv` | 50.9B | 0.86% |
| `dolma1_7-wiki-en` | 2.51B | 0.04% |

**Stage 1 only.** It is 97.5% of Olmo 3's pretraining budget and one named,
published corpus. Later stages are excluded, and the write-up says so: data
late in training is small in volume but disproportionately influential per
token, so "the training data" here means stage 1 rather than everything the
weights ever saw.

## What is sampled

| Subset | Words drawn | Files drawn | Words per file |
|---|---:|---:|---:|
| `common_crawl` | 200,000,000 | 200 | 1,000,000 |
| each of the other five | 20,000,000 | 20 | 1,000,000 |

**`common_crawl` carries the primary comparison.** Nearly a quarter of the mix
is code, mathematics, arXiv and scanned science PDFs, where these frames
essentially cannot occur. Including them lowers the measured input rate, which
makes the model's output look more amplified — bias in favour of the finding
this study would most like to report. The web portion is also the closest
analogue both to the blog posts Study 2 generates and to the web text Study 1
measured.

**The whole mix is the secondary comparison**, because it is literally what the
model saw. It is computed as the token-share-weighted average of the six subset
rates rather than by sampling the mix directly, which would spend most of the
draw on `common_crawl` anyway. The shares above are in tokens and the rates are
per word, and tokens per word differ between prose and code, so the weighted
figure is an approximation and is reported as one.

200 million words gives the rarest frame in Study 1's American rates — F02, at
about 0.5 per million — on the order of a hundred hits, and the composite tens
of thousands. 20 million words per minor subset is enough to place each of them
well below the web rate, which is all the secondary figure needs.

## How the draw works

Deterministic given seed 20260925, the same constant the topic draw uses, with
a separate random stream per subset:

1. List the subset's parquet files from the repository, sorted by path.
2. Draw the file count above without replacement.
3. Read each drawn file from its first row, counting words with
   `python/framecount.word_count`, and stop at the file's quota. A file
   shorter than its quota contributes what it has and the shortfall is made up
   by drawing the next file in the shuffled order.
4. Record, per file: path, rows read, words counted, and hits per frame.

A per-file quota takes a contiguous block rather than a random sample within
the file, because parquet row order is not random and a random-row draw would
mean reading the whole file anyway. Drawing 200 files rather than a handful of
large ones is what limits how much any one crawl segment can matter. The
recorded file list and row counts make the draw checkable.

## What is not done

No filtering, no deduplication, no quality screening, no language
identification, and no removal of boilerplate. The corpus is counted as the
model received it, which is the same rule Study 2 applies to generated text.
Any cleaning would be a judgement about what counts as the training data's
register.

## Counting

`python/framecount.py`, unchanged and frozen, the same module that counts
Study 2's generated text. All fifteen frames, including F06, which a free
GloWbE account could not search. The denominator is the same word definition on
both sides, so the input-output comparison is on one footing. Comparisons back
to Study 1 use the fourteen frames it could count and carry the denominator
caveat in `docs/frame-mapping.md`.

## The prediction this tests

| | Output rate against input rate |
|---|---|
| Volume alone explains the register | approximately equal |
| Amplification | output materially higher |

Equality would be a result too, and a duller one: it would say the model writes
like its training data and that the register question belongs to whoever
assembled the corpus.
