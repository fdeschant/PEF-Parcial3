# Rendimiento

## Metodología

- Corpus reproducible de **200 documentos** (`seed=42`).
- `pytest-benchmark` mide la mediana de múltiples rondas.
- Los benchmarks se comparan contra `benchmarks/baseline.json` con tolerancia
  del **50%**.
- La memoria se mide con `tracemalloc` y `resource.getrusage`; se repite tres
  veces y se conserva la mediana.
- El perfilado de CPU se genera con `cProfile` y `pyinstrument`.

Los valores dependen del hardware. Para que la comparación use el mismo entorno
que el job de rendimiento, el workflow manual `.github/workflows/baseline.yml`
regenera la línea base en `ubuntu-latest` con Python 3.13 y abre un PR con las
medianas actualizadas. Mientras ese PR no se mergee, la copia versionada sigue
siendo la referencia local.

## Benchmarks

Medición local (Python 3.11, Linux):

| Operación | Mediana | Observación |
|---|---|---|
| `tokenize` (texto de 100k caracteres) | **1.73 ms** | Dominado por `re.split`. |
| Construcción de índice (200 docs) | **12.29 ms** | Incluye lectura, tokenización e inserción. |
| Búsqueda secuencial | **0.489 ms** | Recorre los 200 documentos. |
| Búsqueda indexada | **1.36 µs** | Intersección de posting lists. |
| Búsqueda cacheada (hit) | **0.339 µs** | Solo normalización y acceso al `OrderedDict`. |
| Lectura por buffer (archivo de 10k palabras) | **25.9 µs** | Bloques de 8 KB. |

La búsqueda indexada es aproximadamente **360×** más rápida que la secuencial
para esta consulta y corpus. La caché reduce el costo a menos de **1 µs**.

## Perfilado de CPU

Salida de `reports/profile.txt` (cProfile, 200 documentos):

```text
42452 function calls in 0.020 seconds

ncalls  tottime  cumtime  filename:lineno(function)
     1    0.000    0.020  inverted_index.py:105(build_index)
   200    0.008    0.010  inverted_index.py:32(add_document)
   200    0.000    0.009  search_common.py:41(read_tokens)
   201    0.000    0.006  search_common.py:14(tokenize)
   201    0.000    0.004  re/__init__.py:198(split)
   201    0.004    0.004  {method 'split' of 're.Pattern' objects}
 25010    0.001    0.001  {method 'get' of 'dict' objects}
 12486    0.001    0.001  {method 'add' of 'set' objects}
```

Hallazgos:

- La tokenización con `re.split` es el costo dominante de la carga.
- `add_document` concentra el tiempo de construcción por el conteo de términos.
- Las operaciones de diccionario y `set` son el segundo costo.
- La búsqueda indexada no aparece entre los hotspots porque su costo es
  despreciable frente a la construcción.

El perfil interactivo de pyinstrument se publica como
`reports/pyinstrument.html`.

## Consumo de memoria

Medición con `tracemalloc`:

| Escenario | Pico | Actual |
|---|---|---|
| Construcción de índice (200 docs) | **3.81 MB** | 3.66 MB |
| Carga secuencial | **2.27 MB** | 2.11 MB |
| Lectura de archivo grande (10k palabras) | **0.13 MB** | 0.00 MB |

El pico de indexación es bajo porque el corpus de prueba es acotado. El umbral
de CI es `min(256 MB, 1.5 × línea base)`; con la línea base local, el límite es
**5.71 MB**. La medición de CI repite cada escenario tres veces y usa la mediana
para reducir el ruido del runner.

Las principales asignaciones corresponden a:

- Listas de tokens por documento.
- Diccionarios de posting lists y frecuencias.
- Conjuntos de IDs de documento.

## Complejidad

| Operación | Complejidad temporal | Complejidad espacial |
|---|---|---|
| Tokenizar | `O(L)` | `O(L)` |
| Cargar corpus | `O(T)` | `O(T)` |
| Construir índice | `O(T)` | `O(T)` |
| Buscar secuencial | `O(D * W)` | `O(D)` |
| Buscar indexado | `O(k * P + C * k + N log K)` | `O(C)` |
| Ranking top-K | `O(N log K)` | `O(K)` |

## Cómo reproducir

```bash
make perf
```

o por separado:

```bash
pytest benchmarks -q --benchmark-json=reports/benchmark.json
python scripts/check_benchmark.py reports/benchmark.json benchmarks/baseline.json
python scripts/measure_memory.py --repeat 3 --output reports/memory.json
python scripts/check_memory.py reports/memory.json benchmarks/memory_baseline.json
python scripts/profile_cpu.py
```

## Interpretación y límites

- Un benchmark más lento no siempre es una regresión: puede deberse a carga del
  equipo. Por eso se usa mediana, tolerancia y comparación contra una línea base.
- La memoria de Python incluye overhead del intérprete; `tracemalloc` mide
  asignaciones de Python, no memoria residente total.
- Los resultados de este documento son una foto del entorno local; CI mantiene
  la comparación automática.
