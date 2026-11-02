"""Valida complejidad ciclomática e índice de mantenibilidad con Radon."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CORE_FILES = [
    "search_common.py",
    "search_sequential.py",
    "inverted_index.py",
    "ranking.py",
    "cache.py",
    "concurrency.py",
    "generator.py",
    "large_file_handler.py",
    "config.py",
    "api.py",
]

MAX_RANK = "C"
MIN_MAINTAINABILITY = 20.0


def _run_radon(args: list[str]) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "radon", *args, *CORE_FILES],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return result.stdout


def main() -> int:
    reports = Path("reports")
    reports.mkdir(exist_ok=True)

    cc_output = _run_radon(["cc", "-s", "-j"])
    mi_output = _run_radon(["mi", "-s", "-j"])
    (reports / "radon-cc.json").write_text(cc_output, encoding="utf-8")
    (reports / "radon-mi.json").write_text(mi_output, encoding="utf-8")

    complexity = json.loads(cc_output)
    maintainability = json.loads(mi_output)

    failures: list[str] = []
    print("Complejidad ciclomática (bloques con rango >= C):")
    for filename, blocks in complexity.items():
        for block in blocks:
            if block["rank"] >= MAX_RANK:
                failures.append(
                    f"{filename}:{block['lineno']} {block['name']} "
                    f"rango {block['rank']} (CC {block['complexity']})"
                )
                print(f"  FALLA {failures[-1]}")
    if not failures:
        print("  OK: todos los bloques son A o B")

    print(f"Índice de mantenibilidad (mínimo {MIN_MAINTAINABILITY}):")
    for filename, data in maintainability.items():
        score = float(data["mi"])
        status = "OK" if score >= MIN_MAINTAINABILITY else "FALLA"
        print(f"  {status}: {filename} = {score:.2f}")
        if score < MIN_MAINTAINABILITY:
            failures.append(f"{filename}: MI {score:.2f} < {MIN_MAINTAINABILITY}")

    if failures:
        print("\nFallaron los siguientes controles de complejidad:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("\nComplejidad y mantenibilidad dentro de los umbrales.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
