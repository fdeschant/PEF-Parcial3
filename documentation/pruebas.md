# Pruebas

## Estrategia

La suite combina pruebas unitarias y de integración:

- **Unitarias**: cada módulo del núcleo se prueba con corpus temporales.
- **Integración**: la API se prueba con `TestClient` y el menú con un script
  dedicado.
- **Regresión**: cobertura mínima y benchmarks contra línea base.
- **Seguridad**: Bandit, pip-audit y Gitleaks en cada push/PR.

Los datos de prueba se crean en directorios temporales; no dependen de un corpus
versionado. Las pruebas son deterministas y rápidas (< 1 s en el entorno local).

## Estructura

| Archivo | Qué cubre |
|---|---|
| `tests/test_search_common.py` | Tokenización, snippets, IDs, listado y lectura. |
| `tests/test_search_sequential.py` | Carga, búsqueda, top-K, campos y casos vacíos. |
| `tests/test_inverted_index.py` | Posting lists, frecuencias, merge, búsqueda y conteo. |
| `tests/test_cache.py` | Hits, misses, normalización, LRU, hit rate y clear. |
| `tests/test_ranking.py` | Top-K con pocos y muchos resultados. |
| `tests/test_large_file_handler.py` | Buffering, tokens, total y batches paralelos. |
| `tests/test_generator.py` | Conteo, nombres, reproducibilidad y documentos grandes. |
| `tests/test_concurrency.py` | Búsqueda concurrente, hilos e índice paralelo. |
| `tests/test_api.py` | Salud, búsqueda, caché, validación y sin resultados. |
| `scripts/check_menu.py` | Verificación manual de todas las opciones del menú. |

## Casos representativos

| Caso | Resultado esperado |
|---|---|
| Consulta vacía | `[]` o HTTP 422 según el motor. |
| Consulta sin coincidencias | Lista vacía, sin excepción. |
| Todos los términos requeridos | Solo documentos con todos los términos. |
| `top_k` menor que resultados | Se devuelven exactamente `top_k`. |
| Caché LRU llena | Se desaloja la entrada menos usada. |
| Archivo con nombre inválido | `ValueError` en `parse_doc_id`. |
| Directorio inexistente | `[]` en `list_doc_files`. |
| API con `q` de 201 caracteres | HTTP 422. |
| Índice paralelo | Mismos IDs que la construcción secuencial. |

## Ejecución

```bash
pytest -q
pytest -q --cov --cov-report=term-missing
pytest benchmarks -q --benchmark-json=reports/benchmark.json
python scripts/check_menu.py
```

## Resultados actuales

Ejecución local con Python 3.11:

```text
60 passed, 1 warning
```

Cobertura:

```text
Name                    Stmts   Miss Branch BrPart  Cover
---------------------------------------------------------
api.py                     56      0      2      0   100%
cache.py                   37      1      6      1    95%
concurrency.py             47      6      4      1    86%
generator.py               41      0     14      0   100%
inverted_index.py          93      3     32      2    96%
large_file_handler.py      43      8      8      0    80%
search_common.py           29      0      6      0   100%
---------------------------------------------------------
TOTAL                     409     18     88      4    95%
```

La cobertura total es **95.17%**, por encima del umbral de **80%**.

## Matriz de CI

| Python | Ejecución |
|---|---|
| 3.11 | `pytest` + cobertura |
| 3.12 | `pytest` + cobertura |
| 3.13 | `pytest` + cobertura |

Cada versión publica JUnit, XML de cobertura y HTML como artefactos.

## Limitaciones

- La cobertura mide líneas y ramas, no calidad de las aserciones.
- Las pruebas de concurrencia usan corpus pequeños; no reemplazan un benchmark
  de carga.
- `scripts/check_menu.py` verifica que las opciones no exploten, no la estética
  de la salida.
