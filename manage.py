#!/usr/bin/env python
"""Wrapper manage.py at project root.

This script changes the working directory to the `backend` folder so
the `backend_project` module is importable, then delegates to the
real `manage.py` in that folder.

If your backend folder is named differently, edit `BACKEND_DIR` below.
"""
import os
import sys
import runpy
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent / "backend"


def main():
    if not BACKEND_DIR.exists():
        print(f"Backend directory not found: {BACKEND_DIR}")
        sys.exit(1)

    # Ensure backend dir is in sys.path and use it as CWD so Django finds
    # the `backend_project` package defined inside `backend`.
    os.chdir(str(BACKEND_DIR))
    sys.path.insert(0, str(BACKEND_DIR))

    runpy.run_path(str(BACKEND_DIR / "manage.py"), run_name="__main__")


if __name__ == "__main__":
    main()
