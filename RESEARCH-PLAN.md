# Research plan

Status: draft for discussion. Nothing below is settled.

## The question

Are the rhetorical frames characteristic of LLM-generated English specifically
features of **American** web register rather than of English generally?

If they are, it follows that readers of other standard varieties encounter
generated prose as regionally foreign before they encounter it as machine-made,
and that "this reads as AI" is partly a judgement about national register.

## Why this is a paper and not a blog post

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

Do the target frames occur at different rates across national varieties of
human-written web English?

- Instrument: GloWbE, blog and general sections held separate.
- Varieties: US, GB, IE, AU, ZA. Others if the frames survive.
- Frames: frozen in `data/frames.csv` before querying.
- Outcome: rate per million with exact Poisson intervals; US as reference.

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
- Same frames, same counting, same intervals.
- Report per model and per version. This is a moving target and a result about
  one model at one date is all it can be.

### Deliberately out of scope

Whether readers of different varieties actually judge texts differently. That
needs human subjects, ethics approval and an institution, and it is a separate
paper. Study 1 and 2 together support the register claim; they do not establish
the perception claim, and the write-up must not imply otherwise.

## Threats to validity

- **Frame selection.** Fifteen frames chosen from intuition about what LLMs
  overproduce. Freezing them before querying controls for post-hoc selection,
  not for the possibility that they were the wrong frames. Pre-register.
- **Register confound.** "American vs British" could be "blogs vs broadsheets".
  The blog/general split within variety is the control; verify it is exposed in
  the interface before relying on it.
- **Lexicalisation ceiling.** Only fixed frames are countable. The stronger
  claim is about density and near-obligatory use, and the composite rate is a
  weak proxy for it. Do not overstate what the composite shows.
- **GloWbE country assignment** is by web domain and site location, which is a
  proxy for author nationality rather than a measure of it.
- **Study 2 has no ground truth** for what "American-like" means beyond Study 1
  itself, so the two studies are not independent.

## Venue candidates

| Venue | Fit | Note |
|---|---|---|
| *Corpus Pragmatics* (Springer) | high | published GloWbE marker work |
| *English World-Wide* (Benjamins) | high | published the GloWbE description paper |
| *Register Studies* (Benjamins) | medium | register-first framing |
| *ICAME Journal* | medium | corpus linguistics, open access |
| ACL/EMNLP workshop | medium | if Study 2 leads; faster turnaround |

Unaffiliated submission is accepted at all of these. Check article processing
charges before committing — some are substantial and not all are waivable
without an institution.

## Before any more code

1. **Read the literature properly.** The searches so far returned abstracts.
   At minimum: Liang et al. (2023); the GloWbE `please` and `eh` papers; Davies
   & Fuchs (2015); and whatever the citation graph of the first three surfaces.
   The `please` and `eh` papers may already have done part of the
   operationalisation.
2. **Pre-register.** OSF takes registrations from unaffiliated researchers at no
   cost. Frames, varieties, sections and analysis fixed in advance is most of
   what makes this credible given the author picked the frames from intuition.
3. **Confirm the blog/general split** is queryable per variety.

## Open decisions

- Does Study 2 go in the first paper, or does Study 1 stand alone?
- Which venue, and therefore which format and length?
- Is the blog article written before, alongside, or after submission?
