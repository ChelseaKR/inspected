"""The documents that make claims about the repository, checked against the repository.

PROVENANCE.md restates `sources.py` for a reader. A README table states what is true of
the engineering. Both drift the moment nothing reads them.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from inspected.sources import RETRIEVED, SOURCES, WIRES_TYPES

ROOT = Path(__file__).resolve().parents[1]
# Written as escapes so this file does not itself contain what it forbids.
DASHES = ("\u2014", "\u2013")
PROVENANCE = (ROOT / "PROVENANCE.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
CONTRIBUTING = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
MAKEFILE = (ROOT / "Makefile").read_text(encoding="utf-8")
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))


def test_every_source_appears_in_provenance_with_its_hash() -> None:
    for source in SOURCES:
        assert source.title in PROVENANCE, source.key
        assert source.sha256 in PROVENANCE, source.key
        assert str(source.raw_bytes) in PROVENANCE, source.key
        assert str(source.feature_count) in PROVENANCE, source.key


def test_no_source_carries_a_placeholder_hash() -> None:
    for source in SOURCES:
        assert len(source.sha256) == 64, f"{source.key} has no hash recorded"
        assert source.raw_bytes > 0, f"{source.key} has no byte count recorded"


def test_the_retrieval_date_is_the_same_everywhere() -> None:
    assert RETRIEVED in PROVENANCE
    assert RETRIEVED in README
    for source in SOURCES:
        assert source.retrieved == RETRIEVED


def test_every_publisher_caveat_names_what_was_built_from_it() -> None:
    for source in SOURCES:
        assert source.caveats, f"{source.key} quotes no published limitation"
        for caveat in source.caveats:
            assert len(caveat.quote) > 40
            assert len(caveat.measured_as) > 60, (
                f"{source.key}/{caveat.topic} quotes a caveat without saying what was "
                "measured from it"
            )


def test_provenance_names_the_fields_that_are_never_fetched() -> None:
    for field in ("SITEADDRESS", "APN", "ASSESSEDIMPROVEDVALUE"):
        assert field in PROVENANCE


def test_the_wires_types_are_the_ones_the_adr_argues_for() -> None:
    assert set(WIRES_TYPES) == {"IOU", "POU", "CO-OP", "Tribal"}
    adr = (ROOT / "docs" / "adr").glob("0002-*.md")
    text = next(adr).read_text(encoding="utf-8")
    for kind in ("CCA", "ADMIN"):
        assert kind in text


def test_the_readme_disclaims_affiliation_before_anything_else() -> None:
    head = README.split("## ")[0]
    assert "Not affiliated with, endorsed by, or approved by CAL FIRE" in head
    assert "SMUD" in head
    assert "any electric utility" in head


def test_the_readme_has_a_visitor_first_quickstart_near_the_top() -> None:
    first_sixty = "\n".join(README.splitlines()[:60])
    assert "make verify" in first_sixty
    assert "uv sync --locked" in first_sixty


def test_the_readme_never_claims_users_adopters_or_downloads() -> None:
    lowered = README.lower()
    for phrase in (
        "users",
        "adopters",
        "downloads",
        "in production",
        "widely used",
        "trusted by",
    ):
        assert phrase not in lowered, f"the README says {phrase!r}"


def test_no_document_uses_an_em_or_en_dash() -> None:
    targets = [
        *ROOT.glob("*.md"),
        *(ROOT / "docs").rglob("*.md"),
        *(ROOT / "published").glob("*.md"),
        *(ROOT / "src").rglob("*.py"),
        *(ROOT / "tests").rglob("*.py"),
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        for dash in DASHES:
            assert dash not in text, f"{path.name} contains {dash!r}"


def test_the_standards_conformance_table_has_no_blank_state() -> None:
    section = README.split("## Standards conformance")[1]
    rows = [
        line
        for line in section.splitlines()
        if line.startswith("| ")
        and not line.startswith("| Standard")
        and "---" not in line
    ]
    assert len(rows) >= 14
    for row in rows:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        assert len(cells) == 2, row
        assert cells[1], f"{cells[0]} has no state recorded"
        assert cells[1].startswith(("Applies", "N/A")), row


def test_the_standards_version_is_pinned_and_read() -> None:
    pin = (ROOT / ".standards-version").read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"v\d+\.\d+\.\d+", pin)
    assert pin in README


def test_the_changelog_has_an_unreleased_section_and_the_current_version() -> None:
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    assert "## [Unreleased]" in CHANGELOG
    assert f"## [{version}]" in CHANGELOG


def test_the_package_and_citation_versions_agree() -> None:
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert f"version: {version}" in citation


def test_the_coverage_floor_and_complexity_cap_are_declared() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert config["tool"]["coverage"]["report"]["fail_under"] >= 90
    assert config["tool"]["ruff"]["lint"]["mccabe"]["max-complexity"] <= 10
    assert config["project"]["requires-python"].startswith(">=3.1")


def test_the_dev_toolchain_declares_version_floors() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    dev = " ".join(config["dependency-groups"]["dev"])
    assert "ruff>=" in dev
    assert "mypy>=" in dev


def test_the_verify_target_exists_and_is_what_ci_runs() -> None:
    assert "\nverify:" in MAKEFILE
    assert "uv sync --locked" in MAKEFILE
    recipe = [
        line for line in MAKEFILE.splitlines() if not line.lstrip().startswith("#")
    ]
    assert "--frozen" not in "\n".join(recipe), (
        "--frozen means 'do not resolve', not 'the lock is current', and it exits 0 "
        "against a stale lockfile"
    )
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "run: make verify" in ci


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_every_workflow_declares_a_top_level_permissions_block(workflow: Path) -> None:
    text = workflow.read_text(encoding="utf-8")
    assert re.search(r"^permissions:$", text, re.MULTILINE), workflow.name


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_every_action_is_pinned_to_a_full_sha_with_its_version(workflow: Path) -> None:
    text = workflow.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- uses:") and not stripped.startswith("uses:"):
            continue
        assert re.search(r"uses:\s+[\w./-]+@[0-9a-f]{40}\s+#\s+v\d", stripped), (
            f"{workflow.name}: {stripped}"
        )


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_no_security_gate_is_silenced(workflow: Path) -> None:
    text = workflow.read_text(encoding="utf-8")
    assert "continue-on-error: true" not in text, workflow.name
    assert "|| true" not in text, workflow.name


SCANNERS = ("codeql", "semgrep", "gitleaks", "zizmor", "pip-audit")


def test_no_scanner_is_manual_only() -> None:
    """A scanner reachable only by workflow_dispatch is documentation, not enforcement.

    Scoped to workflows that run a scanner. The release workflow is dispatch-only by
    design: a tag push should not be sufficient to publish, so a human names the tag.
    """
    for workflow in WORKFLOWS:
        text = workflow.read_text(encoding="utf-8")
        if not any(scanner in text.lower() for scanner in SCANNERS):
            continue
        triggers = text.split("permissions:")[0]
        if "workflow_dispatch" not in triggers:
            continue
        assert "pull_request" in triggers or "schedule" in triggers, workflow.name


def test_contributing_names_the_rules_the_project_will_not_break() -> None:
    for phrase in (
        "without its denominator",
        "never in CI",
        "make verify",
    ):
        assert phrase in CONTRIBUTING
