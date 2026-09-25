"""Count the frozen frames in raw text, the way GloWbE counts them.

The queries in `data/frames.csv` are written in GloWbE's tokenised form:
clitics split off (`here 's the thing`, `is n't just`) and punctuation as its
own token (`it 's not * , it 's`). None of that survives contact with raw model
output or with Dolma, so this module tokenises text the same way and matches
the queries as token sequences.

Studies 2 and 3 both count through here. If they counted differently the
comparison between them, which is the point of Study 3, would mean nothing.

The tokeniser is deliberately bespoke and about thirty lines: it can be written
into a pre-registration in full, and it cannot change under a library update.
It is an approximation of GloWbE's own tokenisation, which is not published.
`docs/frame-mapping.md` records where the approximation is known to differ.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

# Characters a model or a web page may use where the corpus has the plain
# ASCII form. Normalised before anything else, so "here’s" and "here's" are
# the same three tokens.
PUNCTUATION_FOLD = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "′": "'",
    # Dashes fold to a spaced hyphen, so an em dash between words stays its own
    # token. A plain hyphen inside a word does not: the corpus counts
    # "sad-but-true" as one token, which the List display shows.
    "–": " - ", "—": " - ", "―": " - ", "−": " - ",
    " ": " ", " ": " ", " ": " ", "​": "",
    "…": "...",
}

# Clitics the corpus splits into their own token. "n't" first, so that
# "isn't" becomes "is n't" rather than "isn ' t".
CLITICS = ("n't", "'s", "'re", "'ve", "'ll", "'d", "'m")

_CLITIC_RE = re.compile(r"(" + "|".join(re.escape(c) for c in CLITICS) + r")\b")
_LONE_APOSTROPHE_RE = re.compile(r"(?<!\w)'|'(?!\w)")
_WORDLIKE_RE = re.compile(r"\w")

# A token is a clitic, a word (hyphens inside it included), or a single
# punctuation character.
_TOKEN_RE = re.compile(
    r"|".join([*(re.escape(c) for c in CLITICS), r"\w+(?:-\w+)*", r"[^\w\s]"]))

WILDCARD = "*"


def normalise(text: str) -> str:
    """Fold Unicode punctuation to ASCII and lowercase."""
    text = unicodedata.normalize("NFKC", text)
    for source, target in PUNCTUATION_FOLD.items():
        text = text.replace(source, target)
    return text.lower()


def tokenise(text: str) -> list[str]:
    """Split text into GloWbE-style tokens.

    Punctuation becomes its own token, clitics split off the word they attach
    to, and everything is lowercase. A leftover apostrophe that is not a
    clitic - a quotation mark, or a possessive plural as in "writers' " -
    becomes its own token.
    """
    text = normalise(text)
    # Apostrophes that begin or end a word - a quotation mark, or the
    # possessive in "writers' " - separate first. A clitic's apostrophe is
    # word-internal at this point, so it survives to the next step.
    text = _LONE_APOSTROPHE_RE.sub(" ' ", text)
    text = _CLITIC_RE.sub(r" \1", text)
    return _TOKEN_RE.findall(text)


def word_count(tokens: list[str]) -> int:
    """Tokens carrying at least one word character.

    Rates need a denominator, and counting punctuation as words would make one
    corpus's rate depend on how heavily it is punctuated. See
    `docs/frame-mapping.md` on how this compares with GloWbE's own word counts.
    """
    return sum(1 for token in tokens if _WORDLIKE_RE.search(token))


def parse_query(query: str) -> list[str]:
    """A frozen query becomes the token sequence to look for."""
    return query.split()


def count_pattern(tokens: list[str], pattern: list[str]) -> int:
    """How many positions in `tokens` the pattern matches.

    `*` matches exactly one token of any kind, punctuation included. Matches
    may overlap and may cross sentence boundaries, because the corpus indexes
    a flat stream of tokens and its own matching does the same.
    """
    if not pattern:
        raise ValueError("empty pattern")
    width = len(pattern)
    hits = 0
    for start in range(len(tokens) - width + 1):
        window = tokens[start:start + width]
        if all(p == WILDCARD or p == w for p, w in zip(pattern, window)):
            hits += 1
    return hits


def load_frames(path: str | Path) -> dict[str, list[str]]:
    """Frame id to token pattern, from the frozen `data/frames.csv`."""
    with open(path, newline="", encoding="utf-8") as handle:
        return {row["frame_id"]: parse_query(row["query"])
                for row in csv.DictReader(handle)}


def count_frames(text: str, frames: dict[str, list[str]]) -> dict[str, int]:
    """Count every frame in one piece of text, plus its word count."""
    tokens = tokenise(text)
    counts = {frame_id: count_pattern(tokens, pattern)
              for frame_id, pattern in frames.items()}
    counts["words"] = word_count(tokens)
    return counts


def count_corpus(texts, frames: dict[str, list[str]]) -> dict[str, int]:
    """Accumulate counts over an iterable of texts."""
    totals = {frame_id: 0 for frame_id in frames}
    totals["words"] = 0
    totals["texts"] = 0
    for text in texts:
        counts = count_frames(text, frames)
        for key, value in counts.items():
            totals[key] += value
        totals["texts"] += 1
    return totals
