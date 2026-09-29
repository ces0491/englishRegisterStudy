# Research plan

Status: Study 1 is collected and analysed. It was registered on OSF at
<https://osf.io/48wjn> on 21 September 2026 before any count was retrieved,
with two declared deviations since; the result is in `docs/study1-results.qmd`.
Study 2 is registered at <https://osf.io/qjgtc> and Study 3 at
<https://osf.io/ngt3m>. The Dolma 3 sample was drawn on 27 and 28 September and
Study 2's text generated on 28 September; both runs are in
`docs/collection-log.md`, and both studies are analysed and written up in
`docs/study2-3-results.qmd`. A fourth study, locating where the model's excess
enters its training, is designed below and not registered. The literature
behind Studies 1 to 3 is in `docs/literature-notes.qmd`, where two cited papers
could not be obtained and the wording that depended on them is settled by
decision. Prior art on model style, found on 29 September, is listed with
Study 4. Completion criteria are in `SCOPE.md`.

## The question

Are the rhetorical frames characteristic of LLM-generated English specifically
features of **American** web register rather than of English generally?

If they are, it follows that readers of other standard varieties encounter
generated prose as regionally foreign before they encounter it as machine-made,
and that "this reads as AI" is partly a judgement about national register.

## Why it is worth doing properly

Three findings already exist separately and nobody appears to have joined them.

1. LLM output defaults to American English, and models show dialect preference
   toward Standard American English.
2. AI detectors misclassify **non-native** English writing as machine-generated,
   because they penalise restricted linguistic variation (Liang et al. 2023).
3. National varieties of English differ measurably in pragmatic and discourse
   markers, and GloWbE is the standard instrument for showing it.

The gap is between (2) and (3). The detector literature compares native against
non-native writers. It does not compare American against **other native
standard varieties** — British, Irish, Australian, South African. That is where
this sits, and it is a different mechanism: not restricted variation, but a
register mismatch between fluent varieties.

## Design

### Study 1 — the pre-LLM baseline

Do the target frames occur less often in other national varieties of
human-written web English than in American?

- Instrument: GloWbE, blog and general sections held separate.
- Varieties: US, GB, IE, AU, ZA. Any other variety is exploratory.
- Frames: frozen in `data/frames.csv` before querying.
- Outcome: rate per million with exact Poisson intervals, US as reference.
- Hypothesis: directional. Each of GB, IE, AU and ZA has a composite rate below
  US, so a ratio against US below 1.
- Per-frame comparison: exact conditional Poisson intervals on each rate ratio
  against US, within section. Descriptive: 120 ratios, uncorrected, and no
  claim rests on any one of them.
- Composite: Poisson GLMM, `hits ~ frame_id + variety + section +
  (1 | frame:variety) + (1 | cell)` with `offset(log(words))`. Frame is a fixed
  factor because base rates differ by orders of magnitude. The frame-by-variety
  random effect carries each frame's own preference for a variety, shared across
  sections, and the cell-level effect carries the remaining overdispersion. The
  variety ratio is therefore an average over frames of this kind, and its
  interval reflects how much frames disagree.
- Why this model: quasi-Poisson and negative binomial were both run against
  synthetic data with a known ratio first. With frame preferences shared across
  sections, quasi-Poisson's 95% intervals covered the truth 15–16% of the time
  and negative binomial's 77–79%; this model's 93%. With independent noise in
  each cell, all but quasi-Poisson reached 88–91%.
- Inference: Wald intervals and two-sided p-values at 0.05, Holm-corrected
  across the confirmatory set. A variety supports the hypothesis when its ratio
  is below 1 and its Holm-adjusted p is under 0.05.
- Genre control: the same model with `variety:section` added, compared by
  likelihood-ratio test. If p < 0.05, the eight per-section ratios from the
  interaction model are the confirmatory set, and the four common ratios are set
  aside. The split is a partial control — see the register confound under
  Threats — so a common effect across sections is evidence against a pure genre
  explanation rather than proof of its absence. The test ran slightly liberal
  on synthetic data, at 6–12% against a nominal 5%.
- A frame with no hits in any of its ten cells leaves the model and is reported.
- Convergence: bobyqa, then Nelder-Mead. If both fail the analysis stops, and
  anything done instead is a declared deviation. A singular fit is reported
  and kept.
- Robustness: the whole analysis rerun without the two frames marked partial in
  `data/frames.csv` (F10, F13), reported beside the primary result.
- All of the above was fixed before any count existed, and is registered at
  <https://osf.io/48wjn>.
- **What collection changed.** The interface will not split six of the frames
  by section, and will not count F06 at all on a free account, so the
  confirmatory analysis runs on the fourteen countable frames with the sections
  combined, and the registered per-section model becomes a secondary analysis
  on the eight frames that split, and the combined model's intervals use a t
  reference with one degree of freedom per frame less one. Deviation D2 in
  `docs/deviations.md`, filed on OSF. The genre control is the casualty: it now covers eight frames rather
  than fifteen, and not the contrastive family.

**GloWbE's 2012 collection date is the reason to use it.** Any corpus collected
after 2022 contains generated text in unknown proportion, so a "human baseline"
drawn from one is circular. A decade-old corpus cannot be contaminated by the
thing being studied. State this as a design choice rather than a limitation.

### Study 2 — the generated comparison

Do LLM outputs use those frames at rates resembling the American end of Study 1?

- Generate a matched corpus: same genres and topics as the GloWbE blog section,
  several models, temperature and prompt held constant and recorded.
- Prompts must not name a variety or mention style. Asking for "British English"
  measures instruction-following instead of default register.
- Same frames and same intervals. "Same counting" takes work rather than
  assertion: the queries in `data/frames.csv` are in GloWbE's tokenised form,
  with clitics split off (`here 's the thing`, `is n't just`) and punctuation as
  its own token (`it 's not * , it 's`). Counting them in raw generated text
  means either tokenising that text the same way or translating each frame into
  a pattern over raw text. Whichever is chosen is written down and frozen with
  the frames and goes into the registration. An ad hoc mapping would leave the
  two studies measuring different things while appearing to measure the same
  one, and the comparison between them is the study.
- Report per model and per version. This is a moving target and a result about
  one model at one date is all it can be.

### Study 3 — input against output, which is the actual test

A model producing American register proves nothing on its own. If the training
data was overwhelmingly American, a model reproducing that is a model working
correctly, and "American register" is a fact about the corpus rather than about
the model. Volume is the explanation to beat, and beating it needs the input
measured on the same scale as the output.

**The measurement needed is not the training data's dialect composition. It is
the training data's frame rate.** Composition would have to be inferred from
domain TLDs, where `.com` is ambiguous and dominant. The frame rate is directly
countable with the same fifteen patterns used everywhere else, which makes input
and output comparable without anyone having to classify a single document.

- **Primary: Olmo 3 on Dolma 3.** Ai2 publishes the weights, the training code
  and the pretraining corpus. Frame rates can be counted in the corpus and in
  the model's output and set against each other exactly. No other model family
  allows this.

  The release matters. Olmo 3's stage-1 pretraining corpus is published as
  `allenai/dolma3_mix-6T-1025`, so one checkpoint pairs with one named corpus. OLMo 2 does not work that way: its mix draws on DCLM, Dolma,
  Starcoder and Proof Pile II, followed by a midtraining stage on
  Dolmino-Mix-1124, so "count the frames in its training data" would mean
  reconstructing a four-source mixture with stage weights. Study 3's sampling
  frame also has to say whether it covers stage 1 alone, which is 97.5% of the
  budget but not all of it.
- **This is cheaper than it looks, because OLMo is one of Study 2's models.**
  The generation run produces Study 2's open-model output and Study 3's output
  side at once, and both count through the same frame-to-raw-text mapping. What
  Study 3 adds over Study 2 is the Dolma sample and the pass that counts it.
  That is the argument for running them as one phase rather than two.
- Sample Dolma rather than processing it whole. At these rates a few million
  words gives intervals tight enough. **The sampling frame has to be specified
  before the draw and registered with it** — version, subsets, how shards are
  drawn, how much text, and the seed. "A few million words" is a target, not a
  sampling frame, and the study cannot be registered on it.
- **Secondary: the closed models.** GPT, Claude and Gemini output can be
  measured; their inputs cannot. For those the volume confound stays open and
  the write-up says so rather than implying otherwise.

The prediction that distinguishes the two explanations:

| | Output frame rate vs Dolma frame rate |
|---|---|
| Volume alone | approximately equal |
| Amplification | output materially higher |

Amplification is the claim in *The Average Human Problem* — that a model writes
like the centroid of its training data rather than a sample from it, so the
majority register is over-produced rather than reproduced in proportion. Study 3
is what turns that from an assertion into a number, and it is the finding worth
publishing. Equality would be a real result too, and a duller one.

### Study 4 — where the excess enters

*Designed 29 September 2026. Not registered: nothing below has been generated
or counted.*

The exploratory results of Studies 2 and 3 raise a narrower question. On the
contrastive frames, Olmo 3's base model runs at about five times the rate of
its stage-1 web input, and the instruct model at about three times the base
model's (`docs/study2-3-results.qmd`, exploratory). Olmo 3 reached its final
form in six stages: stage-1 pretraining, midtraining, long-context training,
supervised fine-tuning (SFT), preference tuning (DPO) and reinforcement
learning with verifiable rewards (RLVR). Ai2 released a checkpoint after each
and the data for each, which makes it possible to set every stage's input rate
against the rate of the checkpoint it produced, and so to locate where the
excess enters.

Each explanation on offer predicts a different contrast. They are not
exclusive, and the design measures all of them.

| Explanation | Predicts |
|---|---|
| Pretraining amplifies by itself | the stage-1 checkpoint above its stage-1 input |
| Midtraining's synthetic text carries it | the midtraining mix above stage 1, and the rate rising across midtraining |
| Fine-tuning data carries it | SFT responses rich in the frames, and the SFT checkpoint above the base |
| Preference tuning pushes it | chosen responses above rejected ones, and DPO above SFT |
| Reinforcement learning pushes it | the final model above the DPO checkpoint |

The last is the argument in
[Salvaggio (2026)](https://mail.cyberneticforests.com/its-not-just-data-its-post-training/),
which presents no measurement.

**Output side.** Generation under Study 2's protocol (the same 4,000 titles,
temperature 1.0, top-p 1.0, 1,024 new tokens) in a new seed namespace, from
each checkpoint:

| Checkpoint | Revision | Prompt |
|---|---|---|
| End of stage 1 | `stage1-step1413814` (`373bad25`) | raw, as Study 2's base |
| End of midtraining | `stage2-step47684` (`c3c800dc`) | raw |
| Final base | `main` (`a81bae42`), Study 2's revision | raw |
| SFT | `allenai/Olmo-3-7B-Instruct-SFT` | chat template |
| DPO | `allenai/Olmo-3-7B-Instruct-DPO` | chat template |
| Final instruct | `6e5971d9`, Study 2's revision | chat template |

The final base and final instruct are regenerated so that every arm is new
data, and Study 2's text for them becomes a replication check. The three chat
templates differ only in how they treat an empty tool list, so with no tools
they should render the same default system prompt; the pre-flight confirms the
renders.

**Input side.**

- Stage 1: Study 3's counts, reused as registered.
- Midtraining, `allenai/dolma3_dolmino_mix-100B-1025`: each source directory
  sampled the way Study 3 sampled Dolma 3, the synthetic categories (reasoning
  traces, instruction data, QA rewrites) reported separately, and a mix rate
  weighted by the card's token shares.
- SFT, `allenai/dolci-instruct-sft`: the assistant turns of its 2,152,112
  conversations, by `source_dataset`, with the GPT-4.1 WildChat responses
  reported separately.
- DPO, `allenai/dolci-3-instruct-dpo-with-metadata`: chosen and rejected
  responses from its 260,000 pairs. The paired difference is the direction
  preference tuning pushes, broken down by `chosen_model` and
  `rejected_model`.
- Not counted: the long-context mix, two-thirds of which is midtraining data,
  and the RLVR set, `allenai/Dolci-Instruct-RL-7B`, which holds 169,964
  prompts with reference answers and none of the model's responses. RLVR is
  measured on the output side only.

**Outcome.** The contrastive family, F06 to F09, with the partial F10 added in
a sensitivity run and the fifteen-frame composite reported alongside. The
family is chosen because Studies 2 and 3 found the excess there, and the
registration will say so: the hypotheses come from their exploratory results
and are tested on data that did not exist when those results were seen.

**Analysis.** A family of four frames is too few to serve as the unit of
replication the way frames did in Studies 1 to 3. Texts and documents can. The
proposal is a negative binomial model of each text's or document's contrastive
hits, offset by log(words), with one contrast per explanation and Holm across
them. Its interval coverage is checked by simulation before registration, as
`R/calibrate-composite.R` did for Study 1's model. That check matters here:
in Study 1's calibration a negative binomial model covered the true ratio only
77-79% of the time. There the unit was the frame-by-variety cell and the model
ignored frames' shared preferences; with texts as the unit the failure may not
carry over, and the simulation is how to find out.

**A natural experiment, if the compositions support it.** Ai2 also released
three midtraining runs started from the same stage-1 checkpoint at 2T tokens,
each on a different mix, as branches `stage2-step47684-mix-gen-mc-only-from-2T-ckpt`,
`stage2-step47684-mix-math-code-reasoning-web-from-2T-ckpt` and
`stage2-step47684-mix-round5-from-2T-ckpt`. The base model's card describes
them as a Gen-QA mix, a math-code-thinking mix and the final Round 5 mix. With
the same start and the same budget, generating from all three would isolate
what the midtraining mix does, provided their synthetic prose content differs.
Their compositions need confirming from Table 7 of the Olmo 3 paper
([arXiv 2512.13961](https://arxiv.org/abs/2512.13961)) first.

**Threats.**

- The step from base to SFT changes the prompt format as well as the weights,
  as it did in Study 2.
- The end-of-stage-1 checkpoint may write less fluently than the final model,
  and fluency alone could move frame rates. The natural experiment is the
  check.
- Seeds fix sampling requests but not exact text (Study 2's trial).
- RLVR's own training text is never observed, so its effect is the difference
  between the DPO checkpoint and the final model and nothing finer.
- One 7B model family, one prompt and fifteen frozen frames: the limits of
  Studies 2 and 3 carry over.

**Prior art.** [Reinhart et al. (2025)](https://doi.org/10.1073/pnas.2422455122)
found model style further from human style after instruction tuning than
before, in Llama 3 and GPT-4o.
[Lin et al. (2024)](https://arxiv.org/abs/2312.01552) found alignment tuning
shifts mostly stylistic tokens.
[Li et al. (2026)](https://arxiv.org/abs/2605.27878) traced OLMo 32B's base,
SFT, DPO and RLVR checkpoints against human fiction and found post-training
compresses stylistic variation, measuring outputs only. What Study 4 adds is
the input side at every stage, the three pretraining stages, and the
constructions readers flag.

**Order of work.** The choices under *Open decisions* are settled first. Then
the code (generation by revision, counters for the three datasets), then a
listing and pre-flight that count no frames, then the registration, pinned to
that commit, then the runs. Study 4 is optional, and the article on Studies 1
to 3 does not wait for it.

### Deliberately out of scope

Whether readers of different varieties actually judge texts differently. That
needs human subjects and an ethics process, which an unaffiliated project does
not have. Study 1 and 2 together support the register claim; they do not
establish the perception claim, and the write-up must not imply otherwise.

## Threats to validity

- **Frame selection.** Fifteen frames chosen from intuition about what LLMs
  overproduce. Freezing them before querying controls for post-hoc selection,
  not for the possibility that they were the wrong frames. Pre-register.
- **Register confound.** "American vs British" could be "blogs vs broadsheets".
  The blog/general split within variety is the control, and it is exposed in the
  interface — Westphal (2024) reports rates by section for nine components. It is
  also a weak control: Murphy (2025) abandoned the split, reporting that Biber,
  Egbert & Davies (2015) found the two categories overlap too much to be useful,
  and Westphal (2024) cites Davies & Fuchs (2015) as holding that a clean
  distinction is not possible. Neither original has been read, so the overlap
  finding is held as Murphy's report of it. Westphal's own counts nonetheless
  put both eh and huh higher in the blog section than the general one, so the
  split carries signal even if the categories are impure. Report the section
  term as reducing genre confounding, never as eliminating it.
- **Lexicalisation ceiling.** Only fixed frames are countable. The stronger
  claim is about density and near-obligatory use, and the composite rate is a
  weak proxy for it. Do not overstate what the composite shows. This ceiling is
  a consequence of working through the web interface, which exposes no sentence
  or document structure. Buying the full-text release would lift it and widen
  the frame set; the study is costed at zero instead, and this is the main thing
  that buys.
- **GloWbE country assignment** is by web domain and site location, which is a
  proxy for author nationality rather than a measure of it. Murphy (2025)
  estimates from a spelling test on `color`, `tumor` and `neighbor` that 10-15%
  of writers in the GB and US components are non-nationals. That biases toward
  the null, so a difference found here is understated rather than manufactured.
- **Study 2 has no ground truth** for what "American-like" means beyond Study 1
  itself, so the two studies are not independent.
- **Training data volume** is the confound that would otherwise sink the whole
  argument, and Study 3 exists to answer it. It remains unanswered for every
  closed model, which is a limit on how far the secondary results can be pushed.
- **OLMo is not the model anyone reads.** Study 3 buys a clean comparison at the
  cost of measuring a model with little real-world readership, and the
  generalisation from OLMo to GPT or Claude is an argument rather than a result.

## Output, and what "properly" means without a journal

The aim is a reproducible public analysis and an article, not a submission. That
removes the venue, the article processing charge and a review cycle that would
have run six to eighteen months, over which the models being measured would have
been replaced.

It removes none of the rigour. Every reason for pre-registering, freezing the
frames, reporting intervals and stating the threats holds regardless of who
publishes it. The reader is the constraint, not a reviewer.

What ships:

- This repository, public, with the counts, the code and the frozen frame list,
  so anyone can rerun it.
- An OSF pre-registration, made before the data is collected. Free, open to
  unaffiliated researchers, and it is most of what makes a frame set chosen from
  intuition credible.
- The article, on the blog.
- A preprint only if the result warrants being citable. Optional, free, and a
  decision for after there is a result.

## What it costs

| Item | Cost |
|---|---|
| GloWbE queries | free account; rate-limited, so Study 1 spreads over days |
| GloWbE full text | not bought: a few hundred dollars from corpusdata.org, academic or non-academic licence. Would lift the lexicalisation ceiling |
| Dolma sample | free; stream from Hugging Face rather than pulling 3T tokens |
| Dolma frame counting | Modal, CPU fan-out over shards; cheap enough to be noise |
| OLMo inference for Study 2 and 3 | Modal GPU, batch, a few hours at most |
| Closed-model generation | the only line that scales; optional |
| Study 4 generation and counting | Modal: six generation runs the size of Study 2's conditions, and CPU counting of three public datasets; optional |
| OSF pre-registration, preprint | free |

Modal's monthly free credits cover the compute comfortably, and it suits this
better than Colab: the work is batch rather than interactive, and a Dolma pass
is a fan-out over shards rather than something to babysit in a notebook session.

Sizing: a frame at roughly 50 occurrences per million words needs about two
million words to accumulate a hundred hits, which is where the interval gets
tight enough to report. That is under three million output tokens per model.
Open-weight models on Modal make it free; closed models turn it into a real if
small bill. Check current per-token pricing rather than trusting a figure here.

The remaining cost is time, and the literature review is the largest item.

## Before any more code

1. **Read the literature properly.** Done for Liang et al. (2023), Murphy (2025)
   on `please` and Westphal (2024) on `eh`. Neither GloWbE paper pre-empts the
   operationalisation: between them they omit AU, IE and ZA, and neither puts an
   interval on a cross-variety rate comparison. Biber, Egbert & Davies (2015)
   and Davies & Fuchs (2015) are both out of reach — paywalled, with no
   institutional route and no reachable copy — so what they say reaches this
   study only through the two papers that cite them, and the write-up says so
   wherever it matters. Notes and full citations in
   `docs/literature-notes.qmd`.
2. **Pre-register, once per study.** OSF takes registrations from unaffiliated
   researchers at no cost. Frames, varieties, sections and analysis fixed in
   advance is most of what makes this credible given the author picked the
   frames from intuition.

   What pre-registration protects is each study's design being fixed before
   that study's own data exists, so three registrations serve it better than
   one. Study 1 registered on 21 September 2026 at <https://osf.io/48wjn>, on
   the Secondary Data template — GloWbE was collected in 2012 and no count
   from it had been looked at. Study 2 registers
   before any text is generated, carrying the generation protocol and the
   frame-to-raw-text mapping. Study 3 registers before the Dolma sample is
   drawn, carrying the sampling frame.

   Combining them would hold Study 1 behind decisions only the later studies
   need, and the mapping in particular is better written after the grid has
   been collected by hand, because that is how the interface's matching
   behaviour is learned.
3. **Confirm the blog/general split** is queryable per variety. Answered: it is,
   and Westphal (2024) reports section word counts for nine components. What
   remains is one live session to check the click path for holding a section
   constant across all twenty countries, and to read the limit off the account.
   The limit is unlikely to bind either way: the grid is fifteen searches, or
   thirty if the two sections need separate passes. The free-tier figure is not
   published anywhere reachable — english-corpora.org blocks automated access —
   so it has to come from the account itself.

## Open decisions

Studies 1 to 3 ship, decided 4 September 2026, and are reported in one
article, decided 29 September. `SCOPE.md` sequences the work as gated phases:
Study 1 alone, then the counting layer, then Studies 2 and 3 together on OLMo,
then two optional additions, the closed models and Study 4.

- Study 4, before its registration is drafted:
  - Whether to generate from the checkpoints at all. Counting the midtraining
    and fine-tuning data was the part first agreed, but without each stage's
    output those counts cannot say whether a stage amplifies what it was
    given. Recommended: include them.
  - The outcome: the contrastive family (F06 to F09) as proposed, or the
    fifteen-frame composite as in Studies 1 to 3.
  - The unit and model: texts and documents under a negative binomial model,
    subject to the simulation check.
  - Regenerating the final base and instruct arms (recommended) or reusing
    Study 2's text.
  - The SFT count: all 2,152,112 conversations, or a sample per source.
  - The natural experiment, in or out, once Table 7's compositions are read.
- Whether a preprint follows the article. Free, and worth it only if the result
  is one people will want to cite. Decided after there is a result.
