# Draft: request for documentation of the Type field

Status: **draft, not sent**. Sending date and any response get recorded in
`PROVENANCE.md`. Recipient placeholder until then.

---

To: [CEC contact named in the layer's own metadata text]
From: Chelsea Kelly-Reif, independent project below; not affiliated with CAL FIRE, the
California Energy Commission, or any electric utility
Subject: Documentation request: coded values for the Type field in Electric Load
Serving Entities item 30410214d637434ba1003cbdcc32cf55

Hello,

I maintain an unofficial open-source project,
https://github.com/ChelseaKR/wildfire-service-territory-overlap, which measures how much of CAL FIRE's wildfire
damage-inspection record set falls inside the service territory outlines your agency
publishes. One field of that layer decides most of my methodology, and I cannot find
any place where its values are defined by the party that publishes them.

**The field:** `Type` in items 30410214d637434ba1003cbdcc32cf55 (IOU & POU) and
07224640a2fe42f89399be796e7b8810 (other), as retrieved 2026-08-23.

**What I checked on that date:**

- the layer metadata carries no description on the `Type` field and no coded-value
  domain;
- the FGDC metadata record carries no entity and attribute section;
- neither item has a data dictionary attached;
- the published load serving entities page names four categories in prose and does not
  name `Tribal` or `ADMIN` at all.

**The values present, in name order:** ADMIN, CCA, CO-OP, IOU, POU, Tribal.

My inclusion rule reads CO-OP, IOU, POU and Tribal as retail service territories and
excludes ADMIN and CCA, on reasoning recorded publicly in my repository's decision log.
What I cannot do is check that reading against yours, because yours is nowhere written
down. The cost of the unreviewed half of the rule is measured and small; the exclusions
are what carry weight, and a documented domain would either confirm them or change
them.

**The ask:** a coded-value domain for the `Type` field, or any written definition of
the values it carries, or a correction if some values should not appear in the layer at
all. If definitions exist somewhere I failed to look, a pointer would settle it and I
will cite it.

The project publishes counts only: no coordinates, addresses, or parcel-level data,
and no comparison between utilities.

Chelsea Kelly-Reif
[sending address]
