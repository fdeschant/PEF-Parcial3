import os
import subprocess
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table
from rich.text import Text

import run_quality_check
from cache import QueryCache
from complexity import print_complexity_analysis
from config import DOCS_DIR, NUM_DOCUMENTS
from generator import generate_documents, generate_large_documents, get_document_count
from inverted_index import InvertedIndexEngine
from large_file_handler import build_index_large_files
from profiler import BenchmarkSuite, ScaleneRunner
from reporter import ReportGenerator
from search_sequential import SequentialSearchEngine

console = Console()


def show_menu():
    console.print()
    console.print(
        Panel(
            Text("BUSCADOR EFICIENTE DE INFORMACION", style="bold white", justify="center")
            + "\n"
            + Text("Programacion Eficiente - Parcial 3", style="italic cyan", justify="center"),
            border_style="blue",
        )
    )
    console.print()

    options = [
        ("1", "Generar documentos sinteticos"),
        ("2", "Generar documentos grandes (10k+ palabras)"),
        ("3", "Busqueda secuencial"),
        ("4", "Busqueda con indice invertido"),
        ("5", "Busqueda con cache"),
        ("6", "Indice invertido para archivos grandes"),
        ("7", "Ejecutar benchmark completo"),
        ("8", "Analisis de complejidad"),
        ("9", "Test completo + reporte + perfilado"),
        ("10", "Analisis de calidad (pylint + radon)"),
        ("11", "Perfilado cProfile + SnakeViz"),
        ("12", "Documentacion MkDocs"),
        ("0", "Salir"),
    ]

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Opcion", style="bold yellow", justify="right")
    table.add_column("Descripcion")
    for num, desc in options:
        table.add_row(num, desc)
    console.print(table)
    console.print()


def option_generate():
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Generando documentos...", total=NUM_DOCUMENTS)
        for _ in range(NUM_DOCUMENTS):
            progress.update(task, advance=1)

        count = generate_documents(NUM_DOCUMENTS, DOCS_DIR)

    console.print(f"\n[green]Se generaron {count} documentos en {DOCS_DIR}[/green]")


def option_generate_large():
    console.print()
    num_large = 50
    words_per_doc = 10000
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"Generando {num_large} documentos grandes...", total=num_large)
        for _ in range(num_large):
            progress.update(task, advance=1)

        count = generate_large_documents(num_large, DOCS_DIR, words_per_doc)

    console.print(
        f"\n[green]Se generaron {count} documentos grandes ({words_per_doc} palabras c/u)[/green]"
    )


def option_sequential_search():
    engine = SequentialSearchEngine(DOCS_DIR)
    t0 = time.perf_counter()
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as p:
        task = p.add_task("Cargando documentos...")
        count = engine.load_documents()
        p.update(task, completed=True)
    load_elapsed = time.perf_counter() - t0

    if count == 0:
        console.print(
            "[red]No se encontraron documentos. Genere documentos primero (opcion 1).[/red]"
        )
        return

    console.print(f"[dim]Documentos cargados: {count} (carga: {load_elapsed:.4f}s)[/dim]")
    query = console.input("[bold]Ingrese la consulta:[/bold] ")
    if not query.strip():
        return

    t0 = time.perf_counter()
    results = engine.search(query)
    search_elapsed = time.perf_counter() - t0

    _show_results(results, search_elapsed, "Busqueda secuencial", count)
    console.print(
        f"[dim]Tiempo total: carga + busqueda = {load_elapsed + search_elapsed:.4f}s[/dim]"
    )


def option_indexed_search():
    engine = InvertedIndexEngine(DOCS_DIR)
    t0 = time.perf_counter()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Construyendo indice invertido...", total=None)
        doc_count = engine.build_index(
            progress_callback=lambda cur, tot: progress.update(task, completed=cur, total=tot)
        )
    build_elapsed = time.perf_counter() - t0

    if doc_count == 0:
        console.print(
            "[red]No se encontraron documentos. Genere documentos primero (opcion 1).[/red]"
        )
        return

    console.print(
        f"[dim]Indice construido: {doc_count} documentos, {len(engine.index.index)} terminos (construccion: {build_elapsed:.4f}s)[/dim]"
    )
    query = console.input("[bold]Ingrese la consulta:[/bold] ")
    if not query.strip():
        return

    t0 = time.perf_counter()
    results = engine.search(query)
    search_elapsed = time.perf_counter() - t0

    _show_results(results, search_elapsed, "Busqueda con indice invertido", doc_count)
    console.print(
        f"[dim]Tiempo total: construccion + busqueda = {build_elapsed + search_elapsed:.4f}s[/dim]"
    )


def option_cached_search():
    engine = InvertedIndexEngine(DOCS_DIR)
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as p:
        task = p.add_task("Construyendo indice invertido...")
        engine.build_index()
        p.update(task, completed=True)

    if engine.get_doc_count() == 0:
        console.print("[red]No se encontraron documentos.[/red]")
        return

    cache = QueryCache()
    console.print("[dim]Motor listo. Las consultas se almacenaran en cache.[/dim]")

    while True:
        query = console.input("[bold]Ingrese la consulta (o 'volver'):[/bold] ")
        if query.strip().lower() == "volver":
            break
        if not query.strip():
            continue

        cached = cache.get(query)
        if cached is not None:
            console.print("[green]Consulta encontrada en cache.[/green]")
            results = cached
            t0 = time.perf_counter()
            elapsed = time.perf_counter() - t0
        else:
            console.print("[yellow]Consulta no encontrada. Procesando...[/yellow]")
            t0 = time.perf_counter()
            results = engine.search(query)
            elapsed = time.perf_counter() - t0
            cache.put(query, results)

        _show_results(results, elapsed, "Busqueda con cache", len(engine.index.doc_lengths))

    console.print(
        f"\n[dim]Estadisticas de cache: {cache.hits} hits, {cache.misses} misses, "
        f"tasa de acierto: {cache.hit_rate():.1%}[/dim]"
    )


def option_large_file_index():
    console.print()
    doc_count = get_document_count(DOCS_DIR)
    if doc_count == 0:
        console.print(
            "[red]No se encuentaron documentos. Genere documentos grandes primero (opcion 2).[/red]"
        )
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Construyendo indice para archivos grandes...")
        index = build_index_large_files(DOCS_DIR)
        progress.update(task, completed=True)

    total_docs = len(index.get_all_doc_ids())
    total_terms = len(index.index)
    console.print(
        f"\n[green]Indice construido: {total_docs} documentos, {total_terms} terminos[/green]"
    )

    query = console.input("[bold]Ingrese la consulta:[/bold] ")
    if not query.strip():
        return

    engine = InvertedIndexEngine(DOCS_DIR)
    engine.index = index
    t0 = time.perf_counter()
    results = engine.search(query)
    elapsed = time.perf_counter() - t0

    _show_results(results, elapsed, "Busqueda en archivos grandes", total_docs)


def option_benchmark():
    console.print()
    console.print(Panel("Ejecutando benchmark completo", border_style="yellow"))

    suite = BenchmarkSuite(DOCS_DIR)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Ejecutando benchmark...")
        results = suite.run_full()
        progress.update(task, completed=True)

    _show_benchmark_results(results)


def option_complexity():
    print_complexity_analysis(console)


def option_quality():
    console.print()
    console.print(Panel("Analisis de calidad de codigo", border_style="cyan"))

    console.print("\n[bold]Ejecutando pylint...[/bold]")
    pylint_results = run_quality_check.run_pylint()
    console.print(f"  Score: {pylint_results['score']:.2f}/10")
    console.print(f"  Problemas: {pylint_results['problems']}")

    console.print("\n[bold]Ejecutando radon...[/bold]")
    radon_results = run_quality_check.run_radon()
    console.print(radon_results["complexity_output"])
    console.print(radon_results["maintainability_output"])


def option_profiling():
    console.print()
    console.print(Panel("Perfilado cProfile + SnakeViz", border_style="magenta"))

    from profiling_integration import generate_snakeviz_compatible_profile, run_profile_benchmark

    run_profile_benchmark(DOCS_DIR)

    console.print("\n[bold]Generando perfil para SnakeViz...[/bold]")
    generate_snakeviz_compatible_profile("profile.prof")
    console.print(f"[dim]Visualizar con: {sys.executable} -m snakeviz profile.prof[/dim]")


def option_docs():
    console.print()
    console.print(Panel("Generando documentacion MkDocs", border_style="green"))

    base_dir = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict"],
        cwd=base_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        console.print(f"\n[green]Documentacion generada en {base_dir}/site/index.html[/green]")
    else:
        console.print("\n[red]Error generando documentacion con MkDocs.[/red]")
        console.print(result.stderr.strip())
        console.print("[dim]pip install -r requirements-docs.txt[/dim]")


def option_full_test():
    console.print()
    console.print(Panel("Test completo: benchmark + reporte", border_style="magenta"))

    if get_document_count(DOCS_DIR) == 0:
        console.print("[yellow]No existen documentos. Generando...[/yellow]")
        option_generate()

    console.print()
    suite = BenchmarkSuite(DOCS_DIR)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Ejecutando benchmark completo...")
        results = suite.run_full()
        progress.update(task, completed=True)

    _show_benchmark_results(results)

    scalene_results = None
    if ScaleneRunner.is_available():
        console.print()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Ejecutando perfilado con Scalene...")
            runner = ScaleneRunner()
            scalene_results = runner.run_benchmark(DOCS_DIR)
            progress.update(task, completed=True)

        if "error" in scalene_results:
            console.print(f"[yellow]Scalene: {scalene_results['error']}[/yellow]")
        else:
            _show_scalene_results(scalene_results)
    else:
        console.print("[yellow]Scalene no esta instalado. Omitiendo perfilado.[/yellow]")

    reporter = ReportGenerator()
    json_path, md_path = reporter.generate(results, scalene_results)

    console.print()
    console.print(
        Panel(
            Text("Reportes generados", style="bold green", justify="center"),
            border_style="green",
        )
    )
    console.print(f"  [bold]JSON:[/bold] {json_path}")
    console.print(f"  [bold]Markdown:[/bold] {md_path}")


def _show_scalene_results(results: dict):
    console.print()

    resumen_cpu = results.get("resumen_cpu", {})
    resumen_mem = results.get("resumen_memoria", {})

    t_resumen = Table(
        title="Resumen del Perfilado",
        show_header=True,
        header_style="bold yellow",
        border_style="dim",
    )
    t_resumen.add_column("Metrica", style="bold")
    t_resumen.add_column("Valor", justify="center")
    t_resumen.add_row("Tiempo total CPU", f"{resumen_cpu.get('total_seg', 0):.4f}s")
    t_resumen.add_row("Total allocaciones", str(resumen_mem.get("allocaciones", 0)))
    t_resumen.add_row("Total memoria asignada", f"{resumen_mem.get('total_malloc_mb', 0):.2f} MB")
    console.print(t_resumen)
    console.print()

    lineas_calientes = resumen_cpu.get("lineas_calientes", [])
    if lineas_calientes:
        t_hot = Table(
            title="Lineas con Mayor Consumo de CPU",
            show_header=True,
            header_style="bold red",
            border_style="dim",
        )
        t_hot.add_column("#", justify="right", width=3)
        t_hot.add_column("Archivo")
        t_hot.add_column("Linea", justify="center")
        t_hot.add_column("CPU (s)", justify="center")
        t_hot.add_column("Mallocs", justify="center")
        t_hot.add_column("Mem (MB)", justify="center")

        for i, line in enumerate(lineas_calientes[:10], 1):
            t_hot.add_row(
                str(i),
                line["archivo"],
                str(line["linea"]),
                f"{line['cpu_time_seg']:.6f}",
                str(line["mallocs"]),
                f"{line['total_malloc_mb']:.4f}",
            )
        console.print(t_hot)
        console.print()

    archivos = results.get("archivos", {})
    if archivos:
        t_files = Table(
            title="Desglose por Archivo",
            show_header=True,
            header_style="bold cyan",
            border_style="dim",
        )
        t_files.add_column("Archivo", style="bold")
        t_files.add_column("CPU (s)", justify="center")
        t_files.add_column("Mallocs", justify="center")
        t_files.add_column("Mem (MB)", justify="center")

        for fname, finfo in archivos.items():
            t_files.add_row(
                fname,
                f"{finfo['cpu_time_seg']:.4f}",
                str(finfo["mallocs"]),
                f"{finfo['total_malloc_mb']:.4f}",
            )
        console.print(t_files)


def _show_results(results, elapsed: float, title: str, doc_count: int):
    console.print()
    table = Table(title=title, show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("#", style="bold", justify="right", width=4)
    table.add_column("Documento", style="bold")
    table.add_column("Score", justify="center")
    table.add_column("Fragmento")

    for i, r in enumerate(results, 1):
        snippet = r.snippet[:50] + "..." if len(r.snippet) > 50 else r.snippet
        table.add_row(str(i), r.doc_name, f"{r.score:.4f}", snippet)

    console.print(table)
    console.print(f"[dim]Tiempo: {elapsed:.4f}s | Documentos analizados: {doc_count}[/dim]")


def _show_benchmark_results(results: dict):
    console.print()

    idx = results.get("construccion_indice", {})
    table = Table(
        title="Construccion del Indice",
        show_header=True,
        header_style="bold yellow",
        border_style="dim",
    )
    table.add_column("Metodo", style="bold")
    table.add_column("Tiempo (s)", justify="center")
    table.add_column("Documentos", justify="center")
    table.add_column("Memoria pico", justify="center")

    seq = idx.get("secuencial", {})
    inv = idx.get("invertido", {})
    mem_pico = inv.get("memoria_pico_bytes", 0)
    mem_str = f"{mem_pico / 1024:.1f} KB" if mem_pico else "-"

    table.add_row(
        "Secuencial (lectura)",
        f"{seq.get('tiempo_seg', 0):.4f}",
        str(seq.get("documentos", 0)),
        "-",
    )
    table.add_row(
        "Indice invertido",
        f"{inv.get('tiempo_seg', 0):.4f}",
        str(inv.get("documentos", 0)),
        mem_str,
    )

    par = results.get("paralelo", {})
    if par:
        table.add_row(
            f"Paralelo ({par.get('workers', '?')} cores)",
            f"{par.get('tiempo_seg', 0):.4f}",
            str(par.get("documentos", 0)),
            f"Speedup: {par.get('speedup', 0):.2f}x",
        )

    console.print(table)
    console.print()

    consultas = results.get("consultas", [])
    if consultas:
        t_consultas = Table(
            title="Comparacion de Consultas",
            show_header=True,
            header_style="bold cyan",
            border_style="dim",
        )
        t_consultas.add_column("Consulta")
        t_consultas.add_column("Secuencial (s)", justify="center")
        t_consultas.add_column("Indice (s)", justify="center")
        t_consultas.add_column("Mejora", justify="center", style="bold green")

        for c in consultas:
            t_consultas.add_row(
                c["query"],
                f"{c['secuencial']['tiempo_seg']:.6f}",
                f"{c['indice']['tiempo_seg']:.6f}",
                f"{c['mejora_x']:.1f}x",
            )

        console.print(t_consultas)
        console.print()

    cache = results.get("cache", {})
    if cache:
        t_cache = Table(
            title="Cache LRU", show_header=True, header_style="bold magenta", border_style="dim"
        )
        t_cache.add_column("Metrica", style="bold")
        t_cache.add_column("Valor", justify="center")
        t_cache.add_row("Hits", str(cache.get("hits", 0)))
        t_cache.add_row("Misses", str(cache.get("misses", 0)))
        t_cache.add_row("Tasa de acierto", f"{cache.get('hit_rate', 0):.1%}")
        t_cache.add_row("Tiempo promedio hit", f"{cache.get('tiempo_hit_seg', 0):.6f}s")
        t_cache.add_row("Tiempo promedio miss", f"{cache.get('tiempo_miss_seg', 0):.6f}s")
        console.print(t_cache)
        console.print()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        option_full_test()
        return

    while True:
        show_menu()
        choice = console.input("[bold]Seleccione una opcion:[/bold] ").strip()

        if choice == "1":
            option_generate()
        elif choice == "2":
            option_generate_large()
        elif choice == "3":
            option_sequential_search()
        elif choice == "4":
            option_indexed_search()
        elif choice == "5":
            option_cached_search()
        elif choice == "6":
            option_large_file_index()
        elif choice == "7":
            option_benchmark()
        elif choice == "8":
            option_complexity()
        elif choice == "9":
            option_full_test()
        elif choice == "10":
            option_quality()
        elif choice == "11":
            option_profiling()
        elif choice == "12":
            option_docs()
        elif choice == "0":
            console.print("[dim]Saliendo...[/dim]")
            break
        else:
            console.print("[red]Opcion no valida.[/red]")

        console.print()


if __name__ == "__main__":
    main()
