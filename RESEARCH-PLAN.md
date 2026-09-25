# Research plan

Status: Study 1 is collected and analysed. It was registered on OSF at
<https://osf.io/48wjn> on 21 September 2026 before any count was retrieved,
with two declared deviations since; the result is in `docs/study1-results.qmd`.
Study 2 is registered at <https://osf.io/qjgtc> with its generation protocol
and counting layer; nothing has been generated yet. Study 3 has not started. The literature
review is as complete as it will get — two of the cited papers cannot be
obtained, and the wording that depended on them is settled by decision rather
than by reading. Completion criteria are in `SCOPE.md`.

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

  The release matters. Olmo 3's stage-1 pretraining used `dolma3_6T-mix-1025`,
  published as `allenai/dolma3_mix-6T-1025`, so one checkpoint pairs with one
  named corpus. OLMo 2 does not work that way: its mix draws on DCLM, Dolma,
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

All three studies ship, decided 4 September 2026. `SCOPE.md` sequences them as
gated phases: Study 1 alone, then the counting layer, then Studies 2 and 3
together on OLMo, then the closed models as an optional widening.

- The Dolma sampling frame. Blocks Study 3's registration and nothing else, so
  it can be decided while Study 1 is being collected.
- Whether a preprint follows the article. Free, and worth it only if the result
  is one people will want to cite. Decided after there is a result.
