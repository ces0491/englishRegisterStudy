# SCOPE — englishRegisterStudy

## Purpose

Measure whether fifteen frozen rhetorical frames occur at different rates in
American web English than in British, Irish, Australian and South African web
English, using a corpus collected before generated text existed.

## What this covers

Study 1 — the pre-LLM baseline — through to a published article. Studies 2 and
3 in `RESEARCH-PLAN.md` are the next phase and are scoped separately, because a
document that covers all three has no stop condition.

## Done

- [ ] OSF pre-registration submitted before any count is recorded, carrying the
      frozen frames, varieties, sections and the analysis as written
- [ ] Full grid collected by hand from GloWbE: 15 frames x 5 varieties x 2
      sections, plus the 10 section word counts, committed as `data/counts.csv`
      and `data/corpus-sizes.csv`
- [ ] `Rscript R/analyse.R` runs end to end on the real counts and produces the
      rates, the per-frame ratios against US, the composite and the
      `variety:section` F test
- [ ] Every reported comparison carries an interval
- [ ] A stranger with a free english-corpora.org account can reproduce every
      count from what is in the repository
- [ ] Article published on blog.sheetsolved.com, stating the lexicalisation
      ceiling, the December 2012 collection date and what the genre control
      does and does not do
- [ ] `README.md` and `RESEARCH-PLAN.md` describe what was actually done

## Out of scope

- Studies 2 and 3 — the generated comparison, and Dolma against OLMo output.
- Whether readers actually judge texts differently. Needs human subjects and an
  ethics process this project does not have.
- Journal submission. A preprint stays optional and is decided after there is a
  result.
- Buying the full-text GloWbE release. Settled; the lexicalisation ceiling is
  accepted as the price of a study that is free to replicate.
- Frames needing sentence position or document structure.
- Adding or changing frames after seeing results.
- Any claim about web English after December 2012.
- Biber, Egbert & Davies (2015). It cannot be obtained, so the genre-control
  wording stands as attributed to Murphy (2025) rather than pending.

## Bar

Research, public, pre-registered. Not a journal submission, and the rigour is
unchanged by that: the analysis is frozen before the data exists, every
comparison carries an interval, the threats are stated in the write-up, and the
repository reproduces from a clean clone. The reader is the constraint.

Code quality: correct on the real grid, refuses a partial one rather than
warning about it, and invents no numbers. `R/analyse.R` serves this study only
and is not a library.

## Changes to the frozen parts

Once the OSF registration is submitted, the frames, varieties, sections and the
model are pre-registered. Changing any of them is a declared deviation, not an
edit. Raise it rather than making it.

## Decision

Ces, when the article is published and the analysis reproduces from a clean
clone.

## Revision history

- 2026-09-04: initial scope
