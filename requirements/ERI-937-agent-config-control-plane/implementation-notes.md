# 工程实现默认与升级门槛

## 用途

本文把产品契约翻译成工程约束。它不是 principal 决策清单；满足 `design.md` 与 `acceptance.md` 的前提下，实现者直接选择最小、确定、可验证的方案。

旧工作台中的 root、frontmatter、inventory、coverage、evidence、plan、apply 等细化内容只作为 Git 历史参考。除非在本文或测试中重新声明，否则不构成当前规范。

## 实现默认

### Source-first

- owned source 是唯一 authored authority；
- resolved、rendered、live、cache 和 runtime observation 都是派生或观察状态；
- 意图变化修改 source；live 漂移通过获批 plan 重新投影现有 source；
- live import/adopt 先生成 source change，再进入普通 plan；
- 外部 upstream 的发现和吸收由其它工具完成，Almagest 只消费固定 owned revision。

### 确定且可重放

- 相同 source、policy、adapter、binding 和 target 输入必须得到相同 desired/rendered 结果；
- plan 固定全部输入、action set 和版本，不能在 apply 时重新猜测；
- identity、revision、digest、provenance 和 diagnostic code 使用稳定机器字段；
- 不使用 path、mtime、内容相似度或 LLM 推断取得 ownership 或 mutation authority。

### 保守处理未知

- 缺 root、权限、binding、adapter capability 或完整 inventory 时返回 unknown/block；
- partial discovery 不得冒充 absent、unique winner 或 compliant；
- external-owned、unknown-owner、duplicate、orphan 默认只读；
- 不自动 adopt、deduplicate、删除、提权、扩扫或跨 host fallback。

### Consumer adapter 承担差异

每个 adapter 负责声明并测试：

- 支持的 consumer 产品与版本；
- 配置 roots、precedence、visibility 和 active profile 规则；
- skills/frontmatter、MCP、instructions、settings、hooks、plugins 的输入输出映射；
- safe diff、round-trip、lossy transform 和不兼容行为；
- Mac/Windows fixture 与 consumer 版本变化后的阻断。

raw source 保持 consumer-neutral；任何 lossy transform 都必须在 plan 中可见。adapter 失败只影响相关 target，不扩大成 host manager 或 runtime probe。

### Agent-first 机器接口

- 规范入口非交互、结构化、可脚本调用；
- 默认返回状态、计数、诊断码、阻断项和下一步 action IDs；
- 详细 diff、provenance、evidence 和 receipt 按稳定 ID 获取；
- principal 批准与 operator Agent 身份分开记录；
- 人用 TUI/GUI 可后置，不能形成第二套语义。

### 安全 Apply

- 只写获批 plan 中的 managed resources；
- 写入具备锁、幂等、原子边界、备份和可恢复失败状态；
- apply 前重新验证 plan 输入，apply 后重新 inventory；
- partial failure 明确区分已执行、未执行和恢复动作；
- work、secret/local-sensitive 内容在 plan、日志、receipt 和错误中使用安全视图。

### Drift 与 Evidence

- v1 比较 authored source、resolved/rendered、live 与必要 binding；
- runtime loaded/enabled/callable/observed-used 属 Later evidence；
- drift check 是可调用能力，不内置 daemon/scheduler 生命周期；
- 当前 host 的 receipt/evidence 留在本机，work 相关记录只留 Mac；
- 旧证据可以审计，但不能在输入或版本变化后继续驱动当前写入。

## 实现工作流

建议按以下依赖拆 issue，而不是继续创建 principal 决策卡：

1. **Registry 与 source model**：登记配置、targets、ownership、source revisions 和 host-local bindings；
2. **Inventory 与 adapters**：发现 live 配置，覆盖四个 consumer，建立 compatibility fixtures；
3. **Resolve 与 render**：计算 Mac/Windows 目标状态并生成 consumer artifact；
4. **Plan 与 approval**：产生结构化 dry-run，绑定 principal 批准；
5. **Apply 与 recovery**：安全写入、备份、复验和失败恢复；
6. **Drift 与 explain**：复用同一 inventory/plan engine 做本地对账和审计解释。

每个 issue 使用 `acceptance.md` 中相关端到端场景作为完成门禁。

## 何时升级给 Principal

| 发现 | 处理 |
|---|---|
| 两种 schema、数据库、序列化或目录布局都满足契约 | 工程侧选择更简单、可测试的一种 |
| consumer root/precedence/frontmatter 行为变化 | 更新 adapter 与 fixture；不升级 |
| adapter 无法读取某个 target | 返回 unsupported/unknown，先取证或修 adapter；不升级 |
| 新 consumer 或新配置域需要进入受管范围 | 升级产品决策 |
| 需要让 work 信息离开 Mac | 阻断并升级产品决策 |
| 需要把 live/external state 自动变成 source | 阻断并升级产品决策 |
| 需要自动删除、修复、远程执行或绕过 principal 批准 | 阻断并升级产品决策 |
| 既定产品约束彼此冲突、没有实现可以同时满足 | 带证据、选项和推荐升级 |

升级时只解释产品冲突、用户影响和推荐方案；不向 principal 倾倒内部 schema 或完整实现选项。
