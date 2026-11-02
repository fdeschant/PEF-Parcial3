PYTHON ?= python3.11
VENV ?= .venv
BIN := $(VENV)/bin
GITLEAKS ?= .tools/gitleaks
LYCHEE ?= .tools/lychee
CORE := search_common.py search_sequential.py inverted_index.py ranking.py cache.py concurrency.py generator.py large_file_handler.py config.py api.py

.PHONY: install lint types test security docs perf baseline ci clean

install: $(BIN)/python
$(BIN)/python: requirements.txt requirements-dev.txt requirements-docs.txt
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt -r requirements-dev.txt -r requirements-docs.txt
	$(BIN)/pip check
	$(BIN)/python -m compileall -q *.py scripts tests benchmarks

lint: install
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .
	$(BIN)/pylint --rcfile=.pylintrc $(CORE)

types: install
	$(BIN)/mypy

test: install
	mkdir -p reports
	$(BIN)/pytest -q \
		--cov \
		--cov-report=term \
		--cov-report=xml:reports/coverage.xml \
		--cov-report=html:reports/htmlcov \
		--junitxml=reports/junit.xml

security: install
	mkdir -p reports
	$(BIN)/bandit -r . -x ./.venv,./tests,./docs,./documentation,./reports,./benchmarks,./scripts -f json -o reports/bandit.json -q || true
	$(BIN)/bandit -r . -x ./.venv,./tests,./docs,./documentation,./reports,./benchmarks,./scripts -lll -iii
	$(BIN)/pip-audit -r requirements.txt --format json --output reports/pip-audit.json
	$(BIN)/pip-audit -r requirements-dev.txt --format json --output reports/pip-audit-dev.json || true
	@if git rev-parse --git-dir >/dev/null 2>&1; then \
		$(GITLEAKS) git --report-format sarif --report-path reports/gitleaks.sarif; \
	else \
		$(GITLEAKS) dir . --report-format sarif --report-path reports/gitleaks.sarif; \
	fi

docs: install
	$(BIN)/mkdocs build --strict
	$(LYCHEE) --offline --no-progress documentation

perf: install
	mkdir -p reports
	$(BIN)/pytest benchmarks -q --benchmark-json=reports/benchmark.json
	$(BIN)/python scripts/check_benchmark.py reports/benchmark.json benchmarks/baseline.json
	$(BIN)/python scripts/measure_memory.py --output reports/memory.json
	$(BIN)/python scripts/check_memory.py reports/memory.json benchmarks/memory_baseline.json
	$(BIN)/python scripts/profile_cpu.py

baseline: install
	$(BIN)/pytest benchmarks -q --benchmark-json=benchmarks/baseline.json
	$(BIN)/python scripts/measure_memory.py --output benchmarks/memory_baseline.json

ci: lint types test security docs perf
	@echo "Todos los controles de CI pasaron."

clean:
	rm -rf reports site htmlcov .pytest_cache .mypy_cache .ruff_cache
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
