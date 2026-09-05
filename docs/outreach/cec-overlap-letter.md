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
https://github.com/ChelseaKR/wildfire-service-territory-overlap, which places CAL FIRE's postfire
damage-inspection records (DINS, POSTFIRE_MASTER_DATA_SHARE layer 0, retrieved
2026-08-23) inside your published Electric Load Serving Entities outlines (items
30410214d637434ba1003cbdcc32cf55 and 07224640a2fe42f89399be796e7b8810, last modified
by you 2026-08-12). Your metadata invites reports about these layers, and this is one.

**What I measured.** Of 132,520 wildfire records, 82,353 (62.1%) fall inside exactly
one outline you publish with a `Type` of CO-OP, IOU, POU or Tribal; 50,167 (37.9%)
fall inside two or more at once; none falls outside all of them.

**What I am not claiming.** Nothing about any utility's infrastructure, posture or
performance. The overlaps look like a property of how the boundary layer was
assembled, and my project deliberately awards contested records to nobody.

**All 12 overlapping combinations, by size, named as your layer names them.** These
are every combination, not the largest few: their records sum to the 50,167 above.

- Metropolitan Water District of So. Cal with Southern California Edison: 25,345
  records
- Pacific Gas & Electric Company with Power and Water Resource Pooling Authority:
  12,241 records
- Los Angeles Department of Water & Power with Metropolitan Water District of So.
  Cal: 9,794 records
- Metropolitan Water District of So. Cal with Pasadena Water & Power: 1,880 records
- Metropolitan Water District of So. Cal with San Diego Gas & Electric: 620 records
- Lassen Municipal Utility District with Plumas-Sierra Rural Electric Cooperative: 85
  records
- City of Healdsburg Electric Department with Power and Water Resource Pooling
  Authority: 69 records
- City of Anaheim Public Utilities Department with Metropolitan Water District of So.
  Cal: 46 records
- City of Riverside with Metropolitan Water District of So. Cal: 42 records
- Modesto Irrigation District with Pacific Gas & Electric Company: 40 records
- City and County of San Francisco - Hetch Hetchy Water and Power with Pacific Gas &
  Electric Company: 4 records
- PacifiCorp with Surprise Valley Electrification Corporation: 1 record

A related fact, offered in the same spirit: 8 of the 59 outlines fail an OGC validity
check on retrieval, including two of the largest territories in the state, and my
measurement has to choose a repair before asking containment questions. Under two
standard repairs, 927 records come out differently. The repaired polygons are named in
the generated report.

**The question:** are these overlaps intended, for example because a polygon
represents something other than exclusive retail service, or should some be reported
as corrections? If it would help, I can supply the full generated report, the
per-combination counts with intervals, or the exact retrieval artifacts behind every
number above.

The project publishes counts only: no coordinates, addresses, or parcel-level data of
any kind, and no comparison between utilities.

Chelsea Kelly-Reif
[sending address]
