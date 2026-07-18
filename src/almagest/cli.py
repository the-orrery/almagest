from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from almagest import inventory, registry, skills, telemetry
from almagest.logging_setup import setup_logging

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="almagest — 本机 Agent 配置控制面",
)
registry_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="严格加载并校验 authored Agent 配置 registry",
)
app.add_typer(registry_app, name="registry")
inventory_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="只读盘点当前 host 的 Agent 配置与 adapter coverage",
)
app.add_typer(inventory_app, name="inventory")


def _doctor_report(
    manifest: skills.Manifest, *, allow_extra: set[str]
) -> tuple[dict[str, object], bool]:
    link_ops = skills.plan(manifest)
    composition_problems = skills.composition_problems(
        manifest, allow_extra=allow_extra
    )
    failed_links = [op for op in link_ops if op.status != "ok"]
    checks: list[dict[str, object]] = []
    for op in link_ops:
        checks.append(
            {
                "id": f"skill.{op.skill}",
                "kind": "skill-link",
                "lane": op.lane,
                "status": "pass" if op.status == "ok" else "fail",
                "detail_code": None if op.status == "ok" else op.status,
                "source_ref": op.source_ref,
            }
        )
    for op in composition_problems:
        checks.append(
            {
                "id": f"composition.{op.target.name}",
                "kind": "runtime-composition",
                "lane": op.lane,
                "status": "fail",
                "detail_code": op.status,
            }
        )
    failed = len(failed_links) + len(composition_problems)
    return (
        {
            "schema_version": 1,
            "status": "pass" if failed == 0 else "fail",
            "checks": checks,
            "summary": {
                "passed": len(link_ops) - len(failed_links),
                "failed": failed,
            },
        },
        failed == 0,
    )


@app.callback()
def _root() -> None:
    """保留子命令名空间 (typer 单命令会塌缩, 加 callback 防止)。"""


@app.command(name="list")
def list_skills() -> None:
    """列出索引里的所有 skill。"""
    setup_logging()
    m = skills.load()
    for sk in m.skills:
        typer.echo(
            f"{sk.name:34s} {sk.visibility:8s} {','.join(sk.lanes):14s} {sk.source}"
        )
    typer.echo(f"\n{len(m.skills)} skills · lanes: {', '.join(m.lanes)}")


def _filter_manifest_lane(m: skills.Manifest, lane: str) -> skills.Manifest:
    if lane not in m.lanes:
        typer.echo(f"未知 lane: {lane}(可选:{', '.join(m.lanes)})")
        raise typer.Exit(2)
    return skills.Manifest(
        lanes={lane: m.lanes[lane]},
        skills=[
            s.model_copy(update={"lanes": [lane]}) for s in m.skills if lane in s.lanes
        ],
    )


@registry_app.command(name="validate")
def validate_registry(
    shared: list[Path] = typer.Option(
        ..., "--shared", help="shared registry JSON；可重复"
    ),
    host_bindings: Path = typer.Option(
        ..., "--host-bindings", help="当前 host-local bindings JSON"
    ),
    local: list[Path] = typer.Option(
        [], "--local", help="Mac-local registry JSON；可重复，Windows 禁止"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="输出稳定、脱敏的机器可读 JSON"
    ),
) -> None:
    """校验 authored registry、物理驻留边界和当前 host bindings。"""
    setup_logging()
    try:
        result = registry.check_registry(
            shared,
            local_paths=local,
            host_bindings_path=host_bindings,
        )
    except RuntimeError:
        result = registry.RegistryCheck(
            catalog=None,
            diagnostics=(
                registry.RegistryDiagnostic(
                    code="unsupported-host-platform",
                    scope="host",
                ),
            ),
        )
    report = result.report()
    if json_output:
        typer.echo(json.dumps(report, ensure_ascii=False, sort_keys=True))
    elif result.ok:
        summary = report["summary"]
        typer.echo(
            f"ok · registry {report['registry_revision']} · "
            f"{summary['assets']} assets · {summary['targets']} targets"
        )
    else:
        for diagnostic in result.normalized_diagnostics:
            typer.echo(f"BLOCK  {diagnostic.code} [{diagnostic.scope}]")
    if not result.ok:
        raise typer.Exit(1)


@inventory_app.command(name="adapters")
def list_inventory_adapters(
    json_output: bool = typer.Option(False, "--json", help="输出稳定的机器可读 JSON"),
) -> None:
    """列出内置 consumer adapter、revision 与兼容证据要求。"""
    setup_logging()
    report = inventory.adapter_report()
    if json_output:
        typer.echo(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return
    for adapter in report["adapters"]:
        typer.echo(
            f"{adapter['adapter_id']:22s} {adapter['platform']:8s} "
            f"{adapter['product']:12s} {adapter['format_fingerprint']}"
        )


@inventory_app.command(name="scan")
def scan_inventory(
    shared: list[Path] = typer.Option(
        ..., "--shared", help="shared registry JSON；可重复"
    ),
    host_bindings: Path = typer.Option(
        ..., "--host-bindings", help="当前 host-local bindings JSON"
    ),
    consumer_evidence: Path = typer.Option(
        ..., "--consumer-evidence", help="当前 consumer 版本/格式证据 JSON"
    ),
    local: list[Path] = typer.Option(
        [], "--local", help="Mac-local registry JSON；可重复，Windows 禁止"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="输出稳定、脱敏、root-relative 的机器可读 JSON"
    ),
) -> None:
    """只读盘点当前 host；不写、不 adopt、不推导修复动作。"""
    setup_logging()
    try:
        result = inventory.scan_inventory(
            shared,
            host_bindings_path=host_bindings,
            consumer_evidence_path=consumer_evidence,
            local_paths=local,
        )
    except RuntimeError:
        result = inventory.InventorySnapshot(
            status=inventory.SnapshotStatus.BLOCK,
            registry_revision=None,
            inventory_revision="",
            host_id=None,
            platform=registry.Platform.MACOS,
            adapters=(),
            claims=(),
            coverage=(),
            diagnostics=(
                inventory.InventoryDiagnostic(
                    code="unsupported-host-platform",
                    scope="inventory",
                    severity="block",
                ),
            ),
        )
    report = result.report()
    if json_output:
        typer.echo(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        summary = report["summary"]
        typer.echo(
            f"{report['status']} · inventory {report['inventory_revision']} · "
            f"{summary['targets']} targets · {summary['claims']} claims"
        )
        for diagnostic in report["diagnostics"]:
            typer.echo(
                f"{diagnostic['severity'].upper():5s} "
                f"{diagnostic['code']} [{diagnostic['scope']}]"
            )
    if result.status != inventory.SnapshotStatus.PASS:
        raise typer.Exit(1)


@app.command()
def verify(
    lane: str = typer.Option("", "--lane", help="只校验某个 lane(默认全部)"),
    strict_active: bool = typer.Option(
        False,
        "--strict-active",
        help="额外扫描 lane 目录,报告 manifest 外 active entry",
    ),
    allow_extra: list[str] = typer.Option(
        [],
        "--allow-extra",
        help="strict-active 下允许的额外 entry 名,可重复",
    ),
) -> None:
    """校验每个 skill 在每个 lane 的 symlink 是否健康;有问题 exit 1。"""
    setup_logging()
    full_manifest = skills.load()
    m = full_manifest
    if lane:
        m = _filter_manifest_lane(full_manifest, lane)
    bad = skills.verify(m)
    extra = (
        skills.active_problems(
            m, allow_extra=set(allow_extra), expected_manifest=full_manifest
        )
        if strict_active
        else []
    )
    if not bad and not extra:
        total = len(skills.plan(m))
        suffix = " · active clean" if strict_active else ""
        typer.echo(f"ok · {total} links healthy{suffix}")
        return
    for op in bad:
        cur = f" (现指 {op.current})" if op.current else ""
        typer.echo(f"FAIL  {op.skill} [{op.lane}]  {op.status}  {op.target}{cur}")
    for op in extra:
        cur = f" (现指 {op.current})" if op.current else ""
        typer.echo(f"FAIL  {op.target.name} [{op.lane}]  {op.status}  {op.target}{cur}")
    typer.echo(f"\n{len(bad) + len(extra)} problem(s)")
    raise typer.Exit(1)


@app.command()
def doctor(
    allow_extra: list[str] = typer.Option(
        [],
        "--allow-extra",
        help="允许的 manifest 外 active entry 名,可重复",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="输出稳定的机器可读诊断 JSON"
    ),
) -> None:
    """完整健康检查:manifest link/source + runtime composition。"""
    setup_logging()
    m = skills.load()
    allowed = set(allow_extra)
    if json_output:
        report, healthy = _doctor_report(m, allow_extra=allowed)
        typer.echo(json.dumps(report, ensure_ascii=False, sort_keys=True))
        if not healthy:
            raise typer.Exit(1)
        return
    link_problems = skills.verify(m)
    composition_problems = skills.composition_problems(m, allow_extra=allowed)
    if not link_problems and not composition_problems:
        total = len(skills.plan(m))
        profiles = len(skills.composition_snapshots(m, allow_extra=allowed))
        typer.echo(f"ok · {total} links healthy · {profiles} composition target(s)")
        return
    for op in link_problems:
        cur = f" (现指 {op.current})" if op.current else ""
        typer.echo(f"FAIL  {op.skill} [{op.lane}]  {op.status}  {op.target}{cur}")
    for op in composition_problems:
        cur = f" (现指 {op.current})" if op.current else ""
        typer.echo(f"FAIL  composition [{op.lane}]  {op.status}  {op.target}{cur}")
    typer.echo(f"\n{len(link_problems) + len(composition_problems)} problem(s)")
    raise typer.Exit(1)


@app.command()
def install(
    apply: bool = typer.Option(
        False, "--apply", help="真正建/重指 symlink(默认 dry-run 只打印计划)"
    ),
    force: bool = typer.Option(
        False, "--force", help="替换含真文件的真目录 target(危险)"
    ),
    prune_active_symlinks: bool = typer.Option(
        False,
        "--prune-active-symlinks",
        help="apply 后删除 lane 目录里 manifest 外的 symlink entry",
    ),
    lane: str = typer.Option("", "--lane", help="只装某个 lane(默认全部)"),
) -> None:
    """按 skills.json 把每个 skill 整目录 symlink 进各 lane。默认 dry-run。"""
    setup_logging()
    full_manifest = skills.load()
    m = full_manifest
    if lane:
        m = _filter_manifest_lane(full_manifest, lane)
    ops = skills.plan(m)
    for op in ops:
        mark = "  " if op.status == "ok" else "* "
        typer.echo(f"{mark}{op.skill:30s} [{op.lane:8s}] {op.status}  {op.target}")
    pending = [o for o in ops if o.needs_change]
    problems = [o for o in ops if o.status in {"missing-src", "unknown-lane"}]
    typer.echo(f"\n{len(pending)} change(s), {len(problems)} problem(s)")
    if not apply:
        typer.echo("dry-run(加 --apply 落地)")
        return
    changed = skills.apply(m, force=force)
    pruned = (
        skills.prune_active_symlinks(m, expected_manifest=full_manifest)
        if prune_active_symlinks
        else []
    )
    typer.echo(f"applied {len(changed)} change(s)")
    if prune_active_symlinks:
        typer.echo(f"pruned {len(pruned)} unmanaged symlink(s)")


@app.command()
def stats() -> None:
    """本地用量统计: per-verb 调用次数 / p50·p95 耗时 / 错误率 (零网络, 见 telemetry.py)。"""
    typer.echo(telemetry.stats())


def run() -> None:
    """Console-script entry: 在 per-invocation telemetry 捕获下跑 CLI。
    wrapper 负责 stdout/stderr 捕获 + exit-code 映射, 然后向本地 SQLite ledger 写一行
    ($ALMAGEST_TELEMETRY_OFF 或 DO_NOT_TRACK 关闭)。"""
    raise SystemExit(telemetry.run_instrumented(app, sys.argv[1:]))


if __name__ == "__main__":
    run()
