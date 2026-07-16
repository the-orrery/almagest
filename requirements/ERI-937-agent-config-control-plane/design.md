# Agent 配置控制面能力拍板工作台

## 文档契约

| 项 | 约定 |
|---|---|
| 读者动作 | principal 按依赖顺序逐项选择能力语义；Codex 负责澄清、生成真实候选、说明推荐与代价，并把结果写回 |
| 生命周期 | `capture/` 是不可变诉求快照；本文在能力拍板和蒸馏期间持续更新，结论进入 ADR/spec 后删除本文，不保留待维护的提案副本 |
| 交付形态 | living decision workbench；它不是当前架构真相，也不是实现计划 |
| 证据规则 | 每个决策轴必须包含范围、候选、推荐理由、principal 明示决定、被拒选项、后果、依赖影响和可验证断言 |
| Gate | 诉求不清时先澄清；上游项未定不得偷跑下游实现；能力契约稳定前不做 build/buy/retire 选择 |

语域：中性、精确、可审计。本合同先定义“需要什么能力”，不预设由 Almagest、gaal、`npx skills`、Agent 原生能力或新组件承载。Almagest 当前只是候选承载者和本需求包所在的代码仓。

## 目标与成功口径

Agent 配置控制面应能对任意**已声明 target** 回答以下问题；target 的候选维度包括 host、OS、consumer、consumer version、profile、workspace 和 lane，最终键由 DEC-02 决定：

1. 目标应当拥有哪些资产，来自哪个权威 source 和 overlay；
2. apply 前会 add/remove/change/shadow/block 什么，为什么；
3. apply 后 live 状态与 consumer 实际消费状态是否符合目标；
4. 发生漂移时，差异来自 source、resolve、render、projection、live 还是 consumer runtime；
5. personal/work 或 public/private 边界是否被违反。

当前阶段采用“配置一致优先”：v1 先保证每个 target 的 declared → resolved → rendered → live 配置与其目标状态一致，并能在 apply 前报告差异、apply 后检查漂移。“一致”不是要求 Mac/Windows 或 personal/work 配置字节相同，而是各自 live 状态符合各自 overlay 后的目标。

这里必须区分三种对象，不能再用“配置/运行时”二分法一刀切：

1. **受管配置**：人有意声明、会改变 Agent 行为或能力面的 desired state；v1 负责解析、渲染、投影和漂移检查。
2. **绑定与依赖观测**：不由 v1 安装或维护，但会决定哪个配置被消费、或该配置能否成立的事实；v1 必须盘点并参与 plan/verify，不能当成无关主机环境。
3. **运行态与生成状态**：进程、执行结果、缓存、会话等；不属于 v1 配置一致性承诺，后续另行决定是否治理。

因此，“不负责安装/运行”不等于“不看”。例如 v1 不升级 Codex binary，但必须知道 consumer 产品、版本、路径和配置 schema；不管理整个 shell，但若 wrapper、alias、启动参数或环境变量选择了 `CODEX_HOME`、profile、lane 或 settings source，就必须纳入受管配置或绑定观测。

## 已知目标拓扑

| Host | OS | Consumer | 已知 lane | 仍需取证 |
|---|---|---|---|---|
| Mac | macOS | Codex | personal + work | 产品版本、roots、precedence、profile、runtime probe；两条 lane 是否共享 global root |
| Mac | macOS | QoderCLI | personal + work | 产品版本、多 roots、precedence、profile、frontmatter、runtime probe |
| Windows | Windows | Codex | personal | 产品版本、roots、precedence、profile、runtime probe |
| Windows | Windows | Claude，具体产品待确认 | personal | Claude Code/Desktop/其它、产品版本、roots、precedence、profile、runtime probe |

这张表只记录已知消费范围。“文件写到了某个目录”不等于 consumer 已加载，也不证明 lane 隔离成立。

## 关键术语

| 术语 | 工作定义 |
|---|---|
| asset | 被治理的 skill、MCP、instructions、settings、hook、plugin 等能力单元；确切范围由 DEC-01 决定 |
| consumer | 消费配置的具体 Agent 产品及版本，例如 Codex、QoderCLI、Claude Code |
| source | 对声明内容拥有权威性的来源；cache、rendered artifact 和 live target 默认不是 source |
| root | consumer 会搜索或读取的物理目录/配置入口，一个 consumer 可以有多个 root |
| target | 一次策略解析、渲染和投影的目标上下文；最终 identity 由 DEC-02 决定 |
| profile | 同一 consumer 的一组显式运行配置；与 personal/work lane 是独立维度 |
| lane | personal/work 这类并列的消费与策略域，不表示高低层级 |
| layer | 可参与组合的声明片段，例如 public base、private、lane、host、consumer、local overlay |
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
| DEC-04 | Lane 与投影策略 | personal/work 如何继承、允许、阻断和例外 | projection policy 与防误投影约束 |
| DEC-05 | Overlay 与解析 | 各 layer 及各类 asset 如何合成、删除和冲突 | 确定性 resolved desired state |
| DEC-06 | Secret 与本地参数 | secret、路径、账号和 host 差异放哪里 | 不泄漏且可移植的 local-value contract |
| DEC-07 | Inventory | source、resolved、rendered、live、effective 各盘点什么 | 有证据边界的全状态清单 |
| DEC-08 | Consumer 可见与渲染 | 多 root、shadow、frontmatter、格式转换后 consumer 看见什么 | per-consumer visibility/render contract |
| DEC-09 | 变更预演 | apply 前必须报告并固定哪些差异、输入和风险 | 可审批且可复现的 plan contract |
| DEC-10 | 安全实施 | ownership、计划等价、原子性、幂等、备份和恢复怎么做 | apply safety contract |
| DEC-11 | Effective 验证 | 如何分级证明 Codex/Qoder/Claude 真正加载或使用 | runtime evidence contract |
| DEC-12 | 漂移检查 | 查什么、何时查、谁负责、何时自动修 | drift/reconcile policy |
| DEC-13 | 跨机协调 | 分发、离线、版本错位、receipt、汇总如何工作 | fleet coordination contract |
| DEC-14 | 生命周期 | bootstrap、import、迁移、升级、废弃和恢复怎么走 | lifecycle state machine |
| DEC-15 | Consumer 兼容与扩展 | 新 consumer/root/格式如何描述、接入和测试 | compatibility/extension contract |
| DEC-16 | 审计与可解释性 | 谁在何时把什么从哪里投影到哪里，为什么生效 | audit/receipt/explain contract |

## 决策卡

所有卡片进入讨论时都要补：`Must/Later/Out`、候选、推荐、decision version/date、principal 决定、被拒选项、理由、后果、依赖影响和最终验收。

### DEC-01 资产范围与身份

- 状态：01A 需重开；01B、01C 待给方案
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
| wrapper | 在真正 binary 前设置参数、环境变量、profile、代理或工作目录的脚本/启动器 | 若决定配置 root、profile、lane 或 settings source，则 wrapper 声明属于受管配置；其解析结果必须观测。与 Agent 无关的通用 wrapper 才是 `Out` |
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
| 权限与安全策略 | approval、sandbox、filesystem/network permission、tool allow/deny、trust、managed policy/requirements | 受管配置；不得被 local overlay 绕过 |
| Profiles、scope 与层级 | user/project/local/managed scope、profile、lane、workspace/project layer、settings source、precedence、overlay 与 CLI/config override policy | 受管配置；实际启动选择结果必须观测 |
| Hooks | 事件、matcher、顺序、类型、timeout、command/prompt/agent/http/MCP target，以及受管 hook script 内容 | 受管配置；是否执行、退出码和副作用属于 Later |
| Plugins、extensions 与 marketplace | manifest、source/ref/version constraint、marketplace/registry、enabled state、override、plugin 所带 skills/agents/hooks/MCP/apps/LSP/bin 声明 | 受管配置；实际安装包、cache、依赖安装和运行健康只观测或 Later |
| 自定义 agents/subagents | role、description、instructions、model、tools/MCP、skills、permissions、sandbox、并发/深度限制 | 受管配置 |
| Commands、prompts 与输出交互 | custom commands/prompts、output styles、status line、notification command；已废弃 surface 仍需 inventory/migrate | 是否全部纳入仍需拍板；它们确实会改变 Agent 交互或调用入口，不能漏列 |
| Agent 客户端偏好 | CLI/TUI/IDE language、theme、layout、更新频道、遥测、索引等 user-authored settings | 是否纳入仍需拍板；需要区分 Agent 行为配置与纯 UI 偏好 |
| Secret 与本地参数 | token、OAuth 状态、账号、credential store、绝对路径、machine ID、proxy/local endpoint | 只受管 schema、reference、required/optional 和本地绑定；不跨 lane/host 复制 secret value |
| 控制面元数据 | asset identity、source authority、digest/revision、adapter/schema version、ownership、lock、policy 与 receipt | Almagest 自身必须受管，否则无法解释或重现配置 |

#### 必须观测但不由 v1 安装维护

| 观测对象 | 为什么不能遗漏 |
|---|---|
| consumer 产品、版本、binary path、配置 schema/capability | 同一文件在不同产品/版本中可能含义不同，甚至不被识别 |
| 实际 config root、home、active profile/lane/workspace、project trust | 决定加载哪一层配置 |
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

#### 01A v0.3 待拍板候选

| 候选 | 范围 | 主要代价 |
|---|---|---|
| A：核心行为配置 | instructions、skills、MCP、模型/权限 settings、hooks、plugins、agents | 仍会漏掉 profile/root/override、启动绑定、commands/UX 等导致的有效配置差异 |
| B：全部 user-authored Agent 配置 + 绑定观测 | 纳入上面全量候选清单；管理配置声明，观测 binary/安装包/依赖和启动绑定，不管理其生命周期 | adapter 和 inventory 范围更大；必须把“managed / observed / generated”标清 |
| C：Agent runtime fleet | B + binary/plugin/依赖安装、进程、执行健康、自动恢复 | 重新进入此前否决的运行平台范围，明显超出“先保证配置一致” |

- 当前推荐：**B**。它修复漏项但不扩成 host/runtime manager；核心原则是“所有 user-authored Agent 配置都列入，所有决定配置消费结果的绑定都观测，所有生成状态与生命周期都不接管”。
- B 的边界示例：系统证明“目标声明启用 plugin X、当前安装版本为 V、注册 hook Y、active profile 为 P，live 配置与声明一致”；它不承诺安装 X、启动相关进程或证明 Y 已成功执行业务逻辑。
- 重开影响：只有 DEC-01A；DEC-01B/01C 尚未拍板，无需撤销下游决定。DEC-02、DEC-06—DEC-12 的候选生成必须使用修正后的三类对象。
- 初步验收：系统能枚举每个 target 的 user-authored 配置、绑定输入和生成状态并明确分类；任何 active root/profile/override 未知时不得报告“无漂移”；每个纳入类型都有 identity、version、overlay、render 和 ownership 规则。

### DEC-02 目标拓扑与隔离能力

- 状态：待给方案
- 依赖：DEC-01。
- 决策轴：
  - 02A：target key 包含哪些维度：host、OS、consumer/version、profile、workspace、lane。
  - 02B：profile、workspace 与 lane 哪些是一等隔离边界，哪些只是 selector。
  - 02C：如何声明 target/consumer 的实际能力；所需隔离无法承载时是 `unsupported`、`block` 还是允许显式降级。
- 初步验收：四个已知消费者都能映射到无歧义 target；共享 global root 无法满足隔离时不会伪称成功。

### DEC-03 权威来源与信任

- 状态：待给方案
- 依赖：DEC-01、DEC-02。
- 决策轴：
  - 03A：public、private、work-only、本机声明和外部 registry 各自能声明什么，ownership 如何分配。
  - 03B：冲突时按字段/资产由谁裁决；cache、rendered 和 live 如何禁止反客为主。
  - 03C：外部 source、浮动 revision、签名/digest、allowlist 和更新策略如何受信。
  - 03D：skill、hook、MCP 等可执行或可调用内容如何分级风险并获批。
- 初步验收：每个 resolved asset 能追溯到唯一 authority 和不可歧义的输入 revision/digest；不可信输入 fail closed。

### DEC-04 Lane 与投影策略

- 状态：待给方案
- 依赖：DEC-02、DEC-03。
- 决策轴：
  - 04A：personal/work 是标签、继承域、并集还是强策略隔离域。
  - 04B：Mac 同时消费两条 lane 时采用 union、独立 profile/root，还是按 consumer 能力选择。
  - 04C：默认 allow/deny、跨 lane 继承、例外授权和 work-only 防误投影如何定义。
  - 04D：物理 root/profile 不支持隔离时的停止条件与迁移要求。
- 初步验收：work-only asset 投影到 Windows/personal 必须 `block`；任何例外有显式授权和 receipt；共享 root 不能制造虚假隔离。

### DEC-05 Overlay 与解析

- 状态：待给方案
- 依赖：DEC-01—DEC-04。
- 决策轴：
  - 05A：public base、private、lane、host、consumer、local layer 的顺序和适用范围。
  - 05B：每种纳入 asset 的 merge algebra：skill 的集合/目录、MCP/settings 的键或字段、instructions 的 import/拼接、hooks 的有序列表等。
  - 05C：add、override、remove/mask、duplicate 和 conflict 的语义；哪些冲突按优先级，哪些必须阻断。
  - 05D：如何表达 `private-shared + work-only + host/consumer/local`；local overlay 不得绕过 lane policy 或 source trust。
- 初步验收：相同输入生成相同 resolved state；每个字段/资产可解释 provenance；所有纳入类型均有 merge/remove/conflict 规则。

### DEC-06 Secret 与本地参数

- 状态：待给方案
- 依赖：DEC-03—DEC-05。
- 决策轴：
  - 06A：secret value/reference、本机绝对路径、账号、OS/host 参数如何分类。
  - 06B：各类值存在哪里、由谁提供、哪些 layer 允许覆盖。
  - 06C：plan、diff、receipt、日志和错误信息如何脱敏。
  - 06D：缺值、引用失效或权限不足时如何 fail closed 并诊断。
- 初步验收：portable source、rendered artifact 和 receipt 不泄漏 secret；本机路径不会误投影到其它 host。

### DEC-07 Inventory

- 状态：待给方案
- 依赖：DEC-01—DEC-06。
- 决策轴：
  - 07A：source、resolved、rendered、live、effective 哪些状态必须盘点。
  - 07B：如何标注 managed、unmanaged、orphan、duplicate、unknown-owner。
  - 07C：如何标注 observed、inferred、unknown，以及采集时间、版本和证据来源。
  - 07D：发现边界、权限不足、不可访问 host 与部分结果如何表达。
- 初步验收：报告不把“文件存在”写成“consumer 已加载”；非纳管资产可被发现但不会因此自动取得删除授权。

### DEC-08 Consumer 可见与渲染

- 状态：待给方案
- 依赖：DEC-02、DEC-05、DEC-07。
- 决策轴：
  - 08A：每个 consumer 的多 root、precedence、shared root、duplicate 和 shadow 如何建模。
  - 08B：raw source 是否保持不变；Codex/Qoder/Claude 如何生成不同 derived artifact。
  - 08C：frontmatter key 如何保留、删除或翻译；如何评估 token/触发语义影响和审批 lossy transform。
  - 08D：MCP JSON/TOML、instructions import/拼接、settings 等 consumer 格式如何映射并保留 provenance/hash。
- 初步验收：能列出每个 consumer 最终可见集合；同名项的 winner/shadow 可解释；派生差异可审阅、可复现、不反写 raw source。

### DEC-09 变更预演

- 状态：待给方案
- 依赖：DEC-03—DEC-08。
- 决策轴：
  - 09A：plan 是否完整覆盖 add/remove/change/shadow/block/no-op 及原因链。
  - 09B：是否固定所有 source revision/digest、policy、renderer/adapter 版本和 target inventory snapshot。
  - 09C：如何按 host/consumer/lane 汇总“多、少、变、shadow、block”数量和风险。
  - 09D：plan identity/hash、审批粒度、有效期和输入变化后的失效规则。
- 初步验收：apply 前可回答每个消费者变化及原因；未进入获批 plan 或输入已变化的动作不能执行。

### DEC-10 安全实施

- 状态：待给方案
- 依赖：DEC-09。
- 决策轴：
  - 10A：resource ownership 与非纳管资产保护边界。
  - 10B：apply 如何证明与获批 plan/hash 及固定输入完全等价。
  - 10C：事务/原子边界、并发锁、幂等和重复执行语义。
  - 10D：备份、rollback、部分失败状态、恢复与人工接管。
- 初步验收：不会静默删除 unmanaged/unknown-owner 资产；部分失败可诊断且有确定恢复动作。

### DEC-11 Effective 验证

- 状态：待给方案
- 依赖：DEC-07、DEC-08、DEC-10。
- 决策轴：
  - 11A：每个 asset/consumer 需要达到 present、parsed/registered、discoverable/enabled、callable、observed-used 中哪一级。
  - 11B：各 consumer 使用原生命令、受控探针、行为测试还是推断；每种方法的信任等级。
  - 11C：没有 runtime API、consumer 离线或权限不足时如何降级为 inferred/unknown。
  - 11D：probe 与 consumer version 如何绑定，证据何时过期。
- 初步验收：Codex/Qoder/Claude 的结果标注实际证据级别；低等级证据不会被包装成更高等级成功。

### DEC-12 漂移检查

- 状态：待给方案
- 依赖：DEC-07—DEC-11。
- 决策轴：
  - 12A：source/resolved/rendered/live/effective 之间比较哪些边。
  - 12B：检查由手动、hook、定时任务还是 daemon 触发；退出码和告警语义。
  - 12C：如何归因、分级、指派 owner；哪些漂移允许自动修，哪些必须人工审批。
  - 12D：consumer runtime 漂移与文件漂移如何区分并关联。
- 初步验收：报告指出差异层、责任 source、证据、风险和下一动作；破坏性修复不会静默发生。

### DEC-13 跨机协调

- 状态：待给方案
- 依赖：DEC-02—DEC-12。
- 决策轴：
  - 13A：每台机器独立 pull+plan+apply，还是存在控制端；边界和信任如何划分。
  - 13B：配置/引用、policy、adapter 与 source revision 如何分发和锁定。
  - 13C：离线、版本错位、失败重试、receipt 上传和跨机对比如何处理。
  - 13D：汇总哪些元数据；如何避免把 private/work 内容带到错误 lane 或中央端。
- 初步验收：不暴露 private/work 内容也能判断 Mac 与 Windows 是否处于各自正确 target 状态。

### DEC-14 生命周期

- 状态：待给方案
- 依赖：DEC-01—DEC-13。
- 决策轴：
  - 14A：首次 bootstrap、现状 import、adopt/unmanaged 的状态机。
  - 14B：schema、policy、renderer/adapter 与 consumer version 升级如何迁移。
  - 14C：asset deprecate、remove/mask、host 退役与历史 receipt 如何处理。
  - 14D：host 重装、灾难恢复、回退旧版本和重建 effective evidence 如何走。
- 初步验收：全新、已有脏状态、升级和恢复场景都有 dry-run、停止条件、回滚或恢复路径。

### DEC-15 Consumer 兼容与扩展

- 状态：待给方案
- 依赖：DEC-07—DEC-14。
- 决策轴：
  - 15A：consumer capability manifest 至少声明哪些 roots、formats、precedence、scope、probe 与限制。
  - 15B：新增 consumer 使用数据声明、adapter/plugin 还是核心改动；这里只拍能力契约，不先锁定机制。
  - 15C：跨 OS fixture、round-trip、lossy transform、runtime evidence 和兼容版本矩阵如何测试。
  - 15D：consumer 行为变化时如何探测 incompatibility、阻断投影和升级契约。
- 初步验收：新增 consumer 的影响面和证据要求明确；未声明能力或不兼容版本 fail closed。

### DEC-16 审计与可解释性

- 状态：待给方案
- 依赖：DEC-01—DEC-15。
- 决策轴：
  - 16A：audit/receipt 保存哪些 actor、time、source/digest、policy、plan、target、action、result 和 evidence。
  - 16B：记录存在哪里、保留多久、如何脱敏和防篡改。
  - 16C：explain 如何回答 identity、provenance、shadow、block、drift 和 runtime failure。
  - 16D：跨机聚合、离线 receipt、schema 升级和审计记录自身生命周期如何处理。
- 初步验收：能回答“谁在何时基于哪个固定输入/plan，把什么投影到哪个 target，结果为何生效或失败”。

## 需求追踪矩阵

| 用户成功口径 | 主责任卡 | 需覆盖对象 | 最终证据 |
|---|---|---|---|
| target 应有资产及其 authority/overlay | DEC-01—DEC-06 | DEC-01 纳入的每种 asset；四个已知 consumer | capability spec assertion + fixture |
| apply 前完整说明变化与原因 | DEC-07—DEC-10 | 每个 host/consumer/lane | plan contract + golden plan |
| apply 后证明 live 与实际消费 | DEC-07、DEC-08、DEC-11 | Mac Codex/Qoder；Windows Codex/Claude | inventory + 分级 runtime probe |
| 定位 source 到 runtime 的漂移层 | DEC-07—DEC-12 | 每种状态边和 asset 类型 | drift matrix + failure fixture |
| 防止 personal/work、public/private 越界 | DEC-02—DEC-06、DEC-09—DEC-13 | 正向与负向投影场景 | policy denial + receipt |

DEC-01 拍板后必须把实际 asset 类型展开进矩阵；DEC-02 与 DEC-11 拍板后必须把四个 consumer 的确切产品/版本/target/probe 填入矩阵。上游卡重开时，矩阵用于列出受影响卡和证据。

## RAID 台账

| ID | 类型 | 状态 | 影响 | 问题 / 假设 | Owner | 缓解或退出条件 | 处理点 |
|---|---|---|---|---|---|---|---|
| A-01 | Assumption | open | high | Mac personal/work 可能在同一 Codex/Qoder global root 中形成 union | principal | DEC-02/04 明示隔离语义；实际 root 不支持时标记 unsupported/block | DEC-02、DEC-04 |
| A-02 | Assumption | open | high | private shared layer 可能同时进入 personal/work，也可能必须拆为 private-personal/private-work | principal | 明示 ownership、继承和禁止边 | DEC-03—DEC-05 |
| R-01 | Risk | open | critical | 共享 root 被误当强隔离，可能把 work-only 资产泄漏到 personal/Windows | Codex | 负例 fixture；能力不足时 fail closed；不得仅靠标签宣称隔离 | DEC-02、DEC-04、DEC-09 |
| R-02 | Risk | open | medium | vendor 无 runtime probe，文件正确却无法证明 consumer 生效 | Codex | 使用 evidence ladder；最高只报 inferred/unknown | DEC-11 |
| I-01 | Issue | open | high | QoderCLI 的真实 roots、precedence、frontmatter、profile 和 runtime inventory 未取证 | Codex | 固定产品版本并取得官方/实机证据 | DEC-08、DEC-11 前 |
| I-02 | Issue | open | high | Mac/Windows Codex 的真实 roots、precedence、profile 与 runtime probe 未完整取证 | Codex | 分 OS/版本取得官方/实机证据 | DEC-02、DEC-08、DEC-11 前 |
| I-03 | Issue | open | high | Windows “Claude” 的具体产品、版本、roots、profile 与 probe 未确认 | principal + Codex | principal 确认产品；Codex 完成取证 | DEC-02 前 |
| D-01 | Dependency | open | medium | consumer roots、格式和 runtime 行为依赖外部产品版本 | Codex | 建版本矩阵与 fixture；指定复核触发条件 | DEC-08、DEC-11、DEC-15 |
| S-01 | Scope | open | high | v1 是否超出 skill，纳入 MCP、instructions、settings 等 | principal | DEC-01 明示 Must/Later/Out | DEC-01 |

最终验收时，Assumption 必须已验证或转成显式约束；Risk 必须已接受或缓解；Issue 必须关闭或转单；Dependency 必须有 owner、版本边界和复核条件。

## 不做范围

- 本文不决定 Almagest 继续、改造或退役。
- 本文不选择 gaal、`npx skills`、chezmoi 或任一具体 executor。
- 本文不预设两份独立配置、编译期生成还是 runtime merge。
- 本文不预设文件格式、存储位置、控制端拓扑或 adapter/plugin 架构。
- 本文不修改 live 配置，不迁移 skill，不注册 MCP，不建立后台服务。
- 本文不把 gaal 的已有数据模型或 Almagest 当前实现直接当作目标模型。

## 后续产物

1. 16 项全部拍板后，从本工作台蒸馏 capability spec、acceptance matrix 和必要 ADR。
2. 方向性结论进入 `docs/decisions/`，稳定约束进入 contract/spec；确认引用闭合后删除本 living design，保留不可变 capture 与 Git 历史。
3. 再建立“能力 → gaal / `npx skills` / Agent 原生 / Almagest 自建”的实现归属矩阵，供 principal 决定继续建设、改造或退役。
4. 实现、迁移和发布分别建立新 PM issue，不复用本设计 issue 承载执行。
