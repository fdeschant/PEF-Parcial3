# ADR 0003: MkDocs Material como herramienta de documentación externa

## Contexto

El parcial 3 exige documentación externa, versionada y publicada, además de un
pipeline de CI que la construya y valide. El proyecto ya tenía ADR y un glosario
en Markdown, pero no un sitio navegable ni un control automático de enlaces.

## Decisión

Usar **MkDocs** con el tema **Material**, **mkdocstrings** y **Mermaid**:

- Fuente en Markdown dentro de `documentation/`.
- Navegación declarada en `mkdocs.yml`.
- Referencia de API generada desde docstrings de Python.
- Diagramas de arquitectura y flujo en Mermaid.
- Publicación en GitHub Pages desde `main`.

## Alternativas consideradas

| Alternativa | Ventaja | Motivo para descartarla |
|---|---|---|
| Sphinx | Maduro, potente para Python. | Curva de configuración mayor; el equipo ya escribe Markdown. |
| Documento Word/PDF | Formato familiar para la entrega. | No se versiona por página, no se navega ni se valida en CI. |
| Wiki del repositorio | Edición simple. | No vive en el mismo PR ni se construye con el código. |
| MkDocs Material | Markdown, búsqueda, temas, plugins, Pages. | — |

## Consecuencias

### Positivas

- La documentación se revisa en el mismo pull request que el código.
- `mkdocs build --strict` convierte advertencias en errores.
- Lychee valida enlaces internos en cada push.
- La referencia de API no se desincroniza de los docstrings.
- El sitio se publica automáticamente en GitHub Pages.

### Negativas y mitigaciones

- Requiere dependencias adicionales: se fijan en `requirements-docs.txt`.
- `--strict` puede ser ruidoso: se corrige el warning en lugar de desactivarlo.
- La publicación depende de GitHub Pages: el build local sigue siendo la fuente
  de verdad y se archiva como artefacto.

## Estado

Aceptada. La opción 12 del menú construye el sitio localmente con
`python -m mkdocs build --strict`.
