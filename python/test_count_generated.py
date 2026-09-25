"""Checks on turning Study 3's per-subset JSON into the by-topic table.

The table carries deviation S3-D2's report: olmOCR's drawn words by topic
against each topic's share of the subset's bytes.
"""

from count_generated import dolma_topic_rows

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
