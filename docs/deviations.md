# Deviations from the registrations

## Study 1

Every departure from the registration at <https://osf.io/48wjn>, recorded when
it was made and before the analysis was run. Each is also filed as an update on
the OSF registration.

### D1. Section word counts come from the corpus's TEXTS page

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

#### D1 filed on OSF

D1 was submitted as a registration update on 22 September 2026, revising the
Data collection procedures answer.

### D2. The section split is unavailable for six frames, and F06 for none

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

#### D2 filed on OSF

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

The coverage figures in the justification above are a third. They were taken
from a run of the combined-sections block on its own, and do not come back from
`R/calibrate-composite.R` as committed: the four model-comparison conditions
draw from the random number stream first, so the block starts at a different
position. Running the committed script end to end on 29 September 2026 gives
coverage of 0.90, 0.89 and 0.93 with the normal reference against 0.93, 0.92
and 0.96 with the t reference, across the three cell-SD conditions — 89-93%
and 92-96% rather than the 88-90% and 92% filed. The choice of the t reference
is unaffected: it covers at least as well as the normal in every condition in
both runs. The false-positive claim is weaker than filed. The t reference
lowers the rate at which a variety whose true ratio is 1 is called significant
in all three conditions (0.053, 0.060, 0.053 against 0.040, 0.033, 0.027), but
"halved" is not resolvable at 150 replicates, where the Monte Carlo error on a
5% rate is about 1.8 points. The direction holds; the magnitude should not be
quoted without more replicates. Recorded here rather than in a further update,
on the same rule as the two above.

## Study 2

Every departure from the registration at <https://osf.io/qjgtc>, recorded
before any of the study's text was generated. Each is also filed as an update
on the OSF registration.

### S2-D1. The instruct checkpoint's template adds a system prompt

**Registered:** in Data collection procedures, "For the instruction-tuned
model the prompt is the user turn, with the checkpoint's own chat template and
no system prompt."

**What happened:** the chat template of `allenai/Olmo-3-7B-Instruct`, at the
revision the run uses (`6e5971d9eba42665f5bd5a0fcf047f299ce1dccc`), inserts a
system turn whenever the conversation has none: "`You are a helpful
function-calling AI assistant. You do not currently have access to any
functions. <functions></functions>`". With this checkpoint, its own template
and no system prompt cannot both hold.

**What is done instead:** the checkpoint's template is applied as it stands to
a conversation holding only the user turn, so the model receives its default
system prompt, as it does for anyone who supplies none. This study adds no
system prompt of its own, and the default names no variety, register or style.
The full rendered prompt is recorded with every generation.

The alternatives were an empty system message, which keeps "no system prompt"
literally but gives the model an empty system turn its template never
produces, and a prompt built by hand without a system turn, which abandons the
checkpoint's template. Study 2 measures default register, and the template's
default is the checkpoint as shipped.

**Effect on the analysis:** none on the model, frames, counts or inference.
The instruct conditions measure the checkpoint with its default system prompt,
and the write-up says so. The difference between the base and instruct
conditions, registered as what post-training adds, includes whatever that
system prompt contributes.

**When:** 28 September 2026, from the checkpoint's template, confirmed by the
trial recorded in `docs/collection-log.md`, before any of the study's text was
generated.

### S2-D2. Every condition covers all 4,000 topics

**Registered:** in Starting and stopping rules, "A condition stops when its
text reaches 2 million words as counted by python/framecount.py. If 4,000
generations fall short of 2 million words, topics are reused in topic_id order
with the seed advanced"; in Study design, "The same 4,000 topics serve every
condition, so topic is held constant across models and settings."

**What happened:** a condition averaging more than 500 words a generation
reaches 2 million words before its 4,000th topic. The trial averaged 585 words
for the base model and 656 for the instruct model at temperature 1.0, so
stopping at 2 million would end those conditions around topics 3,400 and
3,050, and topic would no longer be held constant across conditions.

**What is done instead:** every condition generates each of the 4,000 topics
once, whatever its word count. Only if that falls short of 2 million words are
topics reused, in topic_id order with the seed advanced, 64 at a time, and the
condition stops after the batch that brings its text to 2 million words. A
condition can therefore end above 2 million words, and the write-up reports
each condition's words and generations.

**Effect on the analysis:** none on the model or inference. Each condition's
words enter as its offset, so more text narrows a condition's interval without
changing what its rate estimates. Topic stays constant across conditions, as
the design registers.

**When:** 28 September 2026, before any of the study's text was generated.

### Study 2's OSF update

S2-D1 and S2-D2 were submitted as one update to the registration on 28
September 2026, citing this file at commit `bb8274b`, and the update was
approved the same day. It also discloses the trial. These are its changes,
answer by answer. Answers not listed are unchanged.

#### Overview: Explanation of foreknowledge and managing unintended influences

**Disclosure of the trial.** At the end, add

> After registration and before the run, a trial generated text for 128 topics
> with each model at temperature 1.0 to test the pipeline. Its seeds came from
> a separate namespace, so it produced none of the study's text, and its text
> was not counted and is not part of the data. docs/collection-log.md records
> what it found.

#### Sampling: Data collection procedures

**S2-D1.** Replace

> For the instruction-tuned model the prompt is the user turn, with the
> checkpoint's own chat template and no system prompt.

with

> For the instruction-tuned model the prompt is the user turn, with the
> checkpoint's own chat template and no system prompt added by this study.
> Whenever a conversation has no system prompt, the template supplies a default
> one, "You are a helpful function-calling AI assistant. You do not currently
> have access to any functions." followed by an empty functions tag, so the
> model receives that, as it would for anyone who gives no system message. The
> full rendered prompt is recorded with every generation.

OSF drops text in angle brackets, so the answer describes the template's empty
`<functions></functions>` element in words. S2-D1 gives the prompt in full.

#### Sampling: Sample size

**S2-D2.** Replace

> About 2 million words per condition, so about 8 million in total. 4,000
> generations per condition at roughly 500 words each reaches that.

with

> At least 2 million words per condition, so at least 8 million in total.
> Every condition generates all 4,000 topics, and 4,000 generations at roughly
> 500 words each reach 2 million; a condition that falls short reuses topics
> until it does.

#### Sampling: Starting and stopping rules

**S2-D2.** Replace

> A condition stops when its text reaches 2 million words as counted by
> python/framecount.py. If 4,000 generations fall short of 2 million words,
> topics are reused in topic_id order with the seed advanced, and the write-up
> reports how many generations each condition needed.

with

> Every condition generates each of the 4,000 topics once, whatever its word
> count, so topic is held constant across conditions. If those 4,000
> generations fall short of 2 million words as counted by python/framecount.py,
> topics are reused in topic_id order with the seed advanced, 64 at a time, and
> the condition stops after the batch that brings its text to 2 million words.
> The write-up reports each condition's words and how many generations it
> needed.

## Study 3

Every departure from the registration at <https://osf.io/ngt3m>, recorded
before any frame was counted in Dolma 3. Each is also filed as an update on the
OSF registration.

### S3-D1. The corpus is JSON Lines, under a new name, at a pinned revision

**Registered:** in Datasets used, "allenai/dolma3_mix-6T-1025 ... stored as
parquet"; in Data collection procedures, as the first step of the draw, "List
the subset's parquet files from the repository, sorted by path."

**What happened:** the first `count_dolma.py --list-only` run found 144,245
files and no parquet. The data files are JSON Lines, compressed with zstd
except for 78,137 olmOCR shards compressed with gzip. They sit in directories
named for the subset followed by a topic, language or part
(`data/common_crawl-politics-0016/`), with no single directory for a subset.
The registered name redirects to `allenai/dolma3_mix-6T-1025-7B`, whose card
now describes it as the mix used to train Olmo 3 7B and points to
`allenai/dolma3_mix-6T` for the 32B. Study 2 generates from the 7B, so the
pairing holds.

**What is done instead:** the first step lists the subset's `.jsonl.zst` and
`.jsonl.gz` files. A file belongs to a subset when its directory is named for
the subset alone or for the subset followed by a hyphen. At the pinned
revision that gives:

| Subset | Files |
|---|---:|
| `common_crawl` | 36,936 |
| `olmocr_science_pdfs` | 104,752 |
| `stack_edu` | 1,977 |
| `finemath-3plus` | 128 |
| `rpj-proofpile-arxiv` | 20 |
| `dolma1_7-wiki-en` | 42 |

`rpj-proofpile-arxiv` has exactly the 20 files its draw asks for, so its draw
is the whole subset in shuffled order.

The gzip shards are counted even though the dataset card's loader
configuration reads only `*.jsonl.zst`. They hold olmOCR topics found nowhere
else in the repository, education, finance, literature, history and religion
among them, so leaving them out would drop those topics from the subset.

387 files named like `shard_00000032.jsonl.zst338588528` are left out. All are
in olmOCR directories and each sits beside a shard of the same name without the
trailing digits, so they read as interrupted uploads.

The listing is pinned to revision `2ca900fbe14e86c5c83d064d9f0882f1c0b8c05b`,
so the draw can be reproduced whatever Ai2 later changes in the repository.

Sorting by path, the seeded draw, and reading each file from its first
document to its quota are unchanged. The registered reason for a contiguous
block holds for these files as it did for parquet: document order within a
shard is not random, and reading random documents would mean decompressing the
whole shard.

**Effect on the analysis:** none. The subsets, volumes, seed, order and
counting rules are as registered.

**When:** 25 September 2026, from the listing, before any frame was counted.
Settling the format meant reading documents from 68 shards, 63 of them olmOCR
for the redaction check in S3-D2, and counting words but no frames in six of
them to test the reader.

### S3-D2. Two problems in `olmocr_science_pdfs`

**Registered:** in Data collection procedures, "The corpus is counted as the
model received it", and a draw in which every file is equally likely, each read
to a quota of 1,000,000 words, with a short file's shortfall made up from the
next one.

**What happened:**

1. **Redaction.** The dataset card says some olmOCR documents were redacted
   after Olmo 3 7B was trained, their text replaced with `[REMOVED]`. In 60
   olmOCR shards picked at random for this check, reading the first 3 MB of
   each, 668 of 8,582 documents were redacted, about 8%, spread over 34 of the
   shards. Every redaction replaced the whole text. The model saw those
   documents and this study cannot.
2. **File sizes.** olmOCR's shards come in two families. 26,615 zstd shards,
   median 27 MB, hold 80% of the subset's compressed bytes; 78,137 gzip
   shards, median 0.5 MB, hold 20%. The families mostly divide by topic:
   science, maths and technology and health are zstd, while education,
   finance, literature, history, religion and most of the smaller topics are
   gzip. A zstd shard fills its million-word quota. A gzip shard of median size
   holds roughly 200,000 words, so it gives all it has and the draw moves on.
   With every file equally likely, the gzip topics supply far more of the drawn
   words than their share of the subset. Estimated from file sizes, science,
   maths and technology is 57% of the subset's bytes and would supply about 27%
   of the drawn words; literature, religion and history together are under 5%
   of the bytes and would supply about a fifth of the words.

   The same mechanism is mild in `stack_edu`, where Markdown is 24% of the
   bytes and 18% of the files, and absent in `common_crawl`, where each topic's
   share of files is within a point of its share of bytes.

**What is done instead:**

- The registered draw is kept, and redacted documents are counted as
  registered. `[REMOVED]` counts as one word and matches no frame, so each
  redacted document adds one word to the denominator. Every file's record
  carries its number of redacted documents, so those words can be taken back
  out exactly. The write-up says the olmOCR rate describes the unredacted
  documents only.
- The olmOCR rate is reported with each topic's share of the drawn words
  beside its share of the subset's compressed bytes at the pinned revision,
  counting a topic split into part directories once. The run records every
  directory's files and bytes from the listing it draws from.
- As exploratory analysis, the per-topic rates reweighted to those byte
  shares, over the topics the draw reached, and the whole-mix comparison
  recomputed with that rate in olmOCR's place. Compressed bytes are the only
  size the repository publishes per file, and gzip packs text less tightly
  than zstd, so byte shares somewhat overstate the gzip topics and the
  reweighting corrects only part of the imbalance.

**Effect on the analysis:** none on the primary comparison, which uses
`common_crawl` alone. The whole-mix figure, the secondary comparison, carries
olmOCR at its 13.57% token share. If the humanities topics use the frames more
than science and medicine do, the draw raises the olmOCR rate, which raises the
whole-mix input rate and makes any amplification look smaller: a bias against
the finding H1 predicts. What the redacted documents would have contributed is
unknown. The placeholder text itself is negligible: in the one olmOCR shard read
to its quota while testing the reader, it came to 29 words out of 1,025,431.

**When:** 25 September 2026, before any frame was counted.

### Study 3's OSF update

S3-D1 and S3-D2 were submitted as one update to the registration on 27
September 2026, citing this file at commit `e45f5d3`, and the update was
approved the same day. These are its changes, answer by answer, each marked
with the deviation it comes from. Answers not listed are unchanged.

#### Data Description: Datasets used

**S3-D1.** Replace

> allenai/dolma3_mix-6T-1025, the stage-1 pretraining mix for Olmo 3: 5.93
> trillion tokens over 3.87 billion documents, stored as parquet, published by
> Ai2.

with

> allenai/dolma3_mix-6T-1025-7B, the stage-1 pretraining mix for Olmo 3 7B:
> 5.93 trillion tokens over 3.87 billion documents, published by Ai2 as JSON
> Lines compressed with zstd or, for part of olmocr_science_pdfs, gzip. It was
> registered as allenai/dolma3_mix-6T-1025, which now redirects here.

**S3-D2.** After the paragraph giving the composition, add

> Ai2 has redacted some olmocr_science_pdfs documents since Olmo 3 7B was
> trained, replacing their text with [REMOVED]. In the first 3 MB of 60 olmOCR
> shards chosen at random, 668 of 8,582 documents were redacted, about 8%. The
> olmOCR rate therefore describes the unredacted documents only.

#### Data Description: Data identifiers

**S3-D1.** Replace

> <https://huggingface.co/datasets/allenai/dolma3_mix-6T-1025> — the model it
> trained: <https://huggingface.co/allenai/Olmo-3-1025-7B>

with

> <https://huggingface.co/datasets/allenai/dolma3_mix-6T-1025-7B> at revision
> 2ca900fbe14e86c5c83d064d9f0882f1c0b8c05b, to which the listing and the draw
> are pinned. Registered as
> <https://huggingface.co/datasets/allenai/dolma3_mix-6T-1025>, which redirects
> there. The model it trained: <https://huggingface.co/allenai/Olmo-3-1025-7B>

#### Data Description: Data collection procedures

**S3-D1.** Replace step 1

> 1\. List the subset's parquet files from the repository, sorted by path.

with

> 1\. List the subset's data files at the pinned revision, sorted by path. A
> data file ends .jsonl.zst or .jsonl.gz and sits in a directory named for the
> subset alone or for the subset followed by a hyphen and a topic, language or
> part, as in data/common_crawl-politics-0016/. 387 files beside olmOCR
> shards, named like shard_00000032.jsonl.zst338588528, are left out as
> interrupted uploads.

**S3-D1.** In step 3, replace

> Read each drawn file from its first row, counting words with
> python/framecount.word_count, and stop at the file's quota.

with

> Read each drawn file from its first document, counting words with
> python/framecount.word_count, and stop at the document that brings the file
> to its quota.

**S3-D1 and S3-D2.** Replace step 4

> 4\. Record, per file: path, rows read, words counted, and hits per frame.

with

> 4\. Record, per file: path, documents read, words counted, hits per frame,
> redacted documents and the file's size; and per subset, the files and bytes
> in each directory.

**S3-D1.** Replace

> because parquet row order is not random and a random-row draw would mean
> reading the whole file anyway.

with

> because document order within a shard is not random and a random draw of
> documents would mean decompressing the whole shard anyway.

**S3-D2.** After "The corpus is counted as the model received it, which is the
rule Study 2 applies to generated text.", add

> The exception is outside this study's control: olmOCR documents Ai2 redacted
> after training read [REMOVED]. They are counted as they stand, adding one
> word each and no hits, and each file's record gives their number so those
> words can be taken back out.

**S3-D2.** At the end, add

> olmOCR's files differ in size by topic. Science, maths and technology and
> health, which hold most of its bytes, are stored in large shards, and most
> other topics in small ones. Every file is equally likely to be drawn, so the
> draw over-represents the topics in small files against their share of the
> subset. The draw is kept as registered and its composition is reported,
> under Reliability and Robustness Testing.

#### Knowledge of Data: Prior knowledge

**S3-D1.** Replace

> The author (sole author) has not drawn, read or counted any part of Dolma 3,
> and has seen no frame count from it.

with

> At submission, the author (sole author) had not drawn, read or counted any
> part of Dolma 3, and had seen no frame count from it. Since then, and before
> the draw, documents from 68 shards were read to settle the file format and
> check the redactions, and words were counted in six of them to test the
> reader. No frame has been counted in Dolma 3 and no frame count from it has
> been seen.

#### Analyses: Reliability and Robustness Testing

**S3-D2.** At the end, add

> The olmocr_science_pdfs rate is reported with each topic's share of the
> drawn words beside its share of the subset's compressed bytes at the pinned
> revision, counting a topic split into part directories once, because the
> draw over-represents the topics stored in small files (see Data collection
> procedures).

#### Analyses: Exploratory analysis

**S3-D2.** At the end of the list, add

> - The olmocr_science_pdfs per-topic rates reweighted to each topic's share
>   of the subset's compressed bytes, over the topics the draw reached, and the
>   whole-mix comparison recomputed with that rate. gzip packs text less
>   tightly than zstd, so byte shares overstate the topics stored with gzip and
>   the reweighting corrects only part of the imbalance.

## Study 4

Every departure from the registration at <https://osf.io/d79u4> and the
protocol it specifies the study through, each recorded before the analysis was
run. All but S4-D3 are also filed as an update on the OSF registration.

### S4-D1. One directory pattern in the protocol matches nothing

**Registered:** the registration allocates the midtraining sample across "the
24 sources" of the dataset card. The protocol it specifies the study through,
`docs/study4-protocol.md`, gives each source's directory pattern, and for
StackEdu (FIM) that pattern is `stack_edu-fim-*`.

**What happened:** at the pinned commit no directory matches
`stack_edu-fim-*`. The source's 474 files sit in 60 directories named
`stack_edu-fim_vigintile_*`, with an underscore where the pattern has a
hyphen. Checked on 29 September 2026 against the full listing, while writing
the counting code: every other pattern matches its source's directories, and
no directory is claimed by two sources.

**What is done instead:** the pattern is read as `stack_edu-fim_*`, which
matches those 60 directories and nothing else, so StackEdu (FIM) is sampled at
its registered allocation of 24,023,062 words like every other source.

**Effect on the analysis:** none on the registered design. The registration
names the source and its share; only the protocol's pattern was wrong, and no
other reading of it is possible. Without the correction the source would have
no files and the sample could not be drawn as registered.

**When:** 29 September 2026, after registration and before any Study 4 text
was generated or any frame counted in its data.

### S4-D2. The DPO set holds 259,922 pairs

**Registered:** in Study design, "all 260,000 pairs", and in Sample size, "DPO:
260,000 pairs". The protocol gives the same figure.

**What happened:** the count read every row of the set's four parquet files at
the pinned commit and found 259,922 pairs: 64,981, 64,981, 64,980 and 64,980.
The dataset card at that commit records the same number in its metadata
(`num_examples: 259922`). Its prose gives 260,000, the sum of 125,000, 125,000
and 10,000 pairs from its three components, and the registration and protocol
quoted that.

**What is done instead:** nothing. The registered rule is every pair at the
pinned commit, and every pair was counted. The write-up gives 259,922.

**Effect on the analysis:** none.

**When:** 29 September 2026, from the check of the count's totals, after the
count and before the analysis was run.

### S4-D3. SFT conversations are identified by file and row

**Registered:** the protocol records, per SFT conversation, "`id`,
`source_dataset`, words and hits per frame".

**What happened:** the counting code identifies each conversation by its
parquet file and row number, as in `train-00000-of-00015:52`, the way the
protocol identifies DPO pairs, and does not record the `id` field.

**What is done instead:** the file and row stand as the identifier. At the
pinned commit they locate each conversation exactly.

**Effect on the analysis:** none. The analysis uses each conversation's words,
hits and `source_dataset`, all recorded as registered. No registration answer
mentions the identifier, so this is recorded here and not filed on OSF.

**When:** 29 September 2026, after the count and before the analysis was run.

### S4-D4. Redacted documents in the midtraining olmOCR source

**Registered:** the midtraining draw reads whole documents, allocated so that
"the pooled sample is the mix as the model saw it". Neither the registration
nor the protocol mentions redaction.

**What happened:** as Study 3 found in stage 1 (S3-D2), Ai2 has replaced the
text of some olmOCR documents with `[REMOVED]` since the model was trained. Of
the 2,446 documents the draw read from OLMOCR Science PDFs (High Q.), 353 were
redacted. The model saw those documents and this study cannot.

**What is done instead:** redacted documents are counted as they stand, as
Study 3 counted them. `[REMOVED]` is one word and matches no frame, and every
file's record gives its number of redacted documents.

**Effect on the analysis:** the source reached its allocation from its
unredacted documents, so its rate describes those only. What the redacted
documents would have contributed is unknown. The source holds 5.0% of the
midtraining sample's words, and the placeholders add 353 words to the sample's
240 million.

**When:** the counting code set this handling before the count, at commit
`1d0bd82`. The count found how many documents it covers, and this entry was
recorded on 29 September 2026, before the analysis was run.

### Study 4's OSF update

S4-D1, S4-D2 and S4-D4 were submitted as one update to the registration on 29
September 2026 at 13:04 UTC, and the update was approved the same day, before
the analysis was run. It changes three answers, filed word for word as below,
checked against OSF's API. Its justification names this file but no commit;
GitHub then held `0f2b6b2`, the first commit to hold S4-D2 to S4-D4. Answers
not listed are unchanged.

#### Research Design: Study design

**S4-D2.** In the list of input sources, replace

> all 260,000 pairs

with

> all 259,922 pairs

#### Sampling: Data collection procedures

**S4-D1.** After the paragraph beginning "Midtraining draw.", add

> One directory pattern in docs/study4-protocol.md is corrected. The protocol
> gives StackEdu (FIM)'s directories as stack_edu-fim-*, which matches no
> directory at the pinned commit; the source's 474 files are in 60 directories
> named stack_edu-fim_vigintile_*, and the draw reads the pattern as
> stack_edu-fim_*. No other reading is possible, and nothing else changes. This
> is deviation S4-D1 in docs/deviations.md.

**S4-D4.** After that, add

> As in Study 3, Ai2 has redacted some olmOCR documents since the model was
> trained, replacing their text with [REMOVED]. They are counted as they
> stand, adding one word each and no hits, and each file's record gives their
> number. The draw read 2,446 documents from OLMOCR Science PDFs (High Q.), of
> which 353 were redacted, so that source's rate describes its unredacted
> documents only. This is deviation S4-D4 in docs/deviations.md.

#### Sampling: Sample size

**S4-D2.** Replace

> DPO: 260,000 pairs.

with

> DPO: 259,922 pairs, which the dataset card's description rounds to 260,000.

The justification OSF asks for:

> Corrects two clerical errors and records one counting rule. The protocol's
> directory pattern for one midtraining source matched no directory; this was
> found while writing the counting code, before any of the study's text was
> generated or any frame counted in its data. The registration gave the DPO
> set as 260,000 pairs, the dataset card's rounded description; the set holds
> 259,922, and every pair was counted as registered. Redacted olmOCR documents
> in the midtraining sample are counted as they stand, as in Study 3; the
> counting code set this before the count, and the count found 353. The last
> two were recorded after the count and before the analysis was run.
