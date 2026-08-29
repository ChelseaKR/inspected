"""The offline build, and the gate behind the byte-identical claim.

`tools/determinism.sh` is run here against trees that should fail it, because a gate
nobody has watched fail is a gate that might not be able to.
"""

from __future__ import annotations

import importlib.metadata as metadata
import subprocess
import tomllib
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


def test_the_version_flag_prints_the_installed_version_and_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["--version"])
    assert exit_info.value.code == 0
    printed = capsys.readouterr().out.strip()
    assert printed == f"{cli.DISTRIBUTION} {metadata.version(cli.DISTRIBUTION)}"


def test_the_version_cannot_drift_from_pyproject() -> None:
    """One source of truth, checked from both ends.

    `pyproject.toml` holds the version, hatchling copies it into the installed
    distribution metadata, and the flag reads it back from there. There is no second
    copy to drift, and these two assertions are what hold the chain together: the name
    the flag looks up has to be the name the project is packaged under, and the version
    that comes back has to be the one declared.
    """
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert config["project"]["name"] == cli.DISTRIBUTION
    assert metadata.version(cli.DISTRIBUTION) == config["project"]["version"]


def test_a_version_that_cannot_be_read_is_refused_rather_than_guessed(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Not measured, on stderr, with a nonzero exit. Never a placeholder string."""

    def absent(_name: str) -> str:
        raise metadata.PackageNotFoundError(cli.DISTRIBUTION)

    monkeypatch.setattr(cli.metadata, "version", absent)
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["--version"])
    assert exit_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == "", "a version that could not be read was printed anyway"
    assert "not measured" in captured.err
    assert "uv sync --locked" in captured.err


def test_a_build_never_asks_for_the_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The trap this flag was written around, held shut by a test.

    Resolving the version while the parser is built runs the lookup on every
    invocation. Here the lookup is rigged to fail outright, and a full fixture build
    still has to succeed, because a build has no business asking what version it is.
    """

    def never(_name: str) -> str:
        raise AssertionError("a build asked for the version")

    monkeypatch.setattr(cli.metadata, "version", never)
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
