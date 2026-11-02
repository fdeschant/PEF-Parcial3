# Glossary — Buscador Eficiente de Información

Sistema de recuperación de información que implementa búsquedas secuenciales e indexadas, con técnicas de optimización de memoria, tiempo y legibilidad.

## Language

**Documento**:
Un archivo de texto que contiene tokens delimitados por espacios. Unidad mínima de indexación y búsqueda.
_Avoid_: file, doc

**Posting List**:
Conjunto de IDs de documentos en los que aparece un término específico. Estructura central del índice invertido.
_Avoid_: document list, occurrences

**Query**:
Conjunto de términos de búsqueda ingresados por el usuario. Se normaliza (minúsculas, orden canónico) para optimizar la caché.
_Avoid_: search, search terms

**Snippet**:
Fragmento de contexto extraído de un documento que muestra dónde aparece un término de la consulta.
_Avoid_: preview, excerpt

**Index**:
Proceso de construcción del índice invertido a partir de los documentos. Lee cada documento una vez y construye posting lists.
_Avoid_: indexing, build

**Candidate**:
Documento cuyo ID aparece en la intersección de posting lists de todos los términos de la consulta.
_Avoid_: match, hit

**Batch**:
Grupo de documentos procesados juntos en memoria antes de agregar al índice. Reduce overhead de I/O y procesamiento.
_Avoid_: chunk, group

**Buffer**:
Lectura parcial de un archivo grande en memoria, en lugar de cargar el archivo completo de una vez.
_Avoid_: chunk, buffer zone

**Parallel Indexing**:
Construcción del índice invertido dividiendo los documentos entre múltiples procesos, y luego fusionando los índices parciales.
_Await_: parallel build, multiprocess index

**Top-K**:
Los K resultados con mayor score, seleccionados mediante un heap de mínimo de tamaño K.
_Avoid_: best results, ranked results
