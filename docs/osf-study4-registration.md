# OSF registration — Study 4

Text for OSF's **OSF Preregistration** template (version 4), in the template's
order, for filing from the project the other three studies were registered
from. Fields marked *required* cannot be left blank. The answers are plain
text because OSF does not render Markdown, and they contain no angle
brackets, which OSF drops.

What this registers is `docs/study4-protocol.md`, the estimator in
`R/ratio.R` and its calibration in `R/calibrate-ratio.R`, the model in
`R/model.R`, and the pre-flight in `python/preflight_study4.py`, at the
commit this registration links to, together with the frozen frames in
`data/frames.csv`, the counting layer in `python/framecount.py` and the
topics in `data/topics.csv`. The link to that commit goes into the last
answer once the commit exists.

Suggested title: *Where does a language model's excess of rhetorical frames
enter its training? Olmo 3, stage by stage*

---

## Overview

### Research questions or hypotheses *(required)*

RQ. At which stage of Olmo 3's training does its excess of contrastive frames
enter?

Background. Studies 2 and 3 of this project (https://osf.io/qjgtc and
https://osf.io/ngt3m) found, in analysis they registered as exploratory, that
Olmo 3 7B's base model uses the contrastive frames at about five times the
rate of the web text in its stage-1 pretraining data, and that the
instruction-tuned model uses them at about three times the base model's rate.
Olmo 3 was trained in six published stages: stage-1 pretraining, midtraining,
long-context training, supervised fine-tuning (SFT), preference tuning (DPO)
and reinforcement learning with verifiable rewards (RLVR). Ai2 released a
checkpoint after each stage and the data for each.

Two outcomes, co-primary. The contrastive family (frames F06 to F09), as a
rate per word. The composite of all fifteen frozen frames, as the source
effect in the model Studies 2 and 3 used, so that it means what it meant in
Studies 1 to 3.

Hypotheses. Each except H4 is directional, and each is tested on both
outcomes. They are not exclusive: any number of them can hold.

H1. Pretraining amplifies by itself: the checkpoint at the end of stage 1
uses the frames more than its stage-1 input.

H2. Midtraining data carries it: the midtraining data contains the frames at
a higher rate than the stage-1 input.

H3. Midtraining raises the model's rate: the checkpoint at the end of
midtraining uses the frames more than the checkpoint at the end of stage 1.

H4. Instruction data or reasoning traces. Ai2 ran three midtraining mixes
from the same 2T-token stage-1 checkpoint with the same 100B-token budget. By
the Olmo 3 paper's description, the Gen-QA mix keeps web, QA and instruction
data and omits reasoning traces, and the math-code-thinking mix keeps
reasoning traces and omits QA and instruction data. If instruction data
carries the excess, the Gen-QA checkpoint uses the frames more; if reasoning
traces do, the math-code-thinking checkpoint does. Tested two-sided.

H5. Fine-tuning data carries it: the SFT responses use the frames more than
the final base model's output.

H6. Fine-tuning raises the model's rate: the SFT checkpoint uses the frames
more than the final base model.

H7. Preference data pushes it: chosen responses use the frames more than
rejected responses to the same prompts.

H8. Preference tuning raises the model's rate: the DPO checkpoint uses the
frames more than the SFT checkpoint.

H9. Reinforcement learning raises the model's rate: the final instruct model
uses the frames more than the DPO checkpoint.

### Foreknowledge of data or evidence *(required)*

Some data exist and none has been analysed for this plan. The generated text
does not exist and will not be generated until this plan is registered. The
midtraining, SFT and preference datasets are public and no frame has been
counted in them. The stage-1 counts are Study 3's, analysed and public.

### Explanation of foreknowledge and managing unintended influences

The author has seen the results of Studies 1 to 3 in full, including the
exploratory finding this study follows up. The outcomes and hypotheses were
chosen after seeing it, so each hypothesis is tested only on data that did not
exist, or had not been counted, when it was chosen.

Three kinds of data are already known. The stage-1 input is Study 3's
registered sample, reused as counted. Two arms, the final base model and the
final instruct model, are checkpoints Study 2 generated from, and their Study
2 rates are known; this study draws new text from them with seeds from a
namespace no earlier run used. The midtraining, SFT and preference datasets
have been examined only through their cards and file listings, for sizes,
formats, fields and published composition; no document's text has been read
for this study.

Before registering, a pre-flight checked that each new checkpoint loads. Each
scored one public-domain passage, the opening of Pride and Prejudice. All
five loaded, the three runs from 2T through a configuration naming the Olmo 3
architecture, and each scored the passage with a perplexity between 1.17 and
1.26; the passage is famous enough that this shows correct loading and
nothing about fluency. No text was generated from the study's prompts and no
frame was counted. The family estimator's intervals were calibrated on data
Studies 2 and 3 already hold, and none of this study's data; the composite's
model is the one Study 1's calibration checked.

---

## Research Design

### Study type *(required)*

Non-randomized study. Descriptive study.

### Intention for causal interpretation

Limited. A difference between successive checkpoints is the effect of the
training between them, but that training bundles its data with other changes:
the learning-rate schedule and, at the step from base to SFT, the prompt
format. The three midtraining runs from the same 2T-token checkpoint share
their start and their 100B-token budget and differ in their data, so H4 is
the contrast read as an effect of data.

### Blinding of experimental treatments *(required)*

No blinding is involved. The subjects are model checkpoints and training
datasets, and the outcome is counted by a frozen script rather than coded by
a person.

### Study design *(required)*

Output side: nine checkpoints of Olmo 3 7B each generate one text for each of
4,000 topics.

  B1  end of stage 1                  allenai/Olmo-3-1025-7B, branch
                                      stage1-step1413814
  B2  end of midtraining              allenai/Olmo-3-1025-7B, branch
                                      stage2-step47684
  B3  final base                      allenai/Olmo-3-1025-7B, main
  N1  Gen-QA mix from 2T              allenai/Olmo-3-1025-7B, branch
                                      stage2-step47684-mix-gen-mc-only-from-2T-ckpt
  N2  math-code-thinking mix from 2T  allenai/Olmo-3-1025-7B, branch
                                      stage2-step47684-mix-math-code-reasoning-web-from-2T-ckpt
  N3  Round 5 mix from 2T             allenai/Olmo-3-1025-7B, branch
                                      stage2-step47684-mix-round5-from-2T-ckpt
  P1  SFT                             allenai/Olmo-3-7B-Instruct-SFT
  P2  DPO                             allenai/Olmo-3-7B-Instruct-DPO
  P3  final instruct                  allenai/Olmo-3-7B-Instruct

Each is pinned to a commit, listed in docs/study4-protocol.md.

Input side: four sources of training text.

  stage 1       Study 3's registered sample of common_crawl, 200 files
  midtraining   allenai/dolma3_dolmino_mix-100B-1025, 240 million words
                allocated across its 24 sources by their token shares
  SFT           allenai/dolci-instruct-sft, all 2,152,112 conversations
  DPO           allenai/dolci-3-instruct-dpo-with-metadata, all 260,000 pairs

The long-context stage's data is two-thirds midtraining data and is not
counted. The RLVR data holds prompts and reference answers but none of the
model's responses, so RLVR is measured on the output side only.

The nine hypotheses map to nine contrasts: B1 against stage 1 (H1), the
midtraining sample against stage 1 (H2), B2 against B1 (H3), N1 against N2
(H4), the SFT responses against B3 (H5), P1 against B3 (H6), chosen against
rejected DPO responses (H7), P2 against P1 (H8), and P3 against P2 (H9).

### Randomization

No assignment of subjects. Three draws are random and all are seeded: the
topic sample, which is Study 2's (seed 20260925); the sampling of tokens
during generation, one seed per generation from the namespace "study4:"
followed by the arm, recorded with the text; and the draw of midtraining
files, seed 20260929 with one stream per source.

---

## Sampling

### Data collection procedures *(required)*

Generation. Every arm uses Study 2's protocol: the prompt "Write a blog post
titled:" followed by the topic, temperature 1.0, top-p 1.0, at most 1,024 new
tokens, a 2,048-token context, bfloat16 weights, vLLM 0.30.0 with its PyTorch
sampler, transformers 5.17.0 and huggingface_hub 1.33.0. B1 to B3 and N1 to N3
take the prompt raw. P1 to P3 take it as the user turn of their own chat
template, which in all three inserts the same default system prompt (the one
Study 2's deviation S2-D1 describes) and renders byte-identical prompts when
no tools are passed. Every generation is kept with its arm, topic, commit,
settings, seed, prompt, raw text and finish reason.

N1 to N3 declare a pre-release architecture, olmo2-retrofit, which the pinned
libraries do not recognise, and ship no modelling code. Their configuration
otherwise matches Olmo 3's, apart from a sliding window of 4097 against 4096,
which never binds at a 2,048-token context. They are loaded from a local copy
of the weight files their own index lists, with a configuration naming the
Olmo 3 architecture. Each branch also carries a second set of weight shards
that its index does not list, and those are not used.

Midtraining draw. 240 million words, allocated across the 24 sources in
proportion to their shares of the dataset card's token counts, so the pooled
sample is the mix as the model saw it. Within each source, its files at the
pinned commit are sorted by path and ordered by a random key proportional to
compressed size: each file's key is u to the power one over its size, with u
uniform from the seeded stream, and files are taken in descending order of
key. Each file is read from its first document, whole documents at a time,
taking at most 250,000 words from any one file, and reading stops after the
document that brings the source to its allocation. Per file: path, documents
read, words and hits per frame.

SFT. The unit is the conversation; its text is the content of every message
whose role is assistant, joined by newlines.

DPO. The unit is the pair; its two texts are the content of the last message
whose role is assistant in the chosen and in the rejected conversation.

Counting. python/framecount.py, frozen since Study 1 and specified in
docs/frame-mapping.md, counts words and frames in every text. A word is a
token containing at least one word character.

### Sample size *(required)*

Nine arms of 4,000 generations, 36,000 texts. Midtraining: 240 million words
from at least 973 files. SFT: 2,152,112 conversations. DPO: 260,000 pairs.
Stage 1: Study 3's 200 files.

### Sample size rationale

For the family outcome, the calibration in R/calibrate-ratio.R resampled Study
2's texts and Study 3's files. At the final base model's contrastive rate, two
arms of 4,000 texts gave a median 95% interval on their ratio of a factor of
about 1.16 either way, and at a fifth of that rate about 1.35; the pooled
midtraining sample against the stage-1 sample gave about 1.13. The
differences that motivate this study are threefold to fivefold.

For the composite, frames are the replication unit, as in Studies 2 and 3, so
its intervals will be wide wherever frames disagree, as they were there.

### Starting and stopping rules *(required)*

Generation and counting start after this registration is submitted. Each arm
stops at exactly 4,000 generations, one per topic in topic_id order, with no
word target and no reuse of topics. The input data are counted as specified
above, in full where the specification says all. No arm or source is extended
or shortened after its counts have been looked at.

---

## Variables

### Manipulated variables *(required)*

The checkpoint, one of the nine above. Nothing else differs between the
output arms: the same topics, the same prompt text, the same sampling
settings, the same maximum length and the same counting. The raw and chat
prompt formats differ between the base-model arms and the post-trained arms,
as they do in use.

### Measured variables *(required)*

For every unit, its words and its hits on each of the fifteen frozen frames.
A unit is a generated text, a stage-1 file, a midtraining file, an SFT
conversation, or a DPO pair, whose two texts are measured separately.

Outcomes: for the family, each unit's hits summed over F06 "it 's not * , it
's", F07 "it 's not just", F08 "not just * but" and F09 "is n't just"; for
the composite, each frame's hits and words per source, over all fifteen
frames. The frames are as registered for Study 1 at https://osf.io/48wjn and
unchanged. F10 "not * , but *", the contrastive frame marked partial, is left
out of the family and added in a sensitivity analysis.

### Indices *(required)*

The family outcome is a summed rate: a source's total family hits divided by
its total words, every hit counting equally.

The composite is not a sum or a weighted index. It is a source's effect in the
model below, the ratio of its frame rates to another source's averaged over
frames, so no frame is weighted above another, as in Studies 1 to 3.

The midtraining sample is drawn in proportion to its sources' token shares,
so it enters both analyses as one source. Shares are in tokens and rates per
word, so the sample matches the mix's composition only approximately.

---

## Analysis Plan

### Statistical models *(required)*

Family. No model of the counts is fitted. Each source's rate is a ratio
estimator, R = sum of hits over sum of words, with variance n / (n - 1) times
the sum over units of (hits - R * words) squared, divided by the square of
total words: the ratio estimator's linearisation, which assumes independent
units and nothing about the distribution of hits. Two independent sources are
compared as log(R_a / R_b), with standard error the square root of Var(R_a) /
R_a squared plus Var(R_b) / R_b squared, and a Wald interval from the normal
reference. The DPO contrast is paired: its standard error comes from each
pair's linearised contribution to both rates. The code is R/ratio.R.

Before registration, R/calibrate-ratio.R checked these intervals on data
Studies 2 and 3 already hold: across 30 scenarios matching the contrasts, with
2,000 replications each, 95% intervals covered the true ratio between 93.5%
and 95.6% of the time.

Composite. The Poisson generalised linear mixed model Studies 2 and 3 used,
fitted by maximum likelihood (lme4::glmer), over all fourteen sources
together: the nine output arms, the stage-1 sample, the pooled midtraining
sample, the SFT responses, and the chosen and the rejected DPO responses.

    hits ~ frame_id + source + (1 | frame:source)
           offset: log(words)

frame_id fixed absorbs base rates that differ by orders of magnitude between
frames. The frame-by-source random effect carries each frame's own preference
for each source, so a source effect is an average over frames and its interval
reflects how much frames disagree. The fit uses bobyqa and, on a convergence
failure, Nelder-Mead. Each contrast is a difference of two source effects,
with a t reference on degrees of freedom equal to the number of frames less
one; on synthetic grids in Study 1's calibration, that reference covered a
known ratio 92% of the time. The chosen and rejected responses enter as two
sources, so the model ignores their pairing; the family's contrast for H7 is
the paired one. The code is R/model.R.

### Transformations *(required)*

For the family, the log of each ratio of rates, for its interval. For the
composite, the model's log link and log(words) offset, as in Studies 1 to 3.
Text is not cleaned, edited or transformed before counting.

### Inference criteria *(required)*

95% intervals and two-sided p-values, from the normal reference for the family
and the t reference for the composite. Nine contrasts on two outcomes make
eighteen tests, Holm-corrected together.

A hypothesis is supported on an outcome when its ratio is in the predicted
direction and the Holm-adjusted p is below 0.05. A ratio in the opposite
direction with an adjusted p below 0.05 is evidence against it. H4 supports
the explanation its significant direction favours.

### Data inclusion and exclusion *(required)*

Nothing is excluded. Generated text is counted as generated: refusals,
truncated endings, markdown, repetition and empty generations included.
Training text is counted as published, whatever it contains. An empty text
contributes zero words and zero hits.

### Missing data *(required)*

If a pinned checkpoint or dataset revision cannot be downloaded or loaded, its
arm and every contrast that uses it are dropped and reported, and nothing is
substituted.

For the family, if either side of a contrast has no hits, the contrast has no
log ratio: it is reported with its counts and enters the Holm set with a
p-value of 1. For the composite, a frame with no hits in any source leaves the
model and is reported, as in Studies 1 to 3.

### Other planned analysis

Secondary, reported with intervals and no correction:

- The final base model against the end of midtraining, the long-context
  stage, for which no direction is predicted.
- The Round 5 mix from 2T against each of the other two mixes from 2T.
- Each checkpoint against its own stage's data: the end of midtraining against
  the midtraining sample, and the SFT checkpoint against the SFT responses.
- Replication: the final base and final instruct arms against Study 2's text
  from the same checkpoints.
- Midtraining rates by category, and by source where its sample allows (the
  smallest sources get under 400,000 words); SFT rates by source dataset,
  with the GPT-4.1 WildChat responses separately; DPO rates by the models that
  wrote the chosen and rejected responses.
- The family outcome with F10 added.

Exploratory: per-frame rates, and generation length against frame rate, as in
Study 2.

---

## Other

### Context and additional information

This is the fourth study of the project. Study 1 (https://osf.io/48wjn)
measured the frames in five national varieties of web English from 2012,
Study 2 (https://osf.io/qjgtc) in Olmo 3's output, and Study 3
(https://osf.io/ngt3m) in its stage-1 training data.

Everything is in a public repository:
https://github.com/ces0491/englishRegisterStudy

The work is unaffiliated and unfunded. It is not being submitted to a
journal; the output is the repository and an article.
