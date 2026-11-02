# Política de seguridad

## Alcance

Este documento define cómo se analiza la seguridad del Buscador Eficiente de
Información y qué condiciones bloquean la integración en la rama principal.

## Controles automáticos

| Control | Herramienta | Comando | Reporte |
|---|---|---|---|
| Código inseguro | Bandit | `bandit -r . -x ./.venv,./tests,./docs,./documentation,./reports,./benchmarks,./scripts -lll -iii` | `reports/bandit.json` |
| Dependencias | pip-audit | `pip-audit -r requirements.txt` | `reports/pip-audit.json` |
| Secretos | Gitleaks | `gitleaks git --report-format sarif --report-path reports/gitleaks.sarif` | `reports/gitleaks.sarif` |
| Dependencias desactualizadas | Dependabot | Configuración en `.github/dependabot.yml` | PR automáticos |

## Política de bloqueo por severidad

| Hallazgo | Severidad | Acción |
|---|---|---|
| Bandit HIGH + confianza HIGH | Alta | Bloquea el pipeline |
| Bandit MEDIUM | Media | Revisión obligatoria antes de integrar |
| Bandit LOW | Baja | Se registra y se revisa en el backlog |
| CVE en dependencia de ejecución | Alta/Crítica | Bloquea el pipeline |
| CVE en dependencia de desarrollo | Informativa | Se revisa, no bloquea automáticamente |
| Secreto detectado | Crítica | Bloquea siempre; rotar el secreto y revisar el historial |

## Falsos positivos y excepciones

Toda excepción debe registrarse aquí con justificación, responsable y fecha de
revisión. No se aceptan supresiones sin documentación.

| ID | Herramienta | Hallazgo | Justificación | Responsable | Revisión |
|---|---|---|---|---|---|
| FP-001 | Bandit B311 | `random.Random` en `generator.py` | Se usa para generar un corpus sintético reproducible; no interviene en decisiones de seguridad ni criptografía. | Equipo | 2026-12-31 |
| FP-002 | Bandit B404/B603 | `subprocess` en `main.py`, `profiler.py` y `run_quality_check.py` | Se ejecutan herramientas conocidas con listas de argumentos, sin `shell=True` ni entrada de usuario. | Equipo | 2026-12-31 |

Para ignorar una vulnerabilidad puntual de dependencias se debe usar
`pip-audit --ignore-vuln <ID>` y agregar la fila correspondiente en esta tabla.

## Reporte de vulnerabilidades

Si encontrás una vulnerabilidad, no abras un issue público. Enviá el detalle al
responsable del repositorio y permití un plazo razonable para corregirla antes
de divulgarla.

## Limitaciones

- La API no implementa autenticación; debe ejecutarse en `127.0.0.1` o detrás de
  un proxy con autenticación.
- Bandit no reemplaza un SAST completo ni un análisis de flujo de datos.
- pip-audit depende de las bases públicas de vulnerabilidades.
- Gitleaks detecta secretos, pero no puede determinar si ya fueron rotados.
