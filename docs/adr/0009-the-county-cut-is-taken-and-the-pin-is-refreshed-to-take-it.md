# 9. The county cut is taken, and the pin is refreshed in the open to take it

Date: 2026-08-17

## Status

Accepted. Extends ADR 0008, which is not superseded.

## Context

ADR 0008 published the contested share by incident and by incident year and recorded a
third cut as untested: *"By county. Not tested. CAL FIRE publishes a county field and
this project does not fetch it. Fetching it means a new acquisition and a new pin, which
moves every figure in the repository, so it is named as an open item rather than
half-built."*

That was the right thing to write down and the wrong place to leave it. A cut that is
named as unavailable because taking it would disturb the pin is a cut nobody ever takes,
and the reason given was about the cost of a refresh rather than about the measurement.
The cost is real: a new acquisition is a new hash, a new byte count and a new set of
records, and every figure in the repository is downstream of those.

The honest way to pay it is to pay it visibly. A published number that changes is fine.
A published number that changes without anybody saying so is not, and the difference
between the two is entirely in whether the change was measured.

## Decision

Fetch `COUNTY`, refresh the pin, and publish what the refresh moved.

`COUNTY` is the eighth field the acquisition requests. It is a published administrative
area name, coarser by orders of magnitude than the coordinate this project already reads
and does not republish, and it reaches the output only as a row label beside a count. The
address, parcel and assessed-value columns remain unfetched and a test still asserts it.

The cut itself is the one the year cut already is: for each county the publisher names,
the fire records, the records that could be classified, and the contested share over the
second of those, with a Wilson interval. In name order, never in size order. No county is
compared against another and no difference between two counties is published.

**No damage rate is published for a county.** ADR 0004 refuses that arithmetic for a
territory because it would describe which fires burned inside a boundary while wearing a
company's name. Inside a county line it is the same arithmetic wearing a place name, and
`tests/test_published.py` refuses a county row carrying a key that names damage.

**The refresh is reported leaf by leaf rather than asserted to be safe.** The artifact
built after the refresh was compared against the artifact built before it, at every
published value.

## Consequences

The refresh moved nothing. 4,370 published values before, none removed, none changed, and
the one prose note that differs is one this decision rewrote by hand. The reason is
visible in the retrieval rather than inferred: the re-acquired DINS file is byte-for-byte
the previously pinned file once the new column is removed, and both territory layers came
back with the hashes already recorded. PROVENANCE.md states this, with the counts.

That is a fact about this refresh and not a property of refreshes. The next one will
land in a file CAL FIRE has added records to, and the comparison is what will say so.

**The cut is a third confirmation of ADR 0008 rather than a new finding, and a strong
one.** 52 counties are named in the record set and 30 records carry no county name at
all. In 36 of the 52 the contested share is zero: not low, zero. Where it is not zero it
is mostly very high, and the counties it is high in are the ones the large overlapping
outlines cover. Whether a record can be attributed is settled by where its fire burned,
and the county cut says that in geography rather than in fire names.

**A reader can now locate the overlap on a map without this project drawing one.** That
is the useful half. The half that is deliberately not built: no county is joined to a
territory, no table says which entity serves which county, and nothing here reads a
county as evidence about who owns a wire in it.
