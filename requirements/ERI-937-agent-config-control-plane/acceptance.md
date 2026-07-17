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
  And rendered artifact、live 文件、cache、session、external-owned 与 unknown-owner 本机文件均不能成为 authored layer
  When principal 要接纳一个 external-owned 或 unknown-owner 本机差异
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
  And 合法 override/mask 必须按 DEC-05D 绑定 stable target locator 与 expected target semantic digest
```

```gherkin
Scenario: 两个 authority source 使用 inventory 引用原生 payload
  Given GitHub personal/shared 与 Mac-local work 是仅有的两个 authored source
  And 每个 source 均提供一份逻辑、版本化、机器可校验的 inventory
  When Almagest 读取一个 inventory entry
  Then entry 可表达 stable logical ID、asset kind、source-relative payload reference、selector 与 contribution operation
  And override/mask entry 可表达无歧义的 target reference
  And 实际 skill、MCP、instructions、settings、hooks 或 plugin 内容仍保存在原生 payload 中
  And inventory 不复制 payload 正文
  When payload path 改变但 logical ID 与 canonical content 保持不变
  Then Almagest 仍把它识别为同一 logical asset
  When inventory schema 缺失或不受支持、logical ID 重复、payload reference dangling/ambiguous 或越出 source root
  Then source 标记 invalid 并阻断依赖它的 resolve/apply
  When payload root 中出现未登记的候选内容
  Then 不得自动 adopt 或加入 authored candidate set
  And 只能作为 orphan/unknown-owner evidence 交给 DEC-07/09，除非另有正向证据证明 external-owned owner
  When Almagest 为 Windows target 建立候选
  Then 只读取 GitHub inventory 及其 payload
  And 不读取、不接收也不探测 work inventory
  When Almagest 为 Mac target 建立候选
  Then 分别验证 GitHub 与 work inventory/payload，再按 eligibility 和 DEC-05A—05C resolve
  When Almagest render 任一 consumer 配置
  Then inventory 中的 ID、selector、operation、target reference 与 provenance 不得注入 SKILL.md frontmatter、instruction/prompt body 或 rendered config
  And payload 原有 consumer/asset frontmatter 的保留、删除或翻译仍由 DEC-08C 决定
  When work inventory 声明 override 或 mask
  Then target reference 必须包含 stable logical/subresource/item locator
  And 必须包含由固定 adapter/schema 对该精确目标单元计算的 expected canonical semantic digest
  And 不得使用 raw file bytes、path、mtime、whole asset revision 或 whole source revision 代替精确目标摘要
  When base 只发生格式化、payload 移动、其它字段或其它资产变化
  And 被引用目标的 canonical semantic digest 保持不变
  Then 旧 plan/approval 因 source revision 变化而失效
  But 重新 plan 后 override/mask 意图仍有效，不标记 stale
  When 被引用目标的 canonical semantic value 变化、目标消失或 schema identity 无法验证
  Then target reference 标记 stale_target 并阻断普通 resolve/apply
  And 诊断包含 target locator、expected/observed digest、目标差异与 provenance
  And Almagest 不得自动刷新 digest、扩大 target 或继续套用旧意图
  When principal 明确要求按新 base 语义持久修复
  Then operator Agent 才能更新或删除 override/mask，或更新 expected digest
  And 该修改形成新的 work source revision 并重新 plan
  When principal 只要求处理当前一次
  Then 只能走 DEC-03B1 transient resolution，不得永久刷新 digest
```

```gherkin
Scenario: 本机敏感输入按 declaration、binding、observation 三类分离
  Given GitHub personal/shared 与 Mac-local work 是仅有的两个 authored layer
  When source 需要 secret、账号、本机路径或 host-dependent 参数
  Then source 只能声明 portable typed slot/reference、value type、required/optional、sensitivity 与约束
  And provider-neutral logical reference 可以随 source 版本化
  And 实际 secret、绝对路径、账号/profile 选择、machine ID 或 local endpoint 不得内联进 portable declaration
  When 当前 target 为已声明且允许本机补值的 typed slot 提供实际路径、账号/profile、local endpoint、machine ID 或 credential provider locator
  Then 该表示分类为 host-local binding
  And binding 只能满足该 slot，不得新增 asset、改变引用语义、覆盖普通 authored 字段或绕过 authority/residency policy
  And secret value 的生命周期仍由外部 credential provider 拥有
  When Almagest 读取 OS、architecture、hostname、consumer/version、路径存在性/权限或 credential/login 可用性
  Then 该表示分类为 observed host fact
  And 它只能用于 selector、capability、plan/verify evidence 或诊断
  And 不得作为 authored contribution、binding override 或 desired-state winner
  When 同一账号概念分别表示所需账号角色、本机选中账号和当前登录状态
  Then 三个表示必须分别分类为 portable declaration、host-local binding 与 observed host fact
  When binding 或 observation 在 Mac 与 Windows 间不同
  Then 两台 host 的 authored base revision 可以保持相同
  And 不得为该差异创建第三 authored layer
  When schema/adapter 无法证明 local-sensitive 字段的分类
  Then 返回 unknown_local_role 并阻断依赖该字段的普通 resolve/plan/apply
  And 不得按 non-secret、环境变量存在或 adapter 惯例猜测分类
  And binding 的存放/provider/scope 已由 DEC-06B 固定
  And 脱敏与缺值恢复必须分别遵守 DEC-06C—06D
```

```gherkin
Scenario: 每台 host 通过显式 typed registry 绑定本机值
  Given authored source 已声明 stable typed slot、sensitivity、allowed binding scope 与 binding mode
  And 当前 host 有一份逻辑 host-local binding registry
  When registry 为该 slot 保存非 secret 本机值
  Then entry 必须显式绑定 slot ID、host-wide 或 exact-target scope、fill 或 replace-ref mode
  And value 必须通过 slot type/schema validation
  When registry 为 secret slot 提供 binding
  Then registry 只能保存显式 provider kind 与 provider locator
  And secret value 的创建、轮换、撤销与存储仍由外部 credential provider 负责
  And plan、diff、receipt、日志、错误与 explain 对 registry locator/value 的披露必须遵守 DEC-06C 的 per-surface safe view
  When 环境变量、Keychain、credential manager、本机文件或其它 provider 中存在候选值
  But registry entry 未显式引用该 provider 与 locator
  Then 候选值不得被自动发现、adopt 或用于 render
  When slot 只允许 exact-target scope
  And registry 只提供 host-wide entry
  Then binding scope 无权满足该 slot
  When 同一 slot/target 同时匹配多个 entry
  Then 返回 ambiguous_binding 并阻断依赖它的普通 resolve/plan/apply
  And 不得采用 exact-target-wins、last-writer-wins 或 provider 顺序
  When registry 以 fill/resolve mode 绑定 slot
  Then 只能补充空 slot 或解析既有 provider-neutral logical reference
  When registry 以 replace-ref mode 替换 reference
  Then source slot 必须显式声明 replaceable 且允许当前 scope
  And replacement 只影响当前 target render，不修改 source
  And 不得覆盖 concrete portable value、普通 authored 字段或任意配置正文
  When operator Agent 新增、修改或删除 registry entry
  Then 该动作必须进入绑定当前 registry revision/digest 与完整 action set 的 DEC-03D non-no-op plan
  And principal 批准当前精确 plan 后才能写入
  When registry revision、命中 entry 或 provider kind 变化
  Then 旧 plan/approval 失效并重新 plan
  When Mac 与 Windows 对同一 base slot 绑定不同本机值
  Then authored base revision 可以保持相同
  And 两台 host 不同步 registry、不生成跨机 binding 报告，也不创建第三 authored layer
  When slot 零匹配、provider locator 失效或权限不足
  Then 保持 unresolved/error evidence
  And required/optional、诊断与恢复行为必须遵守 DEC-06D
```

```gherkin
Scenario: 所有 report surface 从 schema 生成最小安全视图
  Given adapter/schema 已为 reportable 字段声明 portable-safe、local-sensitive、secret 或 unknown sensitivity
  And plan、diff、receipt、日志、错误与 explain 各有独立版本化 allowlist schema
  When Almagest 生成任一 report surface
  Then 必须先从 rich internal state 投影 safe view，再序列化、记录或返回
  And 不得先序列化完整对象再用字段名、正则或 best-effort scrub 脱敏
  When 字段 sensitivity 为 portable-safe
  Then plan/diff 或按 ID explain 可提供精确 before/after
  And compact summary、receipt 与常规日志仍只保存各自职责所需的最小结构
  When 字段 sensitivity 为 local-sensitive
  Then 默认 safe view 只返回 slot/entry ID、type、scope、change kind、状态和结构化 redaction marker
  And summary、plan/diff value、receipt、日志与错误不得包含绝对路径、账号/profile、provider locator、machine ID 或 local endpoint
  When principal 明确确认当前 host 上一个精确 explain field/slot
  And schema 证明该 local-sensitive 字段不是 secret
  Then 本次 explain 可以显示该单一字段
  And confirmation 必须绑定 current host、target、plan/explain identity、field/slot ID 与本次调用
  And 不得批量、通配、持久化、跨 host 或复用
  And reveal 结果不得进入 receipt、log 或 cache
  When 字段 sensitivity 为 secret
  Then 所有 surface 只能返回 absent、present、changed、invalid 或 permission_denied 等安全状态
  And secret value 不得进入任何 reportable object、hash、fingerprint、exception、trace、telemetry、cache key 或 reveal
  When 字段 sensitivity 缺失、不受支持或动态结构无法验证
  Then 值必须隐藏并返回 unknown_sensitivity/block
  And 不得退回 key-name regex、完整本地 debug output 或默认 non-secret
  When provider 返回包含 secret canary 的 stdout、stderr、exception message 或 response body
  Then 原始内容不得透传
  And adapter 只能输出 stable diagnostic code、provider kind、operation、safe status 与 allowlisted metadata
  And 无法证明安全的字段必须丢弃并标记 diagnostic_redacted
  When 同一 internal state 被投影到 plan、receipt、log 与 explain
  Then 每个 surface 只能取得自己的 allowlist 字段
  And 不得因复用同一序列化对象扩大披露
  When safe view 包含 Mac work-derived ID、状态、数量、digest 或 redaction metadata
  Then 它仍不得离开 Mac
  When consumer render/live 需要实际 secret material
  Then 该投影与写入不属于 report surface
  And 其安全合同仍由 DEC-08/10 决定
```

```gherkin
Scenario: 本机参数失败时类型化阻断并由 principal 现场决定修复
  Given Almagest 正在为当前 host 上一个 target 解析 typed slot、provider 或 required observation
  When required slot 零匹配
  Then 返回 missing_required_binding/block
  And 阻断依赖该 slot 的 target resolve、render 与 apply
  When 同一 slot/target 命中多个 binding
  Then 返回 ambiguous_binding/block
  And 不得猜测 scope precedence、provider order 或 last-writer
  When provider locator 失效、权限/登录不可用、value validation 失败、provider unavailable 或 required observation 不满足
  Then 分别返回稳定 typed diagnostic code 并阻断受影响 target
  And 不得采用环境变量、其它 provider、consumer live value、默认值、cache 或 last-known-good
  When source 将 slot 明确声明为 optional
  And 固定 adapter/schema 明确定义 deterministic safe omission
  Then 零匹配可以生成 optional_omitted
  And omission 必须逐项进入精确 plan 并由 principal 批准
  When source 未声明 optional 或 schema 无法证明 omission 安全
  Then 必须按 missing_required_binding/block 处理
  When Almagest 向 operator Agent 返回 failure 或 omission
  Then safe diagnostic 至少包含 stable diagnostic ID/code、target ID、slot/entry opaque ID、失败阶段、影响范围、固定输入 evidence 与 allowlisted resolution action kind
  And 所有字段必须遵守 DEC-06C，不得包含 secret、provider locator、本机路径、账号或 raw provider error
  And 同一次调用应返回不跨越安全边界即可确定的全部独立 blocker/omission
  When diagnostic 提供 create/update binding、修复 provider/权限、修改 source requirement 或 retry 等 resolution action
  Then action 只是供 operator Agent 向 principal 解释的受限选项，不构成执行授权
  And Almagest 不得自动执行、自动修 source、自动改 required 为 optional 或静默跳过
  When principal 选择一个精确修复动作
  Then 受管配置修改必须进入 DEC-03D 新 non-no-op plan
  And 外部 provider/权限修复必须由其 owner/tool 完成
  And 修复后必须重新读取 observation、resolve、validate 并生成新 plan
  And 旧 failure evidence、plan、approval、普通 acknowledgment 或 reveal 不得解除阻断
  When blocker 只影响一个 target
  Then 不依赖该 blocker 的只读 inventory、diff、explain 与健康 target 可以继续
  And 被阻断 target 必须保持零写入
```

```gherkin
Scenario: 按 logical asset 盘点 source 到 live 的配置阶段
  Given 当前 host/target 的 source、binding、adapter/schema 与受限 live discovery boundary 已固定
  When Almagest 生成一次 v1 stage inventory snapshot
  Then 必须分别生成 source、resolved、rendered 与 live stage records
  And binding 与 observation 必须作为 side facts 分栏，不得冒充 authored stage
  And record 主键语义必须包含 snapshot、stage、target ID、logical asset ID 与可选 stable subresource/item ID
  And record 必须包含 asset kind、presence/state、stage revision/digest 与直接上游 provenance reference
  When source invalid、binding unresolved、merge conflict、render unsupported 或 live missing/unreadable
  Then 对应 stage 必须生成 absent、blocked 或 unresolved record 及稳定 reason
  And 下游未产生不得被解释为 logical asset 从系统中消失
  When rendered artifact 已生成但 live 尚未写入或内容不同
  Then rendered 与 live 必须保留为两个独立 stage
  And 不得把 render success 写成 materialize success
  When live config item 存在且可以解析
  Then 结果最多证明当前 bounded live state 为 present/parsed
  And 不得宣称 consumer 已 loaded、registered、enabled、callable 或 observed-used
  When Later 的 DEC-11 probe 产生 effective evidence
  Then evidence 必须保存在独立 schema/namespace
  And 只能通过 target、logical asset/subresource、consumer version 与 probe identity 关联 v1 stage record
  And effective evidence 不得覆盖或反写 source、resolved、rendered、live
  When adapter 扫描 live
  Then 只能读取声明的 config roots、文件类型、config keys 与引用边界
  And 不得扩展为全磁盘、进程、package、cache、history 或 session 快照
  When 受限边界内发现无法映射 logical ID 的物理对象
  Then 可以保留 opaque observed identity 与 stage evidence
  And 不得自动赋予 logical identity、managed classification、source authority、adopt 或 delete 权限
  When snapshot 包含 payload、binding、secret、local-sensitive 或 work-derived facts
  Then inventory 默认只保存 identity、state、revision/digest 与 provenance reference
  And 精确内容只能经按 ID safe diff/explain 读取
  And 所有输出与驻留必须遵守 DEC-04D 和 DEC-06C
```

```gherkin
Scenario: Control ownership 与 integrity 独立分类且不授予自动处置权
  Given 07A inventory 已发现一个 source/resolved/rendered/live stage record 或 binding side-fact record
  When Almagest 可以用当前合法 source/registry 或固定 adapter/plan/receipt evidence 证明该 record 属于受管边界
  Then control_state 为 managed
  And managed 只表示可进入受管 plan，不构成写入批准
  When 正向 evidence 明确指向 consumer、vendor、plugin、package 或其它 external owner contract
  Then control_state 可以为 external-owned
  And 必须保存 external owner identity 与 ownership evidence reference
  And Almagest 只能只读盘点，不得 adopt、rewrite、move、deduplicate 或 delete
  When record 既无可验证 managed provenance，也无足够 external owner evidence
  Then control_state 必须为 unknown-owner
  And 不得因位于 config root、名称或内容相同、mtime、历史路径或曾被写入而猜测 owner
  And 任何可能覆盖、移动、接纳或删除它的动作必须阻断
  When ownership evidence 冲突、失效或无法按 07C 证明仍有效
  Then control_state 必须回到 unknown-owner
  And 不得默认 external-owned
  When record 实际存在且有且仅有一个合法当前上游关系
  Then integrity.link_state 为 linked
  When record 实际存在但没有合法当前直接 upstream relationship
  Then integrity.link_state 为 orphan
  When expected record 不存在
  Then 必须使用 07A presence=absent
  And 不得把 missing 误标为 orphan
  When 同一 stage/target logical identity 或声明为独占的 physical slot 有多个 claimant
  Then integrity.cardinality_state 为 duplicate
  And 不得自动选择 winner、shadow、merge 或删除副本
  When 一个 record 同时为 unknown-owner、orphan 且属于 duplicate group
  Then 三个事实必须同时保留，不得压成单一枚举
  When external-owned、unknown-owner、orphan 或 duplicate 不与 managed desired state 冲突
  Then 可以保持只读可见，不自动阻断整台 host
  When target action 会覆盖或删除这些 record，依赖 duplicate winner，或发生 shadow/collision
  Then 受影响 target action 必须阻断并向 principal 报告
  When principal 决定接纳一个 external-owned 或 unknown-owner record
  Then 不得直接翻转 classification flag
  And Agent 必须先修改合法 GitHub/Mac-local source 或 host-local binding
  And 形成新 revision 与 DEC-03D plan
  And 重新 inventory 后只能由新 provenance 自然得到 managed
```

```gherkin
Scenario: 用类型化证据信封区分直接观测、确定性推导与当前未知
  Given 07A inventory 正在为一个 stage/fact record 求值 claim
  When 声明的 collector/adapter 在当前 snapshot 和获准边界内直接读取目标
  And 固定 schema 成功解析或验证读取结果
  Then evidence level 为 observed
  And envelope 必须记录 subject/claim kind、method、collector/adapter/schema versions、snapshot、采集时间与安全 evidence reference
  When adapter 在边界内直接确认对象不存在
  Then 可以记录 observed absence
  When root 未知、权限拒绝、读取失败或解析失败
  Then evidence level 必须为 unknown 并带稳定 reason 与 attempt evidence
  And 不得把失败写成 observed absence
  When claim 只由当前有效的输入 evidence 通过命名且版本化的确定性规则得出
  Then evidence level 为 inferred
  And envelope 必须引用全部决定性 input evidence IDs 与 derivation rule version
  And 相同输入和版本必须产生相同结论
  And inferred 不得提升为 observed
  When 推导依赖概率、相似度、路径惯例、LLM 判断或未登记 fallback
  Then 该 claim 必须为 unknown
  And 不得输出主观 confidence score 冒充 evidence level
  When claim 的输入 evidence unknown、互相冲突、已过期或与 adapter/schema/consumer version 不兼容
  Then 当前 claim 必须为 unknown
  And 必须保留并引用原始或 stale envelopes，不得按最新时间或最高版本自动选 winner
  When evidence 对应 immutable revision-bound fact
  And 其输入 revision、schema/rule 与 policy 均未变化
  Then freshness policy 可以继续判定为 current
  When evidence 对应权限、登录、consumer version、active root 或 live state 等可变事实
  Then freshness policy 必须要求 current snapshot 或 adapter/policy 声明的最大年龄和失效条件
  And 不得使用覆盖所有 claim 的统一 TTL 或跨 host 时钟比较
  When action policy 明确要求 current observed evidence
  Then inferred、unknown 或 stale evidence 均不能满足该前置条件
  And 只阻断依赖该 claim 的写动作，安全 inventory/explain 与独立 target 可以继续
  When principal 或 operator Agent 接受风险或提供解释
  Then 不得直接把 evidence label 改成 observed 或 inferred
  And 必须取得新证据、修复合法输入，或使用 DEC-09/10 明确允许的降级计划
  When 证据摘要或按 ID 详情被返回
  Then 默认摘要只包含 level、freshness、reason 与 evidence ID
  And 完整 envelope 仍须遵守 DEC-04D/06C，不得泄漏 secret、locator、work 内容/元数据、原始 payload 或 raw error
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
- [ ] authored overlay 只有 GitHub base 与 Mac-local work 两层；host/consumer 环境差异、本机 binding、rendered/live/external-owned/unknown-owner 状态均不得取得 layer authority。
- [ ] merge 由版本化 schema 显式区分 atomic、granular map、set、keyed list 与 ordered list；缺可信 schema fail closed，缺失稳定 ID 或无效顺序只生成 typed collision，均不做通用 deep merge。
- [ ] 已形成实现归属评估的输入，但尚未替 principal 做技术选型。

## 本轮文档落盘验收

- [x] 用户原始目标已进入不可变 capture。
- [x] 16 项能力与依赖顺序完整记录。
- [x] 每项均列出独立决策轴，并预留 A/B/C/D 形式候选、推荐、决定、后果与验收位置。
- [x] PM issue 与 bundle 互相可定位。
- [x] Markdown、YAML、Git diff 与仓级检查通过。
