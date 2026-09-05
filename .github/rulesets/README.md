# The committed branch ruleset

`main.json` is a copy of the ruleset that is live on `main`, captured from
`GET /repos/{owner}/{repo}/rulesets/{id}` on 2026-09-05.

It exists because branch protection is otherwise a setting with no evidence:
it lives in repository settings, it can be changed or removed without a commit,
and nothing in the history would show it. The README's CI/CD row claims `main`
is PR-only behind its gates; this file is what that claim is checked against.

## What it does not claim

**The repository-admin role can bypass every rule, always.** That is in the file
as `bypass_actors`, faithfully, rather than omitted to make the posture read
better. It is deliberate: a solo maintainer who cannot push to their own
default branch has locked themselves out rather than hardened anything, and that
is why this file is evidence of intent rather than proof of enforcement against
the owner.

## What holds it to the code

`tests/test_ruleset.py` asserts that **every job that runs on `pull_request` is
named as a required status check**. That is the invariant worth gating: adding a
job to CI without making it required produces a check that looks like a gate on
the pull-request page and blocks nothing. The test reads the workflows rather
than trusting a list, so it fails when the two drift.

It does **not** assert that the live ruleset still matches this file, because a
public-scope token cannot read `bypass_actors` and a check that silently degrades
to comparing a subset is worse than one that states its limit. Re-capture with:

```sh
gh api repos/ChelseaKR/wildfire-service-territory-overlap/rulesets/21222489 \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps({k: d[k] for k in ("name","target","enforcement","conditions","bypass_actors","rules")}, indent=2))' \
  > .github/rulesets/main.json
```
