---
name: remote-git-dev-workflow
description: Set up and operate a safe local development + GitHub/GitLab center repository + remote server execution workflow. Use when a user wants Codex or another agent to connect to a server by SSH, clone or rebuild a project locally, create or migrate a GitHub/GitLab repository, exclude datasets/secrets/outputs from Git history, push local code changes, pull/update a remote runtime workspace, configure conda or virtualenv environments, add smoke tests, or prevent remote running jobs from being overwritten.
---

# Remote Git Dev Workflow

## Core Model

Use a center repository as the source of truth:

```text
local workstation/Codex -> origin: GitHub or GitLab -> remote server runtime
```

Avoid pushing directly into a checked-out remote worktree except for explicit emergency recovery. Prefer `git pull --ff-only origin main` on the server, guarded by a run lock and followed by a smoke test.

## Required Inputs

Collect or infer these values before changing state:

- `PROJECT_NAME`: repository/project name.
- `LOCAL_DIR`: local working copy path.
- `REMOTE_HOST_ALIAS`: SSH alias such as `gpu-server` or `prod-runner`.
- `REMOTE_PROJECT_DIR`: absolute or shell-expanded server project path.
- `CENTER_REMOTE_URL`: `git@github.com:OWNER/REPO.git` or GitLab equivalent.
- `DEFAULT_BRANCH`: usually `main`.
- `REMOTE_ENV`: conda/venv name, such as `project-env`, if the server runs code in a managed Python environment.
- Data policy: dataset directories, output directories, model weights, secrets, and which documentation inside data folders should remain tracked.

If any value is missing, inspect local SSH config, Git remotes, repo layout, and remote paths before asking the user.

## Workflow

1. **Verify SSH first**
   - Confirm `ssh REMOTE_HOST_ALIAS "pwd && hostname"` works.
   - Configure key-based login before automation. Never store plaintext passwords in files or commits.
   - Add `IdentityFile` and `IdentitiesOnly yes` to the host block.

2. **Choose the center remote**
   - Prefer GitHub/GitLab as `origin`.
   - Keep direct server remotes named `server`, `a800`, or similar only for backup/emergency.
   - If converting from direct push-to-server, remove reliance on `receive.denyCurrentBranch=updateInstead`.

3. **Clean Git history before publishing**
   - If the existing repository has datasets, secrets, or huge files in old commits, create a clean history before pushing to the center remote.
   - Do not rely on `git rm --cached` alone when old commits already contain sensitive or large files.
   - Preserve local/remote data on disk as ignored files, not tracked Git content.

4. **Write ignore and secret policy**
   - Ignore datasets, outputs, caches, archives, checkpoints, model weights, local environment files, and API keys.
   - Track only allowed documentation inside data directories, such as `**/*.md`, when requested.
   - Replace hardcoded keys in scripts with environment variables and commit a `.env.example` with empty placeholders.
   - Scan staged content and reachable history before pushing.

5. **Create remote update and smoke test**
   - Add a lightweight smoke test that does not call external paid APIs and does not require full benchmark data unless explicitly requested.
   - Add a remote update script that checks a lock file, pulls from `origin`, activates the project runtime environment, and runs the smoke test.
   - Keep a strict mode for full dependency import checks, but make the default smoke portable enough for fresh clones.

6. **Operate the loop**
   - Local agent edits code.
   - Local agent verifies, commits, and pushes to `origin`.
   - Remote server runs `scripts/remote_update.sh`.
   - Long-running jobs create `.run.lock` before starting and remove it only after completion.

## Command Templates

For full command templates, read [references/command-templates.md](references/command-templates.md) when implementing the workflow.

For data/secrets/history rules, read [references/data-secret-policy.md](references/data-secret-policy.md) before touching `.gitignore`, `.env`, or Git history.

For reusable `remote_update.sh` and smoke-test skeletons, read [references/script-templates.md](references/script-templates.md) when adding workflow files to a repository.

## Bundled Scripts

- `scripts/render_workflow_commands.py`: render parameterized command snippets for a new project from a JSON config. Use it to reduce quoting mistakes when preparing a migration plan.

## Safety Rules

- Do not print, commit, or summarize real secrets. Refer to them by variable name.
- Before destructive actions such as deleting old `.git` backups, rewriting history, or resetting a remote worktree, verify exact paths and explain the reason.
- Prefer `git push --force-with-lease` over `git push --force` when history rewrite is required.
- After a history rewrite, update server worktrees once with `git fetch` + controlled reset, then return to `pull --ff-only`.
- Never assume the remote non-interactive shell has conda initialized; explicitly source `conda.sh` or set `PROJECT_PYTHON`.
- Keep generated workflow changes committed separately from unrelated project code unless the user asks for a single initial commit.
