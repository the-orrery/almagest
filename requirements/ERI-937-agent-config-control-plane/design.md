# Almagest Agent 配置控制面产品契约

## 文档契约

| 项 | 约定 |
|---|---|
| 读者动作 | principal 只确认产品能力、数据驻留、权威来源和写入权限；实现者据此直接设计和开发，不再把 schema、root、frontmatter 等工程细节逐项上交拍板 |
| 生命周期 | 本文是活的产品契约；产品边界变化时更新，工程实现细节不得反向扩张本文 |
| 交付形态 | 产品能力契约，不是逐项选型工作台，也不是实现方案 |
| 证据 | principal 对话快照、端到端验收场景、后续实现与实机证据 |
| Gate | 只有改变产品范围、驻留安全、source authority、破坏性权限或 principal 控制权时，才升级给 principal 决策 |

语域：中性、精确、面向 Agent。Almagest 的直接操作者是 AI Agent，不以人直接使用 CLI/TUI 的便利性为设计中心。

## 已确认的产品方向

> Almagest 是本机 Agent 配置控制面：登记所有受关注的 Agent 配置，固化期望状态，按 consumer 生成目标配置，对账 live 状态，并在有差异时由当前 operator Agent 报警、取得 principal 确认后修复和复验。

拍板人：principal，2026-07-17。

```text
注册配置与目标
    ↓
固化 source revision 与期望状态
    ↓
按本机 consumer 解析和生成配置
    ↓
dry-run / 对账 live
    ↓
无差异 ───────────────> 结束
    │
    └─ 有差异 → Agent 报警 → principal 确认
                                  ↓
                              apply + verify
                                  ↓
                           后续 drift 再报警
```

成功不是“Mac 与 Windows 文件完全一样”，而是每台机器上的每个 consumer 都符合自己的声明目标，同时 Mac-local work 内容始终不离开 Mac。

## 要解决的问题

同一套 Agent 能力被 Mac、Windows 和不同 consumer 消费，但配置分散在多个 source、目录和格式中。单独的 skill 安装器只能解决 skill 分发，consumer 原生配置只能说明单个产品，二者都不能回答：

1. 两台机器和每个 consumer 应当拥有哪些完整配置；
2. 当前 live 状态相对期望状态多了什么、少了什么、改了什么；
3. personal/shared 与 Mac-local work 如何组合且不越界；
4. 差异由谁批准、如何安全修复、如何证明修复成功；
5. 哪些对象受 Almagest 管理，哪些只是观察到但不得覆盖。

Almagest 填补的是跨 consumer 的配置控制闭环，不替代 `npx skills`、consumer 原生加载器、Git 或 secret provider；这些能力可以作为输入、适配器或执行依赖。

## 已声明目标

`consumer` 指消费配置的 Agent 产品实例；`target` 指当前 host 上一个 consumer 的受管目标；`live` 指目标位置中实际观察到的配置状态。

| Host | Consumer | 期望 source |
|---|---|---|
| Mac 工作机 | Codex | GitHub personal/shared base + Mac-local work overlay |
| Mac 工作机 | QoderCLI | GitHub personal/shared base + Mac-local work overlay |
| Windows | Codex | GitHub personal/shared base |
| Windows | Claude，具体产品待实机确认 | GitHub personal/shared base |

每次操作只作用于当前 host。Mac Agent 只操作 Mac 本机 Almagest，Windows Agent 只操作 Windows 本机 Almagest；不设置中央控制端，不远程操作另一台机器，也不生成跨机状态报告。

## “全部 Agent 配置”的边界

“全部”指所有会改变 Agent 行为、能力或配置选择的声明，不等于接管整台主机。

### 必须登记并治理

- skills：内容、元数据、启用/注册关系和目标 consumer 投影；
- MCP：server 声明、transport、command、参数、环境引用和启用关系；
- instructions：全局、profile、workspace、import/拼接关系；
- settings 与 profiles：consumer 可配置的行为、工具和策略项；
- hooks 与自动化配置：hook 声明、触发关系和顺序，不负责 hook 执行结果；
- plugins 配置：注册、启用和 consumer 配置，不负责 plugin package 安装升级；
- config selector/binding：会选择 active root、profile、workspace 或 settings source 的受管 wrapper、alias、启动参数和环境声明；
- host-local binding reference：本机路径、账号、secret reference 等配置补值关系，不接管 secret value。

### 必须盘点但不自动接管

- consumer 产品、版本、active roots、profile、workspace 和配置格式能力；
- live 文件、配置项和 consumer 原生/bundled/plugin 资产；
- external-owned、unknown-owner、duplicate、orphan 或无法读取的配置对象；
- 配置依赖是否存在、引用是否有效、目标是否可写。

观察到对象不等于获得修改权。外部或归属不明资产只有经过 principal 明确 import/adopt，形成合法 source revision 后，才能进入受管状态。

### 明确不负责

- Agent binary、plugin package、运行时和依赖的安装、升级或卸载；
- 进程、daemon、session、cache、模型和实际调用结果的生命周期；
- 与 Agent 配置选择无关的完整 shell、PATH、代理、系统服务和主机环境；
- secret value 的存储、轮换和生命周期；
- 外部版本的发现、拉取、评审、吸收和周期调度；
- 后台常驻调度器、中央 fleet 管理、远程执行和跨机报告。

外部工具可以周期性检查 upstream，但 Almagest 只消费已经被吸收到 owned source 的 revision。

## Source、Overlay 与驻留

### 权威来源

1. **GitHub personal/shared source**：Mac 与 Windows 都可消费。
2. **Mac-local work source**：只存在并只允许在 Mac 工作机上被消费。
3. **Host-local binding**：为合法声明补本机值或引用，不是 authored source。

live target、rendered artifact、cache、consumer 当前可见结果都不是 source of truth。意图需要变化时修改合法 source 并形成新 revision；只是 live 漂移时，在 principal 批准后把现有 source 重新投影到 live。只有 principal 明确要求 import/adopt，才能把 live 差异转化为新的 source revision。

### Overlay 结果

- Mac Codex/Qoder 的目标状态：GitHub base + Mac-local work overlay；
- Windows Codex/Claude 的目标状态：GitHub base；
- consumer、OS、host、profile 和 root 可以影响 selector 与渲染，但不能自行成为新的 authored layer；
- 不同 consumer 可以生成不同物理格式，raw source 不因投影而反写。

### Work 零离机

Mac-local work 的内容、名称、数量、digest、路径和可推导元数据都不得进入 GitHub、Windows、远端服务或跨机报告。无法证明安全时必须阻断，报警后由 principal 现场决定恢复动作；普通变更批准不能绕过该边界。

## 六项产品能力

### 1. 注册与盘点

Almagest 维护受管配置注册表，能够按当前 host/consumer 列出：

- 期望存在的配置、source revision、适用目标和 ownership；
- 当前 live 配置与必要的 target/binding 事实；
- 未登记、外部拥有、重复、缺失、不可读取或无法归属的对象。

盘点必须覆盖所有声明配置域；看不到或不确定时返回 unknown/block，不得把“没看到”写成“不存在”。

### 2. 解析与 Consumer 投影

Almagest 从合法 source 与 Mac-local overlay 计算每个 target 的期望状态，并生成 Codex、QoderCLI、Claude 各自需要的配置形态。consumer 的 root、precedence、frontmatter、JSON/TOML 和 import 规则由 adapter 负责，必须确定、可复现、可测试，并保留 source provenance。

### 3. Dry-run 与差异解释

任何写入前都能生成零副作用 plan，至少回答：

- 会新增、删除、修改、移动、mask、shadow 或阻断什么；
- before/after、来源、目标、原因和影响；
- 哪些输入、版本和 inventory 被固定；
- 哪些问题需要 principal 决定或先修复。

默认输出给 Agent 紧凑摘要；完整 diff 和证据按稳定 ID 获取，避免把全部细节塞入对话上下文。

### 4. Principal 批准后的安全实施

只读 inventory、plan、verify 和无差异结果不需要批准。任何非 `no-op` 写计划都必须先由 operator Agent 报警，并取得 principal 对当前精确 plan 的确认。

Almagest 只能执行获批 action set。输入、目标或 plan 变化后旧批准立即失效。不得自动覆盖、删除、adopt `external-owned`、`unknown-owner`、duplicate 或归属不明对象。

### 5. Verify 与漂移检查

apply 后必须重新盘点和验证 live 状态。后续由 operator Agent、hook 或外部周期工具调用同一检查入口；Almagest 不管理调度器生命周期。

发现漂移时返回结构化差异并报警，不自动修复。principal 仍按当前 plan 现场决定。consumer 是否实际加载、可调用或被使用属于 Later runtime evidence，不作为 v1 配置一致性的成功门槛。

### 6. 本地审计与解释

每次 plan/apply/verify 在当前 host 保留可解释记录，能够回答：

- 谁提出目标、谁批准、哪个 operator Agent 执行；
- 使用了哪些 source revision、target、adapter 和 plan；
- 做了什么、结果如何、为什么阻断或失败；
- 如何恢复、重试或修 source。

work 相关记录只留在 Mac，不上传或跨机汇总。

## 操作者与控制权

```text
Principal
  └─ 用自然语言给目标、处理歧义、批准写计划
      └─ Operator Agent（Codex / QoderCLI / Claude）
          └─ 调用 Almagest 的机器接口、解释结果、提交批准、驱动重试
              └─ Almagest 确定性 inventory / plan / apply / verify
```

principal 不需要直接编辑配置、解析原始 diff 或操作交互式 `[y/N]`。Almagest 的规范接口应稳定、非交互、机器可消费；TUI、dashboard 和 wizard 不是 v1 必需能力。

## Principal 与工程实现的决策边界

### 必须升级给 Principal

只有以下变化需要新的产品拍板：

1. 增删受管配置类型、consumer、host 或 v1/Later/Out 边界；
2. 改变 personal/work 驻留、跨机可见性或 secret 安全边界；
3. 改变 source of truth、live import/adopt 或 external ownership 规则；
4. 增加自动写入、删除、修复、远程执行，或减少 principal 对非 `no-op` 计划的控制。

### 工程侧直接决定

下列事项由实现者选择并用兼容 fixture、golden test 和失败用例证明，不再逐项请求 principal 选择：

- logical ID、revision、inventory、coverage、evidence 和 receipt 的 schema；
- root discovery、precedence、duplicate/shadow 的内部表示；
- frontmatter 保留/翻译、MCP JSON/TOML、instructions 拼接和 settings 映射；
- adapter/plugin 接口、诊断码、hash、锁、原子写、备份和 rollback 机制；
- 命令形态、文件布局、序列化格式、分页和性能实现。

如果多个实现都满足本契约，工程侧直接选择成本最低、最容易验证的方案。只有无法同时满足产品约束时，才带着明确冲突和推荐方案升级。

## 被拒绝的产品方向

| 方向 | 拒绝原因 |
|---|---|
| 只用 skill installer 替代 Almagest | 只覆盖 skills，无法治理 MCP、instructions、settings、hooks、plugins、overlay、审批和 drift |
| 把 Almagest 扩成 Agent/主机生命周期管理器 | 超出“配置一致”目标，承担 binary、process、package、host 环境等不必要复杂度 |
| 建中央跨机控制面 | 与本机即时操作和 Mac work 零离机约束冲突 |
| 把 live 状态或 consumer 当前结果当 source | 无法稳定复现，容易把手工漂移反向固化为权威配置 |
| 所有差异自动修复 | 削弱 principal 控制权，可能覆盖外部或未知资产 |

## 后果与实现交接

- Almagest 继续建设，但定位从 skill 分发器/配置脚本升级为完整 Agent 配置控制面；
- `npx skills`、consumer 原生工具和现有 source repo 继续复用，不重复实现其成熟能力；
- 旧的 63 个决策轴不再作为 principal 待办。其中产品约束已经吸收到本文，root/schema/evidence 等细节降级为工程默认；
- 旧工作台内容保留在 Git 历史中供实现考古，不再维护为第二份真相；
- 下一阶段按注册盘点、adapter、plan/apply、verify/drift 拆实现 issue，并用 `acceptance.md` 作为完成门禁。

当前没有待 principal 拍板的产品 RAID。以下只是实现前需要在对应 host 取证的事实，不构成产品方向问题：

- Windows 上 Claude 的具体产品、版本和 active roots；
- 四个 consumer 当前版本、配置入口、优先级和格式能力；
- Mac/Windows 现有 live 配置的完整 inventory 与 ownership；
- 各 consumer adapter 的跨 OS fixture 和 round-trip 证据。
