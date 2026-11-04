# Buscador Eficiente de Información

Sistema de recuperación de información que compara una búsqueda secuencial con
un índice invertido, caché LRU, ranking por heap, procesamiento concurrente y
lectura eficiente de archivos grandes.

Este sitio reúne la documentación **funcional, técnica y operativa** del
proyecto. Está versionada junto con el código y se publica automáticamente desde
la rama `main`.

## Inicio rápido

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt -r requirements-docs.txt

python scripts/generate_corpus.py --docs 200 --seed 42
python main.py                 # menú interactivo
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

## Mapa de la documentación

| Necesidad | Página |
|---|---|
| Entender qué problema resuelve y su alcance | [Descripción funcional](descripcion-funcional.md) |
| Ver módulos, responsabilidades y dependencias | [Arquitectura](arquitectura.md) |
| Instalar, configurar y ejecutar | [Instalación y ejecución](instalacion.md) |
| Entender estructuras de datos y algoritmos | [Diseño técnico](diseno-tecnico.md) |
| Usar la API REST | [API y contratos](api.md) |
| Consultar firmas y docstrings | [Referencia de API](referencia-api.md) |
| Conocer la estrategia y los resultados de pruebas | [Pruebas](pruebas.md) |
| Ver benchmarks, profiling y memoria | [Rendimiento](rendimiento.md) |
| Revisar riesgos y política de seguridad | [Seguridad](seguridad.md) |
| Entender el pipeline y reproducirlo localmente | [Integración continua](ci.md) |
| Contribuir, actualizar líneas base y resolver fallos | [Mantenimiento](mantenimiento.md) |
| Vocabulario del dominio | [Glosario](glosario.md) |

## Documentación como parte del repositorio

La documentación se mantiene actualizada con el mismo flujo que el código:

1. Todo cambio de comportamiento, interfaz o umbral se documenta en el mismo
   pull request.
2. CI construye el sitio con `mkdocs build --strict` y valida los enlaces
   internos con Lychee.
3. La rama `main` publica el sitio en GitHub Pages.

### Control de acceso y colaboración

El repositorio puede ser **público** (necesario para GitHub Pages en el plan
free) o privado con un plan pago. La visibilidad no otorga permisos de escritura:
solo los colaboradores con `Write` pueden pushear y mergear; los forks pueden
abrir pull requests, pero no mergear. No publiques secretos ni datos personales;
la documentación y el código quedan visibles. Para publicarla:

1. Crear el repositorio en GitHub e invitar al equipo.
2. En **Settings → Pages**, elegir **GitHub Actions** como fuente.
3. En **Settings → Branches**, proteger `main` y exigir los checks de CI.
4. Hacer push a `main`; el workflow `pages.yml` publica el sitio.

## Estado actual

- Pruebas: **60 pasan**.
- Cobertura: **95.17%** sobre los módulos medidos.
- Pylint: **10.00/10** en los módulos del núcleo.
- Complejidad: todos los bloques en rango **A/B**; mantenibilidad **≥ 20**.
- Documentación: construcción estricta y enlaces internos validados.
- Rendimiento y memoria: líneas base versionadas; el workflow manual
  `baseline.yml` las regenera en `ubuntu-latest` con Python 3.13.
- CI remoto: repositorio público y sitio publicado en GitHub Pages.
