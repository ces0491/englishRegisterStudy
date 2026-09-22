# OSF registration — Study 1

Submitted to OSF on 21 September 2026 as <https://osf.io/48wjn>. This is the
text as submitted.

Text for OSF's **Secondary Data Preregistration** template (version 3), in the
template's order. Fields marked *required* cannot be left blank on OSF. The
analysis it registers is `R/analyse.R` at the commit this registration links
to, and the frames are `data/frames.csv` at the same commit.

The answers are plain text because OSF does not render Markdown. An asterisk
inside a quoted query is GloWbE's wildcard, and no other asterisks appear in
the answers.

Suggested title: *Rhetorical frames in American and other national varieties of
web English: a GloWbE baseline*

---

## Study Information

### Research questions *(required)*

1. Do fifteen rhetorical frames associated with short-form "punchy" prose occur
   at a lower composite rate in British, Irish, Australian and South African web
   English than in American web English?
2. Does the difference between varieties depend on whether the text is in
   GloWbE's blog or general section?

### Hypotheses *(required)*

H1 (directional). For each of GB, IE, AU and ZA, the composite rate of the
fifteen frames is lower than the US rate: a variety-to-US rate ratio below 1.
Four tests, one per variety.

Rationale: the frames are constructions that readers associate with generated
text, and generated text defaults to American English. If the frames are a
feature of American web register rather than of English generally, readers of
other varieties would meet them as regional before they meet them as machine
made. This study tests the first half of that argument on human writing
collected in December 2012, before large language models could contaminate a
web corpus.

RQ2 has no directional prediction. Its test decides which set of estimates
is confirmatory (see Statistical models), so it is registered as a decision
rule rather than a hypothesis.

---

## Data Description

### Datasets used *(required)*

The Corpus of Global Web-Based English (GloWbE), queried through its web
interface at english-corpora.org. It holds about 1.9 billion words from web
pages in 20 countries, collected in December 2012, with each country's
component divided into a blog section and a general section.

Subsets used: five national components (US, GB, IE, AU, ZA), each section
separately. The interface reports component sizes of 386.8 million words for
US, 387.6 million for GB, 148.2 million for AU, 101.0 million for IE and 45.4
million for ZA.

Cross-sectional: one collection, no waves.

### Data availability *(required)*

The dataset is publicly available.

### Data access

Querying needs a free english-corpora.org account. The full text is sold
separately by corpusdata.org and is not used here: every count in this study
can be reproduced with a free account.

### Data identifiers

https://www.english-corpora.org/glowbe/ — corpus description: Davies, M. &
Fuchs, R. (2015), English World-Wide 36(1), https://doi.org/10.1075/eww.36.1.01dav

### Access date *(required)*

No count has been retrieved. All counts are collected after this registration
is submitted, and the date of each query session is recorded in the notes
column of data/counts.csv.

### Data collection procedures *(required)*

The corpus. Built by Mark Davies from web pages collected in December 2012
and assigned to countries by the corpus builder. The corpus description is
Davies & Fuchs (2015), cited above; it is paywalled and has not been read for
this study, so what it says about construction reaches here through the papers
that cite it.

Known biases:

- Country assignment is a proxy for author nationality. From a spelling test
  on "color", "tumor" and "neighbor", Murphy (2025) estimates that 10–15% of
  writers in the GB and US components are non-nationals. That biases the
  comparison toward the null.
- The blog/general split is impure. Murphy (2025) reports that Biber, Egbert
  & Davies (2015) found the two categories overlap too much to be useful. That
  paper is also unread, so the claim is held as Murphy's account of it.
  Westphal (2024) nonetheless finds pragmatic markers more frequent in the blog
  section, so the split carries some signal.
- Web text from 2012 says nothing about any register that has developed since.

This study's collection. Each frame is searched once per section, with the
section set through the interface's Sections control. One search returns all
twenty countries. For each of the five varieties, the raw hit count (FREQ) is
recorded, never the per-million figure. Section word counts are read off the
interface when querying and recorded in data/corpus-sizes.csv. Nothing is
estimated or reconstructed. Queries are entered exactly as written in
data/frames.csv, in GloWbE's tokenised form with clitics split off and
punctuation as a separate token.

### Data collection procedures documentation

None uploaded. The query list is data/frames.csv in the linked repository.

### Codebook

No codebook exists for the interface counts. The variables are defined under
Measured variables below, and data/counts-template.csv and
data/corpus-sizes-template.csv in the repository give the record layout.

### Codebook documentation

None uploaded.

---

## Variables

### Manipulated variables

None. Observational.

### Manipulated variables documentation

None.

### Measured variables *(required)*

Outcome. hits: raw count of matches for one frame in one variety and
section.

Exposure. words: the section's word count, entered as log(words) as an
offset, so the model is of rates.

Predictors, all categorical, with treatment coding:

- variety: US, GB, IE, AU, ZA. US is the reference.
- section: blog, general. Blog is the reference.
- frame_id: F01–F15, a fixed factor absorbing base-rate differences between
  frames. F01 is the reference.

The frames, frozen before any query:

- F01: "here 's the thing" (announce)
- F02: "here 's the * part" (announce)
- F03: "here 's what" (announce)
- F04: "the thing is" (announce)
- F05: "what 's interesting is" (announce)
- F06: "it 's not * , it 's" (contrastive)
- F07: "it 's not just" (contrastive)
- F08: "not just * but" (contrastive)
- F09: "is n't just" (contrastive)
- F10: "not * , but *" (contrastive, partial)
- F11: "that 's the whole point" (epigram)
- F12: "which is the point" (epigram)
- F13: "and that 's" (epigram, partial)
- F14: "turns out" (reveal)
- F15: "the real question is" (announce)

"Partial" marks a pattern that will also match text outside the construction
it stands for. F13 matches any "and that's", not only a closing epigram.

The composite is not a scale or a sum. It is the variety effect in the
model under Statistical models: the ratio of a variety's rate to the US rate,
averaged over frames. No frame is weighted above another.

Descriptive outputs that carry no hypothesis test: the rate per million
for each cell with an exact Poisson interval, the summed rate per variety and
section, and the 120 per-frame ratios against US with exact conditional
Poisson intervals.

### Missing data

None is permitted. The grid is 15 frames × 5 varieties × 2 sections = 150
cells, plus 10 section word counts, and the script refuses to run if any cell
is missing, repeated, non-integer or mislabelled. A missing cell would lower
that variety's summed rate without any sign in the output. A zero count is a
result, not a missing value.

### Unit of analysis

The frame × variety × section cell. 150 cells expected. A frame with zero hits
in all ten of its cells is removed from the model (see Assumption violation),
which removes ten cells.

### Statistical outliers

None defined and none removed. A frame with an unusually high or low rate in
one variety is the thing being measured. Its influence on the composite is
limited by the frame × variety random effect, and the partial-frame
sensitivity analysis covers the two patterns most likely to over-match.

### Sampling weights

None. GloWbE supplies none, and none are constructed.

---

## Knowledge of Data

### Prior Publication/Dissemination

None. The author has not published or presented any work using GloWbE.

### Prior knowledge *(required)*

The author (sole author) has never run a search on GloWbE, and has seen no
count or rate for any of the fifteen frames in any variety or section.

Prior knowledge from reading:

- Westphal (2024) on sentence-final "eh" and Murphy (2025) on "please", both
  across GloWbE varieties. Neither concerns any of the frames.
- Section word counts for the GB and US components, from Westphal (2024), and
  component sizes for all five varieties, from Davies's guided tour of
  english-corpora.org (2020).
- Murphy's (2025) estimate of non-national writers in the GB and US
  components, reported above.

The frames were chosen from the author's impression of what language models
overproduce, not from any corpus.

---

## Analyses

### Statistical models *(required)*

Primary model (H1). A Poisson generalised linear mixed model, fitted by
maximum likelihood (Laplace approximation, lme4::glmer):

    hits ~ frame_id + variety + section + (1 | frame:variety) + (1 | cell)
           offset: log(words)

- frame_id fixed: absorbs base rates that differ by orders of magnitude
  between frames.
- (1 | frame:variety): each frame's own preference for each variety, shared
  across the two sections. The variety effect is therefore an average over
  frames, and its interval reflects how much frames disagree.
- (1 | cell): an observation-level random effect for overdispersion that
  remains within cells.

The composite ratio for each of GB, IE, AU and ZA is exp of its variety
coefficient.

Genre test (RQ2). The same model with variety:section added, compared to
the primary model by likelihood-ratio test on 4 df.

- If p ≥ 0.05: the four common ratios from the primary model are the
  confirmatory result.
- If p < 0.05: the eight per-section ratios from the interaction model are the
  confirmatory result, and the common ratios are set aside. The general-section
  ratio is the variety coefficient plus its variety:section interaction,
  with its standard error from the model's covariance matrix.

Why this model. Before registration, quasi-Poisson, negative binomial and
two Poisson GLMMs were fitted to simulated grids with a known ratio (script
R/calibrate-composite.R; corpus sizes near GloWbE's, base rates invented, no
GloWbE count used). With frame preferences shared across sections, 95%
intervals covered the true ratio 15–16% of the time for quasi-Poisson, 77–79%
for negative binomial, and 93% for this model. With independent noise in each
cell, this model covered it 89–91%.

Post-hoc analyses. None beyond those listed under Reliability and
Exploratory analysis.

### Effect size

No minimum effect size of interest is specified. No prior estimate of these
frames' rates by variety exists to base one on. Each ratio is reported with its
95% interval, and the interpretation in the write-up rests on the interval, not
on significance alone.

### Statistical power

No formal power analysis: the corpus fixes the sample. In the calibration
simulation, with invented base rates and a frame × variety SD of 0.2 on the log
scale, the GB ratio's estimate had a standard deviation of about 0.05. At that
precision, a true ratio of 0.7 would be detected reliably and one of 0.9 often
would not. With an SD of 0.4 the estimate's SD was about 0.1. The real
precision depends mainly on how much frames disagree across varieties, which
is unknown until the data exists.

### Inference criteria

- Wald 95% intervals and two-sided p-values on the variety coefficients.
- Holm's correction across the confirmatory set: four ratios, or eight if the
  genre test splits by section.
- A variety supports H1 when its ratio is below 1 and its Holm-adjusted p is
  below 0.05. A ratio above 1 with adjusted p below 0.05 is reported as
  evidence against H1 for that variety.
- The genre test uses α = 0.05 with no correction, since it is a single test
  that selects the confirmatory set. It ran slightly liberal in simulation, at
  6–12% against a nominal 5%, which errs toward the more cautious per-section
  reporting.
- The 120 per-frame ratios are descriptive, reported with uncorrected intervals,
  and no conclusion rests on any one of them.

### Assumption Violation/Model Non-Convergence

- Zero-hit frames. A frame with no hits in any of its ten cells carries no
  information about varieties, and its fixed effect would be unbounded. It is
  removed from the model, named in the output, and kept in the descriptive
  rates.
- Convergence. Fit with the bobyqa optimiser. If lme4 reports a
  convergence failure, refit with Nelder–Mead. If both fail, no estimate is
  reported from that model, and any analysis used instead is reported as a
  deviation from this registration.
- Singular fit. If a random-effect variance is estimated at zero, the fit
  is kept and reported. It means that source of variation is not detectable,
  and the model reduces to the simpler one.

### Reliability and Robustness Testing

The whole composite analysis (primary model, genre test, and whichever ratio
set the primary genre test selected) is rerun without the two partial frames,
F10 and F13, and reported beside the primary result. The primary result stays
primary. If the two disagree on whether a variety supports H1, the write-up
says so and treats that variety's result as dependent on patterns that
over-match.

### Exploratory analysis

Reported separately from the confirmatory results and labelled exploratory:

- The per-frame ratios, including which frames and frame families drive any
  variety difference.
- Any of GloWbE's other fifteen varieties, since one search returns all twenty.
- A precision check on F10 and F13: a sample of concordance lines per variety,
  coded for whether each match is the intended construction.

---

### References

Biber, D., Egbert, J. & Davies, M. (2015) 'Exploring the composition of the
searchable web: a corpus-based taxonomy of web registers', Corpora, 10(1),
pp. 11–45. doi:10.3366/cor.2015.0065.

Davies, M. (2020) English-Corpora.org: a guided tour.

Davies, M. & Fuchs, R. (2015) 'Expanding horizons in the study of World
Englishes with the 1.9 billion word Global Web-based English Corpus (GloWbE)',
English World-Wide, 36(1). doi:10.1075/eww.36.1.01dav.

Murphy, M. L. (2025) 'Separated by a common im/politeness marker: please in
American and British web-based English', English Language & Linguistics,
29(4), pp. 781–804. doi:10.1017/S1360674324000455.

Westphal, M. (2024) 'Eh across Englishes: a corpus-pragmatic analysis of the
Corpus of Global Web-Based English', Corpus Pragmatics, 8, pp. 53–75.
doi:10.1007/s41701-023-00159-6.
