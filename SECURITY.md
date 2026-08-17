# Security

## Reporting

Report a vulnerability through GitHub private vulnerability reporting on this repository.
Acknowledgment target is 72 hours. Please do not open a public issue for a security
report.

## What this project is, in security terms

An offline command-line tool over two public datasets. It has no server, no accounts, no
network listener, and no runtime that anyone else operates. It opens a socket in exactly
one place, `src/inspected/acquire.py`, which is run by hand and never from a build or CI.

## The parts worth attacking

- **`src/inspected/acquire.py`** is the only code that reads a remote host. It pins the
  scheme to HTTPS, sends a User-Agent naming the project, stops on 401, 403 and 429
  rather than routing around them, and refuses a response that is not JSON. There is no
  fallback path and no retry under a different identity.
- **`src/inspected/artifacts.py`** decides what is allowed to be written. A change that
  weakens a rule there is a change to what this project will publish about somebody.
- **`src/inspected/sources.py`** holds the reviewed endpoints. A change to a URL there
  points the acquisition somewhere new.

`.github/CODEOWNERS` routes all three.

## Data handling

The CAL FIRE retrieval is structure-level. Site addresses, parcel numbers and assessed
values are published by CAL FIRE and are deliberately never requested; a test asserts
that. Coordinates are requested, are used only to answer which polygon a point is in,
are never written to a published artifact, and a test refuses an artifact containing one.
`data/raw/` is gitignored.

## Supply chain

Dependencies are locked in `uv.lock` and installed with `uv sync --locked`. One
dependency, `perimeter`, is a git reference pinned to a full commit SHA. GitHub Actions
are pinned to full commit SHAs with the version in a trailing comment. Workflows declare
`permissions: contents: read` at the top level and widen only where a job needs it.
`pip-audit`, `gitleaks`, `semgrep`, `zizmor` and CodeQL run in CI.
