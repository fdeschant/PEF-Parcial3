# Large File Architecture

Se agrega un modo `--large` al generador que produce archivos de 10,000+ palabras, y un módulo `large_file_handler.py` con lectura por buffer (bloques de 8KB), procesamiento en batches de N documentos, y construcción del índice en paralelo con `multiprocessing.Pool`.

**Por qué**: el corpus original (500 archivos de 50-200 palabras) es demasiado pequeño para demostrar batching, buffering y procesamiento en paralelo. Sin archivos grandes, estas técnicas serían teoría sin evidencia medible.
