#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3.11}"
VENV="${VENV:-.venv}"
GITLEAKS_VERSION="8.30.1"
LYCHEE_VERSION="lychee-v0.24.2"

step() {
  printf '\n\033[1;34m==> %s\033[0m\n' "$1"
}

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "No se encontró $PYTHON. Instalá Python 3.11+ o definí PYTHON=..." >&2
  exit 1
fi

if [ ! -x "$VENV/bin/python" ]; then
  "$PYTHON" -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip -q
pip install -q -r requirements.txt -r requirements-dev.txt -r requirements-docs.txt
pip check
python -m compileall -q *.py scripts tests benchmarks

mkdir -p reports .tools

ensure_gitleaks() {
  if [ -x .tools/gitleaks ]; then
    return
  fi
  echo "Descargando Gitleaks ${GITLEAKS_VERSION}..."
  curl -sL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" -o /tmp/gitleaks.tgz
  tar -xzf /tmp/gitleaks.tgz -C .tools gitleaks
}

ensure_lychee() {
  if [ -x .tools/lychee ]; then
    return
  fi
  echo "Descargando Lychee..."
  curl -sL "https://github.com/lycheeverse/lychee/releases/download/${LYCHEE_VERSION}/lychee-x86_64-unknown-linux-gnu.tar.gz" -o /tmp/lychee.tgz
  tmpdir="$(mktemp -d)"
  tar -xzf /tmp/lychee.tgz -C "$tmpdir"
  install -m 0755 "$(find "$tmpdir" -type f -name lychee -print -quit)" .tools/lychee
  rm -rf "$tmpdir"
}

step "Calidad estática: Ruff"
ruff check .
ruff format --check .

step "Tipado estático: mypy"
mypy

step "Diseño: Pylint"
pylint --rcfile=.pylintrc \
  search_common.py search_sequential.py inverted_index.py ranking.py \
  cache.py concurrency.py generator.py large_file_handler.py config.py api.py \
  | tee reports/pylint.txt

step "Complejidad y mantenibilidad: Radon"
python scripts/check_complexity.py

step "Pruebas y cobertura"
pytest -q \
  --cov \
  --cov-report=term \
  --cov-report=xml:reports/coverage.xml \
  --cov-report=html:reports/htmlcov \
  --junitxml=reports/junit.xml

step "Seguridad: Bandit"
bandit -r . -x ./.venv,./tests,./docs,./documentation,./reports,./benchmarks,./scripts -f json -o reports/bandit.json -q || true
bandit -r . -x ./.venv,./tests,./docs,./documentation,./reports,./benchmarks,./scripts -lll -iii

step "Seguridad: pip-audit"
pip-audit -r requirements.txt --format json --output reports/pip-audit.json
pip-audit -r requirements-dev.txt --format json --output reports/pip-audit-dev.json || true

step "Seguridad: Gitleaks"
ensure_gitleaks
if git rev-parse --git-dir >/dev/null 2>&1; then
  .tools/gitleaks git --report-format sarif --report-path reports/gitleaks.sarif
else
  .tools/gitleaks dir . --report-format sarif --report-path reports/gitleaks.sarif
fi

step "Documentación: MkDocs"
mkdocs build --strict

step "Documentación: enlaces internos"
ensure_lychee
.tools/lychee --offline --no-progress documentation

step "Rendimiento: benchmarks"
pytest benchmarks -q --benchmark-json=reports/benchmark.json
python scripts/check_benchmark.py reports/benchmark.json benchmarks/baseline.json

step "Rendimiento: memoria"
python scripts/measure_memory.py --output reports/memory.json
python scripts/check_memory.py reports/memory.json benchmarks/memory_baseline.json

step "Rendimiento: perfilado de CPU"
python scripts/profile_cpu.py

step "Resumen"
python scripts/ci_summary.py

printf '\n\033[1;32mTodos los controles de CI pasaron.\033[0m\n'
