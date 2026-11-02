"""Genera un corpus reproducible para pruebas manuales y benchmarks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DOCS_DIR
from generator import generate_documents, generate_large_documents


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", type=int, default=200)
    parser.add_argument("--large", type=int, default=0)
    parser.add_argument("--words-per-large", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path(DOCS_DIR))
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    generate_documents(args.docs, str(args.output), seed=args.seed)
    if args.large:
        generate_large_documents(
            args.large,
            str(args.output),
            words_per_doc=args.words_per_large,
            seed=args.seed,
        )
    print(
        f"Corpus generado en {args.output}: "
        f"{args.docs} documentos pequeños, {args.large} grandes (seed={args.seed})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
