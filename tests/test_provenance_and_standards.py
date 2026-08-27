"""The documents that make claims about the repository, checked against the repository.

PROVENANCE.md restates `sources.py` for a reader. A README table states what is true of
the engineering. Both drift the moment nothing reads them.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

from wildfire_service_territory_overlap.acquire import DINS_FIELDS
from wildfire_service_territory_overlap.sources import RETRIEVED, SOURCES, WIRES_TYPES

ROOT = Path(__file__).resolve().parents[1]
# Written as escapes so this file does not itself contain what it forbids.
DASHES = ("\u2014", "\u2013")
PROVENANCE = (ROOT / "PROVENANCE.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
CONTRIBUTING = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
MAKEFILE = (ROOT / "Makefile").read_text(encoding="utf-8")
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
MAKE = shutil.which("make")
DEFINITION_OF_DONE = (ROOT / "docs" / "DEFINITION_OF_DONE.md").read_text(
    encoding="utf-8"
)
PR_TEMPLATE = (ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(
    encoding="utf-8"
)
ISSUE_FORMS = sorted(
    path
    for path in (ROOT / ".github" / "ISSUE_TEMPLATE").glob("*.yml")
    if path.name != "config.yml"
)
ISSUE_CONFIG = (ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(
    encoding="utf-8"
)
# The labels this repository carries, read from its own label list on 2026-08-27. A form
# that names a label the repository does not have files with no label at all and says
# nothing about it, so the set is written down here rather than assumed to exist.
EXISTING_LABELS = frozenset(
    {
        "accessibility",
        "bug",
        "documentation",
        "duplicate",
        "enhancement",
        "good first issue",
        "help wanted",
        "invalid",
        "question",
        "wontfix",
    }
)


def squashed(text: str) -> str:
    """One line, single spaces, so a rewrapped sentence still matches its source."""
    return " ".join(text.split())


def done_items() -> list[str]:
    """Every checklist item in the Definition of Done, continuation lines folded in."""
    items: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            items.append(squashed(" ".join(buffer)))
            buffer.clear()

    for line in DEFINITION_OF_DONE.splitlines():
        if line.startswith("- [ ] "):
            flush()
            buffer.append(line[len("- [ ] ") :])
        elif line.strip() and line.startswith("      ") and buffer:
            buffer.append(line)
        else:
            flush()
    flush()
    return items


def form_field(form: str, field_id: str) -> str:
    """One `id:` block of an issue form, up to the next element."""
    start = form.index(f"id: {field_id}\n")
    remainder = form[start:]
    end = remainder.find("\n  - type:")
    return remainder if end == -1 else remainder[:end]


def run_make(*args: str) -> subprocess.CompletedProcess[str]:
    """`make` as a reader would run it, from the repository root.

    MAKEFLAGS is cleared because these tests run from inside `make test`, and a child
    make that inherits the parent's flags is not the command a reader types.
    """
    assert MAKE, "make is the one gate here, so the tests run where make exists"
    return subprocess.run(  # noqa: S603
        [MAKE, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "MAKEFLAGS": "", "MAKELEVEL": "0"},
    )


def phony_targets() -> list[str]:
    """Every target named on the `.PHONY` line, continuations included."""
    names: list[str] = []
    reading = False
    for raw in MAKEFILE.splitlines():
        line = raw.rstrip()
        if line.startswith(".PHONY:"):
            reading = True
            line = line[len(".PHONY:") :]
        elif not reading:
            continue
        keeps_going = line.endswith("\\")
        names.extend(line.rstrip("\\").split())
        if not keeps_going:
            break
    return names


def help_lines() -> dict[str, str]:
    """What `make help` printed, as target to description."""
    result = run_make("help")
    assert result.returncode == 0, result.stderr
    listed: dict[str, str] = {}
    for line in result.stdout.splitlines():
        target, _, description = line.strip().partition(" ")
        listed[target] = description.strip()
    return listed


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


def test_provenance_names_every_field_that_is_fetched() -> None:
    """A column added to the retrieval and not to the document is undisclosed collection."""
    for field in DINS_FIELDS:
        assert field in PROVENANCE, field


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
        # The issue forms and the pull request template are prose a contributor reads
        # before writing any, so the writing rule reaches them too.
        *(ROOT / ".github").rglob("*.md"),
        *(ROOT / ".github").rglob("*.yml"),
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


def _uncommented(text: str) -> str:
    """The workflow with its comment lines removed.

    A workflow that explains in a comment why it accepts a scanner finding is not a
    workflow that runs a scanner, and the check below is about the second thing. Matching
    on the whole file made release.yml look like a scanner job the moment it said the
    word CodeQL.
    """
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )


def test_no_scanner_is_manual_only() -> None:
    """A scanner reachable only by workflow_dispatch is documentation, not enforcement.

    Scoped to workflows that run a scanner. The release workflow is dispatch-only by
    design: a tag push should not be sufficient to publish, so a human names the tag.
    """
    for workflow in WORKFLOWS:
        text = workflow.read_text(encoding="utf-8")
        if not any(scanner in _uncommented(text).lower() for scanner in SCANNERS):
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


def test_every_accepted_codeql_finding_is_written_down_with_its_reasoning() -> None:
    """An acceptance nobody can argue with is a suppression with better manners."""
    accepted = json.loads(
        (ROOT / ".github" / "codeql-accepted.json").read_text(encoding="utf-8")
    )
    assert isinstance(accepted, list)
    for entry in accepted:
        assert set(entry) == {"rule", "path", "accepted", "reason"}, entry
        assert (ROOT / entry["path"]).exists(), entry["path"]
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", entry["accepted"]), entry
        assert len(entry["reason"]) > 200, (
            f"{entry['rule']} is excused in one line. Say why it is not a defect, or "
            "fix it."
        )
    assert len(accepted) <= 3, (
        "an acceptance list this long is a scanner that has been talked out of its job"
    )


def test_the_codeql_gate_refuses_an_acceptance_that_has_outlived_its_finding() -> None:
    """The half of the gate that keeps the list from becoming a graveyard."""
    codeql = (ROOT / ".github" / "workflows" / "codeql.yml").read_text(encoding="utf-8")
    assert "codeql-accepted.json" in codeql
    assert "no longer reports" in codeql
    assert "stale.json" in codeql


def test_the_release_build_writes_no_actions_cache() -> None:
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    assert "enable-cache: false" in release, (
        "a release build caching under the main scope is a cross-workflow write it does "
        "not need"
    )


def test_the_unresolvable_dependency_is_ignored_with_its_reason_rather_than_left_red() -> (
    None
):
    dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    assert 'dependency-name: "perimeter"' in dependabot
    assert "PyPI" in dependabot, "the ignore must say what the real fix is and is not"


def test_make_help_documents_every_target_and_only_the_targets() -> None:
    """A target added without a help line is an undocumented target, not a passing build."""
    listed = help_lines()
    assert set(listed) == set(phony_targets())
    for required in ("verify", "report-offline", "determinism", "acquire"):
        assert required in listed, required
    for target, description in listed.items():
        assert len(description) > 20, f"{target} is listed without saying what it does"


def test_the_help_line_for_verify_names_the_list_ci_runs() -> None:
    """The comment above `verify` promises CI runs the same list. So must its one line."""
    recipe = next(line for line in MAKEFILE.splitlines() if line.startswith("verify:"))
    prerequisites = recipe.split("##")[0].split(":", 1)[1].split()
    description = help_lines()["verify"]
    for prerequisite in prerequisites:
        assert prerequisite in description, prerequisite
    assert "CI" in description


def test_the_help_line_for_acquire_says_it_touches_the_network() -> None:
    """The one target that opens a socket is the one a reader must not run by accident."""
    listed = help_lines()
    assert "network" in listed["acquire"]
    for target, description in listed.items():
        if target != "acquire":
            assert "network" not in description, target


def test_bare_make_still_runs_the_one_gate() -> None:
    """`help` is a target, not the default goal.

    Bare `make` has run `verify` since the file was written. Turning it into a list
    printer would change what a habitual keystroke does, so the goal is declared instead
    of moved, and this dry run is what holds the declaration to its behaviour.
    """
    assert ".DEFAULT_GOAL := verify" in MAKEFILE
    result = run_make("-n")
    assert result.returncode == 0, result.stderr
    assert "uv run pytest" in result.stdout
    assert "tools/determinism.sh" in result.stdout
    assert "MAKEFILE_LIST" not in result.stdout, "bare make printed the help list"


def test_the_pull_request_template_mirrors_the_definition_of_done() -> None:
    """A checklist that has fallen behind the rules is worse than no checklist.

    Every item, including the docs-only section: the em dash rule is the one a docs-only
    change is most likely to break and the one a shortened template drops first.
    """
    items = done_items()
    assert len(items) >= 15, "the Definition of Done lost items, or this parse did"
    template = squashed(PR_TEMPLATE)
    for item in items:
        assert item in template, f"the pull request template is missing: {item}"
    assert "No em dash or en dash anywhere" in template


def test_the_pull_request_template_asks_whether_published_figures_move() -> None:
    """The one question the template requires, and where it sends a yes."""
    assert "Does this change published figures?" in PR_TEMPLATE
    assert "Required. Tick exactly one." in PR_TEMPLATE
    assert "docs/RUNBOOK.md" in PR_TEMPLATE


def test_blank_issues_stay_enabled() -> None:
    """Neither form fits an issue like this repository's own 16 to 23.

    A maintainer note about a flag or a Makefile target has no numerator and no
    denominator. Sending it through the measurement form would ask for both, and the
    honest answers are blank, so the form would collect fiction or the issue would go
    unfiled.
    """
    assert "blank_issues_enabled: true" in ISSUE_CONFIG
    assert "blank_issues_enabled: false" not in ISSUE_CONFIG


def test_every_issue_form_names_a_label_the_repository_has() -> None:
    assert ISSUE_FORMS, "no issue forms found"
    for path in ISSUE_FORMS:
        text = path.read_text(encoding="utf-8")
        declared = re.search(r"^labels: \[(.*)\]$", text, re.MULTILINE)
        assert declared, f"{path.name} declares no labels"
        for label in declared.group(1).split(","):
            name = label.strip().strip('"').strip("'")
            assert name in EXISTING_LABELS, (
                f"{path.name} files under {name!r}, which this repository does not have"
            )


def test_the_measurement_form_asks_for_the_denominator_and_refuses_a_ranking() -> None:
    """The form talks the way `artifacts.py` talks, and requires what it requires."""
    form = (ROOT / ".github" / "ISSUE_TEMPLATE" / "measurement_proposal.yml").read_text(
        encoding="utf-8"
    )
    assert "THE DENOMINATOR" in form
    for field in ("question", "numerator", "denominator", "ranks-nobody"):
        assert "required: true" in form_field(form, field), field
    assert "required: true" in form_field(form, "touches-no-infrastructure")
    prose = squashed(form)
    assert "A count without a denominator is not a risk" in prose
    assert "a measurement that could not be made is not a zero" in prose


def test_the_bug_form_asks_for_the_command_the_output_and_a_reproduction() -> None:
    form = (ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text(
        encoding="utf-8"
    )
    for field in (
        "command",
        "what-happened",
        "what-should-have-happened",
        "reproduction",
    ):
        assert "required: true" in form_field(form, field), field
    assert "SECURITY.md" in form, "the bug form must send a vulnerability elsewhere"
    assert "make report-offline" in form


def paragraph_saying(text: str, phrase: str) -> str:
    """The one blank-line-separated paragraph carrying `phrase`, squashed to a line."""
    found = [
        squashed(block) for block in text.split("\n\n") if phrase in squashed(block)
    ]
    assert len(found) == 1, f"{phrase!r} appears in {len(found)} paragraphs"
    return found[0]


def test_the_name_order_claim_names_its_one_exception_wherever_it_is_made() -> None:
    """Issue 23: the claim was made without qualification and is false for one key.

    `contested_groups` is ordered by record count, and `check_all` only ever applies the
    name-order rule to `territories`. The claim is narrowed rather than the code changed,
    so the claim has to keep naming what it excludes, in the README and in the module
    that does the ordering.
    """
    measure = (
        ROOT / "src" / "wildfire_service_territory_overlap" / "measure.py"
    ).read_text(encoding="utf-8")
    for document, text in (("README.md", README), ("measure.py", measure)):
        claim = paragraph_saying(text, "in the output is sorted by name")
        assert "contested_groups" in claim, document
        assert "exception" in claim, document
