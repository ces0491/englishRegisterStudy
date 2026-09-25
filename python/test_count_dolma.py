"""Checks on Study 3's draw, without touching the corpus.

The counting pass itself can only be verified by running it. What can be
checked here is that the code implements the sampling frame registered at
https://osf.io/ngt3m: the subsets, the volumes, and a draw that is
deterministic, seeded per subset, and without replacement.
"""

import pytest

from count_dolma import (FILES_OTHER, FILES_PRIMARY, PRIMARY, SEED, SUBSETS,
                         WORDS_PER_FILE, FileCount, draw, enough, files_drawn,
                         subset_files, totals, words_wanted)

PATHS = [
    "data/common_crawl/part-00000.parquet",
    "data/common_crawl/part-00001.parquet",
    "data/common_crawl/part-00002.parquet",
    "data/stack_edu/part-00000.parquet",
    "data/stack_edu/notes-about-common_crawl.parquet",
    "data/finemath-3plus/part-00000.parquet",
    "README.md",
    "data/common_crawl/index.json",
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


def test_subset_files_matches_a_directory_not_a_substring():
    got = subset_files(PATHS, "common_crawl")
    assert got == [
        "data/common_crawl/part-00000.parquet",
        "data/common_crawl/part-00001.parquet",
        "data/common_crawl/part-00002.parquet",
    ]
    # A stack_edu file whose name mentions common_crawl belongs to stack_edu.
    assert "data/stack_edu/notes-about-common_crawl.parquet" in \
        subset_files(PATHS, "stack_edu")


def test_draw_is_deterministic_and_subset_specific():
    paths = [f"data/common_crawl/part-{i:05d}.parquet" for i in range(50)]
    first = draw(paths, "common_crawl")
    assert first == draw(paths, "common_crawl")
    assert first != draw(paths, "stack_edu")
    assert sorted(first) == sorted(paths)  # a permutation, nothing dropped
    assert len(set(first)) == len(paths)   # without replacement


def test_draw_refuses_an_empty_listing():
    with pytest.raises(ValueError):
        draw([], "common_crawl")


def test_totals_sum_words_and_hits():
    counts = [
        FileCount("a.parquet", rows=10, words=100, hits={"F01": 2, "F02": 0}),
        FileCount("b.parquet", rows=5, words=50, hits={"F01": 1, "F02": 3}),
    ]
    assert totals(counts) == {
        "files": 2, "rows": 15, "words": 150, "F01": 3, "F02": 3}


def test_enough_uses_the_registered_quota():
    short = [FileCount("a", 1, 19_999_999, {})]
    assert not enough(short, "stack_edu")
    assert enough(short + [FileCount("b", 1, 1, {})], "stack_edu")
    # The primary subset wants ten times as much.
    assert not enough(short, PRIMARY)
