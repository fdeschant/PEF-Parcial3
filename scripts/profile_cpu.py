"""Genera perfiles de CPU con cProfile y pyinstrument."""

from __future__ import annotations

import argparse
import cProfile
import io
import pstats
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator import generate_documents
from inverted_index import InvertedIndexEngine
from search_sequential import SequentialSearchEngine


def _profile_cprofile(docs_dir: str, reports: Path) -> None:
    engine = InvertedIndexEngine(docs_dir)
    profiler = cProfile.Profile()
    profiler.enable()
    engine.build_index()
    engine.search("python java")
    profiler.disable()

    output = io.StringIO()
    stats = pstats.Stats(profiler, stream=output).sort_stats("cumulative")
    stats.print_stats(25)
    (reports / "profile.txt").write_text(output.getvalue(), encoding="utf-8")
    profiler.dump_stats(str(reports / "profile.prof"))


def _profile_pyinstrument(docs_dir: str, reports: Path) -> None:
    from pyinstrument import Profiler

    engine = SequentialSearchEngine(docs_dir)
    profiler = Profiler(interval=0.001)
    profiler.start()
    engine.load_documents()
    engine.search("python java")
    profiler.stop()
    (reports / "pyinstrument.html").write_text(profiler.output_html(), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("reports"))
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        generate_documents(args.docs, tmpdir, seed=args.seed)
        _profile_cprofile(tmpdir, args.output)
        _profile_pyinstrument(tmpdir, args.output)

    print(f"Perfiles generados en {args.output}")
    print("  - profile.txt / profile.prof (cProfile)")
    print("  - pyinstrument.html (pyinstrument)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
