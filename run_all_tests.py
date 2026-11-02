"""Ejecuta todas las funciones del proyecto con output detallado y mediciones.

Uso:
    python run_all_tests.py
"""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache import QueryCache
from complexity import COMPLEXITY_ANALYSIS
from concurrency import ConcurrentSearcher, ConcurrentSearcherThreaded, ParallelIndexBuilder
from config import DOCS_DIR
from generator import generate_documents, generate_large_documents
from inverted_index import InvertedIndexEngine
from large_file_handler import (
    BATCH_SIZE,
    BUFFER_SIZE,
    build_index_large_files,
    get_total_tokens_large_files,
    read_file_buffered,
    tokens_from_large_file,
)
from ranking import ResultRanker
from search_common import (
    SearchResult,
    build_snippet,
    list_doc_files,
    parse_doc_id,
    tokenize,
)
from search_sequential import SequentialSearchEngine

PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = ""):
    global PASSED, FAILED
    status = "PASS" if condition else "FAIL"
    if condition:
        PASSED += 1
    else:
        FAILED += 1
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def section(title: str):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def subsection(title: str):
    print(f"\n  --- {title} ---")


def measure_time(label: str, func, *args, **kwargs):
    t0 = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    print(f"    {label}: {elapsed:.4f}s")
    return result, elapsed


def test_search_common():
    section("search_common.py — Utilidades compartidas")

    subsection("tokenize()")
    result = tokenize("Hello, World! This is a TEST.")
    print(f"    tokenize('Hello, World! This is a TEST.') = {result}")
    check("tokenize básico", result == ["hello", "world", "this", "is", "a", "test"])

    result = tokenize("")
    print(f"    tokenize('') = {result}")
    check("tokenize vacío", result == [])

    subsection("parse_doc_id()")
    for fname in ["documento_1.txt", "documento_500.txt", "documento_large_10001.txt"]:
        doc_id = parse_doc_id(fname)
        print(f"    parse_doc_id('{fname}') = {doc_id}")
    check("parse_doc_id normal", parse_doc_id("documento_1.txt") == 1)
    check("parse_doc_id grande", parse_doc_id("documento_large_10001.txt") == 10001)

    subsection("build_snippet()")
    tokens = ["el", "python", "es", "eficiente"]
    snippet = build_snippet(tokens, ["python"])
    print(f"    build_snippet({tokens}, ['python']) = '{snippet}'")
    check("build_snippet", "python" in snippet)


def test_generator():
    section("generator.py — Generación de documentos")

    with tempfile.TemporaryDirectory() as tmpdir:
        subsection("generate_documents() — documentos pequeños")
        count, _elapsed = measure_time(
            "generate_documents(5, min_words=10, max_words=20)",
            generate_documents,
            5,
            tmpdir,
            10,
            20,
        )
        files = list_doc_files(tmpdir)
        print(f"    Documentos creados: {len(files)}")
        for f in files:
            filepath = os.path.join(tmpdir, f)
            size = os.path.getsize(filepath)
            print(f"      {f}: {size} bytes")
        check("generate_documents", count == 5 and len(files) == 5)

        subsection("generate_large_documents() — documentos grandes")
        count, _elapsed = measure_time(
            "generate_large_documents(3, words_per_doc=500)",
            generate_large_documents,
            3,
            tmpdir,
            500,
        )
        large_files = [f for f in files if f.startswith("documento_large_")]
        print(f"    Documentos grandes creados: {len(large_files)}")
        for f in large_files:
            filepath = os.path.join(tmpdir, f)
            size = os.path.getsize(filepath)
            print(f"      {f}: {size} bytes")
        check("generate_large_documents", count == 3)


def test_sequential_search(docs_dir: str):
    section("search_sequential.py — Búsqueda secuencial")

    engine = SequentialSearchEngine(docs_dir)

    subsection("load_documents()")
    count, _elapsed = measure_time("load_documents()", engine.load_documents)
    print(f"    Documentos cargados: {count}")
    check("load_documents", count > 0, f"count={count}")
    check("get_doc_count", engine.get_doc_count() == count)

    subsection("search()")
    for query in ["python", "python java", "nonexistentterm", ""]:
        print(f"    Ingresando consulta: '{query}'")
        results, _elapsed = measure_time(f"search('{query}')", engine.search, query)
        print(f"    Resultados: {len(results)}")
        if results:
            print(
                f"    Top resultado: doc_id={results[0].doc_id}, "
                f"doc_name={results[0].doc_name}, score={results[0].score:.4f}"
            )
            print(f"    Snippet: '{results[0].snippet[:60]}...'")
        if query == "python":
            check("search python", len(results) > 0)
        elif query == "nonexistentterm":
            check("search sin resultados", len(results) == 0)
        elif query == "":
            check("search vacía", len(results) == 0)

    subsection("search() con top_k")
    results, _elapsed = measure_time("search('python', top_k=1)", engine.search, "python", 1)
    print(f"    Resultados con top_k=1: {len(results)}")
    check("top_k=1", len(results) <= 1)


def test_inverted_index(docs_dir: str):
    section("inverted_index.py — Índice invertido")

    engine = InvertedIndexEngine(docs_dir)

    subsection("build_index()")
    count, _elapsed = measure_time("build_index()", engine.build_index)
    print(f"    Documentos indexados: {count}")
    print(f"    Términos únicos: {len(engine.index.index)}")
    check("build_index", count > 0, f"count={count}")
    check("get_all_doc_ids", len(engine.index.get_all_doc_ids()) == count)

    subsection("get_posting_list()")
    posting = engine.index.get_posting_list("python")
    print(f"    get_posting_list('python') = {len(posting)} documentos")
    check("get_posting_list", isinstance(posting, set))

    subsection("get_doc_length() / get_doc_tokens()")
    sample_id = next(iter(engine.index.get_all_doc_ids()))
    doc_len = engine.index.get_doc_length(sample_id)
    doc_tokens = engine.index.get_doc_tokens(sample_id)
    print(f"    Doc {sample_id}: longitud={doc_len}, tokens={len(doc_tokens)}")
    check("get_doc_length", doc_len > 0)
    check("get_doc_tokens", isinstance(doc_tokens, list) and len(doc_tokens) > 0)

    subsection("search()")
    for query in ["python", "python java", "nonexistentterm", ""]:
        print(f"    Ingresando consulta: '{query}'")
        results, _elapsed = measure_time(f"search('{query}')", engine.search, query)
        print(f"    Resultados: {len(results)}")
        if results:
            print(f"    Top resultado: doc_id={results[0].doc_id}, score={results[0].score:.4f}")
        if query == "python":
            check("search python", len(results) > 0)
        elif query == "nonexistentterm":
            check("search sin resultados", len(results) == 0)
        elif query == "":
            check("search vacía", len(results) == 0)

    subsection("build_partial_index()")
    partial = engine.build_partial_index(list_doc_files(docs_dir)[:1])
    print(f"    Documentos en índice parcial: {len(partial.get_all_doc_ids())}")
    check("build_partial_index", len(partial.get_all_doc_ids()) == 1)

    subsection("merge()")
    other = InvertedIndexEngine(docs_dir)
    other.build_index()
    pre_merge = len(engine.index.get_all_doc_ids())
    engine.index.merge(other.index)
    post_merge = len(engine.index.get_all_doc_ids())
    print(f"    Antes: {pre_merge} documentos, Después: {post_merge} documentos")
    check("merge", post_merge == pre_merge)


def test_cache():
    section("cache.py — Caché LRU")

    cache = QueryCache()
    print(f"    Tamaño máximo: {cache.max_size}")

    subsection("get() miss")
    result = cache.get("python")
    print(f"    get('python') = {result}")
    print(f"    hits={cache.hits}, misses={cache.misses}")
    check("get miss", result is None and cache.misses == 1)

    subsection("put() y get() hit")
    fake_results = [SearchResult(1, "doc_1.txt", 0.5, "snippet")]
    cache.put("python java", fake_results)
    result = cache.get("python java")
    print("    put('python java', resultados)")
    print(f"    get('python java') = {result}")
    print(f"    hits={cache.hits}, misses={cache.misses}")
    check("put y get", result == fake_results and cache.hits == 1)

    subsection("Normalización")
    result1 = cache.get("java python")
    result2 = cache.get("Python Java")
    print(f"    get('java python') = {result1}")
    print(f"    get('Python Java') = {result2}")
    print(f"    hits={cache.hits}, misses={cache.misses}")
    check("normalización orden", result1 == fake_results)
    check("normalización case", result2 == fake_results)

    subsection("LRU eviction")
    cache.max_size = 2
    cache.put("a", [1])
    cache.put("b", [2])
    cache.get("a")
    cache.put("c", [3])
    result_b = cache.get("b")
    result_a = cache.get("a")
    print(f"    Después de eviction: get('b')={result_b}, get('a')={result_a}")
    print(f"    hits={cache.hits}, misses={cache.misses}")
    check("LRU eviction", result_b is None and result_a is not None)

    subsection("hit_rate()")
    rate = cache.hit_rate()
    print(f"    hit_rate() = {rate:.2%}")
    check("hit_rate", 0 < rate <= 1.0)

    subsection("clear()")
    cache.clear()
    print(f"    Después de clear(): size={cache.size()}, hits={cache.hits}, misses={cache.misses}")
    check("clear", cache.size() == 0 and cache.hits == 0 and cache.misses == 0)


def test_ranking():
    section("ranking.py — Rankeador con heap")

    subsection("rank() con menos resultados que K")
    results = [SearchResult(i, f"doc_{i}", s) for i, s in enumerate([0.3, 0.1, 0.5])]
    print(f"    Scores entrada: {[r.score for r in results]}")
    ranked = ResultRanker.rank(results, top_k=10)
    print(f"    Scores salida: {[r.score for r in ranked]}")
    check("menos que K", len(ranked) == 3 and ranked[0].score == 0.5)

    subsection("rank() con más resultados que K")
    scores = [0.1, 0.5, 0.3, 0.9, 0.2, 0.8, 0.4, 0.7, 0.6, 0.0, 0.95]
    results = [SearchResult(i, f"doc_{i}", s) for i, s in enumerate(scores)]
    print(f"    Scores entrada: {scores}")
    ranked = ResultRanker.rank(results, top_k=3)
    print(f"    Top 3: {[r.score for r in ranked]}")
    check("más que K", len(ranked) == 3)
    check("orden descendente", all(ranked[i].score >= ranked[i + 1].score for i in range(2)))
    check("top score", ranked[0].score == 0.95)


def test_concurrency(docs_dir: str):
    section("concurrency.py — Procesamiento paralelo")

    engine = InvertedIndexEngine(docs_dir)
    engine.build_index()

    subsection("ParallelIndexBuilder")
    builder = ParallelIndexBuilder(docs_dir, workers=2)
    index, _elapsed = measure_time("ParallelIndexBuilder.build()", builder.build)
    print(f"    Documentos indexados: {len(index.get_all_doc_ids())}")
    check("ParallelIndexBuilder", len(index.get_all_doc_ids()) > 0)

    subsection("ConcurrentSearcher (multiprocessing)")
    searcher = ConcurrentSearcher(engine, workers=2)
    results, _elapsed = measure_time(
        "ConcurrentSearcher.search_batch(['python', 'java'])",
        searcher.search_batch,
        ["python", "java"],
    )
    for query, res in results.items():
        print(f"    '{query}': {len(res)} resultados")
    check("ConcurrentSearcher", len(results) == 2)

    subsection("ConcurrentSearcherThreaded (threads)")
    threaded = ConcurrentSearcherThreaded(engine, workers=2)
    results, _elapsed = measure_time(
        "ConcurrentSearcherThreaded.search_batch(['python', 'java'])",
        threaded.search_batch,
        ["python", "java"],
    )
    for query, res in results.items():
        print(f"    '{query}': {len(res)} resultados")
    check("ConcurrentSearcherThreaded", len(results) == 2)


def test_large_file_handler(docs_dir: str):
    section("large_file_handler.py — Manejo de archivos grandes")

    large_files = [f for f in list_doc_files(docs_dir) if f.startswith("documento_large_")]
    if not large_files:
        print("  [SKIP] No hay documentos grandes. Ejecute generate_large_documents primero.")
        return

    subsection("read_file_buffered()")
    filepath = os.path.join(docs_dir, large_files[0])
    file_size = os.path.getsize(filepath)
    print(f"    Archivo: {large_files[0]} ({file_size} bytes)")
    print(f"    Buffer size: {BUFFER_SIZE} bytes")
    content, _elapsed = measure_time("read_file_buffered()", read_file_buffered, filepath)
    print(f"    Leído: {len(content)} caracteres")
    check("read_file_buffered", len(content) > 0)

    subsection("tokens_from_large_file()")
    tokens, _elapsed = measure_time("tokens_from_large_file()", tokens_from_large_file, filepath)
    print(f"    Tokens extraídos: {len(tokens)}")
    print(f"    Primeros 10 tokens: {tokens[:10]}")
    check("tokens_from_large_file", len(tokens) > 0)

    subsection("get_total_tokens_large_files()")
    total, _elapsed = measure_time(
        "get_total_tokens_large_files()", get_total_tokens_large_files, docs_dir
    )
    print(f"    Total tokens en archivos grandes: {total}")
    check("get_total_tokens", total > 0, f"total={total}")

    subsection("build_index_large_files()")
    print(f"    Batch size: {BATCH_SIZE}")
    index, _elapsed = measure_time(
        "build_index_large_files(batch_size=5, workers=2)",
        build_index_large_files,
        docs_dir,
        5,
        2,
    )
    print(f"    Documentos indexados: {len(index.get_all_doc_ids())}")
    print(f"    Términos únicos: {len(index.index)}")
    check("build_index_large_files", len(index.get_all_doc_ids()) > 0)


def test_complexity():
    section("complexity.py — Análisis de complejidad")
    print(f"    Entradas en COMPLEXITY_ANALYSIS: {len(COMPLEXITY_ANALYSIS)}")
    for key, value in COMPLEXITY_ANALYSIS.items():
        print(f"    {key}:")
        if isinstance(value, dict):
            for k, v in value.items():
                print(f"      {k}: {v}")
        else:
            print(f"      {value}")
    check("COMPLEXITY_ANALYSIS existe", isinstance(COMPLEXITY_ANALYSIS, dict))
    check("tiene entradas", len(COMPLEXITY_ANALYSIS) > 0)


def test_quality_tools():
    section("run_quality_check.py — Análisis de calidad (pylint + radon)")

    subsection("pylint")
    from run_quality_check import run_pylint

    pylint_results = run_pylint()
    print(f"    Score: {pylint_results['score']:.2f}/10")
    print(f"    Problemas detectados: {pylint_results['problems']}")
    check(
        "pylint score > 9.0", pylint_results["score"] > 9.0, f"score={pylint_results['score']:.2f}"
    )

    subsection("radon cc (complejidad ciclomática)")
    from run_quality_check import run_radon

    radon_results = run_radon()
    cc_lines = radon_results["complexity_output"].strip().split("\n")
    print(
        f"    Funciones analizadas: {len([line for line in cc_lines if line.strip() and not line.startswith(' ')])}"
    )
    grades = {}
    for line in cc_lines:
        for grade in ["A", "B", "C", "D", "E", "F"]:
            if f" - {grade}" in line or f" {grade} " in line:
                grades[grade] = grades.get(grade, 0) + 1
    print(f"    Distribución: {dict(sorted(grades.items()))}")
    check("radon cc output", len(radon_results["complexity_output"]) > 0)

    subsection("radon mi (mantenibilidad)")
    mi_lines = radon_results["maintainability_output"].strip().split("\n")
    print(
        f"    Módulos analizados: {len([line for line in mi_lines if line.strip() and not line.startswith(' ')])}"
    )
    check("radon mi output", len(radon_results["maintainability_output"]) > 0)


def test_profiling():
    section("profiling_integration.py — Profiling cProfile + SnakeViz")

    subsection("profile_with_cprofile()")
    from profiling_integration import profile_with_cprofile

    def sample_work():
        total = 0
        for i in range(10000):
            total += i * i
        return total

    result, stats = profile_with_cprofile(sample_work)
    print(f"    Resultado: {result}")
    stat_lines = [line for line in stats.strip().split("\n") if line.strip()]
    print(f"    líneas de estadísticas: {len(stat_lines)}")
    print("    Top 5 funciones por tiempo:")
    for line in stat_lines[5:10]:
        print(f"      {line.strip()}")
    check("profile_with_cprofile", result == sum(i * i for i in range(10000)))

    subsection("generate_snakeviz_compatible_profile()")
    from profiling_integration import generate_snakeviz_compatible_profile

    with tempfile.NamedTemporaryFile(suffix=".prof", delete=False) as f:
        prof_path = f.name
    generate_snakeviz_compatible_profile(prof_path)
    prof_size = os.path.getsize(prof_path)
    print(f"    Archivo generado: {prof_path}")
    print(f"    Tamaño: {prof_size} bytes")
    check("archivo .prof generado", prof_size > 0)
    os.unlink(prof_path)


def test_docs_config():
    section("documentation/ — Configuración MkDocs")
    print(f"    mkdocs.yml existe: {os.path.exists('mkdocs.yml')}")
    print(f"    index.md existe: {os.path.exists('documentation/index.md')}")
    print(f"    ci.md existe: {os.path.exists('documentation/ci.md')}")
    check("mkdocs.yml existe", os.path.exists("mkdocs.yml"))
    check("index.md existe", os.path.exists("documentation/index.md"))
    check("ci.md existe", os.path.exists("documentation/ci.md"))


def test_api():
    section("api.py — API REST con FastAPI")
    print(f"    api.py existe: {os.path.exists('api.py')}")
    try:
        from api import FASTAPI_AVAILABLE

        if FASTAPI_AVAILABLE:
            from api import app

            print(f"    FastAPI disponible: {FASTAPI_AVAILABLE}")
            print(f"    App creada: {app is not None}")
            print(f"    Title: {app.title}")
            print(f"    Endpoints: {[r.path for r in app.routes if hasattr(r, 'path')]}")
            check("FastAPI importable", True)
            check("app creada", app is not None)
        else:
            print("  [SKIP] FastAPI no instalado")
    except ImportError:
        print("  [SKIP] FastAPI no instalado")


def test_glossary_and_adrs():
    section("Documentación del proyecto")
    print(f"    GLOSSARY.md: {os.path.exists('GLOSSARY.md')}")
    print(f"    docs/adr/: {os.path.exists('docs/adr/')}")
    print(f"    Parcial2.md: {os.path.exists('Parcial2.md')}")
    check("GLOSSARY.md existe", os.path.exists("GLOSSARY.md"))
    check("docs/adr/ existe", os.path.exists("docs/adr/"))
    check("Parcial2.md existe", os.path.exists("Parcial2.md"))


def test_main_menu_functions(docs_dir: str):
    section("main.py — Todas las funciones del menú interactivo")

    subsection("Opción 1: option_generate() — Generar documentos sintéticos")
    with tempfile.TemporaryDirectory() as tmpdir:
        count, elapsed = measure_time("generate_documents(20)", generate_documents, 20, tmpdir)
        print(f"    Generados: {count} documentos en {elapsed:.4f}s")
        check("option_generate", count == 20)

    subsection("Opción 2: option_generate_large() — Generar documentos grandes")
    with tempfile.TemporaryDirectory() as tmpdir:
        count, _elapsed = measure_time(
            "generate_large_documents(3, words_per_doc=500)",
            generate_large_documents,
            3,
            tmpdir,
            500,
        )
        print(f"    Generados: {count} documentos grandes en {elapsed:.4f}s")
        check("option_generate_large", count == 3)

    subsection("Opción 3: option_sequential_search() — Búsqueda secuencial")
    engine = SequentialSearchEngine(docs_dir)
    engine.load_documents()
    user_query = "python"
    print(f"    Ingresando consulta: '{user_query}'")
    results, elapsed = measure_time(f"sequential search('{user_query}')", engine.search, user_query)
    print(f"    Resultados: {len(results)} en {elapsed:.4f}s")
    if results:
        print(f"    Top: {results[0].doc_name} (score={results[0].score:.4f})")
    check("option_sequential_search", isinstance(results, list))

    subsection("Opción 4: option_indexed_search() — Búsqueda con índice invertido")
    engine = InvertedIndexEngine(docs_dir)
    engine.build_index()
    user_query = "python"
    print(f"    Ingresando consulta: '{user_query}'")
    results, elapsed = measure_time(f"indexed search('{user_query}')", engine.search, user_query)
    print(f"    Resultados: {len(results)} en {elapsed:.4f}s")
    if results:
        print(f"    Top: {results[0].doc_name} (score={results[0].score:.4f})")
    check("option_indexed_search", isinstance(results, list))

    subsection("Opción 5: option_cached_search() — Búsqueda con caché")
    cache = QueryCache()
    engine = InvertedIndexEngine(docs_dir)
    engine.build_index()

    user_query = "python"
    r1 = cache.get(user_query)
    print(f"    Ingresando consulta: '{user_query}'")
    print(f"    Primera consulta '{user_query}': cache {'HIT' if r1 else 'MISS'}")
    t0 = time.perf_counter()
    r1 = engine.search(user_query)
    cache.put(user_query, r1)
    t_miss = time.perf_counter() - t0

    print(f"    Ingresando consulta: '{user_query}' (repetida)")
    t0 = time.perf_counter()
    r2 = cache.get(user_query)
    t_hit = time.perf_counter() - t0

    print(f"    Miss: {t_miss:.6f}s ({len(r1)} resultados)")
    print(f"    Hit:  {t_hit:.6f}s ({len(r2)} resultados)")
    print(f"    Speedup: {t_miss / t_hit:.1f}x más rápido con caché")
    print(f"    Cache: hits={cache.hits}, misses={cache.misses}, hit_rate={cache.hit_rate():.1%}")
    check("option_cached_search", r2 == r1 and cache.hits == 1)

    subsection("Opción 6: option_large_file_index() — Índice para archivos grandes")
    large_files = [f for f in list_doc_files(docs_dir) if f.startswith("documento_large_")]
    if large_files:
        index, elapsed = measure_time(
            "build_index_large_files(batch_size=5, workers=2)",
            build_index_large_files,
            docs_dir,
            5,
            2,
        )
        print(f"    Documentos indexados: {len(index.get_all_doc_ids())} en {elapsed:.4f}s")
        check("option_large_file_index", len(index.get_all_doc_ids()) > 0)
    else:
        print("  [SKIP] No hay documentos grandes")

    subsection("Opción 7: option_benchmark() — Benchmark completo")
    from profiler import BenchmarkSuite

    suite = BenchmarkSuite(docs_dir)
    results, elapsed = measure_time("BenchmarkSuite.run_full()", suite.run_full)
    idx = results.get("construccion_indice", {})
    seq = idx.get("secuencial", {})
    inv = idx.get("invertido", {})
    print(f"    Construcción secuencial: {seq.get('tiempo_seg', 0):.4f}s")
    print(f"    Construcción invertida: {inv.get('tiempo_seg', 0):.4f}s")
    consultas = results.get("consultas", [])
    for c in consultas:
        print(
            f"    '{c['query']}': secuencial={c['secuencial']['tiempo_seg']:.6f}s, "
            f"indice={c['indice']['tiempo_seg']:.6f}s, mejora={c['mejora_x']:.1f}x"
        )
    check("option_benchmark", elapsed > 0)

    subsection("Opción 8: option_complexity() — Análisis de complejidad")
    from rich.console import Console

    from complexity import print_complexity_analysis

    with open(os.devnull, "w") as devnull:
        test_console = Console(file=devnull)
        print_complexity_analysis(test_console)
    print(f"    Términos documentados: {len(COMPLEXITY_ANALYSIS)}")
    check("option_complexity", len(COMPLEXITY_ANALYSIS) > 0)

    subsection("Opción 10: option_quality() — Análisis de calidad")
    from run_quality_check import run_pylint, run_radon

    pylint_results = run_pylint()
    radon_results = run_radon()
    print(f"    pylint score: {pylint_results['score']:.2f}/10")
    print(f"    radon cc: {len(radon_results['complexity_output'].strip().split(chr(10)))} líneas")
    print(
        f"    radon mi: {len(radon_results['maintainability_output'].strip().split(chr(10)))} líneas"
    )
    check("option_quality", pylint_results["score"] > 9.0)

    subsection("Opción 11: option_profiling() — Perfilado cProfile + SnakeViz")
    from profiling_integration import generate_snakeviz_compatible_profile, profile_with_cprofile

    def work():
        e = InvertedIndexEngine(docs_dir)
        e.build_index()
        return len(e.index.get_all_doc_ids())

    result, stats = profile_with_cprofile(work)
    print(f"    Documentos indexados durante profiling: {result}")
    print(f"    Estadísticas: {len(stats)} caracteres")
    with tempfile.NamedTemporaryFile(suffix=".prof", delete=False) as f:
        prof_path = f.name
    generate_snakeviz_compatible_profile(prof_path)
    print(f"    profile.prof: {os.path.getsize(prof_path)} bytes")
    os.unlink(prof_path)
    check("option_profiling", result > 0)

    subsection("Opción 12: option_docs() — Documentación MkDocs")
    check("mkdocs.yml", os.path.exists("mkdocs.yml"))
    check("documentation/index.md", os.path.exists("documentation/index.md"))


def main():
    print("=" * 70)
    print("  TEST COMPLETO — Buscador Eficiente de Información")
    print("  Con output detallado y mediciones")
    print("=" * 70)

    if not os.path.isdir(DOCS_DIR) or len(list_doc_files(DOCS_DIR)) == 0:
        print("\nGenerando documentos sintéticos...")
        generate_documents(50, DOCS_DIR)

    has_large = any(f.startswith("documento_large_") for f in list_doc_files(DOCS_DIR))
    if not has_large:
        print("Generando documentos grandes...")
        generate_large_documents(3, DOCS_DIR, words_per_doc=500)

    test_search_common()
    test_generator()
    test_sequential_search(DOCS_DIR)
    test_inverted_index(DOCS_DIR)
    test_cache()
    test_ranking()
    test_concurrency(DOCS_DIR)
    test_large_file_handler(DOCS_DIR)
    test_complexity()
    test_quality_tools()
    test_profiling()
    test_docs_config()
    test_api()
    test_glossary_and_adrs()
    test_main_menu_functions(DOCS_DIR)

    print(f"\n{'=' * 70}")
    print(f"  RESULTADO FINAL: {PASSED} passed, {FAILED} failed")
    print(f"{'=' * 70}")

    if FAILED > 0:
        print(f"\n  {FAILED} tests fallaron. Revisar output anterior para detalles.")
    else:
        print("\n  Todos los tests pasaron exitosamente.")

    return FAILED == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
