# almagest

## Install

Production installs use the `almagest-<os>-<arch>` asset and `SHA256SUMS` from
[GitHub Releases](https://github.com/the-orrery/almagest/releases). The frozen
binary does not need Python, `uv`, or a local source checkout. Current targets
are macOS arm64 and Linux x86_64 (built on Ubuntu 22.04).

Run `./scripts/build-release.sh` for a local build. Pull requests build and
smoke-test both targets; a matching `v<project.version>` tag publishes an
immutable release.



## 开发

    uv sync                # 开发依赖留在仓内 .venv
    uv run poe check       # ruff check + format-check + typecheck + test

## 运行

    uv run almagest

## 文档

    docs/INDEX.md          # 文档入口
    docs/architecture.md   # 开发地图

> 由 [seed](https://github.com/the-orrery/seed) 模版生成；后续一致性靠 CI 和本地审计维护，不做模版回灌。
