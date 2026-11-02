# Arquitectura

## Vista general

El proyecto es una aplicación Python de módulos planos. El núcleo de búsqueda no
depende de la API ni del menú; ambos son adaptadores de entrada.

```mermaid
flowchart LR
    CLI[main.py<br/>menú Rich] --> GEN[generator.py]
    CLI --> SEQ[search_sequential.py]
    CLI --> IDX[inverted_index.py]
    CLI --> CACHE[cache.py]
    CLI --> CONC[concurrency.py]
    CLI --> LARGE[large_file_handler.py]
    CLI --> PERF[profiler.py / complexity.py]
    CLI --> DOCS[option_docs<br/>MkDocs]

    API[api.py<br/>FastAPI] --> SEQ
    API --> IDX
    API --> CACHE

    SEQ --> COMMON[search_common.py]
    IDX --> COMMON
    IDX --> RANK[ranking.py]
    CONC --> IDX
    LARGE --> IDX
    LARGE --> COMMON
    GEN --> CONFIG[config.py]
    SEQ --> CONFIG
    IDX --> CONFIG
    CACHE --> CONFIG
```

## Módulos y responsabilidades

| Módulo | Responsabilidad | Depende de |
|---|---|---|
| `config.py` | Constantes: rutas, tamaños, vocabulario, workers. | — |
| `search_common.py` | Tokenización, snippets, IDs, lectura y listado de documentos. | `config` |
| `search_sequential.py` | Motor que recorre y puntúa todos los documentos. | `search_common`, `config` |
| `inverted_index.py` | Índice invertido, posting lists, frecuencias y motor indexado. | `search_common`, `ranking`, `config` |
| `ranking.py` | Selección top-K con heap de mínimo. | `search_common` |
| `cache.py` | Caché LRU de resultados con normalización de consultas. | `config`, `search_common` |
| `concurrency.py` | Búsqueda concurrente y construcción paralela del índice. | `inverted_index`, `search_common` |
| `generator.py` | Corpus sintético reproducible (semilla opcional). | `config` |
| `large_file_handler.py` | Lectura por buffer, batching y pool de procesos. | `inverted_index`, `search_common` |
| `api.py` | Adaptador HTTP con FastAPI. | núcleo |
| `main.py` | Menú interactivo y orquestación. | todos los anteriores |
| `profiler.py`, `complexity.py`, `reporter.py` | Medición y reportes de apoyo. | núcleo |

## Reglas de dependencia

1. `config.py` y `search_common.py` son la base; no importan módulos de negocio.
2. El núcleo (`search_*`, `inverted_index`, `cache`, `ranking`, `concurrency`,
   `large_file_handler`) no importa `api.py` ni `main.py`.
3. `api.py` es un adaptador reemplazable: no contiene lógica de búsqueda.
4. `main.py` orquesta; no implementa algoritmos.
5. Los scripts de CI y benchmarks usan el núcleo, pero no son importados por él.

Estas reglas permiten probar el núcleo sin levantar la API ni el menú.

## Flujo de una búsqueda indexada

```mermaid
sequenceDiagram
    participant U as Usuario
    participant C as QueryCache
    participant E as InvertedIndexEngine
    participant I as InvertedIndex
    participant R as ResultRanker

    U->>C: get(query)
    alt hit
        C-->>U: resultados cacheados
    else miss
        C-->>E: continuar
        E->>E: tokenize(query)
        E->>I: posting lists por término
        I-->>E: intersección de doc_ids
        E->>I: frecuencias y longitudes
        E->>R: rank(resultados, top_k)
        R-->>E: top-K ordenado
        E-->>C: put(query, resultados)
        C-->>U: resultados
    end
```

## Construcción del índice

```mermaid
flowchart TD
    A[list_doc_files] --> B[leer y tokenizar]
    B --> C[add_document]
    C --> D[posting lists]
    C --> E[frecuencias]
    C --> F[longitudes]
    D --> G[InvertedIndex]
    E --> G
    F --> G
```

## Decisiones arquitectónicas

- [ADR 0001: API FastAPI aislada](adr/0001-fastapi-isolation-strategy.md)
- [ADR 0002: arquitectura para archivos grandes](adr/0002-large-file-architecture.md)
- [ADR 0003: MkDocs Material como documentación externa](adr/0003-mkdocs-documentation.md)
- [ADR 0004: política de calidad y umbrales de CI](adr/0004-ci-quality-gates.md)

## Despliegue local

```mermaid
flowchart LR
    DEV[Desarrollador] --> GIT[Repositorio Git]
    GIT --> CI[GitHub Actions]
    CI --> ART[Reportes y artefactos]
    CI --> PAGES[GitHub Pages]
    PAGES --> DOC[Sitio de documentación]
```

El pipeline no despliega la aplicación; solo valida, mide y publica
documentación. La API se ejecuta localmente con Uvicorn.
