#!/usr/bin/env python
"""Draw the topics Study 2 generates on, from GloWbE's own page titles.

Study 2 asks whether a model's default register resembles the American end of
Study 1. Topics are a confound: if the model writes about different things from
the corpus, a difference in frame rates could be a difference in subject
matter. So the topics are the corpus's own, sampled from the titles of blog
pages in the five varieties.

The draw is deterministic given the seed, and the rules below are registered
with the protocol, so anyone can reproduce `data/topics.csv` exactly.

The metadata is the "download metadata" link on the GloWbE TEXTS page: a zip
holding glowbe_sources.txt, one row per page with its word count, country,
genre, URL and title. It is third-party data and is not committed here.

Usage:
  python python/sample_topics.py path/to/glowbe_sources.txt
"""

from __future__ import annotations

import csv
import random
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

VARIETIES = ("US", "GB", "IE", "AU", "ZA")
PER_VARIETY = 800
SEED = 20260925
MIN_WORDS = 4
MAX_WORDS = 18

# Titles carry the site name after a separator often enough to matter: "a
# million dresses | UK Fashion and Lifestyle Blog: Going Copper!". The part
# before the first separator is the topic, when enough of it is left.
SEPARATORS = ("|", "»", "–", "—", " - ", "::")
WORD_RE = re.compile(r"[a-z][a-z'-]*", re.IGNORECASE)


def clean_title(title: str) -> str | None:
    """A title becomes a topic, or None if it cannot be used.

    Refused: empty titles, titles with fewer than four or more than eighteen
    word tokens, and titles carrying characters that did not survive the
    corpus's own encoding, which would otherwise be handed to a model as if
    they were words.
    """
    title = unicodedata.normalize("NFKC", title).strip()
    if "�" in title or "﻿" in title:
        return None
    if any("" <= ch <= "" for ch in title):
        return None
    # The site name sits on either side: "a million dresses | UK Fashion and
    # Lifestyle Blog: Going Copper!" has it first, "Holiday-substitute chicken
    # pilaf | Yumbolicious" last. Take whichever side carries more words.
    for separator in SEPARATORS:
        if separator not in title:
            continue
        parts = [part.strip() for part in title.split(separator)]
        longest = max(parts, key=lambda part: len(WORD_RE.findall(part)))
        if len(WORD_RE.findall(longest)) >= MIN_WORDS:
            title = longest
            break
    title = re.sub(r"\s+", " ", title).strip(" -–—:|")
    words = WORD_RE.findall(title)
    if not MIN_WORDS <= len(words) <= MAX_WORDS:
        return None
    # Anything outside Latin-1 printable range is a sign the row did not
    # decode cleanly rather than a topic a model should be asked to write on.
    if any(ord(ch) > 0x2122 for ch in title):
        return None
    return title


def domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def read_blog_pages(path: Path):
    """Yield (variety, domain, title) for blog pages in the five varieties."""
    # cp1252, not latin-1: these are web page titles, so byte 0x92 is a
    # curly apostrophe and 0x96 an en dash. Latin-1 would turn both into
    # control characters, and the separator and encoding checks below would
    # then keep site names and damaged rows.
    with open(path, encoding="cp1252", errors="replace", newline="") as handle:
        for line_number, line in enumerate(handle):
            if line_number < 2:  # header, then a row of dashes
                continue
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) < 5:
                continue
            country_genre = fields[2].split()
            if len(country_genre) < 2:
                continue
            variety, genre = country_genre[0], country_genre[1]
            if genre != "B" or variety not in VARIETIES:
                continue
            yield variety, domain(fields[3]), fields[4]


def sample(path: Path):
    """One topic per domain, deduplicated, the same number per variety.

    One per domain because a single prolific blog would otherwise supply
    dozens of topics and carry its own subject matter into the sample. Equal
    numbers per variety because the topics should not be American merely
    because the American component is large.
    """
    by_variety: dict[str, dict[str, str]] = defaultdict(dict)
    for variety, site, title in read_blog_pages(path):
        topic = clean_title(title)
        if topic is None or site in by_variety[variety]:
            continue
        by_variety[variety][site] = topic

    rng = random.Random(SEED)
    rows = []
    for variety in VARIETIES:
        candidates = sorted(by_variety[variety].items())
        seen: set[str] = set()
        unique = []
        for site, topic in candidates:
            key = topic.casefold()
            if key in seen:
                continue
            seen.add(key)
            unique.append((site, topic))
        if len(unique) < PER_VARIETY:
            raise SystemExit(
                f"{variety}: only {len(unique)} usable titles, need {PER_VARIETY}")
        for site, topic in rng.sample(unique, PER_VARIETY):
            rows.append({"variety_source": variety, "site": site, "topic": topic})
    rng.shuffle(rows)
    for index, row in enumerate(rows, start=1):
        row["topic_id"] = f"T{index:04d}"
    return rows


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__.strip().splitlines()[-1])
    rows = sample(Path(sys.argv[1]))
    out = Path(__file__).resolve().parent.parent / "data" / "topics.csv"
    with open(out, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["topic_id", "variety_source", "site", "topic"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} topics written to {out}")


if __name__ == "__main__":
    main()
