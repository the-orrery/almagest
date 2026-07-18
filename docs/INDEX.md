---
description: "almagest 的文档索引：项目架构、行为契约、运行知识和接手资料。源码、测试、配置和运行态数据不属于这里。"
keywords: [almagest, docs, architecture, CLI]
kind: index
---

# almagest docs

这里放 `almagest` 的长期文档。源码、测试、配置、lockfile 和运行态数据是工件，不直接作为文档；需要被长期查阅的知识应写成本目录下的 reference、spec、decision 或 runbook。

当前入口：

- [[architecture]]：仓库开发地图；说明项目是什么、模块怎么分、关键不变量、主路径和“改 X 去哪”。
- [[source-resolution-contract]]：skill source identity 与 host-local root overlay 的实现约束。
- [[registry-contract]]：Agent 配置 Registry、Mac-local overlay、host binding 与安全诊断约束。
- [[inventory-contract]]：当前主机只读盘点、consumer adapter、兼容证据、正交状态与安全输出约束。

维护规则：

- 新增稳定约束时，补 `*-contract.md` 或 `*-spec.md`，`kind: spec`。
- 新增架构取舍时，补 ADR/decision；不要把 why 写进 `architecture.md`。
- 新增操作流程时，补 runbook/how-to；不要把步骤堆进 `architecture.md`。
- 文档涉及可漂移事实时，应写明代码入口或重验命令。
