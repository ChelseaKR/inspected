"""The refresh diff, held to the behaviour the refresh procedure will rely on."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wildfire_service_territory_overlap.artifact_diff import diff_trees, main

# The prose report exactly as it stood before `--json` existed, captured from the
# module at commit c8831ff. `--json` is opt-in and the default output is a published
# interface: the refresh procedure in docs/RUNBOOK.md reads these lines by eye. A
# byte that moves here moves without anybody deciding it should.
PLAIN_CHANGED_AND_ADDED = (
    "changed  $.placement_coverage.fire_records: 132520 -> 132522\n"
    "added    $.attributability_by_fire.counties_named_in_the_record_set: 52\n"
    "25 values compared: 1 added, 0 removed, 1 changed.\n"
    "Nothing was removed.\n"
)
PLAIN_REFUSED = (
    "REMOVED  $.placement_coverage.counts.placed: 82353\n"
    "24 values compared: 0 added, 1 removed, 0 changed.\n"
    "REFUSED: published values disappeared. If the removal is deliberate, "
    "re-run with --allow-removals and say so in PROVENANCE.md.\n"
)
PLAIN_IDENTICAL = (
    "24 values compared: 0 added, 0 removed, 0 changed.\nNo published value moved.\n"
)


def sample_tree() -> dict:
    """A small artifact with every shape the real one has."""
    return {
        "is_fixture": False,
        "placement_coverage": {
            "fire_records": 132520,
            "counts": {"placed": 82353, "contested": 50167},
            "rates": [
                {
                    "label": "placed in exactly one published territory",
                    "numerator": 82353,
                    "denominator": 132520,
                }
            ],
        },
        "territories": [
            {
                "territory": "Anza Electric Cooperative, Inc.",
                "records_placed_here": 305,
                "contested_with": [],
            },
            {
                "territory": "Pacific Gas & Electric Company",
                "records_placed_here": 65865,
                "contested_with": ["Power and Water Resource Pooling Authority"],
            },
        ],
        "by_county": [
            {"county": "Alameda", "records": 120},
            {"county": "Butte", "records": 28747},
        ],
        "by_year": [{"year": 2024, "records": 8117}],
        "contested_groups": [
            {"records": 25345, "territories": ["Metropolitan Water District", "SCE"]},
            {"records": 12241, "territories": ["PG&E", "PWRPA"]},
        ],
    }


def test_identical_trees_report_nothing_and_count_every_leaf() -> None:
    result = diff_trees(sample_tree(), sample_tree())
    assert not result.added
    assert not result.removed
    assert not result.changed
    assert result.total == result.unchanged
    # A hand count of leaves in sample_tree, so "everything agreed" cannot be vacuous.
    assert result.unchanged == 24


def test_a_changed_leaf_is_reported_at_its_path() -> None:
    old = sample_tree()
    new = json.loads(json.dumps(old))
    new["placement_coverage"]["fire_records"] = 132522
    result = diff_trees(old, new)
    assert len(result.changed) == 1
    change = result.changed[0]
    assert change.path == "$.placement_coverage.fire_records"
    assert change.before == 132520
    assert change.after == 132522
    assert not result.removed


def test_a_removed_leaf_is_refused_and_allow_removals_passes_it(tmp_path: Path) -> None:
    old = tmp_path / "old.json"
    new = tmp_path / "new.json"
    stripped = sample_tree()
    del stripped["placement_coverage"]["counts"]["placed"]
    old.write_text(json.dumps(sample_tree()), encoding="utf-8")
    new.write_text(json.dumps(stripped), encoding="utf-8")

    refused = main([str(old), str(new)])
    assert refused == 1

    allowed = main(["--allow-removals", str(old), str(new)])
    assert allowed == 0


def test_an_added_leaf_is_reported_not_refused() -> None:
    old = sample_tree()
    new = json.loads(json.dumps(old))
    new["attributability_by_fire"] = {"counties_named_in_the_record_set": 52}
    result = diff_trees(old, new)
    assert [leaf.path for leaf in result.added] == [
        "$.attributability_by_fire.counties_named_in_the_record_set"
    ]
    assert not result.removed and not result.changed


def test_a_reordered_keyed_collection_reports_nothing() -> None:
    old = sample_tree()
    new = json.loads(json.dumps(old))
    new["territories"].reverse()
    new["by_county"].reverse()
    result = diff_trees(old, new)
    assert not result.changed, result.changed
    assert not result.added and not result.removed


def test_a_changed_row_stays_attached_to_its_own_name() -> None:
    old = sample_tree()
    new = json.loads(json.dumps(old))
    new["territories"][0]["records_placed_here"] = 306
    result = diff_trees(old, new)
    assert len(result.changed) == 1
    # The pairing ran by territory name, so the one moved number belongs to Anza even
    # though PG&E's row sits at index 0 in both files.
    assert result.changed[0].path == "$.territories[0].records_placed_here"
    assert result.changed[0].before == 305
    assert result.changed[0].after == 306


def test_a_positional_collection_reports_movement_when_rows_swap() -> None:
    old = sample_tree()
    new = json.loads(json.dumps(old))
    # contested_groups carries no identifying field: identity is positional, and a size
    # swap reports every leaf under both rows rather than guessing which row is which.
    # The noise is visible and the reader judges it; the tool does not smooth it over.
    new["contested_groups"].reverse()
    result = diff_trees(old, new)
    paths = {change.path for change in result.changed}
    assert paths == {
        "$.contested_groups[0].records",
        "$.contested_groups[1].records",
        "$.contested_groups[0].territories[0]",
        "$.contested_groups[0].territories[1]",
        "$.contested_groups[1].territories[0]",
        "$.contested_groups[1].territories[1]",
    }


def test_a_scalar_replaced_by_a_container_is_one_change_whole() -> None:
    old = sample_tree()
    new = json.loads(json.dumps(old))
    new["by_year"][0]["year"] = {"value": 2024}
    result = diff_trees(old, new)
    assert len(result.changed) == 1
    assert result.changed[0].path == "$.by_year[0].year"


def test_bool_and_int_are_not_the_same_leaf() -> None:
    result = diff_trees({"flag": False}, {"flag": 0})
    assert len(result.changed) == 1


def test_an_empty_container_counts_as_a_leaf_on_each_side() -> None:
    gone = diff_trees({"rows": []}, {"rows": {"note": "none"}})
    assert len(gone.changed) == 1
    added = diff_trees({"rows": []}, {"rows": [], "extra": {}})
    assert [leaf.path for leaf in added.added] == ["$.extra"]


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["/does/not/exist.json", "/also/missing.json"], 2),
    ],
)
def test_bad_usage_exits_two(tmp_path: Path, argv: list[str], expected: int) -> None:
    assert main(argv) == expected


def test_main_prints_a_verdict_line(capsys: pytest.Capsys, tmp_path: Path) -> None:
    old = tmp_path / "old.json"
    new = tmp_path / "new.json"
    changed = sample_tree()
    changed["placement_coverage"]["fire_records"] = 132522
    old.write_text(json.dumps(sample_tree()), encoding="utf-8")
    new.write_text(json.dumps(changed), encoding="utf-8")
    assert main([str(old), str(new)]) == 0
    out = capsys.readouterr().out
    assert "1 changed." in out
    assert "Nothing was removed." in out


def write_pair(tmp_path: Path, old: dict, new: dict) -> tuple[str, str]:
    """Two artifacts on disk, as the paths `main` takes."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    old_path = tmp_path / "old.json"
    new_path = tmp_path / "new.json"
    old_path.write_text(json.dumps(old), encoding="utf-8")
    new_path.write_text(json.dumps(new), encoding="utf-8")
    return str(old_path), str(new_path)


def changed_and_added() -> dict:
    new = json.loads(json.dumps(sample_tree()))
    new["placement_coverage"]["fire_records"] = 132522
    new["attributability_by_fire"] = {"counties_named_in_the_record_set": 52}
    return new


def with_a_removal() -> dict:
    stripped = sample_tree()
    del stripped["placement_coverage"]["counts"]["placed"]
    return stripped


def test_the_default_output_is_byte_for_byte_what_it_printed_before_json_mode(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """`--json` is opt-in, and opt-in means the other path did not move."""
    old, new = write_pair(tmp_path / "one", sample_tree(), changed_and_added())
    assert main([old, new]) == 0
    assert capsys.readouterr().out == PLAIN_CHANGED_AND_ADDED

    old, new = write_pair(tmp_path / "two", sample_tree(), with_a_removal())
    assert main([old, new]) == 1
    assert capsys.readouterr().out == PLAIN_REFUSED

    old, new = write_pair(tmp_path / "three", sample_tree(), sample_tree())
    assert main([old, new]) == 0
    assert capsys.readouterr().out == PLAIN_IDENTICAL


def test_json_mode_prints_one_object_and_nothing_else(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    old, new = write_pair(tmp_path, sample_tree(), changed_and_added())
    assert main(["--json", old, new]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert isinstance(payload, dict)


def test_json_mode_counts_agree_with_a_direct_diff_trees_call(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """The mode reports the comparison; it does not do a second one of its own."""
    new_tree = changed_and_added()
    old, new = write_pair(tmp_path, sample_tree(), new_tree)
    assert main(["--json", old, new]) == 0
    payload = json.loads(capsys.readouterr().out)

    expected = diff_trees(sample_tree(), new_tree)
    assert payload["counts"] == {
        "added": len(expected.added),
        "changed": len(expected.changed),
        "removed": len(expected.removed),
        "total": expected.total,
        "unchanged": expected.unchanged,
    }
    assert [row["path"] for row in payload["added"]] == [
        leaf.path for leaf in expected.added
    ]
    assert [row["path"] for row in payload["changed"]] == [
        change.path for change in expected.changed
    ]
    assert payload["changed"][0]["before"] == 132520
    assert payload["changed"][0]["after"] == 132522
    assert payload["refused"] is False
    assert payload["allow_removals"] is False


def test_json_mode_carries_a_long_value_whole_where_the_prose_shortens_it(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """A machine-readable value that is not the value would be worse than no mode."""
    long_note = "b" * 500
    old_tree = {"note": "a"}
    new_tree = {"note": long_note}
    old, new = write_pair(tmp_path, old_tree, new_tree)

    assert main([old, new]) == 0
    assert "\u2026" in capsys.readouterr().out

    assert main(["--json", old, new]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["changed"][0]["after"] == long_note


def test_json_mode_does_not_soften_the_removal_refusal(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    old, new = write_pair(tmp_path, sample_tree(), with_a_removal())

    assert main(["--json", old, new]) == 1
    refused = json.loads(capsys.readouterr().out)
    assert refused["refused"] is True
    assert refused["allow_removals"] is False
    assert refused["counts"]["removed"] == 1
    assert refused["removed"] == [
        {"path": "$.placement_coverage.counts.placed", "value": 82353}
    ]

    assert main(["--json", "--allow-removals", old, new]) == 0
    allowed = json.loads(capsys.readouterr().out)
    assert allowed["refused"] is False
    assert allowed["allow_removals"] is True
    # The allowed run still says a value went. `refused` is about this run, not about
    # whether the record set kept everything it published.
    assert allowed["counts"]["removed"] == 1


def test_json_mode_leaves_stdout_empty_on_bad_usage(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Half an object is worse than none: a usage failure writes prose to stderr."""
    assert main(["--json", "/does/not/exist.json", "/also/missing.json"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "could not read an artifact" in captured.err
