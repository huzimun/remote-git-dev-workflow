# Script Templates

Adapt these templates to the project. Keep them small, deterministic, and free of external paid API calls.

## `scripts/deploy_via_ssh.ps1`

Use this from the local workstation in SSH Sync Mode. It deploys the exact committed `HEAD` snapshot and refuses dirty working trees.

```powershell
param(
  [string]$LocalDir = ".",
  [string]$RemoteHost = "REMOTE_HOST_ALIAS",
  [string]$RemoteDeployDir = "~/Deploy/PROJECT_NAME",
  [string]$RemoteEnv = "REMOTE_ENV",
  [string]$SmokeCommand = "bash eval/run_smoke_test.sh"
)

$ErrorActionPreference = "Stop"

$status = git -C $LocalDir status --short
if ($status) {
  Write-Error "Refusing to deploy: commit or discard local changes first."
  exit 2
}

$commit = (git -C $LocalDir rev-parse --short=12 HEAD).Trim()
$release = "$RemoteDeployDir/releases/$commit"

ssh $RemoteHost "mkdir -p '$release'"
git -C $LocalDir archive --format=tar HEAD |
  ssh $RemoteHost "tar -xf - -C '$release' && printf '%s\n' '$commit' > '$release/.deploy_commit' && ln -sfn '$release' '$RemoteDeployDir/current'"

ssh $RemoteHost "cd '$RemoteDeployDir/current' && DEPLOY_COMMIT='$commit' REMOTE_ENV='$RemoteEnv' $SmokeCommand"
Write-Host "Deployed $commit to $RemoteHost:$RemoteDeployDir/current"
```

## `scripts/run_remote_release.sh`

Use this on the remote server from `REMOTE_DEPLOY_DIR/current`. It copies the deployed snapshot into a timestamped run directory and writes run metadata.

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="${PROJECT_NAME:-PROJECT_NAME}"
REMOTE_RUNS_DIR="${REMOTE_RUNS_DIR:-$HOME/Runs/$PROJECT_NAME}"
REMOTE_ENV="${REMOTE_ENV:-}"
RUN_COMMAND="${RUN_COMMAND:-bash eval/run_smoke_test.sh}"
LOCK_FILE="${RUN_LOCK_FILE:-.run.lock}"

RELEASE_DIR="$(pwd)"
COMMIT="$(cat "$RELEASE_DIR/.deploy_commit" 2>/dev/null || git rev-parse --short=12 HEAD 2>/dev/null || echo unknown)"
STAMP="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="$REMOTE_RUNS_DIR/$STAMP-$COMMIT"

if [[ -e "$RELEASE_DIR/$LOCK_FILE" ]]; then
  echo "Another run appears active: $RELEASE_DIR/$LOCK_FILE" >&2
  exit 2
fi

touch "$RELEASE_DIR/$LOCK_FILE"
trap 'rm -f "$RELEASE_DIR/$LOCK_FILE"' EXIT

mkdir -p "$RUN_DIR"
tar -cf - -C "$RELEASE_DIR" . | tar -xf - -C "$RUN_DIR"

cat > "$RUN_DIR/RUN_METADATA.md" <<EOF
# Run Metadata

- project: $PROJECT_NAME
- commit: $COMMIT
- release_dir: $RELEASE_DIR
- run_dir: $RUN_DIR
- conda_env: ${REMOTE_ENV:-unset}
- command: $RUN_COMMAND
- started_at: $(date -Iseconds)
EOF

cd "$RUN_DIR"

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

eval "$RUN_COMMAND"
```

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
