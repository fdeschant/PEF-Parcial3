# ADR 0004: Política de calidad y umbrales de CI

## Contexto

El pipeline debe bloquear cambios que degraden correctitud, seguridad,
documentación, rendimiento o memoria. Los umbrales deben ser medibles,
reproducibles y estar versionados con el código para que CI y el entorno local
apliquen exactamente la misma política.

## Decisión

Adoptar estos controles bloqueantes:

| Control | Herramienta | Umbral |
|---|---|---|
| Pruebas | pytest | 0 fallos en Python 3.11, 3.12 y 3.13. |
| Cobertura | pytest-cov | ≥ 80%. |
| Estilo y errores | Ruff | 0 hallazgos; formato verificado. |
| Diseño | Pylint | Score ≥ 8.0. |
| Tipado | mypy | 0 errores en el núcleo. |
| Complejidad | Radon | Sin bloques ≥ C; MI ≥ 20. |
| Seguridad de código | Bandit | 0 HIGH/HIGH. |
| Dependencias | pip-audit | 0 CVE en dependencias de ejecución. |
| Secretos | Gitleaks | 0 hallazgos. |
| Documentación | MkDocs | `--strict` sin warnings. |
| Enlaces | Lychee | 0 enlaces internos rotos. |
| Rendimiento | pytest-benchmark | Regresión ≤ 50% en `main`. |
| Memoria | tracemalloc | ≤ `min(256 MB, 1.5× base)` en `main`. |

Los controles de rendimiento y memoria son informativos en pull requests y
bloqueantes en `main`, `schedule` y ejecución manual, para evitar falsos
negativos por ruido del runner compartido.

## Justificación de los umbrales

- **80% de cobertura**: cubre los caminos principales sin exigir cobertura
  artificial de ramas triviales.
- **Pylint 8.0**: permite estilo consistente sin bloquear por convenciones
  menores; los mensajes desactivados están justificados en `.pylintrc`.
- **Complejidad C**: los bloques A/B son mantenibles; un bloque C requiere
  justificación y el gate actual lo prohíbe.
- **MI ≥ 20**: umbral estándar de Radon para código mantenible.
- **50% de tolerancia**: absorbe variación de hardware sin ocultar regresiones
  grandes.
- **Memoria 1.5×**: permite variación del recolector y del sistema operativo.

## Consecuencias

### Positivas

- La política es explícita y auditable.
- CI y local usan los mismos archivos de configuración.
- Las excepciones se registran en `SECURITY.md`, no se silencian.

### Negativas y mitigaciones

- Los umbrales pueden generar fricción en cambios legítimos: se revisan en un
  ADR y se actualizan junto con la documentación.
- Los benchmarks dependen del hardware: se usan medianas, tolerancia y línea
  base regenerada solo con justificación.
- Un runner más lento puede fallar el gate de rendimiento: el job se ejecuta
  después de las pruebas y se puede relanzar.

## Estado

Aceptada. Los valores concretos están en `pyproject.toml`, `.pylintrc`,
`scripts/check_complexity.py`, `scripts/check_benchmark.py` y
`scripts/check_memory.py`.
