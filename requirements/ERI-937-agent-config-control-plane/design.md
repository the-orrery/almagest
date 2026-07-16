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

当前阶段采用“配置一致优先”：v1 先保证每个 target 的 declared → resolved → rendered → live 配置与其目标状态一致，并能在 apply 前报告差异、apply 后检查漂移。“一致”不是要求 Mac/Windows 或 personal/work 配置字节相同，而是各自 live 状态符合各自 overlay 后的目标。consumer runtime 是否实际加载、hook 是否执行成功、plugin 包是否安装并健康属于后续能力；保留在 16 项能力地图中，不自动进入 v1 `Must`。

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

- 状态：01A 已拍板；01B、01C 待给方案
- 决策轴：
  - 01A：v1 纳入哪些 asset 类型：skill、MCP、instructions、settings、hooks、plugins 或其它。
  - 01B：每种 asset 的 identity granularity 与 canonical ID 由哪些字段构成。
  - 01C：如何区分同一资产、版本/revision、consumer 派生物、冲突副本和无关同名资产。
- 01A 决定（v0.2，2026-07-16，approver: principal）：选择 B——v1 纳管完整 Agent **配置面**，先保证配置一致；运行生命周期和行为正确性以后再考虑。

| 候选 | 配置范围 | 责任边界 | 结果 |
|---|---|---|---|
| A | skills、MCP、instructions、settings、hooks 配置 | 不纳管 plugin 配置 | 拒绝：plugins 也必须进入配置一致性范围 |
| B | A + plugins 配置 | 保证 declared/resolved/rendered/live 配置一致；不负责 hook 执行、plugin 包安装/升级、依赖解析或运行结果 | **已选择** |
| C | B + plugin 包、wrapper、alias、Agent binary 和实际运行行为 | 进一步负责安装、版本、进程、执行验证与恢复 | 拒绝作为 v1：超出“先保证配置一致” |

- `Must`：skills、MCP、instructions、settings、hooks 配置、plugins 配置的声明、overlay、consumer 渲染、投影、diff 与漂移检查。
- `Later`：hook 是否成功执行、plugin 包安装/升级/卸载及依赖、consumer 是否实际调用、运行健康与自动恢复。
- `Out`（v1）：Agent binary、wrapper、shell alias、进程管理和完整主机环境管理。
- B 与 C 的边界示例：B 证明“目标配置声明启用 plugin X、注册 hook Y，且目标文件与声明一致”；C 还要证明“plugin X 已正确安装并运行、hook Y 已执行成功、Agent binary 版本正确”。
- 后果：DEC-11 的 runtime Effective 验证不属于 01A 的 v1 配置一致性承诺；后续单独决定是否列入 Later 或下一阶段，不能反向扩大本项范围。
- 需要避免：把目录名相同直接当同一资产；一次纳入所有配置导致范围失控。
- 初步验收：给任意两个候选配置资产，系统能判定关系并解释依据；每个纳入类型都有 identity 与 version 规则；对 hooks/plugins 只验证配置状态，不以实际执行结果作为本项成功条件。

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
