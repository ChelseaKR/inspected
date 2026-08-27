"""The offline build, the version flag, and the gate behind the byte-identical claim.

`tools/determinism.sh` is run here against trees that should fail it, because a gate
nobody has watched fail is a gate that might not be able to.
"""

from __future__ import annotations

import subprocess
import tomllib
from importlib import metadata
from pathlib import Path
from typing import Any

import pytest

from wildfire_service_territory_overlap import cli

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
SCRIPT = ROOT / "tools" / "determinism.sh"
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def build_argv(out: Path) -> list[str]:
    return [
        "--fixture",
        "--dins",
        str(FIXTURES / "dins_sample.json"),
        "--iou-pou",
        str(FIXTURES / "else_iou_pou_sample.geojson"),
        "--other",
        str(FIXTURES / "else_other_sample.geojson"),
        "--counties",
        str(FIXTURES / "county_boundaries_sample.geojson"),
        "--out",
        str(out),
    ]


def build_into(out: Path) -> tuple[Path, Path]:
    return cli.build(
        dins_path=FIXTURES / "dins_sample.json",
        iou_pou_path=FIXTURES / "else_iou_pou_sample.geojson",
        other_path=FIXTURES / "else_other_sample.geojson",
        counties_path=FIXTURES / "county_boundaries_sample.geojson",
        out_dir=out,
        is_fixture=True,
    )


def _absent_distribution(calls: list[str] | None = None) -> Any:
    """A `metadata.version` that has never heard of this distribution.

    Scoped: any other distribution is answered by the real lookup, so patching this in
    cannot make some unrelated library fail and be read as this flag working.
    """
    real = metadata.version

    def version(name: str) -> str:
        if calls is not None:
            calls.append(name)
        if name == cli.DISTRIBUTION:
            raise metadata.PackageNotFoundError(name)
        return str(real(name))

    return version


def run_gate(a: Path, b: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [str(SCRIPT), str(a), str(b)], capture_output=True, text=True, check=False
    )


def test_the_offline_build_writes_both_artifacts(tmp_path: Path) -> None:
    artifact, document = build_into(tmp_path / "out")
    assert artifact.exists() and document.exists()
    assert artifact.name == "measurements.json"
    assert document.name == "REPORT.md"


def test_a_fixture_build_is_marked_as_one(tmp_path: Path) -> None:
    import json

    artifact, _ = build_into(tmp_path / "out")
    assert json.loads(artifact.read_text(encoding="utf-8"))["is_fixture"] is True


def test_the_cli_returns_zero_and_names_what_it_wrote(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = cli.main(build_argv(tmp_path / "out"))
    assert code == 0
    assert "measurements.json" in capsys.readouterr().out


def test_the_version_flag_prints_the_installed_version_and_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["--version"])
    assert exit_info.value.code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == f"{cli.DISTRIBUTION} {PYPROJECT['project']['version']}\n"


def test_the_version_cannot_drift_from_pyproject() -> None:
    """There is one version, in `pyproject.toml`, and one path back to it.

    The distribution name is asserted against `project.name` so the lookup cannot start
    naming a distribution nothing here builds, and the version is asserted against
    `project.version` so an edit to the manifest without a reinstall is a red test rather
    than a CLI quietly reporting the version of a stale install.
    """
    assert PYPROJECT["project"]["name"] == cli.DISTRIBUTION
    assert metadata.version(cli.DISTRIBUTION) == PYPROJECT["project"]["version"], (
        "the installed metadata and pyproject.toml disagree; run `uv sync --locked`"
    )


def test_a_version_that_cannot_be_read_is_refused_rather_than_guessed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """No installed metadata is a question that was not answered, not a version."""
    monkeypatch.setattr(cli.metadata, "version", _absent_distribution())
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["--version"])
    assert exit_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "version not measured" in captured.err


def test_a_build_never_asks_for_the_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The lookup belongs to the flag, not to the parser.

    Resolving the version while the parser is being built runs it on every invocation,
    so a checkout with no installed distribution metadata loses `--dins` along with
    `--version`. The counter is the half of this that keeps working once somebody has
    metadata installed: a build that never asks cannot be broken by the answer.
    """
    calls: list[str] = []
    monkeypatch.setattr(cli.metadata, "version", _absent_distribution(calls))
    assert cli.main(build_argv(tmp_path / "out")) == 0
    assert "measurements.json" in capsys.readouterr().out
    assert calls == []


def test_two_builds_of_the_same_inputs_are_byte_identical(tmp_path: Path) -> None:
    build_into(tmp_path / "one")
    build_into(tmp_path / "two")
    result = run_gate(tmp_path / "one", tmp_path / "two")
    assert result.returncode == 0, result.stderr


def test_the_gate_fails_on_trees_that_differ(tmp_path: Path) -> None:
    build_into(tmp_path / "one")
    build_into(tmp_path / "two")
    (tmp_path / "two" / "REPORT.md").write_text("edited", encoding="utf-8")
    assert run_gate(tmp_path / "one", tmp_path / "two").returncode == 1


def test_the_gate_refuses_an_empty_tree_rather_than_calling_it_a_match(
    tmp_path: Path,
) -> None:
    (tmp_path / "one").mkdir()
    (tmp_path / "two").mkdir()
    assert run_gate(tmp_path / "one", tmp_path / "two").returncode == 2


def test_the_gate_refuses_a_missing_tree(tmp_path: Path) -> None:
    build_into(tmp_path / "one")
    assert run_gate(tmp_path / "one", tmp_path / "absent").returncode == 2


def test_the_gate_refuses_the_wrong_number_of_arguments() -> None:
    result = subprocess.run(  # noqa: S603
        [str(SCRIPT), "only-one"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 2
    assert "usage" in result.stderr
