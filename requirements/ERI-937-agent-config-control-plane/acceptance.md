# 能力拍板工作包验收

## 本阶段验收断言

```gherkin
Scenario: principal 通过 operator Agent 驱动 Almagest
  Given principal 用自然语言向 operator Agent 表达目标或作出批准
  When operator Agent 调用 Almagest 执行 inventory、plan、apply 或 verify
  Then Almagest 通过稳定 schema、诊断码、退出码和引用 ID 返回机器可消费结果
  And operator Agent 可按引用 ID 获取完整 diff、provenance 和 explain
  And principal 不需要直接操作 CLI/TUI 或解析原始 plan
  And 高风险 apply 只接受绑定 principal 决定与精确 plan hash 的 approval artifact
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
  And 吸收后的可执行或可调用内容仍须经过 DEC-03D 风险策略
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
- [ ] 已形成实现归属评估的输入，但尚未替 principal 做技术选型。

## 本轮文档落盘验收

- [x] 用户原始目标已进入不可变 capture。
- [x] 16 项能力与依赖顺序完整记录。
- [x] 每项均列出独立决策轴，并预留 A/B/C/D 形式候选、推荐、决定、后果与验收位置。
- [x] PM issue 与 bundle 互相可定位。
- [x] Markdown、YAML、Git diff 与仓级检查通过。
