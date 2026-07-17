# Agent 配置控制面能力拍板工作台

## 文档契约

| 项 | 约定 |
|---|---|
| 读者动作 | principal 通过与 operator Agent 对话，按依赖顺序逐项选择能力语义；operator Agent 负责澄清、生成真实候选、说明推荐与代价，并把结果写回 |
| 生命周期 | `capture/` 是不可变诉求快照；本文在能力拍板和蒸馏期间持续更新，结论进入 ADR/spec 后删除本文，不保留待维护的提案副本 |
| 交付形态 | living decision workbench；它不是当前架构真相，也不是实现计划 |
| 证据规则 | 每个决策轴必须包含范围、候选、推荐理由、principal 明示决定、被拒选项、后果、依赖影响和可验证断言 |
| Gate | 诉求不清时先澄清；上游项未定不得偷跑下游实现；能力契约稳定前不做 build/buy/retire 选择 |

语域：中性、精确、可审计。本合同先定义“需要什么能力”，不预设由 Almagest、gaal、`npx skills`、Agent 原生能力或新组件承载。Almagest 当前只是候选承载者和本需求包所在的代码仓。

## 目标与成功口径

Agent 配置控制面 v1 应能对任意**已声明 target** 回答以下问题。DEC-02A/02B 已确定 target identity 为 `host_id + consumer_instance_id`；OS、consumer version、binary/root、profile 和 workspace 是观测属性或 selector，不进入 target identity：

1. 目标应当拥有哪些资产，来自哪个权威 source 和 overlay；
2. apply 前会 add/remove/change/shadow/block 什么，为什么；
3. apply 后 live 配置与 active root/profile/workspace 等绑定事实是否符合目标；
4. 发生配置漂移时，差异来自 source、resolve、render、projection、live 还是绑定输入；
5. personal/shared 与 work-local 的驻留/投影边界，或 public/private 边界是否被违反。

consumer 是否已 parsed/registered、discoverable/enabled、callable 或 observed-used，以及 runtime drift 如何归因，是控制面完整能力地图中的 `Later` 分支，不是 v1 配置一致性的成功门禁。后续可以拍板其证据合同，但不得反向阻塞 v1 的 plan/apply/config-drift 闭环。

当前阶段采用“配置一致优先”：v1 先保证每个 target 的 declared → resolved → rendered → live 配置与其目标状态一致，并能在 apply 前报告差异、apply 后检查漂移。“一致”不是要求 Mac/Windows 配置字节相同，而是 Mac 各 consumer 符合 `GitHub personal/shared base + Mac-local work overlay`，Windows 各 consumer 符合 GitHub base 的目标状态。

这里必须区分三种对象，不能再用“配置/运行时”二分法一刀切：

1. **受管配置**：人有意声明、会改变 Agent 行为或能力面的 desired state；v1 负责解析、渲染、投影和漂移检查。
2. **绑定与依赖观测**：不由 v1 安装或维护，但会决定哪个配置被消费、或该配置能否成立的事实；v1 必须盘点并参与 plan/verify，不能当成无关主机环境。
3. **运行态与生成状态**：进程、执行结果、缓存、会话等；不属于 v1 配置一致性承诺，后续另行决定是否治理。

因此，“不负责安装/运行”不等于“不看”。例如 v1 不升级 Codex binary，但必须知道 consumer 产品、版本、路径和配置 schema；不管理整个 shell，但若 wrapper、alias、启动参数或环境变量选择了 `CODEX_HOME`、profile、workspace 或 settings source，就必须纳入受管配置或绑定观测。

## 操作者与批准者模型

Almagest 的主要调用者不是直接操作 CLI/TUI 的人，而是受 principal 指挥的 AI Agent。principal 用自然语言表达目标、裁决歧义并批准所有非 `no-op` 配置变更；operator Agent 调用、解释并驱动流程；Almagest 只做确定性的 plan/apply/verify 和策略执行。

```text
Principal（目标、歧义裁决、逐变更批准）
  └─ Operator Agent（Codex / Claude / QoderCLI；调用、解释、提交批准、重试）
       └─ Almagest（确定性解析、预演、实施、验证、审计）
            └─ Consumer config（被治理的 Codex / Claude / Qoder 配置）
```

每次调用都绑定当前 host，并在本次操作中当场完成（in-operation / in-time）：Mac 上的 Agent 只调用 Mac 本机 Almagest，Windows 上的 Agent 只调用 Windows 本机 Almagest。Almagest 不远程操作另一台机器，不设中央控制端，也不生成跨机汇总报告；principal 需要处理哪台机器，就在该机器的 Agent 会话中取得本机结果并决策。

这一定义带来以下全局约束：

1. canonical interface（规范主接口）必须是稳定、非交互、机器可消费的命令/API 合同，提供结构化 schema、诊断码、退出码、plan/receipt ID、provenance、diff 和可选 resolution action；具体传输形态留给实现阶段。
2. 默认输出应紧凑，只返回 Agent 做下一步判断所需的摘要和引用 ID；详细 provenance、diff 与解释按 ID 按需获取，避免每轮把完整证据塞进上下文。
3. principal 不需要直接解析原始 plan、编辑配置或操作 `[y/N]` prompt。operator Agent 负责把结构化结果翻译成人话、请求拍板，再提交绑定该决定和精确 plan hash 的 approval artifact。
4. principal 的批准责任与 operator Agent 的执行身份必须分开记录。Agent 可以自主做只读 inventory/plan/verify，但任何非 `no-op` 写计划都必须先报警并取得 principal 对当前精确 plan 的批准；Agent 不得把自己的推断冒充批准。
5. 面向人的 TUI、wizard 或 dashboard 不是 v1 必需能力；未来即使增加，也只能是同一机器合同的客户端，不能形成第二套 authority 或行为语义。

这里的 operator Agent 与 consumer 是两个角色：前者是本次调用 Almagest 的执行主体，后者是配置被投影给的目标实例。同一产品可能同时扮演两者，但在 plan、approval 和 receipt 中不得混用身份。

## 已知目标拓扑

| Host | OS | Consumer | 允许的 source | 仍需取证 |
|---|---|---|---|---|
| Mac 工作机 | macOS | Codex | GitHub personal/shared base + Mac-local work overlay | v1：产品版本、roots、precedence、profile；Later：runtime probe |
| Mac 工作机 | macOS | QoderCLI | GitHub personal/shared base + Mac-local work overlay | v1：产品版本、多 roots、precedence、profile、frontmatter；Later：runtime probe |
| Windows | Windows | Codex | GitHub personal/shared base | v1：产品版本、roots、precedence、profile；Later：runtime probe |
| Windows | Windows | Claude，具体产品待确认 | GitHub personal/shared base | v1：Claude Code/Desktop/其它、产品版本、roots、precedence、profile；Later：runtime probe |

这张表只记录已知消费范围。Mac 上没有并列的 personal/work consumer context；每个 consumer 只有一个 target，其 resolved state 是允许进入该 host 的 source overlay。“文件写到了某个目录”仍不等于 consumer 已加载。

## 关键术语

| 术语 | 工作定义 |
|---|---|
| asset | 被治理的 skill、MCP、instructions、settings、hook、plugin 等能力单元；确切范围由 DEC-01 决定 |
| principal | 通过自然语言给出目标、裁决歧义并批准每个非 `no-op` 配置计划的人；不承担日常 CLI/TUI 操作 |
| operator Agent | 代表 principal 调用 Almagest、解释结构化结果、提交批准和驱动重试的 AI Agent |
| consumer | 消费配置的稳定 Agent 实例，例如 Codex、QoderCLI、Claude；具体产品版本是该实例的观测属性 |
| source | 对声明内容拥有权威性的来源；cache、rendered artifact 和 live target 默认不是 source |
| root | consumer 会搜索或读取的物理目录/配置入口，一个 consumer 可以有多个 root |
| target | 稳定消费端，identity 为 `host_id + consumer_instance_id`；OS、版本、路径和 profile 等是属性或 selector |
| profile | 同一 consumer 的一组显式运行配置；当前不是独立 target identity |
| placement/residency policy | 声明 source/asset 允许出现、缓存、渲染和投影到哪些 host；work-local 内容只允许留在 Mac 工作机 |
| layer | 拥有 authored configuration authority、可参与 resolve 的声明层；v1 只有 GitHub personal/shared base 与 Mac-local work 两层，host/OS/consumer/profile/root 和本机绑定均不是 layer |
| overlay | 多个 layer 按确定规则合成 resolved desired state 的机制；不同 asset 类型可以有不同 merge algebra |
| resolved | source 与 policy 解析后的目标状态，尚未适配 consumer 格式 |
| rendered | 为具体 consumer/target 生成的派生 artifact，必须可追溯到 source 和 renderer 版本 |
| live | target 文件系统或配置存储中观察到的状态 |
| effective | 分级证据，而非单个布尔值：present → parsed/registered → discoverable/enabled → callable → observed-used |
| projection | 把获批的 rendered desired state 应用到具体 target |
| receipt | 一次 plan/apply/verify 的输入、动作、结果和证据记录 |
| fixture | 用于验证 consumer adapter、格式与跨 OS 行为的固定测试样本 |
| fail closed | 缺少身份、策略、本地值或证据时停止危险动作，不把未知当成功 |

## 逐项拍板协议

每次只处理一张卡中的一个决策轴：

1. Codex 先复述该轴要解决的问题、已知事实和证据边界。
2. 信息不足时只问 1—2 个高杠杆问题，暂不生成假选项。
3. 信息足够后给 2—4 个真实候选，并优先用 A/B/C/D 命名；只有一个可行项时改做“约束确认”。
4. 同一决策轴的候选必须互斥；不同轴独立拍板后可以组合。principal 提出混合方案时，Codex 先把它写成一个显式新候选，再请求确认。
5. Codex 给出推荐、收益、代价、风险和可逆性；只有 principal 明示选择后才能标记 `已拍板`。
6. 每个轴写回 decision version/date、决定、理由、被拒选项、后果、验收断言和对后续卡片的影响。
7. 每张卡同时把能力分入 `Must / Later / Out`；卡内所有轴完成后才进入下一张卡。
8. 上游决定重开时，列出并重审所有受影响的下游卡片。

状态词：`待澄清`、`待给方案`、`待拍板`、`已拍板`、`需重开`。

## 拍板顺序总览

| ID | 能力 | 核心拍板问题 | 完成本项后得到什么 |
|---|---|---|---|
| DEC-01 | 资产范围与身份 | v1 管什么；每类资产如何获得稳定身份 | 资产类型清单与 identity contract |
| DEC-02 | 目标拓扑与隔离能力 | target 由哪些维度组成；物理环境能否承载所需隔离 | target key 与 capability/unsupported 规则 |
| DEC-03 | 权威来源与信任 | 谁拥有真相；外部来源和可执行内容如何受信 | source authority 与 supply-chain policy |
| DEC-04 | Source 驻留与投影策略 | personal/shared 与 work-local 如何组合、允许、阻断并执行无例外驻留 | placement/projection policy 与防泄漏约束 |
| DEC-05 | Overlay 与解析 | 两个 authored layer 及各类 asset 如何合成、删除和冲突 | 确定性 resolved desired state |
| DEC-06 | Secret 与本地参数 | secret、路径、账号和 host 差异放哪里 | 不泄漏且可移植的 local-value contract |
| DEC-07 | Inventory | source、resolved、rendered、live、effective 各盘点什么 | 有证据边界的全状态清单 |
| DEC-08 | Consumer 可见与渲染 | 多 root、shadow、frontmatter、格式转换后 consumer 看见什么 | per-consumer visibility/render contract |
| DEC-09 | 变更预演 | apply 前必须报告并固定哪些差异、输入和风险 | 可审批且可复现的 plan contract |
| DEC-10 | 安全实施 | ownership、计划等价、原子性、幂等、备份和恢复怎么做 | apply safety contract |
| DEC-11 | Effective 验证（Later） | 如何分级证明 Codex/Qoder/Claude 真正加载或使用 | runtime evidence contract，不作为 v1 gate |
| DEC-12 | 漂移检查 | 查什么、何时查、谁负责、何时自动修 | drift/reconcile policy |
| DEC-13 | 跨机配置一致性 | 共享 source 下两台机器如何各自在本机达到正确状态并处理离线、版本错位 | independent per-host config contract |
| DEC-14 | 配置资产生命周期 | bootstrap、import、迁移、升级、废弃和恢复怎么走 | config lifecycle state machine |
| DEC-15 | Consumer 兼容与扩展 | 新 consumer/root/格式如何描述、接入和测试 | compatibility/extension contract |
| DEC-16 | 审计与可解释性 | 谁在何时把什么从哪里投影到哪里，为什么生效 | audit/receipt/explain contract |

### DEC-01A 选择 B 后的方向约束

这张表只记录由 01A 已拍板边界直接推导出的阶段归类，不替代后续卡片的机制拍板。任何候选若要突破这里的 `Must / Later / Out`，必须显式重开 DEC-01A，不能在下游卡中顺手扩权。

| ID | v1 posture | 不得漂移的边界 |
|---|---|---|
| DEC-02 | Must | target 必须覆盖 active config 绑定；不管理 consumer binary 生命周期 |
| DEC-03 | Must | 管 source authority、revision/digest 与可执行配置信任；不因此承担包安装或服务运行 |
| DEC-04 | Must | 管 personal/shared 与 work-local 的驻留/投影；work 内容不得进入 Windows 或非授权中间产物 |
| DEC-05 | Must | 管 13 个配置域的 deterministic overlay；不 merge cache/session/generated state |
| DEC-06 | Must | 管 secret schema/reference/local binding 与脱敏；secret value 仍由本机 credential provider 持有 |
| DEC-07 | Must + Later | v1 盘点 source/resolved/rendered/live 和 6 类绑定事实；effective 高阶证据属于 Later |
| DEC-08 | Must + Later | v1 做格式渲染、静态 visibility/shadow；consumer runtime 确认属于 Later |
| DEC-09 | Must | plan 只覆盖受管配置投影及其绑定风险，不生成 runtime/host 生命周期动作 |
| DEC-10 | Must | 原子性、备份和 rollback 只针对受管配置资源，不升级为整机事务或进程恢复 |
| DEC-11 | Later | 可以定义 runtime evidence contract，但不能成为 v1 apply/config-drift 的前置 gate |
| DEC-12 | Must + Later | source→live/binding drift 是 v1；effective/runtime drift 与自动恢复是 Later；daemon 生命周期 Out |
| DEC-13 | Must | 两台机器各自通过本机 Agent 达到目标配置；不上传 receipt、不做跨机汇总、不设中央控制端或管理远端进程 |
| DEC-14 | Must + Out | 管配置 bootstrap/import/migrate/deprecate/restore；host、binary、plugin package 生命周期 Out |
| DEC-15 | Must + Later | config capability/adapter/fixture 是 v1；runtime probe 兼容属于 Later |
| DEC-16 | Must + Later | v1 审计配置 plan/apply/verify；runtime failure/evidence 的审计扩展属于 Later |

## 决策卡

所有卡片进入讨论时都要补：`Must/Later/Out`、候选、推荐、decision version/date、principal 决定、被拒选项、理由、后果、依赖影响和最终验收。

### DEC-01 资产范围与身份

- 状态：01A、01B、01C 已拍板
- 决策轴：
  - 01A：v1 纳入哪些 asset 类型：skill、MCP、instructions、settings、hooks、plugins 或其它。
  - 01B：每种 asset 的 identity granularity 与 canonical ID 由哪些字段构成。
  - 01C：如何区分同一资产、版本/revision、consumer 派生物、冲突副本和无关同名资产。
- 01A 历史决定（v0.2，2026-07-16，approver: principal）：选择 B——v1 纳管完整 Agent **配置面**，先保证配置一致；运行生命周期和行为正确性以后再考虑。这个方向继续有效，但“完整配置面”的枚举不完整，且旧 `Out` 把配置绑定误归为主机环境，所以 v0.2 不能继续视为最终范围拍板。

| v0.2 候选 | 配置范围 | 责任边界 | 结果 |
|---|---|---|---|
| A | skills、MCP、instructions、settings、hooks 配置 | 不纳管 plugin 配置 | 拒绝：plugins 也必须进入配置一致性范围 |
| B | A + plugins 配置 | 保证 declared/resolved/rendered/live 配置一致；不负责 hook 执行、plugin 包安装/升级、依赖解析或运行结果 | **已选择** |
| C | B + plugin 包、wrapper、alias、Agent binary 和实际运行行为 | 进一步负责安装、版本、进程、执行验证与恢复 | 拒绝作为 v1：超出“先保证配置一致” |

#### 旧 `Out` 到底指什么，以及边界修正

| 旧名词 | 原意 | v0.3 修正后的归类 |
|---|---|---|
| Agent binary | `codex`、`qodercli`、`claude` 可执行文件本身、安装渠道和升级 | 安装/升级 `Out`；产品、版本、路径、支持的 schema/capability 是必须观测的 target 元数据 |
| wrapper | 在真正 binary 前设置参数、环境变量、profile、代理或工作目录的脚本/启动器 | 若决定配置 root、profile、workspace 或 settings source，则 wrapper 声明属于受管配置；其解析结果必须观测。与 Agent 无关的通用 wrapper 才是 `Out` |
| shell alias/function | 把短命令映射到 binary、参数或环境的 shell 绑定 | 同 wrapper；不能因位于 shell dotfile 就整体排除。v1 不接管整份 shell 配置，只治理/观测与 target 绑定有关的片段 |
| 进程 | Agent、MCP、daemon、hook 子进程的启动、停止、守护和恢复 | 进程生命周期 `Out`；若进程实际启动参数可安全取得，可作为 Later 的 effective 证据 |
| 完整主机环境 | OS、包管理器、全部 PATH、shell、系统服务、代理、运行时与其它 dotfiles | 整体 `Out`；但 OS、home/config root、路径、所需 executable 是否存在等配置相关事实属于绑定/依赖观测 |

本机已出现实际反例：`qodercli` 与 `/usr/local/bin/qoder` 指向的不是同一产品入口；Codex 还可能被 `CODEX_HOME`、`--profile`、单次 `-c`、项目 trust 和项目级 `.codex/` 层改变最终配置。如果不记录这些绑定，系统可能在错误 root 上得到“无漂移”的假阳性。

#### v0.3 全量配置候选清单

以下清单按“会不会改变目标 Agent 的声明行为/能力”收口，不按某一家产品当前目录名收口。厂商没有对应能力时标为 unsupported，而不是静默忽略。

| 配置域 | 典型内容 | v1 候选责任 |
|---|---|---|
| 指令与持久上下文 | `AGENTS.md`、`CLAUDE.md`、rules、imports、author-written memory/instructions、fallback filenames、大小限制与 precedence | 受管配置；自动生成 memory、会话摘要和历史不在此列 |
| Skills | skill 本体、scripts/references/assets、启用/禁用、root、scope、frontmatter、override、依赖声明与 lock/source revision | 受管配置；consumer 触发或执行成功属于 Later |
| MCP、apps 与 connectors | server/app 声明、transport、command/url、tool allow/deny、scope、OAuth/credential reference、启用状态 | 受管配置；secret value 本机化；服务进程、登录会话和连通健康属于 Later |
| 模型与推理默认值 | model/provider/base URL reference、reasoning、context、输出限制、feature flags、实验能力 | 受管配置；模型缓存与下载状态 `Out` |
| 权限与安全策略 | approval、sandbox、filesystem/network permission、tool allow/deny、trust、managed policy/requirements | 受管配置；不得被未受权 local state 绕过 |
| Profiles、scope 与层级 | user/project/local/managed scope、profile、workspace/project layer、source class、settings source、precedence、overlay 与 CLI/config override policy | 受管配置；实际启动选择结果必须观测 |
| Hooks | 事件、matcher、顺序、类型、timeout、command/prompt/agent/http/MCP target，以及受管 hook script 内容 | 受管配置；是否执行、退出码和副作用属于 Later |
| Plugins、extensions 与 marketplace | manifest、source/ref/version constraint、marketplace/registry、enabled state、override、plugin 所带 skills/agents/hooks/MCP/apps/LSP/bin 声明 | 受管配置；实际安装包、cache、依赖安装和运行健康只观测或 Later |
| 自定义 agents/subagents | role、description、instructions、model、tools/MCP、skills、permissions、sandbox、并发/深度限制 | 受管配置 |
| Commands、prompts 与输出交互 | custom commands/prompts、output styles、status line、notification command；已废弃 surface 仍需 inventory/migrate | 受管配置；废弃项的迁移时机由 DEC-14 决定，不得因废弃而漏盘点 |
| Agent 客户端偏好 | CLI/TUI/IDE language、theme、layout、更新频道、遥测、索引等 user-authored settings | 受管配置；只管理用户声明值，不同步 telemetry event、index 或其它生成数据 |
| Secret 与本地参数 | token、OAuth 状态、账号、credential store、绝对路径、machine ID、proxy/local endpoint | 只受管 schema、reference、required/optional 和本地绑定；不跨 source residency/host 边界复制 secret value |
| 控制面元数据 | asset identity、source authority、digest/revision、adapter/schema version、ownership、lock、policy 与 receipt | Almagest 自身必须受管，否则无法解释或重现配置 |

#### 必须观测但不由 v1 安装维护

| 观测对象 | 为什么不能遗漏 |
|---|---|
| consumer 产品、版本、binary path、配置 schema/capability | 同一文件在不同产品/版本中可能含义不同，甚至不被识别 |
| 实际 config root、home、active profile/workspace、project trust | 决定加载哪一层配置 |
| wrapper/alias/function/启动参数/相关环境变量的解析结果 | 可能把同一命令路由到另一个 binary、root 或 profile |
| plugin/extension 实际安装版本与 package digest | enabled 配置只有在对应包存在且版本兼容时才有意义；v1 只报告，不负责安装 |
| hook/MCP/skill script 所需 executable、文件和本地 endpoint 是否存在 | 区分“配置一致”与“依赖缺失”；v1 不自动修复主机依赖 |
| OS、路径语义、filesystem capability 和 consumer roots | 支撑 Mac/Windows 渲染与 unsupported 判断 |

#### v1 仍然明确不负责

- Agent binary、plugin package、系统依赖和模型的安装、升级、卸载。
- Agent/MCP/daemon/hook 进程的启动、停止、守护、重试和恢复。
- hook/MCP/plugin/skill 的业务执行正确性、性能和副作用治理。
- cache、log、history、transcript、session、telemetry event、代码索引和模型缓存等生成状态的一致化。
- 整机 dotfiles、包管理器、shell、PATH、代理、系统服务和 OS 策略的通用管理；只有与 Agent target 绑定直接相关的最小片段进入上面的受管/观测范围。

#### 01A v0.3 已拍板：B

| 候选 | 范围 | 主要代价 |
|---|---|---|
| A：核心行为配置 | instructions、skills、MCP、模型/权限 settings、hooks、plugins、agents | 仍会漏掉 profile/root/override、启动绑定、commands/UX 等导致的有效配置差异 |
| B：全部 user-authored Agent 配置 + 绑定观测 | 纳入上面全量候选清单；管理配置声明，观测 binary/安装包/依赖和启动绑定，不管理其生命周期 | adapter 和 inventory 范围更大；必须把“managed / observed / generated”标清 |
| C：Agent runtime fleet | B + binary/plugin/依赖安装、进程、执行健康、自动恢复 | 重新进入此前否决的运行平台范围，明显超出“先保证配置一致” |

- 决定（v0.3，2026-07-16，approver: principal）：选择 **B——全部 user-authored Agent 配置 + 绑定观测**。核心原则是“所有 user-authored Agent 配置都列入，所有决定配置消费结果的绑定都观测，所有生成状态与生命周期都不接管”。
- 理由：B 修复旧清单漏项，能发现 active root/profile/override、wrapper/alias/env 等造成的配置漂移，同时不把 Almagest 扩成 binary、plugin、进程和主机环境的生命周期管理平台。
- 被拒选项：A 因无法覆盖配置绑定、commands/UX 等完整有效配置而拒绝；C 因引入安装、进程、执行健康和自动恢复责任，超出“配置一致优先”而拒绝。
- `Must`：上表 13 个配置域的声明、overlay、consumer render、projection、diff 与漂移检查；并盘点上表 6 类绑定/依赖事实。commands/prompts/output 与客户端偏好中的 user-authored 值明确纳入，不再留待本项后续拍板。
- `Later`：consumer 是否实际 discover/call、hook/skill/plugin/MCP 是否成功执行、安装依赖是否健康、runtime probe 与自动恢复；具体证据等级由 DEC-11 决定。
- `Out`：binary/plugin/系统依赖/模型安装升级、进程生命周期、业务执行正确性、生成状态一致化和整机通用环境管理；但其与 target 直接相关的最小事实仍须观测。
- B 的边界示例：系统证明“目标声明启用 plugin X、当前安装版本为 V、注册 hook Y、active profile 为 P，live 配置与声明一致”；它不承诺安装 X、启动相关进程或证明 Y 已成功执行业务逻辑。
- 后果：DEC-01B 已为 13 个配置域和 6 类观测事实确定 identity 边界；DEC-01C 使用不可变 revision、类型化派生元数据与 Git-backed lineage 定义 version/derivation/conflict 关系。DEC-02、DEC-06—DEC-12 的候选生成必须使用受管配置、绑定观测、运行/生成状态三分模型。adapter 与 inventory 的范围扩大，但安装和运行责任不随之扩大。
- 验收断言：系统能枚举每个 target 的 user-authored 配置、绑定输入和生成状态并明确分类；任何 active root/profile/override 未知时不得报告“无漂移”；每个纳入类型最终都具备 identity、version、overlay、render 和 ownership 规则。

#### 01B 已拍板：分层逻辑 ID + 投影实例 ID

本轴只决定“什么变化后仍算同一个资产”以及 canonical ID 的稳定字段，不决定 revision/copy/conflict 的完整判定算法；后者留给 01C。已拍板的 01A 要求 identity 同时覆盖 13 个受管配置域与 6 类 target-scoped 观测事实。

| 候选 | Canonical identity | 收益 | 主要问题 |
|---|---|---|---|
| A：物理位置 ID | `consumer + scope/root + path/config-key` | inventory 最直接，不需要额外 registry | 移路径、换 OS、换 root 就变成新资产；同一逻辑资产跨 Mac/Windows 无法对齐 |
| B：单层逻辑 ID | `kind + name`，文件或顶层对象作为最小单元 | 简单、可移植，足以覆盖 skill/plugin/MCP 等命名对象 | settings/hooks/instructions 易碰撞或被迫整文件覆盖；无法稳定表达子资源与多投影 |
| C：分层逻辑 ID + 投影实例 ID | logical asset 使用 `kind + namespace + name + optional stable subresource`；projection instance 另用 `asset_id + target_id + consumer_slot` | 路径、版本、source、target 变化不会误改逻辑身份；可表达 overlay、跨机同源和 consumer 派生物 | schema 较 B 复杂；ordered hooks/list item 等必须补显式稳定 ID |
| D：内容寻址 ID | digest 直接作为 asset ID | 去重和完整性强，天然固定内容 | 每次编辑都变成新资产；人不可读；无法表达“同一资产的新 revision” |

- 决定（v0.1，2026-07-16，approver: principal）：选择 **C——分层逻辑 ID + 投影实例 ID**。logical asset 使用 `kind + namespace + name + optional stable subresource`；projection instance 使用 `asset_id + target_id + consumer_slot`。逻辑身份回答“它是否仍是同一项资产”，投影身份回答“这项资产被放到哪个 target 的哪个 consumer 槽位”。
- 理由：C 是唯一同时覆盖命名资产、字段/片段级配置、多 target 投影和跨 consumer 派生物，且不把路径、内容版本或主机属性误当逻辑身份的候选。它能支撑 01A 已纳入的 settings、hooks、instructions 等复杂配置，也能让 skill、MCP、plugin 等天然命名对象保持简单。
- 被拒选项：A 因路径/root/OS 变化会制造伪“新资产”而拒绝；B 因 settings、hooks、instructions 容易退化为整文件覆盖，且多投影不是一等对象而拒绝；D 因内容一变就失去同一资产的版本连续性而拒绝作为 logical identity。revision 与完整性机制不由 01B 决定，留给 01C。
- `Must`：logical asset 与 projection instance 使用不同 ID 空间；所有受管配置都能映射到稳定 logical ID；所有 target 投影都能映射到稳定 projection ID；有序项、命名片段和 adapter 原子对象不得依赖数组下标或临时路径。
- `Later`：DEC-11 引入的 runtime evidence 可以引用 logical/projection ID，并为 observation 增加证据实例；不得反向改变本次 logical identity。
- `Out`：把 digest、live path、root、host/OS、consumer version、layer、secret value 或数组下标直接作为 logical asset ID。
- C 的 granularity 规则：以“可独立声明、override、mask/remove 和审计”的最小语义资源为 identity 边界。命名对象使用对象 ID；map 使用稳定语义 key 或 adapter 声明的原子 object；有序列表使用显式 item ID，不使用数组下标；instructions 使用声明片段/文件级 ID，不给任意段落造 ID。
- C 的字段边界：`source authority/location`、layer、revision/version/digest、host/OS、consumer version、root/path 都是 provenance、selector、revision 或 projection 属性，不进入 logical asset ID。DEC-02 尚未确定的 target key 只进入 projection/binding identity。
- 观测事实：binary path、active profile、wrapper 解析等不冒充 portable asset；使用 `target_id + binding_kind + stable binding name` 标识 observation subject，并附采集时间和 evidence。
- 后果：DEC-01C 必须在 logical identity 之上定义 revision、consumer render、copy/conflict 和同名隔离，不得再用 digest 替代 logical ID；DEC-02 必须提供稳定 `target_id`；DEC-05/08/10/12/16 的 overlay、render、apply、drift 和 receipt 必须分别引用 logical/projection ID。adapter/schema 需要为可独立覆盖的有序项和片段提供稳定 ID，并承担一次性迁移成本。
- 验收断言：资产改路径、换 target、产生 consumer render 或内容 revision 后仍可追溯为同一 logical asset；同一 logical asset 的两个 target/consumer 投影具有不同 projection ID；两个无关同名对象不会因 basename 相同发生碰撞；任何 ID 不依赖数组下标、临时路径、secret value 或内容 digest。

#### 01C 已拍板：不可变 revision + Git-backed lineage

本轴在 01B 的 logical/projection ID 之上决定版本、consumer 派生物、copy 与 conflict 如何判定。source authoring history 与配置控制面的 revision evidence 分工处理，不由 Almagest 复制一套 Git。

| 候选 | Version / lineage 模型 | 结果 |
|---|---|---|
| A：可变 current pointer | logical asset 只保存当前 version label/digest | 拒绝：旧 plan/receipt 难复现，copy、render 与 conflict 只能靠推断 |
| B：不可变 revision + 类型化派生元数据 | Almagest 固定 source revision、render inputs/output 与 projection receipt；Git source 的 parent/fork/merge/history 按需从 Git 查询 | **已选择** |
| C：Almagest 自建 VCS lineage | B + 内建 parent/fork/merge/copy 图与历史查询 | 拒绝：重复 Git，并引入 merge ancestry、历史修剪和跨 source 对齐责任 |
| D：全事件 provenance DAG | resolve、overlay、render、projection、apply 全部成为不可变事件节点 | 拒绝：存储、查询、schema 和隐私成本过高，扩成通用 provenance 平台 |

- 决定（v0.1，2026-07-16，approver: principal）：选择 **B——不可变 revision + 类型化派生元数据，并采用 Git-backed lineage**。Almagest 保存当前 plan/apply/verify 所需的精确 revision 与派生证据；若 source 是 Git，authored history、parent、fork、merge 和 source diff 由 Git 提供，Almagest 按需查询而不复制 revision graph。
- revision 规则：logical ID 相同表示同一资产；`asset_revision_id` 由 canonicalizer/schema version 与 content digest（Git 可使用等价 blob/tree identity）固定 authored content；`source_snapshot_ref` 另存 authority/repository、commit/ref 与 path，固定 provenance 输入。同一内容跨 commit 可保持相同 asset revision，但 source snapshot 不同；不同 logical asset 不因 digest 相同而合并。非 Git source 同样分开保存 authority/ref 与 canonical content digest。
- 派生规则：consumer render 记录 `source_revision(s) + adapter identity/version + consumer capability/version + relevant selectors + render digest`；projection receipt 引用预期 source/render revision。同一 logical/revision 出现在不同 projection 是 copy/mirror；带明确输入和 renderer 元数据的是 consumer 派生物。
- conflict 规则：同一 resolution context 中，多个候选争用同一 logical ID 且 authority/precedence 无法唯一裁决时才标记 conflict 并停止；basename 相同但 logical ID 不同是无关同名。多 source overlay 记录精确输入集合，不伪造为单一 Git ancestry。
- `Must`：所有 plan 同时固定 source snapshot ref 与不可变 asset revision；所有 render/projection 可追溯到精确输入、adapter/capability 版本和输出 digest；Git source 可按 snapshot ref 查询 authored history；非 Git source 不得伪造 parent/fork/merge。
- `Later`：若未来确有脱离 Git 的多方编辑、三方合并或长期 fork 管理需求，再重开本项评估 C；当前不预建 lineage graph。
- `Out`：在 Almagest 内实现通用 branch、merge、rebase、历史垃圾回收或全事件 provenance 平台；把 Git commit/digest 当作 logical asset ID；在 portable plan/receipt 中保存 secret value 或其可关联 digest。
- 后果：DEC-03 必须定义 owned source authority 与 revision 可信性；外部候选的发现、拉取、评审和吸收不进入 Almagest。DEC-05/08 必须输出确定的 resolved/render input set；DEC-09/10/12/16 必须使用获批 revision 与 receipt 做 plan 等价、apply、drift 和 explain。dirty source、secret/local binding fingerprint 与历史不可用时的具体处理分别留给 DEC-03、DEC-06 和 DEC-09。
- 验收断言：获批 plan 能固定全部 source revision、adapter/capability 输入和预期 render；相同 logical asset 的内容更新不会变成新资产；相同内容的无关资产不会因 digest 相同被合并；Git 历史不可用时仍可依 receipt 校验本次 revision，但不得声称已验证 ancestry；任何 conflict 都指出 competing candidates、authority/precedence 和停止原因。

### DEC-02 目标拓扑与隔离能力

- 状态：已拍板
- 依赖：DEC-01。
- 决策轴：
  - 02A：target key 包含哪些维度：host、consumer，以及哪些事实只作为属性。
  - 02B：work 是 target context，还是 source/asset placement 与 residency policy。
  - 02C：如何声明 target/consumer 的实际能力；`unsupported/unknown` 如何阻断，以及人工 break-glass（受审计的例外放行）如何显式承担降级。

#### 02A/02B 已拍板：稳定消费端 target + work-local 驻留策略

| 候选 | Target / work 模型 | 结果 |
|---|---|---|
| A：仅靠 source 不出现 | target 使用 host/consumer，但只靠 Windows 不 checkout work source 防泄漏 | 拒绝：迁移、打包或同步配置错误时没有显式 policy 阻断 |
| B：稳定 endpoint + placement/residency policy | target 为 `host_id + consumer_instance_id`；work 是 source/asset 的驻留与投影限制 | **已选择** |
| C：Mac personal/work 双 context | 为同一 Mac consumer 创建 personal、work 两个 target | 拒绝：真实消费是单 target 上的 base + work overlay，会制造虚假隔离 |
| D：通用动态 context | profile、workspace、env、CLI invocation 都参与 target identity | 拒绝：当前无此需求，target 爆炸并越过稳定配置边界 |

- 决定（v0.1，2026-07-16，approver: principal）：02A/02B 选择 **B——稳定消费端 target + work-local 驻留策略**。target identity 仅由 `host_id + consumer_instance_id` 构成；当前有 Mac × Codex、Mac × Qoder、Windows × Codex、Windows × Claude 四类 target，实际 `host_id` 与 `consumer_instance_id` 值留待受管 inventory 声明。OS、consumer version、binary path、config root、profile 和 workspace 是观测属性或 selector，不进入 target ID。
- source 拓扑：GitHub 上的 personal/shared base 由 Mac 与 Windows 共同消费；Mac 另有一份不进入 GitHub 的 work-local overlay，只能被 Mac 工作机上的 Codex/Qoder 消费。Mac effective config 是 `GitHub base + work-local overlay + consumer render`，Windows effective config 是 `GitHub base + consumer render`。
- residency 边界：work-local 应使用独立 source root，不以同一 GitHub checkout 内的 `.gitignore` 充当安全边界；它可以使用没有 GitHub remote 的 local Git，以复用 DEC-01C 的 Git-backed history。Almagest 对其自身管理的 discovery、cache、resolve、render、plan、receipt 和 live projection 全链路执行“不离开授权 Mac”的约束；通用 OS backup/cloud sync 不在本控制面承诺内，需由 host policy 保证。
- `Must`：稳定 host/consumer ID；target 属性与 ID 分离；personal/shared 与 work-local source eligibility 可审计；任何 Windows target 的 source、cache、resolved、rendered、plan/receipt 和 live 内容都不包含 work-local payload。
- `Later`：对单次 CLI/env invocation 的逐次 fingerprint 与 runtime 使用证明；当前只观测会改变默认 active config 的稳定绑定。
- `Out`：为当前不存在的 personal/work 双 context、任意 cwd 或单次 invocation 建永久 target；仅靠 `.gitignore` 宣称 work residency 已受保护；把 OS backup/sync 生命周期纳入 Almagest。
- 后果：DEC-03 定义 GitHub personal/shared 与 Mac-local work 的 authority/trust；DEC-04 定义 placement/egress deny、Mac union、无例外驻留和 work 元数据零离机；DEC-05 固定 overlay；DEC-06 只定义本机 binding 与脱敏合同，DEC-13 只定义各机本地如何从共享 base 达到目标状态，不得引入跨机报告。capability/unsupported 行为由下述 02C 独立决定。
- 验收断言：四个 consumer 均映射到唯一稳定 target；升级 consumer、改变 binary path/root 不产生新 target；Mac 两个 target 解析 base + work overlay，Windows 两个 target 只解析 base；任一 work payload 出现在 Windows 或未授权中间产物时必须被检测为 policy violation，而不是 drift success。

#### 02C 已拍板：默认阻断 + 单次 break-glass 二次确认

| 候选 | `unsupported/unknown` 行为 | 结果 |
|---|---|---|
| A：告警后自动跳过 | 继续 apply，自动省略不支持项 | 拒绝：容易把能力损失伪装成成功 |
| B1：绝对硬阻断 | 告警只能被确认已读，不能继续 apply | 拒绝：缺少 principal 要求的人工担责出口 |
| B2：默认阻断 + break-glass | 先阻断；对精确降级计划二次确认后，允许带审计地继续 | **已选择** |
| C：按 required/optional 自动分流 | required 阻断，optional 自动告警跳过 | 拒绝：把是否接受损失预先藏进字段分类，弱于逐次 principal 确认 |
| D：自动近似转换 | adapter 自动改写成 consumer 最接近的配置 | 拒绝：可能静默改变语义，并显著扩大 adapter 责任 |

- 决定（v0.1，2026-07-16，approver: principal）：02C 选择 **B2——默认阻断 + 单次 break-glass 二次确认**。Almagest 将 consumer capability 评估为 `supported`、`unsupported` 或 `unknown`；证据缺失、过期或无法判定时属于 `unknown`，不能乐观视为支持。
- 默认行为：plan 发现任何 `unsupported/unknown` 时先返回结构化阻断诊断，至少引用 target、受影响资产/字段、capability evidence、预期损失以及能否形成安全降级计划；operator Agent 向 principal 解释后请求现场拍板，未取得二次确认前不得写 live target。
- break-glass 合同：operator Agent 只能提交由 principal 明确作出的二次确认；该 approval artifact 只批准当前 target 的精确 plan/hash 与预计算降级动作，并要求记录理由。允许继续时只实施可安全拆分的可支持子集，明确省略获批的能力缺失项；不得借确认写入 adapter 无法证明安全的原始配置。若无法形成安全降级计划，仍保持硬阻断。
- 审计与状态：receipt 至少记录 target、plan hash、capability 状态及证据、被省略项、预期与实际损失、principal approver、operator Agent、理由、时间和结果。结果必须标记为 `applied_with_exception` 或等价非合规状态，不得报告为普通 `success/compliant`；source desired state 不因 override 被修改。
- 生效范围：override 仅对一次 plan/apply 有效；输入、target、capability evidence 或 plan hash 变化即失效，后续 apply 必须重新评估并再次确认。approval artifact 的认证、格式与传输载体由 DEC-09/10 决定；直接面向 principal 的交互式 prompt 不是 canonical gate，也不存在全局永久 `always allow`。
- 边界：B2 只处理 consumer capability gap，不把硬策略拒绝改造成可确认告警。source trust、secret 泄漏、work residency/egress deny 等禁止项仍由 DEC-03/04/06 fail closed；违反这些规则时不得生成可越过的降级计划。
- `Must`：三态 capability 判断；告警先于写入；默认阻断；逐 plan 二次确认；安全降级动作；完整 exception receipt；非合规状态持续可见。
- `Later`：用 runtime probe 证明 consumer 是否实际消费降级结果，以及据此更新 capability evidence；不阻塞 v1 的 config/binding 闭环。
- `Out`：静默跳过、自动近似改写、永久忽略某类 capability、operator Agent 自行批准、把 exception 当成功、通过 break-glass 越过硬策略拒绝，或在无法安全拆分时强行写入。
- 后果：DEC-07/08 必须给 capability observation、freshness 与降级渲染证据；DEC-09 必须返回机器可消费的阻断诊断、损失和精确 plan hash；DEC-10 实现 Agent 提交的二次确认、事务边界和 receipt；DEC-12/16 持续报告生效中的 exception 并可解释其来源。
- 验收断言：无绑定 principal 决定的 approval artifact 时，`unsupported/unknown` 导致零写入；确认后只执行 plan 中已列出的安全降级，receipt 可分别还原谁批准、哪个 Agent 执行、在什么证据下接受了哪些损失；plan 输入变化后旧确认不可复用；硬策略拒绝永远不能通过 B2 放行。

### DEC-03 权威来源与信任

- 状态：03A v0.2、03B1、03B2、03C、03D 已拍板
- 依赖：DEC-01、DEC-02。
- 决策轴：
  - 03A：GitHub personal/shared、Mac-local work、host-local binding 与派生目录各自能声明什么，ownership 如何分配；外部 registry/upstream 是否构成 Almagest source class。
  - 03B1：多个已获 authority 的候选仍无法由确定规则裁决时，如何输出结构化 conflict artifact、取得 principal 决定并决定该裁决的生效范围。
  - 03B2：检测到 cache、resolved、rendered 或 live 反向污染 source 后，是否自动隔离/恢复，以及如何阻断、取证和取得 principal 决定。污染证据类型、置信度和 freshness 合同由 DEC-07/16 细化。
  - 03C：外部候选的发现、检查、拉取、评审、吸收和周期调度是否属于 Almagest；吸收后的 owned revision 如何进入正常配置闭环。
  - 03D：是否按 skill、hook、MCP、plugin 等类型或风险等级区别审批，还是任何非 `no-op` 配置差异都统一报警并由 principal 实时处理。
- 初步验收：每个 resolved field/contribution 能追溯到允许的 owned authority；外部候选在吸收前对 desired state 零权威；最终裁决与输入 revision/digest 不可歧义；临时裁决不冒充稳定一致；任何配置写入均有当前精确 plan 的 principal 批准，硬策略拒绝 fail closed。

#### 03A 已拍板：按 source 类型固定 ownership

| 候选 | Authority 模型 | 结果 |
|---|---|---|
| A：GitHub 单一 authority | 所有 desired declaration 最终都进入 GitHub，其它位置仅保存派生物或参数 | 拒绝：无法容纳禁止进入 GitHub 的 work-local 内容 |
| B：按 source 类型固定 ownership | 每类 source 只在固定 authority scope 内声明内容 | **已选择** |
| C：逐 asset 自由指定 authority | 每个 asset 可指向任意 Git、本地或 registry source | 拒绝：当前规模不需要 per-asset authority registry，迁移和冲突成本过高 |
| D：多 authority / last writer wins | GitHub、work、registry 与 live 均可改 desired state，以最后写入或最高版本为准 | 拒绝：无法区分有意修改与漂移，也无法稳定复现 |

- 决定（v0.1，2026-07-16，approver: principal）：03A 选择 **B——按 source 类型固定 ownership**。authority 表示某个 source class 有权声明哪类 authored intent 或内容；它不等于 overlay precedence。多个合法声明如何组合、override 或 mask 仍由 DEC-03B/05 决定。
- 修订（v0.2，2026-07-17，approver: principal）：保留 B 与固定 ownership 模型，但撤销 v0.1 中 `External registry/upstream` 作为 Almagest source class 的结论。Almagest 的 authority 只来自已归入 owned source 的 authored revision；外部 registry/upstream 只是控制面外的候选提供方，对 desired state 与 resolved content 均无 authority。

| Source class | 拥有的 authority | 明确不拥有 |
|---|---|---|
| GitHub personal/shared base | 两机共享的可移植 desired declaration；已吸收为自有资产的共享内容；consumer 配置自身需要的 package/ref/version 字段 | work-only payload、host secret value、本机路径值；尚未吸收的外部候选 |
| Mac-local work | work-only authored asset、work-specific delta 与已吸收为自有资产的 work-only 内容 | 向 Windows 投影的资格、GitHub base 的所有权、host secret value；尚未吸收的外部候选 |
| Host-local binding | 受 schema 允许的机器路径、账号/credential reference、本地 endpoint 与其它本机绑定值 | skill/instruction/hook/plugin 等可移植逻辑正文；任意绕过 portable/work source 的配置重定义 |
| Resolved/rendered/cache/live | 无 authored authority；只保存派生结果、观测或 evidence | 反向成为 desired state，或以 live 修改自动覆盖 source |

- 外部边界：外部工具完成候选发现、检查、拉取、校验、评审与吸收；只有吸收进 GitHub personal/shared 或 Mac-local work 并形成 authored revision 后，内容才进入 Almagest。owned source 可以保留 upstream locator/revision/digest、吸收时间等 provenance；外部周期工具也可以读取 owned source revision/time 与这些元数据作为检查水位，但它们只是惰性元数据，不参与 authority、resolve 或自动更新。
- 配置值边界：若 consumer 的 user-authored plugin/extension 配置本身需要 registry、ref 或 version constraint，这些值仍可作为普通 desired data 管理和投影；Almagest 不据此下载 package，也不把所指 registry 内容变成 source。实际 package 安装版本继续只作为 DEC-01A 已确认的绑定/依赖事实观测。
- scope enforcement：每个 source 必须声明稳定 `source_id`、`source_class` 与 `authority_scope`。source 在 scope 外声明内容属于 authority violation，进入 plan 时直接阻断；不得把它降格成普通低优先级候选，也不得通过 DEC-02C break-glass 放行。
- overlap 边界：work source 可以声明 work-only asset 和允许的 work delta，但本项不决定它能否覆盖、删除或拼接 GitHub base 的具体字段；host-local 只能填入已授权的本机 binding slot。字段级冲突裁决、merge algebra 和本机值边界分别留给 03B1、05、06。
- `Must`：固定 owned source-class ownership matrix；所有 source 与声明可审计归类；外部候选吸收前零 authority；吸收后只以 owned revision 进入配置闭环；外部 provenance 不影响 resolve；派生/live 状态无 authority；越权声明 fail closed。
- `Later`：若未来出现多个团队独立维护同一 source class，再评估 namespace/team delegation；当前不预建通用组织级 authority service。
- `Out`：GitHub-only 伪单一真相、逐 asset 任意 authority、多主/last-writer-wins、自动 adopt live drift、把 registry/upstream 作为 Almagest source、让外部版本变化直接改变本地 desired state。
- 后果：03B1 只在已获 authority 且确定规则仍无法裁决的候选之间定义临时裁决；03B2 定义派生物反向污染后的处置，污染 evidence 合同由 07/16 细化；03C 固化外部采集/吸收面 Out 的边界；03D 对所有吸收后的配置差异采用统一逐变更审批；05 定义合法 layer 的 overlay；06 定义 host-local binding/secret contract；07/16 必须展示 authority provenance 与越权原因。
- 验收断言：每个 resolved asset/field 都能追溯到允许其声明的 owned source class；registry 发布新版本或外部 tag 漂移不会产生 Almagest plan；只有吸收后的新 owned revision 才可能改变 desired state；手改 live target 被报告为 drift 而不是新 source；GitHub base 出现 work-only payload、host-local 重写可移植逻辑或任意派生目录反向声明 desired state 时均阻断。

#### 03B1 已拍板：当前 plan 一次性裁决，修 source 必须显式指示

本轴只处理多个候选均已通过 03A authority 检查、但 DEC-05 的确定性 precedence/merge 规则仍无法唯一解析的冲突。authority violation、source trust、secret 泄漏和 work residency/egress deny 等硬策略拒绝不进入本轴。

| 候选 | 冲突裁决如何持久化 | 结果 |
|---|---|---|
| A：当前 plan 一次性裁决 | principal 为精确 conflict set 选择本次结果；source 与全局规则不变，下次 plan 重新阻断 | **已选择** |
| B：Almagest 持久化裁决规则 | 把选择保存为独立 resolution registry，后续自动复用 | 拒绝：会形成 source 之外的第二份配置真相 |
| C：必须先修 source | 不允许临时 apply；operator Agent 修改权威 source 后重新 plan | 拒绝作为默认：未经 principal 明确转向，不应自动扩大为 source 变更 |
| D：默认修 source，必要时持久化规则 | 同时支持 C 与 B，由系统或 Agent 决定路径 | 拒绝：默认动作和状态面过多，弱化 principal 对 source 修改的显式控制 |

- 决定（v0.1，2026-07-16，approver: principal）：03B1 选择 **A——当前 plan 一次性裁决**。默认流程是阻断并返回结构化 conflict artifact；operator Agent 解释候选、provenance、差异与影响，principal 只为当前精确 plan 选择结果。
- 单次裁决合同：approval artifact 必须绑定 target、plan hash、完整 conflict set、固定输入 revision、每个冲突的已选 candidate/action、principal approver 和 operator Agent。未取得完整选择时零写入；任一输入、冲突集合或 plan hash 变化即失效。
- source 边界：一次性裁决不修改 authored source、不创建永久 precedence/rule，也不允许 operator Agent 从本次选择推断“以后都这样”。只有 principal 明确要求“修 source”或等价动作时，Agent 才进入正常 source 变更流程，修改拥有 authority 的 source、生成新 revision 并重新 plan；该动作不复用本次临时裁决冒充 source approval。
- 状态与重复：apply 结果必须标记为 `applied_with_transient_resolution` 或等价 exception 状态，receipt 保存冲突、选择、理由和结果；不得报告为普通 `compliant`。由于 source 仍存在歧义，下次 plan 必须重新阻断并再次请求 principal 决定。
- `Must`：结构化 conflict artifact；默认阻断；逐 conflict 明确选择；approval 绑定精确 plan；source 零修改；exception receipt；下次重新阻断；显式“修 source”才允许持久变更并强制 replan。
- `Later`：若重复冲突造成不可接受的审批负担，再由 principal 重开本轴评估持久规则；当前不预建 resolution registry。
- `Out`：last-writer-wins、按 layer/时间猜测 principal 意图、自动修 source、Agent 自行批准、把单次选择升级为永久规则、复用已失效的裁决，或用本轴越过硬策略拒绝。
- 接受的代价：该选择保留了 principal 对每次歧义和 source 修改的完全控制，但不会让歧义 source 自动收敛；重复冲突会重复消耗审批，并使对应 target 保持 exception 而非稳定合规状态。
- 后果：DEC-05 必须先穷尽确定性 overlay/merge，只有真正歧义才产生 conflict；DEC-09 固定 conflict set、候选和 plan hash；DEC-10 验证 approval 与执行等价；DEC-12 持续报告未修 source 的冲突；DEC-16 分别解释 principal 选择、operator Agent 和 exception 状态。03B2 污染处置见下节。
- 验收断言：无完整单次裁决时冲突导致零写入；获批后只执行精确 plan 中逐项选择的结果且 source digest 不变；重新 plan 时同一 source 歧义再次阻断；只有 principal 明确要求修 source 后才生成 source diff/new revision，并必须基于新 revision 重新 plan。

#### 03B2 已拍板：阻断并告警，source 保持不动

本轴的输入是 Almagest 已根据受管 provenance/inventory evidence 将某个 source 内容识别为 downstream 反向污染；哪些证据足以形成 `confirmed/suspected/unknown`、证据何时过期，由 DEC-07/16 定义。本轴只决定一旦达到阻断条件后系统能否自行修改 source。

| 候选 | 检出污染后的默认动作 | 结果 |
|---|---|---|
| A：阻断并告警 | 停止 resolve/plan/apply，返回证据和恢复候选；source 不动，等待 principal 现场决定 | **已选择** |
| B：自动隔离 | 把疑似污染内容移出 source 到隔离区，再继续或重新 plan | 拒绝：即使可逆也会在未授权时修改 source |
| C：自动恢复 | 按 Git/已知 source revision 自动覆盖污染内容 | 拒绝：误判时可能覆盖合法 authored change |
| D：证据分级自动处置 | 证据确凿时自动隔离，其余情况走 A | 拒绝：仍把 source mutation authority 隐藏在证据分类中 |

- 决定（v0.1，2026-07-16，approver: principal）：03B2 选择 **A——阻断并告警，source 保持不动**。Almagest 返回机器可读 contamination diagnostic，由 operator Agent 解释；在 principal 明确指定下一动作前，不隔离、不删除、不恢复、不 adopt，也不继续生成可 apply 的 plan。
- 阻断合同：diagnostic 至少引用 `detection_id`、`source_id`、受影响 path/asset、observed digest、预期 source revision、downstream lineage/evidence、影响的 target/plan、风险和可选 recovery action。检测发生后允许继续只读 inventory/explain/取证；plan surface 只能返回 block-only record，所有依赖该 source 的 resolve、可执行 action 和 apply 均停止且零写入。
- principal 决策边界：principal 可以要求继续取证、判定误报，或明确选择隔离、删除、恢复、重写/接纳为 authored content 等修复动作。operator Agent 只能执行被明确指定的动作；若要接纳 downstream 内容，必须转成由合法 authority source 承载的显式 authored change，不能把 cache/rendered/live 本身重新标成 source。
- 恢复出口：任何 source 修复都必须留下 before/after evidence，形成新的 source revision/snapshot，并重新执行 inventory → resolve → plan；旧 plan、03B1 单次裁决和 DEC-02C break-glass 均不能绕过 source contamination block。
- `Must`：污染诊断结构化；先阻断后告警；source 与 downstream 零自动写入；只读取证可继续；任何修复逐动作取得 principal 明示；修复后新 revision + 全量 replan；硬阻断不可被临时 approval 绕过。
- `Later`：若证据合同成熟且实际出现大量重复污染，再由 principal 重开本轴评估自动隔离/恢复；v1 不预建自动修复。
- `Out`：静默清理、自动 quarantine/restore/adopt、继续使用已污染 source 生成 plan、Agent 自行选择恢复动作、把 derived/live 状态提升为 authority，或在 source 未恢复可信前报告 compliant。
- 接受的代价：即使恢复动作看似显然，Almagest 也不会自动执行；污染会持续阻断依赖该 source 的配置闭环，直到 principal 现场决定并由 operator Agent 完成修复或纠正检测证据。
- 后果：DEC-07 定义污染 evidence 与 inventory classification；DEC-09 将污染作为无可 apply plan 的 block；DEC-10 保证阻断路径零写入；DEC-12 区分 source contamination 与普通 live drift；DEC-16 提供按 `detection_id` 获取的 provenance、决策和恢复审计。
- 验收断言：识别到 source contamination 后，source/live digest 均不因 Almagest 自动动作变化，且相关 target 无可执行 plan；未经 principal 明确指定动作不能隔离、删除、恢复或接纳内容；修复后必须产生新 source revision 并重新 plan；03B1/02C 的任何一次性批准均不能继续使用污染 source。

#### 03C 已拍板：外部采集面完全 Out，只消费吸收后的 owned revision

| 候选 | 外部版本处理边界 | 结果 |
|---|---|---|
| A：完全外置采集与吸收 | 外部工具负责周期检查、拉取、校验、评审与吸收；Almagest 只消费吸收后的 owned revision | **已选择** |
| B：Almagest 只检查并报告 | Almagest 连接外部 registry/upstream 并报告候选，吸收仍由外部工具完成 | 拒绝：仍引入 registry adapter、网络、凭据、调度状态和上游版本语义 |
| C：Almagest 拉取到非权威隔离区 | Almagest 检查并下载候选，但候选须经外部评审后才吸收 | 拒绝：虽然候选无 authority，仍把 package acquisition 与隔离区生命周期带入控制面 |
| D：Almagest 端到端更新 | Almagest 检查、选择、拉取、批准并写入 source | 拒绝：混合配置一致性与外部供应链更新，明显超过当前能力边界 |

- 决定（v0.1，2026-07-17，approver: principal）：03C 选择 **A——外部采集与吸收完全外置**。Almagest 不接受外部 registry/upstream 作为 source，也不解析浮动 tag、semver range 或远端 latest；它的输入从“已吸收并形成 owned source revision”开始。
- 外部工具边界：周期调度、网络访问、registry credential、候选发现、版本比较、拉取、依赖解析、签名/attestation 校验、候选 diff/review、晋级与写入 owned source 均不属于 Almagest。是否建设何种周期工具也不由本决策预设。
- 水位读取：外部周期工具最多消费 owned source 的 revision/time 与可选 upstream provenance，判断从哪个上游水位继续检查。Almagest 不负责调度该工具，也不把检查结果、候选版本或“可更新”状态纳入 desired、plan、drift 或 receipt。
- 接入合同：外部流程把内容写入 GitHub personal/shared 或 Mac-local work 并形成新 authored revision 后，Almagest 才按普通 owned source 执行 inventory → resolve → plan → apply → verify。候选区、下载 cache 或 quarantine 不在 source root 内时完全忽略；若进入 source root，则按 03B2 source contamination 阻断，不能自动吸收。
- `Must`：只解析 owned source；输入固定到 owned revision；外部 provenance 仅作惰性元数据；外部版本变化对 Almagest 零状态变化；吸收后的内容重新经过正常 authority、residency、overlay、capability 与 03D 统一逐变更审批。
- `Later`：Almagest 内无外部版本管理扩展项；未来若要让它承担任一上游检查或吸收责任，必须由 principal 明确重开本边界，而不是从 provenance 字段自然扩权。
- `Out`：上游调度与通知、registry client/adapter、网络与凭据、floating ref resolution、外部候选状态机、下载/cache/quarantine、签名与依赖验证、候选审批、PR/merge 和自动吸收。
- 接受的代价：Almagest 无法单独回答“上游是否有新版本”或保证外部内容新鲜度；外部检查工具失效时，配置仍保持可复现和一致，但可能停留在旧的 owned revision。
- 后果：03A v0.2 删除 external authority；DEC-07/16 最多暴露 owned source revision/time 与惰性 provenance，不记录外部候选状态；DEC-09 只固定 owned revision；DEC-12 不把上游可用版本视为配置漂移；DEC-13 只分发 owned 内容；DEC-14 的配置生命周期从吸收完成后的 revision 开始；DEC-15 的 adapter 只适配 consumer 配置，不适配上游 registry。吸收后的 skill、hook、MCP、plugin 等内容与其它配置一样，必须通过 03D 的逐变更批准；“已 owned”不等于“已批准”或“已安全”。
- 验收断言：外部 tag、release 或 registry metadata 单独变化时，Almagest 的 inventory/desired/plan 均不变化；外部工具吸收内容并产生新 owned revision 后，Almagest 只显示该 revision 引起的普通配置差异；Almagest 配置、状态和凭据中不存在上游调度或拉取责任；source root 外的候选被忽略，进入 source root 的候选按 03B2 阻断；吸收后的任何配置差异仍须取得 03D 的当前 plan 批准。

#### 03D 已拍板：任何配置差异统一报警并逐 plan 批准

| 候选 | 配置差异审批模型 | 结果 |
|---|---|---|
| A：统一逐变更审批 | 所有会产生写动作的非 `no-op` plan 都先阻断并报警；principal 实时审阅当前精确 diff 后批准、拒绝或要求改 plan | **已选择** |
| B：按风险等级审批 | 只让高风险差异等待 principal；低风险差异自动 apply | 拒绝：需要维护风险分类器，并可能把误分类变成静默写入 |
| C：按资产类型审批 | hook、MCP、plugin 等固定类型等待批准，skill/instruction/settings 等默认自动 apply | 拒绝：同一类型内部风险差异很大，也违背“有差异就报警” |
| D：完整内容安全门 | 在审批前追加签名、静态分析、沙箱或行为探测，并由结果决定是否可 apply | 拒绝：扩成内容与供应链安全平台；仍不能替代 principal 对具体配置差异的判断 |

- 决定（v0.1，2026-07-17，approver: principal）：03D 选择 **A——统一逐变更审批**。不对 skill、instruction、settings、hook、MCP、plugin 或其它受管配置建立高/中/低风险等级；任何会新增、删除、修改、mask、shadow、移动或接纳配置的非 `no-op` plan 都先返回结构化差异并阻断写入，由 operator Agent 报警给 principal 现场处理。
- 审批合同：principal 可以批准整个精确 plan、拒绝，或要求 Agent 调整 source/目标/动作后重新 plan。approval artifact 必须绑定 target、plan hash、source/resolved revision、相关 inventory snapshot、完整 action/diff set、principal approver 与 operator Agent；任一输入、差异集合、动作或 plan hash 变化后旧批准失效。
- 适用范围：正常 source 更新、首次 bootstrap/projection、absorbed revision、render 变化、live drift 修复，以及 adopt/remove/mask 等写动作都适用。只读 inventory、plan、diff、explain、verify 和真正的 `no-op` 不需要批准，也不能借只读操作产生隐式写入。
- 告警内容：Almagest 提供稳定差异 ID、target、asset/field、before/after、provenance、动作、影响与阻断原因；operator Agent 负责把它压缩为 principal 可实时判断的摘要，并按 ID 展开完整证据。具体 plan/approval schema 与紧凑摘要由 DEC-09/10 定义。
- 与既有门禁的关系：本项是所有写计划的通用必要条件，不替代专项阻断。DEC-02C 的 capability exception、03B1 的冲突裁决必须满足各自合同后才能形成或批准可执行 plan；03B2 contamination、authority violation、work residency/egress deny、secret 泄漏等硬策略拒绝不能因 principal 批准普通 diff 而放行。多种 approval 如何在一次 principal 对话中组合，由 DEC-09/10 定义。
- `Must`：所有非 `no-op` 配置写计划默认阻断；逐 plan 报警；完整 diff 可展开；principal 实时批准；approval 绑定精确输入与动作；输入变化即失效；receipt 分开记录 approver 与 operator；无批准零写入。
- `Later`：若实际审批量造成不可接受的负担，只能由 principal 重开本轴评估批量批准或自动化；当前不预建风险等级、资产白名单、永久 `always allow` 或历史批准复用。
- `Out`：低风险自动 apply、按资产类型静默放行、Agent 自行批准、永久批准、从历史选择推断未来授权、自动 drift 修复/adopt，以及把签名、静态分析、沙箱或行为探测建设成 Almagest 的内容安全平台。
- 接受的代价：首次安装、普通文本微调和低风险配置也会报警，principal 的审批次数增加；Almagest 只能证明“展示了什么差异、谁批准了哪个精确 plan、执行是否等价”，不能证明被批准内容本身无恶意或业务上正确。
- 后果：DEC-09 必须把所有非 `no-op` plan 标为 `approval_required` 或等价状态并输出紧凑摘要；DEC-10 必须拒绝无有效 approval 的写动作；DEC-12 只能检测并报警 drift，不能自动修复；DEC-16 必须记录完整 diff、principal approver、operator Agent、approval、apply 与结果链。
- 验收断言：任一 target 的任一配置写动作在无有效 approval 时均为零写入；principal 能通过 Agent 先看到完整差异及影响，再批准当前精确 plan；任何输入变化都会令旧 approval 失效；普通批准不能越过专项 exception 合同或硬策略 block；只读与 `no-op` 不制造审批噪音。

### DEC-04 Source 驻留与投影策略

- 状态：04A—04D 已拍板
- 依赖：DEC-02、DEC-03。
- 决策轴：
  - 04A：驻留权限是跟随 source，还是允许每项 asset 单独声明 allowed hosts 或例外。
  - 04B：每个已知 target 可以从哪些 source class 取得候选输入，以及 source eligibility 在 overlay/render 前如何固定。
  - 04C：如何在 source/cache/resolved/rendered/plan/receipt/live 全链路执行默认拒绝、零例外的 work 防泄漏，并报告和恢复违规状态。
  - 04D：work 内容或派生元数据是否允许离开 Mac；无法证明 residency 时的停止条件与迁移要求。
- 初步验收：work-only payload 或派生元数据进入 Windows、GitHub 或非授权中间产物必须 `block`；不存在逐 asset 放宽或临时例外；不存在虚构的 Mac personal/work 双 target 或中央汇总面。

#### 04A 已拍板：驻留权限只跟 source，work source 全量 Mac-only

本轴已被 DEC-02 的 source topology 与 principal 的约束确认收敛为单一可行口径，因此不再制造 A/B/C/D 伪选项。需要固化的规则是：资产放在哪个 authority source，就继承哪个 source 的驻留边界；每项资产不再单独声明或放宽 allowed hosts。

| Source | 所有内容的驻留边界 | 单项 asset 能否覆盖 |
|---|---|---|
| GitHub personal/shared base | 可以被 Mac 与 Windows 的已授权 consumer 消费 | 不能；需要更严格驻留时必须进入另一 source |
| Mac-local work | 只能留在 Mac 工作机，并且只能投影给该机的 Codex/Qoder target；不得进入 GitHub 或 Windows | 不能；不存在“这一个 work asset 可以外发”的例外 |

- 决定（v0.1，2026-07-17，approver: principal）：04A 采用 **source 级硬驻留**。source 是驻留策略的最小声明与执行单元；其下所有 asset、field contribution 和 content-bearing 派生物自动继承该边界。任何包含 work source contribution 的 resolved/rendered/plan/receipt/live payload 都按更严格的 Mac-only 边界处理。
- source 边界：Mac-local work 使用与 GitHub checkout 分离的独立 source root；不能靠 `.gitignore`、文件名、目录名或 Agent 猜测资产性质建立安全边界。`source_id/source_class` 的受管 inventory 是判定入口，具体 manifest/schema 留给 DEC-07。
- 无例外合同：asset 不拥有 `allowed_hosts` 放宽字段，不支持 per-file waiver、临时 egress approval 或把 work 内容复制到 GitHub/Windows 后再补标签。若未来确实需要共享某项内容，principal 必须明确要求把它改写/迁移为 GitHub personal/shared 的 authored asset，形成新 source revision，并按 DEC-03D 重新 plan 和批准；这不是驻留例外。
- 派生继承：纯 GitHub 输入可以为 Mac 或 Windows 生成派生物；只要输入集合含任一 work contribution，整个 content-bearing 派生结果就是 Mac-only。04D 进一步确认 work-derived metadata 也不离开 Mac，不能以“不可还原内容”为由建立跨机例外。
- `Must`：source 级 residency classification；asset 与字段贡献自动继承；work source 全量 Mac-only；混合派生取最严格边界；无逐 asset 放宽和临时例外；违规输入 fail closed。
- `Later`：若未来出现第三种真实驻留边界，新增独立 source class/root 并重开本轴；当前不预建通用标签表达式或例外系统。
- `Out`：per-asset allowed-host policy、资产白名单、临时外发 approval、路径/文件名启发式、用 `.gitignore` 充当安全边界，以及把 work payload 先复制到非授权位置再检测。
- 接受的代价：即使某个 work asset 后来被判断为可共享，也不能原地加例外；必须经过显式 source 迁移、内容审阅、新 revision 和逐 plan 批准。以此换取规则简单、可静态验证且不会因单项标签遗漏而泄漏。
- 后果：04B 只需生成 Mac 的 GitHub + work union 与 Windows 的 GitHub-only 投影；04C 不再设计例外授权，只设计全链路阻断、告警与恢复；04D 要求全部 work evidence 留在 Mac；DEC-07/09/16 必须在本机保留 source residency provenance 并解释拒绝原因，DEC-13 不得上传或汇总它。
- 验收断言：任一 GitHub source asset 可进入已授权 Mac/Windows target；任一 work source asset 或含 work contribution 的派生物在 Windows、GitHub 或其它非授权位置出现时必须阻断；不存在能放宽该结论的 asset 字段或 approval；从 work 迁移到 GitHub 必须成为显式 authored change、新 revision 和 DEC-03D 新 plan，而不是更新标签。

#### 04B 已拍板：target 固定 eligible source 集合，Mac 双源、Windows 单源

本轴同样由已知 target 拓扑与 04A 的无例外驻留约束收敛为约束确认，不再制造 A/B/C/D 伪选项。它只回答“这个 target 最多能从哪些 source 取得候选输入”，不回答同名资产如何覆盖、字段如何合并或 consumer 格式如何渲染。

| Target | Eligible source 集合 |
|---|---|
| Mac 工作机 / Codex | GitHub personal/shared base + Mac-local work |
| Mac 工作机 / QoderCLI | GitHub personal/shared base + Mac-local work |
| Windows / Codex | GitHub personal/shared base |
| Windows / Claude | GitHub personal/shared base |

- 决定（v0.1，2026-07-17，approver: principal）：Almagest 先根据稳定 `target_id` 和受管 `source_class` 得到固定 source eligibility，再把符合条件的候选交给 DEC-05 做 overlay/resolve，最后由 DEC-08 做 per-consumer render。相同 target 与 source inventory 必须得到相同 eligible source 集合。
- eligibility 语义：上表是候选输入的上界，不代表 source 中每个 asset 都适用于每个 consumer。asset 的 consumer/target selector 可以进一步缩小候选集，但不能把 Mac-local work 扩给 Windows，也不能创建表外 source 组合。
- 静态拓扑：source eligibility 不因当前工作目录、启动 profile、某个 root 恰好存在、operator Agent 身份或一次运行中的可用性而变化。OS、consumer 版本、root 和 profile 可以参与后续 selector、兼容性与绑定验证，但不能动态改写这张 target→source 映射。
- fail-closed 边界：已登记给 Mac target 的 work source 不可访问、身份不明或无法证明来源时，结果必须是 `unknown/block`；不得静默退化为 GitHub-only 并宣称 Mac 配置合规。具体 inventory 证据、诊断码与 plan 表达由 DEC-07/09 定义。
- `Must`：四个已知 target 的显式 source eligibility；Mac Codex/Qoder 双源；Windows Codex/Claude 单源；resolve 前完成 eligibility filter；结果确定且可解释；work source 对 Windows 永不成为候选。
- `Later`：新增 host、consumer 或独立 source class 时，显式登记新的 target→source 映射并重做驻留审阅；当前不建设自动推断拓扑的规则引擎。
- `Out`：按 cwd/profile/operator/临时可用性动态选 source、Windows 发现或读取 work source、Mac 在 work source 故障时静默降级为合规、在本轴决定 merge precedence，以及在本轴决定 consumer 的目录与 frontmatter 转换。
- 接受的代价：每增加一个 target 或 source class 都必须显式维护映射；Mac-local work 暂时不可访问时，即使 GitHub base 完整也不能得到“配置合规”的成功结果。以此换取跨 host 的 source eligibility 不会依赖环境猜测或 fallback。
- 后果：DEC-05 只能在本轴给出的 eligible source 内定义 overlay、merge、remove 与 conflict；DEC-07 必须盘点 target/source 身份及可访问性；DEC-08 只能把已 resolve 的目标状态适配给对应 consumer；DEC-09 必须把 eligibility filter、缺失输入和拒绝原因纳入 plan 证据。若 work 内容要改为跨机共享，仍走 04A 的 GitHub authored migration 与新 plan，不修改映射来绕过驻留。
- 验收断言：Mac Codex/Qoder 的候选 source 集合恰为 GitHub + work，Windows Codex/Claude 恰为 GitHub-only；selector 只能缩小集合，不能扩大；任何运行态条件都不能静默改写映射；已登记的 Mac work source 缺失或不可证明时停止 resolve/apply，而不是以 GitHub-only 冒充成功；本轴不规定 asset merge winner 或 rendered 格式。

#### 04C 已拍板：全链路阻断并告警，principal 决定恢复

本轴已经由 04A 的无例外驻留和 principal 的处置要求收敛为约束确认：Almagest 必须在自己控制的物化边界阻止 work payload 越界，并在发现既有越界时阻断受影响的变更链；但它不因发现问题而自动取得删除、迁移、修复或接纳任何内容的权限。

```text
预防：work-derived payload ──写入前 residency check──X──> GitHub / Windows / 非授权位置
发现：既有越界 ──> block 受影响链路 + 结构化诊断 ──> principal 决策
恢复：principal 明示动作 ──> Agent 执行精确 recovery plan ──> 重新 inventory/verify ──> 证据通过后解除
```

- 决定（v0.1，2026-07-17，approver: principal）：任何 work asset、field contribution 或含 work contribution 的 content-bearing 派生物，在进入 `source/cache/resolved/rendered/plan/receipt/live` 任一非授权位置前都必须被拒绝，产生零越界写入；若越界状态已经存在，则立即阻断依赖该状态的 resolve、普通 plan 与 apply，并通过 operator Agent 告警 principal。
- 两类 enforcement：Almagest 控制的写入采用 pre-write deny，不允许“先复制、后扫描”；consumer 或其它组件已经生成、且 Almagest 没有写权限的 cache/live 等位置采用只读 detection。被发现不等于 Almagest 取得管理权，不能据此自动修改该位置。
- 与 03B2 的边界：03B2 按数据流方向识别“downstream 内容反向进入 authority source”，无论内容属于 personal 还是 work；04C 按驻留策略识别“work 内容进入非授权位置”，无论由哪条数据流造成。同一事实同时命中时可以共享 evidence，但必须同时满足两项恢复条件，不能用修复其中一项来解除另一项阻断。
- 告警合同：Almagest 在当前 host 返回机器可消费的结构化诊断，至少能引用 detection、违规 stage/location、work provenance 证据、受影响 target/action 和当前阻断状态；同机 operator Agent 在本次会话中将其翻译成人话交给 principal。稳定 schema 与诊断码由 DEC-07/09/16 细化；04D 禁止把该诊断转成跨机摘要，本轴不建设独立通知平台。
- 阻断范围：只读 inventory、diff、explain 和取证可以继续；依赖该违规状态的 resolve、普通 plan 与 apply 保持阻断。普通变更 approval、DEC-02C break-glass、DEC-03B1 单次冲突裁决以及“已知悉/忽略”均不能绕过 work residency block。
- 恢复 authority：Almagest 可以给出可引用的恢复候选，但不能自动选择或执行。principal 必须现场明确修复目标与动作，operator Agent 才能形成绑定 detection、固定输入、精确 action set 和 plan hash 的 recovery plan；任何写动作仍须满足 DEC-03D 的逐 plan 批准。
- 解除条件：执行获批 recovery plan 后必须重新 inventory/verify；只有新证据证明违规 payload 已从非授权位置消失、且受影响输入已重新固定，才解除阻断并重新生成普通 plan。仅关闭告警、记录 acknowledgment、等待一段时间或修复部分副本都不算恢复完成。
- `Must`：所有 content-bearing stage 的 residency 继承；受控物化点 pre-write deny；既有越界 read-only detection；受影响链路硬阻断；结构化告警；principal 现场决策；独立 recovery plan；修复后重新取证再解除。
- `Later`：本机检测覆盖面和大规模历史扫描由 DEC-12 或本机 operator automation 决定；本轴只规定在当前操作中一旦检测到违规时必须怎样处置。跨机汇总、中央报告和 Almagest 主动通知不进入 Later。
- `Out`：先写后扫、自动删除/隔离/迁移/修复/adopt、静默清理 consumer cache/live、永久忽略、acknowledgment 解锁、用普通 approval 或 break-glass 放行，以及让 Almagest 承担通用 data loss prevention（DLP，数据防泄漏）或内容分类平台。
- 接受的代价：已知越界会让受影响配置链持续不可变更，直到 principal 作出决定、Agent 完成修复并重新验证；即使恢复动作明显，也不能由 Almagest 自动代办。以此换取发现问题不会扩大权限或造成二次破坏。
- 后果：04D 要求告警、plan、receipt 与 evidence 全部留在产生它们的 Mac；DEC-07 必须提供逐 stage 的本机 provenance evidence；DEC-09 必须表达 block-only 与 recovery plan；DEC-10 必须保证 deny 发生在写入前且 apply 与获批 recovery plan 等价；DEC-12 决定本机检测入口；DEC-13 不得增加跨机汇总；DEC-16 在本机记录 detection→principal decision→recovery apply→verify 的完整链。
- 验收断言：Almagest 控制的任一 work 越界写入在落盘前被拒绝且目标零变化；任一既有越界都会阻断受影响的 resolve、普通 plan 与 apply，同时允许只读取证；没有 principal 明示决定与精确批准时零修复写入；普通 approval、exception 或 acknowledgment 不能解锁；只有获批恢复完成且重新验证通过后才能解除阻断。

#### 04D 已拍板：A，work 内容和元数据零离机

principal 明确纠正了“跨机报告”前提：Almagest 是被当前机器上的 operator Agent 在操作现场调用的本地工具，不是中央控制面。04D 因此选择 A；Mac-local work 的内容、存在性和所有派生元数据都只留在 Mac，不为 Windows 或中央端生成任何状态信封。

| 选项 | 跨机可见范围 | 结论 |
|---|---|---|
| A：零离机 | work 内容和 work-derived metadata 均不离开 Mac | **已选择** |
| B：最小状态信封 | 允许跨机发送状态、诊断码、时间和本机 evidence reference | 拒绝：仍然制造了不存在的跨机报告面，也泄露 work 的存在与活动状态 |
| C：脱敏诊断 | 允许 asset 名、相对路径、digest、数量或差异摘要跨机 | 拒绝：脱敏不等于无信息，会暴露工作结构并增加分类错误面 |
| D：加密完整证据 | 加密后把完整 evidence 发送到其它 host 或中央端 | 拒绝：加密 payload 仍已离开 Mac，直接违反 04A |

```text
Mac：principal ──> Mac Agent ──> Mac Almagest ──> 本机 plan / receipt / evidence
Windows：principal ──> Windows Agent ──> Windows Almagest ──> 本机 plan / receipt / evidence
                                      两条本地操作链之间没有 report / receipt / evidence 通道
```

- 决定（v0.1，2026-07-17，approver: principal）：work content 与 work-derived metadata 一律 Mac-only。禁止离机的范围包括 work 的存在/缺失、状态、asset/source/detection/evidence ID、名称、路径、digest、数量、时间、diff、provenance、plan、receipt、错误详情和任何可关联 reference；不因字段已脱敏、不可还原或加密而放宽。
- 本地交互：Mac operator Agent 可以在当前操作中读取本机 Almagest 的完整结构化结果并向 principal 解释；Almagest 不持久化或推送跨机报告。Windows operator Agent 只检查本机 GitHub base target，不查询 Mac，也不知道 Mac 是否有 work source、是否合规或是否被阻断。
- 未知停止条件：若一个待导出、写入 GitHub、复制到 Windows 或发送给中央端的 artifact 无法证明完全不含 work content/metadata，egress 必须 `block`。本机只读 inventory/explain 可以继续；unknown 不能靠字段删除、hash、加密或 operator acknowledgment 变成可外发。
- 共享出口：确需跨机消费的内容必须由 principal 明确要求重新编写/迁移为 GitHub personal/shared authored asset，经内容审阅形成新 source revision，再走 DEC-03D 新 plan；不能把 Mac 证据包、receipt 或 work metadata 当迁移载体。
- `Must`：work content/metadata 全量 Mac-only；每次操作只调用当前 host 的 Almagest；完整本机 evidence；未知 egress fail closed；Windows 零 work knowledge；共享必须经过 GitHub authored migration。
- `Later`：若未来真的出现中央报告或跨机诊断需求，必须显式重开 04A/04D 与 DEC-13/16；当前不预留 status envelope、上传接口或远端 evidence reference。
- `Out`：中央控制端、跨机 dashboard/report、receipt 上传、跨机对比、远程查询 Mac work 状态、推送通知、最小/脱敏/加密 work metadata egress，以及让 Almagest 远程操作另一台 host。
- 接受的代价：principal 无法在 Windows 或一个中央视图看到 Mac work 是否合规；处理哪台机器就必须在那台机器的 Agent 会话中当场检查和决策。以此换取 Almagest 无需维护跨机通道、脱敏规则或中央数据面，且 work 的存在本身也不会泄漏。
- 后果：DEC-07/09/10/12/16 的 work inventory、plan、apply、drift、receipt 与 audit 均只在 Mac 本机产生和消费；DEC-13 只能定义两台机器如何分别从共享 GitHub source 达到各自 target，不得设计中央协调、receipt 上传或跨机汇总；本地 evidence 的保留与清理由 DEC-16 决定。
- 验收断言：Windows、GitHub 和任何中央端均观察不到 work 的内容、存在性、状态或派生元数据；Mac 与 Windows 的操作分别由同机 Agent 调用同机 Almagest 完成；无法证明 work-free 的 egress 零写入；若 principal 需要共享内容，只能生成新的 GitHub authored asset 和新 plan，不能导出原 work evidence。

### DEC-05 Overlay 与解析

- 状态：05A—05D 已拍板
- 依赖：DEC-01—DEC-04。
- 决策轴：
  - 05A：authored overlay 有哪些 layer；host、consumer 与本机差异是否形成额外 layer。
  - 05B：每种纳入 asset 的 merge algebra：skill 的集合/目录、MCP/settings 的键或字段、instructions 的 import/拼接、hooks 的有序列表等。
  - 05C：add、override、remove/mask、duplicate 和 conflict 的语义；哪些冲突按优先级，哪些必须阻断。
  - 05D：如何表达 `GitHub personal/shared base + Mac-local work`，同时让 selector、consumer render 与本机 binding 不冒充 authored layer。
- 初步验收：相同输入生成相同 resolved state；每个字段/资产可解释 provenance；所有纳入类型均有 merge/remove/conflict 规则。

#### 05A 已拍板：A，只有 GitHub base 与 Mac-local work 两个 authored layer

本轴只决定“谁有资格向 resolved desired state 提交 authored 声明”和 layer 的适用范围，不决定两个 layer 出现同一 logical asset 或字段时谁赢。source eligibility 已由 04B 固定；05B 已定义按 schema shape 的结构组合，05C 已规定非等价碰撞必须有显式 override/mask 意图，否则阻断。

| 选项 | Layer 模型 | 结论 |
|---|---|---|
| A：两层 authored overlay | GitHub personal/shared base 为共享基础层；Mac-local work 为仅适用于 Mac target 的后层 | **已选择** |
| B：再加 host overlay | 每台机器拥有独立 authored host layer | 拒绝：当前真实差异只有 work；OS、路径和 host 差异是 selector、render 或 binding，不应制造第三份意图 |
| C：再加 consumer overlay | Codex、QoderCLI、Claude 各自拥有 authored layer | 拒绝：consumer 差异应由同一 resolved state 的 adapter/render 表达，不能让派生格式取得 source authority |
| D：允许 arbitrary local override | live target 或任意本机目录可作为最高优先级配置层 | 拒绝：会形成不可审阅的第二真相，使手改 live state 从 drift 变成合法 desired state |

```text
GitHub personal/shared base ──> Mac resolved candidate set <── Mac-local work
             │
             └───────────────> Windows resolved candidate set

host / OS / consumer / profile / root ──> selector、render 或 binding 输入
live / rendered artifact                ──> 观测或派生物，不反向成为 layer
```

- 决定（v0.1，2026-07-17，approver: principal）：05A 选择 **A——两层 authored overlay**。v1 的 logical layer 集合严格为 `GitHub personal/shared base` 与 `Mac-local work`；Mac target 在通过 04B eligibility 后按 base→work 的顺序把候选交给 resolve，Windows target 只取得 base。
- 顺序边界：base→work 只表示 layer 适用范围和确定的候选处理顺序，不表示 work 对同名 asset 或字段无条件取胜。05B 只定义哪些结构可以组合以及组合单元；同一原子值/叶子的非等价碰撞按 05C 要求显式 override/mask，否则形成 conflict。
- 单一 base：GitHub personal/shared 是一个逻辑 authored layer；其物理仓、checkout 或未来存储拆分不得自动形成新的 precedence 层。只有拥有明确 source authority、revision 和驻留合同的 authored input 才能成为 layer。
- 非 layer 输入：host、OS、consumer、consumer version、profile、workspace、root 与 binary path 只能作为 target observation、asset selector、adapter/render 输入或 active binding 证据；它们可以缩小适用范围或改变目标格式，但不能新增、覆盖或删除 authored intent。
- 本机值边界：secret reference/value、本机绝对路径、账号和 credential provider 属于 DEC-06 的 local binding；它们可以为已声明配置补值，但不形成 local overlay，也不能借补值改变 asset ownership、绕过 source trust 或 work residency。
- 派生与 live 边界：rendered artifact、consumer root 中的 live 文件、cache 和 session 均不拥有 authored authority。非 Almagest 管理的本机文件可以被 inventory 为 `external-owned`、`unknown-owner` 或 drift，但不能因存在、mtime 更新或 consumer 正在读取就成为最高优先级 layer；若 principal 要接纳，必须显式修改合法 authored source 并生成新 plan。
- 演进约束：未来若出现第三种真实 authored authority 或独立驻留边界，必须显式重开 03A、04A/04B 与 05A，登记新的 source class/root 和 target eligibility；不得通过新增 `host/`、`consumer/` 或 `local/` 目录静默扩展 layer 集合。
- `Must`：恰好两个 authored layer；Mac 为 base + work，Windows 为 base-only；source eligibility 先于 overlay；layer 与 selector/render/binding/live 严格分离；未受管本机状态无 authority；每项贡献保留 layer/source provenance。
- `Later`：新增真实 source class 或驻留域时重开上游决策；当前不预建任意层级、动态 precedence 表达式或 host/consumer override 机制。
- `Out`：authored host layer、authored consumer layer、任意 local override、以 live/rendered/cache 反推 desired state、按目录存在性动态创建 layer，以及让本机绑定覆盖 source ownership 或驻留策略。
- 接受的代价：某台 host 或 consumer 的特殊 authored 行为不能就地放进专属 override 目录；必须优先表达为 base/work 中带 selector 的声明、consumer render 规则或 local binding。若三者都无法准确表达，需重开 05A，而不是临时加层。以此换取配置权威只有两个入口，漂移判断和 provenance 更简单。
- 后果：05B 只需为两个 layer 定义各类 asset 的组合代数；05C 定义同一 logical ID 的 add/override/remove/conflict；05D 只需确定两层声明语法及 selector/binding 引用方式。DEC-06 不得创建 local-value layer；DEC-07 必须把 authored、binding、rendered 与 `external-owned`/`unknown-owner` live 分开盘点；DEC-08 的 per-consumer 结果只能是 derived artifact；DEC-09/12 必须把非 Almagest 管理的本机改动报告为差异而非合法 override。
- 验收断言：任一 Mac target 的 authored 候选只来自 GitHub base 与 Mac-local work，任一 Windows target 只来自 GitHub base；host/OS/consumer/profile/root 只能筛选或渲染，secret/path/account 只能绑定已声明引用，rendered/live/`external-owned`/`unknown-owner` 状态均不能取得 layer authority；相同固定输入产生相同 layer 集合；同名非等价贡献不得因 work 位于后层而自动取胜，必须满足 05C 的显式意图合同。

#### 05B 已拍板：B，Schema-aware 类型化合并

本轴决定 resolved model 如何识别“可以结构化组合的不同贡献”，不决定两个贡献写入同一原子值时谁覆盖谁。每个 asset adapter 必须通过版本化 schema 显式声明字段/子资源的 merge shape；Almagest 不从 JSON/YAML/TOML 的表面类型、目录布局或 consumer 当前行为猜合并规则。

| 选项 | Merge 模型 | 结论 |
|---|---|---|
| A：整项原子替换 | 任一修改都以整个 asset 为单位，work 版本整体替换 base 版本 | 拒绝：规则简单但粒度过粗；修改一个 MCP 字段、hook 条目或 skill manifest 值也要复制整项，并把结构合并与 winner 过早绑死 |
| B：Schema-aware 类型化合并 | schema 对每个节点声明 atomic、granular map、set、keyed list 或 ordered list；只按声明的 shape 合并 | **已选择** |
| C：统一递归 deep merge | 所有 object 递归合并，所有 array 使用一个 append 或 replace 规则 | 拒绝：不同配置域的 map/list 语义不同，统一规则会把偶然序列化结构误当业务语义 |
| D：显式 patch 程序 | work 以路径级 add/remove/replace/test 等操作修改 base | 拒绝：精确但强耦合 base 路径与顺序；source 变成脆弱的变更脚本，并提前吞并 05C 的删除/覆盖语义 |

| Schema shape | 组合单元与确定性规则 | 典型适用对象 | 进入 05C 的边界 |
|---|---|---|---|
| `atomic` | 整个 value、正文、文件或 bundle subresource 是一个不可拆单元；禁止行级或递归 merge | `SKILL.md`/instructions/prompt 正文、script、opaque asset、未声明 granular 的对象或列表 | 两个贡献命中同一 atomic ID 且内容不同 |
| `granular-map` | 以 schema 声明的稳定字段/子资源 key 组合；互不相交的 key 可以并存，字段自身继续按其 shape 递归处理 | MCP/server、settings、agent/plugin manifest、model/profile、控制面 metadata 中允许独立声明的字段 | 两个贡献最终命中同一 atomic leaf，或字段 shape 不兼容 |
| `set` | 以规范化 scalar value 或 schema 声明的稳定 element key 做集合并集；不承载顺序语义 | schema 已证明集合语义的 tag/capability 或独立 policy item；安全 policy 未证明前默认 atomic | 同 key 元素语义不等价，或字段其实需要顺序 |
| `keyed-list` | 以稳定 item ID 把列表视为 map；不同 ID 并存，同 ID item 按 schema 继续解析；禁止数组下标充当 identity | MCP tools、plugin components、agent definitions 等序列化为 list 的命名对象 | 缺失/重复 item ID，或同 item 的叶子冲突 |
| `ordered-list` | 每项必须有稳定 item ID，并使用 schema 声明的显式 order key/约束生成确定顺序；禁止按 source 扫描顺序或隐式 append | hooks、instruction imports/片段顺序、fallback/precedence 列表 | 重复 ID、相互矛盾/成环/无法唯一确定的 order 约束 |

- 决定（v0.1，2026-07-17，approver: principal）：05B 选择 **B——Schema-aware 类型化合并**。所有纳入 v1 的配置域都必须由对应 canonical schema/adapter 把 asset、字段和可独立审计的 subresource 映射到上表 shape；没有声明 shape 的节点默认 `atomic`，但“缺少该 asset kind 的可信 schema”必须 `unknown/block`，不能把整个未知 consumer 文档静默当作可安全合并。
- 结构与冲突分界：05B 允许 disjoint map keys、不同 stable item ID 和合法顺序约束确定地组合；一旦多个贡献命中同一 atomic value/leaf、同一集合 key 的非等价元素、同一 item 的不兼容内容，出现重复/无效排序，或出现删除/mask，resolver 只产生带精确路径、候选和 provenance 的 typed collision，不在本轴选择 winner。05C 将跨层等价贡献去重，并只在显式 override/mask 合法时消解非等价 collision；其余 collision 阻断。只有缺失可信 asset schema、schema version 不受支持或无法验证 schema identity 时，本轴直接返回 `unknown/block`。
- Asset 映射：skill/plugin 等目录型资产先按 stable logical asset/subresource ID 形成 keyed collection；结构化 manifest 可 granular，正文、script、reference/asset 文件内容默认 atomic。instructions/prompt body 默认 atomic，import/拼接顺序使用 ordered-list。MCP/settings/profile/agent 等结构化对象只对 schema 明示 granular 的字段递归；permission/security policy 若没有经过验证的领域 algebra，保持 atomic，不用普通 set/map merge 猜安全语义。
- Schema 与版本：merge schema 是 plan 的受管输入，必须具有 adapter/schema version 与 digest。schema shape、stable key 或 ordering 规则变化会改变 resolved result，因此必须让旧 plan/approval 失效，并通过 DEC-15 compatibility fixture 验证；不能在 adapter 升级时静默改变 merge 结果。
- Provenance：resolved tree 的每个字段、集合元素、ordered item 和 atomic subresource 都必须保留 source/layer、logical ID、schema path、merge shape、输入 revision/digest 和解析结果；operator Agent 可以只取紧凑摘要，但完整 explain 必须能回答某值为何合并、为何保持 atomic 或为何形成 collision。
- 工业校准：Kubernetes Server-Side Apply 同样由 schema 区分 list 的 `atomic/set/map` 与 map/struct 的 `atomic/granular`，并要求 list map key；RFC 7396 证明通用 object merge 对 array 只能整体替换；RFC 6902 的路径级操作虽然精确，但会把 authoring 变成有序 patch。参考：[Kubernetes Server-Side Apply](https://kubernetes.io/docs/reference/using-api/server-side-apply/)、[RFC 7396](https://datatracker.ietf.org/doc/html/rfc7396)、[RFC 6902](https://datatracker.ietf.org/doc/html/rfc6902)。
- `Must`：版本化 canonical merge schema；五类基础 shape；稳定 subresource/item ID；ordered-list 显式排序；opaque content 原子化；未知 schema fail closed；字段/元素级 provenance；schema 变化使 plan/approval 失效；每种纳入 asset 都有正负 fixture。
- `Later`：若真实配置域无法由五类 shape 表达，可经独立设计审阅增加命名的 domain algebra；当前不预建通用表达式语言、用户自定义 merge function 或任意 plugin 执行 merge 代码。
- `Out`：通用 recursive deep merge、所有 array 自动 append/replace、按目录或读取顺序拼接、数组下标 identity、文本行 merge、从 consumer 输出反推 schema、把 JSON Patch 作为 source 主模型，以及未知结构 best-effort 合并。
- 接受的代价：每个 consumer/config kind 都要维护 schema、stable key、ordering 与 fixture；schema 演进也会触发 plan 变化和重新批准。以此换取 13 个配置域可以使用符合自身语义的合并方式，而不是依赖容易产生静默错误的通用 deep merge。
- 后果：01B 的 stable subresource/item ID 成为 merge 前提；05C 只处理 typed collision、override、remove/mask、duplicate 与 conflict，不再重新定义结构 shape；05D 只需表达 typed contribution 而不是 patch 程序。DEC-07/09/16 必须保存 schema-aware provenance 与 collision path；DEC-08 adapter 必须把 canonical resolved model 渲染为 consumer 格式而不改变 merge；DEC-15 必须版本化 schema 并提供 atomic/map/set/keyed/ordered 正负 fixture。
- 验收断言：相同固定 layer、schema version 和输入 revision 产生字节等价的 canonical resolved state；disjoint granular fields 与不同稳定 ID 可组合；opaque body 不做文本 merge；ordered list 不依赖文件扫描顺序；缺失/不受支持/无法验证的可信 schema 返回 `unknown/block`；缺/重复 ID、无效排序、同一 leaf 或 shape 不兼容只产生 typed collision 而非 best-effort 结果；typed collision 必须继续满足 05C 的等价去重、显式意图或阻断规则。

#### 05C 已拍板：B，显式意图，否则冲突

本轴只决定 05B 已识别的贡献如何成为 add、等价重复、override、mask、source remove 或 conflict。它不改变 05B 的 schema shape，也不决定 05D 用哪种文件语法表达贡献。base→work 是处理顺序，不是隐式 `last writer wins`。

| 选项 | 碰撞处置 | 结论 |
|---|---|---|
| A：后层自动覆盖 | work 对同一 logical target 自动取胜，删除使用约定 tombstone | 拒绝：拼错 ID、复制旧值或无意重名都会被当成合法覆盖，无法区分 work 增量与事故 |
| B：显式意图，否则冲突 | 不相交贡献自动组合；同 ID 同内容去重；非等价同目标必须声明 override/mask，否则阻断 | **已选择** |
| C：work 只许追加 | work 只能贡献新 ID，任何覆盖、mask 或同名项都禁止；需要改变 base 时只能编辑 GitHub source | 拒绝：无法表达合法的 Mac-only 差异，work overlay 会退化为纯附加目录 |
| D：每次由 principal 临时裁决 | source 不保存 override/mask 意图；每次 plan 遇到碰撞都走 03B1 单次选择 | 拒绝：相同稳定意图会反复报警，source 永远不能确定重放，并把常规 overlay 变成持续 exception |

| 语义 | 确定性规则 | Provenance / 停止条件 |
|---|---|---|
| `add` | 贡献命中新 logical ID、不同 granular key 或不同 stable item ID 时，按 05B shape 自动组合 | 保留贡献的 layer/source/revision/schema path；若最终投影产生写差异，仍走 03D |
| 等价重复 | eligible contribution 命中同一 semantic target，且在同一 schema version 下 canonical value 等价时，只在 resolved state 中保留一个值 | 保留所有贡献的 provenance，并标记 `equivalent_duplicate`；序列化格式差异不构成语义差异 |
| `override` | 当前两层模型中，只有 work 可显式替换 eligible base 的同一 atomic leaf、subresource 或 stable item | 必须无歧义地指向被替换目标；如何编码 target reference 由 05D 决定 |
| `mask` | 当前两层模型中，只有 work 可显式隐藏 eligible base 的 asset、subresource、字段或 stable item；base source 本身保持不变，Windows base-only 结果不受影响 | 必须无歧义地指向被隐藏目标；省略一个字段或文件不自动等于 mask |
| source `remove` | 从拥有该声明的 authority source 中显式删除贡献；删除 work override/mask 可使 base 重新显现，删除 base 会影响所有 eligible target | 这是 authored source change，不伪装成跨层 mask；形成新 source revision，并按 03D 重新 plan/批准 |
| `conflict` | 非等价同目标缺少合法 override/mask，或显式意图缺失目标、目标歧义、多个意图竞争、shape/排序规则无法解析时，阻断正常 resolve/apply | 返回候选、schema path、各自 provenance、digest 和稳定诊断码；不自动选 work、不自动改 source |

- 决定（v0.1，2026-07-17，approver: principal）：05C 选择 **B——显式意图，否则冲突**。不相交贡献继续由 05B 自动组合；同一 ID 的 canonical-equivalent contribution 可以去重；除此之外，base 与 work 命中同一 semantic target 时，只有显式 `override` 或 `mask` 能得到确定 resolved result。
- 显式意图合同：`override`/`mask` 是 work authority 中的 typed contribution，不是 consumer patch 或 live override。它必须声明 operation，并通过 05D 定义的 stable target locator + expected semantic digest 无歧义地固定目标；这些控制元数据进入 source inventory 而非 payload/frontmatter。
- 等价与重复边界：等价性由固定 schema version 下的 canonical semantic value 判断，而非原始 YAML/JSON/TOML 字节或格式。等价贡献 coalesce 后必须保留全部 source/layer provenance，不能因去重而隐去重复来源。
- 删除边界：`mask` 只改变包含该 work contribution 的 Mac resolved state，不删除或改写 base；source `remove` 修改拥有声明的 source，并生成新 revision。省略一个字段或文件不自动表示删除；移除一个既有 work override/mask 则是普通 source edit，重新 resolve 后可让 base 值显现。
- 03B1 边界：05C conflict 默认不自动写入 override/mask。principal 若只想完成当前一次操作，可按 03B1 对精确 target/plan hash/conflict set 做 transient resolution，source 保持不变且下次重新阻断；只有 principal 明确转向“修 source”时，Agent 才生成 override/mask 或其它 source diff。
- 硬策略边界：override、mask、03B1 与 03D approval 都不能扩展 03A authority、04B eligibility、04A/04C residency/egress、DEC-06 secret policy 或 02C capability safety。命中这些条件时是 hard policy block，不是可用 05C precedence 消解的 conflict。
- `Must`：同 ID 同 canonical 内容去重并保留全部 provenance；非等价同目标要求显式 override/mask；无显式意图默认 conflict/block；source remove 与 mask 分离；所有非 no-op 写入继续走 03D；冲突可解释且不自动改 source。
- `Later`：若真实案例需要新的 collision operation 或批量 authoring 辅助，再独立设计；v1 不为假设需求扩充操作集合。
- `Out`：last-layer-wins、按目录/扫描顺序决定 winner、隐式 omission 删除、路径级 patch 主模型、自动把 conflict 写回 source、永久复用 03B1 裁决，以及用 override/mask 越过 hard policy。
- 接受的代价：每个真实覆盖或隐藏都要多保存一个显式意图；没有该意图时，即使 Agent 能推测 principal 想让 work 获胜，也必须先报警并等待现场决策。以此换取拼写错误、旧副本和无意重名不会静默改写 Mac 配置。
- 后果：05D 通过 source inventory 表达 typed contribution，并以精确 target semantic digest 防止旧意图静默覆盖已变化的 base；DEC-07/09/16 必须展示 duplicate、override、mask 与 conflict provenance；DEC-08 只渲染 05C 已确定的 resolved state；DEC-12 要区分 unresolved source conflict 与 live drift；DEC-14/15 必须覆盖 add/override/mask/remove/duplicate/conflict fixture。
- 验收断言：相同固定输入产生相同 resolved state；新增 ID 自动组合；同 ID 同 canonical 内容去重且 provenance 不丢；非等价同目标在无显式意图时零正常写入；显式 override/mask 只作用于其无歧义目标与 eligible Mac 投影；无效或竞争意图阻断；source remove、mask 与 03B1 transient resolution 可被清楚区分；任何 hard policy violation 都不可通过本轴放行。

#### 05D 已拍板：Source inventory + 原生 payload，target 精确摘要绑定

本轴决定两个 authority source 中“控制面元数据放哪里、实际配置内容放哪里”，以及 work override/mask 如何固定它所针对的 base 状态。它不新增 layer，不把 consumer render 或 local binding 变成 authored source，也不要求把 skill、MCP、instructions 等 payload 改写成 Almagest 私有大对象。

| 选项 | Source 表达 | 结论 |
|---|---|---|
| A：纯目录约定 | relative path、文件名和特殊后缀隐式表示 asset ID、kind、override/mask | 拒绝：语义隐藏在路径魔法中，rename 容易改变身份或操作，Agent 必须猜约定 |
| B：Source inventory + 原生 payload | 每个 authority source 提供机器可读 inventory，声明控制元数据并引用保持原生的 payload | **已选择** |
| C：逐资产 sidecar | 每个 payload 旁放独立 metadata 文件，不设 source 级 inventory | 拒绝：局部可读但 sidecar 数量大，跨目录完整性、重复 ID 和漏同步更难检查 |
| D：单体 canonical graph | 把全部配置内容内联到一个大文件/数据库，再生成 skill 目录和 consumer 配置 | 拒绝：会重写现有资产模型、制造大范围迁移和热点 diff，并把控制面扩成完整 authoring platform |

| Target reference 选项 | 绑定范围 | 结论 |
|---|---|---|
| A：Stable ID only | 只绑定 logical/subresource ID，不记录 lower content 状态 | 拒绝：base 目标内容变化后旧 override/mask 仍静默生效，无法判断意图是否过期 |
| B：ID + 精确目标 semantic digest | 绑定 stable target locator 与被操作语义单元的 canonical digest | **已选择** |
| C：ID + 整个 logical asset revision | 即使只覆盖一个字段，也绑定整个 asset | 拒绝：同一资产的无关字段变化也会产生 stale，告警范围过宽 |
| D：ID + 整个 base source revision | 任意 base 文件变化都会让全部 work override/mask stale | 拒绝：无关 source 变化制造全局告警，等价于把常规 replan 变成 overlay 冲突 |

```text
GitHub personal/shared source
├── logical source inventory ──> ID / kind / payload ref / selector / operation / target ref
└── native payload            ──> skills / MCP / instructions / settings / hooks / plugins / ...

Mac-local work source
├── logical source inventory ──> work-only add / override / mask metadata
└── native payload            ──> work-only content or delta payload

Windows：只读取 GitHub source inventory + payload
Mac：分别读取 GitHub 与 work inventory + payload，再按 05A—05C resolve

target ref = stable asset/subresource/item locator + expected target semantic digest
```

- 决定（v0.1，2026-07-17，approver: principal）：05D 的 source 表达模型选择 **B——Source inventory + 原生 payload**。GitHub personal/shared 与 Mac-local work 各自维护一份逻辑 inventory；inventory 是该 source 中控制面元数据的 authored truth，payload 是被引用的实际配置内容。两者共同进入 source revision/provenance，但职责不混写。
- Target 决定（v0.2，2026-07-17，approver: principal）：target reference 选择 **B——stable target locator + 精确目标 semantic digest**。override/mask 必须同时固定被操作的 logical asset/subresource/item/schema leaf 与该语义单元的 expected canonical digest；不得只写 ID，也不得因目标是一个字段而绑定整个 asset 或 source revision。
- Inventory 合同：每个 contribution 至少可表达 stable logical ID、asset kind、source-relative payload reference、selector，以及需要时的 `add/override/mask` operation 与 target locator/expected digest。inventory schema 必须版本化且机器可校验；具体字段名、文件名、YAML/TOML/JSON 选择、digest algorithm 标识、单文件或确定性分片属于实现细节，不在本轮拍板。
- Payload 合同：skill bundle、`SKILL.md`、scripts/references/assets、MCP/settings、instructions、hooks、plugin 配置等保持其自然 authored 形态。inventory 不内联或复制 payload 正文；payload 路径变化但 logical ID 不变时仍是同一资产，实际 revision 继续按 01C 的 canonical content 规则计算。
- Frontmatter/token 边界：Almagest 的 ID、selector、operation、target reference、provenance 等控制元数据只存在于 inventory，不得注入 Agent 消费的 `SKILL.md` frontmatter、prompt/instruction body 或 rendered consumer config。payload 自身原本属于 consumer/asset schema 的 frontmatter 不受本轴删除或翻译；其处理仍由 DEC-08C 决定。
- 完整性边界：只有 inventory 显式登记且 payload reference 能在当前 authority source root 内唯一解析的 contribution 才进入 candidate set。缺失/不受支持的 inventory schema、重复 logical ID、dangling/ambiguous reference 或越出 source root 的引用均 `invalid_source/block`；payload root 内未登记的候选内容不得自动 adopt，只能作为 `orphan + unknown-owner` evidence 交给 DEC-07/09，除非另有正向证据证明其 `external-owned` owner。
- 两源隔离：base inventory 不引用 work payload、work metadata 或 Mac-local 绝对路径；work inventory 与 payload 全部继承 04A/04D 的 Mac-only 边界。Windows 不读取、不接收也不探测 work inventory；Mac 分别验证两个 source 后才按 04B eligibility 与 05A—05C resolve。
- 非 layer 输入：selector 可以收窄 entry 的 target eligibility，但不能扩权；inventory 可以声明 local binding reference，却不能保存 DEC-06 管理的本机值。adapter/render 读取 inventory 和 payload 生成 derived artifact，但 consumer 格式、root、profile 与 live 文件均不能反向成为 inventory contribution。
- Target digest 合同：expected digest 由 05B 的固定 adapter/schema 对精确目标单元做 canonical semantic normalization 后计算，不使用原始 YAML/JSON/TOML 字节、文件路径、mtime 或整个 source snapshot。格式化、payload 移动或其它字段变化只要不改变目标语义，重新 plan 后 target reference 仍有效；目标本身变化、消失或 schema identity 无法验证时返回 `stale_target/block`。
- Plan 与 stale 边界：任何 source/inventory revision 变化仍按 03D 使旧 plan/approval 失效；重新 plan 时只有 expected target digest 不匹配才使 override/mask 意图 stale。Almagest 必须报告 target locator、expected/observed digest、目标语义差异与 provenance，不得自动刷新 expected digest、扩大目标或继续套用旧意图。
- 恢复出口：principal 可要求 Agent 更新/删除 override 或 mask，或在确认新 base 语义后更新 expected digest；这些都是 work source edit，形成新 revision 并重新 plan。若只处理当前一次，可走 03B1 transient resolution，不能把单次裁决写成永久 digest 刷新。
- `Must`：每个 authority source 一份逻辑、版本化、机器可校验的 inventory；原生 payload 独立保存；ID/kind/payload ref/selector/operation 可表达；override/mask 使用 stable target locator + exact expected semantic digest；control metadata 不进入 consumer payload；引用不越 source root；invalid/stale inventory fail closed；base/work inventory 与驻留边界分离。
- `Later`：若规模证明单一物理文件产生热点，可在不改变逻辑 inventory 和确定性读取顺序的前提下分片；当前不预建 registry service、数据库或远程 inventory。
- `Out`：路径/文件名隐式权威、逐资产 sidecar 作为唯一索引、把 payload 正文复制进 inventory、单体配置数据库、从 consumer frontmatter/live 输出反推 inventory、把 control metadata 注入 Agent 上下文、base inventory 引用任何 work 事实、ID-only target、用 whole asset/source revision 代替精确目标摘要，以及自动刷新 expected digest。
- 接受的代价：Agent 新建、移动或删除受管资产时必须同时维护 inventory reference，并由校验器检查 dangling/orphan/duplicate；base 的被覆盖/隐藏目标发生语义变化后，work intent 会阻断并要求现场处理。以此换取 identity 与 overlay 意图不依赖路径猜测，旧 work 意图不会静默吞掉 base 更新，且 Almagest 元数据不消耗 Agent frontmatter/token。
- 后果：DEC-06 必须区分 inventory 中的 binding reference 与本机值；DEC-07 以 inventory 为 managed candidate 基线并报告 orphan/dangling/stale target；DEC-08 从原生 payload 生成 consumer render，不能把 inventory 本身投影出去；DEC-09 固定 inventory/schema/payload revision 与 expected/observed target digest；DEC-14 定义 inventory、payload 与 digest refresh 的原子增删迁移；DEC-15 版本化 inventory/schema canonicalization fixture；DEC-16 可从 projection 追溯 inventory entry、payload revision 与 target digest mismatch。
- 验收断言：相同两个 source inventory、payload revision、schema/adapter 与 target 输入产生相同 resolved state；Windows 只消费 base inventory/payload，Mac 消费 base + work 且 work 事实零离机；只有登记且 source-root 内可解析的 payload 参与 resolve；invalid/dangling/duplicate 引用阻断；unlisted payload 不被自动接纳；移动 payload 不改变 logical identity；任何 control metadata 都不进入 consumer frontmatter/body/render；override/mask 精确绑定 target semantic digest，目标语义变化时 stale/block，无关变化只触发 replan 而不使意图 stale。

### DEC-06 Secret 与本地参数

- 状态：06A—06D 已拍板
- 依赖：DEC-03—DEC-05。
- 决策轴：
  - 06A：secret value/reference、本机绝对路径、账号、OS/host 参数如何分类。
  - 06B：各类 reference/local binding 存在哪里、由谁提供、哪些 binding scope 可以补值或替换引用；外部 credential provider 仍拥有 secret value 生命周期。
  - 06C：plan、diff、receipt、日志和错误信息如何脱敏。
  - 06D：缺值、引用失效或权限不足时如何 fail closed 并诊断。

#### 06A 已拍板：Portable declaration、host-local binding、observed host fact 三分类

本轴只决定 secret、路径、账号与 host 差异在配置模型中属于哪类事实。binding 的物理存储、provider、scope 与补值顺序现由 06B 固定，安全披露由 06C 固定，缺值后的诊断与恢复由 06D 固定。

| 选项 | 分类模型 | 结论 |
|---|---|---|
| A：Authored / local 两类 | 所有 portable 声明归 authored，其余本机信息统一归 local | 拒绝：可补值的 binding 与只读 observation 混在一起，容易把当前环境误当 desired state |
| B：Declaration / binding / observation 三类 | 分开表达可移植需求、本机补值与当前主机事实 | **已选择** |
| C：Secret / non-secret 两类 | secret 本机化，其余内容均可进入 source | 拒绝：绝对路径、账号、machine ID 与 local endpoint 即使不是 secret，也不可移植且可能泄漏 |
| D：各 adapter 自由分类 | 每类 asset 自行决定 local-sensitive 字段语义 | 拒绝：同一账号、路径或 host 参数会跨 asset 得到不同 authority 与漂移结论 |

```text
portable declaration/reference
        │ declares typed slot / requirement / constraints
        ▼
host-local binding value or provider locator
        │ satisfies an existing slot for one target
        ▼
per-target render input

observed host fact ──> selector / capability / validation evidence
                     （只读输入，不是 desired contribution）
```

- 决定（v0.1，2026-07-17，approver: principal）：06A 选择 **B——portable declaration/reference、host-local binding value、observed host fact 三分类**。分类依据是某个表示在配置链路中的职责，不是“账号”“路径”“host 参数”等名词本身。
- Portable declaration/reference：由 GitHub personal/shared 或 Mac-local work 按既有 authority 声明“需要什么”，包括 stable binding slot/ref、value type、required/optional、sensitivity、约束与可移植 selector。它可以表达 provider-neutral 的逻辑引用，但不得内联某台机器的实际 secret、绝对路径、账号选择、machine ID 或 local endpoint。
- Host-local binding：为一个已声明 typed slot 在当前 target 上提供机器相关值或 provider locator，包括实际绝对路径、当前选定账号/profile、本机 endpoint/proxy、machine ID，以及指向本机 credential provider 中 secret material 的定位信息。secret value 的生命周期仍由外部 credential provider 拥有；06A 不决定 Almagest 如何取得或暂存它。
- Observed host fact：Almagest 在当前 host 读取但不拥有的事实，包括 OS/architecture/hostname、consumer/version、路径存在性与权限、credential/login 可用性及其它 capability 状态。它们只能作为 selector、capability、plan/verify 证据或诊断输入，不是 authored desired state，也不是 binding override。
- 同名不同阶段：同一概念必须按表示逐项分类。例如“所需账号角色/逻辑引用”是 portable declaration，“本机选中的账号/profile”是 host-local binding，“当前是否登录及权限是否有效”是 observed fact；“路径 slot”是 declaration，“解析后的绝对路径”是 binding，“路径是否存在/可访问”是 observation。
- Authority 边界：只有 portable declaration/reference 可以形成 authored contribution；host-local binding 只能满足 schema 已声明且允许本机补值的 slot，不能新增 asset、改变逻辑引用语义、覆盖普通 authored 字段或绕过 source trust/work residency。observed fact 更不能反向写成 source 或 binding。
- Layer 边界：三分类是 data-role model，不是三层 overlay。authored layer 仍只有 DEC-05A 的 GitHub base 与 Mac-local work；binding 和 observation 都不取得 precedence、override、mask、remove 或 conflict winner 权力。
- 未知分类：schema/adapter 无法证明某个 local-sensitive 字段属于哪一类时，不得按 non-secret、local default 或 adapter 惯例猜测；该字段标记 `unknown_local_role/block`，并按 06D 返回安全诊断与显式修复选项。
- `Must`：所有 local-sensitive schema 字段可被确定地归入三类之一；reference 与 value 分离；binding 只能填充现有 typed slot；observation 保持只读；secret value 不进入 authored source；binding/observation 不形成第三 authored layer。
- `Later`：Agent authoring hint、从既有 consumer 配置推断候选分类、交互式 binding bootstrap；所有推断在明确采纳前都不取得 authority。
- `Out`：secret/non-secret 二分替代 data-role 分类、任意 local overlay、按环境变量或 adapter 惯例隐式取得 authority、把当前 host observation 写回 desired source、把 secret value/绝对路径/machine ID 作为 logical asset ID，以及在 06A 预设 credential store 或 binding 文件格式。
- 接受的代价：每个 adapter/schema 必须显式标出 local-sensitive 字段的 role，Agent 遇到旧配置或含混字段时需要先补分类而不能直接投影。以此换取“需要什么”“本机填什么”“当前观察到什么”三种事实不会互相冒充。
- 后果：06B 已为 declaration→binding 固定 provider、存放与合法 scope，且不让 binding 获得 authored authority；06C 已按三类固定 value、reference 与 observation 的安全披露边界；06D 已区分 slot 缺值、provider/ref 失效与 observation 不满足，并禁止自动 fallback。DEC-07 分栏盘点 authored/binding/observed，DEC-08 只在 target render 时消费合法 binding，DEC-09/12 区分 source drift、binding drift 与 observation/capability 变化，DEC-16 保留分类与 provenance 而不泄漏值。
- 验收断言：相同 source declaration 在不同 host 可绑定不同本机值而不改变 authored revision；secret value、绝对路径、实际账号和 machine ID 不进入 portable source；OS/权限/登录状态等 observation 不取得配置 authority；binding 不能新增或覆盖未声明字段；任何本机信息都不能因被命名为“参数”而成为第三 overlay layer；分类未知时 fail closed。

#### 06B 已拍板：显式 typed host-local binding registry

本轴决定 host-local binding 的受管入口、provider 边界、合法 scope 与匹配规则。registry 只把已声明 slot 绑定到当前 host 可用的非 secret 值或 provider locator；它不是第三 authored source，也不替代外部 credential provider。

| 选项 | Binding 入口 | 结论 |
|---|---|---|
| A：Provider 直连与隐式发现 | source reference 直接约定环境变量、Keychain 名称或文件路径，不设 registry | 拒绝：依赖散落在 provider 命名和进程环境中，无法统一盘点、定 scope 或区分缺失与拼错 |
| B：Typed binding registry + provider adapter | 每台 host 一份显式 registry，按 slot 与 scope 绑定非 secret 值或 provider locator | **已选择** |
| C：Consumer native/live config | 从 Codex/Qoder/Claude 已有配置反向读取 binding | 拒绝：rendered/live 状态会取得 authority，形成 source→render→binding→render 的循环 |
| D：通用 local overlay | 本机文件可覆盖任意配置字段并作为最终值 | 拒绝：重新制造第三 authored layer，绕过 05C 显式 override 与 source provenance |

```text
authored slot contract
  slot ID / type / sensitivity / allowed scope / binding mode
                         │
                         ▼
host-local typed binding registry
  slot ID + host|exact-target scope + fill|replace-ref + local value|provider locator
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
      non-secret render input   explicit provider adapter
                                      │
                                      ▼
                            external credential provider
                              （secret value owner）
```

- 决定（v0.1，2026-07-17，approver: principal）：06B 选择 **B——每台机器一份逻辑 typed binding registry + 显式 provider adapter**。Mac 与 Windows 各自维护本机 registry，不通过 Git、Almagest 中央服务或跨机 receipt 同步；具体文件名、序列化和是否物理分片属于实现细节。
- Registry 角色：registry 是 Almagest 可 inventory/plan/apply/verify 的 host-local managed input，但没有 authored authority。它只保存 stable slot ID、显式 target scope、binding mode、非 secret 本机值或 provider locator，以及验证所需的类型/敏感性元数据；不得保存 secret value、skill/instruction 正文或任意配置 patch。
- Provider 边界：环境变量、OS Keychain/credential manager、本机文件或其它 provider 只有被 registry entry 显式引用时才成为 binding provider；不得扫描后自动 adopt，也不得按 slot 名猜 provider/key。secret value 的创建、轮换、撤销与存储仍由外部 credential provider 负责，Almagest 只验证 locator 与消费结果。
- Scope 白名单：v1 只允许 `host-wide` 与 `exact-target`。source slot contract 必须显式声明允许哪些 scope；`host-wide` 只能服务当前 host 上明确允许共享的 slot，`exact-target` 必须匹配 DEC-02 的稳定 target identity。cwd、临时 session、进程环境或扫描顺序不形成额外 scope。
- 唯一匹配：对一个 `(slot ID, target)`，合法 scope 解析后必须至多得到一个 binding candidate。多个 host/target entry 同时命中时返回 `ambiguous_binding/block`，不采用 exact-target-wins、last-writer-wins 或 provider 顺序；零匹配保持 unresolved，并按 06D 区分 required block 与显式 optional omission。
- 补值与替换：默认 binding 只能 `fill` 空 slot，或把既有 provider-neutral logical reference `resolve` 为本机 locator/value。只有 source slot contract 明确声明 `replaceable` 并允许当前 scope 时，registry 才能以 `replace-ref` 为当前 target 替换逻辑 reference；它仍不得覆盖 concrete portable value、普通 authored 字段或 source 内容。
- 变更权：operator Agent 可按 principal 指令新增、修改或删除本机 registry entry；这是受管配置写入，必须进入 DEC-03D 的精确 non-no-op plan。Almagest 不自动从 env、provider、native/live config 或 observation 反向写 registry。
- Revision 边界：registry schema、当前 registry revision/digest、命中的 entry identity 与 provider kind 必须成为 plan/verify 输入；任何变化使旧 plan/approval 失效。plan、receipt、日志和错误只能按 06C 的 safe view 披露这些信息。
- 驻留边界：registry 及其值、locator、存在性和 digest 全部留在当前 host；由 work declaration 派生的 binding metadata 继续继承 04D 的 Mac-only 边界。两台 host 可以对同一 base slot 绑定不同值，但不得交换 registry 或生成跨机差异报告。
- `Must`：一台 host 一份逻辑 typed registry；slot/type/scope/mode 显式；只允许 host-wide/exact-target；唯一匹配；secret value provider-owned；registry revision 进入 plan；所有写入走 03D；binding 不能取得 authored authority。
- `Later`：由 Agent 辅助 bootstrap registry entry、provider health probe 与 provider adapter 扩展；候选在 principal 批准本机 plan 前不得写入 registry。
- `Out`：隐式 env/keychain/file 命名约定、provider 自动扫描/adopt、从 consumer native/live config 反向补 registry、跨机同步 registry、在 registry 保存 secret value、通用 local patch、scope precedence 和未声明的 reference replacement。
- 接受的代价：每台机器需要独立维护 registry，并为 slot、scope、mode 和 provider locator 多保存显式元数据；同一 slot 出现多个候选时，即使可按“最具体”猜出结果也必须先处理冲突。以此换取 binding 可盘点、可计划、可验证，且 provider/live 状态不会暗中取得配置权威。
- 后果：06C 已对 registry value、provider locator、entry identity 与 observation 固定分级披露；06D 已分别固定零匹配、ambiguous binding、dangling locator、provider 权限和 value validation 的阻断、诊断与恢复合同。DEC-07 必须把 registry entry 与 provider observation 分栏；DEC-08 只能消费唯一合法 binding；DEC-09 固定 registry revision 与命中 entry；DEC-10 对 registry 写入提供原子性/备份/回滚；DEC-12 将 registry revision/value mismatch 视为 binding drift，而非 source overlay；DEC-16 在本机解释 slot→entry→provider→render 链路。
- 验收断言：相同 authored slot 可在 Mac/Windows registry 中绑定不同本机值；未登记的 env/provider/live 值不会自动生效；secret value 不进入 registry；scope 未授权、多个 entry 命中或未声明 replace-ref 均阻断；registry 变更使旧 plan 失效并需要 principal 批准；registry 不跨机、不进 Git、不成为第三 authored layer。

#### 06C 已拍板：Schema-driven、per-surface safe view

本轴决定 plan、diff、receipt、日志、错误和 explain 如何暴露配置事实。安全输出不是把完整对象序列化后再用正则打码，而是从 rich internal state 投影出版本化、字段白名单化的 safe view；不允许披露的字段从未进入 reportable object。

| 选项 | 输出策略 | 结论 |
|---|---|---|
| A：字段名/正则打码 | 先生成完整输出，再替换 token/password/secret 等命中值 | 拒绝：依赖命名惯例，非标准字段、嵌套对象和 provider 原始错误容易漏出 |
| B：Schema-driven per-surface safe view | 按 sensitivity class 与输出 surface 生成独立白名单结构 | **已选择** |
| C：所有 value 一律隐藏 | 任何 surface 只显示字段名、状态和计数 | 拒绝：虽然简单安全，但 portable 配置 diff 不足以让 principal 审批真实变化 |
| D：本机完整输出，外发前脱敏 | 本地 plan/log/error 保留全部值，只在 egress 时处理 | 拒绝：secret 可能先进入 Agent context、终端历史、日志、异常和临时文件，已经失去控制 |

| Sensitivity class | Plan / diff / default explain | Receipt | Log / diagnostic | 定向 reveal |
|---|---|---|---|---|
| `portable-safe` | 可按 ID 取得精确 before/after；紧凑摘要仍由 09C 定义 | action/result/revision/digest；不复制无必要正文 | stable ID、change kind、状态、原因码 | 无额外限制 |
| `local-sensitive` | 默认只给 slot/entry ID、type、scope、change kind、状态与结构化 redaction marker | 不保存 value/locator，只保存本机 opaque identity、结果与 redaction reason | 不保存 value/locator/path/account/machine ID | 仅 non-secret 字段可在当前 host、当前精确 explain 中经 principal 单次确认后显示 |
| `secret` | 只给 `absent/present/changed/invalid/permission_denied` 等状态；不读值用于报告 | 状态、provider kind 与操作结果；无 value、locator 或 value-derived token | 状态与安全原因码 | **永不 reveal** |
| `unknown` | 隐藏并 `unknown_sensitivity/block` | 仅记录阻断与分类缺失 | 安全诊断，不透传原值 | 禁止 |

```text
rich internal state
        │ typed sensitivity + surface policy
        ▼
safe projection boundary
   ├── plan/diff view
   ├── receipt view
   ├── log/diagnostic view
   └── explain view

secret value ──X──> reportable object / hash / fingerprint / raw error
```

- 决定（v0.1，2026-07-17，approver: principal）：06C 选择 **B——schema-driven、per-surface safe view**。adapter/schema 必须为可报告字段声明 sensitivity class；每种 surface 使用独立、版本化的 allowlist schema，不复用可包含 secret/local value 的 render/internal object。
- Secret 不可序列化：secret value 不得进入 plan、diff、receipt、日志、错误、trace、telemetry、cache key、hash、fingerprint、exception message 或 explain。禁止对 secret value 输出稳定/非稳定 digest，因为低熵值可被离线猜测，任意 digest 也会制造跨运行关联标识；报告只使用 provider/registry 已有的安全 revision 与状态证据。
- Local-sensitive 默认边界：绝对路径、账号/profile、provider locator、machine ID、local endpoint 与其它本机敏感值默认不进入 summary、plan/diff value、receipt、日志或错误。safe view 必须返回 stable slot/entry ID、type、scope、change kind、状态，以及结构化 `{redacted: true, sensitivity, reason}`，不能只输出语义不明的 `***`。
- Portable-safe 边界：被 schema 明确标记为 `portable-safe` 的配置可在 plan/diff 或按 ID explain 中显示精确 before/after，以支撑 DEC-03D 审批；compact summary、receipt 和常规日志仍只保存完成职责所需的最小结构，不因“safe”复制整段 skill/instruction 正文。
- 定向 reveal：只有 schema 明确标记为 non-secret 的 `local-sensitive` 字段可被 reveal。principal 的单次确认必须绑定 current host、target、plan/explain identity、精确 field/slot ID 与本次调用；不得批量、通配、跨 host、持久化或复用。reveal 结果不写 receipt/log/cache，且 04D 的 work Mac-only 边界继续生效。
- Provider/error 边界：provider 原始 stdout/stderr、exception message、response body 和命令回显均视为 unsafe input，不得直接透传。provider adapter 必须在边界内映射为 stable diagnostic code、provider kind、operation、safe status 与 allowlisted metadata；无法证明安全的字段丢弃并标记 `diagnostic_redacted`。
- Unknown fail closed：字段缺少 sensitivity、schema 不受支持，或嵌套/动态值无法套用 allowlist 时，值先隐藏并返回 `unknown_sensitivity/block`；不得退回 key-name regex、best effort serialization 或“仅本机所以安全”。
- Surface/egress 边界：所有 safe view 仍继承 04D 驻留策略；Mac work-derived ID、状态、数量、digest 和 redaction metadata 也不得离开 Mac。06C 不引入远程 telemetry、中央日志或跨机 receipt，也不决定 consumer render/live 是否需要 secret material，后者由 DEC-08/10 的投影与写入合同处理。
- `Must`：schema sensitivity 必填；safe projection 先于 serialization/logging；secret value 永不报告/哈希/reveal；local-sensitive 默认隐藏；portable-safe 精确 diff 可审；unknown 隐藏并阻断；raw provider error 不透传；所有 surface 有独立 allowlist schema 和负向 fixture。
- `Later`：更多细粒度 sensitivity class、provider-specific safe metadata 和受控 explain ergonomics；不得降低 secret 永不序列化或 unknown fail-closed 基线。
- `Out`：regex/key-name 作为主防线、serialize-then-scrub、secret hash/fingerprint、完整本地 debug dump、raw stdout/stderr/exception 透传、全局 reveal 开关、持久 reveal grant、以加密日志或“仅本机”替代 safe view，以及把 consumer secret render 混入 report surface。
- 接受的代价：schema/adapter 要维护 sensitivity 与多套 surface DTO，排障时默认看不到本机值，provider 集成也不能直接复用原始错误文本；需要额外的 safe diagnostic 和单字段 explain 流程。以此换取 Agent 操作、日志和失败路径不会成为绕开 registry/provider 边界的 secret 出口。
- 后果：06D 已将所有错误状态和 resolution action 固定为不依赖原值的 safe diagnostic；DEC-07 inventory 只能保存允许的 binding/observation metadata；DEC-09 plan/approval 使用 safe diff；DEC-10 receipt/rollback evidence 不保存 secret/local-sensitive value；DEC-12 drift 依赖 registry/provider revision 与状态而非 secret digest；DEC-15 为每类 surface 和 provider error 维护 secret-canary 负向 fixture；DEC-16 explain/audit 复用相同 safe projection。
- 验收断言：向任意 secret slot 注入 canary 后，plan/diff/receipt/log/error/trace/explain 均无 canary 或其 hash；portable-safe 字段仍可获得精确 diff；local-sensitive 默认只返回结构化 redaction marker，单次定向 reveal 只能显示获批的 non-secret 字段；unknown sensitivity 阻断；provider 原始错误中的 secret 不会透传；不同 surface 不因复用同一对象扩大披露。

#### 06D 已拍板：类型化 fail-closed、显式修复选项、principal 现场决策

本轴决定 binding 解析、provider 访问、值校验或 host observation 失败后，Almagest 是否继续，以及 operator Agent 应拿到什么。错误不会触发自动猜测或修复；Almagest 返回遵守 06C 的机器可读诊断和有限 resolution action，由 principal 在当前操作中选择。

| 选项 | 失败与恢复策略 | 结论 |
|---|---|---|
| A：所有异常统一 hard block | required、optional 与任一 observation 失败均阻断当前 target，不区分失败语义 | 拒绝：实现简单，但 optional 失去语义，也不能表达可安全省略与必须修复的区别 |
| B：类型化 fail-closed + 显式 resolution action | 按失败类型阻断受影响 target；只有 schema 证明可安全省略的 optional slot 可显式 omission；principal 现场决定修复 | **已选择** |
| C：自动 fallback / skip | 自动尝试 env、其它 provider、默认值或跳过失败字段，再向 principal 报告 | 拒绝：让隐式候选重新取得 authority，且报告发生在配置已经偏离之后 |
| D：last-known-good / cache | provider 或 binding 暂不可用时复用旧值继续 | 拒绝：旧值可能已撤销、失效或越权，secret cache 还会扩大生命周期与泄漏面 |

| Diagnostic code | 语义 | 当前操作结果 | 允许提供的 resolution action |
|---|---|---|---|
| `missing_required_binding` | required slot 无合法唯一 binding | 阻断依赖该 slot 的 target resolve/render/apply | `create_binding`、`change_source_requirement`、`retry` |
| `missing_optional_binding` | optional slot 无 binding | 仅当 source 明确 optional 且 adapter/schema 定义 deterministic safe omission 时生成 `optional_omitted`；否则按 required block | `accept_optional_omission`、`create_binding`、`change_source_requirement` |
| `ambiguous_binding` | 同一 slot/target 命中多个合法候选 | 阻断，不猜 scope/provider precedence | `edit_binding_scope`、`remove_binding`、`retry` |
| `dangling_locator` | registry 引用的 provider locator 不存在或不可解析 | 阻断 | `update_locator`、`repair_provider_entry`、`retry` |
| `permission_denied` / `auth_unavailable` | provider、路径或账号不可访问 | 阻断 | `repair_permission_or_login`、`change_binding`、`retry` |
| `invalid_binding_value` | value 不满足声明的 type/constraint | 阻断 | `update_binding`、`change_source_constraint`、`retry` |
| `observation_unsatisfied` | OS、consumer capability、路径或其它 required observation 不满足 | 阻断受影响 target | `repair_host_condition`、`change_source_requirement`、`retry` |
| `provider_unavailable` | 显式 provider 当前不可用，且不能证明只是安全的 optional omission | 阻断，不使用 cache | `repair_provider`、`change_binding`、`retry` |
| `unknown_local_role` / `unknown_sensitivity` | schema 无法确定 role 或安全披露等级 | 阻断 | `fix_schema_or_adapter`、`retry` |

```text
resolve / provider / validate / observe
                    │
                    ▼
          typed safe diagnostic
          code + target/slot ID
          impact + safe evidence
          resolution action kinds
                    │
                    ▼
        operator Agent 向 principal 报告
                    │
          principal 选择精确动作
                    ▼
     正常 authority / plan / approval 流程
                    │
                    ▼
             重新 resolve + validate
```

- 决定（v0.1，2026-07-17，approver: principal）：06D 选择 **B——类型化 fail-closed + 显式 resolution action + principal 现场决策**。Almagest 只裁定状态、影响边界与合法动作类型；operator Agent 负责解释并按 principal 指令进入已有 source、registry 或外部 provider 修复流程。
- 阻断粒度：required 缺值、ambiguous、dangling locator、权限/登录失败、invalid value、required observation 不满足、provider unavailable 与未知分类，只阻断依赖该失败的 target resolve/render/apply；当前 host 上不依赖它的只读 inventory、diff、explain 和健康 target 仍可继续。多 target plan/apply 的部分执行边界留给 DEC-09/10，06D 不授权绕过被阻断 target。
- Optional 唯一降级：只有 portable source 已显式声明 `optional`，且固定 adapter/schema 定义“省略该字段不会产生含混语义或不安全 consumer default”时，零匹配才能成为 `optional_omitted`。该 omission 必须在 plan 中逐项可见并由 principal 随精确 plan 批准；缺少任一证明时按 `missing_required_binding/block` 处理。
- Safe diagnostic：每条诊断至少含 stable diagnostic ID/code、target ID、slot/entry opaque ID、失败阶段、block/omitted 状态、影响范围、固定输入 revision evidence 与 allowlisted resolution action kind；不得包含 secret、provider locator、本机路径、账号或原始 provider error。具体字段编码归 DEC-09A，披露始终服从 06C。
- Resolution authority：action 是给 operator Agent 与 principal 的受限菜单，不是自动执行授权。修改 GitHub/Mac-local source、host-local registry 或其它受管配置必须形成新的 DEC-03D non-no-op plan；修复外部 credential provider、权限或登录由对应 owner/tool 完成。任何修复后都必须重新读取 observation、resolve、validate 并生成新 plan，旧 failure evidence、plan 与 approval 不可复用。
- `retry` 语义：retry 只在 principal 或 operator Agent 已知外部条件可能变化后重新读取固定入口，不得扫描新 provider、换 locator、采用环境变量、复用旧 secret/value 或改变 requirement；输入 revision 变化仍使旧 plan 失效。
- Acknowledgment 边界：acknowledge、普通 approval、一次性 reveal 或“本机可用”声明都不能把 blocker 变成 success。解除阻断必须由修复后的新 evidence 证明原 failure 已消失；02C 的 unsupported-target exception 不能覆盖 secret/binding/provider 的 authority、安全或 residency 边界。
- 聚合诊断：一次本地调用应返回当前 target 上所有能够在不跨越安全边界的独立 blocker/omission，避免 Agent 修一个才发现下一个；探测过程中遇到 unsafe/unknown 边界时停止该分支并报告对应 blocker，不为收集更多错误读取未授权值。
- `Must`：稳定 failure taxonomy；required fail closed；optional omission 必须 source+schema 双重显式；affected-target 阻断；safe diagnostic + bounded resolution actions；principal 现场选择；修复后重新验证与重新 plan；无自动 fallback/cache/silent skip。
- `Later`：provider-specific remediation hint、在不泄漏值的前提下聚合依赖图与批量修复 plan；不得把 hint 升格为自动 authority。
- `Out`：自动 provider discovery/fallback、隐式 env/default、silent optional skip、last-known-good、secret cache、失败后先 apply 再报告、persistent acknowledgment、用 reveal/approval 绕过 blocker、自动修改 required→optional，以及 Almagest 自行吸收或轮换外部 credential。
- 接受的代价：短暂 provider/权限故障也会停止受影响 target，Agent 与 principal 需要现场选择修复动作；schema 还必须明确 optional omission 的安全语义。以此换取任何继续运行的降级都是 source 已声明、schema 可证明、plan 可见且 principal 已批准的结果。
- 后果：DEC-07 必须把 unresolved、blocked、optional_omitted 与 observed failure 分栏；DEC-08 只能 render resolved 或获批 optional omission；DEC-09A 固定 diagnostic/action schema 与 block-only plan，DEC-09D 绑定 principal approval 和输入 revision；DEC-10 禁止被阻断 target 写入并在修复后重新验证；DEC-12 把持续/新发生的 failure 作为本机 drift signal；DEC-16 按 diagnostic ID 解释 failure→impact→resolution chain。
- 验收断言：required binding 缺失、ambiguous、dangling、权限拒绝、invalid value、provider unavailable 或未知分类时，受影响 target 零写入且返回安全 typed diagnostic；optional 只有在 source/schema 双重允许时才显式 omission；Almagest 不自动采用 env/其它 provider/cache/default；principal 选择修复后必须通过正常 authority/plan 流程并重新验证，单纯 acknowledgment 不能解除阻断。

### DEC-07 Inventory

- 状态：07A—07B 已拍板；07C—07D 待给方案
- 依赖：DEC-01—DEC-06。
- 决策轴：
  - 07A：v1 对 source、resolved、rendered、live 和绑定事实盘点到什么粒度；Later 的 effective evidence 是否另表保存。
  - 07B：如何标注 managed、external-owned、orphan、duplicate、unknown-owner。
  - 07C：如何标注 observed、inferred、unknown，以及采集时间、版本和证据来源。
  - 07D：发现边界、权限不足、不可访问 host 与部分结果如何表达。
- 初步验收：报告不把“文件存在”写成“consumer 已加载”；`external-owned` 或 `unknown-owner` 资产可被发现，但不会因此自动取得 adopt、修改或删除授权。

#### 07A 已拍板：按配置流水线生成 logical stage inventory

本轴决定 v1 要看见哪些配置阶段及其最小粒度。05D 的 `source inventory` 是 authored source 内的控制元数据；07A 的 `stage inventory snapshot` 是一次本机只读盘点产生的阶段事实。后者不得反向取得 source authority，也不证明 consumer 进程已经加载配置。

| 选项 | Inventory 范围 | 结论 |
|---|---|---|
| A：两端对比 | 只盘 authored source 与最终 live target | 拒绝：成本最低，但出现差异时无法区分 eligibility/merge、binding、render 还是 materialize 阶段出错 |
| B：配置流水线 logical stage inventory | 按 logical asset/subresource 盘点 source、resolved、rendered、live，并分栏记录 binding/observation；effective evidence 另表 Later | **已选择** |
| C：完整物理快照 | 枚举 roots、文件、symlink、cache、provider 与原始内容，保存 host 物理快照 | 拒绝：敏感面与噪声过大，路径细节会压过逻辑资产，也把配置控制面扩成 host snapshot manager |
| D：Runtime-effective-first | 以 consumer 实际 loaded/registered/callable 状态为主，再反推配置阶段 | 拒绝：依赖不稳定 runtime probe，无法覆盖 consumer 离线状态，并会让观察结果反向主导 desired 配置 |

```text
authored source inventory + payload
                │
                ▼
            source stage
                │ eligibility / merge
                ▼
binding facts → resolved stage ← capability observations
                │ consumer adapter / renderer
                ▼
           rendered stage
                │ materialize
                ▼
              live stage

effective evidence ── Later / 独立 evidence set ──X──> v1 配置真相
```

| Stage / facts | v1 盘点对象 | 明确不声称 |
|---|---|---|
| `source` | 每个 eligible/ineligible authored contribution 的 source ID/class、inventory entry、logical asset/subresource ID、kind、operation/selector、payload revision 与 source provenance | 不把 unlisted payload、外部候选、live 文件或当前 consumer 状态当 authored contribution |
| `binding` | slot/entry opaque ID、scope、mode、provider kind、registry revision、resolution status 与 target 关联 | 不保存或报告 secret value、provider locator、本机敏感值，也不把 binding 当第三 authored layer |
| `observation` | target/consumer/schema/capability 等解析与验证实际使用的 host fact identity、status 与 evidence reference | 不把 observation 当 desired value；置信度、freshness 与 observed/inferred/unknown 规则留给 07C |
| `resolved` | 每个 target 的 canonical logical asset/subresource、resolved revision/digest、schema version、contribution lineage、merge/conflict/binding/optional 状态 | 不代表 consumer 格式，不复制 source payload，也不因 resolve 成功宣称已写入 live |
| `rendered` | consumer-specific derived artifact/item ID、target、renderer/adapter version、expected semantic digest、resolved lineage 与 intended live ref | 不取得 authored authority，不把生成成功写成 materialize 成功或 runtime effective |
| `live` | adapter 声明的受限 config root/key 中实际存在、缺失、不可读或无法映射的文件/config item，及其 observed semantic digest、parse/read status、rendered mapping | 不把“存在/可解析”写成 loaded、enabled、callable 或 observed-used |
| `effective`（Later） | DEC-11 单独定义的 present/registered/discoverable/enabled/callable/observed-used evidence、consumer version 与 probe identity | 不进入 v1 stage snapshot 的成功口径，不覆盖 source/resolved/rendered/live 事实 |

- 决定（v0.1，2026-07-17，approver: principal）：07A 选择 **B——按配置流水线生成 logical stage inventory**。v1 在当前 host、当前 target 上盘点 `source → resolved → rendered → live`，并把 binding 与 observation 作为有 provenance 的 side facts 分栏；runtime effective evidence 只在 Later 以独立 evidence set 表达。
- 共同粒度：stage record 以 `inventory snapshot + stage + target ID + logical asset ID + optional stable subresource/item ID` 为主键语义，附 asset kind、presence/state、stage revision/digest 与上游 provenance reference。物理路径、文件名、行号、config key 只作为 stage-specific evidence/ref，不替代 01B 的 logical identity。
- Snapshot 与 authored inventory 边界：`stage inventory snapshot` 是某次本地调用的只读结果，不写回 05D source inventory、payload 或 binding registry。snapshot identity、采集边界和固定输入必须可引用；observed/inferred/unknown、采集时间与 freshness 语义由 07C 继续决定，plan 如何冻结 snapshot 由 09B 决定。
- Stage 连续性：每个 stage record 必须引用直接上游 record/revision，或给出稳定 absent/blocked/unresolved reason。下游尚未产生不是“资产不存在”：source invalid、resolve conflict、binding block、render unsupported、live missing/unreadable 必须停在相应 stage 并保留可解释断点。
- Bounded live discovery：live 只读取 target/adapter 声明的配置 roots、文件类型、config keys 与引用边界；具体多 root、precedence、shadow 语义由 08A 决定。边界外 host 文件、process、package、cache、history、session 与模型数据不因本轴进入全盘扫描。
- Unmapped candidate：在受限 live/source discovery 边界内发现但无法映射 logical ID 的物理对象，可以先保留 opaque observed identity 与 stage evidence；它不自动取得 logical identity、managed classification、删除授权或 source authority。07B 已固定其 control/integrity 分类规则：缺少正向 owner evidence 时为 `unknown-owner`，不得按路径或内容猜测。
- 内容与敏感边界：stage inventory 保存 identity、state、revision/digest 和 provenance reference，不复制完整 payload/render/live 内容。需要精确审阅时通过按 ID diff/explain 读取允许的 stage 视图；binding、observation、work 与 secret 字段始终服从 04D、06C 的驻留和 safe-view 规则。
- Effective 隔离：Later effective evidence 使用独立 schema/namespace，并以 target、logical asset/subresource、consumer version、probe identity 关联 v1 stage record；缺失 effective evidence 只表示 effective `not_observed/unknown`，不能否定已经由 v1 stage evidence 证明的配置一致，也不能被包装成 runtime success 或让 runtime observation 改写 source、resolved、rendered、live。
- `Must`：source/resolved/rendered/live 四阶段；binding/observation 分栏；logical asset/subresource 粒度；直接上游 lineage；absence/block 作为显式 record；bounded discovery；live≠effective；stage snapshot 无 authority；06C safe view 与 04D residency 全程生效。
- `Later`：DEC-11 effective evidence set、按需增加 item-level probe 与更细性能统计；只有稳定 logical identity 和明确收益时才增加粒度，不预建全 host snapshot。
- `Out`：仅 source/live 两端清单、全磁盘/进程/package/cache 快照、原始内容复制仓、以 path/mtime/line 作为 logical identity、把 live/effective 反推为 source、把 effective 作为 v1 gate、跨机 inventory 汇总，以及因发现物理对象自动 adopt/delete。
- 接受的代价：每个 adapter 必须同时产出 stage mapping、semantic digest 与 lineage，inventory 数量会大于两端 diff；blocked/missing 也需要显式记录。以此换取 Agent 能直接定位差异发生在哪个配置阶段，而不用把一次 live mismatch 重新人工拆成 source、binding、render 与写入四轮排查。
- 后果：07B 已固定各 stage 的 control/integrity 分类且不改变 identity；07C 为 observation/evidence 增加信任等级、时间与 freshness；07D 表达 bounded discovery、权限和 partial snapshot；DEC-08 固定 rendered/live mapping；DEC-09B 固定被批准 plan 使用的 stage snapshot 与 adapter versions；DEC-12A 选择要比较的 stage edges；DEC-16 通过 record ID 串起 source→live provenance，Later 再关联 DEC-11 effective evidence。
- 验收断言：相同固定 source/binding/adapter/target 输入产生相同 source/resolved/rendered inventory；live 读取只发生在声明边界；任一 stage 缺失或阻断都有显式断点而非从报告消失；live present/parsed 不会被写成 runtime loaded/enabled；unmapped 物理对象不被自动接纳；secret/work 信息不因进入 snapshot 扩大披露或驻留范围；Later effective evidence 可关联但不能改变 v1 stage truth。

#### 07B 已拍板：Control ownership 与 integrity 正交分类

本轴决定 inventory record 如何表达“谁有控制权”与“阶段链是否完整”。`external-owned` 取代容易误解的 `unmanaged`：它表示有正向证据证明另一个系统负责，而不是“没人管”。`unknown-owner` 则表示现有证据无法证明 Almagest 或任何外部 owner，属于 fail-closed 的认知状态。

| 选项 | 分类模型 | 结论 |
|---|---|---|
| A：单一状态枚举 | 每个 record 只能标 managed、external-owned、unknown-owner、orphan 或 duplicate 之一 | 拒绝：ownership 与完整性互相覆盖，无法表达 `managed + orphan`、`external-owned + duplicate` 等真实组合 |
| B：正交 control + integrity | control state 独立表达管理归属，integrity object 独立表达 link 与 cardinality | **已选择** |
| C：Source inventory 二分 | source 登记即 managed，其余一律 external-owned | 拒绝：把“没有 Almagest 记录”误当成“外部 owner 已知”，掩盖手工副本、旧迁移残留与 provenance 丢失 |
| D：启发式归属与自动归并 | 根据 path、name、content digest 或相似度推断 owner，并自动 adopt/deduplicate | 拒绝：把推测升级为 authority，可能覆盖或删除 principal 仍需要的配置 |

```text
classification
├── control_state
│   ├── managed
│   ├── external-owned
│   └── unknown-owner
└── integrity
    ├── link_state: linked | orphan
    └── cardinality_state: unique | duplicate
```

| Classification | 必要条件 | Almagest 权限 |
|---|---|---|
| `managed` | 当前 record 存在可验证的 Almagest ownership claim：合法 authored source/registry entry，或固定 plan/apply/receipt evidence 证明该 identity 属于受管边界；direct upstream 是否完整由 `link_state` 另行表达 | 仅表示资源属于受管边界；任何实际写入仍必须满足 DEC-03D 与 DEC-09/10，不因 managed 自动可改 |
| `external-owned` | 正向 evidence 指向明确外部 owner/contract，例如 consumer/vendor bundled surface、plugin/package manifest 或明确声明的外部生成边界 | 只读 inventory；Almagest 无 adopt、rewrite、move、deduplicate 或 delete 权限 |
| `unknown-owner` | 无法建立 managed provenance，也没有足够正向证据证明 external owner，或证据互相冲突/已失效 | 只读且 fail closed；任何可能覆盖、移动、接纳或删除该 record 的动作阻断并交给 principal |
| `linked` | 当前 record 对其 stage 具有且仅具有一条合法直接上游关系，或已声明的 stage root relation | 不表示内容一致或 effective，只表示 lineage 关系完整 |
| `orphan` | 一个 observed record 实际存在，但当前 snapshot 无法建立合法直接上游关系；ownership 仍由 `control_state` 独立判断。expected record 缺失仍使用 07A `presence=absent`，不滥用 orphan | 不自动删除或接纳；保留 observed identity/evidence 并要求显式处置 |
| `unique` | 当前 stage/target identity 与独占 physical slot 至多有一个 claimant | 不表示 claimant 获得 authority |
| `duplicate` | 两个或更多 records 声称同一 stage/target logical identity，或占用 schema 声明必须独占的 physical slot | 不自动选 winner、shadow、merge 或删除；08A/09 决定影响与处置 plan |

- 决定（v0.1，2026-07-17，approver: principal）：07B 选择 **B——control ownership 与 integrity 正交分类**，并将 active model 中的 `unmanaged` 更名为 `external-owned`。每个 inventory stage/fact record 必须有一个 `control_state`，以及由 `link_state`、`cardinality_state` 组成的 integrity object。
- Managed proof：source record 只有属于 03A/05D 合法 authority inventory 才是 managed；binding record 只有属于 06B typed registry 才是 managed；resolved/rendered/live 必须有固定 plan/apply/receipt evidence 证明当前 identity 来自 managed inputs 和固定 adapter/version。若 ownership evidence 仍有效、但当前 snapshot 缺少直接上游关系，可表达为 `managed + orphan`；路径位于 consumer config root、内容与 managed asset 相同、名称相同或曾经被 Almagest 写过，单独都不足以证明当前 managed。
- External proof：`external-owned` 必须有可引用的外部 owner identity 与 ownership evidence。Almagest source/provenance 缺失只能得出“非已证 managed”，不能直接得出 external-owned；证据不足、冲突或过期时降为 `unknown-owner`。证据类型、信任等级与 freshness 由 07C 固定。
- Integrity 独立：control 与 integrity 不互相推导。`managed + orphan` 可表示仍有 Almagest ownership evidence、但当前 source/derived lineage 已断开的残留；`external-owned + duplicate` 可表示明确外部 owner 的多个副本；`unknown-owner + orphan + duplicate` 可同时表达无 owner、无合法 link 且多份占位。
- Absence 边界：expected source/resolved/rendered/live 不存在时使用 07A stage record 的 `presence=absent` 与 reason；`orphan` 只标记“对象实际存在但没有合法当前直接上游关系”，防止把 missing 与 extra 混成同一种漂移。
- Classification 无 mutation authority：managed 只是进入受管 plan 的必要条件，不是批准；external-owned/unknown-owner/orphan/duplicate 的发现均不授权自动 adopt、修改、移动、winner selection、deduplicate 或删除。任何处置必须由 operator Agent 报告并由 principal 选择合法 source/registry change、外部 owner 操作或 DEC-14 lifecycle plan。
- 影响边界：`external-owned` 非冲突记录可以保持只读可见；`unknown-owner`、orphan 或 duplicate 不自动使整台 host 失败，但任何会覆盖/删除它们、依赖其取得唯一 winner，或让它们 shadow/collide managed desired state 的 target action 必须阻断。具体 root precedence/shadow 由 08A，plan/block 表达由 09，写保护由 10A 决定。
- Adoption 边界：classification flag 不能被直接改成 managed。principal 决定接纳后，Agent 必须把内容写入合法 GitHub 或 Mac-local source，或创建合法 host-local binding，形成新 revision 和 DEC-03D plan；重新 inventory 后由新 provenance 自然得到 managed。Almagest 不从 live/external object 反向吸收内容。
- `Must`：`managed/external-owned/unknown-owner` 三态；external-owned 正向证据；unknown 默认 fail closed；integrity 的 link/cardinality 分离；absence≠orphan；classification 不授权 mutation；adopt 必须修合法 source/registry 并重新 inventory。
- `Later`：更多明确 external owner adapter、批量 classification explain 和 DEC-14 lifecycle ergonomics；不得增加 path/name/content heuristic authority。
- `Out`：`unmanaged` 作为 active 状态、单一扁平枚举、absence 即 external-owned、路径/root 即 owner、内容相同即 managed、启发式 owner 推断、自动 adopt/deduplicate/delete、classification 直接翻转为 managed，以及让 external/live state 反向成为 authored source。
- 接受的代价：每条 stage record 要保存 control、link、cardinality 与 evidence reference，external owner adapter 也需要明确合同；来源不明对象会持续阻断相关写入，直到 principal 处置。以此换取“已知外部负责”不会和“完全不知道是谁的”混在一起，Almagest 也不会因为发现文件就获得修改权。
- 后果：07C 必须给 managed/external proof 标注 evidence type、confidence 与 freshness，并在证据失效时重新分类；07D 对不可访问区域只能产出 partial/unknown，不得批量 external-owned；08A 使用 duplicate records 计算 root winner/shadow 但不改变 control；09/10 对 external-owned、unknown-owner、orphan、duplicate 生成保护性 block；12 区分 managed drift、external collision 与 unknown-owner risk；14A 定义 principal 主导的 adopt/remove lifecycle；16 按 classification evidence 解释归属与处置历史。
- 验收断言：同一 record 可同时表达 control 与 integrity；缺少 Almagest provenance 但也无 external proof 时必为 unknown-owner；明确系统内置资产可为 external-owned；实际存在但无 link 的对象为 orphan，expected missing 仍为 absent；duplicate 不自动产生 winner；任一非 managed 对象不会因 path/name/digest 相似而被 adopt、覆盖或删除；principal 接纳后必须先形成合法 source/registry revision，再经新 snapshot 变为 managed。

### DEC-08 Consumer 可见与渲染

- 状态：待给方案
- 依赖：DEC-02、DEC-05、DEC-07。
- 决策轴：
  - 08A：每个 consumer 的多 root、precedence、shared root、duplicate 和 shadow 如何建模。
  - 08B：raw source 是否保持不变；Codex/Qoder/Claude 如何生成不同 derived artifact。
  - 08C：frontmatter key 如何保留、删除或翻译；如何评估 token/触发语义影响和审批 lossy transform。
  - 08D：MCP JSON/TOML、instructions import/拼接、settings 等 consumer 格式如何映射并保留 provenance/hash。
- 初步验收：能按声明的 roots/precedence 静态计算每个 consumer 的预期可见集合；同名项的 winner/shadow 可解释；派生差异可审阅、可复现、不反写 raw source。runtime 是否实际加载由 DEC-11 的 Later 证据确认。

### DEC-09 变更预演

- 状态：待给方案
- 依赖：DEC-03—DEC-08。
- 决策轴：
  - 09A：canonical plan schema 是否完整覆盖 add/remove/change/shadow/block/no-op、原因链、稳定诊断码和可执行 resolution action。
  - 09B：是否固定所有 source revision/digest、policy、renderer/adapter 版本和 target inventory snapshot。
  - 09C：如何按 host/consumer/source class 生成紧凑的“多、少、变、shadow、block”摘要，并允许 operator Agent 按 ID 获取完整 diff/provenance/explain。
  - 09D：plan identity/hash、approval artifact、principal approver 与 operator Agent 身份、审批粒度、有效期和输入变化后的失效规则。
- 初步验收：operator Agent 不解析易变 prose 就能确定状态、风险、下一动作和所需批准，并能按 ID 深挖证据；未进入获批 plan 或输入已变化的动作不能执行。

### DEC-10 安全实施

- 状态：待给方案
- 依赖：DEC-09。这里只约束受管配置资源的 apply，不承担整机事务、binary/plugin package 安装或进程恢复。
- 决策轴：
  - 10A：resource ownership 与非纳管资产保护边界。
  - 10B：apply 如何验证 operator Agent 提交的 approval artifact 确实绑定 principal 决定、获批 plan/hash 及固定输入，并证明执行完全等价。
  - 10C：事务/原子边界、并发锁、幂等和重复执行语义。
  - 10D：备份、rollback、部分失败状态、恢复，以及 operator Agent 告警后由 principal 现场裁决的接管路径。
- 初步验收：operator Agent 可通过非交互机器接口执行精确获批计划；不会静默删除 `external-owned`、`unknown-owner`、orphan 或 duplicate 资产；部分失败以稳定状态/诊断码返回，并有确定恢复动作。

### DEC-11 Effective 验证（Later）

- 状态：待给方案；已由 DEC-01A 确认为 Later，不作为 v1 gate
- 依赖：DEC-07、DEC-08、DEC-10。
- 决策轴：
  - 11A：每个 asset/consumer 需要达到 present、parsed/registered、discoverable/enabled、callable、observed-used 中哪一级。
  - 11B：各 consumer 使用原生命令、受控探针、行为测试还是推断；每种方法的信任等级。
  - 11C：没有 runtime API、consumer 离线或权限不足时如何降级为 inferred/unknown。
  - 11D：probe 与 consumer version 如何绑定，证据何时过期。
- 初步验收：Codex/Qoder/Claude 的结果标注实际证据级别；低等级证据不会被包装成更高等级成功。

### DEC-12 漂移检查

- 状态：待给方案
- 依赖：v1 的 source→live/binding drift 依赖 DEC-07—DEC-10；Later 的 effective/runtime drift 另依赖 DEC-11。
- 决策轴：
  - 12A：v1 在 source/resolved/rendered/live/binding 之间比较哪些边；Later 是否追加 effective 边。
  - 12B：检查由 operator Agent、hook、定时任务还是外部 daemon 触发；稳定退出码、诊断码和结构化告警语义。Almagest 不负责 daemon 生命周期。
  - 12C：如何归因、分级、指派 owner；哪些漂移允许自动修，哪些必须由 operator Agent 告警并取得 principal 批准。
  - 12D：Later 如何把 consumer runtime 漂移与配置漂移区分并关联，不得反向改变 v1 成功口径。
- 初步验收：结构化报告指出差异层、责任 source、证据、风险和下一动作；operator Agent 可直接据此解释和重试；破坏性修复不会静默发生。

### DEC-13 跨机配置一致性（本地独立执行）

- 状态：待给方案
- 依赖：DEC-02—DEC-12。
- 决策轴：
  - 13A：每台机器如何由本机 operator Agent 独立完成 source sync、plan、apply 与 verify；04D 已排除中央控制端、远程执行和跨机报告。
  - 13B：配置/引用、policy、adapter 与 source revision 如何分发和锁定。
  - 13C：每台机器本地如何处理离线、配置/adapter 版本错位和 apply 失败重试；receipt 不上传，也不做跨机对比。
  - 13D：如何让每台机器只依赖本机 source/inventory/evidence 判断自己的 target 状态；Mac work 事实对 Windows 保持完全不可见。
- 初步验收：Mac 与 Windows 各自通过本机 Agent 判断并达到正确 target 状态，不需要中央端、receipt 上传或另一台机器的状态。

### DEC-14 配置资产生命周期

- 状态：待给方案
- 依赖：DEC-01—DEC-13。
- 决策轴：
  - 14A：首次 bootstrap、现状 import，以及 `external-owned`/`unknown-owner` 的 adopt/remove 状态机。
  - 14B：schema、policy、renderer/adapter 与 consumer version 升级如何迁移。
  - 14C：asset deprecate、remove/mask、target 配置退役与历史 receipt 如何处理。
  - 14D：host 重装后如何重建目标配置、配置灾难恢复、回退旧配置版本，以及 Later 的 effective evidence 是否需要重建；不管理 host 重装本身。
- 初步验收：全新配置、已有脏状态、配置 schema/adapter 升级和配置恢复场景都有 dry-run、停止条件、回滚或恢复路径。

### DEC-15 Consumer 兼容与扩展

- 状态：待给方案
- 依赖：DEC-07—DEC-14。
- 决策轴：
  - 15A：consumer capability manifest 至少声明哪些 roots、formats、precedence、scope 与限制；runtime probe 作为 Later capability 单独声明。
  - 15B：新增 consumer 使用数据声明、adapter/plugin 还是核心改动；这里只拍能力契约，不先锁定机制。
  - 15C：v1 如何测试跨 OS fixture、round-trip、lossy transform 和配置兼容版本矩阵；Later 如何追加 runtime evidence fixture。
  - 15D：consumer 行为变化时如何探测 incompatibility、阻断投影和升级契约。
- 初步验收：新增 consumer 的影响面和证据要求明确；未声明能力或不兼容版本 fail closed。

### DEC-16 审计与可解释性

- 状态：待给方案
- 依赖：DEC-01—DEC-15。
- 决策轴：
  - 16A：audit/receipt 如何分别保存 principal approver、operator Agent、time、source/digest、policy、plan、target、action、result 和 evidence。
  - 16B：记录存在哪里、保留多久、如何脱敏和防篡改。
  - 16C：v1 的机器可读 explain 如何通过稳定 ID/诊断码回答 identity、provenance、shadow、block 和 config/binding drift，并以紧凑摘要 + 按需详情控制 Agent 上下文成本；Later 如何追加 runtime failure/evidence。
  - 16D：每台机器本地如何处理离线 receipt、schema 升级和审计记录自身生命周期；04D 已排除跨机聚合。
- 初步验收：operator Agent 能通过稳定 schema 回答“哪位 principal 在何时批准、哪个 Agent 基于哪个固定输入/plan，把什么投影到哪个 target，结果为何生效或失败”，无需抓取人类界面文本。

## 需求追踪矩阵

| 用户成功口径 | 主责任卡 | 需覆盖对象 | 最终证据 |
|---|---|---|---|
| principal 通过 AI Agent 操作，机器合同稳定且所有配置写动作保留人工拍板 | DEC-03D、DEC-09、DEC-10、DEC-12、DEC-16 | principal、operator Agent、Almagest、consumer 四种角色 | machine contract fixture + approval/receipt golden case |
| target 应有资产及其 authority/overlay | DEC-01—DEC-06 | 13 个受管配置域、6 类绑定/依赖观测事实；四个已知 consumer | capability spec assertion + fixture |
| apply 前完整说明变化与原因 | DEC-07—DEC-10 | 每个 host/consumer/source class | plan contract + golden plan |
| v1 apply 后证明 live 配置与 active binding 正确 | DEC-07—DEC-10、DEC-12 | Mac Codex/Qoder；Windows Codex/Claude | config/binding inventory + drift fixture |
| Later 证明 consumer 实际消费并定位 runtime drift | DEC-11、DEC-12 | 启用 runtime evidence 的 consumer/asset | 分级 runtime probe + failure fixture |
| 防止 work-local 驻留/投影、public/private 越界 | DEC-02—DEC-06、DEC-09—DEC-13 | 正向与负向投影场景 | policy denial + receipt |

DEC-01A—01C 已补齐资产范围、identity、version/derivation/conflict 关系。DEC-02 与 DEC-11 拍板后必须把四个 consumer 的确切产品/版本/target/probe 填入矩阵。上游卡重开时，矩阵用于列出受影响卡和证据。

## RAID 台账

| ID | 类型 | 状态 | 影响 | 问题 / 假设 | Owner | 缓解或退出条件 | 处理点 |
|---|---|---|---|---|---|---|---|
| A-01 | Assumption | resolved | high | Mac 是否需要 personal/work 两个 consumer context | principal | 2026-07-16 确认不需要；每个 Mac consumer 一个 target，effective config 为 GitHub base + work-local overlay | DEC-02、DEC-04 |
| A-02 | Assumption | resolved | high | shared 与 work 配置是否为两份完整配置或 overlay | principal | 2026-07-16 确认 GitHub personal/shared base 两机消费，Mac-local work 只作增量 overlay | DEC-02—DEC-05 |
| A-03 | Assumption | resolved | high | 谁直接操作 Almagest，principal 是否需要面向人的 CLI/TUI | principal | 2026-07-16 确认 principal 通过自然语言指挥 AI Agent；2026-07-17 DEC-03D 进一步确认任何非 `no-op` 配置写计划都由 Agent 报警并交 principal 实时批准 | 全局；DEC-03D、DEC-09、DEC-10、DEC-12、DEC-16 |
| R-01 | Risk | open | critical | work-local payload 可能经 GitHub、Windows cache/render、plan/receipt 或 live projection 泄漏 | Codex | 独立 source root + 全链路 negative fixture；Almagest 管理面内 fail closed，不以 `.gitignore` 作为安全边界 | DEC-02、DEC-04、DEC-06、DEC-09、DEC-13 |
| R-02 | Risk | open | medium | Later：vendor 无 runtime probe，文件正确却无法证明 consumer 生效 | Codex | 使用 evidence ladder；最高只报 inferred/unknown；不阻塞 v1 配置闭环 | DEC-11 |
| I-01 | Issue | open | high | QoderCLI 的真实 roots、precedence、frontmatter、profile 未完整取证；runtime inventory 属 Later | Codex | v1 固定产品版本并取得 roots/precedence 实机证据；Later 再补 probe | DEC-08、DEC-11 |
| I-02 | Issue | open | high | Mac/Windows Codex 的真实 roots、precedence、profile 未完整取证；runtime probe 属 Later | Codex | v1 分 OS/版本取得配置证据；Later 再补 probe | DEC-02、DEC-08、DEC-11 |
| I-03 | Issue | open | high | Windows “Claude” 的具体产品、版本、roots、profile 未确认；runtime probe 属 Later | principal + Codex | principal 确认产品；Codex 在 DEC-08 前完成 v1 配置取证 | DEC-08、DEC-11 |
| D-01 | Dependency | open | medium | consumer roots/格式及 Later runtime 行为依赖外部产品版本 | Codex | 分开建立 config capability matrix 与 Later runtime fixture；指定复核触发条件 | DEC-08、DEC-11、DEC-15 |
| S-01 | Scope | resolved | high | v1 是否超出 skill，纳入 MCP、instructions、settings 等 | principal | 2026-07-16 DEC-01A v0.3 选择 B：13 个 user-authored 配置域纳管，6 类绑定/依赖事实观测；runtime/host 生命周期不接管 | DEC-01 |

最终验收时，Assumption 必须已验证或转成显式约束；Risk 必须已接受或缓解；Issue 必须关闭或转单；Dependency 必须有 owner、版本边界和复核条件。

## 不做范围

- 本文不决定 Almagest 继续、改造或退役。
- 本文不选择 gaal、`npx skills`、chezmoi 或任一具体 executor。
- 本文不预设两份独立配置、编译期生成还是 runtime merge。
- 本文不预设文件格式、存储位置、控制端拓扑或 adapter/plugin 架构。
- v1 不建设面向 principal 的 TUI、wizard 或 dashboard；未来 UI 只能作为 canonical machine contract 的客户端。
- 本文不修改 live 配置，不迁移 skill，不注册 MCP，不建立后台服务。
- 本文不把 gaal 的已有数据模型或 Almagest 当前实现直接当作目标模型。

## 后续产物

1. 16 项全部拍板后，从本工作台蒸馏 capability spec、acceptance matrix 和必要 ADR。
2. 方向性结论进入 `docs/decisions/`，稳定约束进入 contract/spec；确认引用闭合后删除本 living design，保留不可变 capture 与 Git 历史。
3. 再建立“能力 → gaal / `npx skills` / Agent 原生 / Almagest 自建”的实现归属矩阵，供 principal 决定继续建设、改造或退役。
4. 实现、迁移和发布分别建立新 PM issue，不复用本设计 issue 承载执行。
