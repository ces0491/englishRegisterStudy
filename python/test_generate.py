"""Checks on the parts of the generation run that do not need a GPU.

The run itself can only be verified by running it. What can be checked here is
that the protocol registered at https://osf.io/qjgtc is what the code encodes:
the four conditions, the prompt, the seeds, and the word target.
"""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from framecount import word_count, tokenise
from generate import (CONDITIONS, CONFIRMATORY, MAX_NEW_TOKENS, WORD_TARGET,
                      Generation, build_prompt, check_resumable, load_topics,
                      read_records, run_condition, seed_for, seed_name,
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


def test_topics_load_in_topic_id_order(tmp_path):
    path = tmp_path / "topics.csv"
    path.write_text("topic_id,variety_source,site,topic\n"
                    "T0002,GB,b,Second\nT0001,US,a,First\n", encoding="utf-8")
    assert [t["topic_id"] for t in load_topics(path)] == ["T0001", "T0002"]


def test_trial_seeds_are_not_the_study_seeds():
    assert seed_name("base-1.0", 0) == "base-1.0"
    trial = {seed_for(seed_name("base-1.0", 128), f"T{i:04d}", 1)
             for i in range(1, 129)}
    study = {seed_for("base-1.0", f"T{i:04d}", 1) for i in range(1, 129)}
    assert not trial & study


# --- the stopping rule, with a stand-in for the model ----------------------

TOPICS = [{"topic_id": f"T{i:04d}", "topic": f"Topic {i}"} for i in range(1, 11)]


def fake_generator(words_each, calls):
    """Returns `words_each` words per generation and logs every call."""
    def generate(batch, pass_number):
        calls.append(([t["topic_id"] for t in batch], pass_number))
        return [Generation("base-1.0", t["topic_id"], pass_number,
                           seed_for("base-1.0", t["topic_id"], pass_number),
                           "p", " ".join(["word"] * words_each), "length",
                           "m", "r", 1.0, 1.0, 1024) for t in batch]
    return generate


def count(text):
    return word_count(tokenise(text))


def test_first_pass_covers_every_topic_even_past_the_target():
    calls = []
    records = run_condition(TOPICS, fake_generator(100, calls), count,
                            word_target=300, chunk=4)
    assert [r.topic_id for r in records] == [t["topic_id"] for t in TOPICS]
    assert {r.pass_number for r in records} == {1}
    assert [len(ids) for ids, _ in calls] == [4, 4, 2]


def test_reuse_goes_in_topic_id_order_and_stops_after_the_batch_that_reaches_it():
    calls = []
    # The first pass gives 10 x 10 = 100 words; each reuse batch of two adds 20.
    records = run_condition(TOPICS, fake_generator(10, calls), count,
                            word_target=135, reuse_batch=2)
    reused = [(r.topic_id, r.pass_number) for r in records if r.pass_number > 1]
    assert reused == [("T0001", 2), ("T0002", 2), ("T0003", 2), ("T0004", 2)]
    assert sum(count(r.text) for r in records) == 140
    assert len({r.seed for r in records}) == len(records)


def test_a_resumed_run_generates_only_what_is_missing():
    calls = []
    earlier = fake_generator(100, [])(TOPICS[:5], 1)
    records = run_condition(TOPICS, fake_generator(100, calls), count,
                            existing=earlier, word_target=300)
    assert calls == [(["T0006", "T0007", "T0008", "T0009", "T0010"], 1)]
    assert [r.topic_id for r in records] == [t["topic_id"] for t in TOPICS]


def test_a_run_that_never_reaches_the_target_stops_after_the_last_pass():
    calls = []
    records = run_condition(TOPICS, fake_generator(0, calls), count,
                            word_target=1, reuse_batch=5, max_passes=3)
    assert len(records) == 30
    assert {r.pass_number for r in records} == {1, 2, 3}


def test_batches_are_handed_on_as_they_finish():
    batches = []
    run_condition(TOPICS, fake_generator(100, []), count, word_target=300,
                  chunk=6, on_batch=batches.append)
    assert [len(b) for b in batches] == [6, 4]


# --- resuming from the volume -----------------------------------------------

def test_read_records_drops_only_a_cut_off_last_line(tmp_path):
    good = fake_generator(3, [])(TOPICS[:2], 1)
    path = tmp_path / "base-1.0.jsonl"
    lines = [json.dumps(asdict(r)) for r in good]
    path.write_text("\n".join(lines) + '\n{"condition": "base-1', encoding="utf-8")
    assert [r.topic_id for r in read_records(path)] == ["T0001", "T0002"]
    path.write_text(lines[0] + '\n{"broken"\n' + lines[1] + "\n", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        read_records(path)
    assert read_records(tmp_path / "missing.jsonl") == []


def test_resuming_refuses_text_from_another_revision():
    base = next(c for c in CONDITIONS if c.name == "base-1.0")
    made = [Generation("base-1.0", "T0001", 1, 1, "p", "text", "stop",
                       base.model, "abc123", 1.0, 1.0, MAX_NEW_TOKENS)]
    check_resumable(made, base, "abc123")
    with pytest.raises(RuntimeError, match="cannot resume"):
        check_resumable(made, base, "def456")
