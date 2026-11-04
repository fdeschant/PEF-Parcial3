# Integración continua

## Objetivo

El pipeline se ejecuta en cada push y en cada pull request hacia `main`. Ningún
cambio se integra si incumple los umbrales de calidad, seguridad, pruebas,
documentación o rendimiento definidos por el equipo.

## Etapas

```mermaid
flowchart LR
    A[1. Integración<br/>push / PR] --> B[2. Preparación<br/>dependencias fijadas]
    B --> C[3. Calidad estática<br/>Ruff · Pylint · mypy · Radon]
    B --> D[4. Pruebas<br/>pytest · cobertura]
    B --> E[5. Seguridad<br/>Bandit · pip-audit · Gitleaks]
    B --> F[6. Documentación<br/>MkDocs · Lychee]
    D --> G[7. Rendimiento<br/>benchmark · memoria · profiling]
    C --> H[8. Resultado final]
    D --> H
    E --> H
    F --> H
    G --> H
```

Las etapas 3 a 6 corren en paralelo porque no dependen entre sí. Rendimiento
espera a las pruebas para no competir por CPU con la matriz de Python. El
resultado final consolida los artefactos y falla si alguna etapa falló.

## Matriz de controles

| Control | Herramienta | Comando | Reporte | Criterio de rechazo |
|---|---|---|---|---|
| Pruebas | pytest | `pytest -q --junitxml=reports/junit.xml` | JUnit XML | Una o más pruebas fallan. |
| Cobertura | pytest-cov / coverage.py | `pytest --cov --cov-report=xml` | XML + HTML | Cobertura < 80%. |
| Benchmark | pytest-benchmark | `pytest benchmarks --benchmark-json=reports/benchmark.json` | JSON | Regresión > 50% en `main`/schedule. |
| Profiling CPU | cProfile + pyinstrument | `python scripts/profile_cpu.py` | `profile.txt`, `.prof`, HTML | Informativo; se archiva. |
| Análisis estático | Ruff | `ruff check .` / `ruff format --check .` | Anotaciones GitHub | Cualquier violación. |
| Análisis de diseño | Pylint | `pylint --rcfile=.pylintrc ...` | Texto | Score < 8.0. |
| Complejidad y tamaño | Radon + Pylint | `python scripts/check_complexity.py`; `pylint --rcfile=.pylintrc` | JSON CC/MI + texto | Bloque ≥ C, MI < 20, `max-statements=60` o `max-branches=15`. |
| Tipado | mypy | `mypy` | Texto | Cualquier error en el núcleo. |
| Memoria | tracemalloc | `python scripts/measure_memory.py --repeat 3` + `check_memory.py` | JSON | Mediana de 3 corridas > `min(256 MB, 1.5× base)` en `main`. |
| Código inseguro | Bandit | `bandit -r . ... -lll -iii` | JSON | HIGH/HIGH. |
| Dependencias | pip-audit | `pip-audit -r requirements.txt` | JSON | Cualquier CVE en ejecución. |
| Secretos | Gitleaks | `gitleaks git` | SARIF | Cualquier secreto. |
| Documentación | MkDocs | `mkdocs build --strict` | Sitio HTML | El sitio no compila o hay warnings. |
| Enlaces | Lychee | `lychee --offline documentation` | Texto | Enlace interno roto. |

Lychee se ejecuta con `--offline`: valida enlaces internos y evita depender de
servicios externos durante cada push. Los enlaces externos se revisan
manualmente cuando se agrega o cambia una referencia.

## Jobs del workflow

| Job | Depende de | Contenido |
|---|---|---|
| `preparacion` | — | Instala dependencias fijadas, `pip check`, compila módulos. |
| `calidad-estatica` | `preparacion` | Ruff, formato, mypy, Pylint, Radon. |
| `pruebas-cobertura` | `preparacion` | Matriz Python 3.11/3.12/3.13. |
| `seguridad` | `preparacion` | Bandit, pip-audit, Gitleaks y SARIF de Gitleaks. |
| `documentacion` | `preparacion` | MkDocs strict y Lychee. |
| `rendimiento-memoria` | `pruebas-cobertura` | Benchmarks, memoria y profiling. |
| `resultado-final` | todos | Verifica estados, descarga artefactos y genera resumen. |

## Artefactos

- `reportes-pruebas-<python>`: JUnit, cobertura XML y HTML.
- `reportes-calidad`: Ruff, formato, mypy, Pylint, Radon CC y MI.
- `reportes-seguridad`: Bandit JSON, pip-audit JSON, Gitleaks SARIF.
- `documentacion-html`: sitio MkDocs.
- `reportes-rendimiento`: benchmark JSON, memoria JSON, perfil CPU.
- `baseline-generada`: líneas base de benchmark y memoria generadas en CI.
- `resumen-ci`: resumen consolidado.

El SARIF de Gitleaks se intenta subir a GitHub Code Scanning. Si el repositorio
no tiene Code Scanning habilitado, el paso es tolerante a fallos y el reporte
queda igual como artefacto. Bandit se publica como JSON porque su versión actual
no emite SARIF nativo.

## Regeneración de la línea base en CI

`.github/workflows/baseline.yml` se ejecuta manualmente desde **Actions →
Regenerar línea base → Run workflow**. Corre en `ubuntu-latest` con la misma
versión de Python que el job de rendimiento y:

1. ejecuta los benchmarks;
2. compacta el JSON a las medianas necesarias;
3. mide memoria con tres repeticiones y conserva la mediana;
4. publica los artefactos;
5. abre un pull request `ci/baseline-<run_id>` con las líneas base actualizadas.

El PR se revisa como cualquier cambio: no se usa para ocultar una regresión, sino
para alinear la línea base con el entorno real de CI.

Si el repositorio no permite que `GITHUB_TOKEN` cree pull requests, habilitar
**Settings → Actions → General → Allow GitHub Actions to create and approve pull
requests** o descargar el artefacto `baseline-generada` y commitear los dos
archivos manualmente.

## Política de bloqueo

| Condición | Bloquea |
|---|---|
| Prueba fallida | Sí |
| Cobertura < 80% | Sí |
| Ruff con violaciones | Sí |
| Pylint < 8.0 | Sí |
| mypy con errores en el núcleo | Sí |
| Complejidad ≥ C o MI < 20 | Sí |
| Bandit HIGH/HIGH | Sí |
| Secreto detectado | Sí |
| CVE en dependencias de ejecución | Sí |
| Documentación no compila o enlace roto | Sí |
| Benchmark con regresión > 50% en `main` | Sí |
| Memoria fuera de límite en `main` | Sí |
| Benchmark/memoria en PR | No; se informa |

## Ejecución local

El requisito de reproducibilidad se cumple con un único comando:

```bash
make ci
```

o, sin `make`:

```bash
bash scripts/run_ci_locally.sh
```

El script usa exactamente las mismas herramientas, archivos de configuración y
umbrales que CI:

```bash
pip check
python -m compileall -q *.py scripts tests benchmarks
ruff check .
ruff format --check .
mypy
pylint --rcfile=.pylintrc <módulos>
python scripts/check_complexity.py
pytest -q --cov --cov-report=xml:reports/coverage.xml
bandit -r . ... -lll -iii
pip-audit -r requirements.txt
gitleaks git  # o gitleaks dir . si no hay repositorio Git
mkdocs build --strict
lychee --offline --no-progress documentation
pytest benchmarks -q --benchmark-json=reports/benchmark.json
python scripts/check_benchmark.py reports/benchmark.json benchmarks/baseline.json
python scripts/measure_memory.py --repeat 3 --output reports/memory.json
python scripts/check_memory.py reports/memory.json benchmarks/memory_baseline.json
python scripts/profile_cpu.py
```

## Protección de la rama `main`

Configurar en GitHub:

1. **Settings → Branches → Add branch protection rule** para `main`.
2. Exigir pull request antes de merge.
3. Exigir que pasen los checks:
   - `Preparación del entorno`
   - `Calidad estática`
   - `Pruebas y cobertura (3.11)`, `(3.12)`, `(3.13)`
   - `Seguridad`
   - `Documentación`
   - `Rendimiento y memoria`
   - `Resultado final`
4. Exigir 0 aprobaciones si se trabaja solo; 1 o más si hay equipo. GitHub
   no permite autoaprobarse, pero sí permite mergear con 0 aprobaciones.
5. Bloquear force pushes y borrado de la rama.

## Publicación de documentación

`.github/workflows/pages.yml` construye el sitio en cada push a `main` y lo
publica en GitHub Pages. Requiere:

1. Repositorio con GitHub Pages habilitado y fuente **GitHub Actions**.
2. Permisos `pages: write` e `id-token: write` (ya declarados en el workflow).
3. Rama `main` como única fuente de publicación.

## Resolución de fallos

| Fallo | Causa habitual | Acción |
|---|---|---|
| Ruff | Formato o import desordenado | `ruff check --fix .` y `ruff format .` |
| Pylint | Complejidad o diseño | Refactorizar o justificar la excepción. |
| mypy | Anotación faltante o incompatible | Corregir el tipo; no usar `Any` sin justificar. |
| Cobertura | Código nuevo sin pruebas | Agregar pruebas; no bajar el umbral sin justificación. |
| Bandit | Patrón inseguro | Corregir; si es falso positivo, registrar en `SECURITY.md`. |
| pip-audit | Dependencia vulnerable | Actualizar; si no hay fix, excepción documentada. |
| Gitleaks | Secreto | Rotar, eliminar y revisar historial. |
| MkDocs | Enlace o warning | Corregir la página; `mkdocs build --strict` local. |
| Benchmark | Regresión real o ruido | Revisar profiling; si el cambio es esperado, ejecutar **Regenerar línea base** y mergear el PR. |
| Memoria | Nuevo uso de memoria | Revisar allocations; ajustar solo con justificación. |
