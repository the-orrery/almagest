# almagest



## 开发

    # 一次性(全机共用): seed 提供 canonical 本地 ruff; pyrefly 走全局工具
    uv tool install git+https://github.com/the-orrery/seed.git
    uv tool install pyrefly
    uv tool install pre-commit --with pre-commit-uv

    uv sync                # 各仓 .venv 只装纯 Python 依赖
    uv run poe check       # ruff check + format-check + typecheck + test

## 运行

    uv run almagest

## 文档

    docs/INDEX.md          # 文档入口
    docs/architecture.md   # 开发地图

> 由 [seed](https://github.com/the-orrery/seed) 模版生成；后续一致性靠 CI 和本地审计维护，不做模版回灌。
