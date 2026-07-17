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
- override 不修改 source desired state，不可永久复用；receipt 记录 capability evidence、被省略项、损失、principal approver、operator Agent、理由和结果，并将 target 标为 `applied_with_exception`，不冒充普通成功或合规。
- B2 只处理 consumer capability gap；source trust、secret 泄漏、work residency/egress deny 等硬策略拒绝不可通过二次确认越过。A、B1、C、D 分别因伪成功、缺人工出口、隐式分类放行和语义自动改写而拒绝。

## DEC-03A v0.1 拍板结果（外部 authority 行已被 v0.2 取代）

- 2026-07-16，principal 选择 B：按 source 类型固定 ownership；authority 表示 source 有权声明什么，不等同于 overlay precedence。
- GitHub personal/shared base 拥有共享可移植 declaration 与外部 package 的本地采用意图；Mac-local work 拥有 work-only asset/delta；host-local 只拥有受 schema 约束的本机 binding；registry/upstream 只拥有被选 revision 的内容和发布元数据；resolved/rendered/cache/live 无 authored authority。
- 外部 package 的“本地是否采用、启用和投影”与“上游 revision 内容”分属本地 source 和 registry；签名、digest、浮动 ref 与更新策略留给 03C，合法 overlay/override 留给 03B/05。
- scope 外声明直接作为 authority violation 阻断，不按低优先级候选处理，也不可通过 DEC-02C break-glass 放行。A、C、D 分别因无法承载 work-local、per-asset 治理过重和多主不可复现而拒绝。

## Agent-first 操作者模型确认与定向体检（2026-07-16）

principal 当次明示确认：Almagest 由 AI Agent 直接调用；principal 通过自然语言表达目标、裁决歧义并批准高风险动作，不承担日常 CLI/TUI 操作。operator Agent 负责调用、解释、提交批准和重试；Almagest 负责确定性的 plan/apply/verify 与策略执行；被配置的 consumer 是另一个独立角色。2026-07-17 的 DEC-03D 又把批准范围从“高风险动作”扩展为“所有非 `no-op` 配置写计划”，见后续拍板结果。

本次按该确认对既有设计做定向 `doc-xray`。读者动作仍是 principal 拍板能力，但产品调用者已明确为 operator Agent；成功 oracle 是既有已决语义不变，同时所有交互假设服从 Agent-first / Principal-in-the-loop（principal 保留拍板、Agent 负责操作）的边界。

| 严重度 | 原位置/问题 | 相对已确认操作者模型的偏离 | 修正 |
|---|---|---|---|
| BLOCKER | DEC-02C 把二次确认载体写成“交互式确认或 approval artifact” | 暗示 principal 直接操作 prompt，且 receipt 只有模糊的“确认人” | 改为 operator Agent 提交绑定 principal 决定与 plan hash 的 approval artifact；分别记录 approver 与 operator |
| MAJOR | DEC-09/10 未要求 canonical machine contract | 实现可能退化成 Agent 抓取易变人类文本，或形成 TUI/API 两套语义 | 加入稳定 schema、诊断码、退出码、plan ID、非交互 apply 和按 ID explain 约束 |
| MAJOR | DEC-12/16 只有“告警/解释”，没有 Agent 上下文成本与 actor 边界 | 可能默认输出全部证据、浪费 token，也无法区分谁批准与谁执行 | 默认紧凑摘要，详情按 ID 获取；audit 分开记录 principal 与 operator Agent |
| MINOR | `consumer` 同时可能被理解成调用方和配置消费方 | actor identity 与 target identity 容易混用 | 新增 principal/operator Agent 定义，并明确同一产品可兼任角色但身份必须分开 |

该次操作者模型审计没有替 principal 选择 DEC-03B 或 DEC-09/10/12/16 的具体机制，只把它们的候选空间约束到已确认的操作者模型；DEC-02C 的默认阻断、逐 plan break-glass、硬策略不可越过等既有语义保持不变。后续 03B1 拍板见下节。

## DEC-03B1 拍板结果

- 2026-07-16，principal 选择 A：authority 合法但确定规则仍无法裁决时，默认阻断，由 operator Agent 告警并解释，principal 只为当前精确 plan/conflict set 作一次性选择。
- approval artifact 绑定 target、plan hash、输入 revision、完整 conflict set 和逐项选择；apply 不修改 source，也不创建永久 resolution rule。输入或 plan 变化后旧裁决失效，下一次 plan 对未修 source 的歧义重新阻断。
- 只有 principal 明确要求“修 source”或等价动作时，Agent 才修改拥有 authority 的 source、生成新 revision 并重新 plan；不得从一次性裁决推断长期规则或 source 变更授权。
- 临时 apply 必须保持 exception 状态并可审计，不冒充稳定 `compliant`。B 因形成第二份配置真相被拒；C 因默认扩大为 source 修改被拒；D 因路径与状态面过多被拒。该次 03B2 污染处置仍待拍板，后续决定见下节。

## DEC-03B2 拍板结果

- 2026-07-16，principal 选择 A：一旦受管 evidence 将 cache/resolved/rendered/live 识别为 source contamination，Almagest 只阻断并返回结构化诊断；source 与 downstream 状态保持不动，等待 principal 现场决定。
- 允许继续只读 inventory/explain/取证，plan surface 只返回 block-only record；依赖污染 source 的 resolve、可执行 action 和 apply 零写入。自动隔离、删除、恢复、adopt 或继续生成可执行 plan 均被拒绝。
- principal 明确指定修复动作后，operator Agent 才能改变 source；任何修复必须形成新 revision 并重新 inventory/resolve/plan。03B1 单次裁决与 02C break-glass 均不能绕过污染阻断。
- B/C/D 分别因未授权 source 修改、误覆盖 authored change 风险和把 mutation authority 隐藏进证据分类而拒绝。污染证据类型、置信度和 freshness 留给 DEC-07/16，不在本轴偷跑。

## DEC-03A v0.2 / DEC-03C 拍板结果

- 2026-07-17，principal 选择 03C A，并据此修订 03A：外部 registry/upstream 不再是 Almagest source class，也不拥有内容 authority；Almagest 只消费已经吸收进 GitHub personal/shared 或 Mac-local work 的 owned revision。
- 周期检查、候选发现、拉取、依赖与签名校验、评审、晋级和吸收均由控制面外工具负责。外部工具最多读取 owned source revision/time 与 upstream provenance 作为检查水位；Almagest 不拥有调度、网络、registry credential、候选状态或“可更新”状态。
- consumer 配置中的 registry/ref/version constraint 仍可作为普通 desired data 被投影，但不会触发 package 拉取，也不会让外部内容取得 source authority。吸收后的内容重新经过正常配置闭环与 03D 逐变更审批；owned 不等于已批准或安全。
- B/C/D 分别因仍引入上游检查责任、package acquisition/隔离区生命周期和端到端供应链更新责任而拒绝。

## DEC-03A v0.2 / DEC-03C 定向体检

本次 `doc-xray` 的冻结契约是：读者仍通过本 living design 逐轴拍板；只允许写入 principal 已确认的外部边界，不改变其它已决语义，也不替未决的 03D 选择机制。全文定向扫描得到以下需要回校的旧假设。

| 严重度 | 原位置/问题 | 相对本次 A 拍板的偏离 | 修正 |
|---|---|---|---|
| BLOCKER | DEC-03A v0.1 把 `External registry/upstream` 列为 source class，并赋予被选 revision 的内容 authority | 直接违背“Almagest 只消费吸收后的 owned source” | 以 03A v0.2 取代该行；外部 upstream 降为控制面外候选提供方 |
| MAJOR | DEC-03C 原轴要求 Almagest 决定 floating revision、签名、allowlist 和更新策略 | 会把配置一致性控制面扩成上游版本与供应链更新器 | 改为外部采集/吸收是否 Out，并固化选择 A |
| MAJOR | DEC-01C 要求 DEC-03 定义 non-Git revision 与 floating ref policy | 让上游版本再次进入 Almagest 的 source revision 模型 | 收紧为 owned source authority/revision；外部流程只留下可选 provenance |
| MINOR | plugin/extension 配置仍包含 registry/ref/version 字段 | 容易被误读为 Almagest 要获取 package | 明确这些字段只是 consumer desired data；安装版本只观测，不触发 acquisition |

该体检保留 03A 的固定 source-class ownership、03B1/03B2、01A 的配置域和 01C 的不可变 revision 语义；只重画外部 acquisition plane 边界。该次 03D 尚未拍板，因此不能从“已吸收/已 owned”推导为安全或已批准；后续拍板见下节。

## DEC-03D 拍板结果

- 2026-07-17，principal 选择统一逐变更审批：不建设高/中/低风险分类器，也不按 skill、hook、MCP、plugin 等资产类型自动放行；任何会产生配置写动作的非 `no-op` plan 都先阻断并报警。
- operator Agent 向 principal 报告当前 plan 的完整差异与影响；principal 可批准精确 plan、拒绝或要求调整后重新 plan。approval 绑定 target、plan hash、固定 source/resolved/inventory 输入和完整 action set，任一变化后失效。
- 本通用批准是所有写入的必要条件，但不能越过 02C capability exception、03B1 conflict resolution、03B2 contamination 或 authority/residency/secret 等硬策略 block。只读 inventory/plan/diff/explain/verify 与真正 `no-op` 无需批准。
- B/C/D 分别因误分类会造成静默写入、资产类型不能代表风险和扩成内容/供应链安全平台而拒绝。接受的代价是普通小改也会报警，且批准只证明知情授权，不证明内容本身安全或业务正确。

## DEC-04A 拍板结果

- 2026-07-17，principal 确认 04A 不再做伪选项：驻留权限只跟 authority source；GitHub personal/shared 可供已授权 Mac/Windows consumer 使用，Mac-local work 的全部内容一律只能留在 Mac 工作机。
- asset、字段贡献与 content-bearing 派生物自动继承 source 边界；任一输入包含 work contribution，整个派生 payload 都是 Mac-only。不提供 per-asset allowed-host、白名单、临时外发批准或其它单项放宽。
- 某项 work 内容未来需要共享时，必须显式迁移/改写为 GitHub source 的 authored asset，形成新 revision 并走 DEC-03D 新 plan；不能原地修改标签冒充驻留例外。
- 该约束保留 04B 的确定投影、04C 的全链路 enforcement 与恢复、04D 的脱敏元数据边界作为后续决策；它只消除 per-asset classification 与 exception 方案空间。

## DEC-04B 拍板结果

- 2026-07-17，principal 确认固定 target→source eligibility：Mac Codex/QoderCLI 只从 GitHub personal/shared base + Mac-local work 取得候选，Windows Codex/Claude 只从 GitHub base 取得候选。
- eligibility 在 overlay/resolve/render 前确定，只定义候选 source 上界；asset selector 可以缩小范围，但不能扩权。同名冲突、字段 merge 和 consumer 格式分别留给 DEC-05/08。
- 映射不随 cwd、profile、operator Agent、root 是否碰巧存在或 source 临时可用性变化。已登记的 Mac work source 不可访问或无法证明时 fail closed，不以 GitHub-only 结果冒充 Mac 合规。
- 接受新增 target/source class 必须显式维护映射的成本，以换取投影确定、可解释且不会通过 runtime fallback 把 work 暴露给 Windows。

## DEC-04C 拍板结果

- 2026-07-17，principal 确认 work residency 违规统一采用“阻断、告警、现场决策”：Almagest 控制的物化点必须在写入前 deny；只读发现的既有违规必须阻断受影响的 resolve、普通 plan 与 apply。
- inventory、diff、explain 与取证可以继续。发现违规不会赋予 Almagest 自动删除、隔离、迁移、修复或 adopt source/cache/live 的权限，也不能用普通 approval、break-glass、单次冲突裁决或 acknowledgment 绕过。
- 03B2 按 downstream→source 的污染方向判断，04C 按 work→非授权位置的驻留违规判断；同一事实可以同时命中，但必须分别满足两项恢复条件。
- Almagest 返回结构化诊断和恢复候选，operator Agent 向 principal 报警。principal 明确动作后，Agent 才能提交绑定 detection、固定输入、完整 action set 和 plan hash 的 recovery plan；任何写入继续服从 DEC-03D 的逐 plan 批准。
- 恢复动作完成后必须重新 inventory/verify，只有证据证明越界 payload 已消失且输入重新固定才解除阻断。04D 随后排除了脱敏跨机摘要、中央报告和主动通知；具体本机 schema 与检测入口留给 DEC-07/09/12/16。

## DEC-04D 拍板结果

- 2026-07-17，principal 选择 A，并纠正“跨机报告”这一错误前提：Almagest 由当前 host 的 operator Agent 在操作现场调用；没有中央控制端、跨机 dashboard/report、receipt 上传、远程 evidence reference 或远程 host 操作。
- work content 与 work-derived metadata 全量 Mac-only。存在/缺失、状态、ID、名称、路径、digest、数量、时间、diff、provenance、plan、receipt、诊断和加密 evidence 均不得进入 GitHub、Windows 或中央端；“已脱敏/不可还原/已加密”不构成例外。
- Mac 与 Windows 分别由同机 Agent 调用同机 Almagest，并向 principal 当场解释。Windows 只消费 GitHub base，不查询也不知道 Mac work 是否存在、合规或被阻断。
- 无法证明完全 work-free 的 artifact 在 egress 时 fail closed；本机只读取证仍可继续。确需共享的内容必须重新编写/迁移为 GitHub authored asset、新 revision 和 DEC-03D 新 plan。
- B/C/D 分别因制造无需求的状态信封、暴露工作结构和加密后仍离机而拒绝。接受的代价是无跨机总览；principal 处理哪台机器，就进入哪台机器的 Agent 会话。

## DEC-05A 拍板结果

- 2026-07-17，principal 选择 A：v1 只有 `GitHub personal/shared base` 与 `Mac-local work` 两个 authored layer；Mac target 取得 base + work，Windows target 只取得 base。
- base→work 只固定 layer 适用范围和候选处理顺序，不预先决定同名 asset/字段 winner。该轴当时未决定的 merge 与碰撞语义现已分别由 05B/05C 定义。
- host、OS、consumer、版本、profile、workspace、root 和 binary path 只作为 observation、selector、render 输入或 binding 证据；secret、账号和本机路径只作 local binding；它们都不形成额外 layer。
- rendered/live/cache/session/unmanaged 本机状态没有 authored authority。接纳本机差异必须显式修改合法 source 并生成新 plan，不能把 live target 或任意 local 目录提升为 override。
- B/C/D 分别因制造不存在的 host 意图层、把 consumer 派生差异变成 source、以及让未受管 live state 成为第二真相而拒绝。未来确有第三种 authored authority 时必须重开 03A、04A/04B 与 05A。

## DEC-05B 拍板结果

- 2026-07-17，principal 选择 B：采用 schema-aware 类型化合并；每个 asset adapter/schema 必须把节点显式声明为 atomic、granular map、set、keyed list 或 ordered list，不从序列化格式、目录或 consumer 输出猜语义。
- disjoint map field、不同稳定 item ID 与合法排序约束可以结构化组合；opaque body/file/script 默认 atomic。缺失/不受支持/无法验证的可信 schema 返回 unknown/block；缺失/重复 ID、shape 不兼容和无效顺序只产生 typed collision；两者都不得 fallback 到 deep merge、array append 或扫描顺序。
- 05B 只定义结构组合单元。多个贡献命中同一 atomic leaf、同 key 的非等价元素或 remove/mask 时只产出 typed collision；该轴当时未决定的 winner、删除、duplicate 与 conflict 现已由 05C 定义。
- merge schema version/digest 是 plan 输入；shape、stable key 或 ordering 变化令旧 plan/approval 失效。resolved 字段/元素必须保留 source/layer/schema path/shape/revision provenance。
- A/C/D 分别因复制整项且粒度过粗、通用 deep merge 错配不同 list/map 语义、以及路径 patch 强耦合 base 并吞并 05C 而拒绝。接受 adapter schema 与 fixture 的维护成本。

## DEC-05C 拍板结果

- 2026-07-17，principal 选择 B：不相交贡献按 05B 自动组合，同 ID 同 canonical 内容的 eligible contribution 去重并保留全部 provenance；其它非等价同目标贡献必须有显式 override/mask，否则 conflict/block，不因 work 位于后层而自动取胜。
- override/mask 只允许 Mac-local work 无歧义地指向 eligible base 的 semantic target。target 缺失/歧义、shape 不兼容或多个意图竞争均 conflict/block；05D 已确定 operation/target ref 进入 source inventory，target reference 的具体字段及是否绑定 expected revision/digest 仍待拍板。
- mask 只隐藏匹配的 Mac resolved target，不修改 GitHub base 或 Windows base-only 结果；source remove 修改拥有声明的 authority source并形成新 revision。省略声明不自动表示 mask/remove。
- conflict 本身不自动写 source。principal 可走 03B1 做当前精确 plan 的 transient resolution；只有明确要求修 source 后，Agent 才生成 override/mask/remove 等 source diff 并重新 plan。所有非 no-op 写入仍走 03D，且任何 authority/residency/secret/capability hard policy 均不可越过。
- A/C/D 分别因静默 last-layer-wins、无法表达真实 Mac-only 覆盖、以及把稳定 overlay 变成每次重复的 transient exception 而拒绝。接受每项覆盖/隐藏都要显式声明、无声明时必须现场处理的成本。

## DEC-05D 表达模型拍板结果

- 2026-07-17，principal 选择 B：GitHub personal/shared 与 Mac-local work 各自维护一份逻辑、版本化、机器可校验的 source inventory；inventory 声明 stable ID、kind、source-relative payload ref、selector、operation 与需要时的 target ref，实际配置继续保存在原生 payload 中。
- inventory 是控制面元数据的 authored truth，但不内联/复制 payload；Almagest 的 ID、selector、operation、target ref 和 provenance 不得进入 `SKILL.md` frontmatter、prompt/instruction body 或 rendered consumer config。payload 原有 frontmatter 的 consumer 处理留给 DEC-08C。
- 只有 inventory 登记且在当前 source root 内唯一解析的 payload 才进入 candidate set。invalid schema、duplicate ID、dangling/ambiguous/root-escaping ref 均 block；unlisted payload 不自动 adopt，只作为 orphan/unmanaged evidence。
- Windows 只读取 base inventory/payload，Mac 分别读取 base + work；base inventory 不引用任何 work 内容或元数据，work inventory/payload 全量 Mac-only。selector 只能收窄 eligibility，binding value 与 rendered/live 状态不成为 inventory contribution。
- A/C/D 分别因路径魔法、sidecar 漏同步与单体 authoring platform 迁移成本而拒绝。接受 Agent 维护 inventory reference 的成本，以换取机器契约清晰且 control metadata 不消耗 Agent token。
- 尚未拍板：target reference 只绑定 stable logical/subresource ID，还是同时固定 expected revision/digest；具体 inventory 文件名、序列化格式和物理分片属于实现细节，不在本轮决定。

## 验证记录

| 检查 | 预期 | 实际结果 |
|---|---|---|
| 16 项编号完整性 | DEC-01—DEC-16 各出现一个总览项和一个决策卡 | 通过：总览 16、决策卡 16、独立决策轴 63 |
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
| 03A 决策记录 | 五类 source 的 ownership、采用权/内容权、越权处理与未决边界均可审计 | 通过：B 标记 `已选择`；source-class matrix、派生目录无 authority、scope violation block 以及 03B/03C/05/06 边界均已明确 |
| 03A 拍板仓级回归 | 固化 source-class ownership 后不破坏仓级检查 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| Agent-first 角色合同 | principal、operator Agent、Almagest、consumer 四个角色分离，且当次审计不偷跑待决机制 | 通过：新增全局 actor contract、验收场景与 A-03；02C 仅修正批准载体；该次审计保持 03B、09、10、12、16 待给方案，后续 03B1 独立拍板 |
| Agent-first 结构完整性 | 总览、决策卡、方向约束和新验收均可机械复核 | 通过：总览 16、决策卡 16、DEC-01A 方向约束 15、actor scenario 1、A-03 resolved 1；`git diff --check` 通过 |
| Agent-first 仓级回归 | 操作者模型与定向审计不破坏现有工程 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 03B1 决策记录 | 单次裁决、source 边界、失效、重复阻断和显式修 source 路径均可审计 | 通过：A 标记 `已选择`；03B 拆为 03B1/03B2；临时 resolution 与 source change 的 authority 分离 |
| 03B1 结构完整性 | 拆轴后不丢能力、不误标 03B2，验收与状态同步 | 通过：决策卡 16、独立决策轴 63、03B1 决策节 1、验收场景 1、旧 `03B—03D 待给方案` 无残留；`git diff --check` 通过 |
| 03B1 仓级回归 | 固化一次性冲突裁决合同后不破坏现有工程 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 03B2 决策记录 | 阻断、零自动写入、人工恢复 authority、不可绕过与重新 plan 均可审计 | 通过：A 标记 `已选择`；处置策略与 DEC-07/16 检测证据合同分离；03B1/02C 不得绕过 |
| 03B2 结构完整性 | 状态、候选、block-only plan、验收和未决边界同步 | 通过：决策卡 16、独立决策轴 63、03B2 决策节 1、验收场景 1；当次提交中 03C/03D 保持待给方案；`git diff --check` 通过 |
| 03B2 仓级回归 | 固化 source contamination 阻断合同后不破坏现有工程 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 03A v0.2 / 03C 决策记录 | external authority 已撤销，外部采集/吸收 Out，水位读取与 owned revision 接入合同可审计 | 通过：03C A 标记 `已选择`；03A source 表无 external row；Must/Later/Out、接受代价、后果与验收均已写入 |
| 03A v0.2 / 03C 结构完整性 | 只改变外部边界，不丢能力卡/决策轴，并同步状态、验收和历史 supersede 说明 | 通过：决策卡 16、独立决策轴 63、03C 决策节 1、验收场景 1、active external source row 0；`git diff --check` 通过 |
| 03A v0.2 / 03C 仓级回归 | 固化外部 acquisition plane Out 后不破坏现有工程 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 03D 决策记录 | 所有非 no-op 配置写计划统一报警、逐 plan 批准、失效和不可越过边界均可审计 | 通过：A 标记 `已选择`；不建立风险分级/资产白名单；Must/Later/Out、接受代价、后果与验收均已写入 |
| 03D 结构完整性 | 全局 actor 合同、03D 卡片、验收和下游 09/10/12/16 约束一致 | 通过：决策卡 16、独立决策轴 63、03D 决策节 1、验收场景 1、当前状态 1、旧待定口径 0；`git diff --check` 通过 |
| 03D 仓级回归 | 固化统一逐变更审批后不破坏现有工程 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 04A 约束记录 | source 级驻留、work 全量 Mac-only、无单项例外与显式迁移出口均可审计 | 通过：04A 标记 `已拍板`；constraint confirmation、Must/Later/Out、接受代价、后果和验收均已写入 |
| 04A 结构完整性 | 只收敛 classification/exception，不偷跑 04B—04D，并同步状态和验收 | 通过：决策卡 16、独立决策轴 63、04A 决策节 1、验收场景 1、旧 DEC-04 全待定口径 0；`git diff --check` 通过 |
| 04A 仓级回归 | 固化 source 级无例外驻留后不破坏现有工程 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 04B 约束记录 | 四个 target 的 source eligibility、静态映射、selector 收窄与 fail-closed 边界均可审计 | 通过：04B 标记 `已拍板`；Mac 双源、Windows 单源；Must/Later/Out、接受代价、后果和验收均已写入 |
| 04B 结构完整性 | 只固定 source 候选上界，不偷跑 DEC-05 merge 或 DEC-08 render，并同步状态和验收 | 通过：决策卡 16、独立决策轴 63、04B 决策节 1、验收场景 1、当前 DEC-04 状态 1；`git diff --check` 通过 |
| 04B 仓级回归 | 固化 target→source eligibility 后不破坏现有工程 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 04C 约束记录 | 写前拒绝、既有违规阻断、结构化告警、人工恢复 authority 与重新验证均可审计 | 通过：04C 标记 `已拍板`；Must/Later/Out、03B2 边界、接受代价、后果和验收均已写入 |
| 04C 结构完整性 | 只规定检测命中后的处置，不偷跑 04D 跨机元数据、DEC-12 调度或通知渠道 | 通过：决策卡 16、独立决策轴 63、04C 决策节 1、验收场景 1、当前 DEC-04 状态 1；`git diff --check` 通过 |
| 04C 仓级回归 | 固化 work 越界阻断与人工恢复合同后不破坏现有工程 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 04D 决策记录 | A 的零离机边界、本机即时操作者模型、未知 egress 停止条件和 GitHub migration 出口均可审计 | 通过：04D 标记 `已拍板`；A/B/C/D、Must/Later/Out、接受代价、后果和验收均已写入 |
| 04D 方向修正 | 清除跨机汇总前提，且不误删“共享 GitHub source 下各机独立一致”的能力 | 通过：04A/04C 验收、操作者模型、DEC-13/16 已改为本机独立执行；旧跨机汇总面、receipt 上传候选和中央控制端假设无活动口径残留 |
| 04D 结构完整性 | 完成 DEC-04 全部四轴，并同步状态、验收和未决证据 | 通过：决策卡 16、独立决策轴 63、04D 决策节 1、验收场景 1、当前 DEC-04 状态 1；`git diff --check` 通过 |
| 04D 仓级回归 | 固化 work 零离机与本机即时调用后不破坏现有工程 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 05A 决策记录 | 两个 authored layer、非 layer 输入边界、接纳与演进路径均可审计 | 通过：05A 标记 `已拍板`；A/B/C/D、Must/Later/Out、接受代价、后果和验收均已写入；当轮未偷跑同名 winner，现由 05C 定义 |
| 05A 结构完整性 | 只固定 layer 集合与适用范围，不偷跑 05B/05C merge 或 DEC-08 render | 通过：决策卡 16、独立决策轴 63、05A 决策节 1、验收场景 1、当前 DEC-05 状态 1；`git diff --check` 通过 |
| 05A 仓级回归 | 固化两层 authored overlay 后不破坏现有工程 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 05B 决策记录 | schema-aware shape、结构组合边界、版本/provenance 与 fail-closed 行为均可审计 | 通过：05B 标记 `已拍板`；A/B/C/D、五类 shape、Must/Later/Out、接受代价、后果和验收均已写入；当轮未偷跑 winner/remove，现由 05C 定义 |
| 05B 结构完整性 | 只固定 merge topology，不偷跑 05C winner/remove/conflict 或 DEC-08 consumer render | 通过：决策卡 16、独立决策轴 63、05B 决策节 1、验收场景 1、当前 DEC-05 状态 1；`git diff --check` 通过 |
| 05B 仓级回归 | 固化 schema-aware 类型化合并后不破坏现有工程 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 05C 决策记录 | add/duplicate/override/mask/remove/conflict 与硬策略边界均可审计 | 通过：05C 标记 `已拍板`；A/B/C/D、六种语义、Must/Later/Out、接受代价、后果和验收均已写入；表达模型现由 05D 固定，target reference 绑定仍未决 |
| 05C 结构完整性 | 只固定 collision outcome，不重定义 05B shape、不偷跑 05D syntax 或 DEC-08 render | 通过：决策卡 16、独立决策轴 63、05C 决策节 1、验收场景 1、当前 DEC-05 状态 1；`git diff --check` 通过 |
| 05C 仓级回归 | 固化显式 overlay 意图后不破坏现有工程 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| 05D 表达模型决策 | source inventory、原生 payload、frontmatter/token 与两源隔离边界均可审计 | 通过：05D 表达模型标记 `已拍板`；A/B/C/D、Inventory/Payload 合同、Must/Later/Out、接受代价、后果和验收均已写入；target reference 绑定保持未决 |
| 05D 结构完整性 | 只固定 source representation，不新增 layer、不偷跑 target digest、DEC-06 binding 或 DEC-08 render | 通过：决策卡 16、独立决策轴 63、05D 决策节 1、验收场景 1、当前 DEC-05 状态 1；`git diff --check` 通过 |
| 05D 仓级回归 | 固化 inventory + 原生 payload 后不破坏现有工程 | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |

## 验证边界

- 直接运行 `uv run poe check` 时，仓内既有测试读取了本机真实 `XDG_CONFIG_HOME`，`test_identity_source_missing_root_is_actionable_json` 预期 `missing-source-root`、实际得到本机 overlay 的 `missing-src`。这不是本轮文档变更引入的代码失败。
- 使用空目录隔离 `XDG_CONFIG_HOME` 后完整仓级检查通过；本轮没有修改测试或实现来掩盖该环境耦合。
- 首次 YAML 校验脚本未允许 Ruby `Date` 类型而停止；加入 `permitted_classes: [Date]` 后安全解析通过，属于验证脚本修正，不是 YAML 内容修复。

## 尚未产生的证据

- DEC-05D target reference 绑定与 DEC-06—DEC-16 的拍板结果：后续逐项写入 `design.md`。
- capability spec / ADR：所有相关决定稳定后再蒸馏。
- 实现与 runtime 验证：不属于本设计阶段。
