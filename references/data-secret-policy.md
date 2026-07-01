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

If any forbidden file or secret appears in reachable history, rewrite the initial publication history before pushing to GitHub/GitLab, or rotate the exposed secret if it has already left the machine.
