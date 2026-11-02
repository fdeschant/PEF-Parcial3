# Glosario

Vocabulario del dominio del buscador. Se usa de forma consistente en el código,
la documentación y los reportes.

## Términos

**Documento**
Archivo de texto con tokens delimitados por espacios. Es la unidad mínima de
indexación y búsqueda.
*Evitar*: archivo, doc.

**Token**
Unidad léxica producida por la tokenización: minúsculas y separación por
caracteres no alfanuméricos.
*Evitar*: palabra, término crudo.

**Posting list**
Conjunto de IDs de documentos en los que aparece un término. Es la estructura
central del índice invertido.
*Evitar*: lista de documentos, ocurrencias.

**Consulta (query)**
Conjunto de términos ingresados por el usuario. Se normaliza a minúsculas y
orden canónico para aprovechar la caché.
*Evitar*: búsqueda, términos de búsqueda.

**Snippet**
Fragmento de contexto extraído de un documento que muestra dónde aparece un
término de la consulta.
*Evitar*: vista previa, extracto.

**Indexación**
Proceso de construcción del índice invertido. Lee cada documento una vez y
construye posting lists y frecuencias.
*Evitar*: indexado, build.

**Candidato**
Documento cuyo ID aparece en la intersección de las posting lists de todos los
términos de la consulta.
*Evitar*: coincidencia, hit.

**Batch**
Grupo de documentos procesados juntos en memoria antes de agregarlos al índice.
Reduce el overhead de I/O y de creación de procesos.
*Evitar*: chunk, grupo.

**Buffer**
Lectura parcial de un archivo grande en bloques, en lugar de cargar el archivo
completo de una vez.
*Evitar*: chunk, zona de buffer.

**Indexación paralela**
Construcción del índice dividiendo los documentos entre varios procesos y
fusionando luego los índices parciales.
*Evitar*: build paralelo, índice multiproceso.

**Top-K**
Los K resultados con mayor score, seleccionados con un heap de mínimo de tamaño
K.
*Evitar*: mejores resultados, resultados rankeados.

**Score**
Puntuación de relevancia de un documento para una consulta. En el motor
secuencial es `ocurrencias / longitud`; en el indexado es la suma de
`tf / longitud` por término.

**Hit / Miss**
Un *hit* es una consulta resuelta por la caché; un *miss* obliga a ejecutar el
motor y luego almacenar el resultado.

**LRU**
*Least Recently Used*: política que desaloja la entrada usada hace más tiempo.

**Línea base (baseline)**
Valores de referencia de rendimiento y memoria versionados en `benchmarks/`.
Se usan para detectar regresiones.

**Gate**
Control bloqueante del pipeline. Si no se cumple el umbral, el cambio no se
integra.

**ADR**
*Architecture Decision Record*: registro breve de una decisión de arquitectura,
su contexto y sus consecuencias.

**Corpus**
Conjunto de documentos usado para indexar, buscar y medir. En este proyecto es
sintético y reproducible mediante una semilla.
