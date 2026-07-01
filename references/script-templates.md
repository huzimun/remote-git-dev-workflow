# Script Templates

Adapt these templates to the project. Keep them small, deterministic, and free of external paid API calls.

## `scripts/remote_update.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCK_FILE="${RUN_LOCK_FILE:-$REPO_ROOT/.run.lock}"
REMOTE_ENV="${REMOTE_ENV:-}"

cd "$REPO_ROOT"

if [[ -e "$LOCK_FILE" ]]; then
  echo "Refusing to update: run lock exists at $LOCK_FILE" >&2
  exit 2
fi

git fetch origin main
git pull --ff-only origin main

if [[ -z "${PROJECT_PYTHON:-}" && -n "$REMOTE_ENV" ]]; then
  for conda_root in "$HOME/anaconda3" "$HOME/miniconda3" "/opt/conda"; do
    if [[ -f "$conda_root/etc/profile.d/conda.sh" ]]; then
      # shellcheck disable=SC1090
      source "$conda_root/etc/profile.d/conda.sh"
      conda activate "$REMOTE_ENV"
      break
    fi
  done
fi

bash eval/run_smoke_test.sh
```

## `eval/run_smoke_test.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

"${PROJECT_PYTHON:-python3}" - <<'PY'
import importlib
import os
import pathlib

root = pathlib.Path.cwd()

required_files = [
    ".gitignore",
    "README.md",
    "requirements.txt",
]

missing = [path for path in required_files if not (root / path).exists()]
if missing:
    raise SystemExit(f"Missing required files: {missing}")

modules = os.environ.get("SMOKE_IMPORT_MODULES", "").split()
for module in modules:
    try:
        importlib.import_module(module)
    except ModuleNotFoundError:
        if os.environ.get("STRICT_SMOKE_IMPORTS", "0") == "1":
            raise
        print(f"warning: skipped import check for {module}")

print("Smoke test passed")
PY
```

## Long-Running Jobs

Wrap long jobs with a lock:

```bash
#!/usr/bin/env bash
set -euo pipefail

LOCK_FILE="${RUN_LOCK_FILE:-.run.lock}"
if [[ -e "$LOCK_FILE" ]]; then
  echo "Another run appears active: $LOCK_FILE" >&2
  exit 2
fi

touch "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# run training or inference here
```
