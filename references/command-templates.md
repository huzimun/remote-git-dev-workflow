# Command Templates

Use placeholders literally until project-specific values are confirmed:

- `REMOTE_HOST_ALIAS`: SSH alias, for example `gpu-server`.
- `REMOTE_PROJECT_DIR`: remote project path.
- `REMOTE_DEPLOY_DIR`: remote deploy base path, for example `~/Deploy/PROJECT_NAME`.
- `REMOTE_RUNS_DIR`: remote runs base path, for example `~/Runs/PROJECT_NAME`.
- `LOCAL_DIR`: local project path.
- `CENTER_REMOTE_URL`: GitHub/GitLab SSH URL.
- `DEFAULT_BRANCH`: usually `main`.
- `REMOTE_ENV`: conda/venv environment name.

## SSH

Create a local key:

```powershell
ssh-keygen -t ed25519 -C "<user-or-project label>" -f "$env:USERPROFILE\.ssh\<key_name>"
```

SSH config:

```sshconfig
Host REMOTE_HOST_ALIAS
  HostName <server-ip-or-dns>
  Port <port>
  User <user>
  IdentityFile ~/.ssh/<key_name>
  IdentitiesOnly yes
```

Verify no password prompt:

```powershell
ssh -o BatchMode=yes REMOTE_HOST_ALIAS "echo ok && hostname"
```

## Center Remote

Inspect first:

```powershell
git -C LOCAL_DIR status --short
git -C LOCAL_DIR log --oneline -5
git -C LOCAL_DIR remote -v
git -C LOCAL_DIR branch --show-current
```

If there is no Git repository yet:

```powershell
git -C LOCAL_DIR init
git -C LOCAL_DIR branch -M DEFAULT_BRANCH
git -C LOCAL_DIR add .
git -C LOCAL_DIR commit -m "Initialize PROJECT_NAME repository"
git -C LOCAL_DIR remote add origin CENTER_REMOTE_URL
git -C LOCAL_DIR push -u origin DEFAULT_BRANCH
```

If `origin` already points to `CENTER_REMOTE_URL`, keep it:

```powershell
git -C LOCAL_DIR remote -v
git -C LOCAL_DIR branch -M DEFAULT_BRANCH
git -C LOCAL_DIR branch --set-upstream-to=origin/DEFAULT_BRANCH DEFAULT_BRANCH
```

If there is no `origin` remote:

```powershell
git -C LOCAL_DIR remote add origin CENTER_REMOTE_URL
git -C LOCAL_DIR push -u origin DEFAULT_BRANCH
```

If `origin` points to a server worktree, old mirror, or wrong repository, preserve it under a backup name before adding the center remote:

```powershell
git -C LOCAL_DIR remote rename origin legacy-origin
git -C LOCAL_DIR remote add origin CENTER_REMOTE_URL
git -C LOCAL_DIR branch -M DEFAULT_BRANCH
git -C LOCAL_DIR push -u origin DEFAULT_BRANCH
```

Server remote:

```bash
cd REMOTE_PROJECT_DIR
git remote set-url origin CENTER_REMOTE_URL || git remote add origin CENTER_REMOTE_URL
git fetch origin DEFAULT_BRANCH
git branch --set-upstream-to=origin/DEFAULT_BRANCH DEFAULT_BRANCH
```

## Clean History

Use only when existing commits contain data or secrets and the user has accepted a clean-history migration:

```powershell
git -C LOCAL_DIR checkout --orphan clean-main
git -C LOCAL_DIR reset
git -C LOCAL_DIR add .
git -C LOCAL_DIR commit -m "Initialize PROJECT_NAME repository"
git -C LOCAL_DIR branch -M DEFAULT_BRANCH
git -C LOCAL_DIR push --force-with-lease origin DEFAULT_BRANCH
```

Do not use the clean-history flow automatically when the target GitHub/GitLab repository is shared, public, or already has important history. In those cases, scan and report the problem first.

After a clean-history force push, update the server once:

```bash
cd REMOTE_PROJECT_DIR
git fetch origin DEFAULT_BRANCH
git reset --hard origin/DEFAULT_BRANCH
```

Then return to normal updates:

```bash
cd REMOTE_PROJECT_DIR
git pull --ff-only origin DEFAULT_BRANCH
```

## Remote Environment

Conda activation in non-interactive SSH shells:

```bash
for conda_root in "$HOME/anaconda3" "$HOME/miniconda3" "/opt/conda"; do
  if [ -f "$conda_root/etc/profile.d/conda.sh" ]; then
    . "$conda_root/etc/profile.d/conda.sh"
    conda activate REMOTE_ENV
    break
  fi
done
```

Smoke test with an explicit Python:

```bash
PROJECT_PYTHON=/path/to/env/bin/python bash eval/run_smoke_test.sh
```

## SSH Sync Mode Operation

Use this mode when the server cannot reliably access GitHub/GitLab. It deploys the exact local `HEAD` snapshot over SSH.

Local publish:

```powershell
git -C LOCAL_DIR status --short
git -C LOCAL_DIR add .
git -C LOCAL_DIR commit -m "<message>"
git -C LOCAL_DIR push origin DEFAULT_BRANCH
```

Require a clean tree before deployment:

```powershell
$status = git -C LOCAL_DIR status --short
if ($status) {
  Write-Error "Refusing to deploy: commit or discard local changes first."
  exit 2
}
```

Deploy `HEAD` to a release directory:

```powershell
$commit = git -C LOCAL_DIR rev-parse --short=12 HEAD
$release = "REMOTE_DEPLOY_DIR/releases/$commit"
ssh REMOTE_HOST_ALIAS "mkdir -p '$release'"
git -C LOCAL_DIR archive --format=tar HEAD | ssh REMOTE_HOST_ALIAS "tar -xf - -C '$release' && printf '%s\n' '$commit' > '$release/.deploy_commit' && ln -sfn '$release' 'REMOTE_DEPLOY_DIR/current'"
```

Run the smoke test after deployment:

```powershell
ssh REMOTE_HOST_ALIAS "cd REMOTE_DEPLOY_DIR/current && bash eval/run_smoke_test.sh"
```

Create a timestamped run directory and run from it:

```powershell
ssh REMOTE_HOST_ALIAS "cd REMOTE_DEPLOY_DIR/current && bash scripts/run_remote_release.sh"
```

## Server Pull Mode Operation

Use this mode when the server can reliably access GitHub/GitLab and holds deploy credentials.

Local publish:

```powershell
git -C LOCAL_DIR status --short
git -C LOCAL_DIR add .
git -C LOCAL_DIR commit -m "<message>"
git -C LOCAL_DIR push origin DEFAULT_BRANCH
```

Remote update:

```powershell
ssh REMOTE_HOST_ALIAS "cd REMOTE_PROJECT_DIR && bash scripts/remote_update.sh"
```

Run-lock check:

```bash
cd REMOTE_PROJECT_DIR
test -e .run.lock && { echo "running job lock exists"; exit 2; }
```
