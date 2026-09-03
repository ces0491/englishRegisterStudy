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

Scope and design are in [RESEARCH-PLAN.md](RESEARCH-PLAN.md). This is aimed at a
paper, with anything written for the blog as a by-product, so the frames are
pre-registered and the analysis is fixed before the data is collected.

## The four questions

A study that produces an index has to answer the same four questions it would ask
of anyone else's.

**What is counted?** Occurrences of 15 fixed lexical frames, listed in
`data/frames.csv` and frozen before any querying. Each is a string or wildcard
pattern that the GloWbE interface can match without syntactic parsing.

**Over what population?** GloWbE: 1.9 billion words across 1.8 million web pages
from 20 countries, roughly 60% informal blogs and 40% other genres. Five
varieties are used here: US, GB, IE, AU, ZA. Each is split into the corpus's
blog and general-web sections and analysed separately, so a difference between
varieties cannot be a difference between genres.

**Weighted how?** Not weighted. Frame rates are reported individually. The
composite is a plain sum of hits over the same word base, because no defensible
reason exists to weight one frame above another, and an index that invents
weights is the failure this study is partly a response to.

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

So the study tests the lexicalised end of the claim. The sharper version — that
what distinguishes the register is the *density* and near-obligatory quality of
these moves rather than their existence — is only reachable through the composite
rate, which is a weak proxy. Say so in anything written from these results.

## Method

GloWbE has no API and its downloadable form is restricted to researchers at
member institutions, so counts are entered by hand from the web interface at
<https://www.english-corpora.org/glowbe/>.

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
split, which is the control the design leans on.

## Adding a frame

Adding one after seeing results is a different study. If a frame goes in later,
record when and why, and report the frozen set separately.
