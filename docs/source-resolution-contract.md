---
description: "almagest skill source 解析契约：portable source identity、host-local root overlay 与 doctor JSON 的稳定约束。"
keywords: [almagest, skills, source, manifest, contract]
kind: spec
---

# almagest source resolution contract

状态：生效。适用范围：`almagest` 读取的所有 `skills.json` manifest、Registry asset、source-root overlay，以及对应 JSON 消费方。变更须经维护者审阅，并同步实现、测试与示例。

## 边界与术语

- **路径型 source**：旧 manifest 中的字符串 `source`，由当前主机直接展开。它仅为向后兼容保留。
- **逻辑 source ref**：`{"repository": "<identity>", "path": "<relative-path>"}`。它不包含本机根路径。
- **source-root overlay**：主机本地 `repository identity -> 本机目录` 映射。默认文件为 `$XDG_CONFIG_HOME/almagest/source-roots.json`，可由 `ALMAGEST_SOURCE_ROOTS` 指向其他文件。
- **portable manifest**：只含逻辑 source ref、lane 与 capability 信息的 manifest；不承担主机路径、凭证或 runtime 状态。

## 条款

| 条款 | 强制等级 | 约束 | 校验点 |
|---|---|---|---|
| SR-1 | MUST | 路径型字符串 source 必须保持既有展开与安装行为。 | 旧 manifest 的 CLI 回归测试。 |
| SR-2 | MUST | 逻辑 source ref 必须同时包含非空 `repository` 与相对 `path`。 | Pydantic 解析与 `skills.plan`。 |
| SR-3 | MUST | 逻辑 source ref 的根目录必须只从 host-local overlay 读取，不得从 portable manifest 推导。 | `load_source_roots` 与 identity-source 测试。 |
| SR-4 | MUST NOT | 逻辑 source ref 解析后不得逃逸其映射 root；`..` 或 symlink 导致的越界必须失败。 | `source-path-escape` 诊断测试。 |
| SR-5 | MUST | 缺少 repository root 时，安装与校验必须返回 `missing-source-root`，不得 fallback 到其他 root 或旧 workspace 路径。 | `doctor --json` 测试。 |
| SR-6 | MUST | `almagest doctor --json` 必须输出稳定 JSON，含 `schema_version`、总体 `status`、逐项 `checks` 与汇总 `summary`。 | CLI JSON 测试。 |
| SR-7 | MUST NOT | `doctor --json` 不得回显路径型 source 的原始本机路径；其 `source_ref` 必须为 `legacy-path`。 | JSON 输出 review 与测试。 |
| SR-8 | SHOULD | 新建或迁移 capability 应使用逻辑 source ref；路径型 source 只用于未迁移的兼容项。 | manifest review。 |
| SR-9 | MUST | Registry host 校验必须显式传入当前 host bindings 中的 source roots，不得读取旧环境 overlay 作为隐式 fallback。 | `validate_host_bindings` 与 Registry 测试。 |

## 失败代码

| detail_code | 含义 | 处理方 |
|---|---|---|
| `missing-source-root` | 本机未配置该 repository identity 的 root。 | host adapter / 本机配置。 |
| `source-path-escape` | relative path 或已存在的 symlink 越出 root。 | manifest 作者。 |
| `source-resolution-failed` | 文件系统错误或 symlink loop 使路径无法安全解析。 | 当前 host operator。 |
| `missing-src` | root 已解析，但目标目录不存在。 | source repository 维护者。 |
| `unknown-lane` | capability 引用的 lane 未在 manifest 中声明。 | manifest 作者。 |

## 豁免与变更

路径型 source 的存量兼容是唯一默认豁免；不得为新 capability 新增绝对路径。任何新增 source 解析模式、JSON 字段或失败代码，必须先更新本契约与 CLI 测试，再合入实现。Registry 的 layer、authority、target 与安全输出约束见 [[registry-contract]]。
