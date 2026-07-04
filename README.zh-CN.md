# Remote Git Dev Workflow

Remote Git Dev Workflow 是一个 Codex skill，用来建立一套安全、可复用的协作流程：本地机器负责开发，GitHub 或 GitLab 负责版本管理，通过 SSH 部署到远端服务器运行。

它适合需要在本地由 agent 修改代码、通过 GitHub/GitLab 保留历史、再到远端服务器上运行项目的场景，例如 GPU 服务器、实验服务器或部署服务器。

## 什么时候使用

当你需要处理下面这些任务时，可以使用这个 skill：

- 配置 SSH 连接和免密登录。
- 从直接在服务器上改代码，迁移到本地开发加 Git 管理。
- 新建或迁移到以 GitHub/GitLab 为中心的仓库流程。
- 避免数据集、输出结果、模型权重、压缩包和密钥进入 Git 历史。
- 把脚本里的硬编码 API key 改成环境变量和 `.env.example`。
- 增加轻量 smoke test，用于远端快速验证。
- 当服务器不能访问 GitHub/GitLab 时，通过 SSH 部署干净的已提交代码快照。
- 当服务器能访问 GitHub/GitLab 时，增加远端更新脚本，通过 `git pull --ff-only` 拉取中心仓库。
- 使用 `.run.lock` 防止长任务运行时被更新覆盖。

## 安装

推荐方式：直接让 Codex 使用内置的 `skill-installer` skill 从 GitHub 安装。

在 Codex 里输入这段提示词：

```text
Use $skill-installer to install the skill from this GitHub repository:
https://github.com/huzimun/remote-git-dev-workflow.git

Install it as remote-git-dev-workflow, prefer the git install method, and verify that SKILL.md, agents/, references/, and scripts/ are all present after installation.
```

安装位置应该是当前用户的 Codex skills 目录：

```text
~/.codex/skills/remote-git-dev-workflow
```

在 Windows 上通常是：

```text
C:\Users\<user>\.codex\skills\remote-git-dev-workflow
```

如果手动安装，也要把完整仓库克隆到这个目录。不要只复制根目录文件，因为 `references/` 和 `scripts/` 也是 skill 的一部分。

安装后检查这些文件和目录是否存在：

```text
SKILL.md
agents/
references/
scripts/
```

如果安装后只有根目录文件，说明可能拿到了不完整的 sparse checkout。可以重新使用 git 方式安装，或者在该 skill 目录里执行：

```bash
git sparse-checkout disable
```

复制完成后，如有需要，重启或刷新 Codex，让它重新发现 skill。

## 使用方式

可以显式触发：

```text
Use $remote-git-dev-workflow to set up a local development, GitHub, and remote server workflow for this project.
```

当任务涉及 SSH 配置、远端开发、GitHub/GitLab 仓库迁移、服务器更新、数据排除规则、smoke test 或运行锁时，Codex 也可能隐式使用这个 skill。

## 工作流模型

这个 skill 支持两种模式。

**SSH Sync Mode** 是默认推荐模式：

```text
local workstation/Codex -> origin: GitHub or GitLab
local committed Git snapshot -> SSH deploy -> remote server runtime
```

当服务器不能稳定访问 GitHub/GitLab，或不能登录 Codex CLI 时，优先使用这个模式。服务器只需要 SSH、bash、tar 和项目运行环境。

**Server Pull Mode** 保留原来的流程：

```text
local workstation/Codex -> origin: GitHub or GitLab -> remote server runtime
```

当服务器可以稳定访问中心仓库时，可以让服务器从中心仓库拉取更新：

```bash
git pull --ff-only origin main
```

除非是明确的应急恢复，不建议直接 push 到服务器上的已检出工作区。

## 本地改完代码后，怎么放到服务器运行？

默认推荐用 GitHub/GitLab 管版本，用 SSH 部署到服务器：

```text
本地改代码 -> 本地提交 commit -> push 到 GitHub/GitLab -> SSH 部署已提交快照 -> 服务器运行
```

这样服务器每次运行的代码都能对应到一个 Git commit，同时不要求服务器访问 GitHub/GitLab，也不要求服务器登录 Codex。

一个典型流程是：

```bash
git add .
git commit -m "Describe the change"
git push origin main
powershell -ExecutionPolicy Bypass -File scripts/deploy_via_ssh.ps1
ssh REMOTE_HOST_ALIAS "cd ~/Deploy/PROJECT_NAME/current && bash scripts/run_remote_release.sh"
```

当服务器可以稳定访问 GitHub/GitLab 时，也可以使用 Server Pull Mode：

```text
本地改代码 -> 本地提交 commit -> push 到 GitHub/GitLab -> 服务器 pull -> 服务器运行
```

不建议把单个文件手工覆盖到服务器主目录。这样容易出现混合版本，也很难判断服务器到底跑的是哪一版代码。

简单记法：

- **服务器不能稳定访问 GitHub/GitLab 或 Codex 登录**：用 SSH Sync Mode。
- **服务器能稳定访问 GitHub/GitLab**：可以用 Server Pull Mode。
- **正式运行**：同步完整 Git 快照，不要手工 `scp` 单个文件。
- **长任务运行时**：先创建运行锁，避免任务没结束时服务器代码被更新。
- **多人或多个 agent 协作时**：使用分支或 pull request，避免互相覆盖。

## 仓库结构

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

- `SKILL.md`：核心流程和安全规则。
- `agents/openai.yaml`：Codex UI 元数据。
- `references/command-templates.md`：SSH、Git、远端更新等命令模板。
- `references/data-secret-policy.md`：忽略规则、密钥处理和推送前检查。
- `references/script-templates.md`：`remote_update.sh`、smoke test、运行锁脚本骨架。
- `scripts/render_workflow_commands.py`：根据 JSON 配置生成项目专用命令片段。

## 安全注意事项

- 不要提交真实密钥、`.env` 文件、SSH 私钥、API key、token 或密码。
- 不要把数据集、生成输出、模型 checkpoint 或大型二进制文件上传到 Git，除非项目明确采用了合适的大文件管理方案。
- 如果敏感文件或大数据已经进入旧提交，需要在发布到 GitHub/GitLab 前创建干净历史。
- 需要重写历史时，优先使用 `git push --force-with-lease`，不要直接使用普通 `git push --force`。
- 远端长任务运行时使用 `.run.lock` 等锁文件，避免任务执行过程中代码被更新覆盖。
- 不要假设远端非交互 SSH shell 已经初始化 conda；应显式激活环境，或设置 `PROJECT_PYTHON`。

## License

当前还没有声明开源许可证。如果要作为开源项目发布，请先添加 `LICENSE` 文件。
