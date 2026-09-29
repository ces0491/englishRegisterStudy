#!/usr/bin/env python
"""Count the frozen frames in Study 2's generated text.

`python/generate.py` writes one JSONL file per condition, each line a
generation with its text and metadata. This counts them with the frozen
counting layer and writes the tidy table the R analysis reads, the run's
totals, and each generation's own counts for the exploratory analysis.

Text is counted as it came: no deduplication, no dropping refusals or
truncated endings, no stripping of markdown. That is the rule registered at
https://osf.io/qjgtc, and any exclusion would be a judgement about what counts
as the model's register.

Usage:
  python python/count_generated.py data/generated
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import framecount

REPO = Path(__file__).resolve().parent.parent


def count_file(path: Path, frames: dict[str, list[str]]) -> dict:
    """Totals for one condition's JSONL, plus what the run did.

    `texts` holds each generation's own counts, for the registered exploratory
    analysis of generation length against frame rate, which needs them and
    cannot be recovered from the totals.
    """
    totals = {frame_id: 0 for frame_id in frames}
    totals["words"] = 0
    generations = 0
    empty = 0
    passes = 0
    texts = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            text = record.get("text") or ""
            counts = framecount.count_frames(text, frames)
            for key, value in counts.items():
                totals[key] += value
            generations += 1
            empty += not text.strip()
            passes = max(passes, record.get("pass_number", 1))
            texts.append({
                "source": path.stem,
                "topic_id": record.get("topic_id", ""),
                "pass_number": record.get("pass_number", 1),
                "finish_reason": record.get("finish_reason", ""),
                "words": counts["words"],
                **{frame_id: counts[frame_id] for frame_id in frames},
            })
    totals["generations"] = generations
    totals["empty_generations"] = empty
    totals["passes"] = passes
    totals["texts"] = texts
    return totals


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("give the directory holding the condition JSONL files")
    source_dir = Path(sys.argv[1])
    paths = sorted(source_dir.glob("*.jsonl"))
    if not paths:
        raise SystemExit(f"no .jsonl files in {source_dir}")

    frames = framecount.load_frames(REPO / "data" / "frames.csv")
    per_source: dict[str, dict] = {}
    for path in paths:
        per_source[path.stem] = count_file(path, frames)

    rows = []
    for source, totals in sorted(per_source.items()):
        for frame_id in frames:
            rows.append({
                "source": source,
                "frame_id": frame_id,
                "hits": totals[frame_id],
                "words": totals["words"],
            })

    out = REPO / "data" / "counts-generated.csv"
    with open(out, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["source", "frame_id", "hits", "words"])
        writer.writeheader()
        writer.writerows(rows)

    summary = REPO / "data" / "generated-run.csv"
    with open(summary, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["source", "generations", "empty_generations",
                                "passes", "words"])
        writer.writeheader()
        for source, totals in sorted(per_source.items()):
            writer.writerow({
                "source": source,
                "generations": totals["generations"],
                "empty_generations": totals["empty_generations"],
                "passes": totals["passes"],
                "words": totals["words"],
            })

    by_text = REPO / "data" / "counts-generated-by-text.csv"
    with open(by_text, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["source", "topic_id", "pass_number",
                                "finish_reason", "words", *frames])
        writer.writeheader()
        for source in sorted(per_source):
            writer.writerows(per_source[source]["texts"])

    for source, totals in sorted(per_source.items()):
        print(f"{source}: {totals['words']:,} words, "
              f"{totals['generations']:,} generations, "
              f"{totals['empty_generations']} empty, "
              f"{totals['passes']} pass(es)")
    print(f"wrote {out}, {summary} and {by_text}")


def dolma_topic_rows(result: dict) -> list[dict]:
    """One subset's drawn words and hits by topic, beside the topic's size.

    Deviation S3-D2 in docs/deviations.md reports olmOCR's drawn words by topic
    against each topic's share of the subset's compressed bytes, and reweights
    the per-topic rates to those shares. Every topic gets a row per frame
    whether or not a file was drawn from it, so the table shows what the draw
    missed as well as what it took.
    """
    frame_ids = sorted(key for key in result["totals"] if key.startswith("F"))
    topic_of = {directory: entry["topic"]
                for directory, entry in result["directories"].items()}
    topics: dict[str, dict] = {}
    for directory, entry in result["directories"].items():
        topic = topics.setdefault(entry["topic"], {
            "files_available": 0, "bytes": 0, "files_drawn": 0, "words": 0,
            "redacted": 0, "hits": dict.fromkeys(frame_ids, 0)})
        topic["files_available"] += entry["files"]
        topic["bytes"] += entry["bytes"]
    for record in result["per_file"]:
        topic = topics[topic_of[record["path"].split("/")[1]]]
        topic["files_drawn"] += 1
        topic["words"] += record["words"]
        topic["redacted"] += record["redacted"]
        for frame_id in frame_ids:
            topic["hits"][frame_id] += record["hits"][frame_id]
    return [
        {"source": result["subset"], "topic": name, "frame_id": frame_id,
         "hits": topic["hits"][frame_id], "words": topic["words"],
         "files_drawn": topic["files_drawn"],
         "files_available": topic["files_available"], "bytes": topic["bytes"],
         "redacted": topic["redacted"]}
        for name, topic in sorted(topics.items())
        for frame_id in frame_ids
    ]


def dolma_to_csv(dolma_dir: Path) -> list[Path]:
    """Turn count_dolma.py's per-subset JSON into the same tidy shape, and the
    same counts by topic."""
    rows = []
    topic_rows = []
    for path in sorted(dolma_dir.glob("*.json")):
        result = json.load(open(path, encoding="utf-8"))
        topic_rows.extend(dolma_topic_rows(result))
        totals = result["totals"]
        for key, value in totals.items():
            if key.startswith("F"):
                rows.append({
                    "source": result["subset"],
                    "frame_id": key,
                    "hits": value,
                    "words": totals["words"],
                })
    out = REPO / "data" / "counts-dolma.csv"
    with open(out, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["source", "frame_id", "hits", "words"])
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (r["source"], r["frame_id"])))
    topic_out = REPO / "data" / "counts-dolma-topic.csv"
    with open(topic_out, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(topic_rows[0]))
        writer.writeheader()
        writer.writerows(topic_rows)
    return [out, topic_out]


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--dolma":
        for written in dolma_to_csv(Path(sys.argv[2])):
            print(f"wrote {written}")
    else:
        main()
