"""Checks on the tables count_generated.py writes.

Study 2's per-generation counts must add back up to the condition totals the
analysis uses. Study 3's by-topic table carries deviation S3-D2's report:
olmOCR's drawn words by topic against each topic's share of the subset's bytes.
"""

import json

from count_generated import count_file, dolma_topic_rows

FRAMES = {"F01": ["here", "'s", "the", "thing"], "F09": ["is", "n't", "just"]}


def test_per_generation_counts_add_up_to_the_condition(tmp_path):
    records = [
        {"topic_id": "T0001", "pass_number": 1, "finish_reason": "stop",
         "text": "Here's the thing: it isn't just a phone. Here's the thing."},
        {"topic_id": "T0002", "pass_number": 1, "finish_reason": "stop",
         "text": ""},
        {"topic_id": "T0003", "pass_number": 1, "finish_reason": "length",
         "text": "It isn't just"},
    ]
    path = tmp_path / "base-1.0.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in records),
                    encoding="utf-8")
    totals = count_file(path, FRAMES)
    texts = totals["texts"]
    assert [(t["source"], t["topic_id"], t["finish_reason"]) for t in texts] == [
        ("base-1.0", "T0001", "stop"), ("base-1.0", "T0002", "stop"),
        ("base-1.0", "T0003", "length")]
    assert [(t["F01"], t["F09"], t["words"]) for t in texts] == [
        (2, 1, 14), (0, 0, 0), (0, 1, 4)]
    for key in ("F01", "F09", "words"):
        assert sum(t[key] for t in texts) == totals[key]
    assert totals["empty_generations"] == 1

RESULT = {
    "subset": "olmocr_science_pdfs",
    "totals": {"words": 150, "rows": 3, "redacted": 1, "files": 3,
               "F01": 3, "F02": 1},
    "directories": {
        "olmocr_science_pdfs-health": {
            "topic": "health", "files": 10, "bytes": 1000},
        "olmocr_science_pdfs-electronics_and_hardware-part1": {
            "topic": "electronics_and_hardware", "files": 5, "bytes": 50},
        "olmocr_science_pdfs-electronics_and_hardware-part2": {
            "topic": "electronics_and_hardware", "files": 4, "bytes": 40},
        "olmocr_science_pdfs-games": {"topic": "games", "files": 2, "bytes": 5},
    },
    "per_file": [
        {"path": "data/olmocr_science_pdfs-health/shard_00000001.jsonl.zst",
         "rows": 1, "words": 100, "hits": {"F01": 2, "F02": 1},
         "redacted": 0, "size": 100},
        {"path": "data/olmocr_science_pdfs-electronics_and_hardware-part1/"
                 "hardware-1.jsonl.gz",
         "rows": 1, "words": 30, "hits": {"F01": 1, "F02": 0},
         "redacted": 1, "size": 3},
        {"path": "data/olmocr_science_pdfs-electronics_and_hardware-part2/"
                 "hardware-2.jsonl.gz",
         "rows": 1, "words": 20, "hits": {"F01": 0, "F02": 0},
         "redacted": 0, "size": 2},
    ],
}


def by_topic(rows):
    out = {}
    for row in rows:
        out.setdefault(row["topic"], []).append(row)
    return out


def test_one_row_per_topic_and_frame_including_undrawn_topics():
    rows = dolma_topic_rows(RESULT)
    assert len(rows) == 3 * 2
    assert {row["source"] for row in rows} == {"olmocr_science_pdfs"}
    games = by_topic(rows)["games"]
    assert [(r["frame_id"], r["hits"], r["words"], r["files_drawn"])
            for r in games] == [("F01", 0, 0, 0), ("F02", 0, 0, 0)]
    assert games[0]["bytes"] == 5


def test_part_directories_are_summed_into_their_topic():
    hardware = by_topic(dolma_topic_rows(RESULT))["electronics_and_hardware"]
    first = hardware[0]
    assert (first["files_available"], first["bytes"]) == (9, 90)
    assert (first["files_drawn"], first["words"], first["redacted"]) == (2, 50, 1)
    assert [r["hits"] for r in hardware] == [1, 0]


def test_topics_add_back_up_to_the_subset():
    rows = dolma_topic_rows(RESULT)
    words = {r["topic"]: r["words"] for r in rows}
    assert sum(words.values()) == RESULT["totals"]["words"]
    for frame_id in ("F01", "F02"):
        assert sum(r["hits"] for r in rows if r["frame_id"] == frame_id) == \
            RESULT["totals"][frame_id]
