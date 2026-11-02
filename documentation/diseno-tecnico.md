# Diseño técnico

## Estructuras de datos

### Índice invertido

`InvertedIndex` mantiene cuatro estructuras principales:

| Estructura | Tipo | Uso |
|---|---|---|
| `index` | `dict[str, set[int]]` | Posting list: término → documentos. |
| `term_freqs` | `dict[str, dict[int, int]]` | Frecuencia de cada término por documento. |
| `doc_lengths` | `dict[int, int]` | Longitud del documento en tokens. |
| `doc_names` | `dict[int, str]` | ID → nombre de archivo. |
| `_doc_tokens` | `dict[int, list[str]]` | Tokens para construir snippets. |

La intersección de posting lists usa `set`, lo que permite descartar candidatos
en tiempo proporcional al tamaño de la lista más chica.

### Caché LRU

`QueryCache` usa `OrderedDict`:

- La clave es la consulta normalizada: minúsculas y términos ordenados.
- `get()` mueve la entrada al final (más recientemente usada).
- `put()` inserta o actualiza y desaloja la primera entrada si supera `max_size`.

Esto hace que `"java python"` y `"Python Java"` compartan entrada.

### Ranking top-K

`ResultRanker` usa dos estrategias:

- Si `N <= K`: ordenamiento completo, `O(N log N)`.
- Si `N > K`: min-heap de tamaño `K`, `O(N log K)` y `O(K)` memoria.

El heap guarda `(score, id(resultado), resultado)` para desempatar de forma
estable cuando dos documentos tienen el mismo score.

## Algoritmos

### Tokenización

```python
[t for t in re.split(r"\W+", text.lower()) if t]
```

- Convierte a minúsculas.
- Separa por cualquier carácter no alfanumérico.
- Descarta tokens vacíos.

Complejidad: `O(L)` por texto de longitud `L`.

### Búsqueda secuencial

1. Tokeniza la consulta.
2. Para cada documento, verifica que todos los términos estén presentes.
3. Cuenta ocurrencias y calcula `score = ocurrencias / longitud`.
4. Construye snippet y aplica top-K.

Complejidad por consulta: `O(D * W)` donde `D` es la cantidad de documentos y
`W` el promedio de tokens por documento. Memoria: `O(T)` por el corpus cargado.

### Búsqueda indexada

1. Tokeniza la consulta.
2. Obtiene la posting list de cada término.
3. Interseca los conjuntos de candidatos.
4. Calcula score sumando `tf / doc_length` por término.
5. Construye snippet y aplica top-K.

Complejidad por consulta: `O(k * P + C * k + N log K)`, con `k` términos, `P`
tamaño de posting list y `C` candidatos. En la práctica `C` suele ser mucho menor
que `D`.

### Construcción del índice

`add_document()` recorre los tokens una vez, cuenta frecuencias y actualiza las
posting lists. Complejidad: `O(W)` por documento, `O(T)` para todo el corpus.

### Procesamiento concurrente

- `ParallelIndexBuilder` divide archivos en chunks, construye índices parciales
  con `multiprocessing.Pool` y los fusiona con `merge()`.
- `ConcurrentSearcher` reparte consultas independientes entre procesos.
- `ConcurrentSearcherThreaded` usa hilos; se incluye para comparar el efecto del
  GIL en cargas CPU-bound.

### Lectura de archivos grandes

- `read_file_buffered()` lee bloques de 8 KB en lugar de cargar todo el archivo.
- `build_index_large_files()` agrupa documentos en batches y usa un pool de
  procesos.
- `merge()` combina índices parciales sin reconstruir el índice completo.

## Complejidad resumida

| Operación | Tiempo | Espacio |
|---|---|---|
| Tokenizar un texto | `O(L)` | `O(L)` |
| Cargar corpus secuencial | `O(T)` | `O(T)` |
| Construir índice | `O(T)` | `O(T)` |
| Buscar secuencial | `O(D * W)` | `O(D)` resultados |
| Buscar indexado | `O(k * P + C * k + N log K)` | `O(C)` |
| Ranking top-K | `O(N log K)` | `O(K)` |
| Cache hit | `O(k log k)` por normalizar | `O(1)` adicional |
| Leer archivo por buffer | `O(B)` por bloque | `O(B)` |

## Decisiones de implementación

| Decisión | Motivo |
|---|---|
| Índice en memoria | El corpus es acotado y se busca latencia mínima. |
| `set` para posting lists | Intersección rápida y sin duplicados. |
| Heap para top-K | Evita ordenar todos los resultados cuando `N` es grande. |
| Caché con clave normalizada | Aumenta hits sin cambiar la semántica de la consulta. |
| `multiprocessing` para indexar | El trabajo es CPU-bound; los procesos evitan el GIL. |
| Buffering de 8 KB | Reduce picos de memoria en archivos grandes. |
| Semilla en el generador | Corpus reproducible para benchmarks y CI. |
| API aislada | Permite eliminar el adaptador HTTP sin tocar el núcleo. |

## Manejo de errores y contratos

- `parse_doc_id()` lanza `ValueError` si el nombre no termina en un ID numérico.
- `list_doc_files()` devuelve `[]` si el directorio no existe.
- La API valida `q` con `min_length=1` y `max_length=200`; fuera de rango
  devuelve HTTP 422.
- Una búsqueda sin resultados devuelve HTTP 200 con `results: []`.
- El índice vacío no es un error: la API responde con listas vacías.

## Deuda técnica conocida

- El índice no se persiste; se reconstruye al iniciar.
- No hay stemming ni sinónimos.
- La API no tiene autenticación; debe ejecutarse en localhost o detrás de un
  proxy autenticado.
- Los benchmarks dependen del hardware; se comparan con tolerancia.
