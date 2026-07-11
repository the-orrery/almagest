from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from almagest.cli import app

runner = CliRunner()


def _make_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """造一个隔离的临时索引(一个源 skill + 一个 lane 目录),返回 lane 目录。"""
    src = tmp_path / "src" / "demo"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("# demo")
    lane = tmp_path / "lane"
    lane.mkdir()
    manifest = tmp_path / "skills.json"
    manifest.write_text(
        json.dumps(
            {
                "lanes": {"claude": str(lane)},
                "skills": [
                    {
                        "name": "demo",
                        "source": str(src),
                        "lanes": ["claude"],
                        "visibility": "private",
                    }
                ],
            }
        )
    )
    monkeypatch.setenv("ALMAGEST_MANIFEST", str(manifest))
    return lane


def _make_identity_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, source_path: str = "skills/demo"
) -> Path:
    root = tmp_path / "personal-sources"
    src = root / "skills" / "demo"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("# demo")
    lane = tmp_path / "lane"
    lane.mkdir()
    roots = tmp_path / "source-roots.json"
    roots.write_text(json.dumps({"personal/skill-vault": str(root)}))
    manifest = tmp_path / "skills.json"
    manifest.write_text(
        json.dumps(
            {
                "lanes": {"personal": str(lane)},
                "skills": [
                    {
                        "name": "demo",
                        "source": {
                            "repository": "personal/skill-vault",
                            "path": source_path,
                        },
                        "lanes": ["personal"],
                    }
                ],
            }
        )
    )
    monkeypatch.setenv("ALMAGEST_MANIFEST", str(manifest))
    monkeypatch.setenv("ALMAGEST_SOURCE_ROOTS", str(roots))
    return lane


def test_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_manifest(tmp_path, monkeypatch)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "demo" in result.stdout
    assert "1 skills" in result.stdout


def test_identity_source_resolves_from_host_overlay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane = _make_identity_manifest(tmp_path, monkeypatch)

    result = runner.invoke(app, ["install", "--apply"])

    assert result.exit_code == 0, result.stdout
    assert (lane / "demo").is_symlink()
    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 0, result.stdout


def test_identity_source_missing_root_is_actionable_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_identity_manifest(tmp_path, monkeypatch)
    monkeypatch.delenv("ALMAGEST_SOURCE_ROOTS")

    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 1
    report = json.loads(result.stdout)
    assert report["status"] == "fail"
    assert report["checks"][0]["detail_code"] == "missing-source-root"
    assert report["checks"][0]["source_ref"] == "personal/skill-vault:skills/demo"


def test_identity_source_cannot_escape_host_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_identity_manifest(tmp_path, monkeypatch, source_path="../outside")

    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 1
    report = json.loads(result.stdout)
    assert report["checks"][0]["detail_code"] == "source-path-escape"


def test_doctor_json_redacts_legacy_source_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_manifest(tmp_path, monkeypatch)

    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 1
    report = json.loads(result.stdout)
    assert report["checks"][0]["source_ref"] == "legacy-path"


def test_verify_fails_before_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_manifest(tmp_path, monkeypatch)
    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 1
    assert "demo" in result.stdout


def test_install_dry_run_makes_no_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane = _make_manifest(tmp_path, monkeypatch)
    result = runner.invoke(app, ["install"])
    assert result.exit_code == 0
    assert not (lane / "demo").exists()
    assert "dry-run" in result.stdout


def test_install_apply_then_verify_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane = _make_manifest(tmp_path, monkeypatch)
    result = runner.invoke(app, ["install", "--apply"])
    assert result.exit_code == 0
    link = lane / "demo"
    assert link.is_symlink()
    assert (link / "SKILL.md").read_text() == "# demo"
    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 0
    assert "healthy" in result.stdout


def test_verify_strict_active_fails_on_unmanaged_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane = _make_manifest(tmp_path, monkeypatch)
    result = runner.invoke(app, ["install", "--apply"])
    assert result.exit_code == 0
    (lane / "extra").mkdir()

    result = runner.invoke(app, ["verify", "--strict-active"])

    assert result.exit_code == 1
    assert "extra" in result.stdout
    assert "unmanaged-active" in result.stdout


def test_verify_strict_active_allows_explicit_extra(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane = _make_manifest(tmp_path, monkeypatch)
    result = runner.invoke(app, ["install", "--apply"])
    assert result.exit_code == 0
    (lane / "extra").mkdir()

    result = runner.invoke(app, ["verify", "--strict-active", "--allow-extra", "extra"])

    assert result.exit_code == 0
    assert "active clean" in result.stdout


def test_verify_strict_active_ignores_dot_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane = _make_manifest(tmp_path, monkeypatch)
    result = runner.invoke(app, ["install", "--apply"])
    assert result.exit_code == 0
    (lane / ".system").mkdir()

    result = runner.invoke(app, ["verify", "--strict-active"])

    assert result.exit_code == 0
    assert "active clean" in result.stdout


def test_install_prunes_unmanaged_symlink_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane = _make_manifest(tmp_path, monkeypatch)
    stale_source = tmp_path / "stale-source"
    stale_source.mkdir()
    (lane / "stale-link").symlink_to(stale_source, target_is_directory=True)
    (lane / "stale-dir").mkdir()

    result = runner.invoke(app, ["install", "--apply", "--prune-active-symlinks"])

    assert result.exit_code == 0
    assert not (lane / "stale-link").exists()
    assert (lane / "stale-dir").is_dir()
    result = runner.invoke(app, ["verify", "--strict-active"])
    assert result.exit_code == 1
    assert "stale-dir" in result.stdout


def test_install_lane_filters_skill_lanes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "src" / "demo"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("# demo")
    personal_lane = tmp_path / "personal"
    work_lane = tmp_path / "work"
    personal_lane.mkdir()
    work_lane.mkdir()
    manifest = tmp_path / "skills.json"
    manifest.write_text(
        json.dumps(
            {
                "lanes": {"personal": str(personal_lane), "work": str(work_lane)},
                "skills": [
                    {
                        "name": "demo",
                        "source": str(src),
                        "lanes": ["personal", "work"],
                        "visibility": "private",
                    }
                ],
            }
        )
    )
    monkeypatch.setenv("ALMAGEST_MANIFEST", str(manifest))

    result = runner.invoke(app, ["install", "--lane", "personal", "--apply"])
    assert result.exit_code == 0
    assert "unknown-lane" not in result.stdout
    assert (personal_lane / "demo").is_symlink()
    assert not (work_lane / "demo").exists()

    result = runner.invoke(app, ["verify", "--lane", "personal"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["verify", "--lane", "work"])
    assert result.exit_code == 1
    assert "demo" in result.stdout


def test_lane_can_target_multiple_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "src" / "demo"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("# demo")
    claude_dir = tmp_path / "claude-skills"
    codex_dir = tmp_path / "codex-skills"
    claude_dir.mkdir()
    codex_dir.mkdir()
    manifest = tmp_path / "skills.json"
    manifest.write_text(
        json.dumps(
            {
                "lanes": {"personal": [str(claude_dir), str(codex_dir)]},
                "skills": [
                    {
                        "name": "demo",
                        "source": str(src),
                        "lanes": ["personal"],
                        "visibility": "private",
                    }
                ],
            }
        )
    )
    monkeypatch.setenv("ALMAGEST_MANIFEST", str(manifest))

    result = runner.invoke(app, ["install", "--lane", "personal", "--apply"])

    assert result.exit_code == 0
    assert (claude_dir / "demo").is_symlink()
    assert (codex_dir / "demo").is_symlink()
    result = runner.invoke(app, ["verify", "--lane", "personal", "--strict-active"])
    assert result.exit_code == 0
    assert "2 links healthy" in result.stdout


def test_shared_base_across_lanes_no_false_unmanaged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """一个 runtime 目录(codex)被 personal+work 两 lane 共喂时,strict-active
    不应把另一 lane 的 entry 误报成 unmanaged;plan 也不应对共享 target 重复计数。"""
    src = tmp_path / "src"
    for name in ("p", "w", "b"):
        (src / name).mkdir(parents=True)
        (src / name / "SKILL.md").write_text(f"# {name}")
    claude = tmp_path / "claude"
    work = tmp_path / "work"
    codex = tmp_path / "codex"
    for d in (claude, work, codex):
        d.mkdir()
    manifest = tmp_path / "skills.json"
    manifest.write_text(
        json.dumps(
            {
                "lanes": {
                    "personal": [str(claude), str(codex)],
                    "work": [str(work), str(codex)],
                },
                "skills": [
                    {"name": "p", "source": str(src / "p"), "lanes": ["personal"]},
                    {"name": "w", "source": str(src / "w"), "lanes": ["work"]},
                    {
                        "name": "b",
                        "source": str(src / "b"),
                        "lanes": ["personal", "work"],
                    },
                ],
            }
        )
    )
    monkeypatch.setenv("ALMAGEST_MANIFEST", str(manifest))

    result = runner.invoke(app, ["install", "--apply"])
    assert result.exit_code == 0
    # codex 单目录收齐三者(含 personal-only 的 p 与 work-only 的 w)
    for name in ("p", "w", "b"):
        assert (codex / name).is_symlink()
    assert (claude / "p").is_symlink() and (claude / "b").is_symlink()
    assert not (claude / "w").exists()
    assert (work / "w").is_symlink() and (work / "b").is_symlink()
    assert not (work / "p").exists()

    result = runner.invoke(app, ["verify", "--strict-active"])
    assert result.exit_code == 0, result.stdout
    # 去重后 distinct target = claude{p,b} + work{w,b} + codex{p,w,b} = 7
    assert "7 links healthy" in result.stdout
    assert "active clean" in result.stdout

    result = runner.invoke(app, ["verify", "--lane", "personal", "--strict-active"])
    assert result.exit_code == 0, result.stdout
    assert "active clean" in result.stdout

    result = runner.invoke(app, ["verify", "--lane", "work", "--strict-active"])
    assert result.exit_code == 0, result.stdout
    assert "active clean" in result.stdout


def test_lane_prune_preserves_other_lane_in_shared_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "src"
    for name in ("p", "w", "extra"):
        (src / name).mkdir(parents=True)
        (src / name / "SKILL.md").write_text(f"# {name}")
    claude = tmp_path / "claude"
    work = tmp_path / "work"
    codex = tmp_path / "codex"
    for d in (claude, work, codex):
        d.mkdir()
    manifest = tmp_path / "skills.json"
    manifest.write_text(
        json.dumps(
            {
                "lanes": {
                    "personal": [str(claude), str(codex)],
                    "work": [str(work), str(codex)],
                },
                "skills": [
                    {"name": "p", "source": str(src / "p"), "lanes": ["personal"]},
                    {"name": "w", "source": str(src / "w"), "lanes": ["work"]},
                ],
            }
        )
    )
    monkeypatch.setenv("ALMAGEST_MANIFEST", str(manifest))

    result = runner.invoke(app, ["install", "--apply"])
    assert result.exit_code == 0, result.stdout
    (codex / "extra").symlink_to(src / "extra", target_is_directory=True)

    result = runner.invoke(
        app,
        ["install", "--lane", "personal", "--apply", "--prune-active-symlinks"],
    )
    assert result.exit_code == 0, result.stdout
    assert (codex / "w").is_symlink()
    assert not (codex / "extra").exists()
    assert "pruned 1 unmanaged symlink(s)" in result.stdout


def test_doctor_checks_composition_union(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "src"
    for name in ("p", "w", "b"):
        (src / name).mkdir(parents=True)
        (src / name / "SKILL.md").write_text(f"# {name}")
    claude = tmp_path / "claude"
    work = tmp_path / "work"
    codex = tmp_path / "codex"
    for d in (claude, work, codex):
        d.mkdir()
    manifest = tmp_path / "skills.json"
    manifest.write_text(
        json.dumps(
            {
                "lanes": {
                    "personal": [str(claude), str(codex)],
                    "work": [str(work), str(codex)],
                },
                "skills": [
                    {"name": "p", "source": str(src / "p"), "lanes": ["personal"]},
                    {"name": "w", "source": str(src / "w"), "lanes": ["work"]},
                    {
                        "name": "b",
                        "source": str(src / "b"),
                        "lanes": ["personal", "work"],
                    },
                ],
            }
        )
    )
    monkeypatch.setenv("ALMAGEST_MANIFEST", str(manifest))

    result = runner.invoke(app, ["install", "--apply"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0, result.stdout
    assert "7 links healthy" in result.stdout
    assert "3 composition target(s)" in result.stdout


def test_doctor_fails_on_dangling_unmanaged_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane = _make_manifest(tmp_path, monkeypatch)
    result = runner.invoke(app, ["install", "--apply"])
    assert result.exit_code == 0
    (lane / "ghost").symlink_to(tmp_path / "missing", target_is_directory=True)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "ghost" in result.stdout
    assert "dangling-active" in result.stdout
