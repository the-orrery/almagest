---
description: "Almagest Agent 配置 Registry 契约：shared/Mac-local 分层、source authority、target、binding 与安全输出。"
keywords: [almagest, registry, source, overlay, binding, contract]
kind: spec
---

# Almagest Registry contract

状态：生效。拍板来源：ERI-937。实现范围：ERI-945 的 Registry/source model。适用于 `src/almagest/registry.py`、`almagest registry validate` 及其配置生产方。修改产品范围、work 驻留、source authority 或 principal 控制权必须重新拍板；其余 schema 细节由维护者通过代码、测试和本文档同步变更。

## 边界与术语

- **shared layer**：可进入 GitHub、由 Mac 与 Windows 共同消费的 authored 声明。
- **Mac-local layer**：只存在于指定 Mac host 的 authored work 声明；不是 shared layer 的覆盖补丁，只能追加新 ID 和 assignment。
- **owned source**：唯一 authored authority。Registry 登记 repository identity 与不可变 revision，但本阶段不证明 revision 已在磁盘物化。
- **host-local binding**：当前 host 为 path、account 或 secret reference 提供的本机值。binding 只补值，不取得 authored authority。
- **target**：一个 host 上的一个 consumer 实例。当前范围是 Mac 的 Codex/QoderCLI 与 Windows 的 Codex/Claude。
- **asset**：skill、MCP、instruction、settings、profile、hook、plugin、selector 或 binding 配置对象。
- **assignment**：asset 到 target 的显式关系。

## Registry 条款

| 条款 | 强制等级 | 约束 | 校验点 |
|---|---|---|---|
| RG-1 | MUST | 每个 source 必须声明 repository identity、完整 Git commit 或 SHA-256 revision、residency 和 `authored-owned` authority。 | 严格 schema 与 revision 测试。 |
| RG-2 | MUST NOT | target、binding、live target、rendered artifact 或 cache 不得成为 authored source。 | schema 固定 authority；后续 plan/apply 契约。 |
| RG-3 | MUST | shared layer 必须对其引用传递闭合，且不得包含或引用 Mac-local work source。 | shared closure 负向测试。 |
| RG-4 | MUST | Mac-local layer 必须绑定当前已声明的 Mac host；其 source、target、binding 和 assignment 只能属于该 host。 | local boundary 与 current-host 测试。 |
| RG-5 | MUST NOT | Windows loader 不得读取、stat、解析或推断任何 Mac-local layer；只要收到 local layer 参数就必须先阻断。 | Windows no-probe 测试。 |
| RG-6 | MUST | 多份 layer 只能按逻辑 ID 追加；任意重复 ID 必须阻断，不得按文件顺序覆盖。 | collision 测试。 |
| RG-7 | MUST | assignment 必须显式引用已登记 asset 和 target；同一 asset/target 对不得重复。 | 引用与重复测试。 |
| RG-8 | MUST | work asset 只能分配给其 Mac host 上的 Codex 或 QoderCLI target。 | residency 负向测试。 |
| RG-9 | MUST | host-local binding 只能使用 `path`、`account` 或 `secret-ref`；secret 只能登记 provider/reference，不得内联 value。 | discriminated schema 与 secret 负向测试。 |
| RG-10 | MUST | Registry revision 必须只由 canonical authored catalog 计算；JSON map/list 顺序不得改变 digest，本机 binding 值不得进入 digest。 | order-stability 与 revision-sensitivity 测试。 |
| RG-11 | MUST NOT | JSON 报告、错误与诊断不得回显输入、逻辑 ID、本机路径或 secret；只允许 schema version、状态、非敏感计数、catalog revision 和 allowlist 诊断。Windows 输出不得包含 work 名称、数量、路径、digest 或可推导元数据。 | safe-envelope 与 Windows no-probe 测试。 |
| RG-12 | MUST | 未知字段、重复 JSON key、未知 schema version、非 portable repository identity、相对 host path、缺 root、source path 逃逸、host/platform 不匹配或 host binding 不完整必须 fail closed。 | loader/source/binding/host 负向测试。 |
| RG-13 | MUST | Registry 支持的 asset kind 必须覆盖 skill、MCP、instruction、settings、profile、hook、plugin、selector 和 binding。 | asset-kind 参数化测试。 |

## 当前 target 矩阵

| Host platform | Consumer | Shared personal | Mac-local work |
|---|---|---:|---:|
| macOS | Codex | 是 | 是 |
| macOS | QoderCLI | 是 | 是 |
| Windows | Codex | 是 | 否 |
| Windows | Claude | 是 | 否 |

## 执行点

- `almagest registry validate --shared ... --host-bindings ... --json` 执行 loader、catalog 与当前 host binding 校验。
- `uv run poe check` 执行 lint、format、pyrefly 和全部测试。
- `registry.shared.json.example`、`registry.mac-local.json.example` 与两份 host-bindings 示例给配置生产方提供合法形状；示例不是 live 配置。

## 不属于本阶段

ERI-945 不做 live inventory、consumer capability probe、render、dry-run plan、apply/rollback、drift 或 source revision materialization 校验。这些能力必须消费本 Registry，不能另建第二套配置 authority。

## 豁免与变更

本契约不允许 work 离机、Windows 探测 local layer、live 自动晋升为 source 或隐式覆盖 ID。其他 schema 变更必须同时更新实现、示例、契约与自动化测试；与 `docs/source-resolution-contract.md` 冲突时，以更严格的驻留和不回显约束为准。
