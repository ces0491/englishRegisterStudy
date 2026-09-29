"""Checks on Study 4's counting of the midtraining, SFT and DPO data.

The draw must follow the registered protocol: its sources, their word
allocations, the size-weighted file order, the 250,000-word cap on whole
documents, and the stop at each source's allocation.
"""

import gzip
import io
import json
import re
from pathlib import Path

import pytest

import count_study4 as c4
import framecount

REPO = Path(__file__).resolve().parent.parent
FRAMES = framecount.load_frames(REPO / "data" / "frames.csv")
PROTOCOL = (REPO / "docs" / "study4-protocol.md").read_text(encoding="utf-8")


def protocol_sources():
    rows = re.findall(r"^\| (\d+) \| ([^|]+) \| `([^`]+)` \| ([^|]+) \| ([\d.]+) \| [\d.]+ \| ([\d,]+) \|$",
                      PROTOCOL, flags=re.M)
    return [(int(k), name.strip(), pattern, category.strip(), float(tokens),
             int(words.replace(",", ""))) for k, name, pattern, category, tokens, words in rows]


def test_sources_and_allocations_are_the_protocols():
    rows = protocol_sources()
    assert len(rows) == 24
    allocation = c4.allocations()
    for (k, name, pattern, category, tokens, words), source in zip(rows, c4.SOURCES):
        assert (name, category, tokens) == (source.name, source.category, source.tokens_billion)
        assert c4.source_named(name)[0] == k
        assert allocation[name] == words
        # The one pattern that differs is the correction S4-D1 records.
        if name == "StackEdu (FIM)":
            assert (pattern, source.pattern) == ("stack_edu-fim-*", "stack_edu-fim_*")
        else:
            assert pattern == source.pattern


def test_every_directory_is_claimed_by_exactly_one_source():
    directories = [
        "tinymath-mind", "tinymath-pot", "cranemath", "megamatt", "dolmino-math",
        "stack_edu-fim_vigintile_15_C", "stack_edu-fim_vigintile_19_TypeScript",
        "cranecode", "reddit_to_flashcards", "wiki_to_rcqa-part1", "wiki_to_rcqa-part3",
        "nemotron-synth-qa", "math-meta-reasoning", "code-meta-reasoning",
        "program_verifiable", "omr-rewrite-fullthoughts", "qwq-reasoning-traces",
        "general_reasoning_mix", "gemini-reasoning-traces",
        "llama_nemotron-reasoning-traces", "openthoughts2-reasoning-traces",
        "tulu-3-sft", "dolmino_1-flan",
        "olmocr_science_pdfs-high_quality-art_and_design-2e12",
        "stem-heavy-crawl", "common_crawl-high-quality_19_adult_content",
        "common_crawl-high-quality_20_travel_and_tourism",
    ]
    sizes = {f"data/{d}/file-0001.jsonl.zst": 10 for d in directories}
    claims = {path: [s.name for s in c4.SOURCES if path in c4.source_files(sizes, s)]
              for path in sizes}
    assert all(len(owners) == 1 for owners in claims.values()), claims
    assert claims["data/stack_edu-fim_vigintile_15_C/file-0001.jsonl.zst"] == ["StackEdu (FIM)"]


def test_draw_order_is_the_registered_key():
    import numpy as np

    paths = [f"data/x/{i:03d}.jsonl.zst" for i in range(50)]
    sizes = {p: (i + 1) * 1000 for i, p in enumerate(paths)}
    order = c4.draw_order(paths, sizes, k=7)
    rng = np.random.default_rng([c4.SEED, 7])
    u = rng.random(len(paths))
    keys = {p: u[i] ** (1.0 / sizes[p]) for i, p in enumerate(paths)}
    assert order == sorted(paths, key=lambda p: -keys[p])
    assert order == c4.draw_order(paths, sizes, k=7)
    assert order != c4.draw_order(paths, sizes, k=8)
    with pytest.raises(ValueError):
        c4.draw_order(list(reversed(paths)), sizes, k=7)


def test_draw_order_favours_large_files():
    paths = [f"data/x/{i:03d}.jsonl.zst" for i in range(200)]
    sizes = {p: 1_000_000 if i % 2 else 1_000 for i, p in enumerate(paths)}
    first_half = c4.draw_order(paths, sizes, k=3)[:100]
    assert sum(sizes[p] == 1_000_000 for p in first_half) > 90


def doc(words, extra=""):
    return {"text": " ".join(["w"] * words) + extra}


def test_file_cap_takes_whole_documents_up_to_the_cap():
    docs = [doc(100_000), doc(100_000, " here's the thing"), doc(100_000)]
    record = c4.read_file("S", "p", 1, iter(docs), FRAMES, 0, 10**9)
    assert (record.documents, record.words, record.stopped) == (2, 200_004, "cap")
    assert record.hits["F01"] == 1


def test_redacted_documents_are_counted_as_published_and_tallied():
    docs = [{"text": "[REMOVED]"}, doc(10)]
    record = c4.read_file("S", "p", 1, iter(docs), FRAMES, 0, 10**9)
    assert (record.documents, record.redacted, record.words) == (2, 1, 11)


def test_a_first_document_over_the_cap_is_not_taken():
    record = c4.read_file("S", "p", 1, iter([doc(300_000)]), FRAMES, 0, 10**9)
    assert (record.documents, record.words, record.stopped) == (0, 0, "cap")


def test_reading_stops_after_the_document_that_reaches_the_allocation():
    docs = [doc(60_000), doc(60_000), doc(60_000)]
    record = c4.read_file("S", "p", 1, iter(docs), FRAMES, 30_000, 120_000)
    assert (record.documents, record.words, record.stopped) == (2, 120_000, "allocation")
    record = c4.read_file("S", "p", 1, iter(docs[:1]), FRAMES, 0, 10**9)
    assert record.stopped == "end"


def test_a_document_without_text_is_an_error():
    with pytest.raises(RuntimeError, match="no text field"):
        c4.read_file("S", "p", 1, iter([{"body": "x"}]), FRAMES, 0, 10)


def test_count_source_reads_in_draw_order_until_the_allocation(monkeypatch):
    source = c4.Source("Test", "test", "Test", 1.0)
    paths = [f"data/test/{i}.jsonl.zst" for i in range(6)]
    sizes = {p: 100 * (i + 1) for i, p in enumerate(paths)}
    contents = {p: [doc(40_000)] * 10 for p in paths}

    class Handle:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            return self.path

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(c4, "documents", lambda handle, path: iter(contents[path]))
    counts = c4.count_source(source, 1, sizes, Handle, FRAMES, allocation=600_000)
    assert [c.path for c in counts] == c4.draw_order(paths, sizes, 1)[:3]
    assert [c.words for c in counts] == [240_000, 240_000, 120_000]
    assert [c.stopped for c in counts] == ["cap", "cap", "allocation"]


def test_a_failed_read_is_retried_and_counts_the_same(monkeypatch):
    source = c4.Source("Test", "test", "Test", 1.0)
    paths = [f"data/test/{i}.jsonl.zst" for i in range(3)]
    sizes = {p: 100 * (i + 1) for i, p in enumerate(paths)}
    monkeypatch.setattr(c4, "documents", lambda handle, path: iter([doc(40_000)] * 3))
    failures = {"left": 2}

    class Flaky:
        def __init__(self, path):
            pass

        def __enter__(self):
            if failures["left"]:
                failures["left"] -= 1
                raise ConnectionError("reset")
            return None

        def __exit__(self, *exc):
            return False

    class Steady(Flaky):
        def __enter__(self):
            return None

    pauses = []
    flaky = c4.count_source(source, 1, sizes, Flaky, FRAMES, 200_000, wait=pauses.append)
    steady = c4.count_source(source, 1, sizes, Steady, FRAMES, 200_000)
    assert [vars(r) for r in flaky] == [vars(r) for r in steady]
    assert pauses == [2, 4]


def test_a_missing_text_field_is_not_retried(monkeypatch):
    source = c4.Source("Test", "test", "Test", 1.0)
    sizes = {"data/test/0.jsonl.zst": 1}
    monkeypatch.setattr(c4, "documents", lambda handle, path: iter([{"body": "x"}]))

    class Handle:
        def __init__(self, path):
            pass

        def __enter__(self):
            return None

        def __exit__(self, *exc):
            return False

    pauses = []
    with pytest.raises(RuntimeError, match="no text field"):
        c4.count_source(source, 1, sizes, Handle, FRAMES, 100, wait=pauses.append)
    assert pauses == []


def test_count_source_refuses_to_fall_short(monkeypatch):
    source = c4.Source("Test", "test", "Test", 1.0)
    sizes = {"data/test/0.jsonl.zst": 1}
    monkeypatch.setattr(c4, "documents", lambda handle, path: iter([doc(10)]))

    class Handle:
        def __init__(self, path):
            pass

        def __enter__(self):
            return None

        def __exit__(self, *exc):
            return False

    with pytest.raises(RuntimeError, match="ran out of files"):
        c4.count_source(source, 1, sizes, Handle, FRAMES, allocation=100)


def test_zstd_documents_read_across_frames():
    zstandard = pytest.importorskip("zstandard")
    compressor = zstandard.ZstdCompressor()
    lines = [json.dumps({"text": f"doc {i}"}) + "\n" for i in range(4)]
    data = compressor.compress("".join(lines[:2]).encode()) + \
        compressor.compress("".join(lines[2:]).encode())
    docs = list(c4.documents(io.BytesIO(data), "x.jsonl.zst"))
    assert [d["text"] for d in docs] == ["doc 0", "doc 1", "doc 2", "doc 3"]


def test_assistant_turns_and_last_assistant():
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"},
                {"role": "assistant", "content": "first"}, {"role": "user", "content": "u2"},
                {"role": "assistant", "content": "second"}, {"role": "assistant", "content": None}]
    assert c4.assistant_text(messages) == "first\nsecond"
    assert c4.last_assistant(messages) == ""
    assert c4.last_assistant(messages[:5]) == "second"
    assert c4.last_assistant([{"role": "user", "content": "u"}]) == ""
    assert c4.assistant_text(None) == ""


def test_sft_and_dpo_totals_equal_their_units():
    sft_rows = [{"messages": [{"role": "assistant", "content": "It isn't just a test."}],
                 "source_dataset": "a"},
                {"messages": [{"role": "user", "content": "It isn't just a prompt."}],
                 "source_dataset": "b"}]
    units, totals = c4.count_sft_rows(sft_rows, FRAMES, "shard")
    assert [u["F09"] for u in units] == [1, 0]
    assert totals["F09"] == 1 and totals["words"] == sum(u["words"] for u in units)

    dpo_rows = [{"chosen": [{"role": "user", "content": "q"},
                            {"role": "assistant", "content": "It is not just x but y."}],
                 "rejected": [{"role": "user", "content": "q"},
                              {"role": "assistant", "content": "No."}],
                 "chosen_model": "m1", "rejected_model": "m2"}]
    units, totals = c4.count_dpo_rows(dpo_rows, FRAMES, "shard")
    assert units[0]["F08_chosen"] == 1 and units[0]["F08_rejected"] == 0
    assert totals["chosen"]["F08"] == 1 and totals["rejected"]["words"] == 1


def test_collect_writes_the_analysis_tables(tmp_path):
    study4 = tmp_path / "study4"
    (study4 / "generated").mkdir(parents=True)
    for arm in ("B1", "P3"):
        record = dict(condition=arm, topic_id="T0001", pass_number=1, seed=1, prompt="p",
                      text="Here's the thing: it isn't just a test.", finish_reason="stop",
                      model="m", revision="r", temperature=1.0, top_p=1.0, max_new_tokens=1024)
        (study4 / "generated" / f"{arm}.jsonl").write_text(json.dumps(record) + "\n",
                                                            encoding="utf-8")
    (study4 / "midtraining").mkdir()
    hits = {f: 0 for f in c4.FRAME_IDS}
    (study4 / "midtraining" / "01-x.json").write_text(json.dumps({
        "source": "TinyMATH Mind", "category": "Math (synth)",
        "per_file": [{"path": "p", "documents": 2, "redacted": 0, "stopped": "end", "words": 10,
                      "hits": {**hits, "F09": 1}}]}), encoding="utf-8")
    (study4 / "sft").mkdir()
    units, totals = c4.count_sft_rows(
        [{"messages": [{"role": "assistant", "content": "It isn't just one."}],
          "source_dataset": "a"}], FRAMES, "s0")
    c4.write_csv_gz(study4 / "sft" / "s0.units.csv.gz", units)
    (study4 / "sft" / "s0.totals.json").write_text(json.dumps(totals), encoding="utf-8")

    written = {p.name for p in c4.collect(study4, REPO)}
    assert {"counts.csv", "units-generated.csv", "units-stage1.csv",
            "units-midtraining.csv", "units-sft.csv.gz"} <= written
    counts = (study4 / "counts.csv").read_text(encoding="utf-8").splitlines()
    sources = {line.split(",")[0] for line in counts[1:]}
    assert sources == {"B1", "P3", "stage1", "midtraining", "sft"}
    assert len(counts) - 1 == 5 * 15
    with gzip.open(study4 / "units-sft.csv.gz", "rt", encoding="utf-8") as handle:
        assert handle.read().splitlines()[1].startswith("s0:0,a,")


def test_collect_refuses_to_replace_a_table_from_a_partial_run(tmp_path):
    """The per-part counts are gitignored and counts.csv is committed, so a
    clean clone running --collect finds only stage1 and would otherwise
    rewrite the committed table with what it found."""
    study4 = tmp_path / "study4"
    study4.mkdir(parents=True)
    committed = "source,frame_id,hits,words\nsft,F01,1,10\n"
    (study4 / "counts.csv").write_text(committed, encoding="utf-8")

    with pytest.raises(SystemExit) as raised:
        c4.collect(study4, REPO)

    assert "generated" in str(raised.value)
    assert (study4 / "counts.csv").read_text(encoding="utf-8") == committed
