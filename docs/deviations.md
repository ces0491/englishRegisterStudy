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
