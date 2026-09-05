"""The committed ruleset names every gate a pull request actually runs.

Branch protection is a repository setting. It can be widened, narrowed or deleted
without a commit, and the history would not show it, so `.github/rulesets/main.json`
is committed as the evidence the README's CI/CD row is checked against.

The invariant here is not "the file matches the live ruleset": a public-scope token
cannot read `bypass_actors`, and a comparison that silently drops a field it could not
read is a check that passes for the wrong reason. The invariant is the one that catches
the mistake this repository could actually make, which is **adding a job to CI and
forgetting to require it**. An unrequired job still reports on the pull-request page,
still goes red, and still merges.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RULESET = REPO / ".github" / "rulesets" / "main.json"
WORKFLOWS = REPO / ".github" / "workflows"


def required_contexts() -> set[str]:
    ruleset = json.loads(RULESET.read_text(encoding="utf-8"))
    for rule in ruleset["rules"]:
        if rule["type"] == "required_status_checks":
            checks = rule["parameters"]["required_status_checks"]
            return {check["context"] for check in checks}
    raise AssertionError("the committed ruleset requires no status checks at all")


def pull_request_job_names() -> set[str]:
    """Every job of every workflow that triggers on `pull_request`.

    A job's check name is its `name:` where it has one, and its job id otherwise,
    which is how GitHub names them, and therefore how a ruleset must.
    """
    names: set[str] = set()
    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        header, _, body = text.partition("\njobs:")
        if not re.search(r"^\s{2}pull_request:", header, re.MULTILINE):
            continue
        for block in re.finditer(
            r"^  ([a-z0-9][a-z0-9_-]*):\n((?:(?:    .*)?\n)*)", body, re.MULTILINE
        ):
            job_id, job_body = block.group(1), block.group(2)
            named = re.search(r"^    name:\s*(.+?)\s*$", job_body, re.MULTILINE)
            names.add(named.group(1).strip("\"'") if named else job_id)
    return names


def test_the_ruleset_requires_every_job_a_pull_request_runs() -> None:
    missing = pull_request_job_names() - required_contexts()
    assert not missing, (
        f"these jobs run on a pull request but are not required by the committed "
        f"ruleset, so they can go red and still merge: {sorted(missing)}"
    )


def test_the_ruleset_requires_nothing_that_does_not_run() -> None:
    """A required check no workflow produces blocks every merge, forever."""
    stale = required_contexts() - pull_request_job_names()
    assert not stale, (
        f"the committed ruleset requires checks no pull-request job produces, which "
        f"would block every merge: {sorted(stale)}"
    )


def test_the_ruleset_still_refuses_deletion_and_force_push() -> None:
    ruleset = json.loads(RULESET.read_text(encoding="utf-8"))
    types = {rule["type"] for rule in ruleset["rules"]}
    assert {"deletion", "non_fast_forward", "pull_request"} <= types


def test_the_bypass_actors_are_stated_rather_than_omitted() -> None:
    """The admin bypass is real. A file that hides it is a file that lies politely."""
    ruleset = json.loads(RULESET.read_text(encoding="utf-8"))
    assert "bypass_actors" in ruleset, (
        "bypass_actors is absent from the committed ruleset; an omitted bypass reads "
        "as no bypass, which is the claim .github/rulesets/README.md refuses to make"
    )
