"""Run the project modules in order, starting with the university importer."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# Add later module entry points here, in the order they should run.
MODULES = (
    ("module-1", PROJECT_ROOT / "app" / "module-1" / "import_universities.py"),
)


def main():
    arguments = sys.argv[1:]
    for module_name, module_path in MODULES:
        if not module_path.is_file():
            print(f"Cannot run {module_name}: entry point not found at {module_path}.", file=sys.stderr)
            return 1

        result = subprocess.run(
            [sys.executable, str(module_path), *arguments],
            cwd=PROJECT_ROOT,
            check=False,
        )
        if result.returncode:
            print(f"Stopping because {module_name} failed.", file=sys.stderr)
            return result.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
