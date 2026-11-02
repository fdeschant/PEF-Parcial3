# Descripción funcional

## Problema que resuelve

Un buscador necesita encontrar documentos relevantes dentro de un corpus de texto
sin recorrer todo el contenido en cada consulta. La solución implementa dos
motores comparables:

- **Búsqueda secuencial**: lee y tokeniza cada documento en cada consulta.
- **Búsqueda indexada**: construye un índice invertido una vez y responde
  consultas consultando posting lists.

El sistema también incorpora caché LRU, ranking top-K, procesamiento concurrente
y lectura por buffer para archivos grandes. El objetivo es medir y comparar el
costo de cada técnica, no solo obtener el resultado correcto.

## Alcance

### Incluido

- Generación de corpus sintético reproducible.
- Indexación y búsqueda secuencial e indexada.
- Normalización de consultas y caché LRU.
- Ranking de resultados por score con heap de tamaño K.
- Procesamiento por lotes y en paralelo.
- Lectura de archivos grandes por buffer.
- API REST con FastAPI.
- Benchmarks, profiling, medición de memoria y controles de CI.
- Documentación funcional, técnica y operativa.

### Fuera de alcance

- Autenticación y autorización de usuarios finales.
- Persistencia del índice en disco.
- Búsqueda difusa, stemming o corrección ortográfica.
- Despliegue en producción con alta disponibilidad.
- Interfaz gráfica web completa (la API expone Swagger UI).

## Usuarios y casos de uso

| Actor | Caso de uso |
|---|---|
| Estudiante / evaluador | Ejecutar el menú, comparar motores y revisar reportes. |
| Desarrollador | Consumir la API o reutilizar los módulos de búsqueda. |
| Integrante del equipo | Ejecutar CI localmente y actualizar líneas base. |
| Docente | Verificar que los controles de calidad y eficiencia se ejecutan. |

### Casos de uso principales

1. **Generar corpus**: crear documentos pequeños y grandes con una semilla fija.
2. **Buscar secuencialmente**: obtener resultados y tiempos sin índice.
3. **Buscar con índice**: construir el índice y comparar tiempos.
4. **Usar caché**: repetir consultas y observar hits/misses.
5. **Indexar archivos grandes**: demostrar buffering, batching y paralelismo.
6. **Medir rendimiento**: ejecutar benchmarks, profiling y memoria.
7. **Consultar la API**: buscar por HTTP y revisar contratos.
8. **Ejecutar controles**: reproducir el pipeline de CI en local.

## Requisitos funcionales

| ID | Requisito | Verificación |
|---|---|---|
| RF-01 | Generar documentos sintéticos con temáticas y longitudes configurables. | `tests/test_generator.py` |
| RF-02 | Cargar documentos y tokenizarlos de forma consistente. | `tests/test_search_common.py` |
| RF-03 | Buscar secuencialmente y devolver resultados ordenados. | `tests/test_search_sequential.py` |
| RF-04 | Construir un índice invertido y buscar por intersección de posting lists. | `tests/test_inverted_index.py` |
| RF-05 | Cachear consultas normalizadas con política LRU. | `tests/test_cache.py` |
| RF-06 | Ranking top-K por score. | `tests/test_ranking.py` |
| RF-07 | Procesar documentos en batches y en paralelo. | `tests/test_concurrency.py` |
| RF-08 | Leer archivos grandes por buffer. | `tests/test_large_file_handler.py` |
| RF-09 | Exponer búsqueda y estadísticas por API REST. | `tests/test_api.py` |
| RF-10 | Ejecutar un menú interactivo con todas las opciones. | `scripts/check_menu.py` |

## Requisitos no funcionales

| ID | Requisito | Criterio |
|---|---|---|
| RNF-01 | Correctitud | 0 pruebas fallidas en Python 3.11, 3.12 y 3.13. |
| RNF-02 | Cobertura | ≥ 80% en módulos del núcleo. |
| RNF-03 | Calidad estática | Ruff sin hallazgos; Pylint ≥ 8.0. |
| RNF-04 | Tipado | mypy sin errores en módulos del núcleo. |
| RNF-05 | Complejidad | Sin bloques ≥ C; mantenibilidad ≥ 20. |
| RNF-06 | Seguridad | Sin hallazgos Bandit HIGH/HIGH; sin secretos; dependencias auditadas. |
| RNF-07 | Rendimiento | Sin regresión > 50% contra la línea base en `main`. |
| RNF-08 | Memoria | Pico de indexación ≤ 1.5× la línea base y ≤ 256 MB. |
| RNF-09 | Documentación | `mkdocs build --strict` y enlaces internos válidos. |
| RNF-10 | Reproducibilidad | Dependencias fijadas y comandos locales equivalentes a CI. |

## Restricciones y supuestos

- El corpus se genera localmente; no se versiona para mantener el repositorio
  liviano.
- Los benchmarks y la memoria dependen del hardware; por eso se comparan contra
  una línea base con tolerancia.
- La API se ejecuta en `127.0.0.1`; no se expone públicamente sin autenticación.
- La documentación y el código se versionan juntos en Git.
