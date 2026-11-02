"""Compara un reporte de pytest-benchmark contra una línea base."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load(path: Path) -> dict[str, float]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {benchmark["name"]: benchmark["stats"]["median"] for benchmark in data["benchmarks"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("current", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("--tolerance", type=float, default=0.50)
    args = parser.parse_args()

    current = _load(args.current)
    baseline = _load(args.baseline)

    failures: list[str] = []
    print(f"Comparación de benchmarks (tolerancia {args.tolerance:.0%}):")
    for name, current_median in sorted(current.items()):
        if name not in baseline:
            print(f"  INFO: {name} no tiene línea base")
            continue
        baseline_median = baseline[name]
        ratio = current_median / baseline_median if baseline_median else float("inf")
        status = "OK" if ratio <= 1 + args.tolerance else "REGRESION"
        print(
            f"  {status}: {name} = {current_median:.6f}s "
            f"(base {baseline_median:.6f}s, ratio {ratio:.2f}x)"
        )
        if ratio > 1 + args.tolerance:
            failures.append(name)

    if failures:
        print("\nBenchmarks con regresión significativa:")
        for name in failures:
            print(f"  - {name}")
        return 1

    print("\nSin regresiones significativas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
