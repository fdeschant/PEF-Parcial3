# Mantenimiento

## Estructura del repositorio

```text
Parcial3/
├── api.py                  # Adaptador HTTP
├── cache.py                # Caché LRU
├── concurrency.py          # Búsqueda e indexación concurrente
├── config.py               # Constantes y rutas
├── generator.py            # Corpus sintético
├── inverted_index.py       # Índice y motor indexado
├── large_file_handler.py   # Buffering, batching y pool
├── main.py                 # Menú interactivo
├── ranking.py              # Top-K con heap
├── search_common.py        # Tokenización y utilidades
├── search_sequential.py    # Motor secuencial
├── benchmarks/             # Benchmarks y líneas base
├── documentation/          # Sitio MkDocs
├── scripts/                # Automatización de CI
├── tests/                  # Suite de pruebas
├── reports/                # Reportes generados (no versionados)
└── .github/workflows/      # CI y GitHub Pages
```

## Flujo de contribución

1. Crear una rama desde `main`.
2. Implementar el cambio y sus pruebas.
3. Actualizar la documentación afectada.
4. Ejecutar `make ci` localmente.
5. Abrir un pull request con el resumen y la evidencia de los controles.
6. Esperar revisión y checks verdes antes de integrar.

Los detalles de estilo y commits están en `CONTRIBUTING.md`.

## Actualización de dependencias

### Dependencias de ejecución

```bash
pip install --upgrade <paquete>
pip freeze > requirements.txt
```

Verificar que el archivo solo contenga dependencias directas e indirectas
necesarias. Luego:

```bash
pip check
pip-audit -r requirements.txt
pytest -q
```

### Dependencias de desarrollo y documentación

Repetir el procedimiento en `requirements-dev.txt` y `requirements-docs.txt`.
Dependabot abre pull requests semanales; no se integran sin CI verde.

## Actualización de líneas base

Las líneas base solo se regeneran cuando el cambio de rendimiento o memoria es
intencional y está justificado en el pull request.

```bash
make baseline
```

Equivale a:

```bash
pytest benchmarks -q --benchmark-json=reports/benchmark.json
cp reports/benchmark.json benchmarks/baseline.json
python scripts/measure_memory.py --output benchmarks/memory_baseline.json
```

Reglas:

1. Ejecutar en un equipo descargado.
2. Repetir al menos tres veces y conservar la mediana.
3. Documentar la causa del cambio en el PR.
4. No regenerar la línea base para “hacer pasar” una regresión.

## Actualización de la documentación

- Toda página nueva debe agregarse al `nav` de `mkdocs.yml`.
- Los enlaces internos se escriben relativos al archivo `.md`.
- Los diagramas usan Mermaid dentro de bloques ` ```mermaid `.
- La referencia de API se genera desde docstrings; no se edita a mano.

Validar antes de subir:

```bash
mkdocs build --strict
lychee --offline --no-progress documentation
```

## Cambios en el pipeline

- Los umbrales viven en `pyproject.toml`, `.pylintrc`, `scripts/check_complexity.py`,
  `scripts/check_benchmark.py` y `scripts/check_memory.py`.
- Un cambio de umbral requiere justificación y actualización de esta
  documentación y del ADR correspondiente.
- Los workflows deben mantener `permissions` mínimos.
- No agregar `continue-on-error` a controles bloqueantes.

## Resolución de problemas

| Problema | Diagnóstico | Solución |
|---|---|---|
| `docs/` vacío | No se generó el corpus. | `python scripts/generate_corpus.py --docs 200 --seed 42` |
| Pruebas lentas | Corpus grande o equipo cargado. | Usar corpus temporal en pruebas; cerrar procesos. |
| Benchmark inestable | Ruido del sistema. | Repetir, usar mediana, revisar tolerancia. |
| Cobertura baja | Código nuevo sin pruebas. | Agregar pruebas de rama y error. |
| MkDocs falla | Enlace roto o warning. | Corregir la página; revisar `mkdocs build --strict`. |
| Gitleaks falla | Secreto real o falso positivo. | Rotar o registrar excepción en `SECURITY.md`. |
| pip-audit falla | CVE detectado. | Actualizar dependencia; si no hay fix, excepción documentada. |
| CI remoto no corre | Workflow inválido o permisos. | Validar YAML y revisar la pestaña Actions. |

## Contacto y responsabilidades

| Rol | Responsabilidad |
|---|---|
| Mantenedor | Revisar PRs, aprobar cambios de umbral y releases. |
| Seguridad | Atender CVEs y excepciones de Bandit/Gitleaks. |
| Documentación | Mantener el sitio y los ADR actualizados. |
| CI | Mantener workflows, dependencias y líneas base. |

## Hoja de ruta

- Persistir el índice para evitar reconstruirlo al iniciar.
- Agregar stemming y sinónimos configurables.
- Incorporar autenticación si la API se expone fuera de localhost.
- Añadir pruebas de carga con corpus de mayor tamaño.
