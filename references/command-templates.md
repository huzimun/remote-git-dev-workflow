# Command Templates

Use placeholders literally until project-specific values are confirmed:

- `REMOTE_HOST_ALIAS`: SSH alias, for example `gpu-server`.
- `REMOTE_PROJECT_DIR`: remote project path.
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

Local remotes:

```powershell
git -C LOCAL_DIR remote rename origin server
git -C LOCAL_DIR remote add origin CENTER_REMOTE_URL
git -C LOCAL_DIR branch -M DEFAULT_BRANCH
```

Server remote:

```bash
cd REMOTE_PROJECT_DIR
git remote set-url origin CENTER_REMOTE_URL || git remote add origin CENTER_REMOTE_URL
git fetch origin DEFAULT_BRANCH
git branch --set-upstream-to=origin/DEFAULT_BRANCH DEFAULT_BRANCH
```

## Clean History

Use when existing commits contain data or secrets:

```powershell
git -C LOCAL_DIR checkout --orphan clean-main
git -C LOCAL_DIR reset
git -C LOCAL_DIR add .
git -C LOCAL_DIR commit -m "Initialize PROJECT_NAME repository"
git -C LOCAL_DIR branch -M DEFAULT_BRANCH
git -C LOCAL_DIR push --force-with-lease origin DEFAULT_BRANCH
```

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

## Operation

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
