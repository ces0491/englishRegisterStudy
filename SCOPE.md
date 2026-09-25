# SCOPE — englishRegisterStudy

## Purpose

Measure whether fifteen frozen rhetorical frames occur at different rates in
American web English than in other national varieties, and whether a language
model produces them at a rate its training data does not explain.

## What this covers

All three studies in `RESEARCH-PLAN.md`, through to a published article.

They are sequenced rather than run together, because they are not independent
and the dependencies run one way. The stop condition is the phase gates below:
no phase starts before the one it depends on is finished and frozen.

## Phases

Each study registers before its own data exists, which is what pre-registration
protects. That is three registrations rather than one, and it is what lets
Study 1 start now instead of waiting on decisions only Studies 2 and 3 need.

**A — Study 1, the baseline.** Self-contained. No compute, no infrastructure,
nothing downstream depends on its results.

- [x] OSF registration for Study 1 submitted before any count is recorded,
      carrying the frozen frames, varieties, sections and the analysis as
      written. The Secondary Data template fits: GloWbE was collected in 2012
      and no count from it has been looked at
- [x] Full grid collected by hand from GloWbE, as far as the interface allows
      (deviation D2): the 14 countable frames x 5 varieties with the sections
      combined in `data/counts-combined.csv`, both sections for the 8 frames
      that split in `data/counts.csv`, and the word counts in
      `data/corpus-sizes.csv`
- [x] `Rscript R/analyse.R` runs end to end on the real counts and produces the
      rates, the per-frame ratios against US, the confirmatory composite on the
      combined counts, the partial-frame sensitivity rerun, and the secondary
      per-section analysis with its `variety:section` likelihood-ratio test
- [x] A stranger with a free english-corpora.org account can reproduce every
      count from what is in the repository. Spot-checked on 25 September 2026
      across three cells in different parts of the grid, all matching; F06
      remains uncountable on that tier, which D2 records

**B — the counting layer, and Study 2's registration.** The gate for everything
after it. Studies 2 and 3 both count the frozen frames in raw text, and they
have to count them the same way or the comparisons between the three studies
mean nothing.

It comes after phase A on purpose. The mapping has to reproduce what GloWbE's
interface actually matches, and collecting the grid by hand is how that is
learned.

- [x] The frame-to-raw-text mapping written down and frozen with the frames.
      The queries in `data/frames.csv` are in GloWbE's tokenised form, with
      clitics split off and punctuation as its own token, and none of that
      survives contact with raw model output. `docs/frame-mapping.md` defines
      it and `python/framecount.py` implements it
- [x] Verified against a passage counted by hand, so the mapping is known to
      reproduce the interface's own matching rather than assumed to. Three
      behaviours were also checked against the interface itself: case is
      ignored, matches cross sentence boundaries, and a wildcard slot holds one
      word with hyphens included
- [x] OSF registration for Study 2 submitted before any text is generated,
      carrying the generation protocol — models and versions, prompts,
      temperature and sampling, the topic and genre matching — and the mapping.
      <https://osf.io/qjgtc>, 25 September 2026, pinned to commit 1196f8d

**C — Studies 2 and 3 on OLMo.** One phase, not two. The OLMo generation run
produces Study 2's open-model output and Study 3's output side at once, so the
marginal cost of Study 3 over Study 2 is the Dolma sample and the pass that
counts it. Everything else is already required by Study 2.

- [x] Dolma sampling frame decided: version, subsets, how shards are drawn, how
      much text, and the seed. `docs/dolma-sampling-frame.md`: stage 1 of
      `dolma3_6T-mix-1025`, 200M words of `common_crawl` as the primary input
      and 20M of each other subset for the whole-mix figure, 200 files at 1M
      words each, seed 20260925
- [x] OSF registration for Study 3 submitted before the sample is drawn.
      <https://osf.io/ngt3m>, 25 September 2026, pinned to commit 381703b,
      with the sampling frame and the counting layer attached
- [ ] Olmo generation run: prompts, parameters and seeds committed, and enough
      text that the frames carry usable intervals. `python/generate.py` runs
      the four registered conditions on Modal; it has not been run
- [ ] Frame rates counted in the Dolma sample and in OLMo's output with the
      layer from phase B, both with intervals
- [ ] The two set against each other, and against the Study 1 variety rates

**D — closed models.** Optional, and the article stands without it. It widens
Study 2 only: GPT, Claude and Gemini output can be measured and their inputs
cannot, so the volume confound stays open for them by construction.

- [ ] Generation protocol as registered, run per model and per version
- [ ] Rates reported per model and per version, never pooled across them

**Article.** Published on blog.sheetsolved.com, stating the lexicalisation
ceiling, the December 2012 collection date, what the genre control does and does
not do, that Study 2 has no ground truth for "American-like" beyond Study 1
itself, and — if phase D ships — that the volume confound is unanswered for the
closed models.

- [ ] `README.md` and `RESEARCH-PLAN.md` describe what was actually done

## Out of scope

- Whether readers actually judge texts differently. Needs human subjects and an
  ethics process this project does not have.
- Journal submission. A preprint stays optional and is decided after there is a
  result.
- Buying the full-text GloWbE release. Settled; the lexicalisation ceiling is
  accepted as the price of a study that is free to replicate.
- Frames needing sentence position or document structure.
- Adding or changing frames after seeing results.
- Any claim about web English after December 2012.
- Any claim that OLMo's behaviour generalises to GPT or Claude. Phase C buys a
  clean input-output comparison on a model few people read, and the step from
  there to the models people do read is an argument, not a result.
- Biber, Egbert & Davies (2015). It cannot be obtained, so the genre-control
  wording stands as attributed to Murphy (2025) rather than pending.

## Bar

Research, public, pre-registered. Not a journal submission, and the rigour is
unchanged by that: each study's design is fixed before its own data exists,
every comparison carries an interval, the threats are stated in the write-up,
and the repository reproduces from a clean clone. The reader is the constraint.

Code quality: correct on the real data, refuses a partial grid rather than
warning about it, and invents no numbers. `R/analyse.R` serves Study 1 only and
is not a library.

## Changes to the frozen parts

Once a study is registered, its frames, varieties, sections, model and protocol
are pre-registered. Changing any of them is a declared deviation, not an edit.
Raise it rather than making it.

## Decision

Ces, when the article is published and the analysis reproduces from a clean
clone.

## Revision history

- 2026-09-04: initial scope, Study 1 only.
- 2026-09-04: Study 2 brought in alongside Study 1.
- 2026-09-04: Study 3 brought in, and the whole thing restructured into gated
  phases. With all three in, scope size is no longer the stop condition and the
  gates are.
- 2026-09-04: split into one registration per study. A single registration for
  Studies 1 and 2 would have held Study 1 behind the frame-to-raw-text mapping,
  which is better written after the grid has been collected by hand.
- 2026-09-22 to 09-23: collection found that the interface splits only 8 of the
  frames by section and cannot count F06 at all. Phase A's grid criterion now
  matches what D2 registers rather than the 150 cells originally planned.
