# Study 2: the generation protocol

What gets generated, from which models, on what topics, with which settings.
Registered at <https://osf.io/qjgtc> on 25 September 2026, before any text was
generated, together with the counting layer in `docs/frame-mapping.md`.

Study 2 asks whether a model's default register resembles the American end of
Study 1. Everything below exists to stop the answer depending on something
other than the model: the topics come from the corpus, the prompt says nothing
about style or nationality, and the sampling settings are recorded rather than
left to a library default that may change.

## Models

| Condition | Checkpoint |
|---|---|
| base | `allenai/Olmo-3-1025-7B` |
| instruct | `allenai/Olmo-3-7B-Instruct` |

Olmo because Ai2 publishes the weights and the pretraining corpus, which is
what makes Study 3 possible: Olmo 3's stage-1 pretraining used
`dolma3_6T-mix-1025`, released as `allenai/dolma3_mix-6T-1025`. No other model
family allows the input and the output to be counted on the same scale.

Base and instruct both, reported apart, because they answer different
questions. The base model shows what the pretraining corpus produces. The
instruct model is closer to the prose people actually read, and the difference
between them is what post-training adds. Study 3 compares each against the
corpus, so confounding the two would leave "the data did this" and "the tuning
did this" indistinguishable.

The exact revision of each checkpoint is recorded with the run, because a
Hugging Face repository can be updated in place.

## Topics

4,000 topics, drawn from the titles of GloWbE blog pages by
`python/sample_topics.py` and committed as `data/topics.csv`. The same 4,000
serve every condition, so topic is held constant across models and settings.

The rules, deterministic given seed 20260925:

- Blog-section pages only, from the five varieties in Study 1.
- A title is refused if it does not decode cleanly, or if it carries fewer than
  four or more than eighteen word tokens.
- Where a title contains a separator (`|`, `»`, an en or em dash, ` - `, `::`),
  the side carrying more words is kept, because the site name sits sometimes
  before it and sometimes after.
- One title per domain, so a prolific blog cannot supply dozens of topics and
  carry its subject matter into the sample.
- Duplicate titles within a variety are dropped.
- 800 topics per variety, sampled without replacement, then shuffled and
  numbered. Equal numbers because the topics should not be predominantly
  American merely because the American component is the largest.

About 5% of the drawn topics still carry a site name that no separator rule
caught. They are left as they are: hand-tuning the filter against the topics it
produces would be choosing the sample after seeing it.

## Prompt

One template, identical across conditions:

```
Write a blog post titled: {topic}
```

The prompt names no variety, no register and no style. Asking for "British
English" or "a punchy blog post" would measure instruction-following rather
than default register, which is the thing being measured.

For the instruct model the prompt is the user turn, with the checkpoint's own
chat template and no system prompt. For the base model it is the raw prefix.

## Sampling

Four conditions in total: each model at each of two settings.

| Setting | Values |
|---|---|
| unmodified | temperature 1.0, top-p 1.0 |
| deployment | temperature 0.7, top-p 0.9 |

Unmodified sampling draws from the model's own distribution, which is what
"default register" should mean. The deployment setting is what most software
actually uses, and truncating the tail concentrates output on high-probability
phrasing, which is exactly what the frames measure. Registering both makes the
difference between them a result rather than an unexamined choice.

Fixed across conditions: one generation per topic, maximum 1,024 new tokens,
no repetition or frequency penalty, seed recorded per generation.

## How much text

About 2 million words per condition, so roughly 8 million in total. At Study
1's American rates a mid-frequency frame lands in the hundreds, which keeps
intervals tight, and the rarest frames still carry usable ones.

4,000 topics at around 500 words each gets there. If a condition falls short
because generations run shorter, topics are reused in `topic_id` order with the
seed advanced, and the write-up reports how many generations each condition
needed.

## What is recorded

Every generation is kept with its condition, topic id, checkpoint revision,
sampling settings, seed, and the raw text. Counts come from
`python/framecount.py` with no cleaning of the text beforehand: no
deduplication, no removal of refusals or truncated endings, no stripping of
markdown. Anything removed would be a judgement about what counts as the
model's register, and the register is what is being measured.

Empty generations are recorded as empty and contribute zero words.

## Analysis

The model's frame rates are compared with Study 1's variety rates, frame by
frame and as a composite, using the same Poisson intervals. Study 1's
denominators are GloWbE's own word counts and Study 2's come from the counting
layer's definition, which `docs/frame-mapping.md` notes is not the same
quantity; the comparison carries that.

**The confirmatory condition is the base model at unmodified sampling.** It is
the one Study 3's question is about, and naming it in advance stops four
conditions becoming four chances at a result. The other three are registered
and all four are reported, whatever they show.

Fifteen frames are counted here, including F06, which a free GloWbE account
could not search (deviation D2). Comparisons back to Study 1 use the fourteen
it could count.
