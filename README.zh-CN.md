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
