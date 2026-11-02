"""Herramienta de análisis de calidad de código.

Ejecuta pylint y radon sobre el código fuente,
y presenta los resultados en una tabla resumen.

Uso:
    python run_quality_check.py
"""

import contextlib
import subprocess
import sys

MODULES = [
    "search_common.py",
    "search_sequential.py",
    "inverted_index.py",
    "ranking.py",
    "cache.py",
    "concurrency.py",
    "generator.py",
    "large_file_handler.py",
    "profiler.py",
    "reporter.py",
    "config.py",
    "main.py",
]


def run_pylint() -> dict:
    """Ejecuta pylint sobre los módulos del proyecto.

    Returns:
        Diccionario con score y cantidad de problemas.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pylint", "--disable=C0114,C0115,C0116,R0903", *MODULES],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    score_line = [line for line in output.split("\n") if "rated at" in line]
    score = 0.0
    if score_line:
        with contextlib.suppress(IndexError, ValueError):
            score = float(score_line[-1].split("rated at")[1].split("/")[0])
    problem_count = output.count(": ")
    return {"score": score, "problems": problem_count, "output": output}


def run_radon() -> dict:
    """Ejecuta radon para complejidad ciclomática y mantenibilidad.

    Returns:
        Diccionario con métricas de complejidad.
    """
    cc_result = subprocess.run(
        [sys.executable, "-m", "radon", "cc", "-s", "."],
        capture_output=True,
        text=True,
    )
    mi_result = subprocess.run(
        [sys.executable, "-m", "radon", "mi", "-s", "."],
        capture_output=True,
        text=True,
    )
    return {
        "complexity_output": cc_result.stdout,
        "maintainability_output": mi_result.stdout,
    }


def main():
    """Punto de entrada principal."""
    print("=" * 60)
    print("ANÁLISIS DE CALIDAD DE CÓDIGO")
    print("=" * 60)

    print("\n[1] Ejecutando pylint...")
    pylint_results = run_pylint()
    print(f"    Score: {pylint_results['score']:.2f}/10")
    print(f"    Problemas detectados: {pylint_results['problems']}")

    print("\n[2] Ejecutando radon (complejidad ciclomática)...")
    radon_results = run_radon()
    print(radon_results["complexity_output"])

    print("\n[3] Ejecutando radon (mantenibilidad)...")
    print(radon_results["maintainability_output"])

    print("=" * 60)
    print("Análisis completo. Revisar output anterior para detalles.")
    print("=" * 60)


if __name__ == "__main__":
    main()
