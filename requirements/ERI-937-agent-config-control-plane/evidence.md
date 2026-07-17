# Almagest Agent 配置控制面产品契约证据

## 证据来源

| 来源 | 作用 |
|---|---|
| `capture/user-goal.md` | 保存最初“先列能力、逐项拍板、再决定建设方式”的诉求 |
| `capture/product-direction-2026-07-17.md` | 保存 principal 对过度细化的纠正和最终产品目标 |
| `design.md` | 当前产品能力、边界、权威来源、控制权与工程升级门槛 |
| `acceptance.md` | 端到端成功口径与实现完成门禁 |
| `docket:ERI-937` | 工作状态、过程决定、验证和后续实现拆分 |

## 已确认的产品决定

| 决定 | 当前结论 | 证据状态 |
|---|---|---|
| 产品定位 | Almagest 是本机 Agent 配置控制面，不是 skill installer，也不是 host/runtime manager | principal 已确认 |
| 配置范围 | 登记并治理 skills、MCP、instructions、settings/profiles、hooks、plugins 配置及 active config selector/binding | principal 已确认“全部 Agent 配置”；具体 schema 归工程 |
| Host/consumer | Mac：Codex + QoderCLI；Windows：Codex + Claude | principal 已确认；Windows Claude 具体产品待实机取证 |
| Source topology | GitHub personal/shared 供两机消费；Mac-local work 只在 Mac 参与 overlay | principal 已确认 |
| 驻留边界 | work 内容和元数据零离机；不做中央控制、远程执行或跨机报告 | principal 已确认 |
| Source authority | owned source 是配置真相；意图变化修改 source，live 漂移重新投影，import/adopt 必须显式 | principal 已确认 |
| 操作模型 | AI Agent 直接操作 Almagest；所有非 `no-op` 变更先报警并由 principal 确认 | principal 已确认 |
| 漂移策略 | 有差异就报警，由 principal 现场决定；Almagest 不自动修复、不管理周期调度器 | principal 已确认 |

## 决策层级纠正

早期工作台将能力拆成 16 张卡、63 个独立决策轴，并要求 principal 逐项选择 A/B/C/D。该方法完整但层级错误：它把 root precedence、frontmatter transform、coverage/evidence schema、adapter 字段等工程实现问题升级成产品决策，增加了不必要的认知成本。

2026-07-17，principal 明确纠正：

> 我的想法其实很简单，就是能够把两边的 agent 的配置全部固化、管理、注册起来。

当前处理方式：

1. 原逐轴工作台停止维护，不再把剩余 35 个轴交给 principal；
2. 产品约束被蒸馏进 `design.md`；
3. 工程细节归入 `implementation-notes.md` 的默认原则和升级门槛；
4. 旧细节保留在 Git 历史中供实现考古，但不再构成 principal 的不可变拍板；
5. 后续只有产品范围、安全驻留、source authority、破坏性权限或 principal 控制权发生变化时才升级。

## 当前验证记录

| 检查 | 预期 | 结果 |
|---|---|---|
| 产品契约聚焦 | 主文档不再包含 16 卡/63 轴逐项拍板协议 | 通过：`design.md` 230 行；当前契约与工程附录中无旧决策卡/逐项协议标题 |
| 能力闭环 | register → resolve/render → dry-run → approve/apply → verify/drift → explain 完整 | 通过：六项产品能力均有独立职责和安全边界 |
| In/Out 明确 | 全部 Agent 配置与 binary/process/host/runtime 边界可区分 | 通过：8 类必须治理、4 类必须盘点和 6 类明确不负责对象已列出 |
| 两机驻留 | Mac 双 source、Windows 单 source、work 零离机 | 通过：四个 target 与两类 source 映射完整；Windows 负向场景明确零 work 可见性 |
| 决策升级门槛 | principal 与工程实现的职责边界明确 | 通过：4 类产品升级条件、工程默认和实例表均已写入 |
| 端到端验收 | 场景覆盖 inventory、overlay、隔离、plan、approval、apply、drift、adapter | 通过：Gherkin 场景及代码块 9/9，另有 6 项实现完成门禁 |
| YAML identity | `pm_id=ERI-937`、bundle slug 不变 | 通过：Ruby Psych safe load；title 已改为产品契约，PM/slug 保持不变 |
| 仓级回归 | lint、格式、类型检查与测试不受文档重构影响 | 通过：ruff、format、Pyrefly 通过，pytest 31/31 通过 |

## 证据边界

本 issue 当前只完成产品需求与契约重构，不代表 Almagest 已实现上述能力，也不代表当前 Mac/Windows 配置已完成迁移。以下证据必须由后续实现 issue 产生：

- 四个 consumer 的真实版本、roots、formats 与 current inventory；
- personal/shared 与 Mac-local work source registry；
- consumer adapter 和跨 OS compatibility fixtures；
- dry-run、approval、apply、verify、rollback 的自动化证据；
- work 泄漏负向测试；
- 本地 drift check 与结构化 explain/receipt。

## 当前未决项

没有待 principal 决定的产品 RAID。

实现前仍需取证 Windows Claude 具体产品和四个 consumer 的当前配置入口；若事实可以在既定产品契约内适配，由工程侧直接处理，不再请求产品拍板。
