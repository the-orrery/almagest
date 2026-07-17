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
| consumer | 消费配置的稳定 Agent 实例，例如 Codex、QoderCLI、Claude；具体产品版本是该实例的观测属性 |
| source | 对声明内容拥有权威性的来源；cache、rendered artifact 和 live target 默认不是 source |
| root | consumer 会搜索或读取的物理目录/配置入口，一个 consumer 可以有多个 root |
| target | 稳定消费端，identity 为 `host_id + consumer_instance_id`；OS、版本、路径和 profile 等是属性或 selector |
| profile | 同一 consumer 的一组显式运行配置；当前不是独立 target identity |
| placement/residency policy | 声明 source/asset 允许出现、缓存、渲染和投影到哪些 host；work-local 内容只允许留在 Mac 工作机 |
| layer | 可参与组合的声明片段，例如 GitHub personal/shared base、Mac-local work、host、consumer、local overlay |
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
| DEC-04 | Source 驻留与投影策略 | personal/shared 与 work-local 如何组合、允许、阻断和例外 | placement/projection policy 与防泄漏约束 |
| DEC-05 | Overlay 与解析 | 各 layer 及各类 asset 如何合成、删除和冲突 | 确定性 resolved desired state |
| DEC-06 | Secret 与本地参数 | secret、路径、账号和 host 差异放哪里 | 不泄漏且可移植的 local-value contract |
| DEC-07 | Inventory | source、resolved、rendered、live、effective 各盘点什么 | 有证据边界的全状态清单 |
| DEC-08 | Consumer 可见与渲染 | 多 root、shadow、frontmatter、格式转换后 consumer 看见什么 | per-consumer visibility/render contract |
| DEC-09 | 变更预演 | apply 前必须报告并固定哪些差异、输入和风险 | 可审批且可复现的 plan contract |
| DEC-10 | 安全实施 | ownership、计划等价、原子性、幂等、备份和恢复怎么做 | apply safety contract |
| DEC-11 | Effective 验证（Later） | 如何分级证明 Codex/Qoder/Claude 真正加载或使用 | runtime evidence contract，不作为 v1 gate |
| DEC-12 | 漂移检查 | 查什么、何时查、谁负责、何时自动修 | drift/reconcile policy |
| DEC-13 | 跨机配置一致性 | 分发、离线、版本错位、receipt、汇总如何工作 | cross-host config coordination contract |
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
| DEC-13 | Must | 两台机器各自达到目标配置并可汇总 receipt；不预设中央控制端，也不管理远端进程 |
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
| 权限与安全策略 | approval、sandbox、filesystem/network permission、tool allow/deny、trust、managed policy/requirements | 受管配置；不得被 local overlay 绕过 |
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
- 后果：DEC-03 必须定义 source authority、Git/non-Git revision 的信任与浮动 ref policy；DEC-05/08 必须输出确定的 resolved/render input set；DEC-09/10/12/16 必须使用获批 revision 与 receipt 做 plan 等价、apply、drift 和 explain。dirty source、secret/local binding fingerprint 与历史不可用时的具体处理分别留给 DEC-03、DEC-06 和 DEC-09。
- 验收断言：获批 plan 能固定全部 source revision、adapter/capability 输入和预期 render；相同 logical asset 的内容更新不会变成新资产；相同内容的无关资产不会因 digest 相同被合并；Git 历史不可用时仍可依 receipt 校验本次 revision，但不得声称已验证 ancestry；任何 conflict 都指出 competing candidates、authority/precedence 和停止原因。

### DEC-02 目标拓扑与隔离能力

- 状态：02A、02B 已拍板；02C 待给方案
- 依赖：DEC-01。
- 决策轴：
  - 02A：target key 包含哪些维度：host、consumer，以及哪些事实只作为属性。
  - 02B：work 是 target context，还是 source/asset placement 与 residency policy。
  - 02C：如何声明 target/consumer 的实际能力；所需隔离无法承载时是 `unsupported`、`block` 还是允许显式降级。

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
- 后果：DEC-03 定义 GitHub personal/shared 与 Mac-local work 的 authority/trust；DEC-04 定义 placement/egress deny、Mac union 和例外；DEC-05 固定 overlay；DEC-06/13 决定哪些脱敏元数据允许离开 Mac。02C 的 capability/unsupported 行为仍未拍板，不能从本决定推断。
- 验收断言：四个 consumer 均映射到唯一稳定 target；升级 consumer、改变 binary path/root 不产生新 target；Mac 两个 target 解析 base + work overlay，Windows 两个 target 只解析 base；任一 work payload 出现在 Windows 或未授权中间产物时必须被检测为 policy violation，而不是 drift success。

### DEC-03 权威来源与信任

- 状态：待给方案
- 依赖：DEC-01、DEC-02。
- 决策轴：
  - 03A：public、private、work-only、本机声明和外部 registry 各自能声明什么，ownership 如何分配。
  - 03B：冲突时按字段/资产由谁裁决；cache、rendered 和 live 如何禁止反客为主。
  - 03C：外部 source、浮动 revision、签名/digest、allowlist 和更新策略如何受信。
  - 03D：skill、hook、MCP 等可执行或可调用内容如何分级风险并获批。
- 初步验收：每个 resolved asset 能追溯到唯一 authority 和不可歧义的输入 revision/digest；不可信输入 fail closed。

### DEC-04 Source 驻留与投影策略

- 状态：待给方案
- 依赖：DEC-02、DEC-03。
- 决策轴：
  - 04A：GitHub personal/shared 与 Mac-local work 的 source/asset classification、allowed hosts 和 egress deny 如何定义。
  - 04B：Mac 的 base + work union、Windows 的 base-only 如何形成确定投影。
  - 04C：默认 allow/deny、例外授权以及 source/cache/render/receipt/live 全链路防泄漏如何定义。
  - 04D：哪些脱敏元数据允许跨机；无法证明 residency 时的停止条件与迁移要求。
- 初步验收：work-only payload 进入 Windows 或非授权中间产物必须 `block`；任何例外有显式授权和 receipt；不存在虚构的 Mac personal/work 双 target。

### DEC-05 Overlay 与解析

- 状态：待给方案
- 依赖：DEC-01—DEC-04。
- 决策轴：
  - 05A：public/private base、work-local、host、consumer、local layer 的顺序和适用范围。
  - 05B：每种纳入 asset 的 merge algebra：skill 的集合/目录、MCP/settings 的键或字段、instructions 的 import/拼接、hooks 的有序列表等。
  - 05C：add、override、remove/mask、duplicate 和 conflict 的语义；哪些冲突按优先级，哪些必须阻断。
  - 05D：如何表达 `personal/shared base + work-local + host/consumer/local`；local overlay 不得绕过 residency policy 或 source trust。
- 初步验收：相同输入生成相同 resolved state；每个字段/资产可解释 provenance；所有纳入类型均有 merge/remove/conflict 规则。

### DEC-06 Secret 与本地参数

- 状态：待给方案
- 依赖：DEC-03—DEC-05。
- 决策轴：
  - 06A：secret value/reference、本机绝对路径、账号、OS/host 参数如何分类。
  - 06B：各类 reference/local binding 存在哪里、由谁提供、哪些 layer 允许覆盖；外部 credential provider 仍拥有 secret value 生命周期。
  - 06C：plan、diff、receipt、日志和错误信息如何脱敏。
  - 06D：缺值、引用失效或权限不足时如何 fail closed 并诊断。
- 初步验收：portable source、rendered artifact 和 receipt 不泄漏 secret；本机路径不会误投影到其它 host。

### DEC-07 Inventory

- 状态：待给方案
- 依赖：DEC-01—DEC-06。
- 决策轴：
  - 07A：v1 对 source、resolved、rendered、live 和绑定事实盘点到什么粒度；Later 的 effective evidence 是否另表保存。
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
- 初步验收：能按声明的 roots/precedence 静态计算每个 consumer 的预期可见集合；同名项的 winner/shadow 可解释；派生差异可审阅、可复现、不反写 raw source。runtime 是否实际加载由 DEC-11 的 Later 证据确认。

### DEC-09 变更预演

- 状态：待给方案
- 依赖：DEC-03—DEC-08。
- 决策轴：
  - 09A：plan 是否完整覆盖 add/remove/change/shadow/block/no-op 及原因链。
  - 09B：是否固定所有 source revision/digest、policy、renderer/adapter 版本和 target inventory snapshot。
  - 09C：如何按 host/consumer/source class 汇总“多、少、变、shadow、block”数量和风险。
  - 09D：plan identity/hash、审批粒度、有效期和输入变化后的失效规则。
- 初步验收：apply 前可回答每个消费者变化及原因；未进入获批 plan 或输入已变化的动作不能执行。

### DEC-10 安全实施

- 状态：待给方案
- 依赖：DEC-09。这里只约束受管配置资源的 apply，不承担整机事务、binary/plugin package 安装或进程恢复。
- 决策轴：
  - 10A：resource ownership 与非纳管资产保护边界。
  - 10B：apply 如何证明与获批 plan/hash 及固定输入完全等价。
  - 10C：事务/原子边界、并发锁、幂等和重复执行语义。
  - 10D：备份、rollback、部分失败状态、恢复与人工接管。
- 初步验收：不会静默删除 unmanaged/unknown-owner 资产；部分失败可诊断且有确定恢复动作。

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
  - 12B：检查由手动、hook、定时任务还是外部 daemon 触发；退出码和告警语义。Almagest 不负责 daemon 生命周期。
  - 12C：如何归因、分级、指派 owner；哪些漂移允许自动修，哪些必须人工审批。
  - 12D：Later 如何把 consumer runtime 漂移与配置漂移区分并关联，不得反向改变 v1 成功口径。
- 初步验收：报告指出差异层、责任 source、证据、风险和下一动作；破坏性修复不会静默发生。

### DEC-13 跨机配置一致性

- 状态：待给方案
- 依赖：DEC-02—DEC-12。
- 决策轴：
  - 13A：每台机器独立 pull+plan+apply，还是存在只协调配置/receipt 的控制端；边界和信任如何划分。任何选项都不管理远端 Agent 进程。
  - 13B：配置/引用、policy、adapter 与 source revision 如何分发和锁定。
  - 13C：离线、配置/adapter 版本错位、apply 失败重试、receipt 上传和跨机对比如何处理。
  - 13D：汇总哪些元数据；如何避免把 private/work 内容带到未授权 host 或中央端。
- 初步验收：不暴露 private/work 内容也能判断 Mac 与 Windows 是否处于各自正确 target 状态。

### DEC-14 配置资产生命周期

- 状态：待给方案
- 依赖：DEC-01—DEC-13。
- 决策轴：
  - 14A：首次 bootstrap、现状 import、adopt/unmanaged 的状态机。
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
  - 16A：audit/receipt 保存哪些 actor、time、source/digest、policy、plan、target、action、result 和 evidence。
  - 16B：记录存在哪里、保留多久、如何脱敏和防篡改。
  - 16C：v1 explain 如何回答 identity、provenance、shadow、block 和 config/binding drift；Later 如何追加 runtime failure/evidence。
  - 16D：跨机聚合、离线 receipt、schema 升级和审计记录自身生命周期如何处理。
- 初步验收：能回答“谁在何时基于哪个固定输入/plan，把什么投影到哪个 target，结果为何生效或失败”。

## 需求追踪矩阵

| 用户成功口径 | 主责任卡 | 需覆盖对象 | 最终证据 |
|---|---|---|---|
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
- 本文不修改 live 配置，不迁移 skill，不注册 MCP，不建立后台服务。
- 本文不把 gaal 的已有数据模型或 Almagest 当前实现直接当作目标模型。

## 后续产物

1. 16 项全部拍板后，从本工作台蒸馏 capability spec、acceptance matrix 和必要 ADR。
2. 方向性结论进入 `docs/decisions/`，稳定约束进入 contract/spec；确认引用闭合后删除本 living design，保留不可变 capture 与 Git 历史。
3. 再建立“能力 → gaal / `npx skills` / Agent 原生 / Almagest 自建”的实现归属矩阵，供 principal 决定继续建设、改造或退役。
4. 实现、迁移和发布分别建立新 PM issue，不复用本设计 issue 承载执行。
