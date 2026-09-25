#!/usr/bin/env python
"""Count the frozen frames in Study 2's generated text.

`python/generate.py` writes one JSONL file per condition, each line a
generation with its text and metadata. This counts them with the frozen
counting layer and writes the tidy table the R analysis reads.

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
from collections import defaultdict
from pathlib import Path

import framecount

REPO = Path(__file__).resolve().parent.parent


def count_file(path: Path, frames: dict[str, list[str]]) -> dict:
    """Totals for one condition's JSONL, plus what the run did."""
    totals = {frame_id: 0 for frame_id in frames}
    totals["words"] = 0
    generations = 0
    empty = 0
    passes = 0
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
    totals["generations"] = generations
    totals["empty_generations"] = empty
    totals["passes"] = passes
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

    for source, totals in sorted(per_source.items()):
        print(f"{source}: {totals['words']:,} words, "
              f"{totals['generations']:,} generations, "
              f"{totals['empty_generations']} empty, "
              f"{totals['passes']} pass(es)")
    print(f"wrote {out} and {summary}")


def dolma_to_csv(dolma_dir: Path) -> Path:
    """Turn count_dolma.py's per-subset JSON into the same tidy shape."""
    rows = []
    for path in sorted(dolma_dir.glob("*.json")):
        result = json.load(open(path, encoding="utf-8"))
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
    return out


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--dolma":
        print(f"wrote {dolma_to_csv(Path(sys.argv[2]))}")
    else:
        main()
