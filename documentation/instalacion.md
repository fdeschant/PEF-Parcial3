# Instalación y ejecución

## Requisitos

- Python **3.11+** (CI prueba 3.11, 3.12 y 3.13).
- `make` y `bash` para los atajos de desarrollo.
- Git para clonar y para que Gitleaks analice el historial.
- Opcional: Docker, solo si preferís ejecutar herramientas externas en contenedor.

## Instalación reproducible

```bash
git clone <url-del-repositorio>
cd Parcial3

python3.11 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt -r requirements-docs.txt
```

Las versiones están fijadas en:

| Archivo | Contenido |
|---|---|
| `requirements.txt` | Dependencias de ejecución. |
| `requirements-dev.txt` | Pruebas, calidad, seguridad y rendimiento. |
| `requirements-docs.txt` | MkDocs, Material y mkdocstrings. |

Verificar que el entorno quedó consistente:

```bash
pip check
python -m compileall -q *.py scripts tests benchmarks
```

## Configuración

La aplicación no requiere variables de entorno obligatorias. Los valores por
defecto viven en `config.py` y pueden ajustarse editando ese archivo:

| Constante | Valor por defecto | Uso |
|---|---|---|
| `DOCS_DIR` | `docs/` | Directorio del corpus que indexan la CLI y la API. |
| `REPORTS_DIR` | `reports/` | Salida de los reportes generados por la CLI. |
| `NUM_DOCUMENTS` | `200` | Cantidad de documentos del corpus sintético. |
| `MIN_WORDS_PER_DOC` / `MAX_WORDS_PER_DOC` | `50` / `200` | Rango de palabras por documento. |
| `CACHE_MAX_SIZE` | `128` | Capacidad de la caché LRU de consultas. |
| `DEFAULT_TOP_K` | `10` | Cantidad de resultados devueltos por búsqueda. |
| `DEFAULT_WORKERS` | `os.cpu_count()` | Workers del pool para archivos grandes. |

Para cambiar el corpus sin tocar el código se usan los argumentos del generador:

```bash
python scripts/generate_corpus.py --docs 500 --large 2 --words-per-large 20000 --seed 7
```

La API permite inyectar otro directorio al crear la aplicación:

```python
from api import create_app

app = create_app(docs_dir="/ruta/a/otro/corpus")
```

Los atajos de `make` y `scripts/run_ci_locally.sh` respetan `PYTHON` y `VENV`;
por ejemplo, `PYTHON=python3.13 VENV=.venv313 make ci`. La herramienta de
memoria acepta `--repeat` para repetir cada medición y conservar la mediana.

## Generar el corpus

El corpus no se versiona. Se genera con una semilla para que sea reproducible:

```bash
python scripts/generate_corpus.py --docs 200 --large 1 --seed 42
```

Esto crea `docs/documento_*.txt` y, si se indica `--large`, archivos
`docs/documento_large_*.txt` de 10.000 palabras.

## Ejecutar la aplicación

### Menú interactivo

```bash
python main.py
```

Opciones principales:

| Opción | Acción |
|---|---|
| 1 | Generar documentos sintéticos. |
| 2 | Generar documentos grandes. |
| 3 | Búsqueda secuencial. |
| 4 | Búsqueda con índice invertido. |
| 5 | Búsqueda con caché. |
| 6 | Índice para archivos grandes. |
| 7 | Benchmark completo. |
| 8 | Análisis de complejidad. |
| 9 | Test completo + reporte + perfilado. |
| 10 | Análisis de calidad (Pylint + Radon). |
| 11 | Perfilado cProfile + SnakeViz. |
| 12 | Construir la documentación MkDocs. |

### API REST

```bash
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- Salud: <http://127.0.0.1:8000/health>

La API indexa el corpus de `docs/` al iniciar. Si el corpus está vacío, el
servicio responde igualmente y devuelve listas vacías.

## Ejecutar pruebas

```bash
pytest -q
pytest -q --cov --cov-report=term-missing
```

La cobertura mínima es **80%**; el umbral está en `pyproject.toml`.

## Ejecutar los controles de CI en local

La forma recomendada es:

```bash
make ci
```

o, de forma explícita:

```bash
bash scripts/run_ci_locally.sh
```

El script crea el entorno si falta, instala dependencias fijadas, descarga
Gitleaks y Lychee si no están en `.tools/`, ejecuta todos los controles y escribe
los reportes en `reports/`.

### Comandos individuales

```bash
make lint       # Ruff + Pylint
make types      # mypy
make test       # pytest + cobertura
make security   # Bandit + pip-audit + Gitleaks
make docs       # MkDocs strict + Lychee
make perf       # benchmarks + memoria + profiling
make baseline   # regenerar líneas base
```

## Documentación

```bash
mkdocs serve      # vista previa en http://127.0.0.1:8000
mkdocs build --strict
```

El sitio se genera en `site/`. GitHub Pages lo publica desde `main` mediante
`.github/workflows/pages.yml`.

## Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ModuleNotFoundError` | Entorno virtual no activado. | `source .venv/bin/activate` |
| `mkdocs: command not found` | Faltan dependencias de docs. | `pip install -r requirements-docs.txt` |
| Benchmarks inestables | Carga del equipo o hardware distinto. | Cerrar procesos, repetir, revisar tolerancia. |
| Gitleaks no encontrado | No se descargó la herramienta. | `bash scripts/run_ci_locally.sh` o descargar en `.tools/`. |
| Lychee falla por enlaces externos | Sin conectividad o enlace externo caído. | El control automático usa `--offline` y valida solo enlaces internos; los externos se revisan manualmente. |
| `docs/` vacío | Corpus no generado. | `python scripts/generate_corpus.py --docs 200 --seed 42` |
