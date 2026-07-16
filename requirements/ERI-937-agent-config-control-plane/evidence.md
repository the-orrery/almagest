# 当前证据

## 本轮交付

- 建立 `ERI-937`，将 Agent 配置控制面能力定义与 `ERI-936` 的 gaal 外部研究分离。
- 在 Almagest 受管 worktree 中建立需求 bundle。
- 固化用户目标、16 项能力、独立决策轴、依赖顺序、逐项拍板协议、初步验收和开放 RAID。
- 经对抗审阅后，去除 Almagest solution-owner 预设，修正决策轴协议、依赖顺序、按资产类型 overlay、consumer render/frontmatter、供应链信任、Effective 证据等级和 RAID。
- 未触达实现代码和 live 配置。

## 验证记录

| 检查 | 预期 | 实际结果 |
|---|---|---|
| 16 项编号完整性 | DEC-01—DEC-16 各出现一个总览项和一个决策卡 | 通过：总览 16、决策卡 16、独立决策轴 62 |
| YAML 基础检查 | `requirement.yaml` 可安全解析且 PM/slug 正确 | 通过：Ruby Psych safe load；`pm_id=ERI-937`，`slug=agent-config-control-plane` |
| 文档一致性 | 无旧 solution-owner 标题、旧 bundle slug 或“RAID 清零”口径 | 通过：`rg` 无命中；`git diff --check` 通过 |
| 仓级检查 | 文档新增不破坏现有测试与 lint | 通过：隔离 `XDG_CONFIG_HOME` 后 ruff、format、pyrefly 通过，pytest 31/31 通过 |
| Git 范围 | 只包含本需求 bundle | 通过：staged diff 仅 5 个 bundle 文件，共 462 行新增；无实现或 live 配置 |

## 验证边界

- 直接运行 `uv run poe check` 时，仓内既有测试读取了本机真实 `XDG_CONFIG_HOME`，`test_identity_source_missing_root_is_actionable_json` 预期 `missing-source-root`、实际得到本机 overlay 的 `missing-src`。这不是本轮文档变更引入的代码失败。
- 使用空目录隔离 `XDG_CONFIG_HOME` 后完整仓级检查通过；本轮没有修改测试或实现来掩盖该环境耦合。
- 首次 YAML 校验脚本未允许 Ruby `Date` 类型而停止；加入 `permitted_classes: [Date]` 后安全解析通过，属于验证脚本修正，不是 YAML 内容修复。

## 尚未产生的证据

- 16 项拍板结果：后续逐项写入 `design.md`。
- capability spec / ADR：所有相关决定稳定后再蒸馏。
- 实现与 runtime 验证：不属于本设计阶段。
