"""Valida el consumo de memoria contra un umbral absoluto y una línea base."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ABSOLUTE_LIMIT_MB = 256.0
BASELINE_FACTOR = 1.5


def _index_peak(payload: dict) -> float:
    for scenario in payload["scenarios"]:
        if scenario["label"] == "index_build":
            return float(scenario["peak_mb"])
    raise ValueError("El reporte no contiene el escenario index_build")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("current", type=Path)
    parser.add_argument("baseline", type=Path)
    args = parser.parse_args()

    current = _index_peak(json.loads(args.current.read_text(encoding="utf-8")))
    baseline = _index_peak(json.loads(args.baseline.read_text(encoding="utf-8")))
    limit = min(ABSOLUTE_LIMIT_MB, baseline * BASELINE_FACTOR)
    print(
        f"Memoria pico index_build: {current:.2f} MB "
        f"(base {baseline:.2f} MB, límite {limit:.2f} MB)"
    )
    if current > limit:
        print("FALLA: consumo de memoria por encima del límite permitido.")
        return 1
    print("OK: consumo de memoria dentro del límite.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
