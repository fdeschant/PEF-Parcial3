COMPLEXITY_ANALYSIS = {
    "construccion": {
        "secuencial": {
            "complejidad": "O(1)",
            "descripcion": "No construye indice. Cada consulta lee todos los archivos.",
        },
        "indice_invertido": {
            "complejidad": "O(D x W)",
            "descripcion": (
                "D = cantidad de documentos, W = palabras promedio por documento. "
                "Se recorre cada documento una sola vez para construir el indice."
            ),
        },
        "paralelo": {
            "complejidad": "O(D x W / P)",
            "descripcion": (
                "P = cantidad de procesadores. La construccion se divide en chunks "
                "iguales. El merge final agrega O(V x L) donde V = tamano del "
                "vocabulario y L = largo promedio de listas de postings."
            ),
        },
    },
    "consulta": {
        "secuencial": {
            "complejidad": "O(D x W)",
            "descripcion": (
                "Cada consulta recorre todos los documentos (D) y verifica "
                "presencia de cada termino de la consulta en cada documento (W)."
            ),
        },
        "indice_invertido": {
            "complejidad": "O(k x L_min)",
            "descripcion": (
                "k = cantidad de terminos en la consulta, L_min = largo de la "
                "lista de postings mas corta. La interseccion de conjuntos "
                "reduce dramaticamente el espacio de busqueda."
            ),
        },
    },
    "caché": {
        "get": {
            "complejidad": "O(1)",
            "descripcion": (
                "Acceso directo al OrderedDict mas actualizacion de orden en O(1) amortizado."
            ),
        },
        "put": {
            "complejidad": "O(1)",
            "descripcion": ("Insercion y eviction LRU en O(1) amortizado via OrderedDict."),
        },
    },
    "ranking": {
        "heap": {
            "complejidad": "O(N x log K)",
            "descripcion": (
                "N = cantidad de resultados, K = top K a retornar. "
                "El heap de tamano K evita ordenar toda la lista."
            ),
        },
        "sort_completo": {
            "complejidad": "O(N x log N)",
            "descripcion": "Ordenamiento completo de todos los resultados.",
        },
    },
}


def print_complexity_analysis(console=None):
    if console is None:
        _print_plain()
    else:
        _print_rich(console)


def _print_plain():
    print("\n" + "=" * 60)
    print("  ANALISIS DE COMPLEJIDAD ALGORITMICA")
    print("=" * 60)

    for seccion, items in COMPLEXITY_ANALYSIS.items():
        print(f"\n--- {seccion.upper()} ---")
        for nombre, datos in items.items():
            print(f"  {nombre}: {datos['complejidad']}")
            print(f"    {datos['descripcion']}")


def _print_rich(console):
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    console.print()
    console.print(
        Panel(
            Text("Analisis de Complejidad Algoritmica", style="bold cyan", justify="center"),
            border_style="cyan",
        )
    )

    section_titles = {
        "construccion": "Construccion del Indice",
        "consulta": "Consulta / Busqueda",
        "caché": "Cache LRU",
        "ranking": "Ranking con Heap",
    }

    for seccion, items in COMPLEXITY_ANALYSIS.items():
        table = Table(
            title=section_titles.get(seccion, seccion),
            show_header=True,
            header_style="bold yellow",
            border_style="dim",
        )
        table.add_column("Operacion", style="bold")
        table.add_column("Complejidad", style="green", justify="center")
        table.add_column("Descripcion")

        for nombre, datos in items.items():
            table.add_row(nombre, datos["complejidad"], datos["descripcion"])

        console.print(table)
        console.print()
