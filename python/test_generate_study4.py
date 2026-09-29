"""Checks on Study 4's generation code.

The pure functions python/generate_study4.py repeats from Study 2 must behave
exactly as Study 2's do, and its nine arms must be the checkpoints the
registered protocol pins.
"""

import dataclasses
import json
import re
from pathlib import Path

import pytest

import generate
import generate_study4 as g4

REPO = Path(__file__).resolve().parent.parent


def test_repeated_constants_and_prompt_match_study2():
    assert g4.MAX_NEW_TOKENS == generate.MAX_NEW_TOKENS
    assert g4.MAX_MODEL_LEN == generate.MAX_MODEL_LEN
    assert g4.PROMPT_TEMPLATE == generate.PROMPT_TEMPLATE
    assert g4.CHUNK == generate.CHUNK
    for topic in ("Growing Tomatoes", "", "Ünïcode — dashes"):
        assert g4.build_prompt(topic) == generate.build_prompt(topic)


def test_seed_for_matches_study2():
    for name in ("base-1.0", "study4:B1", "trial:study4:P3"):
        for topic_id in ("T0001", "T2809", "T4000"):
            for pass_number in (1, 2):
                assert g4.seed_for(name, topic_id, pass_number) == \
                    generate.seed_for(name, topic_id, pass_number)


def test_topics_and_generation_records_match_study2(tmp_path):
    topics = REPO / "data" / "topics.csv"
    assert g4.load_topics(topics) == generate.load_topics(topics)
    assert [f.name for f in dataclasses.fields(g4.Generation)] == \
        [f.name for f in dataclasses.fields(generate.Generation)]

    record = dict(condition="B1", topic_id="T0001", pass_number=1, seed=7,
                  prompt="p", text="t", finish_reason="stop", model="m",
                  revision="r", temperature=1.0, top_p=1.0, max_new_tokens=1024)
    path = tmp_path / "B1.jsonl"
    path.write_text(json.dumps(record) + "\n" + '{"cut off', encoding="utf-8")
    ours = [dataclasses.asdict(r) for r in g4.read_records(path)]
    theirs = [dataclasses.asdict(r) for r in generate.read_records(path)]
    assert ours == theirs == [record]


def fake_generate(batch, pass_number):
    return [g4.Generation("X", t["topic_id"], pass_number, 0, "", "one two",
                          "stop", "m", "r", 1.0, 1.0, 1024) for t in batch]


def test_run_arm_is_study2s_first_pass():
    topics = [{"topic_id": f"T{i:04d}", "topic": "x"} for i in range(1, 1204)]
    ours = g4.run_arm(topics, fake_generate)
    theirs = generate.run_condition(topics, fake_generate, lambda t: 2,
                                    max_passes=1)
    assert [(r.topic_id, r.pass_number) for r in ours] == \
        [(r.topic_id, r.pass_number) for r in theirs]
    assert len(ours) == 1203


def test_run_arm_resumes_without_repeating_topics():
    topics = [{"topic_id": f"T{i:04d}", "topic": "x"} for i in range(1, 11)]
    existing = fake_generate(topics[:4], 1)
    batches = []
    records = g4.run_arm(topics, fake_generate, existing, chunk=3,
                         on_batch=batches.append)
    assert [r.topic_id for r in records] == [t["topic_id"] for t in topics]
    assert [len(b) for b in batches] == [3, 3]


def test_arms_are_the_registered_checkpoints():
    protocol = (REPO / "docs" / "study4-protocol.md").read_text(encoding="utf-8")
    pinned = dict(re.findall(r"^\| (B[123]|N[123]|P[123]) \|.*?\| `([0-9a-f]{40})` \|",
                             protocol, flags=re.M))
    assert len(pinned) == 9
    assert {arm.name: arm.revision for arm in g4.ARMS} == pinned
    assert {a.name for a in g4.ARMS if a.patched} == {"N1", "N2", "N3"}
    assert {a.name for a in g4.ARMS if a.chat} == {"P1", "P2", "P3"}


def test_seed_namespaces_are_new():
    assert g4.seed_name("B1", 0) == "study4:B1"
    assert g4.seed_name("B1", 8) == "trial:study4:B1"
    study2 = {generate.seed_for(c.name, "T0001", 1) for c in generate.CONDITIONS}
    study4 = {g4.seed_for(g4.seed_name(a.name, 0), "T0001", 1) for a in g4.ARMS}
    assert not study2 & study4


def test_resume_refuses_text_from_another_revision():
    arm = g4.arm_named("B3")
    stale = g4.Generation("B3", "T0001", 1, 0, "", "", "stop", arm.repo,
                          "0" * 40, 1.0, 1.0, 1024)
    with pytest.raises(RuntimeError, match="cannot resume B3"):
        g4.check_resumable([stale], arm)
