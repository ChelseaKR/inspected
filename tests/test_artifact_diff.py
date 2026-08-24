"""The refresh diff, held to the behaviour the refresh procedure will rely on."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wildfire_service_territory_overlap.artifact_diff import diff_trees, main


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


def test_main_prints_a_verdict_line(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
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


def test_main_json_output_mode(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    old = tmp_path / "old.json"
    new = tmp_path / "new.json"
    changed = sample_tree()
    changed["placement_coverage"]["fire_records"] = 132522
    changed["attributability_by_fire"] = {"counties_named_in_the_record_set": 52}
    old.write_text(json.dumps(sample_tree()), encoding="utf-8")
    new.write_text(json.dumps(changed), encoding="utf-8")

    # Byte identical human readable without flag
    main([str(old), str(new)])
    plain_out = capsys.readouterr().out
    assert "1 added" in plain_out
    assert "1 changed" in plain_out
    assert "Nothing was removed." in plain_out

    # JSON mode
    exit_code = main(["--json", str(old), str(new)])
    assert exit_code == 0
    json_out = capsys.readouterr().out
    data = json.loads(json_out)

    expected = diff_trees(sample_tree(), changed)
    assert data["counts"]["total"] == expected.total
    assert data["counts"]["added"] == len(expected.added)
    assert data["counts"]["removed"] == len(expected.removed)
    assert data["counts"]["changed"] == len(expected.changed)
    assert data["counts"]["unchanged"] == expected.unchanged
    assert len(data["added"]) == len(expected.added)
    assert len(data["removed"]) == len(expected.removed)
    assert len(data["changed"]) == len(expected.changed)
    assert data["refused"] is False


def test_main_json_removal_refusal(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    old = tmp_path / "old.json"
    new = tmp_path / "new.json"
    stripped = sample_tree()
    del stripped["placement_coverage"]["counts"]["placed"]
    old.write_text(json.dumps(sample_tree()), encoding="utf-8")
    new.write_text(json.dumps(stripped), encoding="utf-8")

    # Without --allow-removals: exits 1 and refused is True
    refused_code = main(["--json", str(old), str(new)])
    assert refused_code == 1
    refused_data = json.loads(capsys.readouterr().out)
    assert refused_data["refused"] is True
    assert refused_data["counts"]["removed"] == 1

    # With --allow-removals: exits 0 and refused is False
    allowed_code = main(["--json", "--allow-removals", str(old), str(new)])
    assert allowed_code == 0
    allowed_data = json.loads(capsys.readouterr().out)
    assert allowed_data["refused"] is False
    assert allowed_data["counts"]["removed"] == 1
