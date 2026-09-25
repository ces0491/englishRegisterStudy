"""Checks on Study 3's draw and reader, without touching the corpus.

The counting pass itself can only be verified by running it. What can be
checked here is that the code implements the sampling frame registered at
https://osf.io/ngt3m: the subsets, the volumes, a draw that is deterministic,
seeded per subset, and without replacement, and a reader that takes each file
from its first document to its quota.

The paths below follow the repository's real layout, including the partial
uploads beside some olmOCR shards.
"""

import gzip
import io
import json
from pathlib import Path

import pytest

import framecount
from count_dolma import (FILES_OTHER, FILES_PRIMARY, PRIMARY, REDACTED, SEED,
                         SUBSETS, WORDS_PER_FILE, FileCount, count_file,
                         directory_sizes, documents, draw, enough, files_drawn,
                         subset_files, subset_of, topic_of, totals,
                         words_wanted)

REPO = Path(__file__).resolve().parent.parent

PATHS = [
    "data/common_crawl-politics-0016/shard_00000052.jsonl.zst",
    "data/common_crawl-adult_content-0017/shard_00000026.jsonl.zst",
    "data/common_crawl-adult_content-0017/shard_00000014.jsonl.zst",
    "data/stack_edu-Markdown/shard_00000001.jsonl.zst",
    "data/stack_edu-Markdown/notes-about-common_crawl.jsonl.zst",
    "data/finemath-3plus/shard_00000000.jsonl.zst",
    "data/olmocr_science_pdfs-literature/literature-9501.jsonl.gz",
    "data/olmocr_science_pdfs-health/shard_00000032.jsonl.zst",
    "data/olmocr_science_pdfs-health/shard_00000032.jsonl.zst338588528",
    "data/common_crawl_extra/shard_00000000.jsonl.zst",
    "README.md",
    ".gitattributes",
    "dolma-mix.png",
]


def test_subsets_and_volumes_match_the_sampling_frame():
    assert set(SUBSETS) == {
        "common_crawl", "olmocr_science_pdfs", "stack_edu", "finemath-3plus",
        "rpj-proofpile-arxiv", "dolma1_7-wiki-en"}
    assert PRIMARY == "common_crawl"
    assert SEED == 20260925
    assert WORDS_PER_FILE == 1_000_000
    assert (FILES_PRIMARY, FILES_OTHER) == (200, 20)
    assert words_wanted(PRIMARY) == 200_000_000
    assert words_wanted("stack_edu") == 20_000_000
    assert files_drawn(PRIMARY) == 200
    # The published shares should account for the whole mix.
    assert abs(sum(SUBSETS.values()) - 1.0) < 0.001


def test_subset_files_matches_the_directory_name_sorted():
    assert subset_files(PATHS, "common_crawl") == [
        "data/common_crawl-adult_content-0017/shard_00000014.jsonl.zst",
        "data/common_crawl-adult_content-0017/shard_00000026.jsonl.zst",
        "data/common_crawl-politics-0016/shard_00000052.jsonl.zst",
    ]
    # A stack_edu file whose name mentions common_crawl belongs to stack_edu.
    assert "data/stack_edu-Markdown/notes-about-common_crawl.jsonl.zst" in \
        subset_files(PATHS, "stack_edu")
    assert subset_files(PATHS, "finemath-3plus") == [
        "data/finemath-3plus/shard_00000000.jsonl.zst"]


def test_a_directory_prefix_must_end_at_a_hyphen():
    assert subset_of("data/common_crawl_extra/shard_00000000.jsonl.zst") is None


def test_both_compressions_count_and_partial_uploads_do_not():
    assert subset_files(PATHS, "olmocr_science_pdfs") == [
        "data/olmocr_science_pdfs-health/shard_00000032.jsonl.zst",
        "data/olmocr_science_pdfs-literature/literature-9501.jsonl.gz",
    ]
    for path in ("README.md", ".gitattributes", "dolma-mix.png"):
        assert subset_of(path) is None


def test_every_data_file_belongs_to_at_most_one_subset():
    claimed = [p for s in SUBSETS for p in subset_files(PATHS, s)]
    assert len(claimed) == len(set(claimed)) == 8


def test_topic_of_merges_numbered_and_part_directories():
    assert topic_of("common_crawl-politics-0016", "common_crawl") == "politics"
    assert topic_of("common_crawl-adult_content-0017",
                    "common_crawl") == "adult_content"
    assert topic_of("olmocr_science_pdfs-electronics_and_hardware-part1",
                    "olmocr_science_pdfs") == "electronics_and_hardware"
    assert topic_of("olmocr_science_pdfs-health",
                    "olmocr_science_pdfs") == "health"
    assert topic_of("stack_edu-Markdown", "stack_edu") == "Markdown"
    assert topic_of("finemath-3plus", "finemath-3plus") == "finemath-3plus"
    with pytest.raises(ValueError):
        topic_of("stack_edu-Markdown", "common_crawl")


def test_directory_sizes_sums_files_and_bytes_per_directory():
    sizes = {
        "data/olmocr_science_pdfs-health/shard_00000032.jsonl.zst": 100,
        "data/olmocr_science_pdfs-health/shard_00000033.jsonl.zst": 50,
        "data/olmocr_science_pdfs-health/shard_00000032.jsonl.zst338588528": 7,
        "data/olmocr_science_pdfs-literature/literature-9501.jsonl.gz": 3,
        "data/common_crawl-politics-0016/shard_00000052.jsonl.zst": 1000,
    }
    assert directory_sizes(sizes, "olmocr_science_pdfs") == {
        "olmocr_science_pdfs-health": {"topic": "health", "files": 2,
                                       "bytes": 150},
        "olmocr_science_pdfs-literature": {"topic": "literature", "files": 1,
                                           "bytes": 3},
    }


def test_draw_is_deterministic_and_subset_specific():
    paths = [f"data/common_crawl-politics-0016/shard_{i:08d}.jsonl.zst"
             for i in range(50)]
    first = draw(paths, "common_crawl")
    assert first == draw(paths, "common_crawl")
    assert first != draw(paths, "stack_edu")
    assert sorted(first) == sorted(paths)  # a permutation, nothing dropped
    assert len(set(first)) == len(paths)   # without replacement


def test_draw_refuses_an_empty_listing():
    with pytest.raises(ValueError):
        draw([], "common_crawl")


def jsonl(rows) -> bytes:
    return "".join(json.dumps(row) + "\n" for row in rows).encode("utf-8")


ROWS = [{"id": "a", "text": "Here's the thing: it works."},
        {"id": "b", "text": "Second document.", "metadata": {"x": 1}}]


def test_documents_reads_gzip_in_order():
    handle = io.BytesIO(gzip.compress(jsonl(ROWS)))
    got = list(documents(handle, "data/x-y/shard.jsonl.gz"))
    assert [d["id"] for d in got] == ["a", "b"]


def test_documents_reads_every_zstd_frame():
    zstandard = pytest.importorskip("zstandard")
    compressor = zstandard.ZstdCompressor()
    # Two frames back to back, as a shard written in pieces would be.
    raw = compressor.compress(jsonl(ROWS[:1])) + compressor.compress(jsonl(ROWS[1:]))
    got = list(documents(io.BytesIO(raw), "data/x-y/shard.jsonl.zst"))
    assert [d["id"] for d in got] == ["a", "b"]


def test_documents_refuses_anything_else():
    with pytest.raises(ValueError):
        list(documents(io.BytesIO(b""), "data/x-y/shard.jsonl.zst338588528"))


FRAMES = framecount.load_frames(REPO / "data" / "frames.csv")


def test_count_file_stops_at_the_document_that_crosses_the_quota():
    docs = iter([{"text": "one two three four five"} for _ in range(10)])
    record = count_file("f", docs, FRAMES, quota=12)
    assert (record.rows, record.words) == (3, 15)
    # The rest of the file is left unread.
    assert len(list(docs)) == 7


def test_count_file_counts_frames_and_empty_rows():
    docs = [{"text": "Here's the thing: it works."}, {"text": ""},
            {"text": None}]
    record = count_file("f", docs, FRAMES)
    assert record.rows == 3
    assert record.words == 6
    assert record.hits["F01"] == 1
    assert set(record.hits) == set(FRAMES)


def test_count_file_counts_and_records_redacted_documents():
    docs = [{"text": REDACTED}, {"text": " [REMOVED]\n"},
            {"text": "A text that mentions [REMOVED] in passing."}]
    record = count_file("f", docs, FRAMES)
    assert record.rows == 3
    assert record.redacted == 2
    marker = framecount.word_count(framecount.tokenise(REDACTED))
    assert marker == 1
    assert record.words == 2 * marker + 7


def test_count_file_fails_loudly_without_a_text_field():
    with pytest.raises(RuntimeError, match="no text field"):
        count_file("f", [{"id": "a", "content": "x"}], FRAMES)


def test_totals_sum_words_hits_and_redactions():
    counts = [
        FileCount("a", rows=10, words=100, hits={"F01": 2, "F02": 0},
                  redacted=1),
        FileCount("b", rows=5, words=50, hits={"F01": 1, "F02": 3}),
    ]
    assert totals(counts) == {
        "files": 2, "rows": 15, "words": 150, "redacted": 1,
        "F01": 3, "F02": 3}


def test_enough_uses_the_registered_quota():
    short = [FileCount("a", 1, 19_999_999, {})]
    assert not enough(short, "stack_edu")
    assert enough(short + [FileCount("b", 1, 1, {})], "stack_edu")
    # The primary subset wants ten times as much.
    assert not enough(short, PRIMARY)
