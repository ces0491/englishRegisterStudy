"""Study 4's counts of the training data behind Olmo 3's later stages.

Registered at https://osf.io/d79u4 and specified in docs/study4-protocol.md.
This counts the midtraining mix, the SFT conversations and the DPO pairs, and
assembles those counts, the generated text's and Study 3's stage-1 counts
into the tables R/analyse-study4.R reads. The stage-1 data is not recounted.

Every text is counted with python/framecount.py, as in Studies 2 and 3. A
`--check` run reads each source's format and counts words only, never frames,
as Study 3 did before its draw (deviation S3-D1).

Usage:
  modal run python/count_study4.py --check
  modal run --detach python/count_study4.py
  modal run python/count_study4.py --part midtraining --source "Tulu 3 SFT"
  modal volume get --force englishregisterstudy /study4/ ./data/
  python python/count_study4.py --collect data/study4
"""

from __future__ import annotations

import csv
import fnmatch
import gzip
import io
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

SEED = 20260929
WORDS_TOTAL = 240_000_000
WORDS_PER_FILE = 250_000
# Ai2 redacted some olmOCR documents after training; counted as published,
# and tallied, as in Study 3 (deviation S3-D2).
REDACTED = "[REMOVED]"

MIDTRAINING = ("allenai/dolma3_dolmino_mix-100B-1025",
               "f23942ae8a8114af6e992efe8188ce8c531acd16")
SFT = ("allenai/dolci-instruct-sft", "bd3c8f3a9b2cc5a9682e44b96ddd0bb2ff027221")
DPO = ("allenai/dolci-3-instruct-dpo-with-metadata",
       "aed155cf32e809b590490b6c3577ee4b0d0a5019")

FRAME_IDS = tuple(f"F{i:02d}" for i in range(1, 16))
# Kept per SFT conversation and per DPO pair: the family and the partial F10
# its sensitivity run adds. The composite needs only per-frame totals.
UNIT_FRAMES = ("F06", "F07", "F08", "F09", "F10")


@dataclass(frozen=True)
class Source:
    name: str
    pattern: str
    category: str
    tokens_billion: float


# The midtraining mix's 24 sources, in the protocol's order; a source's number
# k is its position here, from 1. Patterns match the directory under data/.
SOURCES = (
    Source("TinyMATH Mind", "tinymath-mind", "Math (synth)", 0.898),
    Source("TinyMATH PoT", "tinymath-pot", "Math (synth)", 0.241),
    Source("CraneMath", "cranemath", "Math (synth)", 5.620),
    Source("MegaMatt", "megamatt", "Math (synth)", 1.730),
    Source("Dolmino Math", "dolmino-math", "Math (synth)", 10.700),
    # The protocol's table reads `stack_edu-fim-*`, which matches no
    # directory; the source's directories are `stack_edu-fim_vigintile_*`.
    # Deviation S4-D1 in docs/deviations.md.
    Source("StackEdu (FIM)", "stack_edu-fim_*", "Code", 10.000),
    Source("CraneCode", "cranecode", "Python (synth)", 10.000),
    Source("Reddit To Flashcards", "reddit_to_flashcards", "QA (synth)", 5.900),
    Source("Wiki To RCQA", "wiki_to_rcqa-part*", "QA (synth)", 3.000),
    Source("Nemotron Synth QA", "nemotron-synth-qa", "QA (synth)", 5.000),
    Source("Math Meta-Reasoning", "math-meta-reasoning", "Thinking (synth)", 0.381),
    Source("Code Meta-Reasoning", "code-meta-reasoning", "Thinking (synth)", 0.459),
    Source("Program-Verifiable", "program_verifiable", "Thinking (synth)", 0.159),
    Source("OMR Rewrite FullThoughts", "omr-rewrite-fullthoughts",
           "Thinking (synth)", 0.850),
    Source("QWQ Reasoning Traces", "qwq-reasoning-traces", "Thinking (synth)", 1.870),
    Source("General Reasoning Mix", "general_reasoning_mix", "Thinking (synth)", 1.870),
    Source("Gemini Reasoning Traces", "gemini-reasoning-traces",
           "Thinking (synth)", 0.246),
    Source("Llama Nemotron Reasoning Traces", "llama_nemotron-reasoning-traces",
           "Thinking (synth)", 1.250),
    Source("OpenThoughts2 Reasoning Traces", "openthoughts2-reasoning-traces",
           "Thinking (synth)", 1.250),
    Source("Tulu 3 SFT", "tulu-3-sft", "Instruction (synth)", 1.100),
    Source("Dolmino 1 Flan", "dolmino_1-flan", "Instruction (synth)", 5.000),
    Source("OLMOCR Science PDFs (High Q.)", "olmocr*", "PDFs", 4.990),
    Source("STEM-Heavy Crawl", "stem-heavy-crawl", "Web pages", 4.990),
    Source("Common Crawl (High Q.)", "common_crawl-high-quality_*", "Web pages", 22.400),
)


def source_named(name: str) -> tuple[int, Source]:
    for k, source in enumerate(SOURCES, start=1):
        if source.name == name:
            return k, source
    raise ValueError(f"no midtraining source {name!r}")


def allocations() -> dict[str, int]:
    """Each source's words, in proportion to its share of the card's tokens."""
    total = sum(s.tokens_billion for s in SOURCES)
    return {s.name: round(WORDS_TOTAL * s.tokens_billion / total) for s in SOURCES}


def source_files(sizes: dict[str, int], source: Source) -> list[str]:
    """The source's data files, sorted by path."""
    return sorted(path for path in sizes
                  if path.startswith("data/") and path.count("/") >= 2
                  and fnmatch.fnmatchcase(path.split("/")[1], source.pattern))


def draw_order(paths: list[str], sizes: dict[str, int], k: int) -> list[str]:
    """Files in descending order of the key u ** (1 / size).

    u is uniform from NumPy's default_rng([SEED, k]), one draw per file in
    path order, so larger files tend to come first: probability proportional
    to compressed size, without replacement.
    """
    import numpy as np

    if paths != sorted(paths):
        raise ValueError("paths must be sorted before the draw")
    rng = np.random.default_rng([SEED, k])
    u = rng.random(len(paths))
    size = np.array([max(sizes[p], 1) for p in paths], dtype=float)
    keys = u ** (1.0 / size)
    return [paths[i] for i in np.argsort(-keys, kind="stable")]


def documents(handle, path: str):
    """The documents in one zstd JSON Lines file, in order, as they stream."""
    if not path.endswith(".jsonl.zst"):
        raise ValueError(f"not a zstd JSON Lines file: {path}")
    import zstandard

    # A file can hold several zstd frames; without read_across_frames the
    # reader stops silently at the end of the first.
    stream = zstandard.ZstdDecompressor().stream_reader(handle, read_across_frames=True)
    for line in io.TextIOWrapper(stream, encoding="utf-8"):
        if line.strip():
            yield json.loads(line)


@dataclass
class FileCount:
    source: str
    path: str
    size: int
    documents: int = 0
    words: int = 0
    hits: dict[str, int] = field(default_factory=dict)
    stopped: str = ""  # cap, allocation or end
    redacted: int = 0


def read_file(source: str, path: str, size: int, docs, frames,
              words_before: int, allocation: int,
              cap: int = WORDS_PER_FILE) -> FileCount:
    """Take whole documents from one file, at most `cap` words of them.

    A document that would take the file past its cap is not taken, and the
    file stops there. Reading also stops after the document that brings the
    source to its allocation.
    """
    import framecount

    record = FileCount(source, path, size, hits={f: 0 for f in frames})
    for document in docs:
        if "text" not in document:
            raise RuntimeError(f"no text field in {path}; fields are {sorted(document)}")
        counts = framecount.count_frames(document["text"] or "", frames)
        if record.words + counts["words"] > cap:
            record.stopped = "cap"
            return record
        record.documents += 1
        record.redacted += (document["text"] or "").strip() == REDACTED
        record.words += counts["words"]
        for frame_id in frames:
            record.hits[frame_id] += counts[frame_id]
        if words_before + record.words >= allocation:
            record.stopped = "allocation"
            return record
    record.stopped = "end"
    return record


def count_source(source: Source, k: int, sizes: dict[str, int], open_file,
                 frames, allocation: int, attempts: int = 5,
                 wait=None) -> list[FileCount]:
    """Read the source's files in draw order until its allocation is reached.

    A read that fails in transit is retried from the file's first document,
    after a growing pause, so a retried file counts exactly as it would have.
    A RuntimeError, which read_file raises for a missing text field, is a
    fault in the data and is not retried.
    """
    import time

    pause = wait or time.sleep
    counts: list[FileCount] = []
    words = 0
    for path in draw_order(source_files(sizes, source), sizes, k):
        if words >= allocation:
            break
        for attempt in range(1, attempts + 1):
            try:
                with open_file(path) as handle:
                    record = read_file(source.name, path, sizes[path],
                                       documents(handle, path), frames, words,
                                       allocation)
                break
            except RuntimeError:
                raise
            except Exception as error:  # noqa: BLE001 - network and stream faults
                if attempt == attempts:
                    raise
                print(f"{source.name}: {path} failed ({error!r}); retry {attempt}",
                      flush=True)
                pause(min(60, 2 ** attempt))
        counts.append(record)
        words += record.words
    if words < allocation:
        raise RuntimeError(f"{source.name} ran out of files at {words:,} of "
                           f"{allocation:,} words")
    return counts


def assistant_text(messages) -> str:
    """An SFT conversation's text: every assistant message, joined by newlines."""
    return "\n".join(m["content"] for m in messages or []
                     if m.get("role") == "assistant" and m.get("content"))


def last_assistant(messages) -> str:
    """A DPO response: the last assistant message in the conversation."""
    for message in reversed(messages or []):
        if message.get("role") == "assistant":
            return message.get("content") or ""
    return ""


def unit_counts(text: str, frames) -> dict[str, int]:
    import framecount

    return framecount.count_frames(text, frames)


def count_sft_rows(rows, frames, shard: str):
    """Per-conversation rows and per-frame totals for one SFT shard."""
    units, totals = [], {"units": 0, "words": 0, **{f: 0 for f in frames}}
    for number, row in enumerate(rows):
        counts = unit_counts(assistant_text(row["messages"]), frames)
        units.append({"unit": f"{shard}:{number}", "source_dataset": row.get("source_dataset", ""),
                      "words": counts["words"], **{f: counts[f] for f in UNIT_FRAMES}})
        totals["units"] += 1
        totals["words"] += counts["words"]
        for frame_id in frames:
            totals[frame_id] += counts[frame_id]
    return units, totals


def count_dpo_rows(rows, frames, shard: str):
    """Per-pair rows and per-frame totals, chosen and rejected, for one shard."""
    units = []
    totals = {side: {"units": 0, "words": 0, **{f: 0 for f in frames}}
              for side in ("chosen", "rejected")}
    for number, row in enumerate(rows):
        unit = {"unit": f"{shard}:{number}", "chosen_model": row.get("chosen_model", ""),
                "rejected_model": row.get("rejected_model", "")}
        for side in ("chosen", "rejected"):
            counts = unit_counts(last_assistant(row[side]), frames)
            unit[f"words_{side}"] = counts["words"]
            for frame_id in UNIT_FRAMES:
                unit[f"{frame_id}_{side}"] = counts[frame_id]
            totals[side]["units"] += 1
            totals[side]["words"] += counts["words"]
            for frame_id in frames:
                totals[side][frame_id] += counts[frame_id]
        units.append(unit)
    return units, totals


def write_csv_gz(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


# --- assembling the tables the analysis reads ---------------------------------

def collect(study4: Path, repo: Path) -> list[Path]:
    """Write data/study4's tidy tables from the downloaded counts.

    counts.csv holds hits and words per source and frame, for the composite.
    The units files hold what the family's ratio estimator needs.
    """
    sys.path.insert(0, str(repo / "python"))
    import count_generated
    import framecount

    frames = framecount.load_frames(repo / "data" / "frames.csv")
    rows, written = [], []

    def add(source: str, totals: dict) -> None:
        for frame_id in FRAME_IDS:
            rows.append({"source": source, "frame_id": frame_id,
                         "hits": totals[frame_id], "words": totals["words"]})

    generated = []
    for path in sorted((study4 / "generated").glob("*.jsonl")):
        totals = count_generated.count_file(path, frames)
        add(path.stem, totals)
        for text in totals["texts"]:
            generated.append({"arm": path.stem, "topic_id": text["topic_id"],
                              "finish_reason": text["finish_reason"],
                              "words": text["words"],
                              **{f: text[f] for f in FRAME_IDS}})

    stage1 = json.loads((repo / "data" / "dolma" / "common_crawl.json").read_text(encoding="utf-8"))
    add("stage1", stage1["totals"])
    stage1_units = [{"path": f["path"], "words": f["words"], **f["hits"]}
                    for f in stage1["per_file"]]

    mid_units, mid_totals = [], {"words": 0, **{f: 0 for f in FRAME_IDS}}
    for path in sorted((study4 / "midtraining").glob("*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        for record in result["per_file"]:
            mid_units.append({"source": result["source"], "category": result["category"],
                              "path": record["path"], "documents": record["documents"],
                              "redacted": record["redacted"],
                              "stopped": record["stopped"], "words": record["words"],
                              **record["hits"]})
            mid_totals["words"] += record["words"]
            for frame_id in FRAME_IDS:
                mid_totals[frame_id] += record["hits"][frame_id]
    if mid_units:
        add("midtraining", mid_totals)

    have = {"generated": bool(generated), "midtraining": bool(mid_units)}
    for part, sides in (("sft", ("sft",)), ("dpo", ("chosen", "rejected"))):
        combined = {side: {"words": 0, **{f: 0 for f in FRAME_IDS}} for side in sides}
        shard_files = sorted((study4 / part).glob("*.totals.json"))
        have[part] = bool(shard_files)
        for path in shard_files:
            totals = json.loads(path.read_text(encoding="utf-8"))
            for side in sides:
                block = totals if part == "sft" else totals[side]
                for key in combined[side]:
                    combined[side][key] += block[key]
        if shard_files:
            for side in sides:
                add("sft" if part == "sft" else f"dpo_{side}", combined[side])

    # counts.csv and the units files are committed, and the per-part counts
    # they are built from are not. A partial run that overwrites them leaves a
    # table that looks complete: on a clean clone the documented command cut
    # counts.csv from 211 rows to 31 and still exited 0. Assembling a fresh
    # set from whatever is present is fine, so this refuses only when it would
    # replace a table that is already there.
    missing = sorted(name for name, present in have.items() if not present)
    if missing and (study4 / "counts.csv").exists():
        raise SystemExit(
            f"no counts found for: {', '.join(missing)}.\n"
            f"Nothing written: {study4 / 'counts.csv'} already exists, and "
            "replacing it with part of a run would leave a table that looks "
            "complete. Download or recount the missing parts first, or check "
            "the path given to --collect.")

    def write(name: str, table: list[dict]) -> None:
        if not table:
            return
        path = study4 / name
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(table[0]))
            writer.writeheader()
            writer.writerows(table)
        written.append(path)

    write("counts.csv", rows)
    write("units-generated.csv", generated)
    write("units-stage1.csv", stage1_units)
    write("units-midtraining.csv", mid_units)

    for part in ("sft", "dpo"):
        shards = sorted((study4 / part).glob("*.units.csv.gz"))
        if not shards:
            continue
        out = study4 / f"units-{part}.csv.gz"
        with gzip.open(out, "wt", encoding="utf-8", newline="") as target:
            for n, shard in enumerate(shards):
                with gzip.open(shard, "rt", encoding="utf-8") as source_handle:
                    header = source_handle.readline()
                    if n == 0:
                        target.write(header)
                    for line in source_handle:
                        target.write(line)
        written.append(out)
    return written


# --- Modal ------------------------------------------------------------------

try:
    import modal
except ImportError:  # pragma: no cover - local use without Modal
    modal = None

if modal is not None:
    REPO = Path(__file__).resolve().parent.parent

    image = (
        modal.Image.debian_slim(python_version="3.11")
        .pip_install("huggingface_hub==2.0.0", "fsspec==2026.9.0",
                     "zstandard==0.25.0", "numpy==2.3.3", "pyarrow==21.0.0")
        .add_local_file(REPO / "python" / "framecount.py", "/root/framecount.py")
        .add_local_file(REPO / "data" / "frames.csv", "/root/frames.csv")
    )
    app = modal.App("englishregisterstudy-study4-count", image=image)
    volume = modal.Volume.from_name("englishregisterstudy", create_if_missing=True)
    OUT = Path("/data/study4")

    def list_midtraining() -> dict[str, int]:
        from huggingface_hub import HfApi
        from huggingface_hub.hf_api import RepoFile

        repo, revision = MIDTRAINING
        tree = HfApi().list_repo_tree(repo, repo_type="dataset", revision=revision,
                                      path_in_repo="data", recursive=True)
        return {item.path: item.size for item in tree if isinstance(item, RepoFile)}

    def parquet_files(repo_revision) -> list[str]:
        from huggingface_hub import HfApi

        repo, revision = repo_revision
        return sorted(f for f in HfApi().list_repo_files(repo, repo_type="dataset",
                                                         revision=revision)
                      if f.endswith(".parquet"))

    def parquet_rows(repo_revision, filename: str, columns, limit: int = 0):
        import pyarrow.parquet as pq
        from huggingface_hub import hf_hub_download

        repo, revision = repo_revision
        local = hf_hub_download(repo, filename, repo_type="dataset", revision=revision)
        seen = 0
        for batch in pq.ParquetFile(local).iter_batches(batch_size=5000, columns=columns):
            for row in batch.to_pylist():
                yield row
                seen += 1
                if limit and seen >= limit:
                    return

    def slug(name: str) -> str:
        return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")

    @app.function(timeout=60 * 15)
    def list_midtraining_remote() -> dict[str, int]:
        return list_midtraining()

    # The mix is listed once and each source is handed its own files, so 24
    # counters do not each page through 71,090 entries.
    @app.function(timeout=60 * 60 * 6, cpu=2, volumes={"/data": volume})
    def count_midtraining_source(name: str, sizes: dict[str, int]) -> dict:
        import datetime

        from huggingface_hub import HfFileSystem

        import framecount

        k, source = source_named(name)
        frames = framecount.load_frames("/root/frames.csv")
        allocation = allocations()[name]
        fs = HfFileSystem()
        repo, revision = MIDTRAINING

        def open_file(path):
            return fs.open(f"datasets/{repo}@{revision}/{path}", "rb",
                           block_size=8 * 2**20)

        import numpy

        counts = count_source(source, k, sizes, open_file, frames, allocation)
        result = {
            "source": name, "k": k, "category": source.category,
            "numpy": numpy.__version__,
            "pattern": source.pattern, "repo": repo, "revision": revision,
            "seed": SEED, "allocation": allocation, "words_per_file": WORDS_PER_FILE,
            "files_available": len(source_files(sizes, source)),
            "words": sum(c.words for c in counts),
            "per_file": [vars(c) for c in counts],
            "counted_at": datetime.datetime.now(datetime.UTC).isoformat(),
        }
        (OUT / "midtraining").mkdir(parents=True, exist_ok=True)
        with open(OUT / "midtraining" / f"{k:02d}-{slug(name)}.json", "w",
                  encoding="utf-8") as handle:
            json.dump(result, handle, indent=1)
        volume.commit()
        return {"source": name, "files": len(counts), "words": result["words"],
                "allocation": allocation}

    @app.function(timeout=60 * 60 * 4, cpu=2, memory=8192, volumes={"/data": volume})
    def count_parquet_shard(part: str, filename: str) -> dict:
        import framecount

        frames = framecount.load_frames("/root/frames.csv")
        shard = Path(filename).stem
        if part == "sft":
            rows = parquet_rows(SFT, filename, ["messages", "source_dataset"])
            units, totals = count_sft_rows(rows, frames, shard)
        else:
            rows = parquet_rows(DPO, filename,
                                ["chosen", "rejected", "chosen_model", "rejected_model"])
            units, totals = count_dpo_rows(rows, frames, shard)
        write_csv_gz(OUT / part / f"{shard}.units.csv.gz", units)
        with open(OUT / part / f"{shard}.totals.json", "w", encoding="utf-8") as handle:
            json.dump({"file": filename, **totals}, handle, indent=1)
        volume.commit()
        return {"part": part, "file": filename, "units": len(units)}

    @app.function(timeout=60 * 60, cpu=2, memory=8192)
    def check_formats() -> dict:
        """Formats and word counts only: no frame is counted.

        Each midtraining source's last file in draw order, the one the draw
        reaches last if at all, gives its first document's fields and the
        words in its first 100 documents; each parquet set's first file gives
        the fields and roles of its first rows.
        """
        from huggingface_hub import HfFileSystem

        import framecount

        def words(text: str) -> int:
            return framecount.word_count(framecount.tokenise(text))

        sizes = list_midtraining()
        fs = HfFileSystem()
        repo, revision = MIDTRAINING
        report = {"midtraining_files": len(sizes), "sources": {}}
        claimed = set()
        for k, source in enumerate(SOURCES, start=1):
            files = source_files(sizes, source)
            claimed.update(files)
            first = draw_order(files, sizes, k)[-1]
            with fs.open(f"datasets/{repo}@{revision}/{first}", "rb") as handle:
                docs = []
                for document in documents(handle, first):
                    docs.append(document)
                    if len(docs) == 100:
                        break
            report["sources"][source.name] = {
                "files": len(files), "file_checked": first,
                "fields": sorted(docs[0]),
                "words_in_first_100_documents": sum(words(d.get("text") or "") for d in docs),
            }
        report["unclaimed_files"] = len(set(sizes) - claimed)

        sft_files, dpo_files = parquet_files(SFT), parquet_files(DPO)
        sft = list(parquet_rows(SFT, sft_files[0], ["messages", "source_dataset"], limit=500))
        dpo = list(parquet_rows(DPO, dpo_files[0],
                                ["chosen", "rejected", "chosen_model", "rejected_model"],
                                limit=500))
        report["sft"] = {
            "files": len(sft_files),
            "roles_first_row": [m.get("role") for m in sft[0]["messages"]],
            "assistant_words_first_500": sum(words(assistant_text(r["messages"])) for r in sft),
            "empty_assistant_first_500": sum(not assistant_text(r["messages"]) for r in sft),
        }
        report["dpo"] = {
            "files": len(dpo_files),
            "roles_first_chosen": [m.get("role") for m in dpo[0]["chosen"]],
            "last_role_is_assistant_first_500": sum(
                (r["chosen"] or [{}])[-1].get("role") == "assistant"
                and (r["rejected"] or [{}])[-1].get("role") == "assistant" for r in dpo),
            "response_words_first_500": sum(
                words(last_assistant(r["chosen"])) + words(last_assistant(r["rejected"]))
                for r in dpo),
        }
        return report

    @app.function(timeout=60 * 10)
    def list_parquet(repo_revision) -> list[str]:
        return parquet_files(tuple(repo_revision))

    @app.local_entrypoint()
    def main(part: str = "", source: str = "", check: bool = False) -> None:
        if check:
            print(json.dumps(check_formats.remote(), indent=2))
            return
        calls = []
        if part in ("", "midtraining"):
            names = [source] if source else [s.name for s in SOURCES]
            sizes = list_midtraining_remote.remote()
            for name in names:
                own = source_files(sizes, source_named(name)[1])
                calls.append(count_midtraining_source.spawn(
                    name, {path: sizes[path] for path in own}))
        for name, repo_revision in (("sft", SFT), ("dpo", DPO)):
            if part in ("", name):
                calls += [count_parquet_shard.spawn(name, f)
                          for f in list_parquet.remote(repo_revision)]
        for call in calls:
            print(json.dumps(call.get()))


if __name__ == "__main__" and "--collect" in sys.argv:
    target = Path(sys.argv[sys.argv.index("--collect") + 1])
    for written in collect(target, Path(__file__).resolve().parent.parent):
        print(f"wrote {written}")
