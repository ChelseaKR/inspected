default: help

.PHONY: default help verify lock-check sync lint format typecheck test audit \
        report report-offline determinism acquire

# Self-documenting Makefile: targets with `##` comments are parsed and displayed by help.
help: ## Show this help message
	@awk '/^[a-zA-Z_-]+:.*?##/ { sub(/:.*?## */, "\t"); split($$0, a, "\t"); printf "  %-16s %s\n", a[1], a[2] }' $(MAKEFILE_LIST)

# CI and `make verify` run the same list. The two MUST stay identical.
# See CONTRIBUTING.md and .github/workflows/ci.yml.
verify: lock-check sync lint format typecheck test audit report-offline determinism ## Run the gates required by CI (lock-check, sync, lint, format, typecheck, test, audit, report-offline, determinism)

# The lockfile-drift gate. `uv sync --frozen` is not one: against a pyproject.toml the
# lockfile does not satisfy, `uv lock --check` exits 1, `uv sync --locked` exits 1, and
# `uv sync --frozen` exits 0 and installs the stale set. `--frozen` means "do not
# resolve", not "the lock is current".
lock-check: ## Check uv.lock matches pyproject.toml without resolving or modifying
	uv lock --check

sync: ## Install locked dependencies into the virtualenv
	uv sync --locked

lint: ## Run ruff linter across the repository
	uv run ruff check .

format: ## Check code formatting with ruff without modifying files
	uv run ruff format --check .

typecheck: ## Run mypy in strict mode over src/
	uv run mypy --strict src

test: ## Run test suite with branch coverage and fail if under 90%
	uv run pytest -n auto --cov=src --cov-branch --cov-report=xml --cov-fail-under=90

audit: ## Audit installed dependencies for known vulnerabilities with pip-audit
	uv run pip-audit

# Build the published tree from locally acquired files. data/raw/ is never in git and
# never in CI, so this target only runs on a machine that has run `make acquire`.
report: ## Build the published tree from locally acquired raw data
	uv run python -m wildfire_service_territory_overlap.cli \
		--dins data/raw/dins_postfire.json \
		--iou-pou data/raw/else_iou_pou.geojson \
		--other data/raw/else_other.geojson \
		--counties data/raw/county_boundaries.geojson \
		--out published

# The same pipeline over committed fixtures: runs anywhere, output flagged is_fixture.
report-offline: ## Build offline fixture report without network access
	uv run python -m wildfire_service_territory_overlap.cli --fixture \
		--dins fixtures/dins_sample.json \
		--iou-pou fixtures/else_iou_pou_sample.geojson \
		--other fixtures/else_other_sample.geojson \
		--counties fixtures/county_boundaries_sample.geojson \
		--out build/offline

# The gate behind the byte-identical claim. Two builds into two directories, compared by
# tools/determinism.sh, which refuses an empty or missing tree instead of calling it a
# match. tests/test_cli_and_determinism.py runs the script against trees that should fail
# it, so this gate is known to be able to fail.
determinism: ## Verify deterministic builds by comparing two fresh fixture runs
	rm -rf build/run-one build/run-two
	uv run python -m wildfire_service_territory_overlap.cli --fixture \
		--dins fixtures/dins_sample.json \
		--iou-pou fixtures/else_iou_pou_sample.geojson \
		--other fixtures/else_other_sample.geojson \
		--counties fixtures/county_boundaries_sample.geojson \
		--out build/run-one
	uv run python -m wildfire_service_territory_overlap.cli --fixture \
		--dins fixtures/dins_sample.json \
		--iou-pou fixtures/else_iou_pou_sample.geojson \
		--other fixtures/else_other_sample.geojson \
		--counties fixtures/county_boundaries_sample.geojson \
		--out build/run-two
	tools/determinism.sh build/run-one build/run-two

# Network. Run by hand, never from a build. See PROVENANCE.md.
acquire: ## Fetch upstream data sources over network into data/raw
	uv run python -m wildfire_service_territory_overlap.acquire --out data/raw
