"""Study 3's counting pass over Dolma 3, on Modal.

The sampling frame is registered at https://osf.io/ngt3m and written out in
docs/dolma-sampling-frame.md. This implements it and nothing else: list a
subset's parquet files, draw them with the registered seed, read each drawn
file from its first row until its word quota, and count the frozen frames with
the same module that counts Study 2's generated text.

Per-file records — path, rows read, words, hits — are kept so the draw can be
checked rather than taken on trust.

Usage:
  modal run python/count_dolma.py --list-only       # inspect the layout first
  modal run python/count_dolma.py --subset common_crawl
  modal run python/count_dolma.py                   # every subset
  modal volume get englishregisterstudy /dolma ./data/dolma

The pure functions carry no Modal dependency, so python/test_count_dolma.py can
check the draw without touching the corpus.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

REPO_ID = "allenai/dolma3_mix-6T-1025"
SEED = 20260925

# Published token shares, used only for the secondary whole-mix figure. The
# shares are in tokens and the rates are per word, so that figure is an
# approximation and the write-up says so.
SUBSETS = {
    "common_crawl": 0.7607,
    "olmocr_science_pdfs": 0.1357,
    "stack_edu": 0.0689,
    "finemath-3plus": 0.0256,
    "rpj-proofpile-arxiv": 0.0086,
    "dolma1_7-wiki-en": 0.0004,
}

PRIMARY = "common_crawl"
WORDS_PER_FILE = 1_000_000
FILES_PRIMARY = 200
FILES_OTHER = 20

# Column names a corpus of this kind uses for the document body. The remote
# function fails loudly with the real schema if none of them is present rather
# than guessing at a column.
TEXT_COLUMNS = ("text", "content", "raw_content", "document")


def files_drawn(subset: str) -> int:
    return FILES_PRIMARY if subset == PRIMARY else FILES_OTHER


def words_wanted(subset: str) -> int:
    return files_drawn(subset) * WORDS_PER_FILE


def subset_files(all_paths, subset: str) -> list[str]:
    """The subset's parquet files, sorted.

    A path belongs to a subset when one of its directory components is the
    subset's name. Matching on a component rather than a substring keeps
    `stack_edu` from catching a file whose name merely mentions it.
    """
    matched = [
        path for path in all_paths
        if path.endswith(".parquet") and subset in Path(path).parts[:-1]
    ]
    return sorted(matched)


def draw(paths: list[str], subset: str, seed: int = SEED) -> list[str]:
    """The registered draw: seeded, without replacement, one stream per subset.

    The whole shuffled order is returned rather than the first n, so that a
    file shorter than its quota can be made up by the next one along without
    leaving the registered order.
    """
    if not paths:
        raise ValueError(f"no parquet files found for subset {subset!r}")
    rng = random.Random(f"{seed}:{subset}")
    shuffled = list(paths)
    rng.shuffle(shuffled)
    return shuffled


@dataclass
class FileCount:
    path: str
    rows: int
    words: int
    hits: dict[str, int] = field(default_factory=dict)


def totals(counts: list[FileCount]) -> dict[str, int]:
    out: dict[str, int] = {"words": 0, "rows": 0, "files": len(counts)}
    for count in counts:
        out["words"] += count.words
        out["rows"] += count.rows
        for frame_id, hits in count.hits.items():
            out[frame_id] = out.get(frame_id, 0) + hits
    return out


def enough(counts: list[FileCount], subset: str) -> bool:
    return sum(count.words for count in counts) >= words_wanted(subset)


# --- Modal ------------------------------------------------------------------

try:
    import modal
except ImportError:  # pragma: no cover - local testing without Modal
    modal = None

if modal is not None:
    REPO = Path(__file__).resolve().parent.parent

    image = (
        modal.Image.debian_slim(python_version="3.11")
        .pip_install("huggingface_hub", "pyarrow", "fsspec")
        .add_local_file(REPO / "python" / "framecount.py", "/root/framecount.py")
        .add_local_file(REPO / "data" / "frames.csv", "/root/frames.csv")
    )

    app = modal.App("englishregisterstudy-dolma", image=image)
    volume = modal.Volume.from_name("englishregisterstudy", create_if_missing=True)
    OUT = Path("/data/dolma")

    @app.function(timeout=60 * 15)
    def list_layout() -> dict:
        """What the repository actually looks like, before anything is drawn.

        Listing file names is not drawing documents, so this can be run before
        the counting pass to confirm the paths the sampling frame assumes.
        """
        from huggingface_hub import HfApi

        paths = HfApi().list_repo_files(REPO_ID, repo_type="dataset")
        parquet = [p for p in paths if p.endswith(".parquet")]
        found = {subset: len(subset_files(parquet, subset)) for subset in SUBSETS}
        return {
            "files": len(paths),
            "parquet": len(parquet),
            "files_per_subset": found,
            "sample_paths": parquet[:10],
        }

    # Counting runs at about 4.7 seconds per million words on one core, so
    # the 200 million of common_crawl is roughly a quarter of an hour and the
    # five smaller subsets eight minutes between them. Downloading the parquet
    # is the slow part, not the matching, so there is nothing to gain from
    # more cores here.
    @app.function(timeout=60 * 60 * 6, cpu=2, volumes={"/data": volume})
    def count_subset(subset: str) -> dict:
        """Draw one subset's files and count the frames in them."""
        import datetime

        import pyarrow.parquet as pq
        from huggingface_hub import HfApi, HfFileSystem

        import framecount

        frames = framecount.load_frames("/root/frames.csv")
        paths = subset_files(
            HfApi().list_repo_files(REPO_ID, repo_type="dataset"), subset)
        order = draw(paths, subset)
        fs = HfFileSystem()

        counts: list[FileCount] = []
        for path in order:
            if enough(counts, subset):
                break
            record = FileCount(path=path, rows=0, words=0,
                               hits={frame_id: 0 for frame_id in frames})
            with fs.open(f"datasets/{REPO_ID}/{path}", "rb") as handle:
                parquet = pq.ParquetFile(handle)
                column = next((c for c in TEXT_COLUMNS
                               if c in parquet.schema_arrow.names), None)
                if column is None:
                    raise RuntimeError(
                        f"no text column in {path}; schema is "
                        f"{parquet.schema_arrow.names}")
                for batch in parquet.iter_batches(batch_size=512,
                                                  columns=[column]):
                    for text in batch.column(column).to_pylist():
                        if not text:
                            record.rows += 1
                            continue
                        document = framecount.count_frames(text, frames)
                        record.rows += 1
                        record.words += document["words"]
                        for frame_id in frames:
                            record.hits[frame_id] += document[frame_id]
                    if record.words >= WORDS_PER_FILE:
                        break
            counts.append(record)

        summary = totals(counts)
        result = {
            "subset": subset,
            "repo": REPO_ID,
            "seed": SEED,
            "words_wanted": words_wanted(subset),
            "words_per_file": WORDS_PER_FILE,
            "files_available": len(paths),
            "drawn": [c.path for c in counts],
            "totals": summary,
            "per_file": [vars(c) for c in counts],
            "token_share": SUBSETS[subset],
            "counted_at": datetime.datetime.now(datetime.UTC).isoformat(),
        }

        OUT.mkdir(parents=True, exist_ok=True)
        with open(OUT / f"{subset}.json", "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
        volume.commit()
        return {"subset": subset, **summary}

    @app.local_entrypoint()
    def main(subset: str = "", list_only: bool = False) -> None:
        if list_only:
            layout = list_layout.remote()
            print(json.dumps(layout, indent=2))
            return
        names = [subset] if subset else list(SUBSETS)
        for name in names:
            summary = count_subset.remote(name)
            print(f"{name}: {summary['words']:,} words over "
                  f"{summary['files']} files")
