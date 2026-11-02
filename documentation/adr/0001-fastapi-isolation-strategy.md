# ADR 0001: Isolated FastAPI Wrapper

The FastAPI API lives in a single file, `api.py`, at the project root. No core
module imports it, and `main.py` does not import it either: the API is an
independent entry point started with Uvicorn. Removing the API means deleting
`api.py`, `tests/test_api.py`, and the FastAPI/Uvicorn dependencies.

**Why**: the assignment asks for the use of a framework, but the core search
engine must remain usable from the CLI and from tests without starting an HTTP
server. Keeping the adapter isolated makes the framework an optional delivery
mechanism rather than a dependency of the algorithms.

**Consequences**:

- `api.py` contains only HTTP concerns: validation, serialization, lifespan and
  error mapping. It delegates all search logic to the core modules.
- The core can be tested and benchmarked without installing FastAPI.
- The CLI menu is unaffected by API changes.
- If the course disallows FastAPI, the removal cost is limited to the adapter,
  its tests and its requirements.
