---
description: "almagest 架构总览：项目定位、模块 codemap、核心不变量、关键路径和开发入口。"
keywords: [almagest, architecture, codemap, CLI, telemetry]
kind: reference
---

# almagest 架构

> 给新 session 的开发地图：这个仓是什么、各模块管什么、关键路径怎么走、改某类能力该从哪里入手。
> 本文档由 seed 模板生成，首次业务化后应按真实代码和领域语义维护。

## 1. 鸟瞰

`almagest` 是一个CLI 工具。工程栈由 seed 模板提供：uv、uv_build、ruff、pyrefly、pytest、poethepoet、pydantic-settings、structlog、typer 和本地 telemetry。

## 2. 模块地图

| 模块 | 路径 | 职责 |
|---|---|---|
| 包入口 | `src/almagest/__init__.py` | 包版本和 import 入口。 |
| 配置 | `src/almagest/config.py` | `pydantic-settings` 配置入口，环境变量前缀为 `ALMAGEST_`。 |
| 日志 | `src/almagest/logging_setup.py` | structlog 配置；TTY 输出 console，非 TTY 输出 JSON。 |
| CLI | `src/almagest/cli.py` | Typer app 和 console-script 入口。 |
| telemetry | `src/almagest/telemetry.py` | 本地 SQLite 用量账本；记录调用、耗时、错误和输出样本。 |
| 测试 | `tests/` | pytest 测试。 |
| 工程配置 | `pyproject.toml` | 依赖、构建后端、poe tasks、ruff、pytest、coverage 配置。 |

## 3. 核心不变量

- **工程入口由 `pyproject.toml` 管理**。依赖、脚本和检查命令应在这里收口，避免散落 shell 脚本成为第二套入口。
- **`uv run poe check` 是默认质量门**。它串联 ruff check、format-check、typecheck 和 test；新增长期规则时应优先并入这个入口或明确说明为什么不能自动化。
- **ruff/pyrefly 不进 dev-deps**。ruff 由 `seed ruff` 通过 `uvx` 按共享 CI canonical 口径运行，pyrefly 走全局 `uv tool`；模板默认不把它们装进每仓 `.venv`，避免每个新仓重复拉二进制工具。
- **telemetry 必须 best-effort**。本地账本只服务工具改进，任何记录失败都不能改变主命令输出或 exit code。
- **CLI 输出是对外契约的一部分**。如果输出会被 agent 或脚本消费，改字段、格式和 exit code 前应补 spec 或测试。
- **`docs/` 是本仓文档域**。耐用知识写进本目录；源码、运行态、raw asset 不属于这里。

## 4. 关键路径

### 一次 CLI 调用

1. console script 进入 `src/almagest/cli.py:run`。
2. `run` 把 Typer app 包进 `telemetry.run_instrumented`。
3. Typer 分发到具体 command。
4. command 调业务模块完成动作。
5. telemetry best-effort 写入本地 SQLite 账本。


## 5. 改 X 去哪

| 想改 / 加什么 | 从这里入手 | 备注 |
|---|---|---|
| 加 CLI 命令 | `src/almagest/cli.py` | 同步补测试；若输出给 agent 消费，补 spec。 |
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
