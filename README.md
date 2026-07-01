# Remote Git Dev Workflow

[中文文档](README.zh-CN.md)

Remote Git Dev Workflow is a Codex skill for setting up a safe collaboration loop between a local development machine, a GitHub or GitLab center repository, and a remote server runtime environment.

It is designed for projects where an agent edits code locally, publishes changes through Git, and runs or validates the project on a remote machine such as a GPU server.

## When To Use

Use this skill when you need to:

- Configure SSH access and key-based login for a remote server.
- Move from direct server editing to local development with Git.
- Create or migrate a GitHub/GitLab-centered repository workflow.
- Keep datasets, outputs, model weights, archives, and secrets out of Git history.
- Replace hardcoded API keys with environment variables and `.env.example`.
- Add a lightweight smoke test for remote validation.
- Add a remote update script that uses `git pull --ff-only`.
- Protect long-running remote jobs with a `.run.lock` file.

## Installation

Copy this repository into the Codex skills directory for the user that should use it:

```text
~/.codex/skills/remote-git-dev-workflow
```

On Windows, the equivalent path is usually:

```text
C:\Users\<user>\.codex\skills\remote-git-dev-workflow
```

After installation, restart or reload Codex if needed so the skill can be discovered.

## Usage

You can invoke the skill explicitly:

```text
Use $remote-git-dev-workflow to set up a local development, GitHub, and remote server workflow for this project.
```

Codex may also use it implicitly when the task involves SSH setup, remote development, GitHub/GitLab repository migration, remote runtime updates, data exclusion rules, smoke tests, or run locks.

## Workflow Model

The skill recommends using a center repository as the source of truth:

```text
local workstation/Codex -> origin: GitHub or GitLab -> remote server runtime
```

The remote server should normally update by pulling from the center repository:

```bash
git pull --ff-only origin main
```

Direct pushes into a checked-out remote worktree should be reserved for explicit emergency recovery.

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
