# englishRegisterStudy

Do the rhetorical frames that make short-form writing "punchy" occur more often
in American English than in other national varieties?

The hypothesis is that a particular set of constructions — announcing a point
before making it, the `it's not X, it's Y` contrast, the epigrammatic assertion —
is characteristic of American web register rather than of English generally, and
that this is part of why generated prose reads as foreign to a British, Irish,
Australian or South African ear before it reads as machine-written.

Neither the hypothesis nor its opposite has any evidence behind it at the time of
writing. That is the point of measuring.

Scope and design are in [RESEARCH-PLAN.md](RESEARCH-PLAN.md). The output is this
repository and an article, not a journal submission. The frames are still
pre-registered and the analysis still fixed before any data is collected,
because both are for a reader rather than for a reviewer.

## The four questions

A study that produces an index has to answer the same four questions it would ask
of anyone else's.

**What is counted?** Occurrences of 15 fixed lexical frames, listed in
`data/frames.csv` and frozen before any querying. Each is a string or wildcard
pattern that the GloWbE interface can match without syntactic parsing.

**Over what population?** GloWbE: 1.9 billion words across 1.8 million web pages
from 20 countries, collected in December 2012. Five varieties are used here —
US, GB, IE, AU, ZA — with components ranging from 387.6 million words for GB
down to 45.4 million for ZA. Each is split into the corpus's blog and
general-web sections and analysed separately.

That split is a partial genre control. Davies and Fuchs describe roughly 60% of
the corpus as coming from informal blogs, while the section labelled Blog holds
about a third of the words in the GB and US components, so blog-like text sits
on both sides of the line. Biber, Egbert and Davies (2015) found the categories
overlap too much to be useful, and Murphy (2025) abandoned balancing a GloWbE
sample across them on that basis. Analysing sections separately reduces the risk
that a difference between varieties is a difference between genres without
removing it.

**Weighted how?** No frame is weighted above another. No defensible reason
exists to do it, and an index that invents weights is the failure this study is
partly a response to.

The composite is a model rather than a total. Fifteen frames whose base rates
differ by orders of magnitude would let the commonest of them dominate a raw
sum, so the composite is a quasi-Poisson GLM: `hits ~ frame_id + variety +
section` with `offset(log(words))`. Frame as a factor absorbs the base-rate
spread without anyone choosing a number for it, and the estimated dispersion
carries what is left into the variety intervals. On structureless fixtures the
dispersion came out above a thousand, so a plain Poisson would have been badly
overconfident about the one comparison the study rests on.

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
   `data/corpus-sizes-template.csv` to `data/corpus-sizes.csv`.
2. Record the raw hit count for each frame in each variety and section, and the
   section word counts. Raw counts rather than the interface's per-million
   figure, so the normalisation can be recomputed and checked.
3. `Rscript R/analyse.R`

The script refuses a partial grid. All 15 frames across 5 varieties and 2
sections have to be present, entered once each, with a whole-number hit count,
and every variety/section pair needs its word count. A cell left out would lower
that variety's composite and nothing in the output would show it, so a gap is an
error rather than a warning.

Outputs — `data/rates.csv`, `data/composite.csv`, `data/ratios-vs-us.csv`,
`data/composite-ratios.csv` and `figures/frame-rates.png` — are all derived and
are not committed. Everything needed to reproduce them is.

Rates carry exact Poisson intervals on the underlying count, because a frame
seen four times and a frame seen four thousand times are not equally well
measured and a bare per-million figure hides the difference.

Every ratio against US carries an interval too. Per frame those are exact
conditional Poisson intervals; the composite comes from a quasi-Poisson model
with frame as a factor and `log(words)` as an offset, because fifteen frames
with base rates orders of magnitude apart are overdispersed and a plain Poisson
interval on the comparison would be too narrow. The same model with a
`variety:section` term tests whether the variety effect survives the genre
split, subject to the caveat above about how much that split can carry.

## Adding a frame

Adding one after seeing results is a different study. If a frame goes in later,
record when and why, and report the frozen set separately.
