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

- **Primary: OLMo on Dolma.** Ai2 publishes the weights, the training code and
  the pretraining corpus. Frame rates can be counted in Dolma and in OLMo's
  output and set against each other exactly. No other model family allows this.
- Sample Dolma rather than processing it whole. At these rates a few million
  words gives intervals tight enough, and the sampling frame gets recorded.
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
- **Training data volume** is the confound that would otherwise sink the whole
  argument, and Study 3 exists to answer it. It remains unanswered for every
  closed model, which is a limit on how far the secondary results can be pushed.
- **OLMo is not the model anyone reads.** Study 3 buys a clean comparison at the
  cost of measuring a model with little real-world readership, and the
  generalisation from OLMo to GPT or Claude is an argument rather than a result.

## What it costs

This is a personal project with no budget, so the design has to stay inside one.

| Item | Cost |
|---|---|
| GloWbE queries | free account; rate-limited, so Study 1 spreads over days |
| Study 2 generation, cheap-tier models | cents to a few pounds per million output tokens |
| Study 2 generation, frontier models | one to two orders of magnitude more |
| Dolma sample | free; stream from Hugging Face rather than downloading 3T tokens |
| OLMo inference | free on Colab's T4, which is already in use for other work |
| OSF pre-registration | free, and open to unaffiliated researchers |
| arXiv or OSF preprint | free |
| Submission and publication | free at a hybrid journal on the subscription route |
| Gold open access | €1,500-3,000 at Benjamins with no institutional agreement |

**Skip gold open access.** John Benjamins journals are hybrid: subscription
revenue with optional paid OA. Publishing on the subscription route costs
nothing. Without an institution there is no Read & Publish agreement, so the
full APC would apply, and it buys reach that a free preprint buys anyway.

Post the preprint to arXiv or OSF at submission. Free, immediate, citable, and
it removes the only real argument for paying.

Sizing Study 2: a frame at roughly 50 occurrences per million words needs about
two million words to accumulate a hundred hits, which is where the Poisson
interval gets tight enough to be worth reporting. Two million words is under
three million output tokens. On cheap-tier models that is a rounding error; on
frontier models it is a real if survivable amount. Check current per-token
pricing rather than trusting any figure written down here.

The genuine cost is time. The literature review is the largest single item and
does not compress. Peer review then runs six to eighteen months, during which
the models being measured will have been replaced.

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
- Study 3 needs Dolma sampling infrastructure and OLMo inference. Both are
  tractable and neither is free of effort. Is that in the first paper?
- Which venue, and therefore which format and length?
- Is the blog article written before, alongside, or after submission?
