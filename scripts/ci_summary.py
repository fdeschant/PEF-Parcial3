"""Construye un resumen Markdown de los reportes de CI."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

REPORTS = [
    ("Pruebas (JUnit)", "reports/junit.xml"),
    ("Cobertura (XML)", "reports/coverage.xml"),
    ("Bandit (JSON)", "reports/bandit.json"),
    ("pip-audit (JSON)", "reports/pip-audit.json"),
    ("Gitleaks (SARIF)", "reports/gitleaks.sarif"),
    ("Ruff (texto)", "reports/ruff.txt"),
    ("Ruff formato (texto)", "reports/ruff-format.txt"),
    ("mypy (texto)", "reports/mypy.txt"),
    ("Radon CC (JSON)", "reports/radon-cc.json"),
    ("Radon MI (JSON)", "reports/radon-mi.json"),
    ("Benchmark (JSON)", "reports/benchmark.json"),
    ("Memoria (JSON)", "reports/memory.json"),
    ("Perfil CPU (texto)", "reports/profile.txt"),
    ("Documentación (sitio)", "site/index.html"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("reports/summary.md"))
    args = parser.parse_args()

    lines = ["# Resumen de CI", ""]
    lines.append(f"- Commit: `{os.environ.get('GITHUB_SHA', 'local')}`")
    lines.append(f"- Ejecución: `{os.environ.get('GITHUB_RUN_ID', 'local')}`")
    lines.append("")
    lines.append("| Reporte | Archivo | Estado |")
    lines.append("|---|---|---|")
    for label, path in REPORTS:
        file = Path(path)
        status = "generado" if file.exists() else "no generado"
        lines.append(f"| {label} | `{path}` | {status} |")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Resumen escrito en {args.output}")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        Path(summary_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
