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
| 启动绑定 | 本机环境中存在 `CODEX_HOME`、`ORCA_CODEX_HOME` 等变量名；未读取或记录值 | 影响配置 root/profile/workspace/settings source 的环境变量属于 target 绑定，不属于“完整主机环境”噪声 |

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

## DEC-01A 对后续决策的方向一致性体检（2026-07-16）

本次按文档自身契约做定向 `doc-xray`：读者动作是 principal 逐轴拍板；生命周期是能力决策前/决策中；交付形态是 living decision workbench；成功 oracle 是后续候选不能静默突破已拍板的 `Must / Later / Out`。扫描覆盖 DEC-02—DEC-16，不评实现优劣，也不替 principal 选择尚未拍板的机制。

| 严重度 | 原位置/问题 | 相对 DEC-01A B 的偏离 | 修正 |
|---|---|---|---|
| BLOCKER | 目标与需求追踪矩阵把“consumer 实际消费/runtime drift”写进统一成功口径 | 把 DEC-11 的 Later 证据变成 v1 隐性 gate | v1 oracle 改为 live config + active binding；actual consumption/runtime drift 单列 Later |
| MAJOR | DEC-11 未标阶段，DEC-12 整体依赖 DEC-11 | v1 config drift 会被 runtime probe 阻塞 | DEC-11 标为 Later；DEC-12 拆为 v1 source→live/binding 与 Later effective/runtime 两条依赖 |
| MAJOR | DEC-13 使用 `fleet coordination`，未先锁定配置边界 | 容易把跨机配置一致性偷换成中央 runtime fleet | 改为“跨机配置一致性”；控制端只可作为待拍板配置/receipt 协调选项，不管理远端进程 |
| MAJOR | DEC-14 包含 host 退役、重装和灾难恢复的宽泛措辞 | 容易扩成完整主机生命周期管理 | 改为配置资产 lifecycle 与“host 重装后的配置重建”；host 重装本身明确 Out |
| MAJOR | DEC-06/10/15/16 未逐项重申 secret、整机事务、runtime fixture/evidence 边界 | 下游候选可能在局部重新引入 C 的责任 | 分别限定 credential provider、受管配置事务、Later probe、Later runtime audit |

修正后，DEC-02—DEC-10 形成 v1 配置闭环；DEC-11 明确为 Later；DEC-12—DEC-16 按配置主线与 runtime 扩展拆层。16 项能力仍保留，因为完整能力地图需要说明 Later/Out，但未拍板卡不得借“完整性”扩张 v1。

本次 semantic finding 由 principal 已拍板的 01A 边界直接复核，未做无证据的文风改写；体检目的为范围一致性，不输出容易误导的综合文风分数。

## DEC-01B 拍板结果

- 2026-07-16，principal 明示选择 C：分层逻辑 ID + 投影实例 ID。
- logical asset 以 `kind + namespace + name + optional stable subresource` 标识；projection instance 以 `asset_id + target_id + consumer_slot` 标识，两者使用不同 ID 空间。
- granularity 以“可独立声明、override、mask/remove 和审计”的最小语义资源为边界；有序项必须有显式稳定 ID，不允许使用数组下标。
- path/root、host/OS、consumer version、layer、revision/digest 和 secret value 不进入 logical asset ID；观测事实使用独立的 target-scoped observation identity。
- A 因位置变化造成身份漂移而拒绝；B 因复杂配置与多投影表达不足而拒绝；D 因无法表达同一资产的版本连续性而拒绝作为 logical identity。01B 未决定 revision/完整性机制，该机制现由 01C 单独确定。

## DEC-01C 拍板结果

- 2026-07-16，principal 确认此前明确推荐：选择 B——不可变 revision + 类型化派生元数据，并采用 Git-backed lineage。
- Almagest 保存 plan/apply/verify 所需的 source revision、render inputs/output、projection receipt 与 conflict evidence；Git source 的 parent/fork/merge/history 按需从 Git 查询，不复制 revision graph。
- Git source 用 repository/commit/path 固定 source snapshot，并用 blob/tree identity 或 canonical digest 固定 asset revision；非 Git source 同样分开保存 authority/ref 与 canonical content digest。digest 只标识 revision/render 完整性，不替代 logical ID。
- 同一 logical/revision 的不同 projection 是 copy/mirror；consumer render 通过明确的输入 revision 与 adapter/capability 元数据标识；无法由 authority/precedence 唯一裁决的同 logical ID 候选才是 conflict。
- A 因不可复现而拒绝；C 因重复 Git 并引入版本控制责任而拒绝；D 因扩成全事件 provenance 平台而拒绝。未来只有出现脱离 Git 的多方编辑/合并需求时才重开 C。

## DEC-02A/02B 拍板结果

- 2026-07-16，principal 确认 B：target 是稳定消费端，identity 为 `host_id + consumer_instance_id`；work 是 source/asset placement 与 residency policy，不是另一个 target context。
- GitHub personal/shared base 由 Mac 与 Windows 共同消费；Mac-local work overlay 不进入 GitHub，且只能留在 Mac 工作机。Mac effective config 为 base + work overlay，Windows 为 base-only，再分别做 consumer render。
- Mac/Windows 是两个已存在的 host，参与 target identity；OS、consumer version、binary/root、profile 与 workspace 是被动观测属性或 selector。当前四类 target 为 Mac Codex/Qoder 与 Windows Codex/Claude，不建立 Mac personal/work 双 target；具体 ID 值留待 inventory 声明。
- work-local 使用独立 source root；允许 local Git 无 remote，但不允许用同一 GitHub checkout 内的 `.gitignore` 充当 residency 安全边界。Almagest 约束自身管理的 source/cache/resolve/render/plan/receipt/live surfaces，不承诺管理通用 OS backup/sync。
- A 因无显式防泄漏 policy 而拒绝；C 因制造虚假双 context 而拒绝；D 因 target 爆炸与 runtime 扩权而拒绝。该次提交未预判 02C，后续拍板见下节。

## DEC-02C 拍板结果

- 2026-07-16，principal 选择 B2：`unsupported/unknown` 默认阻断；Almagest 先输出阻断告警，只有对精确降级计划做 break-glass 二次确认后才能继续。
- 确认只批准当前 target、plan hash 和预计算降级动作；只 apply 可安全拆分的可支持子集，并显式省略获批缺失项。无法形成安全降级计划时仍阻断。
- override 不修改 source desired state，不可永久复用；receipt 记录 capability evidence、被省略项、损失、确认人、理由和结果，并将 target 标为 `applied_with_exception`，不冒充普通成功或合规。
- B2 只处理 consumer capability gap；source trust、secret 泄漏、work residency/egress deny 等硬策略拒绝不可通过二次确认越过。A、B1、C、D 分别因伪成功、缺人工出口、隐式分类放行和语义自动改写而拒绝。

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
| 后续方向一致性 | DEC-02—DEC-16 均显式服从 B，且不再混淆 v1/Later/Out | 通过：16 个总览项、16 张决策卡、15 条 B 影响约束；旧 runtime/fleet/host 宽口径无残留命中 |
| 01B 候选完整性 | 候选互斥，涵盖物理、单层逻辑、分层逻辑+投影、内容寻址四种 identity 模型 | 通过：A/B/C/D 均含 canonical fields、收益与主要问题；C 另含 granularity、字段边界、观测 identity 与验收断言 |
| 01B 决策记录 | C 的身份空间、边界、理由、拒绝项、Must/Later/Out、后果和验收均可审计 | 通过：01B 标记 `已拍板`；logical/projection/observation identity 分开；digest 明确保留给 01C 决定，不作为 logical ID |
| 方向审计仓级回归 | 方向修正与 01B 候选不破坏仓级检查 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 01B 拍板仓级回归 | 固化 C 且不把下一轴未决方案写入正式文档后不破坏仓级检查 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 01C 决策记录 | B 的 revision、Git 分工、派生/conflict 规则、Must/Later/Out、后果和验收均可审计 | 通过：01C 标记 `已拍板`；Almagest revision evidence 与 Git authored history 分开；C/D 的扩权责任明确拒绝 |
| 01C 拍板仓级回归 | 固化 Git-backed revision 模型后不破坏仓级检查 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 02A/02B 决策记录 | endpoint identity、source topology、work residency、边界与下游影响可审计，02C 不被偷跑 | 通过：02A/02B 标记 `已拍板`；四个稳定 target、GitHub base + Mac-local overlay、全链路 residency 与 OS backup Out 均明确；该次提交保持 02C 待定 |
| 02A/02B 拍板仓级回归 | 固化 target 与 source residency 模型后不破坏仓级检查 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 02C 决策记录 | 默认阻断、二次确认、降级计划、审计、失效与不可越过边界均可审计 | 通过：B2 标记 `已选择`；无确认零写入、逐 plan override、exception receipt 和硬策略拒绝均已明确 |
| 02C 拍板仓级回归 | 固化 B2 break-glass 合同后不破坏仓级检查 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |

## 验证边界

- 直接运行 `uv run poe check` 时，仓内既有测试读取了本机真实 `XDG_CONFIG_HOME`，`test_identity_source_missing_root_is_actionable_json` 预期 `missing-source-root`、实际得到本机 overlay 的 `missing-src`。这不是本轮文档变更引入的代码失败。
- 使用空目录隔离 `XDG_CONFIG_HOME` 后完整仓级检查通过；本轮没有修改测试或实现来掩盖该环境耦合。
- 首次 YAML 校验脚本未允许 Ruby `Date` 类型而停止；加入 `permitted_classes: [Date]` 后安全解析通过，属于验证脚本修正，不是 YAML 内容修复。

## 尚未产生的证据

- DEC-03—DEC-16 的拍板结果：后续逐项写入 `design.md`。
- capability spec / ADR：所有相关决定稳定后再蒸馏。
- 实现与 runtime 验证：不属于本设计阶段。
