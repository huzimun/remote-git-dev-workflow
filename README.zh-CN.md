# Remote Git Dev Workflow

Remote Git Dev Workflow 是一个 Codex skill，用来建立一套安全、可复用的协作流程：本地机器负责开发，GitHub 或 GitLab 作为中心仓库，远端服务器负责运行和验证。

它适合需要在本地由 agent 修改代码、通过 Git 发布变更、再到远端服务器上运行项目的场景，例如 GPU 服务器、实验服务器或部署服务器。

## 什么时候使用

当你需要处理下面这些任务时，可以使用这个 skill：

- 配置 SSH 连接和免密登录。
- 从直接在服务器上改代码，迁移到本地开发加 Git 管理。
- 新建或迁移到以 GitHub/GitLab 为中心的仓库流程。
- 避免数据集、输出结果、模型权重、压缩包和密钥进入 Git 历史。
- 把脚本里的硬编码 API key 改成环境变量和 `.env.example`。
- 增加轻量 smoke test，用于远端快速验证。
- 增加远端更新脚本，通过 `git pull --ff-only` 拉取中心仓库。
- 使用 `.run.lock` 防止长任务运行时被更新覆盖。

## 安装

把这个仓库复制到对应用户的 Codex skills 目录：

```text
~/.codex/skills/remote-git-dev-workflow
```

在 Windows 上通常是：

```text
C:\Users\<user>\.codex\skills\remote-git-dev-workflow
```

复制完成后，如有需要，重启或刷新 Codex，让它重新发现 skill。

## 使用方式

可以显式触发：

```text
Use $remote-git-dev-workflow to set up a local development, GitHub, and remote server workflow for this project.
```

当任务涉及 SSH 配置、远端开发、GitHub/GitLab 仓库迁移、服务器更新、数据排除规则、smoke test 或运行锁时，Codex 也可能隐式使用这个 skill。

## 工作流模型

这个 skill 推荐把中心仓库作为唯一可信来源：

```text
local workstation/Codex -> origin: GitHub or GitLab -> remote server runtime
```

远端服务器通常应该从中心仓库拉取更新：

```bash
git pull --ff-only origin main
```

除非是明确的应急恢复，不建议直接 push 到服务器上的已检出工作区。

## 本地改完代码后，怎么放到服务器运行？

默认推荐走 GitHub 或 GitLab：

```text
本地改代码 -> 本地提交 commit -> push 到 GitHub/GitLab -> 服务器 pull -> 服务器运行
```

这是最稳的默认流程。因为服务器每次运行的代码都能对应到一个 Git commit，后面更容易检查、复现、回滚，也更容易说明“这次结果是由哪一版代码跑出来的”。

一个典型流程是：

```bash
git add .
git commit -m "Describe the change"
git push origin main
ssh REMOTE_HOST_ALIAS "cd REMOTE_PROJECT_DIR && bash scripts/remote_update.sh"
```

直接传文件到服务器也可以，但只建议用于临时试错：

```text
本地改代码 -> 复制到服务器临时目录 -> 快速跑一下
```

不建议把文件直接覆盖到服务器的主项目目录。这样容易让服务器出现未提交的改动，之后 `git pull` 可能失败，也很难判断服务器到底跑的是哪一版代码。

简单记法：

- **正式运行、实验记录、多人协作**：走 GitHub/GitLab，先 push，再让服务器 pull。
- **临时调试**：可以直接复制或 rsync，但最好复制到单独的临时运行目录，不要覆盖主项目目录。
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
