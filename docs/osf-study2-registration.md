# OSF registration — Study 2

Registered at <https://osf.io/qjgtc> on 25 September 2026, before any text was
generated, pinned to commit `1196f8d`. This is the text as submitted.

Text for OSF's **OSF Preregistration** template (version 4), in the template's
order. Fields marked *required* cannot be left blank. The answers are plain
text because OSF does not render Markdown.

What this registers is `docs/generation-protocol.md` and
`docs/frame-mapping.md` at the commit this registration links to, together
with the frozen frames in `data/frames.csv` and the topics in
`data/topics.csv`.

Suggested title: *Does a language model's default register resemble American
web English? Generation protocol and analysis plan*

---

## Overview

### Research questions or hypotheses *(required)*

RQ1. Do the frozen rhetorical frames occur in a language model's unprompted
prose at rates resembling the American end of the national-variety spread
measured in Study 1?

All fifteen frames are counted in the generated text. The comparison against
Study 1 uses fourteen of them, because a free GloWbE account cannot search F06
("it 's not * , it 's") at all: it is seven tokens and the interface caps a
search at five. That is deviation D2 on Study 1's registration.

H1 (directional). Over those fourteen frames, the model's composite rate is
higher than the rate of each non-American variety measured in Study 1: GB, IE,
AU and ZA. Five tests in total, the fifth being the comparison against
American web English, for which no direction is predicted.

Rationale. Study 1 found that American web English in 2012 used these frames
between roughly 1.5 and 2 times as often as the other four varieties
(GB 0.69, IE 0.54, AU 0.66, ZA 0.50 against US, each with a Holm-adjusted p
below 0.0001). If generated prose reads as regionally foreign to readers of
other varieties before it reads as machine-made, model output should sit at
the American end of that spread rather than in the middle of it.

RQ2. Does the instruction-tuned model differ from the base model, and does
truncated sampling differ from unmodified sampling? No direction is predicted
for either. These are registered as comparisons rather than hypotheses.

### Foreknowledge of data or evidence *(required)*

Data does not yet exist. No part of the data that will be used for this
analysis plan exists, and no part will be generated until after this plan is
registered.

### Explanation of foreknowledge and managing unintended influences

The generated text does not exist. The comparison target does: Study 1's
counts were collected between 22 and 25 September 2026, analysed, and are
public at https://osf.io/48wjn and in the repository, and the author has seen
them in full. They are stated in the hypothesis above rather than left
implied.

Two things follow. The frames were frozen before Study 1 was collected and are
unchanged here, so the frame set cannot have been chosen to suit either
result. The counting layer this study uses was written and frozen before any
text was generated, and its behaviour was checked against GloWbE's interface
rather than against any model output.

---

## Research Design

### Study type *(required)*

Non-randomized study. Descriptive study.

### Intention for causal interpretation

No causal relationship inferred: this study is not intended to inform a causal
relationship. Whether a model's register is explained by the frequency of
these frames in its training data is Study 3's question, and is registered
separately.

### Blinding of experimental treatments *(required)*

No blinding is involved. The subjects are model checkpoints, and the outcome
is counted by a frozen script rather than coded by a person.

### Study design *(required)*

Four conditions, fully crossed: two checkpoints by two sampling settings.

  checkpoints    allenai/Olmo-3-1025-7B (base)
                 allenai/Olmo-3-7B-Instruct (instruction-tuned)
  sampling       unmodified: temperature 1.0, top-p 1.0
                 deployment: temperature 0.7, top-p 0.9

Olmo because Ai2 publishes both the weights and the pretraining corpus, which
is what allows Study 3 to count the same frames in the model's input. Olmo 3's
stage-1 pretraining used dolma3_6T-mix-1025, released as
allenai/dolma3_mix-6T-1025, so one checkpoint pairs with one named corpus.

Base and instruct are reported apart because they answer different questions:
the base model shows what the pretraining corpus produces, the instruction-
tuned model is closer to the prose people read, and the difference between
them is what post-training adds.

The same 4,000 topics serve every condition, so topic is held constant across
models and settings. The exact revision of each checkpoint is recorded with
the run.

The confirmatory condition is the base model at unmodified sampling. The other
three are registered and all four are reported, whatever they show.

### Randomization

No assignment of subjects. Two draws are random and both are seeded: the topic
sample (seed 20260925, in python/sample_topics.py) and the sampling of tokens
during generation (one seed per generation, recorded with the text).

---

## Sampling

### Data collection procedures *(required)*

Topics. 4,000 titles of GloWbE blog pages, drawn by python/sample_topics.py
from the corpus's published page metadata and committed as data/topics.csv.
Blog-section pages only, from the five varieties in Study 1. A title is
refused if it does not decode cleanly or carries fewer than four or more than
eighteen word tokens. Where a title contains a separator the side carrying
more words is kept, because the site name sits sometimes before it and
sometimes after. One title per domain, duplicates within a variety dropped,
800 topics per variety, shuffled and numbered. Topics come from the corpus so
that a difference in frame rates cannot be a difference in subject matter.

Prompt. One template, identical across conditions:

    Write a blog post titled: {topic}

The prompt names no variety, no register and no style: asking for "British
English" or for "a punchy blog post" would measure instruction-following
rather than default register. For the instruction-tuned model the prompt is
the user turn, with the checkpoint's own chat template and no system prompt.
For the base model it is the raw prefix.

Generation. One generation per topic per condition, maximum 1,024 new tokens,
no repetition or frequency penalty. Every generation is kept with its
condition, topic id, checkpoint revision, sampling settings, seed and raw
text.

Counting. python/framecount.py, frozen with this registration and specified in
full in docs/frame-mapping.md: text is normalised and lowercased, clitics and
punctuation are split into their own tokens, a hyphenated word stays one
token, and each frozen query is matched as a token sequence in which * matches
exactly one token. Three of those behaviours were checked against GloWbE's own
interface rather than assumed.

### Sample size *(required)*

About 2 million words per condition, so about 8 million in total. 4,000
generations per condition at roughly 500 words each reaches that.

### Sample size rationale

At the American rates Study 1 measured, a mid-frequency frame occurring around
20 times per million words lands about 40 hits in 2 million words, and the
composite across the frames lands in the hundreds, so the interval on the
composite is tight enough to place the model within or outside the range
Study 1 measured. The rarest frames will carry wide intervals, as they do in
Study 1.

### Starting and stopping rules *(required)*

Generation starts after this registration is submitted. A condition stops when
its text reaches 2 million words as counted by python/framecount.py. If 4,000
generations fall short of 2 million words, topics are reused in topic_id order
with the seed advanced, and the write-up reports how many generations each
condition needed. No condition is extended or shortened after its counts have
been looked at.

---

## Variables

### Manipulated variables *(required)*

Checkpoint: base or instruction-tuned, as named above.

Sampling setting: unmodified (temperature 1.0, top-p 1.0) or deployment
(temperature 0.7, top-p 0.9).

These cross to four conditions. Nothing else differs between them: the same
topics, the same prompt template, the same maximum length, the same counting.

### Measured variables *(required)*

Outcome. hits: the number of matches for one frozen frame in one condition's
generated text.

Exposure. words: the condition's word count, entered as log(words) as an
offset, so the model is of rates. A word is a token containing at least one
word character.

Predictors, categorical, with treatment coding:

  source     the five GloWbE varieties from Study 1 (US, GB, IE, AU, ZA) and
             the four generated conditions. US is the reference.
  frame_id   F01 to F15, a fixed factor absorbing base-rate differences
             between frames.

The fifteen frozen frames are as registered for Study 1 at https://osf.io/48wjn
and unchanged: F01 "here 's the thing", F02 "here 's the * part", F03 "here 's
what", F04 "the thing is", F05 "what 's interesting is", F06 "it 's not * , it
's", F07 "it 's not just", F08 "not just * but", F09 "is n't just", F10 "not *
, but *", F11 "that 's the whole point", F12 "which is the point", F13 "and
that 's", F14 "turns out", F15 "the real question is".

All fifteen are counted here, F06 included, because raw text has no
five-token limit. Study 1 covers fourteen, so every comparison against it uses
those fourteen and says so.

### Indices *(required)*

The composite is not a sum or a weighted index. It is the source effect in the
model below: the ratio of one source's frame rate to the American rate,
averaged over frames. No frame is weighted above another, and no frame is
dropped for being rare.

---

## Analysis Plan

### Statistical models *(required)*

One Poisson generalised linear mixed model, fitted by maximum likelihood
(Laplace approximation, lme4::glmer), over Study 1's counts and this study's
counts together:

    hits ~ frame_id + source + (1 | frame:source)
           offset: log(words)

frame_id fixed absorbs base rates that differ by orders of magnitude between
frames. The frame-by-source random effect carries each frame's own preference
for each source, so a source effect is an average over frames and its interval
reflects how much frames disagree. There is one observation per frame and
source, so a separate observation-level effect would be the same grouping
twice and is not included, exactly as in Study 1's combined-sections model.

The confirmatory model covers the fourteen frames both sides can contribute,
so that a source effect is not partly estimated from frames only one side has.
F06 is counted and reported for the generated conditions, and enters the
comparisons among those four conditions, where every source has it.

Study 1's denominators are GloWbE's own word counts and this study's come from
the counting layer's definition, which docs/frame-mapping.md notes is not the
same quantity. The comparison between the two carries that difference and the
write-up states it.

Intervals and p-values use a t reference with degrees of freedom equal to the
number of frames less one, as in Study 1, because a source effect is
replicated across frames rather than across cells.

H1 is tested by four contrasts: the confirmatory condition against each of GB,
IE, AU and ZA. The fifth comparison, against US, is reported with its interval
and has no predicted direction.

### Transformations *(required)*

None beyond the log link and the log(words) offset, which make the model one
of rates rather than counts. Text is not cleaned, edited or transformed before
counting.

### Inference criteria *(required)*

95% intervals and two-sided p-values, Holm-corrected across the five
comparisons involving the confirmatory condition.

H1 is supported for a variety when the confirmatory condition's rate is above
that variety's and the Holm-adjusted p is below 0.05. A rate below a variety's
with an adjusted p below 0.05 is reported as evidence against H1.

The comparisons among the four conditions (base against instruct, unmodified
against deployment) are registered and reported with intervals, Holm-corrected
within that set of three. Those comparisons use all fifteen frames, since
every generated condition has F06.

Per-frame rate ratios are descriptive, reported with uncorrected exact Poisson
intervals, and no conclusion rests on any one of them.

### Data inclusion and exclusion *(required)*

Nothing is excluded. Refusals, truncated endings, markdown, repetition and
duplicate passages are all counted as generated. Any exclusion rule would be a
judgement about what counts as the model's register, and the register is what
is being measured.

Empty generations are recorded as empty and contribute zero words and zero
hits.

### Missing data *(required)*

None is possible: every generation is kept, and a frame with no matches in a
condition is a zero rather than a gap. A frame with no matches in any source
is removed from the model and reported, as in Study 1.

### Other planned analysis

Reported separately from the confirmatory results and labelled exploratory:

- Per-frame and per-family rates, including which frames drive any difference.
  Study 1 found the announce-the-point family separating varieties most and
  the contrastive family least, and whether generated text follows that
  pattern is worth reporting.
- The relationship between generation length and frame rate.
- Closed models, if they are run at all, reported per model and per version
  and never pooled.

---

## Other

### Context and additional information

This is the second of three studies. Study 1, registered at
https://osf.io/48wjn, measured the frames across five national varieties of
web English in a corpus collected in December 2012, before generated text
could contaminate it. Study 3 will count the same frames in the model's
published training corpus, which is the comparison that distinguishes a model
reproducing its training data's register from a model over-producing it.

Everything is in a public repository:
https://github.com/ces0491/englishRegisterStudy

The work is unaffiliated and unfunded. It is not being submitted to a journal;
the output is the repository and an article. The rigour is unchanged by that.
