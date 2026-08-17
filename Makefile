.PHONY: verify lock-check sync lint format typecheck test audit \
        report report-offline determinism acquire

# CI and `make verify` run the same list. The two MUST stay identical.
# See CONTRIBUTING.md and .github/workflows/ci.yml.
verify: lock-check sync lint format typecheck test audit report-offline determinism

# The lockfile-drift gate. `uv sync --frozen` is not one: against a pyproject.toml the
# lockfile does not satisfy, `uv lock --check` exits 1, `uv sync --locked` exits 1, and
# `uv sync --frozen` exits 0 and installs the stale set. `--frozen` means "do not
# resolve", not "the lock is current".
lock-check:
	uv lock --check

sync:
	uv sync --locked

lint:
	uv run ruff check .

format:
	uv run ruff format --check .

typecheck:
	uv run mypy --strict src

test:
	uv run pytest -n auto --cov=src --cov-branch --cov-report=xml --cov-fail-under=90

audit:
	uv run pip-audit

# Build the published tree from locally acquired files. data/raw/ is never in git and
# never in CI, so this target only runs on a machine that has run `make acquire`.
report:
	uv run python -m inspected.cli \
		--dins data/raw/dins_postfire.json \
		--iou-pou data/raw/else_iou_pou.geojson \
		--other data/raw/else_other.geojson \
		--out published

# The same pipeline over committed fixtures: runs anywhere, output flagged is_fixture.
report-offline:
	uv run python -m inspected.cli --fixture \
		--dins fixtures/dins_sample.json \
		--iou-pou fixtures/else_iou_pou_sample.geojson \
		--other fixtures/else_other_sample.geojson \
		--out build/offline

# The gate behind the byte-identical claim. Two builds into two directories, compared by
# tools/determinism.sh, which refuses an empty or missing tree instead of calling it a
# match. tests/test_cli_and_determinism.py runs the script against trees that should fail
# it, so this gate is known to be able to fail.
determinism:
	rm -rf build/run-one build/run-two
	uv run python -m inspected.cli --fixture \
		--dins fixtures/dins_sample.json \
		--iou-pou fixtures/else_iou_pou_sample.geojson \
		--other fixtures/else_other_sample.geojson \
		--out build/run-one
	uv run python -m inspected.cli --fixture \
		--dins fixtures/dins_sample.json \
		--iou-pou fixtures/else_iou_pou_sample.geojson \
		--other fixtures/else_other_sample.geojson \
		--out build/run-two
	tools/determinism.sh build/run-one build/run-two

# Network. Run by hand, never from a build. See PROVENANCE.md.
acquire:
	uv run python -m inspected.acquire --out data/raw
