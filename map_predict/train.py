"""Training entry placeholder for map_predict.

Phase 0 explicitly forbids training. This file exists so later phases have a
stable entrypoint, but running it now exits before any optimization can start.
"""

from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "map_predict training is disabled in Phase 0. "
        "Generate GT samples and obtain explicit user approval before training."
    )


if __name__ == "__main__":
    main()
