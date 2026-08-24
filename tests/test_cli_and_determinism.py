"""The offline build, and the gate behind the byte-identical claim.

`tools/determinism.sh` is run here against trees that should fail it, because a gate
nobody has watched fail is a gate that might not be able to.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from wildfire_service_territory_overlap import cli

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
SCRIPT = ROOT / "tools" / "determinism.sh"


def build_into(out: Path) -> tuple[Path, Path]:
    return cli.build(
        dins_path=FIXTURES / "dins_sample.json",
        iou_pou_path=FIXTURES / "else_iou_pou_sample.geojson",
        other_path=FIXTURES / "else_other_sample.geojson",
        counties_path=FIXTURES / "county_boundaries_sample.geojson",
        out_dir=out,
        is_fixture=True,
    )


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
    code = cli.main(
        [
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
            str(tmp_path / "out"),
        ]
    )
    assert code == 0
    assert "measurements.json" in capsys.readouterr().out


def test_the_cli_version_flag_prints_version_and_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    import tomllib

    pyproject_version = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]

    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert pyproject_version in out
    assert "wildfire-service-territory-overlap" in out


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
