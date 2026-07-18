---
description: "Almagest 当前主机只读 Inventory 契约：consumer adapter、证据、正交状态、覆盖度和安全输出。"
keywords: [almagest, inventory, adapter, codex, qodercli, claude, contract]
kind: spec
---

# Almagest Inventory contract

状态：生效。拍板来源：ERI-937。实现范围：ERI-946 的只读 Inventory 与 consumer adapter。适用于 `src/almagest/inventory.py`、`src/almagest/adapters/` 和 `almagest inventory`。

Inventory 只回答“当前主机上实际发现了什么、证据是否足够”。它不决定目标配置，不修改 live target，也不把 live 状态吸收成 source。

## 权威与证据边界

```text
Registry authored catalog       当前 consumer 证据       当前 host bindings
          │                            │                       │
          └──────────────┬─────────────┴───────────────┬───────┘
                         ▼                             ▼
                 consumer adapter               bounded reader
                         └──────────────┬──────────────┘
                                        ▼
                              InventorySnapshot
                         （观测事实，不是修复计划）
```

- **Registry** 是期望对象、分配关系和期望 mutation authority 的唯一权威。
- **ConsumerEvidence** 只证明当前主机上的产品、版本和格式与 adapter fixture 是否兼容，不是配置 authority。
- **Host binding** 只把语义 role 绑定到当前主机的 root、account 或 secret reference。
- **InventorySnapshot** 是一次只读观测；不得反向改写 Registry。
- Registry 中的 `almagest-managed` 只表示**期望由 Almagest 管理**。在没有 Apply receipt 证明前，live 对象必须保持 `unknown-owner`，不能通过同名、路径、内容或 symlink 猜成 `managed`。

## 正交状态

一个对象的状态不得压缩成单一枚举。以下维度必须独立表达：

| 维度 | 状态 | 含义 |
|---|---|---|
| presence | `present` / `absent` / `unknown` | 是否观测到对象。 |
| desired ownership | `almagest-managed` / `not-declared` / `not-applicable` | Registry 声明的期望 authority。 |
| live ownership | `managed` / `external-owned` / `unknown-owner` / `not-applicable` | 已证明的 live mutation provenance。 |
| readability | `readable` / `unreadable` / `invalid` / `unknown` | surface 是否能安全读取、解析。 |
| topology | `canonical` / `duplicate` / `orphan` / `unknown` | 对象与同类观测的结构关系。 |
| effective | `active` / `shadowed` / `ambiguous` / `unknown` | adapter precedence 是否足以判断生效项。 |
| coverage | `complete` / `partial` / `unknown` / `unsupported` | adapter 对一个 surface 的观测完备度。 |

`missing` 不是原始状态。只有 Registry 有期望对象、对应 kind 的全部 adapter surface 都是 `complete`、且没有 live 对象时，才能派生 `missing`。`partial`、`unknown`、`unreadable` 或 `invalid` 一律不能当作 `absent`。

`orphan` 需要可信的 Apply provenance。ERI-946 没有 receipt，因此只冻结状态模型，不凭路径或名称产生 orphan 结论。

## Consumer adapter

每个 adapter 固定以下契约：

- host platform、consumer identity、product、格式 fingerprint 和已验证版本前缀；
- 必须出现且只能无歧义匹配的一组 binding role；
- 每种配置 surface 的 root role、root-relative locator、读取模式和 namespace；
- 已知 precedence、外部拥有的 package root、必须存在的 frontmatter key；
- 每个 Registry asset kind 是可盘点还是明确 `unsupported`。

当前内置 adapter：

| Adapter | 必需 path role | 关键 surface |
|---|---|---|
| `codex.macos` | `codex.runtime-home` + `codex.user-home` | config、MCP、profile、hook、plugin、AGENTS、skill、active root |
| `qodercli.macos` | `qoder.user-home` **或** `qoder.work-home` | settings、MCP、hook、plugin、AGENTS、skill、active root |
| `codex.windows` | `codex.runtime-home` + `codex.user-home` | 与 Codex macOS 相同的 consumer 格式 |
| `claude-code.windows` | `claude.user-home` + `claude.state-file` | settings、MCP、hook、plugin、CLAUDE、skill、active root |

QoderCLI 的 personal 与 Mac-local work 配置是两个 Registry target，共用一个 adapter，但分别绑定 `qoder.user-home` 与 `qoder.work-home`。二者不是同一 target 上的 overlay，也不增加第五种 consumer。

`BindingDeclaration.role` 是 adapter 与 host binding 之间的语义接口。adapter 必须阻断未知 role、缺失 role、重复语义 role或多个 role set 同时匹配，不能回退到默认 home。

## 兼容证据

| 状态 | 条件 | Inventory 行为 |
|---|---|---|
| `proven` | product、format、版本 fixture 匹配，且证据来自当前 host | 允许语义解析。 |
| `host-unverified` | 只有 fixture，或证据未证明来自当前 host | 结构观测可继续，语义覆盖为 partial。 |
| `version-unverified` | product/format 匹配，但版本未进入 fixture | 结构观测可继续，语义覆盖为 partial 并告警。 |
| `identity-unverified` | 当前 target 没有 consumer 证据 | 阻断该 target。 |
| `unsupported` | product 或 format 不匹配，或没有 adapter | 阻断该 target。 |

fixture 只能防 adapter 自身漂移，不能替代 Windows 实机上的 product/version/root 证据。
仓内 `consumer-evidence.*.json.example` 故意使用 `fixture` 与 `host_verified: false`，复制后必须由 operator Agent 用当前主机取证结果替换；模板本身只能得到 partial，不能伪造 proven。

## 有界读取与 Windows 隔离

- reader 只能访问当前 target 显式 binding root，以及 Registry 已声明的 source root。
- adapter locator 必须是 portable 相对路径；`..`、绝对路径和 symlink 逃逸必须阻断或降为 partial。
- 单目录最多返回 512 个 entry，单文件最多读取 1 MiB；超限必须报告 partial。
- JSON 重复键、非法 JSON/TOML、非法 UTF-8、错误 node type 和不可读 surface 都必须 fail closed。
- Inventory 不扫描整台主机，不搜索候选 home，不读取未登记 root，不执行 consumer 命令。
- Windows 一旦收到任何 Mac-local layer 参数，必须在 Registry、binding、evidence、reader 创建以及任何 `stat/read/parse` 之前返回 `forbidden-local-layer`；输出不得泄漏 work 的名称、数量、路径或 revision。

## 输出与退出状态

机器输出可以包含：

- schema、snapshot/Registry/adapter revision；
- target、adapter、asset kind、语义 root role；
- root-relative locator、namespace、logical key；
- 正交状态、coverage、稳定 finding/diagnostic code；
- product/version 兼容证据。

机器输出不得包含绝对路径、文件内容、配置值、secret、命令参数、环境变量或 raw exception。

`status` 表示这次 Inventory 是否完整执行，不表示 live 配置已符合 Registry：

- `pass`：无阻断诊断，且所有可支持 surface 都是 complete；
- `partial`：没有阻断，但至少一个 surface 是 partial/unknown；
- `block`：Registry、证据、adapter、role 或 unsupported assignment 存在阻断问题。

CLI 对 `partial` 和 `block` 都返回非零，由现场 Agent 报告差异并等待 principal 决策。

## 执行入口

```bash
uv run almagest inventory adapters --json

uv run almagest inventory scan \
  --shared <shared-registry.json> \
  --local <mac-local-registry.json> \
  --host-bindings <host-bindings.json> \
  --consumer-evidence <consumer-evidence.json> \
  --json
```

Windows 不得传 `--local`。

## 实机证据状态

- macOS：Codex 与 QoderCLI 已完成当前主机只读盘点，adapter/product/version 兼容性已证明；未修改 live 配置。
- Windows：四 adapter 的跨平台行为已有 fixture 测试，但 fixture 不算 Windows 实机证据。Windows Codex 与 Claude 必须在 Windows 当前主机运行同一 Inventory 命令后，才能宣称 ERI-946 四端实机验收完成。

## 非目标

ERI-946 不做 adopt、resolve、render、diff 修复、deduplicate、plan、apply、rollback、drift 判定、runtime-loaded probe 或外部版本吸收。后续模块必须消费 Registry 与 InventorySnapshot，不能在 adapter 中实现第二套配置 authority。

## 格式依据

- QoderCLI Skills、MCP 与 hooks：<https://docs.qoder.com/en/cli/Skills>、<https://docs.qoder.com/en/cli/mcp-servers>、<https://docs.qoder.com/en/cli/hooks>
- Claude Code 配置目录与 precedence：<https://code.claude.com/docs/en/claude-directory>、<https://code.claude.com/docs/en/configuration>
