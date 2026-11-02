# API y contratos

## Ejecución

```bash
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Documentación interactiva generada por FastAPI:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del servicio y documentos indexados. |
| GET | `/search/sequential?q=...` | Búsqueda secuencial. |
| GET | `/search/indexed?q=...` | Búsqueda indexada con caché. |
| GET | `/cache/stats` | Estadísticas de la caché. |

## Modelos

### `SearchResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `doc_id` | `int` | ID del documento. |
| `doc_name` | `str` | Nombre del archivo. |
| `score` | `float` | Score calculado. |
| `snippet` | `str` | Fragmento de contexto. |

### `SearchResult`

| Campo | Tipo | Descripción |
|---|---|---|
| `query` | `str` | Consulta original. |
| `engine` | `str` | `sequential` o `indexed`. |
| `elapsed_seconds` | `float` | Tiempo de la búsqueda. |
| `results` | `list[SearchResponse]` | Resultados ordenados. |

## Ejemplos

### Salud

```bash
curl -s http://127.0.0.1:8000/health
```

```json
{
  "status": "ok",
  "indexed_docs": 200
}
```

### Búsqueda secuencial

```bash
curl -s "http://127.0.0.1:8000/search/sequential?q=python%20java"
```

```json
{
  "query": "python java",
  "engine": "sequential",
  "elapsed_seconds": 0.0123,
  "results": [
    {
      "doc_id": 17,
      "doc_name": "documento_17.txt",
      "score": 0.081,
      "snippet": "python java algoritmo ..."
    }
  ]
}
```

### Búsqueda indexada

```bash
curl -s "http://127.0.0.1:8000/search/indexed?q=python%20java"
```

La primera llamada es un *miss*; la segunda, con la misma consulta, es un *hit*.

### Estadísticas de caché

```bash
curl -s http://127.0.0.1:8000/cache/stats
```

```json
{
  "hits": 1,
  "misses": 1,
  "hit_rate": 0.5,
  "size": 1
}
```

## Errores y excepciones

| Situación | Código | Respuesta |
|---|---|---|
| `q` vacío | 422 | Error de validación de FastAPI. |
| `q` con más de 200 caracteres | 422 | Error de validación de FastAPI. |
| Consulta sin resultados | 200 | `results: []`. |
| Corpus vacío | 200 | `results: []`; `/health` informa `indexed_docs: 0`. |
| Error interno | 500 | FastAPI devuelve el detalle del error. |

## Contrato de comportamiento

1. Los términos de la consulta se normalizan a minúsculas.
2. Se exige que **todos** los términos estén presentes en el documento.
3. El score secuencial es `ocurrencias / longitud`.
4. El score indexado suma `tf / longitud` por término.
5. Los resultados se ordenan por score descendente.
6. El parámetro `q` es obligatorio, no vacío y de hasta 200 caracteres.

## Seguridad

La API no implementa autenticación. Para uso local, escuchar en `127.0.0.1`.
Para exponerla, colocar un proxy con autenticación y limitar la tasa de
peticiones. Ver [Seguridad](seguridad.md).
