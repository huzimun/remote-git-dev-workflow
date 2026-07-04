---
name: remote-git-dev-workflow
description: Set up and operate a safe local development + GitHub/GitLab version control + SSH deploy + remote server execution workflow. Use when a user wants Codex or another agent to manage code locally, publish to GitHub/GitLab, sync committed code snapshots to a server by SSH, run code remotely, configure conda or virtualenv environments, exclude datasets/secrets/outputs from Git history, add smoke tests, or prevent remote running jobs from being overwritten.
---

# Remote Git Dev Workflow

## Core Model

Use GitHub/GitLab as the long-term source of truth, and choose the simplest server update mode that the environment supports.

Default mode: **SSH Sync Mode**. Use this when the server cannot reliably access GitHub/GitLab or cannot run Codex CLI login:

```text
local workstation/Codex -> origin: GitHub or GitLab
local committed Git snapshot -> SSH deploy -> remote server runtime
```

Advanced mode: **Server Pull Mode**. Use this only when the server can reliably access the center repository:

```text
local workstation/Codex -> origin: GitHub or GitLab -> remote server runtime
```

In SSH Sync Mode, deploy only a clean local `HEAD` snapshot, never hand-copy individual files. In Server Pull Mode, prefer `git pull --ff-only origin main` on the server, guarded by a run lock and followed by a smoke test. Avoid pushing directly into a checked-out remote worktree except for explicit emergency recovery.

## Required Inputs

Collect or infer these values before changing state:

- `PROJECT_NAME`: repository/project name.
- `LOCAL_DIR`: local working copy path.
- `REMOTE_HOST_ALIAS`: SSH alias such as `gpu-server` or `prod-runner`.
- `REMOTE_PROJECT_DIR`: absolute or shell-expanded server project path.
- `REMOTE_DEPLOY_DIR`: remote deployment base path, such as `~/Deploy/PROJECT_NAME`, for SSH Sync Mode.
- `REMOTE_RUNS_DIR`: remote runs base path, such as `~/Runs/PROJECT_NAME`, for SSH Sync Mode.
- `CENTER_REMOTE_URL`: `git@github.com:OWNER/REPO.git` or GitLab equivalent.
- `DEFAULT_BRANCH`: usually `main`.
- `REMOTE_ENV`: conda/venv name, such as `project-env`, if the server runs code in a managed Python environment.
- Data policy: dataset directories, output directories, model weights, secrets, and which documentation inside data folders should remain tracked.

If any value is missing, inspect local SSH config, Git remotes, repo layout, and remote paths before asking the user.

## Existing Repository Decision Tree

Always inspect the current Git state before changing remotes or history:

```bash
git status --short
git log --oneline -5
git remote -v
git branch --show-current
```

Choose one path:

- **No `.git` directory**: initialize a new repository, add ignore rules, make the first commit, then add the center remote as `origin`.
- **Existing Git history, no center remote**: keep the history if it is clean, add the center remote as `origin`, and set the upstream branch.
- **Existing `origin` already points to the desired GitHub/GitLab repository**: keep `origin`; do not rename it. Only verify branch/upstream settings and history cleanliness.
- **Existing `origin` points to a server worktree, old mirror, or wrong repository**: rename it to `server`, `legacy-origin`, or another descriptive backup name, then add the desired center remote as `origin`.
- **Existing GitHub/GitLab repository is shared or has important history**: do not rewrite history automatically. Scan first, report risks, and ask before any force push or clean-history migration.
- **Existing history contains datasets, secrets, or large forbidden files**: do not push until the user chooses between clean-history publication, history filtering, or keeping the existing private history with rotated secrets.

## Mode Decision Tree

Choose one path before adding scripts or changing server update commands:

- **SSH Sync Mode, default**: local Codex edits a local working copy, local Git/GitHub keeps version history, committed snapshots are deployed to the server by SSH, and the server only runs code. Use this when the server cannot access GitHub/GitLab, cannot log in to Codex CLI, or should not hold credentials beyond SSH.
- **Server Pull Mode, advanced**: local Codex edits locally, pushes to GitHub/GitLab, and the server updates with `git pull --ff-only`. Use this when the server can reliably access GitHub/GitLab and can safely store deploy credentials.
- **Direct file copy, temporary only**: use only for disposable debugging in a temporary directory. Do not copy individual files into the main server worktree for official runs.

## Workflow

1. **Verify SSH first**
   - Confirm `ssh REMOTE_HOST_ALIAS "pwd && hostname"` works.
   - Configure key-based login before automation. Never store plaintext passwords in files or commits.
   - Add `IdentityFile` and `IdentitiesOnly yes` to the host block.

2. **Choose the center remote**
   - Prefer GitHub/GitLab as `origin`.
   - Inspect existing remotes before changing them.
   - Preserve an existing correct `origin`.
   - Keep direct server remotes named `server`, `server-backup`, or similar only for backup/emergency.
   - If converting from direct push-to-server, remove reliance on `receive.denyCurrentBranch=updateInstead`.

3. **Clean Git history before publishing**
   - If the existing repository has datasets, secrets, or huge files in old commits, create a clean history before pushing to the center remote.
   - Do not rely on `git rm --cached` alone when old commits already contain sensitive or large files.
   - Preserve local/remote data on disk as ignored files, not tracked Git content.
   - Treat force pushes and remote resets as destructive operations that require an explicit reason and confirmation.

4. **Write ignore and secret policy**
   - Ignore datasets, outputs, caches, archives, checkpoints, model weights, local environment files, and API keys.
   - Track only allowed documentation inside data directories, such as `**/*.md`, when requested.
   - Replace hardcoded keys in scripts with environment variables and commit a `.env.example` with empty placeholders.
   - Scan staged content and reachable history before pushing.

5. **Create remote update or deploy scripts**
   - Add a lightweight smoke test that does not call external paid APIs and does not require full benchmark data unless explicitly requested.
   - In SSH Sync Mode, add a local deploy script that requires a clean Git tree, archives `HEAD`, deploys it to `REMOTE_DEPLOY_DIR/releases/<commit>`, updates `current`, writes `.deploy_commit`, and runs the smoke test.
   - In Server Pull Mode, add a remote update script that checks a lock file, pulls from `origin`, activates the project runtime environment, and runs the smoke test.
   - Keep a strict mode for full dependency import checks, but make the default smoke portable enough for fresh clones.

6. **Operate the loop**
   - Local agent edits code.
   - Local agent verifies, commits, and pushes to `origin`.
   - SSH Sync Mode: local agent deploys the clean committed snapshot by SSH, then runs on the server from a timestamped run directory.
   - Server Pull Mode: remote server runs `scripts/remote_update.sh`.
   - Long-running jobs create `.run.lock` before starting and remove it only after completion.

## Command Templates

For full command templates, read [references/command-templates.md](references/command-templates.md) when implementing the workflow.

For data/secrets/history rules, read [references/data-secret-policy.md](references/data-secret-policy.md) before touching `.gitignore`, `.env`, or Git history.

For reusable SSH deploy, remote run, `remote_update.sh`, and smoke-test skeletons, read [references/script-templates.md](references/script-templates.md) when adding workflow files to a repository.

## Bundled Scripts

- `scripts/render_workflow_commands.py`: render parameterized command snippets for a new project from a JSON config. Use `mode: "ssh-sync"` or `mode: "server-pull"` to reduce quoting mistakes when preparing a migration plan.

## Safety Rules

- Do not print, commit, or summarize real secrets. Refer to them by variable name.
- Before destructive actions such as deleting old `.git` backups, rewriting history, or resetting a remote worktree, verify exact paths and explain the reason.
- Prefer `git push --force-with-lease` over `git push --force` when history rewrite is required.
- After a history rewrite, update server worktrees once with `git fetch` + controlled reset, then return to `pull --ff-only`.
- In SSH Sync Mode, do not deploy when `git status --short` is non-empty. Commit first so every remote run maps to a GitHub/GitLab commit.
- In SSH Sync Mode, deploy complete `git archive HEAD` snapshots instead of hand-copying individual files.
- Never assume the remote non-interactive shell has conda initialized; explicitly source `conda.sh` or set `PROJECT_PYTHON`.
- Keep generated workflow changes committed separately from unrelated project code unless the user asks for a single initial commit.
