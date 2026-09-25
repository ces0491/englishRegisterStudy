# The frame-to-raw-text mapping

Study 1 counted the frozen frames through GloWbE's interface, which matches a
stream of tokens: clitics split off, punctuation as its own token. Studies 2
and 3 count the same frames in raw model output and in Dolma, where none of
that holds. This document defines how, and `python/framecount.py` implements
it. Both are frozen with the frames and go into Study 2's registration.

If the two studies counted differently, the comparison between them — which is
what Study 3 exists to make — would mean nothing.

## The rules

**1. Normalise.** Apply Unicode NFKC, then fold the punctuation a model or a
web page uses to the ASCII the corpus has: curly quotes and apostrophes to `'`
and `"`, non-breaking and thin spaces to a space, zero-width space to nothing,
the ellipsis character to three full stops. En dashes, em dashes and minus
signs fold to a hyphen with spaces around it, so that a dash between words
stays a token of its own while a hyphen inside a word does not. Then
lowercase.

**2. Separate lone apostrophes.** An apostrophe that begins or ends a word
becomes its own token: a quotation mark, or the possessive in `writers'`. A
clitic's apostrophe is word-internal at this point and survives.

**3. Split clitics.** `n't`, `'s`, `'re`, `'ve`, `'ll`, `'d`, `'m` each become
their own token, in that order, so `isn't` becomes `is n't` rather than
`isn ' t`. This is what the frozen queries assume: `here 's the thing`,
`is n't just`.

**4. Read off the tokens.** A token is a clitic, a word, or a single
punctuation character. A word may contain hyphens: `sad-but-true` is one token,
because that is what the corpus does.

**Matching.** A frozen query is its tokens, whitespace-separated, exactly as
`data/frames.csv` holds it. `*` matches exactly one token of any kind,
punctuation included. Matches may overlap, and may cross a sentence boundary,
because the corpus indexes a flat stream of tokens.

**Word counts.** A rate needs a denominator. A word is a token containing at
least one word character, so punctuation tokens do not count and clitics do:
`here 's the thing .` is four words.

## Where this is an approximation

- **GloWbE's own tokeniser is not published.** These rules were inferred from
  the form the queries have to take in the interface. They reproduce the
  clitic and punctuation behaviour the frozen queries depend on, and nothing
  guarantees they agree on every edge case.
- **Decimals and abbreviations.** `3.5` becomes `3 . 5`, and `e.g.` becomes
  `e . g .`. Neither appears in a frozen frame, but both shift the positions a
  wildcard counts, so they reach F02, F08 and F10. Whether the corpus does the
  same is unknown.
- **Word counts are not GloWbE's word counts.** Study 1's denominators come
  from the corpus's own composition table, computed however Davies computed
  them. The rule above is this study's, applied identically to model output
  and to Dolma. Comparisons within Studies 2 and 3 are therefore on one
  footing; a comparison of their rates against Study 1's carries this
  difference and the write-up has to say so.
- **F06 is countable here.** `it 's not * , it 's` is seven tokens, which a
  free GloWbE account refuses (deviation D2), but raw text has no such limit.
  Studies 2 and 3 report all fifteen frames, and any comparison back to Study 1
  uses the fourteen it could count.

## Checked against the interface

**Case is ignored, 25 September 2026.** Searching `Here 's the thing` with a
capital returns exactly what the lowercase query returns: 2,728 overall, and
US 1,109, GB 440, IE 134, AU 211, ZA 62, with the general and blog sections
matching F01's recorded cells. So rule 1's lowercasing reproduces the corpus's
behaviour rather than merely defining this study's. Worth recording because
the interface's own help implies a capitalised query forces a case-sensitive
match, and on this evidence it does not.

**A wildcard slot holds one word, hyphens included, 25 September 2026.** The
List display for `here 's the * part` returns 126 distinct forms totalling 481,
which is the count the Chart gives for the same query. Among them are
`here 's the sad-but-true part`, `non-intuitive`, `mind-bending`,
`hand-waving` and `less-exciting`, so the corpus fills a single-token slot with
a hyphenated compound. Rule 4 was changed to match: an earlier version split
`sad-but-true` into five tokens and would have missed those hits silently.

The same display speaks to F02's precision, which the registration lists as an
exploratory check for the partial frames. Every form in the top hundred is an
adjective or a noun in the slot — best, fun, good, tricky, interesting — with
no punctuation and nothing outside the construction.

**Matches cross sentence boundaries, 25 September 2026.** `thing . here`, a
sequence that can only occur across a full stop, returns 160 hits: US 50,
GB 32, AU 16, IE 3, ZA 3. The corpus indexes a flat stream in which a full stop
is a token like any other, which is what the matching rule above assumes. No
frozen frame contains a full stop, so this reaches only the frames whose
wildcard could land on one: F02, F08 and F10.

## Verification

`python/test_framecount.py` holds a passage written to contain every frame at
least once, counted by hand before the tests were run, with the hand counts as
the expected values. It also checks the clitic, apostrophe, punctuation and
wildcard rules one at a time.

Run from the repository root:

```
python -m pytest python -q
```
