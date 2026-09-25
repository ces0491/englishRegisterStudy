# OSF registration — Study 3

Text for OSF's **Secondary Data Preregistration** template (version 3), in the
template's order, the same template Study 1 used: the corpus exists, is public,
and has not been observed. The answers are plain text because OSF does not
render Markdown.

What this registers is `docs/dolma-sampling-frame.md` and the counting layer in
`docs/frame-mapping.md` at the commit this registration links to.

Suggested title: *Does a language model over-produce its training data's
register? Frame rates in Dolma 3 against Olmo 3 output*

---

## Study Information

### Research questions *(required)*

1. How often do the fifteen frozen rhetorical frames occur in the corpus Olmo
   3 was trained on?
2. Does Olmo 3's own prose use them at the same rate as its training data, or
   at a higher one?

### Hypotheses *(required)*

H1 (directional). The composite frame rate in the confirmatory generated
condition (Olmo 3 base at unmodified sampling, registered at
https://osf.io/qjgtc) is higher than the composite rate in the web portion of
its stage-1 pretraining corpus.

Rationale. A model producing American register proves nothing on its own. If
the training data was full of these frames, a model reproducing them is a model
working correctly, and the register is a fact about the corpus rather than
about the model. The claim worth testing is amplification: that a model writes
like the centroid of its training data rather than like a sample from it, so a
majority register is over-produced rather than reproduced in proportion.

The two outcomes are both informative:

  output rate ~ input rate     volume alone explains the register
  output rate > input rate     amplification

Equality is a real result and a duller one. It would place the register
question with whoever assembled the corpus rather than with the model.

---

## Data Description

### Datasets used *(required)*

allenai/dolma3_mix-6T-1025, the stage-1 pretraining mix for Olmo 3: 5.93
trillion tokens over 3.87 billion documents, stored as parquet, published by
Ai2. Its composition, as published: common_crawl 4.51T tokens (76.07%),
olmocr_science_pdfs 805B (13.57%), stack_edu 409B (6.89%), finemath-3plus 151B
(2.56%), rpj-proofpile-arxiv 50.9B (0.86%), dolma1_7-wiki-en 2.51B (0.04%).

Stage 1 only. It is 97.5% of Olmo 3's pretraining budget and one named
published corpus. Later stages are excluded and the write-up says so.

The other side of the comparison is the generated text from Study 2, produced
under the protocol registered at https://osf.io/qjgtc.

### Data availability *(required)*

The dataset is publicly available.

### Data access

Hugging Face, no licence application, no fee. The full mix is about 4 TB, so
this study samples it rather than downloading it whole.

### Data identifiers

https://huggingface.co/datasets/allenai/dolma3_mix-6T-1025 — the model it
trained: https://huggingface.co/allenai/Olmo-3-1025-7B

### Access date *(required)*

No document has been drawn. The sample is drawn after this registration is
submitted, and the date of the draw is recorded with the counts.

### Data collection procedures *(required)*

The corpus was assembled by Ai2 and released with Olmo 3. How it was built is
their documentation's business; this study takes it as given and counts what
is in it.

The sample, deterministic given seed 20260925 with a separate random stream per
subset:

  common_crawl              200,000,000 words   200 files   1,000,000 per file
  each of the other five     20,000,000 words    20 files   1,000,000 per file

1. List the subset's parquet files from the repository, sorted by path.
2. Draw the file count above without replacement.
3. Read each drawn file from its first row, counting words with
   python/framecount.word_count, and stop at the file's quota. A file shorter
   than its quota contributes what it has, and the shortfall is made up by
   drawing the next file in the shuffled order.
4. Record, per file: path, rows read, words counted, and hits per frame.

A per-file quota takes a contiguous block rather than a random sample within a
file, because parquet row order is not random and a random-row draw would mean
reading the whole file anyway. Drawing 200 files rather than a handful limits
how much any one crawl segment can matter, and the recorded file list makes the
draw checkable.

No filtering, deduplication, quality screening, language identification or
boilerplate removal. The corpus is counted as the model received it, which is
the rule Study 2 applies to generated text.

### Data collection procedures documentation

None uploaded. docs/dolma-sampling-frame.md in the linked repository.

### Codebook

None exists for a corpus sample. The variables are defined under Measured
variables below.

---

## Variables

### Manipulated variables

None. Observational.

### Measured variables *(required)*

Outcome. hits: matches for one frozen frame in one source.

Exposure. words: the source's word count, entered as log(words) as an offset.
A word is a token containing at least one word character, the same definition
on both sides of the comparison.

Predictor. source, categorical: the six Dolma 3 subsets, and the four generated
conditions from Study 2. The primary contrast is between the confirmatory
generated condition and common_crawl.

The fifteen frozen frames are as registered for Study 1 at https://osf.io/48wjn
and unchanged. All fifteen are counted here, F06 included; comparisons back to
Study 1 use the fourteen a free GloWbE account could search.

### Missing data

None is possible. A frame with no matches in a source is a zero, not a gap. A
frame with no matches in any source is removed from the model and reported.

### Unit of analysis

The frame x source cell: 15 frames by 10 sources.

### Statistical outliers

None defined and none removed. A file whose text is unusual is part of the
corpus the model was trained on.

### Sampling weights

The whole-mix rate, which is the secondary comparison, is the token-share-
weighted average of the six subset rates, using the published shares above.
The shares are in tokens and the rates are per word, and tokens per word differ
between prose and code, so that figure is an approximation and is reported as
one. The primary comparison uses no weights.

---

## Knowledge of Data

### Prior Publication/Dissemination

None. The author has not published or presented any work using Dolma.

### Prior knowledge *(required)*

The author (sole author) has not drawn, read or counted any part of Dolma 3,
and has seen no frame count from it.

Study 1 is complete and its results are public at https://osf.io/48wjn and in
the repository: American web English in 2012 used these frames roughly 1.5 to 2
times as often as the other four national varieties. Study 2's protocol is
registered at https://osf.io/qjgtc. Whether Study 2's text has been generated
at the time of this submission is stated in the repository's collection log;
the sampling frame above was fixed before either.

---

## Analyses

### Statistical models *(required)*

One Poisson generalised linear mixed model over the Dolma 3 subsets and the
generated conditions:

    hits ~ frame_id + source + (1 | frame:source)
           offset: log(words)

frame_id fixed absorbs base rates that differ by orders of magnitude between
frames. The frame-by-source random effect carries each frame's own preference
for each source, so a source effect is an average over frames. One observation
per frame and source, so no separate observation-level term, as in Study 1's
combined-sections model and Study 2's.

Intervals and p-values use a t reference with degrees of freedom equal to the
number of frames less one, as in Studies 1 and 2.

H1 is tested by one contrast: the confirmatory generated condition against
common_crawl.

### Effect size

No minimum effect of interest is specified. The ratio and its interval are what
the write-up interprets, not significance alone.

### Statistical power

No formal power analysis; the sample size is set by the sampling frame rather
than by a power calculation. At Study 1's American rates, 200 million words
gives the rarest frame on the order of a hundred hits and the composite tens of
thousands, so the interval on the input rate is narrow relative to any
difference worth calling amplification.

### Inference criteria

95% intervals and a two-sided p-value on the primary contrast, uncorrected,
because it is one test.

Three secondary contrasts — the other three generated conditions against
common_crawl — are Holm-corrected within that set. The whole-mix comparison is
reported with its interval and labelled as resting on the token-share
approximation above.

### Assumption Violation/Model Non-Convergence

As registered for Study 1: a frame with no hits in any source leaves the model
and is reported; the fit tries bobyqa, then Nelder-Mead, and stops if both
fail, with anything done instead declared as a deviation; a singular fit is
kept and reported.

### Reliability and Robustness Testing

The analysis is rerun without the two frames marked partial in data/frames.csv
(F10, F13), which match text outside the construction they stand for, and the
two results are reported together.

Per-subset rates are reported separately, so a reader can see how far the
comparison depends on the choice of common_crawl as the primary input.

### Exploratory analysis

Reported separately and labelled exploratory:

- Per-frame and per-family input and output rates, and whether the frames the
  model most over-produces are the ones Study 1 found most American.
- Variation between the drawn files, as a check on how much one crawl segment
  can move the input rate.
- The instruction-tuned conditions against the base ones, as a measure of what
  post-training adds on top of whatever the corpus supplies.
