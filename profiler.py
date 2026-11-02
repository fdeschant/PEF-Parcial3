import json
import os
import subprocess
import time
import tracemalloc

from cache import QueryCache
from concurrency import ConcurrentSearcher, ConcurrentSearcherThreaded, ParallelIndexBuilder
from config import DOCS_DIR
from inverted_index import InvertedIndexEngine
from search_sequential import SequentialSearchEngine

BENCHMARK_QUERIES = [
    "java concurrencia",
    "python machine learning",
    "base datos sql",
    "algoritmo ordenamiento",
    "red tcp protocolo",
    "sistema operativo proceso",
    "java",
    "python django flask",
    "indice btree hash",
    "memoria virtual paginacion",
]


class BenchmarkSuite:
    def __init__(self, docs_dir: str = DOCS_DIR):
        self.docs_dir = docs_dir
        self.results: dict = {}

    def run_full(self, queries: list[str] | None = None, concurrent_repeats: int = 100) -> dict:
        if queries is None:
            queries = BENCHMARK_QUERIES

        self.results = {
            "construccion_indice": {},
            "consultas": [],
            "cache": {},
            "paralelo": {},
            "busqueda_concurrente": {},
            "busqueda_hilos": {},
        }

        self._benchmark_index_construction()
        self._benchmark_parallel_construction()
        self._benchmark_queries(queries)
        self._benchmark_cache(queries)

        concurrent_queries = queries * concurrent_repeats
        self._benchmark_concurrent_search(concurrent_queries)
        self._benchmark_threaded_search(concurrent_queries)
        self._measure_memory()

        return self.results

    def _benchmark_index_construction(self):
        engine_sequential = SequentialSearchEngine(self.docs_dir)
        engine_indexed = InvertedIndexEngine(self.docs_dir)

        tracemalloc.start()

        t0 = time.perf_counter()
        doc_count_seq = engine_sequential.load_documents()
        t_seq = time.perf_counter() - t0

        t0 = time.perf_counter()
        doc_count_idx = engine_indexed.build_index()
        t_idx = time.perf_counter() - t0

        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self._engine_sequential = engine_sequential
        self._engine_indexed = engine_indexed

        self.results["construccion_indice"] = {
            "secuencial": {
                "tiempo_seg": round(t_seq, 6),
                "documentos": doc_count_seq,
            },
            "invertido": {
                "tiempo_seg": round(t_idx, 6),
                "documentos": doc_count_idx,
                "memoria_pico_bytes": peak,
            },
        }

    def _benchmark_parallel_construction(self):
        builder = ParallelIndexBuilder(self.docs_dir)

        t0 = time.perf_counter()
        parallel_index = builder.build()
        t_par = time.perf_counter() - t0

        build_time = self.results["construccion_indice"]["invertido"]["tiempo_seg"]
        speedup = build_time / t_par if t_par > 0 else 0

        self.results["paralelo"] = {
            "tiempo_seg": round(t_par, 6),
            "workers": builder.workers,
            "speedup": round(speedup, 2),
            "documentos": len(parallel_index.doc_lengths),
        }

    def _benchmark_concurrent_search(self, queries: list[str]):
        t0 = time.perf_counter()
        for q in queries:
            self._engine_indexed.search(q)
        t_seq_search = time.perf_counter() - t0

        searcher = ConcurrentSearcher(self._engine_indexed)
        t0 = time.perf_counter()
        searcher.search_batch(queries)
        t_par_search = time.perf_counter() - t0

        speedup = t_seq_search / t_par_search if t_par_search > 0 else 0

        self.results["busqueda_concurrente"] = {
            "secuencial": {
                "tiempo_total_seg": round(t_seq_search, 6),
                "queries": len(queries),
            },
            "paralelo": {
                "tiempo_total_seg": round(t_par_search, 6),
                "workers": searcher.workers,
                "queries": len(queries),
            },
            "speedup_x": round(speedup, 2),
        }

    def _benchmark_threaded_search(self, queries: list[str]):
        t0 = time.perf_counter()
        for q in queries:
            self._engine_indexed.search(q)
        t_seq_search = time.perf_counter() - t0

        searcher = ConcurrentSearcherThreaded(self._engine_indexed)
        t0 = time.perf_counter()
        searcher.search_batch(queries)
        t_threads_search = time.perf_counter() - t0

        speedup = t_seq_search / t_threads_search if t_threads_search > 0 else 0

        self.results["busqueda_hilos"] = {
            "secuencial": {
                "tiempo_total_seg": round(t_seq_search, 6),
                "queries": len(queries),
            },
            "hilos": {
                "tiempo_total_seg": round(t_threads_search, 6),
                "workers": searcher.workers,
                "queries": len(queries),
            },
            "speedup_x": round(speedup, 2),
        }

    def _benchmark_queries(self, queries: list[str]):
        for query in queries:
            t0 = time.perf_counter()
            res_seq = self._engine_sequential.search(query)
            t_seq = time.perf_counter() - t0

            t0 = time.perf_counter()
            res_idx = self._engine_indexed.search(query)
            t_idx = time.perf_counter() - t0

            mejora = t_seq / t_idx if t_idx > 0 else 0

            self.results["consultas"].append(
                {
                    "query": query,
                    "secuencial": {
                        "tiempo_seg": round(t_seq, 6),
                        "resultados": len(res_seq),
                    },
                    "indice": {
                        "tiempo_seg": round(t_idx, 6),
                        "resultados": len(res_idx),
                    },
                    "mejora_x": round(mejora, 1),
                }
            )

    def _benchmark_cache(self, queries: list[str]):
        cache = QueryCache(max_size=128)

        popular_queries = queries[:10]
        unique_miss_queries = [
            "machine learning",
            "base de datos",
            "redes sociales",
            "inteligencia artificial",
            "desarrollo web",
            "algoritmos geneticos",
            "aprendizaje profundo",
            "computacion cuantica",
            "blockchain",
            "criptografia",
            "redes neuronales",
            "sistema operativo",
            "compiladores",
            "ingenieria de software",
            "bases de datos distribuidas",
        ]

        for query in popular_queries:
            results = self._engine_indexed.search(query)
            cache.put(query, results)

        t0 = time.perf_counter()
        for _ in range(500):
            for query in popular_queries:
                cache.get(query)
        t_hits = time.perf_counter() - t0
        hits_count = cache.hits

        t0 = time.perf_counter()
        for _ in range(500):
            for query in unique_miss_queries:
                cache.get(query)
        t_misses_lookup = time.perf_counter() - t0
        misses_count = cache.misses

        t0 = time.perf_counter()
        for _ in range(500):
            for query in unique_miss_queries:
                self._engine_indexed.search(query)
        t_misses_search = time.perf_counter() - t0

        total = hits_count + misses_count
        hit_rate = hits_count / total if total > 0 else 0
        avg_miss = (t_misses_lookup + t_misses_search) / misses_count if misses_count else 0

        self.results["cache"] = {
            "hits": hits_count,
            "misses": misses_count,
            "hit_rate": round(hit_rate, 4),
            "tiempo_hit_seg": round(t_hits / hits_count, 9) if hits_count else 0,
            "tiempo_miss_seg": round(avg_miss, 9),
            "queries_capturadas": len(popular_queries),
            "queries_futuras": len(unique_miss_queries),
        }

    def _measure_memory(self):
        self.results["memoria"] = {
            "indice_terminos": len(self._engine_indexed.index.index),
            "indice_documentos": len(self._engine_indexed.index.doc_lengths),
        }


class ScaleneRunner:
    SCALENE_AVAILABLE = False
    try:
        subprocess.run(
            [os.sys.executable, "-m", "scalene", "--version"],
            capture_output=True,
            timeout=10,
        )
        SCALENE_AVAILABLE = True
    except Exception:
        SCALENE_AVAILABLE = False

    @classmethod
    def is_available(cls) -> bool:
        return cls.SCALENE_AVAILABLE

    def run_benchmark(self, docs_dir: str = DOCS_DIR) -> dict:
        if not self.is_available():
            return {"error": "Scalene no esta instalado. Ejecute: pip install scalene"}

        script_path = os.path.join(os.path.dirname(__file__), "benchmark_script.py")
        if not os.path.exists(script_path):
            return {"error": f"No se encontro {script_path}"}

        json_output = os.path.join(os.path.dirname(__file__), "scalene-profile.json")

        try:
            result = subprocess.run(
                [
                    os.sys.executable,
                    "-m",
                    "scalene",
                    "run",
                    "--memory",
                    "--profile-all",
                    "-o",
                    json_output,
                    script_path,
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if os.path.exists(json_output):
                return self._parse_scalene_output(json_output)
            else:
                return self._parse_scalene_stdout(result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            return {"error": "El perfilado con Scalene excedio el tiempo limite (300s)."}
        except Exception as e:
            return {"error": f"Error al ejecutar Scalene: {e!s}"}
        finally:
            if os.path.exists(json_output):
                os.unlink(json_output)

    @staticmethod
    def _parse_scalene_output(json_path: str) -> dict:
        try:
            with open(json_path, encoding="utf-8") as f:
                raw = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"error": "No se pudo parsear la salida JSON de Scalene."}

        result = {
            "archivos": {},
            "resumen_cpu": {"total_seg": 0.0, "lineas_calientes": []},
            "resumen_memoria": {"total_malloc_mb": 0.0, "allocaciones": 0, "pico_mb": 0.0},
        }

        result["resumen_cpu"]["total_seg"] = round(raw.get("elapsed_time_sec", 0.0), 6)
        result["resumen_memoria"]["pico_mb"] = round(raw.get("max_footprint_mb", 0.0), 4)

        files_data = raw.get("files", {})
        all_lines = []

        for filepath, file_info in files_data.items():
            filename = os.path.basename(filepath)
            lines_data = file_info.get("lines", [])
            file_summary = {
                "cpu_time_seg": 0.0,
                "mallocs": 0,
                "total_malloc_mb": 0.0,
                "lineas": [],
            }

            for line_entry in lines_data:
                cpu_percent = line_entry.get("n_cpu_percent_python", 0.0) + line_entry.get(
                    "n_cpu_percent_c", 0.0
                )
                mallocs = line_entry.get("n_mallocs", 0)
                malloc_mb = line_entry.get("n_malloc_mb", 0.0)
                lineno = line_entry.get("lineno", 0)

                cpu_time_est = (cpu_percent / 100.0) * raw.get("elapsed_time_sec", 0.0)
                file_summary["cpu_time_seg"] += cpu_time_est
                file_summary["mallocs"] += mallocs
                file_summary["total_malloc_mb"] += malloc_mb

                if cpu_percent > 0.5 or mallocs > 0:
                    line_detail = {
                        "linea": lineno,
                        "archivo": filename,
                        "cpu_percent": round(cpu_percent, 2),
                        "cpu_time_seg": round(cpu_time_est, 6),
                        "mallocs": mallocs,
                        "total_malloc_mb": round(malloc_mb, 4),
                        "pico_mb": round(line_entry.get("n_peak_mb", 0.0), 4),
                    }
                    file_summary["lineas"].append(line_detail)
                    all_lines.append(line_detail)

            file_summary["lineas"].sort(key=lambda x: x["cpu_percent"], reverse=True)
            result["archivos"][filename] = file_summary
            result["resumen_memoria"]["total_malloc_mb"] += file_summary["total_malloc_mb"]
            result["resumen_memoria"]["allocaciones"] += file_summary["mallocs"]

        all_lines.sort(key=lambda x: x["cpu_percent"], reverse=True)
        result["resumen_cpu"]["lineas_calientes"] = all_lines[:15]

        result["resumen_memoria"]["total_malloc_mb"] = round(
            result["resumen_memoria"]["total_malloc_mb"], 4
        )

        return result

    @staticmethod
    def _parse_scalene_stdout(stdout: str, stderr: str) -> dict:
        result = {
            "archivos": {},
            "resumen_cpu": {"total_seg": 0.0, "lineas_calientes": []},
            "resumen_memoria": {"total_malloc_mb": 0.0, "allocaciones": 0},
            "raw_output": stdout[:2000] if stdout else "",
            "raw_errors": stderr[:1000] if stderr else "",
        }
        return result
