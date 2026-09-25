"""Checks on the parts of the generation run that do not need a GPU.

The run itself can only be verified by running it. What can be checked here is
that the protocol registered at https://osf.io/qjgtc is what the code encodes:
the four conditions, the prompt, the seeds, and the word target.
"""

from pathlib import Path

import pytest

from framecount import word_count, tokenise
from generate import (CONDITIONS, CONFIRMATORY, MAX_NEW_TOKENS, WORD_TARGET,
                      Generation, build_prompt, load_topics, seed_for,
                      words_so_far)

REPO = Path(__file__).resolve().parent.parent


def test_conditions_match_the_registration():
    names = {c.name for c in CONDITIONS}
    assert names == {"base-1.0", "base-0.7", "instruct-1.0", "instruct-0.7"}
    settings = {(c.temperature, c.top_p) for c in CONDITIONS}
    assert settings == {(1.0, 1.0), (0.7, 0.9)}
    assert CONFIRMATORY == "base-1.0"
    assert WORD_TARGET == 2_000_000
    assert MAX_NEW_TOKENS == 1024
    assert {c.model for c in CONDITIONS} == {
        "allenai/Olmo-3-1025-7B", "allenai/Olmo-3-7B-Instruct"}
    assert [c.instruct for c in CONDITIONS if c.model.endswith("Instruct")] \
        == [True, True]


def test_prompt_names_no_variety_or_style():
    prompt = build_prompt("Bike Insurance - Better Safe Than Sorry")
    assert prompt == "Write a blog post titled: Bike Insurance - Better Safe Than Sorry"
    for word in ("British", "American", "punchy", "style", "register",
                 "engaging"):
        assert word.lower() not in prompt.lower().replace(
            "bike insurance - better safe than sorry", "")


def test_seeds_are_deterministic_and_distinct():
    assert seed_for("base-1.0", "T0001", 1) == seed_for("base-1.0", "T0001", 1)
    distinct = {
        seed_for(condition, topic, pass_number)
        for condition in ("base-1.0", "instruct-0.7")
        for topic in ("T0001", "T0002", "T0003")
        for pass_number in (1, 2)
    }
    assert len(distinct) == 12
    assert all(0 <= seed < 2**31 - 1 for seed in distinct)


def test_topics_file_matches_the_protocol():
    topics = load_topics(REPO / "data" / "topics.csv")
    assert len(topics) == 4000
    assert len({t["topic_id"] for t in topics}) == 4000
    by_variety = {}
    for topic in topics:
        by_variety[topic["variety_source"]] = \
            by_variety.get(topic["variety_source"], 0) + 1
    assert by_variety == {"US": 800, "GB": 800, "IE": 800, "AU": 800, "ZA": 800}
    assert all(topic["topic"].strip() for topic in topics)


def test_words_so_far_counts_the_way_study_2_counts():
    records = [
        Generation("base-1.0", "T0001", 1, 1, "p", "Here's the thing.", "stop",
                   "m", "r", 1.0, 1.0, 1024),
        Generation("base-1.0", "T0002", 1, 2, "p", "", "stop", "m", "r",
                   1.0, 1.0, 1024),
    ]
    # "here 's the thing ." is four words and one punctuation token; an empty
    # generation contributes nothing.
    assert words_so_far(records, word_count, tokenise) == 4
    assert len(tokenise("Here's the thing.")) == 5


@pytest.mark.parametrize("condition", [c.name for c in CONDITIONS])
def test_every_condition_has_a_distinct_seed_stream(condition):
    seeds = {seed_for(condition, f"T{i:04d}", 1) for i in range(1, 51)}
    assert len(seeds) == 50
