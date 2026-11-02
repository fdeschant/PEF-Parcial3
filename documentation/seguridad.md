# Seguridad

## Modelo de riesgos

| Riesgo | Impacto | Control |
|---|---|---|
| Inyección de comandos por `subprocess` | Alto | Listas de argumentos, sin `shell=True`; Bandit. |
| Dependencia con CVE conocido | Alto | pip-audit + Dependabot. |
| Secreto versionado | Crítico | Gitleaks + rotación. |
| API expuesta sin autenticación | Alto | Escuchar en `127.0.0.1`; proxy con auth si se publica. |
| Consultas gigantes (DoS) | Medio | `max_length=200` en FastAPI. |
| Path traversal | Bajo | Solo se listan archivos `documento_*.txt`; no se aceptan rutas del usuario. |
| Uso de `random` no criptográfico | Bajo | Solo para corpus sintético; documentado como falso positivo. |
| Deserialización insegura | Bajo | No se usa `pickle`, `eval` ni `exec`. |

## Controles implementados

| Control | Herramienta | Comando | Reporte |
|---|---|---|---|
| Código inseguro | Bandit | `bandit -r . -x ... -lll -iii` | `reports/bandit.json` |
| Dependencias | pip-audit | `pip-audit -r requirements.txt` | `reports/pip-audit.json` |
| Dependencias de desarrollo | pip-audit | `pip-audit -r requirements-dev.txt` | `reports/pip-audit-dev.json` |
| Secretos | Gitleaks | `gitleaks git` o `gitleaks dir .` | `reports/gitleaks.sarif` |
| Actualizaciones | Dependabot | `.github/dependabot.yml` | Pull requests |

## Resultados actuales

- **Bandit**: 0 hallazgos HIGH/HIGH. Se revisaron hallazgos LOW de
  `subprocess` (B404/B603) y `random` (B311); ambos están justificados.
- **pip-audit**: 0 vulnerabilidades conocidas en dependencias de ejecución.
- **Gitleaks**: 0 secretos detectados en el árbol de trabajo.

## Política de bloqueo

| Severidad | Acción |
|---|---|
| Crítica | Bloquea el pipeline y requiere rotación/parche inmediato. |
| Alta | Bloquea el pipeline. |
| Media | Revisión obligatoria antes de integrar. |
| Baja | Se registra y se planifica. |
| Secreto | Bloquea siempre. |

La política completa y el registro de excepciones están en `SECURITY.md`, en la
raíz del repositorio.

## Falsos positivos registrados

| ID | Herramienta | Hallazgo | Justificación | Revisión |
|---|---|---|---|---|
| FP-001 | Bandit B311 | `random.Random` en `generator.py` | Corpus sintético reproducible; no se usa para seguridad. | 2026-12-31 |
| FP-002 | Bandit B404/B603 | `subprocess` en `main.py`, `profiler.py`, `run_quality_check.py` | Herramientas conocidas, argumentos en lista, sin `shell=True`. | 2026-12-31 |

## Medidas correctivas

1. Si aparece un CVE, actualizar la dependencia y regenerar `requirements*.txt`.
2. Si no hay corrección, evaluar explotabilidad, aplicar control compensatorio y
   registrar la excepción con fecha de revisión.
3. Si Gitleaks detecta un secreto, rotarlo, eliminarlo del código y evaluar la
   reescritura del historial.
4. Si Bandit detecta un patrón inseguro, corregirlo o justificar la excepción.

## Limitaciones

- Bandit no es un SAST completo ni analiza flujo de datos entre archivos.
- pip-audit depende de bases públicas y de la resolución de dependencias.
- La API no implementa autenticación; es una decisión de alcance documentada.
