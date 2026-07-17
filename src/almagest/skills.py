"""skills.json 索引的加载、规划、校验与安装。

almagest 是 lane-中立的 skill 索引+安装器:读 skills.json(每条 = skill 名 →
{源目录, lanes, 公私}),把每个 skill 整目录 symlink 进每个目标 lane 的 skills
目录。lane → 目标基目录的映射也在 skills.json 里,加 lane 不用改代码。
一个逻辑 lane 可以映射到多个实际 runtime 目录。
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from pydantic import BaseModel

from almagest.source import (
    DEFAULT_SOURCE_ROOTS_ENV,
    SourceRef,
    SourceResolution,
    load_source_roots,
    resolve_source,
    source_reference,
    source_roots_path,
)

__all__ = [
    "DEFAULT_SOURCE_ROOTS_ENV",
    "SourceRef",
    "SourceResolution",
    "load_source_roots",
    "resolve_source",
    "source_reference",
    "source_roots_path",
]

DEFAULT_MANIFEST_ENV = "ALMAGEST_MANIFEST"
LaneTarget = str | list[str]


class Skill(BaseModel):
    name: str
    source: str | SourceRef
    lanes: list[str]
    visibility: str = "private"


class Manifest(BaseModel):
    lanes: dict[str, LaneTarget]
    skills: list[Skill]


def _expand(p: str) -> Path:
    return Path(p).expanduser()


def _lane_targets(raw: LaneTarget) -> list[Path]:
    if isinstance(raw, str):
        return [_expand(raw)]
    return [_expand(item) for item in raw]


def manifest_path() -> Path:
    """manifest 落点:$ALMAGEST_MANIFEST 覆盖,否则 XDG 配置目录。
    引擎刻意不内嵌任何数据/本机路径——真 manifest 在私有数据仓,经 env 或
    $XDG_CONFIG_HOME/almagest/skills.json(惯例软链)指过来。"""
    override = os.environ.get(DEFAULT_MANIFEST_ENV)
    if override:
        return _expand(override)
    config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config_home).expanduser() / "almagest" / "skills.json"


def load(path: Path | None = None) -> Manifest:
    target = path or manifest_path()
    return Manifest.model_validate(json.loads(target.read_text()))


# 安装动作的状态:
#   ok            target 已是指向 source 的 symlink,无需动作
#   create        target 不存在,要新建 symlink
#   repoint       target 是 symlink 但指向别处,要重指
#   replace-dir   target 是真目录(非 symlink),要替换成 symlink(需 --force / 非空真内容时拒)
#   missing-src   源目录不存在(配置错)
#   unknown-lane  skill 的 lane 不在 manifest.lanes 里
class LinkOp(BaseModel):
    skill: str
    lane: str
    source: Path | None = None
    source_ref: str = ""
    target: Path
    status: str
    current: str | None = None

    @property
    def needs_change(self) -> bool:
        return self.status in {"create", "repoint", "replace-dir"}


class ActiveOp(BaseModel):
    lane: str
    target: Path
    status: str
    current: str | None = None


class CompositionSnapshot(BaseModel):
    lane: str
    target: Path
    expected: set[str]
    actual: set[str]


def plan(m: Manifest) -> list[LinkOp]:
    """只读:逐 (skill, lane) 算出当前 vs 目标,给出动作状态。不碰文件系统。

    同一 target 只产一条 op:一个 runtime 目录可被同一 skill 的多个 lane 共喂
    (如 Codex 单目录同时收 personal+work),否则 dry-run plan 会重复打印、verify
    的 healthy 计数会虚高。
    """
    ops: list[LinkOp] = []
    seen: set[Path] = set()
    for sk in m.skills:
        resolution = resolve_source(sk.source)
        src = resolution.path
        for lane in sk.lanes:
            raw_base = m.lanes.get(lane)
            if raw_base is None:
                ops.append(
                    LinkOp(
                        skill=sk.name,
                        lane=lane,
                        source=src,
                        source_ref=resolution.reference,
                        target=Path(),
                        status="unknown-lane",
                    )
                )
                continue
            for base in _lane_targets(raw_base):
                target = base / sk.name
                if target in seen:
                    continue
                seen.add(target)
                current = str(target.readlink()) if target.is_symlink() else None
                if resolution.status != "ok":
                    status = resolution.status
                elif src is None or not src.exists():
                    status = "missing-src"
                elif target.is_symlink():
                    status = "ok" if Path(current or "") == src else "repoint"
                elif target.exists():
                    status = "replace-dir"
                else:
                    status = "create"
                ops.append(
                    LinkOp(
                        skill=sk.name,
                        lane=lane,
                        source=src,
                        source_ref=resolution.reference,
                        target=target,
                        status=status,
                        current=current,
                    )
                )
    return ops


def _is_shallow_managed_dir(d: Path) -> bool:
    """真目录是否「浅」——只含 symlink(典型:目录 + 内部 SKILL.md symlink),可安全替换。
    含真文件则不安全,拒绝自动替换。"""
    try:
        return all(child.is_symlink() for child in d.iterdir())
    except OSError:
        return False


def apply(m: Manifest, *, force: bool = False) -> list[LinkOp]:
    """落地:对 needs_change 的项建/重指 symlink。返回实际改动的 ops。
    real-dir target 仅在「浅」(只含 symlink)或 force 时替换,否则保留 replace-dir 状态不动。"""
    changed: list[LinkOp] = []
    for op in plan(m):
        if op.status in {
            "missing-src",
            "missing-source-root",
            "source-path-escape",
            "unknown-lane",
            "ok",
        }:
            continue
        op.target.parent.mkdir(parents=True, exist_ok=True)
        if op.target.is_symlink() or op.target.is_file():
            op.target.unlink()
        elif op.target.is_dir():
            if not (force or _is_shallow_managed_dir(op.target)):
                continue  # 含真文件,拒绝自动替换;留待人工/--force
            shutil.rmtree(op.target)
        op.target.symlink_to(op.source, target_is_directory=True)
        changed.append(op)
    return changed


def verify(m: Manifest) -> list[LinkOp]:
    """返回所有「不健康」的 op(非 ok)。空列表 = 全绿。"""
    return [op for op in plan(m) if op.status != "ok"]


def _expected_by_base(
    m: Manifest, *, expected_manifest: Manifest | None = None
) -> tuple[dict[Path, set[str]], dict[Path, str]]:
    expected_by_base: dict[Path, set[str]] = {}
    lane_by_base: dict[Path, str] = {}
    for lane, raw_base in m.lanes.items():
        for base in _lane_targets(raw_base):
            expected_by_base.setdefault(base, set())
            lane_by_base.setdefault(base, lane)
    source = expected_manifest or m
    for sk in source.skills:
        for lane in sk.lanes:
            raw_base = source.lanes.get(lane)
            if raw_base is None:
                continue
            for base in _lane_targets(raw_base):
                if base in expected_by_base:
                    expected_by_base[base].add(sk.name)
    return expected_by_base, lane_by_base


def _is_ignored_active_entry(
    name: str,
    *,
    allow_extra: set[str],
    ignore_dot_entries: bool,
) -> bool:
    return (ignore_dot_entries and name.startswith(".")) or name in allow_extra


def active_problems(
    m: Manifest,
    *,
    allow_extra: set[str] | None = None,
    ignore_dot_entries: bool = True,
    expected_manifest: Manifest | None = None,
) -> list[ActiveOp]:
    """扫描 lane 目录里的 active entry,找出 manifest 外的额外入口。

    常规 verify 只证明 manifest 内的 symlink 健康;strict-active 额外证明
    目标目录没有未登记的 skill 入口。dot entries 默认跳过,用于避开
    .git/.DS_Store 以及 agent 自带系统目录。

    expected 按「目标目录」取并集而非按 lane:一个 runtime 目录可被多个逻辑
    lane 共喂(如 Codex 单目录同时收 personal+work),逐 lane 算 expected 会把
    同目录里属于别的 lane 的 entry 误报成 unmanaged-active(进而被 prune 误删)。
    当调用方传入 lane-filtered manifest 时,可用 expected_manifest 提供完整
    manifest;扫描范围仍来自 m,但共享目录的 expected 使用完整并集。
    """
    allowed = allow_extra or set()
    expected_by_base, lane_by_base = _expected_by_base(
        m, expected_manifest=expected_manifest
    )

    problems: list[ActiveOp] = []
    for base, expected in expected_by_base.items():
        if not base.exists():
            continue
        for target in sorted(base.iterdir(), key=lambda p: p.name):
            name = target.name
            if name in expected or _is_ignored_active_entry(
                name, allow_extra=allowed, ignore_dot_entries=ignore_dot_entries
            ):
                continue
            current = str(target.readlink()) if target.is_symlink() else None
            problems.append(
                ActiveOp(
                    lane=lane_by_base.get(base, "?"),
                    target=target,
                    status="unmanaged-active",
                    current=current,
                )
            )
    return problems


def composition_snapshots(
    m: Manifest,
    *,
    allow_extra: set[str] | None = None,
    ignore_dot_entries: bool = True,
) -> list[CompositionSnapshot]:
    """返回每个 runtime skills 目录的 expected/actual skill 集。

    expected 按目标目录取所有 lane 的并集,即 base union overlay;actual 只看目录入口名,
    dot entries 和显式 allow-extra 不参与 composition 判定。
    """
    allowed = allow_extra or set()
    expected_by_base, lane_by_base = _expected_by_base(m)
    snapshots: list[CompositionSnapshot] = []
    for base, expected in expected_by_base.items():
        actual: set[str] = set()
        if base.is_dir():
            actual = {
                target.name
                for target in base.iterdir()
                if not _is_ignored_active_entry(
                    target.name,
                    allow_extra=allowed,
                    ignore_dot_entries=ignore_dot_entries,
                )
            }
        snapshots.append(
            CompositionSnapshot(
                lane=lane_by_base.get(base, "?"),
                target=base,
                expected=set(expected),
                actual=actual,
            )
        )
    return snapshots


def composition_problems(
    m: Manifest,
    *,
    allow_extra: set[str] | None = None,
    ignore_dot_entries: bool = True,
) -> list[ActiveOp]:
    """断言每个 runtime 目录实际 skill 集等于 base union overlays。"""
    allowed = allow_extra or set()
    problems: list[ActiveOp] = []
    for snapshot in composition_snapshots(
        m, allow_extra=allowed, ignore_dot_entries=ignore_dot_entries
    ):
        if not snapshot.target.exists():
            problems.append(
                ActiveOp(
                    lane=snapshot.lane,
                    target=snapshot.target,
                    status="missing-active-dir",
                )
            )
            continue
        if not snapshot.target.is_dir():
            problems.append(
                ActiveOp(
                    lane=snapshot.lane,
                    target=snapshot.target,
                    status="active-target-not-dir",
                )
            )
            continue
        for name in sorted(snapshot.expected - snapshot.actual):
            problems.append(
                ActiveOp(
                    lane=snapshot.lane,
                    target=snapshot.target / name,
                    status="missing-active",
                )
            )
        for name in sorted(snapshot.actual - snapshot.expected):
            target = snapshot.target / name
            current = str(target.readlink()) if target.is_symlink() else None
            status = (
                "dangling-active"
                if target.is_symlink() and not target.exists()
                else "unmanaged-active"
            )
            problems.append(
                ActiveOp(
                    lane=snapshot.lane,
                    target=target,
                    status=status,
                    current=current,
                )
            )
    return problems


def prune_active_symlinks(
    m: Manifest,
    *,
    allow_extra: set[str] | None = None,
    ignore_dot_entries: bool = True,
    expected_manifest: Manifest | None = None,
) -> list[ActiveOp]:
    """删除 manifest 外的 active symlink entry。

    只删 symlink;manifest 外真目录或真文件继续留给 strict-active 报告,避免误删用户数据。
    """
    pruned: list[ActiveOp] = []
    for op in active_problems(
        m,
        allow_extra=allow_extra,
        ignore_dot_entries=ignore_dot_entries,
        expected_manifest=expected_manifest,
    ):
        if op.target.is_symlink():
            op.target.unlink()
            pruned.append(op)
    return pruned
