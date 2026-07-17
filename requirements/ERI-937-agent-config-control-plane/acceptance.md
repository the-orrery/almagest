# 能力拍板工作包验收

## 本阶段验收断言

```gherkin
Scenario: principal 通过 operator Agent 驱动 Almagest
  Given principal 用自然语言向 operator Agent 表达目标或作出批准
  When operator Agent 调用 Almagest 执行 inventory、plan、apply 或 verify
  Then Almagest 通过稳定 schema、诊断码、退出码和引用 ID 返回机器可消费结果
  And operator Agent 可按引用 ID 获取完整 diff、provenance 和 explain
  And principal 不需要直接操作 CLI/TUI 或解析原始 plan
  And 任何非 no-op 配置 apply 只接受绑定 principal 决定与精确 plan hash 的 approval artifact
  And receipt 分别记录 principal approver 与 operator Agent
```

```gherkin
Scenario: authority 合法但仍歧义时只做当前 plan 的一次性裁决
  Given 多个候选均拥有 authority
  And 确定性 precedence 与 merge 规则仍无法唯一解析
  When principal 通过 operator Agent 为当前 conflict set 逐项选择结果
  Then approval artifact 绑定 target、plan hash、固定输入、完整 conflict set 与选择
  And apply 只执行该精确 plan，authored source 保持不变
  And receipt 将结果标记为 transient resolution exception，而不是普通 compliant
  And 下一次 plan 对未修复的同一 source 歧义重新阻断
  And 只有 principal 明确要求修 source 时，Agent 才生成 source 变更并基于新 revision 重新 plan
```

```gherkin
Scenario: downstream 反向污染 source 时只阻断不自动修复
  Given Almagest 根据受管 provenance evidence 识别到 cache、resolved、rendered 或 live 内容进入 authority source
  When operator Agent 请求 inventory、resolve、plan 或 apply
  Then Almagest 返回带 detection ID、source、证据、影响和恢复候选的结构化阻断诊断
  And 只读 inventory、explain 与取证可以继续
  And source、live 及其它 downstream 状态均不被自动隔离、删除、恢复或接纳
  And plan surface 只返回 block-only record，依赖该 source 的 resolve、可执行 action 与 apply 保持阻断
  And DEC-02C break-glass 或 DEC-03B1 单次裁决均不能绕过阻断
  And 只有 principal 明确指定修复动作后，Agent 才改变 source、生成新 revision 并重新 plan
```

```gherkin
Scenario: 外部版本只在吸收为 owned revision 后进入 Almagest
  Given 外部 registry、release 或 tag 出现新候选
  And 外部工具尚未把候选吸收进 GitHub personal/shared 或 Mac-local work
  When operator Agent 请求 Almagest inventory、plan 或 drift
  Then 外部候选对 desired state、resolved state 和 plan 零影响
  And Almagest 不访问上游网络、不解析浮动版本，也不保存候选或可更新状态
  When 外部工具读取 owned source revision/time 作为水位并完成吸收
  And owned source 形成新的 authored revision
  Then Almagest 只把该 revision 作为普通 owned input 进入 inventory、resolve 和 plan
  And upstream provenance 只作惰性元数据，不取得 authority
  And 吸收后的任何配置差异仍须经过 DEC-03D 逐变更审批
```

```gherkin
Scenario: 任何配置差异都先报警并等待当前 plan 批准
  Given Almagest 基于固定 source、resolved revision 和 target inventory 生成 plan
  And plan 包含至少一个新增、删除、修改、mask、shadow、移动、接纳或修复动作
  When operator Agent 请求 apply
  Then Almagest 返回结构化差异并保持零写入
  And operator Agent 向 principal 摘要说明 target、before/after、provenance、动作和影响
  And principal 可以批准当前精确 plan、拒绝或要求调整后重新 plan
  When operator Agent 提交绑定 principal 决定、完整 action set、固定输入和 plan hash 的 approval artifact
  Then Almagest 只执行获批 plan
  And receipt 分别记录 principal approver 与 operator Agent
  And 任一输入、action set 或 plan hash 变化都会令旧 approval 失效
  And 普通配置批准不能越过 capability exception、source contamination 或其它硬策略 block
  And 只读操作与 no-op 不要求批准，也不产生隐式写入
```

```gherkin
Scenario: 驻留权限跟随 source 且 work source 无单项例外
  Given GitHub personal/shared source 中存在一个受管 asset
  And Mac-local work source 中存在另一个受管 asset
  When Almagest 为 Mac target 解析 source eligibility
  Then GitHub asset 与 work asset 都可以成为 Mac Codex/Qoder 的候选
  When Almagest 为 Windows target 解析 source eligibility
  Then GitHub asset 可以成为 Windows Codex/Claude 的候选
  And work asset、work field contribution 及任何含 work payload 的派生物均被排除
  And 任一 work payload 已出现在 GitHub、Windows 或其它非授权位置时必须返回硬策略 block
  And 不存在能放宽该结果的 per-asset allowed-host 字段、白名单或临时 approval
  And 把 work asset 迁移为 GitHub asset 必须形成显式 authored change、新 source revision 和 DEC-03D 新 plan
```

```gherkin
Scenario: target 固定 source eligibility 且不做运行时 fallback
  Given Mac Codex、Mac QoderCLI、Windows Codex、Windows Claude 四个已声明 target
  And GitHub personal/shared base 与 Mac-local work 两类受管 source
  When Almagest 在 overlay 和 render 前计算 source eligibility
  Then Mac Codex 与 Mac QoderCLI 的 eligible source 集合恰为 GitHub base 加 Mac-local work
  And Windows Codex 与 Windows Claude 的 eligible source 集合恰为 GitHub base
  And asset selector 可以缩小候选集，但不能让 Windows 取得 work source
  And cwd、profile、operator Agent、root 是否碰巧存在或 source 临时不可用均不能改写映射
  When 已登记给 Mac target 的 work source 缺失、身份不明或不可证明
  Then resolve 与 apply 必须停止并返回 unknown 或 block
  And 不得以 GitHub-only 结果宣称 Mac 配置合规
  And 同名 asset 的 winner、字段 merge 与 consumer render 仍分别由 DEC-05 和 DEC-08 决定
```

```gherkin
Scenario: 只有两个 authored layer 且环境差异不取得配置权威
  Given GitHub personal/shared base、Mac-local work 与四个已声明 target
  When Almagest 为 Mac target 构造 authored layer 集合
  Then 候选只来自 GitHub base 与 Mac-local work，并按 base 到 work 的确定顺序进入 resolve
  And 该顺序不预先决定同名 asset 或字段的 winner
  When Almagest 为 Windows target 构造 authored layer 集合
  Then 候选只来自 GitHub base
  And host、OS、consumer、consumer version、profile、workspace、root 与 binary path 只能参与 selector、render 或 binding 验证
  And secret、账号与本机绝对路径只能为已声明引用提供 local binding
  And rendered artifact、live 文件、cache、session 与 unmanaged 本机文件均不能成为 authored layer
  When principal 要接纳一个 unmanaged 本机差异
  Then 必须显式修改拥有 authority 的 authored source 并生成新 plan
  And 不得把 live target 或任意 local 目录提升为最高优先级 override
```

```gherkin
Scenario: Schema-aware merge 只组合结构兼容的贡献
  Given GitHub base 与 Mac-local work 中存在经过 authority/eligibility 检查的 authored contribution
  And 对应 adapter schema 已固定 version、digest、stable key 与每个节点的 merge shape
  When Almagest resolve 两个 layer
  Then `atomic` 正文、文件和 opaque subresource 不做行级或递归 merge
  And `granular-map` 中不相交的 key 可以组合，嵌套字段继续按声明的 shape 解析
  And `set` 只按规范化 value 或稳定 element key 去重
  And `keyed-list` 只按稳定 item ID 组合，不使用数组下标
  And `ordered-list` 只按显式 item ID 与 schema 声明的 order key/约束生成确定顺序
  And 每个 resolved 字段、元素和 item 都保留 source、layer、schema path、shape 与 revision provenance
  When 可信 asset schema 缺失、不受支持或 identity 无法验证
  Then resolve 返回结构化 unknown 或 block
  And 不得 fallback 到 recursive deep merge、array append、文件扫描顺序或文本行 merge
  When shape 不兼容、item ID 缺失/重复、order 约束无效、两个贡献命中同一 atomic leaf 或出现 remove/mask
  Then 只产生带候选与 provenance 的 typed collision
  And typed collision 必须继续满足 DEC-05C 的等价去重、显式意图或阻断规则
  When merge schema version、stable key 或 ordering 规则变化
  Then 旧 plan 与 approval 失效，并要求基于新 schema 重新 plan
```

```gherkin
Scenario: 非等价 overlay 必须显式声明 override 或 mask
  Given GitHub base 与 Mac-local work 均通过 authority、residency 与 target eligibility 检查
  And adapter schema 与 source revision 已固定
  When 两层贡献命中新 logical ID、不同 granular key 或不同 stable item ID
  Then Almagest 按 DEC-05B 的 shape 自动组合并保留逐贡献 provenance
  When eligible contribution 命中同一 semantic target 且 canonical value 等价
  Then resolved state 只保留一个值并标记 equivalent_duplicate
  And explain 保留所有重复贡献的 source 与 layer provenance
  When 两层命中同一 semantic target、内容不等价且 work 未声明合法 override 或 mask
  Then resolve 返回结构化 conflict，普通 plan/apply 零写入
  And 不得因 base→work 顺序自动选择 work
  When work 对该 semantic target 显式声明无歧义的 override
  Then 只替换该 eligible target，并把 intent、base 与 work provenance 纳入 resolved evidence
  When work 对该 semantic target 显式声明无歧义的 mask
  Then 该 target 只从匹配的 Mac resolved state 隐藏
  And GitHub base 与 Windows base-only resolved state 保持不变
  When override/mask 未指明目标、目标歧义、多个意图竞争或 shape/顺序规则无法解析
  Then resolve 阻断并返回稳定诊断码、候选、路径、digest 与 provenance
  When principal 只裁决当前一次 conflict
  Then 必须走 DEC-03B1 transient resolution，source 保持不变且下次重新阻断
  When principal 明确要求修 source
  Then operator Agent 才生成 override、mask、remove 或其它 source diff，形成新 revision 并重新 plan
  And 所有非 no-op 写入仍必须取得 DEC-03D 对当前精确 plan 的批准
  When collision 同时违反 authority、eligibility、residency、egress、secret 或 capability hard policy
  Then hard policy block 优先，DEC-05C、DEC-03B1 与普通 approval 均不能放行
  And target reference 是否绑定 expected revision/digest 不在本场景预设，由 DEC-05D 决定
```

```gherkin
Scenario: work 越界全链路阻断且只由 principal 决定恢复
  Given 某个 work asset、field contribution 或含 work contribution 的派生 payload
  When Almagest 即将把它写入 GitHub、Windows 或其它非授权 source、cache、resolved、rendered、plan、receipt 或 live 位置
  Then 写入必须在物化前被拒绝
  And 非授权目标保持零变化
  And Almagest 返回可引用 detection、违规位置、provenance、影响范围和阻断状态的结构化诊断
  When Almagest 只读发现某个非授权位置已经存在 work payload
  Then 依赖该状态的 resolve、普通 plan 与 apply 必须阻断
  And inventory、diff、explain 与取证仍可继续
  And 不得自动删除、隔离、迁移、修复或接纳 source、cache、live 及其它副本
  And 普通变更 approval、break-glass、单次冲突裁决或 acknowledgment 均不能解除阻断
  When principal 明确指定恢复动作且批准绑定 detection、固定输入、完整 action set 和 plan hash 的 recovery plan
  Then operator Agent 只能执行该精确恢复动作
  And 执行后必须重新 inventory 与 verify
  And 只有证据证明越界 payload 已消失且输入重新固定，才能解除阻断并重新生成普通 plan
```

```gherkin
Scenario: work 内容与元数据零离机且每台机器只做本地即时操作
  Given Mac-local work source 及其 inventory、plan、receipt、evidence 和诊断
  When Mac operator Agent 在当前操作中调用 Mac 本机 Almagest
  Then 完整结构化结果只在 Mac 本机产生和消费
  And operator Agent 可以在当前会话中向 principal 解释结果并请求决策
  And Almagest 不生成或推送跨机报告、状态信封、receipt 或远端 evidence reference
  When Windows operator Agent 调用 Windows 本机 Almagest
  Then Windows 只解析本机 GitHub base target
  And Windows 不查询也无法观察 Mac work 的存在性、状态、名称、路径、digest、数量、时间或诊断
  When 任一待导出 artifact 无法证明完全不含 work content 或 metadata
  Then 写入 GitHub、Windows 或中央端的 egress 必须阻断
  And 本机只读 inventory 与 explain 仍可继续
  And 脱敏、hash、加密或 acknowledgment 均不能放行
  When principal 明确要求某项内容跨机共享
  Then 必须将其重新编写或迁移为新的 GitHub authored asset
  And 形成新 source revision 并进入 DEC-03D 新 plan
```

```gherkin
Scenario: 顺序化完成一个决策轴拍板
  Given 当前决策卡的上游依赖均已拍板
  And Codex 已说明问题、事实边界与需要澄清的信息
  And 当前决策轴的候选项同轴互斥
  When principal 对 A/B/C/D 形式的真实候选作出选择或修改
  Then 文档记录决定、理由、后果和可验证断言
  And 当前决策轴标记为已拍板
  And 当前卡全部决策轴完成后才进入下一张卡片
```

```gherkin
Scenario: 诉求不足以形成真实选项
  Given 当前信息不足以区分可行方案
  When 进入该能力卡
  Then Codex 只提出一到两个高杠杆澄清问题
  And 不生成凑数方案
  And 卡片保持待澄清
```

```gherkin
Scenario: 完成能力契约
  Given DEC-01 至 DEC-16 全部标记为已拍板
  When 对整份能力模型做一致性审阅
  Then 每个 target、asset、layer、lane 和状态术语均无歧义
  And 每项能力都有验收断言
  And Assumption 已验证或转成约束
  And Risk 已接受或缓解
  And Issue 已关闭或转单
  And Dependency 已明确 owner、版本边界和复核条件
  And 尚未把实现工具选择偷写成能力需求
```

```gherkin
Scenario: 能力全集具有可追踪证据
  Given DEC-01 已明确纳入的资产类型
  And DEC-02 已明确四个已知 consumer 的 target
  When 对用户五条配置成功口径和一条操作者模型成功口径做覆盖审阅
  Then 每条口径均能追踪到 capability、assertion 和 evidence
  And 每种纳入资产与每个已知 consumer 均至少出现在一个正向和必要的负向验收场景中
  And 没有两个能力在未说明边界的情况下声称拥有同一责任
```

## 完成检查表

- [ ] 16 张卡的每个决策轴均包含真实可选方案。
- [ ] 16 张卡的每个决策轴均记录 principal 决定与理由。
- [ ] 16 张卡的每个决策轴均说明收益、代价、风险和可逆性。
- [ ] 16 张卡的每个决策轴均映射到可执行或可人工复核的验收断言。
- [ ] 五条配置成功口径、一条操作者模型成功口径、四个已知 consumer 与 DEC-01 纳入的每种 asset 均进入追踪矩阵。
- [ ] 上下游决定无冲突；发生重开时已重审受影响卡片。
- [ ] 能力模型可以回答任意 target 的 desired、plan、live、effective 与责任来源。
- [ ] principal、operator Agent、Almagest 与 consumer 四种角色无歧义，机器接口是唯一 canonical contract。
- [ ] 单次冲突裁决与 source 持久修复是两条不同路径；未经 principal 明确指示不得从前者升级到后者。
- [ ] source contamination 默认只阻断并告警；自动隔离、恢复、删除或 adopt 均不构成隐含恢复权限。
- [ ] 外部候选、周期检查与吸收完全位于 Almagest 之外；只有吸收后的 owned revision 能改变配置计划。
- [ ] 所有非 `no-op` 配置写计划均先报警并逐 plan 取得 principal 批准；不按风险或资产类型静默放行。
- [ ] 驻留权限只跟 source；Mac-local work 全量 Mac-only，任何 asset、标签或临时批准都不能单独放宽。
- [ ] 四个 target 的 eligible source 映射固定；Mac Codex/Qoder 为 GitHub + work，Windows Codex/Claude 为 GitHub-only，运行时条件不得静默改写或 fallback。
- [ ] work 越界写入在物化前拒绝；既有越界阻断受影响链路并告警；Almagest 不自动恢复，只有 principal 批准的精确 recovery plan 经重新验证后才能解除。
- [ ] work 内容和派生元数据均不离开 Mac；每台机器只由同机 Agent 当场调用同机 Almagest，不存在中央汇总、receipt 上传或跨机报告。
- [ ] authored overlay 只有 GitHub base 与 Mac-local work 两层；host/consumer 环境差异、本机 binding、rendered/live/unmanaged 状态均不得取得 layer authority。
- [ ] merge 由版本化 schema 显式区分 atomic、granular map、set、keyed list 与 ordered list；缺可信 schema fail closed，缺失稳定 ID 或无效顺序只生成 typed collision，均不做通用 deep merge。
- [ ] 已形成实现归属评估的输入，但尚未替 principal 做技术选型。

## 本轮文档落盘验收

- [x] 用户原始目标已进入不可变 capture。
- [x] 16 项能力与依赖顺序完整记录。
- [x] 每项均列出独立决策轴，并预留 A/B/C/D 形式候选、推荐、决定、后果与验收位置。
- [x] PM issue 与 bundle 互相可定位。
- [x] Markdown、YAML、Git diff 与仓级检查通过。
