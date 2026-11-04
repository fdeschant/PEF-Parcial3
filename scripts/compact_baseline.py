"""Extrae una línea base compacta desde un reporte de pytest-benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _machine_info(data: dict) -> dict[str, object]:
    info = data.get("machine_info", {})
    cpu = info.get("cpu", {})
    return {
        "system": info.get("system"),
        "release": info.get("release"),
        "machine": info.get("machine"),
        "python_version": info.get("python_version"),
        "cpu": cpu.get("brand_raw") if isinstance(cpu, dict) else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    data = json.loads(args.source.read_text(encoding="utf-8"))
    benchmarks = []
    for benchmark in data.get("benchmarks", []):
        median = benchmark.get("stats", {}).get("median")
        if median is None:
            raise SystemExit(f"El benchmark {benchmark.get('name')!r} no tiene mediana")
        benchmarks.append(
            {
                "name": benchmark["name"],
                "stats": {"median": median},
            }
        )

    payload = {
        "source": "pytest-benchmark",
        "generated_at": data.get("datetime"),
        "machine_info": _machine_info(data),
        "benchmarks": benchmarks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Línea base compacta escrita en {args.output} ({len(benchmarks)} benchmarks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
