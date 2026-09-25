# englishRegisterStudy

Do the rhetorical frames that make short-form writing "punchy" occur more often
in American English than in other national varieties?

The hypothesis is that a particular set of constructions — announcing a point
before making it, the `it's not X, it's Y` contrast, the epigrammatic assertion —
is characteristic of American web register rather than of English generally, and
that this is part of why generated prose reads as foreign to a British, Irish,
Australian or South African ear before it reads as machine-written.

Neither the hypothesis nor its opposite had any evidence behind it when this
started. That was the point of measuring.

The design is in [RESEARCH-PLAN.md](RESEARCH-PLAN.md) and the completion
criteria in [SCOPE.md](SCOPE.md). The output is this repository and an article,
not a journal submission. The frames were pre-registered and the analysis fixed
before any data was collected, because both are for a reader rather than for a
reviewer. Study 1 is registered on OSF at <https://osf.io/48wjn>, submitted on
21 September 2026 before any count was retrieved, and its counts were collected
over three sessions from 22 to 25 September.

## The four questions

A study that produces an index has to answer the same four questions it would ask
of anyone else's.

**What is counted?** Occurrences of 15 fixed lexical frames, listed in
`data/frames.csv` and frozen before any querying. Each is a string or wildcard
pattern that the GloWbE interface can match without syntactic parsing.

Fourteen of them can actually be counted. A free account caps a search at five
tokens, and F06, `it 's not * , it 's`, is seven. Six more can be counted only
with the sections combined, because the interface refuses a section-restricted
search when every word in the string is very common. That is deviation D2 in
[docs/deviations.md](docs/deviations.md), and it splits the analysis in two.

**Over what population?** GloWbE: 1.9 billion words across 1.8 million web pages
from 20 countries, collected in December 2012. Five varieties are used here —
US, GB, IE, AU, ZA — with components ranging from 387.6 million words for GB
down to 45.4 million for ZA. Each has a blog and a general-web section, and the
frames the interface will split are analysed by section as well.

That split is a partial genre control. Davies and Fuchs describe roughly 60% of
the corpus as coming from informal blogs, while the section labelled Blog holds
about a third of the words in the GB and US components, so blog-like text sits
on both sides of the line. Murphy (2025) abandoned balancing a GloWbE sample
across them, reporting that Biber, Egbert and Davies (2015) found the categories
overlap too much to be useful. That paper is paywalled and reaches this study
only through her footnote, so the strength of the finding rests on her account
of it. Analysing sections separately reduces the risk that a difference between
varieties is a difference between genres without removing it.

**Weighted how?** No frame is weighted above another. No defensible reason
exists to do it, and an index that invents weights is the failure this study is
partly a response to.

The composite is a model rather than a total. Fifteen frames whose base rates
differ by orders of magnitude would let the commonest of them dominate a raw
sum, so the composite is a Poisson GLMM with `offset(log(words))`. Frame as a
factor absorbs the base-rate spread without anyone choosing a number for it,
and a frame-by-variety random effect carries each frame's own preference for a
variety, so the variety ratio is an average over frames and its interval widens
when frames disagree.

D2 gives it two forms. The confirmatory one covers the fourteen countable
frames with the sections combined: `hits ~ frame_id + variety +
(1 | frame:variety)`. With one observation per frame and variety, that term
carries the frame preference and the overdispersion together; adding a separate
cell-level effect would be the same grouping twice. Its intervals use a t
reference with one degree of freedom per frame less one, because the variety
effect is replicated across fourteen frames rather than across seventy cells:
on synthetic grids the normal reference covered a known ratio 88–90% of the
time and the t reference 92%. The secondary analysis is the registered form,
`hits ~ frame_id + variety + section + (1 | frame:variety) + (1 | cell)`, on
the eight frames that split, with the normal reference as registered, and it
carries the genre control.

Two simpler models were run against synthetic data with a known ratio first.
When a frame's preference for a variety holds across both sections, which is the
plausible case, quasi-Poisson's 95% intervals covered the true ratio 15–16% of
the time and negative binomial's 77–79%. This model covered it 93%.
`Rscript R/calibrate-composite.R` reruns the comparison.

**Covering what dates?** GloWbE's pages were collected in December 2012. Every result is a
statement about web English at that date and about nothing since. This is the
study's most serious limitation: the register in question is claimed to have
spread through Medium, Substack and LinkedIn, most of which postdate the corpus.

Corpus description: Davies, M. & Fuchs, R. (2015), "Expanding horizons in the
study of World Englishes with the 1.9 billion word Global Web-based English
Corpus (GloWbE)", *English World-Wide* 36(1).
<https://doi.org/10.1075/eww.36.1.01dav>

## What this can and cannot measure

**Can:** frames with a fixed lexical shape — `here 's the thing`,
`it 's not * , it 's`, `not just * but`.

**Cannot:** sentence-initial position, one-sentence paragraphs, or a closing
epigram. Each needs sentence or document structure the interface does not expose.
The purchasable full-text release does expose it; see Method for why this study
does not use it.

So the study tests the lexicalised end of the claim. The sharper version — that
what distinguishes the register is the *density* and near-obligatory quality of
these moves rather than their existence — is only reachable through the composite
rate, which is a weak proxy. Say so in anything written from these results.

## Method

GloWbE has no API, so counts are entered by hand from the web interface at
<https://www.english-corpora.org/glowbe/>.

Full-text GloWbE data is purchasable from <https://www.corpusdata.org/> under an
academic or non-academic licence, at a few hundred dollars for a single corpus.
It is deliberately not used here. That keeps the study free to run and free to
replicate — anyone with a no-cost account can rerun every count in this
repository — at the price of the ceiling described above. Buying the data later
stays open; widening the frozen frame set after seeing results does not, so the
decision is recorded here.

1. Copy `data/counts-template.csv` to `data/counts.csv` and
   `data/corpus-sizes-template.csv` to `data/corpus-sizes.csv`. Counts with the
   sections combined go in `data/counts-combined.csv`.
2. Record the raw hit count for each frame in each variety and section from
   the Chart display, with the section chosen in the Sections list, and the
   section word counts from the General and (Only) Blogs Words columns of the
   TEXTS page. The Chart display's own WORDS (M) row is the whole component
   whatever section is chosen, so it cannot be used.
   `Rscript R/check-corpus-sizes.R path/to/glowbe_sources.txt` recomputes the
   section sizes from the metadata download on the same page, and fails if
   `data/corpus-sizes.csv` disagrees. Raw counts rather than the
   interface's per-million figure, so the normalisation can be recomputed and
   checked.
3. `Rscript R/analyse.R`, which needs the R packages dplyr, ggplot2, readr,
   tidyr and lme4.

Studies 2 and 3 count the same frames in raw text rather than through the
interface. `docs/frame-mapping.md` defines how, `python/framecount.py`
implements it with no dependencies beyond the standard library, and
`python -m pytest python -q` checks it against a passage counted by hand.

The script refuses a partial grid, in either file. Every countable frame needs a
combined count in all 5 varieties, every splittable frame needs both sections,
each entered once with a whole-number hit count, and every variety needs its
blog, general and whole-component word counts. A cell left out would lower that
variety's summed rate and nothing in the output would show it, so a gap is an
error rather than a warning.

Outputs — the `rates`, `composite`, `ratios-vs-us` and `composite-ratios` files
in `data/`, and the figures — are all derived and are not committed. Everything
needed to reproduce them is.

Rates carry exact Poisson intervals on the underlying count, because a frame
seen four times and a frame seen four thousand times are not equally well
measured and a bare per-million figure hides the difference.

Every ratio against US carries an interval too. Per frame those are exact
conditional Poisson intervals, reported as description. The confirmatory result
is the composite from the combined-sections model. The hypothesis is directional
(each other variety below US), tested two-sided at 0.05 with Holm's correction
across the four variety ratios.

In the secondary analysis, the same model with a `variety:section` term tests by
likelihood ratio whether the variety effect survives the genre split, subject to
the caveat above about how much that split can carry. It covers eight frames, so
the frames most exposed to a genre explanation are the ones it cannot check.

A frame with no hits anywhere leaves the model and the output names it. The
primary analysis is also rerun without the two frames marked `partial` in
`data/frames.csv`, as a check that the result does not rest on what those two
patterns really match. Both partial frames are combined-only, so the secondary
analysis never contains one.

Study 1's analysis is registered at <https://osf.io/48wjn>, and the text as
submitted is in
[docs/osf-study1-registration.md](docs/osf-study1-registration.md). Study 2 is
registered at <https://osf.io/qjgtc> and Study 3 at <https://osf.io/ngt3m>.
Departures from it are recorded in [docs/deviations.md](docs/deviations.md),
and what each query session did, refusals included, in
[docs/collection-log.md](docs/collection-log.md).

## Result

Every other variety uses the frames less often than American English does:
GB 0.69 [0.61, 0.78], IE 0.54 [0.47, 0.62], AU 0.66 [0.58, 0.76] and
ZA 0.50 [0.43, 0.57], each with a Holm-adjusted p below 0.0001. The secondary
per-section analysis agrees and finds no evidence the gap differs between blog
and general text on the eight frames it can check.

[docs/study1-results.qmd](docs/study1-results.qmd) is the write-up, including
where the pattern is not uniform and what the result does not establish. Every
number in it comes from the files `R/analyse.R` writes, so run that first and
render with `quarto render docs/study1-results.qmd`.

## Adding a frame

Adding one after seeing results is a different study. If a frame goes in later,
record when and why, and report the frozen set separately.
