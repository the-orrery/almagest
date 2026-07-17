# Almagest Agent 配置控制面验收

## 成功口径

在任一声明 host 上，operator Agent 可以让 Almagest 完整盘点本机 Agent 配置，计算每个 consumer 的期望状态，零副作用展示差异，并在 principal 确认后安全修复和复验；Windows 全程无法观察 Mac-local work。

## 端到端验收场景

```gherkin
Scenario: 全部 Agent 配置进入注册与盘点
  Given 当前 host 已声明受支持的 consumer 和配置边界
  When operator Agent 请求 inventory
  Then 结果覆盖 skills、MCP、instructions、settings/profiles、hooks、plugins 配置和影响 active config 的 selector/binding
  And 每项受管配置都能追溯到 source revision、适用 target 和 ownership
  And live 中未登记、外部拥有、重复、缺失、不可读取或无法归属的对象不会从报告消失
  And 无法确认的事实返回 unknown 或 block，不得被写成 absent、managed 或 compliant
  And binary、process、session、cache、模型和完整主机环境不会被包装成受管配置
```

```gherkin
Scenario: Mac 将 GitHub base 与本地 work overlay 解析为本机目标
  Given Mac Codex 与 QoderCLI 已登记
  And GitHub personal/shared source 与 Mac-local work source 都有固定 revision
  When Almagest 计算两个 consumer 的期望配置
  Then 每个 consumer 的候选只来自 GitHub base 与 Mac-local work overlay
  And consumer、root、profile 和本机 binding 只影响选择与渲染，不取得 authored source authority
  And Codex 与 QoderCLI 可以生成不同物理格式
  And raw source 不被 consumer 投影反写
  And 相同固定输入重复计算得到相同目标结果
```

```gherkin
Scenario: Windows 只消费 GitHub base 且完全看不到 Mac work
  Given Windows Codex 与 Claude 已登记
  When Windows operator Agent 执行 inventory、plan、apply、verify 或 drift
  Then 目标状态只来自 GitHub personal/shared source
  And Windows 不查询、接收或推断 Mac-local work
  And 输出、日志、plan、receipt 和错误中不出现 work 的内容、名称、数量、路径、digest 或可推导元数据
  And Mac host 不会因为本次 Windows 操作被远程读取或修改
  When 任一候选 artifact 无法证明不含 work 信息
  Then 操作在写入或导出前阻断并报警
  And 普通变更批准不能绕过该阻断
```

```gherkin
Scenario: Dry-run 精确说明本机会发生什么且保持零写入
  Given source、target、adapter 和本机 inventory 已固定
  When operator Agent 请求 plan
  Then Almagest 返回新增、删除、修改、移动、mask、shadow、no-op 与 block 的紧凑摘要
  And 每项差异都能按稳定 ID 获取 before/after、source、target、原因和影响
  And plan 固定全部输入与 action set
  And live 配置、source、binding 和外部资产保持零变化
  And principal 不需要直接阅读原始配置或操作交互式 CLI
```

```gherkin
Scenario: 任何非 no-op 配置变更都由 principal 确认
  Given plan 至少包含一个写动作
  When operator Agent 请求 apply 但没有当前 plan 的 principal 批准
  Then Almagest 保持零写入并返回 approval-required
  When operator Agent 提交绑定 principal 决定、精确 plan、固定输入和完整 action set 的批准
  Then Almagest 只执行获批动作
  And 任一输入、target 或 action set 变化都会使旧批准失效
  And external-owned、unknown-owner、duplicate 或归属不明对象不会被自动覆盖、删除、deduplicate 或 adopt
  And receipt 分别记录 principal approver 与 operator Agent
```

```gherkin
Scenario: Source 保持权威且 live 不会反向成为 source
  Given live 状态与 owned source 不一致
  When operator Agent 请求解释或修复
  Then Almagest 将 live 视为观察状态而不是 source of truth
  When principal 确认期望状态不变且差异只是 live 漂移
  Then 新 plan 从现有 owned source 重新投影到 live
  When principal 确认期望状态本身需要变化
  Then Agent 修改合法 source、形成新 revision 并重新 plan
  And 不得把 live、rendered artifact、cache 或 consumer 当前结果自动提升为 authored source
  When principal 明确要求 import 或 adopt 某个 live 对象
  Then Agent 先生成可审阅的 source change
  And 只有 source revision 合法提交后，该对象才能在新 plan 中成为 managed
```

```gherkin
Scenario: Apply 后复验且失败可恢复
  Given principal 已批准当前精确 plan
  When Almagest 执行 apply
  Then 受影响的受管配置以可恢复方式写入
  And 未获批资源与不相关 target 保持不变
  And apply 后重新 inventory 并验证 live 与期望状态
  When 任一步失败或复验不通过
  Then 返回稳定失败状态、已执行动作、未执行动作和安全恢复入口
  And 不得把部分成功报告为 compliant
  And operator Agent 报警后由 principal 决定重试、回滚或修 source
```

```gherkin
Scenario: 漂移检查复用同一配置真相且不自动修复
  Given 某次 apply/verify 已成功
  When operator Agent、hook 或外部周期工具再次调用 drift check
  Then Almagest 使用当前 owned source 与本机 inventory 重新计算差异
  And 只报告当前 host 的 config、binding 和 projection drift
  And 不上传 receipt、不生成跨机比较、不远程检查另一台 host
  And 发现差异时返回可执行 plan 并报警
  And 在 principal 批准前保持零写入
  And consumer 是否实际加载、可调用或被使用不会被冒充为 v1 配置一致性结论
```

```gherkin
Scenario: Consumer 兼容细节由 adapter 和 fixture 兜底
  Given Codex、QoderCLI 或 Claude 的 root、precedence、frontmatter 或配置格式发生变化
  When 当前 adapter 无法证明与该 consumer/version 兼容
  Then 相关 target 的 render、plan 和 apply 阻断
  And inventory 与 explain 仍可返回已知事实和取证缺口
  And 实现者通过更新 adapter、版本声明和兼容 fixture 解决
  And 只有该变化会扩大产品范围、突破驻留边界、改变 source authority 或减少 principal 控制权时，才升级为产品决策
```

## 实现完成门禁

实现 issue 只有同时满足以下条件才能关闭：

1. 上述场景已转成自动化测试或可重复的实机验证；
2. Mac Codex/QoderCLI 与 Windows Codex/Claude 都有 inventory 和 dry-run 证据；
3. work 零离机具备负向泄漏测试；
4. 至少一个 add、change、remove、unknown-owner、partial failure 和 rollback 场景通过；
5. 所有非 `no-op` 写入均可证明绑定 principal 批准和精确 plan；
6. 仓级 lint、类型检查、单元测试与兼容 fixture 全部通过。
