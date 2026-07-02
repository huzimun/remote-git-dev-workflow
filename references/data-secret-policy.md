# Data And Secret Policy

## Gitignore Baseline

Start from this policy and adapt to the project:

```gitignore
# Runtime outputs
logs/
output/
outputs/
runs/
checkpoints/
wandb/
tensorboard/
tmp/
temp/
.cache/

# Secrets and local environment
.env
.env.*
!.env.example

# Model/checkpoint/data artifacts
*.pt
*.pth
*.ckpt
*.safetensors
*.pkl
*.pickle
*.npy
*.npz
*.parquet
*.arrow
*.bin
*.onnx

# Archives
*.zip
*.tar
*.tar.gz
*.tgz
*.7z
*.rar
```

For dataset folders where only Markdown documentation should be tracked:

```gitignore
dataset_dir/**
!dataset_dir/
!dataset_dir/**/
!dataset_dir/**/*.md
```

## Secret Removal

Replace hardcoded keys with environment variables:

```bash
: "${SERVICE_API_KEY:?Set SERVICE_API_KEY in your environment or .env file}"
export SERVICE_API_KEY
```

Commit `.env.example` with empty placeholders:

```dotenv
SERVICE_API_KEY=
SERVICE_ENDPOINT=https://example.invalid/v1
```

Never commit `.env`.

## Checks Before Push

Tracked data check:

```powershell
git ls-files dataset_dir
```

Secret pattern check:

```powershell
git grep -n -E "sk-[A-Za-z0-9]{10,}|jina_[A-Za-z0-9]{10,}|API_KEY=\"[A-Za-z0-9]"
```

Reachable-history check:

```powershell
git grep -n -E "sk-[A-Za-z0-9]{10,}|jina_[A-Za-z0-9]{10,}|API_KEY=\"[A-Za-z0-9]" $(git rev-list --all)
```

Large or forbidden path check:

```powershell
git rev-list --objects --all | Select-String "dataset_dir/|\\.(pt|pth|ckpt|safetensors|pkl|npy|npz|parquet)$"
```

## Clean History Rule

If any forbidden file or secret appears in reachable history, do not push blindly.

Choose one of these paths:

- **New or private repository with disposable history**: create a clean history before publishing, then push with `--force-with-lease` if needed.
- **Existing shared repository with important history**: do not rewrite automatically. Report the affected paths and commits, then ask for a migration choice.
- **Secret already reached a remote**: remove it from current files, rotate the secret, and then decide whether history rewriting is still required.
- **Large data already reached a remote**: decide whether to rewrite history, migrate to Git LFS, or move data to external storage.

Before any force push, record the current remote branch SHA and explain what will be replaced.
