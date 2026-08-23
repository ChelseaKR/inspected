# Draft: overlap finding reported to the CEC

Status: **draft, not sent**. Sending date and any response get recorded in
`PROVENANCE.md`. Recipient placeholder until then.

---

To: [CEC contact named in the layer's own metadata text]
From: Chelsea Kelly-Reif, independent project below; not affiliated with CAL FIRE, the
California Energy Commission, or any electric utility
Subject: Overlapping electric load serving entity boundaries in item
30410214d637434ba1003cbdcc32cf55, measured over CAL FIRE damage-inspection records

Hello,

I maintain an unofficial, open-source measurement project,
https://github.com/ChelseaKR/inspected, which places CAL FIRE's postfire
damage-inspection records (DINS, POSTFIRE_MASTER_DATA_SHARE layer 0, retrieved
2026-08-17) inside your published Electric Load Serving Entities outlines (items
30410214d637434ba1003cbdcc32cf55 and 07224640a2fe42f89399be796e7b8810, last modified
by you 2026-08-12). Your metadata invites reports about these layers, and this is one.

**What I measured.** Of 132,520 wildfire records, 82,353 (62.1%) fall inside exactly
one outline you publish as an IOU, POU, cooperative or tribal service territory;
50,167 (37.9%) fall inside two or more at once; none falls outside all of them.

**What I am not claiming.** Nothing about any utility's infrastructure, posture or
performance. The overlaps look like a property of how the boundary layer was
assembled, and my project deliberately awards contested records to nobody.

**The twelve overlapping combinations, by size:** Metropolitan Water District of So.
Cal with Southern California Edison, 25,345 records; Pacific Gas & Electric with Power
and Water Resource Pooling Authority, 12,241; Los Angeles DWP with Metropolitan Water
District, 9,794; Metropolitan Water District with Pasadena, 1,880; Metropolitan Water
District with SDG&E, 620; Lassen MUD with Plumas-Sierra REC, 85; Healdsburg with
Power and Water Resource Pooling Authority, 69; Anaheim with Metropolitan Water
District, 46; Riverside with Metropolitan Water District, 42; Modesto Irrigation
District with PG&E, 40; Hetch Hetchy with PG&E, 4; PacifiCorp with Surprise Valley
Electrification, 1.

A related fact, offered in the same spirit: eight of the 59 outlines fail an OGC
validity check on retrieval, including two of the largest territories in the state,
and my measurement has to choose a repair before asking containment questions. Under
two standard repairs, 927 records come out differently. The repaired polygons are
named in the generated report.

**The question:** are these overlaps intended, for example because a polygon
represents something other than exclusive retail service, or should some be reported
as corrections? If it would help, I can supply the full generated report, the
per-combination counts with intervals, or the exact retrieval artifacts behind every
number above.

The project publishes counts only: no coordinates, addresses, or parcel-level data of
any kind, and no comparison between utilities.

Chelsea Kelly-Reif
[sending address]
