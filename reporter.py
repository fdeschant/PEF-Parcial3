import json
import os
from datetime import datetime

from config import REPORTS_DIR


class ReportGenerator:
    def __init__(self, output_dir: str = REPORTS_DIR):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(
        self, benchmark_results: dict, scalene_results: dict | None = None
    ) -> tuple[str, str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = os.path.join(self.output_dir, f"reporte_{timestamp}.json")
        md_path = os.path.join(self.output_dir, f"reporte_{timestamp}.md")

        export_data = dict(benchmark_results)
        if scalene_results:
            export_data["scalene"] = scalene_results

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self._build_markdown(export_data))

        return json_path, md_path

    def _build_markdown(self, r: dict) -> str:
        lines: list[str] = []
        lines.append("# Reporte de Benchmark - Buscador Eficiente de Informacion\n")

        meta = r.get("consultas", [])
        idx = r.get("construccion_indice", {})
        par = r.get("paralelo", {})
        cache = r.get("cache", {})
        busq = r.get("busqueda_concurrente", {})
        hilos = r.get("busqueda_hilos", {})
        mem = r.get("memoria", {})

        lines.append("## 1. Construccion del Indice\n")
        lines.append("| Metodo | Tiempo (s) | Documentos | Memoria pico |")
        lines.append("|--------|-----------|------------|--------------|")

        seq = idx.get("secuencial", {})
        inv = idx.get("invertido", {})
        lines.append(
            f"| Secuencial (lectura) | {seq.get('tiempo_seg', 0):.4f} "
            f"| {seq.get('documentos', 0)} | - |"
        )
        mem_pico = inv.get("memoria_pico_bytes", 0)
        mem_str = f"{mem_pico / 1024:.1f} KB" if mem_pico else "-"
        lines.append(
            f"| Indice invertido | {inv.get('tiempo_seg', 0):.4f} "
            f"| {inv.get('documentos', 0)} | {mem_str} |"
        )

        if par:
            lines.append(
                f"| Paralelo ({par.get('workers', '?')} cores) "
                f"| {par.get('tiempo_seg', 0):.4f} "
                f"| {par.get('documentos', 0)} "
                f"| Speedup: {par.get('speedup', 0):.2f}x |"
            )

        lines.append("")
        lines.append("## 2. Comparacion de Consultas\n")
        lines.append("| Consulta | Secuencial (s) | Indice (s) | Mejora |")
        lines.append("|----------|----------------|------------|--------|")

        for c in meta:
            lines.append(
                f"| {c['query']} "
                f"| {c['secuencial']['tiempo_seg']:.6f} "
                f"| {c['indice']['tiempo_seg']:.6f} "
                f"| {c['mejora_x']:.1f}x |"
            )

        if cache:
            lines.append("")
            lines.append("## 3. Cache\n")
            lines.append("| Metrica | Valor |")
            lines.append("|---------|-------|")
            lines.append(f"| Queries capturadas | {cache.get('queries_capturadas', 0)} |")
            lines.append(f"| Queries futuras | {cache.get('queries_futuras', 0)} |")
            lines.append(f"| Hits | {cache.get('hits', 0)} |")
            lines.append(f"| Misses | {cache.get('misses', 0)} |")
            lines.append(f"| Hit rate | {cache.get('hit_rate', 0):.1%} |")
            lines.append(f"| Tiempo promedio hit | {cache.get('tiempo_hit_seg', 0) * 1e9:.0f}ns |")
            lines.append(
                f"| Tiempo promedio miss | {cache.get('tiempo_miss_seg', 0) * 1e6:.2f}us |"
            )

        if busq:
            lines.append("")
            lines.append("## 6.1 Busqueda Concurrente\n")
            lines.append("| Metrica | Secuencial | Paralelo |")
            lines.append("|---------|-----------|----------|")
            lines.append(
                f"| Tiempo total | {busq.get('secuencial', {}).get('tiempo_total_seg', 0):.6f}s "
                f"| {busq.get('paralelo', {}).get('tiempo_total_seg', 0):.6f}s |"
            )
            lines.append(
                f"| Queries | {busq.get('secuencial', {}).get('queries', 0)} "
                f"| {busq.get('paralelo', {}).get('queries', 0)} |"
            )
            lines.append(f"| Workers | 1 | {busq.get('paralelo', {}).get('workers', 0)} |")
            lines.append(f"| Speedup | 1.0x | {busq.get('speedup_x', 0):.2f}x |")

        if hilos:
            lines.append("")
            lines.append("## 6.2 Busqueda con Hilos\n")
            lines.append("| Metrica | Secuencial | Hilos (16 workers) |")
            lines.append("|---------|-----------|-------------------|")
            lines.append(
                f"| Tiempo total | {hilos.get('secuencial', {}).get('tiempo_total_seg', 0):.6f}s "
                f"| {hilos.get('hilos', {}).get('tiempo_total_seg', 0):.6f}s |"
            )
            lines.append(
                f"| Queries | {hilos.get('secuencial', {}).get('queries', 0)} "
                f"| {hilos.get('hilos', {}).get('queries', 0)} |"
            )
            lines.append(f"| Workers | 1 | {hilos.get('hilos', {}).get('workers', 0)} |")
            lines.append(f"| Speedup | 1.0x | {hilos.get('speedup_x', 0):.2f}x |")

        lines.append("")
        lines.append("## 4. Analisis de Complejidad\n")
        lines.append("| Operacion | Complejidad | Descripcion |")
        lines.append("|-----------|-------------|-------------|")
        lines.append("| Construccion secuencial | O(1) | No construye indice |")
        lines.append("| Construccion indice | O(D x W) | D=docs, W=palabras/doc |")
        lines.append("| Construccion paralela | O(D x W / P) | P=procesadores |")
        lines.append("| Consulta secuencial | O(D x W) | Recorre todo |")
        lines.append("| Consulta indexada | O(k x L_min) | k=terminos, L_min=postings mas corto |")
        lines.append("| Consulta concurrente | O(N x k x L_min / P) | N=queries, P=procesadores |")
        lines.append("| Cache get | O(1) | OrderedDict |")
        lines.append("| Cache put | O(1) | OrderedDict |")
        lines.append("| Ranking heap | O(N x log K) | N=resultados, K=top K |")

        if mem:
            lines.append("")
            lines.append("## 5. Estadisticas del Indice\n")
            lines.append(f"- **Terminos en vocabulario:** {mem.get('indice_terminos', 0)}")
            lines.append(f"- **Documentos indexados:** {mem.get('indice_documentos', 0)}")

        scalene = r.get("scalene", {})
        if scalene and "error" not in scalene:
            lines.append("")
            lines.append("## 6. Perfilado con Scalene\n")

            resumen_cpu = scalene.get("resumen_cpu", {})
            resumen_mem = scalene.get("resumen_memoria", {})
            lines.append(f"- **Tiempo total CPU:** {resumen_cpu.get('total_seg', 0):.4f}s")
            lines.append(f"- **Total allocaciones:** {resumen_mem.get('allocaciones', 0)}")
            lines.append(
                f"- **Total memoria asignada:** {resumen_mem.get('total_malloc_mb', 0):.2f} MB"
            )

            lineas_calientes = resumen_cpu.get("lineas_calientes", [])
            if lineas_calientes:
                lines.append("")
                lines.append("### Lineas con mayor consumo de CPU\n")
                lines.append("| # | Archivo | Linea | CPU (s) | Mallocs | Mem (MB) |")
                lines.append("|---|---------|-------|---------|---------|----------|")
                for i, line in enumerate(lineas_calientes[:10], 1):
                    lines.append(
                        f"| {i} | {line['archivo']} | {line['linea']} "
                        f"| {line['cpu_time_seg']:.6f} | {line['mallocs']} "
                        f"| {line['total_malloc_mb']:.4f} |"
                    )

            archivos = scalene.get("archivos", {})
            if archivos:
                lines.append("")
                lines.append("### Desglose por Archivo\n")
                lines.append("| Archivo | CPU (s) | Mallocs | Mem (MB) |")
                lines.append("|---------|---------|---------|----------|")
                for fname, finfo in archivos.items():
                    lines.append(
                        f"| {fname} | {finfo['cpu_time_seg']:.4f} "
                        f"| {finfo['mallocs']} | {finfo['total_malloc_mb']:.4f} |"
                    )

        lines.append("")
        lines.append("---")
        lines.append(
            f"*Generado automaticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        )

        return "\n".join(lines)
