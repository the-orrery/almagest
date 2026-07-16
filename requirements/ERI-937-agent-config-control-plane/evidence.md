# 当前证据

## 本轮交付

- 建立 `ERI-937`，将 Agent 配置控制面能力定义与 `ERI-936` 的 gaal 外部研究分离。
- 在 Almagest 受管 worktree 中建立需求 bundle。
- 固化用户目标、16 项能力、独立决策轴、依赖顺序、逐项拍板协议、初步验收和开放 RAID。
- 经对抗审阅后，去除 Almagest solution-owner 预设，修正决策轴协议、依赖顺序、按资产类型 overlay、consumer render/frontmatter、供应链信任、Effective 证据等级和 RAID。
- 未触达实现代码和 live 配置。

## DEC-01A 配置面补充取证（2026-07-16）

### Mac 本机只读盘点

本轮只读取文件名、链接关系、产品版本和配置 key 结构；未输出 auth、token、OAuth、API key、endpoint credential 或其它 secret value，也未修改 live 配置。

| Consumer/入口 | 已观察事实 | 对范围的影响 |
|---|---|---|
| Codex | `/opt/homebrew/bin/codex`，`codex-cli 0.144.5`；存在 `/Users/a123/.codex/config.toml`、`hooks.json`、`hooks/config.json`、`AGENTS.md`、`skills/`、`plugins/`、`prompts/`、`agents/` | 旧清单漏了 profiles/overrides、permissions/trust、custom agents、prompts/commands、plugin marketplace/lock 等配置域 |
| Codex 共享入口 | `/Users/a123/.codex/AGENTS.md` 链接到 `/Users/a123/workspace/eridanus-ops/chezmoi/AGENTS.md`；另有 `/Users/a123/.agents/skills` 和 `/Users/a123/.agents/.skill-lock.json` | live target、managed source、共享 root 与 lock 必须分别建模 |
| QoderCLI | `/opt/homebrew/bin/qodercli`，版本 `1.0.47`；存在 `/Users/a123/.qoder/settings.json`、`argv.json`、`AGENTS.md`、`agents/`、`hooks/`、`plugins/`、`extensions/`、`external-commands/`、statusline 和 compound 配置 | 旧清单漏了 commands、agents、extensions、statusline、启动参数与 permission/trust 等配置域 |
| `qoder` 命令 | `/usr/local/bin/qoder` 链接到 `/Applications/Qoder.app/Contents/Resources/app/bin/code`，与 `qodercli` 不是同一入口 | binary/alias/wrapper 不能整体视为 `Out`；至少要观测入口解析，防止对错误 consumer/root 验证 |
| 启动绑定 | 本机环境中存在 `CODEX_HOME`、`ORCA_CODEX_HOME` 等变量名；未读取或记录值 | 影响配置 root/profile/lane 的环境变量属于 target 绑定，不属于“完整主机环境”噪声 |

已发现但不自动视为配置的目录包括 cache、logs、history、sessions、telemetry、代码索引、模型缓存和生成 memories。它们需要在 inventory 中标记为 generated/runtime state，避免被 adopt、复制或删除。

### 厂商官方配置面校准

| Consumer | 官方证据 | 得到的配置域 |
|---|---|---|
| Codex | [Codex manual](https://developers.openai.com/codex/codex-manual.md)、[Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference)、[Customization](https://learn.chatgpt.com/docs/customization/overview) | user/project/system/profile layers、`CODEX_HOME`、CLI overrides、trust、AGENTS、skills、MCP、hooks、plugins/marketplaces、agents、prompts、permissions、安全策略和 feature flags |
| QoderCLI | [Settings](https://docs.qoder.com/plugins/settings)、[Hooks](https://docs.qoder.com/extensions/hooks)、[MCP servers](https://docs.qoder.com/en/cli/mcp-servers)、[Permissions](https://docs.qoder.com/en/cli/permissions)、[Skills](https://docs.qoder.com/en/cli/Skills) | user/project/local settings、rules/memory、hooks、MCP scopes、permissions、skills/commands、plugins、agents 和 CLI override |
| Claude Code | [Settings](https://code.claude.com/docs/en/settings)、[Hooks](https://code.claude.com/docs/en/hooks)、[Skills](https://code.claude.com/docs/en/skills)、[MCP](https://code.claude.com/docs/en/mcp)、[Plugins](https://code.claude.com/docs/en/plugins-reference) | managed/user/project/local layers、CLAUDE instructions、skills/commands、MCP、hooks、agents、permissions、output styles、plugins/marketplaces、environment 与 policy |

官方文档与本机盘点共同证明：配置面不能只枚举 skills/MCP/instructions/settings/hooks/plugins 六个名词；还必须显式建模 scope/precedence、profile/override、permissions/trust、agents、commands/prompts/output、marketplace/lock，以及决定 active config 的启动绑定。

### DEC-01A v0.3 拍板结果

- 2026-07-16，principal 明示选择 B：全部 user-authored Agent 配置 + 绑定观测。
- 13 个受管配置域全部进入 v1 `Must`，包括 commands/prompts/output 和客户端偏好中的 user-authored 值；不复制其生成状态。
- 6 类启动绑定与依赖事实必须盘点并参与 plan/verify，但 v1 不负责安装、升级、进程或自动恢复。
- A 因继续漏掉有效配置来源而拒绝；C 因扩成 runtime/host manager 而拒绝。

## 验证记录

| 检查 | 预期 | 实际结果 |
|---|---|---|
| 16 项编号完整性 | DEC-01—DEC-16 各出现一个总览项和一个决策卡 | 通过：总览 16、决策卡 16、独立决策轴 62 |
| YAML 基础检查 | `requirement.yaml` 可安全解析且 PM/slug 正确 | 通过：Ruby Psych safe load；`pm_id=ERI-937`，`slug=agent-config-control-plane` |
| 文档一致性 | 无旧 solution-owner 标题、旧 bundle slug 或“RAID 清零”口径 | 通过：`rg` 无命中；`git diff --check` 通过 |
| 仓级检查 | 文档新增不破坏现有测试与 lint | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 初始 Git 范围 | 只包含本需求 bundle | 通过：初始提交仅 5 个 bundle 文件，共 462 行新增；无实现或 live 配置 |
| 01A 边界重开证据 | 不再把配置绑定整体列为 `Out`，并完整区分 managed/observed/generated | 通过：三类边界、13 个配置域、6 类必须观测对象和 5 类明确不负责项均已写入；拍板前曾将 01A 标记为 `需重开`，避免沿用不完整范围 |
| 01A v0.3 决策记录 | B 的范围、理由、被拒项、Must/Later/Out、后果和验收均可审计 | 通过：01A 标记 `已拍板`；S-01 标记 `resolved`；需求追踪矩阵已展开 13 个配置域与 6 类观测事实 |
| 01A 仓级回归 | 补充范围文档不破坏仓级检查 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 01A Git 范围 | 只修改本需求的设计与证据 | 通过：当前 diff 仅 `design.md`、`evidence.md`；无实现或 live 配置 |

## 验证边界

- 直接运行 `uv run poe check` 时，仓内既有测试读取了本机真实 `XDG_CONFIG_HOME`，`test_identity_source_missing_root_is_actionable_json` 预期 `missing-source-root`、实际得到本机 overlay 的 `missing-src`。这不是本轮文档变更引入的代码失败。
- 使用空目录隔离 `XDG_CONFIG_HOME` 后完整仓级检查通过；本轮没有修改测试或实现来掩盖该环境耦合。
- 首次 YAML 校验脚本未允许 Ruby `Date` 类型而停止；加入 `permitted_classes: [Date]` 后安全解析通过，属于验证脚本修正，不是 YAML 内容修复。

## 尚未产生的证据

- 01B、01C 与 DEC-02—DEC-16 的拍板结果：后续逐项写入 `design.md`。
- capability spec / ADR：所有相关决定稳定后再蒸馏。
- 实现与 runtime 验证：不属于本设计阶段。
