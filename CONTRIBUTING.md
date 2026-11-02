# Contribuir

## Flujo de trabajo

1. Crear una rama desde `main`: `git switch -c feat/mi-cambio`.
2. Implementar el cambio con pruebas.
3. Ejecutar los mismos controles que CI: `make ci`.
4. Abrir una pull request usando la plantilla del repositorio.
5. Esperar la revisión y los checks obligatorios.

## Controles obligatorios

| Control | Comando |
|---|---|
| Lint | `make lint` |
| Tipos | `make types` |
| Pruebas y cobertura | `make test` |
| Seguridad | `make security` |
| Documentación | `make docs` |
| Rendimiento y memoria | `make perf` |
| Todo | `make ci` |

## Convenciones

- Docstrings y comentarios en español.
- Nombres descriptivos; evitar abreviaturas de una letra.
- Formato PEP 8 validado por Ruff.
- Cada funcionalidad nueva debe incluir pruebas.
- No agregar secretos, credenciales ni archivos generados al repositorio.

## Actualizar la documentación

La documentación vive en `documentation/` y se publica con MkDocs. Si cambia una
interfaz, un umbral, un comando o una decisión de diseño, actualizar la página
correspondiente y ejecutar `make docs`.

## Actualizar líneas base

Los benchmarks y la memoria se comparan contra archivos versionados:

```bash
make baseline
```

Revisar el diff de `benchmarks/baseline.json` y `benchmarks/memory_baseline.json`
antes de commitear. Una actualización de línea base debe explicar por qué el
cambio es esperado.
