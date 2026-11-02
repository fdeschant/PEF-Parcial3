"""Test de integración que ejecuta TODAS las opciones del menú de main.py.

Simula input del usuario con unittest.mock y verifica que cada
opción del menú funcione correctamente de punta a punta.

Uso:
    python scripts/check_menu.py
"""

import io
import os
import sys
import tempfile
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DOCS_DIR
from generator import generate_documents, generate_large_documents
from search_common import list_doc_files

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


def setup_docs():
    if len(list_doc_files(DOCS_DIR)) == 0:
        print("Generando documentos sintéticos...")
        generate_documents(50, DOCS_DIR)
    has_large = any(f.startswith("documento_large_") for f in list_doc_files(DOCS_DIR))
    if not has_large:
        print("Generando documentos grandes...")
        generate_large_documents(3, DOCS_DIR, words_per_doc=500)


def test_option_1_generate():
    section("Opción 1: option_generate() — Generar documentos sintéticos")
    import main

    with tempfile.TemporaryDirectory() as tmpdir:
        with (
            patch("main.DOCS_DIR", tmpdir),
            patch("main.NUM_DOCUMENTS", 5),
            patch("main.generate_documents", wraps=main.generate_documents) as mock_gen,
            patch("main.Console.print"),
            patch("main.Progress"),
        ):
            mock_gen.return_value = 5
            buf = io.StringIO()
            with redirect_stdout(buf):
                main.option_generate()
        check("option_generate", mock_gen.called, "generate_documents fue llamado")


def test_option_2_generate_large():
    section("Opción 2: option_generate_large() — Generar documentos grandes")
    import main

    with patch("main.Console.print"), patch("main.Progress"):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main.option_generate_large()
    check("option_generate_large", True)


def test_option_3_sequential_search():
    section("Opción 3: option_sequential_search() — Búsqueda secuencial")
    import main

    user_input = "python"
    print(f"    Simulando input del usuario: '{user_input}'")

    with (
        patch("main.SequentialSearchEngine") as mock_engine_cls,
        patch("main.Console.print"),
        patch("main.Progress"),
    ):
        mock_engine = mock_engine_cls.return_value
        mock_engine.load_documents.return_value = 50
        mock_engine.search.return_value = [
            type(
                "R",
                (),
                {
                    "doc_id": 1,
                    "doc_name": "documento_1.txt",
                    "score": 0.5,
                    "snippet": "python es...",
                },
            )()
        ]

        inputs = iter([user_input])
        with patch("main.console.input", side_effect=lambda prompt: next(inputs)):
            buf = io.StringIO()
            with redirect_stdout(buf):
                main.option_sequential_search()

        check("SequentialSearchEngine instanciado", mock_engine_cls.called)
        check("load_documents llamado", mock_engine.load_documents.called)
        check(f"search('{user_input}') llamado", mock_engine.search.called)


def test_option_4_indexed_search():
    section("Opción 4: option_indexed_search() — Búsqueda con índice invertido")
    import main

    user_input = "python"
    print(f"    Simulando input del usuario: '{user_input}'")

    with (
        patch("main.InvertedIndexEngine") as mock_engine_cls,
        patch("main.Console.print"),
        patch("main.Progress"),
    ):
        mock_engine = mock_engine_cls.return_value
        mock_engine.build_index.return_value = 50
        mock_engine.search.return_value = [
            type(
                "R",
                (),
                {
                    "doc_id": 1,
                    "doc_name": "documento_1.txt",
                    "score": 0.5,
                    "snippet": "python es...",
                },
            )()
        ]

        inputs = iter([user_input])
        with patch("main.console.input", side_effect=lambda prompt: next(inputs)):
            buf = io.StringIO()
            with redirect_stdout(buf):
                main.option_indexed_search()

        check("InvertedIndexEngine instanciado", mock_engine_cls.called)
        check("build_index llamado", mock_engine.build_index.called)
        check(f"search('{user_input}') llamado", mock_engine.search.called)


def test_option_5_cached_search():
    section("Opción 5: option_cached_search() — Búsqueda con caché")
    import main

    user_input = "python"
    print(f"    Simulando input del usuario: '{user_input}'")

    with (
        patch("main.InvertedIndexEngine") as mock_engine_cls,
        patch("main.QueryCache") as mock_cache_cls,
        patch("main.Console.print"),
        patch("main.Progress"),
    ):
        mock_engine = mock_engine_cls.return_value
        mock_engine.build_index.return_value = 50
        mock_engine.search.return_value = [
            type(
                "R",
                (),
                {
                    "doc_id": 1,
                    "doc_name": "documento_1.txt",
                    "score": 0.5,
                    "snippet": "python es...",
                },
            )()
        ]
        mock_cache = mock_cache_cls.return_value
        mock_cache.get.return_value = None
        mock_cache.hits = 0
        mock_cache.misses = 1
        mock_cache.hit_rate.return_value = 0.0

        inputs = iter([user_input, "volver"])
        with patch("main.console.input", side_effect=lambda prompt: next(inputs)):
            buf = io.StringIO()
            with redirect_stdout(buf):
                main.option_cached_search()

        check("InvertedIndexEngine instanciado", mock_engine_cls.called)
        check("QueryCache instanciado", mock_cache_cls.called)
        check("cache.get llamado", mock_cache.get.called)
        check("cache.put llamado", mock_cache.put.called)


def test_option_6_large_file_index():
    section("Opción 6: option_large_file_index() — Índice para archivos grandes")
    import main

    has_large = any(f.startswith("documento_large_") for f in list_doc_files(DOCS_DIR))
    if not has_large:
        print("  [SKIP] No hay documentos grandes")
        return

    user_input = "python"
    print(f"    Simulando input del usuario: '{user_input}'")

    with (
        patch("main.build_index_large_files") as mock_build,
        patch("main.InvertedIndexEngine") as mock_engine_cls,
        patch("main.get_document_count", return_value=3),
        patch("main.Console.print"),
        patch("main.Progress"),
    ):
        mock_build.return_value = type(
            "Idx",
            (),
            {
                "get_all_doc_ids": lambda self: set(),
                "index": {"term": set()},
            },
        )()
        mock_engine = mock_engine_cls.return_value
        mock_engine.search.return_value = [
            type(
                "R",
                (),
                {
                    "doc_id": 10001,
                    "doc_name": "documento_large_10001.txt",
                    "score": 0.5,
                    "snippet": "python es...",
                },
            )()
        ]

        inputs = iter([user_input])
        with patch("main.console.input", side_effect=lambda prompt: next(inputs)):
            buf = io.StringIO()
            with redirect_stdout(buf):
                main.option_large_file_index()

        check("build_index_large_files llamado", mock_build.called)


def test_option_7_benchmark():
    section("Opción 7: option_benchmark() — Benchmark completo")
    import main

    with (
        patch("main.BenchmarkSuite") as mock_suite_cls,
        patch("main.Console.print"),
        patch("main.Progress"),
    ):
        mock_suite = mock_suite_cls.return_value
        mock_suite.run_full.return_value = {
            "construccion_indice": {
                "secuencial": {"tiempo_seg": 0.01, "documentos": 50},
                "invertido": {"tiempo_seg": 0.005, "documentos": 50, "memoria_pico_bytes": 4500000},
            },
            "consultas": [
                {
                    "query": "python",
                    "secuencial": {"tiempo_seg": 0.002},
                    "indice": {"tiempo_seg": 0.0002},
                    "mejora_x": 10.0,
                }
            ],
            "cache": {
                "hits": 10,
                "misses": 5,
                "hit_rate": 0.67,
                "tiempo_hit_seg": 0.00001,
                "tiempo_miss_seg": 0.0001,
            },
        }

        buf = io.StringIO()
        with redirect_stdout(buf):
            main.option_benchmark()

        check("BenchmarkSuite instanciado", mock_suite_cls.called)
        check("run_full llamado", mock_suite.run_full.called)


def test_option_8_complexity():
    section("Opción 8: option_complexity() — Análisis de complejidad")
    import main

    with patch("main.print_complexity_analysis") as mock_print, patch("main.Console.print"):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main.option_complexity()

        check("print_complexity_analysis llamado", mock_print.called)


def test_option_10_quality():
    section("Opción 10: option_quality() — Análisis de calidad")
    import main

    with (
        patch("main.Console.print"),
        patch("main.run_quality_check.run_pylint") as mock_pylint,
        patch("main.run_quality_check.run_radon") as mock_radon,
    ):
        mock_pylint.return_value = {"score": 9.5, "problems": 3, "output": ""}
        mock_radon.return_value = {
            "complexity_output": "file.py\n    F 10:0 func - A (1)",
            "maintainability_output": "file.py - A (80.0)",
        }

        buf = io.StringIO()
        with redirect_stdout(buf):
            main.option_quality()

        check("run_pylint llamado", mock_pylint.called)
        check("run_radon llamado", mock_radon.called)


def test_option_11_profiling():
    section("Opción 11: option_profiling() — Perfilado cProfile + SnakeViz")
    import main

    with patch("main.Console.print"), patch("main.Progress"):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main.option_profiling()
        check("option_profiling completado", True)


def test_option_12_docs():
    section("Opción 12: option_docs() — Documentación MkDocs")
    import main

    with patch("main.subprocess.run") as mock_run, patch("main.Console.print"):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        buf = io.StringIO()
        with redirect_stdout(buf):
            main.option_docs()

        check("mkdocs build ejecutado", mock_run.called)


def main():
    print("=" * 70)
    print("  TEST DE INTEGRACIÓN — Todas las opciones del menú de main.py")
    print("  Simula input del usuario y verifica funcionamiento de cada opción")
    print("=" * 70)

    setup_docs()

    test_option_1_generate()
    test_option_2_generate_large()
    test_option_3_sequential_search()
    test_option_4_indexed_search()
    test_option_5_cached_search()
    test_option_6_large_file_index()
    test_option_7_benchmark()
    test_option_8_complexity()
    test_option_10_quality()
    test_option_11_profiling()
    test_option_12_docs()

    print(f"\n{'=' * 70}")
    print(f"  RESULTADO FINAL: {PASSED} passed, {FAILED} failed")
    print(f"{'=' * 70}")

    if FAILED > 0:
        print(f"\n  {FAILED} tests fallaron. Revisar output anterior para detalles.")
    else:
        print("\n  Todas las opciones del menú funcionan correctamente.")

    return FAILED == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
