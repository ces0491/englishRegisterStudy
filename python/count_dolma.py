"""Study 3's counting pass over Dolma 3, on Modal.

The sampling frame is registered at https://osf.io/ngt3m and written out in
docs/dolma-sampling-frame.md. This implements it and nothing else: list a
subset's data files, draw them with the registered seed, read each drawn file
from its first document until its word quota, and count the frozen frames with
the same module that counts Study 2's generated text.

The registration describes the corpus as parquet. It is JSON Lines, compressed
with zstd or, for part of olmocr_science_pdfs, gzip; docs/deviations.md
records that and the other differences between the registered description and
the repository as it stands.

Per-file records — path, documents read, words, hits, redacted documents — are
kept so the draw can be checked rather than taken on trust.

Usage:
  modal run python/count_dolma.py --list-only       # inspect the layout first
  modal run python/count_dolma.py --subset common_crawl
  modal run python/count_dolma.py                   # every subset
  modal volume get englishregisterstudy /dolma ./data/dolma

The pure functions carry no Modal dependency, so python/test_count_dolma.py can
check the draw and the reader without touching the corpus.
"""

from __future__ import annotations

import gzip
import io
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

# The registration names allenai/dolma3_mix-6T-1025, which now redirects here.
# The revision is pinned so that the listing the draw is taken from cannot
# change between runs.
REPO_ID = "allenai/dolma3_mix-6T-1025-7B"
REVISION = "2ca900fbe14e86c5c83d064d9f0882f1c0b8c05b"
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

EXTENSIONS = (".jsonl.zst", ".jsonl.gz")

# Ai2 replaced some olmOCR documents with this text after Olmo 3 7B was
# trained. Such a document is counted like any other, as registered, and
# recorded, so the words it adds can be taken back out exactly.
REDACTED = "[REMOVED]"


def files_drawn(subset: str) -> int:
    return FILES_PRIMARY if subset == PRIMARY else FILES_OTHER


def words_wanted(subset: str) -> int:
    return files_drawn(subset) * WORDS_PER_FILE


def subset_of(path: str) -> str | None:
    """The subset a data file belongs to, or None for anything else.

    Data files sit one directory below data/, in a directory named for the
    subset alone or for the subset followed by a topic, language or part:
    data/common_crawl-politics-0016/shard_00000052.jsonl.zst. Matching the
    directory name rather than a substring anywhere in the path keeps a file
    from being claimed by a subset its name merely mentions. Only the two data
    extensions count, which leaves out the partial uploads
    (shard_00000032.jsonl.zst338588528) beside some olmOCR shards.
    """
    parts = path.split("/")
    if len(parts) != 3 or parts[0] != "data" or not path.endswith(EXTENSIONS):
        return None
    directory = parts[1]
    for subset in SUBSETS:
        if directory == subset or directory.startswith(subset + "-"):
            return subset
    return None


def subset_files(all_paths, subset: str) -> list[str]:
    """The subset's data files, sorted by path."""
    return sorted(path for path in all_paths if subset_of(path) == subset)


def topic_of(directory: str, subset: str) -> str:
    """The topic a subset's directory holds: a WebOrganizer topic for the web
    and olmOCR subsets, a language for stack_edu.

    Numbered directories (common_crawl-politics-0016) and parts
    (olmocr_science_pdfs-electronics_and_hardware-part1) belong to the topic
    they split. A subset kept in one directory is its own topic.
    """
    if directory == subset:
        return subset
    if not directory.startswith(subset + "-"):
        raise ValueError(f"{directory} is not a {subset} directory")
    return re.sub(r"-(part)?\d+$", "", directory[len(subset) + 1:])


def directory_sizes(sizes: dict[str, int], subset: str) -> dict[str, dict]:
    """Files and compressed bytes in each of a subset's directories.

    S3-D2 in docs/deviations.md reports olmOCR's drawn words by topic against
    these byte shares, so the run records them from the listing it draws from.
    """
    out: dict[str, dict] = {}
    for path in subset_files(sizes, subset):
        directory = path.split("/")[1]
        entry = out.setdefault(directory, {
            "topic": topic_of(directory, subset), "files": 0, "bytes": 0})
        entry["files"] += 1
        entry["bytes"] += sizes[path]
    return out


def draw(paths: list[str], subset: str, seed: int = SEED) -> list[str]:
    """The registered draw: seeded, without replacement, one stream per subset.

    The whole shuffled order is returned rather than the first n, so that a
    file shorter than its quota can be made up by the next one along without
    leaving the registered order.
    """
    if not paths:
        raise ValueError(f"no data files found for subset {subset!r}")
    rng = random.Random(f"{seed}:{subset}")
    shuffled = list(paths)
    rng.shuffle(shuffled)
    return shuffled


def documents(handle, path: str):
    """The documents in one shard, in file order, decompressed as they stream.

    Reading stops wherever the caller stops, so a file is downloaded only as
    far as its quota needs.
    """
    if path.endswith(".jsonl.gz"):
        stream = gzip.GzipFile(fileobj=handle)
    elif path.endswith(".jsonl.zst"):
        import zstandard

        # A shard can hold several zstd frames; without read_across_frames the
        # reader stops silently at the end of the first.
        stream = zstandard.ZstdDecompressor().stream_reader(
            handle, read_across_frames=True)
    else:
        raise ValueError(f"not a data file: {path}")
    for line in io.TextIOWrapper(stream, encoding="utf-8"):
        if line.strip():
            yield json.loads(line)


@dataclass
class FileCount:
    path: str
    rows: int
    words: int
    hits: dict[str, int] = field(default_factory=dict)
    redacted: int = 0
    size: int = 0  # the whole file, compressed, in bytes


def count_file(path: str, docs, frames: dict[str, list[str]],
               quota: int = WORDS_PER_FILE) -> FileCount:
    """Count one file's documents in order until its word quota is reached.

    The document that crosses the quota is counted whole, so a file stops
    within one document of its quota rather than splitting a text.
    """
    import framecount

    record = FileCount(path=path, rows=0, words=0,
                       hits={frame_id: 0 for frame_id in frames})
    for document in docs:
        if "text" not in document:
            raise RuntimeError(
                f"no text field in {path}; fields are {sorted(document)}")
        text = document["text"] or ""
        record.rows += 1
        if text.strip() == REDACTED:
            record.redacted += 1
        if text:
            counts = framecount.count_frames(text, frames)
            record.words += counts["words"]
            for frame_id in frames:
                record.hits[frame_id] += counts[frame_id]
        if record.words >= quota:
            break
    return record


def totals(counts: list[FileCount]) -> dict[str, int]:
    out: dict[str, int] = {"words": 0, "rows": 0, "redacted": 0,
                           "files": len(counts)}
    for count in counts:
        out["words"] += count.words
        out["rows"] += count.rows
        out["redacted"] += count.redacted
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
        .pip_install("huggingface_hub==2.0.0", "fsspec==2026.9.0",
                     "zstandard==0.25.0")
        .add_local_file(REPO / "python" / "framecount.py", "/root/framecount.py")
        .add_local_file(REPO / "data" / "frames.csv", "/root/frames.csv")
    )

    app = modal.App("englishregisterstudy-dolma", image=image)
    volume = modal.Volume.from_name("englishregisterstudy", create_if_missing=True)
    OUT = Path("/data/dolma")

    def list_repo() -> dict[str, int]:
        """Every file at the pinned revision, with its size in bytes."""
        from huggingface_hub import HfApi
        from huggingface_hub.hf_api import RepoFile

        tree = HfApi().list_repo_tree(REPO_ID, repo_type="dataset",
                                      revision=REVISION, recursive=True)
        return {item.path: item.size for item in tree
                if isinstance(item, RepoFile)}

    @app.function(timeout=60 * 15)
    def list_layout() -> dict:
        """What the repository actually looks like, before anything is drawn.

        Listing file names is not drawing documents, so this can be run before
        the counting pass to confirm the paths the sampling frame assumes.
        """
        sizes = list_repo()
        paths = list(sizes)
        under_data = [p for p in paths if p.startswith("data/")]
        claimed = {subset: subset_files(paths, subset) for subset in SUBSETS}
        by_extension = {
            subset: {ext: sum(p.endswith(ext) for p in files)
                     for ext in EXTENSIONS}
            for subset, files in claimed.items()
        }
        unclaimed = [p for p in under_data if subset_of(p) is None]
        return {
            "repo": REPO_ID,
            "revision": REVISION,
            "files": len(paths),
            "files_under_data": len(under_data),
            "files_per_subset": {s: len(f) for s, f in claimed.items()},
            "bytes_per_subset": {s: sum(sizes[p] for p in f)
                                 for s, f in claimed.items()},
            "files_per_subset_by_extension": by_extension,
            "unclaimed_under_data": len(unclaimed),
            "unclaimed_sample": unclaimed[:5],
            "sample_paths": {s: f[:2] for s, f in claimed.items()},
        }

    # Counting runs at about 4.7 seconds per million words on one core, so
    # the 200 million of common_crawl is roughly a quarter of an hour.
    # Reading stops at each file's quota, so only the head of a shard is
    # downloaded. Most olmOCR shards hold well under a million words, so that
    # subset reads many more than 20 files to reach its 20 million.
    @app.function(timeout=60 * 60 * 6, cpu=2, volumes={"/data": volume})
    def count_subset(subset: str) -> dict:
        """Draw one subset's files and count the frames in them."""
        import datetime

        from huggingface_hub import HfFileSystem

        import framecount

        frames = framecount.load_frames("/root/frames.csv")
        sizes = list_repo()
        paths = subset_files(sizes, subset)
        order = draw(paths, subset)
        fs = HfFileSystem()

        counts: list[FileCount] = []
        for path in order:
            if enough(counts, subset):
                break
            with fs.open(f"datasets/{REPO_ID}@{REVISION}/{path}", "rb",
                         block_size=8 * 2**20) as handle:
                record = count_file(path, documents(handle, path), frames)
            record.size = sizes[path]
            counts.append(record)

        summary = totals(counts)
        result = {
            "subset": subset,
            "repo": REPO_ID,
            "revision": REVISION,
            "seed": SEED,
            "words_wanted": words_wanted(subset),
            "words_per_file": WORDS_PER_FILE,
            "files_available": len(paths),
            "bytes_available": sum(sizes[p] for p in paths),
            "directories": directory_sizes(sizes, subset),
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
                  f"{summary['files']} files, {summary['redacted']:,} "
                  f"redacted documents")
