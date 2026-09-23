# Deviations from the Study 1 registration

Every departure from the registration at <https://osf.io/48wjn>, recorded when
it was made and before the analysis was run. Each is also filed as an update on
the OSF registration.

## D1. Section word counts come from the corpus's TEXTS page

**Registered:** "Section word counts are read off the interface when querying
and recorded in data/corpus-sizes.csv."

**What happened:** the Chart display's WORDS (M) row shows the whole-component
size whichever section is selected, and PER MIL is computed against it. For
`here 's the thing` restricted to General, US shows 583 hits against 386.8
million words, the whole US component. The query screen therefore does not
report section sizes.

**What is done instead:** section sizes come from the GloWbE TEXTS page (the
document icon beside the corpus title), which gives exact word counts per
country for the General and (Only) Blogs sections. The interface's own help
describes that icon as "Description of the corpus: number of words in each
section", so this is the interface's documented source for section sizes.
They were read on 22 September 2026 and recorded in `data/corpus-sizes.csv`.
All ten match, to the word, the sums by country and genre of the corpus's
downloadable page-level metadata (1,791,422 pages), which
`R/check-corpus-sizes.R` recomputes. The GB and US figures also match
Westphal (2024).

That page's Total column is 0.055–0.088% larger than General plus Blog for each
of the five varieties, apparently words assigned to neither section. Hit counts
restricted to General and to Blog sum exactly to the unrestricted count
(checked for F01 in all five varieties), so the section columns are the matching
denominators and the Total column is not used.

**Effect on the analysis:** none on the model, frames, counts or inference. The
offsets change from component totals, which would have been wrong, to section
sizes, which is what the registration intended. The blog share of words ranges
from 20% (IE) to 34% (US, GB), so using component totals for both sections
would have biased the variety comparison.

**When:** 22 September 2026, during the first query session. Only F01 had been
counted, and no analysis had been run.

## D2. The section split is unavailable for six frames, and F06 for none

**Registered:** all fifteen frames counted in each variety's blog and general
sections, 150 cells, with the composite estimated per section and the
`variety:section` test deciding which ratios are confirmatory.

**What happened:** two limits of a free english-corpora.org account, each
stated only when a query is refused.

1. A section-restricted search is refused when every slot in the string occurs
   1,500,000 times or more: "(Except in COCA) You cannot search for high
   frequency multi-word strings, when you have also selected a SECTION." This
   blocks F03, F07, F08, F09, F10 and F13 — the whole contrastive family plus
   two others. The unrestricted search still returns them.
2. A search string may be at most five tokens: "Unless you have a premium
   license, your search string must not be longer than five words in length."
   F06, `it 's not * , it 's`, is seven tokens, so it cannot be counted at all.

`docs/collection-log.md` records which frames were refused and what each
refusal said.

**What is done instead:**

- **Primary analysis:** the registered model on counts with both sections
  combined, for the fourteen countable frames, with each variety's whole
  component as the offset: `hits ~ frame_id + variety + (1 | frame:variety)`,
  Poisson, `offset(log(words))`. The `section` term drops out because there is
  no section. The registered model's second random effect drops out too: with
  the sections combined there is one observation per frame and variety, so a
  cell-level effect is the same grouping as the frame-by-variety effect, only
  their sum is identified, and fitting both gives a degenerate Hessian. The one
  remaining term carries the frame's preference for a variety and the
  overdispersion of that count together.

  Intervals and p-values use a t reference with one degree of freedom per frame
  less one, rather than the registered normal reference, because the variety
  effect is replicated across fourteen frames and not across seventy cells. On
  synthetic grids with a known ratio, the normal reference covered it 88-90% of
  the time against a nominal 95%; the t reference covered it 92%, and halved
  the rate at which a variety whose true ratio is 1 was called significant.
  `R/calibrate-composite.R` reruns the comparison.

  The hypothesis, the directional test, Holm's correction, the zero-hit rule,
  the convergence rule and the partial-frame sensitivity rerun are unchanged.
- **Secondary analysis:** the registered per-section model, exactly as
  registered and with its normal reference, on the eight frames that do split.
  It carries the genre control, including the `variety:section` test.
- **F06 is dropped** and reported as uncountable on a free account. The study
  keeps its property that anyone can reproduce every count without paying,
  which the registration states. A premium licence would lift the five-word
  limit but, on the evidence of the error messages, not the section rule, so
  buying one would add F06 as another combined-only frame and nothing else.

**Effect on the analysis:** the genre control weakens, and this is the real
cost. It was registered as a control over all fifteen frames and now covers
eight, so a common variety effect across sections is evidence about those
eight and not about the contrastive family. Any write-up has to say that the
frames most exposed to a genre explanation are the ones that cannot be tested
for it. The frame set for the main hypothesis falls from fifteen to fourteen.

**When:** 22-23 September 2026, during the first two query sessions, before any
analysis was run. Counts already collected are unaffected: the eight splittable
frames keep their section counts, which the secondary analysis uses.

### Filed on OSF

D2 was submitted as a registration update on 23 September 2026, revising the
Statistical models, Inference criteria, Unit of analysis and Missing data
answers.

Two sentences elsewhere in the registration were left as written and are stale
in a small way. Assumption Violation describes a zero-hit frame as one with no
hits "in any of its ten cells", which is the secondary analysis's cell count;
the primary has five per frame, and the revised Unit of analysis answer states
the rule in general terms. Reliability and Robustness Testing describes the
partial-frame rerun as covering the genre test, which it no longer does,
because neither partial frame can be split by section. Both are recorded here
rather than in a further update, and will be corrected if another deviation
needs filing.
