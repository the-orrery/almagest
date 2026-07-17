---
description: "almagest 架构总览：项目定位、模块 codemap、核心不变量、关键路径和开发入口。"
keywords: [almagest, architecture, codemap, registry, CLI]
kind: reference
---

# almagest 架构

> 给新 session 的开发地图：这个仓是什么、各模块管什么、关键路径怎么走、改某类能力该从哪里入手。
> 本文档由 seed 模板生成，首次业务化后应按真实代码和领域语义维护。

## 1. 鸟瞰

`almagest` 是本机 Agent 配置控制面。当前已实现 portable Registry、Mac-local overlay、host-local binding 校验和旧 skill manifest 投影；inventory、consumer adapter、plan/apply 与 drift 仍由后续模块补齐。

## 2. 模块地图

| 模块 | 路径 | 职责 |
|---|---|---|
| 包入口 | `src/almagest/__init__.py` | 包版本和 import 入口。 |
| 配置 | `src/almagest/config.py` | `pydantic-settings` 配置入口，环境变量前缀为 `ALMAGEST_`。 |
| 日志 | `src/almagest/logging_setup.py` | structlog 配置；TTY 输出 console，非 TTY 输出 JSON。 |
| CLI | `src/almagest/cli.py` | Typer app 和 console-script 入口。 |
| Registry | `src/almagest/registry.py` | 装载 shared 与 Mac-local 声明，校验 source、target、ownership、assignment 和 host-local binding，生成稳定 catalog revision。 |
| source resolver | `src/almagest/source.py` | 定义 consumer-neutral source ref，读取旧 overlay，并阻止相对路径或 symlink 逃逸 source root。 |
| skill resolver | `src/almagest/skills.py` | 读取旧 manifest，并计划、校验、安装 lane symlink；复用 `source.py`，但尚未切换为 Registry control-plane 输入。 |
| telemetry | `src/almagest/telemetry.py` | 本地 SQLite 用量账本；记录调用、耗时、错误和输出样本。 |
| 测试 | `tests/` | pytest 测试。 |
| 工程配置 | `pyproject.toml` | 依赖、构建后端、poe tasks、ruff、pytest、coverage 配置。 |

## 3. 核心不变量

- **工程入口由 `pyproject.toml` 管理**。依赖、脚本和检查命令应在这里收口，避免散落 shell 脚本成为第二套入口。
- **`uv run poe check` 是默认质量门**。它串联 ruff check、format-check、typecheck 和 test；新增长期规则时应优先并入这个入口或明确说明为什么不能自动化。
- **ruff/pyrefly 不进 dev-deps**。ruff 由 `seed ruff` 通过 `uvx` 按共享 CI canonical 口径运行，pyrefly 走全局 `uv tool`；模板默认不把它们装进每仓 `.venv`，避免每个新仓重复拉二进制工具。
- **telemetry 必须 best-effort**。本地账本只服务工具改进，任何记录失败都不能改变主命令输出或 exit code。
- **CLI 输出是对外契约的一部分**。如果输出会被 agent 或脚本消费，改字段、格式和 exit code 前应补 spec 或测试。
- **portable manifest 与 host root 分离**。新 capability 的 source 用 repository identity + 相对路径表达；本机根目录只由 source-root overlay 提供。详见 [[source-resolution-contract]]。
- **authored source、host binding 与 live target 不能互相替代**。Registry 只登记 owned source；本机路径、账号与 secret reference 只补值，不取得 source authority；live 状态不反向成为 source。详见 [[registry-contract]]。
- **Windows 不探测 Mac-local layer**。只要 Windows 调用携带 local layer，loader 必须在读文件、取元数据或解析内容前阻断。
- **Registry layer 只追加、不覆盖**。shared 和 Mac-local 出现重复逻辑 ID 时必须阻断，不能用 overlay 顺序静默覆盖。
- **`docs/` 是本仓文档域**。耐用知识写进本目录；源码、运行态、raw asset 不属于这里。

## 4. 关键路径

### 一次 CLI 调用

1. console script 进入 `src/almagest/cli.py:run`。
2. `run` 把 Typer app 包进 `telemetry.run_instrumented`。
3. Typer 分发到具体 command。
4. command 调业务模块完成动作。
5. telemetry best-effort 写入本地 SQLite 账本。

### 一次 Registry 校验

1. `src/almagest/cli.py` 的 `registry validate` 接收 shared、可选 Mac-local 和当前 host bindings。
2. `src/almagest/registry.py:load_registry` 先执行物理 layer gate；Windows 在这里拒绝 local layer。
3. 严格 JSON/Pydantic loader 拒绝重复键、未知字段、错误 schema version 与错误 layer。
4. `assemble_registry` 执行 shared 闭包、add-only merge、引用、驻留和 target/consumer 校验，并对 authored catalog 生成稳定 revision。
5. `validate_host_bindings` 只为当前 host 校验所需 path、account、secret reference 和 source root。
6. CLI 只输出计数、catalog revision 和 allowlist 诊断码；不回显 ID、路径、输入或 secret。


## 5. 改 X 去哪

| 想改 / 加什么 | 从这里入手 | 备注 |
|---|---|---|
| 加 CLI 命令 | `src/almagest/cli.py` | 同步补测试；若输出给 agent 消费，补 spec。 |
| 改 Registry schema、驻留或 ownership | `src/almagest/registry.py` | 同步 `docs/registry-contract.md`、示例和 `tests/test_registry.py`。 |
| 改 source root 或逃逸防护 | `src/almagest/source.py` | 同步 `docs/source-resolution-contract.md`；兼容入口仍由 `skills.py` re-export。 |
| 增加受管配置种类 | `src/almagest/registry.py:AssetKind` | 这是产品范围变化，需要同步 ERI-937 契约。 |
| 接入 live inventory / adapter / plan | 新模块 | 不要塞进 Registry loader；分别由后续 ERI-946/948/949 实现。 |
| 改 telemetry | `src/almagest/telemetry.py` | 保持 best-effort 和本地-only。 |
| 加配置项 | `src/almagest/config.py` | 环境变量前缀为 `ALMAGEST_`。 |
| 改日志格式 | `src/almagest/logging_setup.py` | 注意 TTY 和非 TTY 两种输出。 |
| 改工程检查 | `pyproject.toml` | 同步 `README.md` 和 CI。 |
| 补长期知识 | `docs/` | reference 写当前事实，spec 写必须遵守的约束，ADR 写为什么这么选。 |

## 6. 非目标

- 本文档不是 README；安装和快速使用归 `README.md`。
- 本文档不是 ADR；方案取舍和历史原因归 decision/ADR。
- 本文档不是 spec；可单条违反的约束归 `*-contract.md` 或 `*-spec.md`。
- 本文档不是 runbook；连续操作步骤归 runbook/how-to。
- 当前 Registry 不发现 live 配置、不渲染 consumer 格式、不写目标文件，也不验证声明 revision 已在本机物化。
