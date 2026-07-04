# Remote Git Dev Workflow

[中文文档](README.zh-CN.md)

Remote Git Dev Workflow is a Codex skill for setting up a safe collaboration loop between a local development machine, GitHub or GitLab version control, SSH deployment, and a remote server runtime environment.

It is designed for projects where an agent edits code locally, keeps history in GitHub or GitLab, and runs or validates the project on a remote machine such as a GPU server.

## When To Use

Use this skill when you need to:

- Configure SSH access and key-based login for a remote server.
- Move from direct server editing to local development with Git.
- Create or migrate a GitHub/GitLab-centered repository workflow.
- Keep datasets, outputs, model weights, archives, and secrets out of Git history.
- Replace hardcoded API keys with environment variables and `.env.example`.
- Add a lightweight smoke test for remote validation.
- Deploy clean committed snapshots to a server by SSH when the server cannot access GitHub/GitLab.
- Add a remote update script that uses `git pull --ff-only` when the server can access GitHub/GitLab.
- Protect long-running remote jobs with a `.run.lock` file.

## Installation

Recommended: ask Codex to install the skill from GitHub with the built-in `skill-installer` skill.

Use this prompt in Codex:

```text
Use $skill-installer to install the skill from this GitHub repository:
https://github.com/huzimun/remote-git-dev-workflow.git

Install it as remote-git-dev-workflow, prefer the git install method, and verify that SKILL.md, agents/, references/, and scripts/ are all present after installation.
```

Codex should install it into the current user's skills directory:

```text
~/.codex/skills/remote-git-dev-workflow
```

On Windows, the equivalent path is usually:

```text
C:\Users\<user>\.codex\skills\remote-git-dev-workflow
```

If you install manually instead, clone the full repository into that directory. Do not copy only the root files; the `references/` and `scripts/` directories are part of the skill.

After installation, check that these files and directories exist:

```text
SKILL.md
agents/
references/
scripts/
```

If an installer produced a partial checkout that only contains root files, reinstall with the git method or disable sparse checkout in that skill directory:

```bash
git sparse-checkout disable
```

After installation, restart or reload Codex if needed so the skill can be discovered.

## Usage

You can invoke the skill explicitly:

```text
Use $remote-git-dev-workflow to set up a local development, GitHub, and remote server workflow for this project.
```

Codex may also use it implicitly when the task involves SSH setup, remote development, GitHub/GitLab repository migration, remote runtime updates, data exclusion rules, smoke tests, or run locks.

## Workflow Model

The skill supports two modes.

**SSH Sync Mode** is the recommended default:

```text
local workstation/Codex -> origin: GitHub or GitLab
local committed Git snapshot -> SSH deploy -> remote server runtime
```

Use it when the server cannot reliably access GitHub/GitLab or cannot log in to Codex CLI. The server only needs SSH, bash, tar, and the project runtime environment.

**Server Pull Mode** preserves the original workflow:

```text
local workstation/Codex -> origin: GitHub or GitLab -> remote server runtime
```

Use it when the server can reliably access the center repository. The remote server updates by pulling from the center repository:

```bash
git pull --ff-only origin main
```

Direct pushes into a checked-out remote worktree should be reserved for explicit emergency recovery.

## How Should Code Reach The Server?

For the default SSH Sync Mode, use GitHub or GitLab for version history and SSH for server deployment:

```text
edit locally -> commit locally -> push to GitHub/GitLab -> deploy committed snapshot by SSH -> run on the server
```

This keeps every server run tied to a Git commit without requiring the server to access GitHub/GitLab or log in to Codex.

A typical flow looks like this:

```bash
git add .
git commit -m "Describe the change"
git push origin main
powershell -ExecutionPolicy Bypass -File scripts/deploy_via_ssh.ps1
ssh REMOTE_HOST_ALIAS "cd ~/Deploy/PROJECT_NAME/current && bash scripts/run_remote_release.sh"
```

Use Server Pull Mode only when the server can reach GitHub/GitLab reliably:

```text
edit locally -> commit locally -> push to GitHub/GitLab -> pull on the server -> run on the server
```

Avoid hand-copying individual files into the main server directory. It can leave mixed versions on the server and make it unclear which code version produced a result.

Recommended rule of thumb:

- Use **SSH Sync Mode** for servers that cannot access GitHub/GitLab or Codex login reliably.
- Use **Server Pull Mode** when the server has stable GitHub/GitLab access and deploy credentials.
- Use complete **Git snapshots**, not individual `scp` copies, for official runs.
- Use a **run lock** before long-running jobs so the server code is not updated while a job is still using it.
- Use **branches or pull requests** when multiple people or agents may edit the same project.

## Repository Structure

```text
SKILL.md
agents/
  openai.yaml
references/
  command-templates.md
  data-secret-policy.md
  script-templates.md
scripts/
  render_workflow_commands.py
```

- `SKILL.md` contains the core workflow and safety rules.
- `agents/openai.yaml` provides Codex UI metadata.
- `references/command-templates.md` contains reusable SSH, Git, and remote update command templates.
- `references/data-secret-policy.md` documents ignore rules, secret handling, and pre-push checks.
- `references/script-templates.md` contains skeletons for `remote_update.sh`, smoke tests, and run locks.
- `scripts/render_workflow_commands.py` renders project-specific command snippets from a JSON config.

## Safety Notes

- Do not commit real secrets, `.env` files, SSH private keys, API keys, tokens, or passwords.
- Do not upload datasets, generated outputs, model checkpoints, or large binary artifacts unless the project explicitly uses a suitable storage strategy.
- If sensitive files or large data were already committed, create a clean Git history before publishing to GitHub or GitLab.
- Use `git push --force-with-lease`, not plain `git push --force`, when a history rewrite is required.
- Use a remote run lock, such as `.run.lock`, to avoid updating code while a long-running job is active.
- Do not assume a remote non-interactive SSH shell has conda initialized; explicitly activate the environment or set `PROJECT_PYTHON`.

## License

No license has been declared yet. Add a `LICENSE` file before publishing this repository as open source.
