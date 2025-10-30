#!/usr/bin/env python3
"""Fail if docs include direct Alembic downgrade commands.

This enforces the forward-only migrations policy in documentation.
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    docs_dir = Path("docs")
    if not docs_dir.exists():
        return 0

    offending: list[str] = []
    for path in docs_dir.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if "alembic downgrade" in text:
            offending.append(str(path))

    if offending:
        print("Disallowed Alembic downgrade command found in docs:")
        for p in offending:
            print(f" - {p}")
        print("\nUse forward-only guidance: create corrective migration or restore via backups/PITR.")
        return 1

    print("Docs check passed: no downgrade commands found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


