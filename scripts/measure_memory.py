"""Mide memoria pico y asignaciones relevantes con tracemalloc."""

from __future__ import annotations

import argparse
import gc
import json
import resource
import sys
import tempfile
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator import generate_documents, generate_large_documents
from inverted_index import InvertedIndexEngine
from large_file_handler import read_file_buffered
from search_sequential import SequentialSearchEngine


def _top_allocations(limit: int = 10) -> list[dict[str, object]]:
    snapshot = tracemalloc.take_snapshot()
    return [
        {
            "location": str(stat.traceback),
            "size_kb": round(stat.size / 1024, 2),
            "count": stat.count,
        }
        for stat in snapshot.statistics("lineno")[:limit]
    ]


def _measure(label: str, operation) -> dict[str, object]:
    gc.collect()
    tracemalloc.start()
    result = operation()
    current, peak = tracemalloc.get_traced_memory()
    allocations = _top_allocations()
    tracemalloc.stop()
    return {
        "label": label,
        "current_mb": round(current / (1024 * 1024), 2),
        "peak_mb": round(peak / (1024 * 1024), 2),
        "result": result,
        "top_allocations": allocations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("reports/memory.json"))
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmpdir:
        generate_documents(args.docs, tmpdir, seed=args.seed)
        generate_large_documents(1, tmpdir, words_per_doc=10000, seed=args.seed)

        index_engine = InvertedIndexEngine(tmpdir)
        index_result = _measure(
            "index_build",
            lambda: {
                "documents": index_engine.build_index(),
                "terms": len(index_engine.index.index),
            },
        )

        sequential_engine = SequentialSearchEngine(tmpdir)
        sequential_result = _measure(
            "sequential_load",
            lambda: {"documents": sequential_engine.load_documents()},
        )

        large_file = next(Path(tmpdir).glob("documento_large_*.txt"))
        file_result = _measure(
            "large_file_read",
            lambda: {"characters": len(read_file_buffered(str(large_file)))},
        )

    payload = {
        "scenarios": [index_result, sequential_result, file_result],
        "process_peak_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    for scenario in payload["scenarios"]:
        print(
            f"[{scenario['label']}] pico={scenario['peak_mb']:.2f} MB "
            f"actual={scenario['current_mb']:.2f} MB"
        )
    print(f"Reporte escrito en {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
