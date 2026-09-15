STATUS: LOW-PRIORITY RESERVE
NOT PRODUCTION AUTHORITY
NOT AUTHORIZED FOR UI OR RUNTIME INTEGRATION
SAFE TO LEAVE INCOMPLETE
IMPLEMENT ONLY UNDER A FUTURE EXPLICIT CARD

# Result-to-Asset Identity / Conversion

## PURPOSE

Preserve the relationship between a generated result, its settings, source
job/take, and a future reusable Asset without redesigning History or inventing
an Asset schema early.

## LIKELY HOME

A future domain adapter at the Asset/Assemble boundary, consuming existing
result metadata, job identity, canonical output locator, and provenance.

## PREREQUISITES

An explicitly owned Asset model, stable result/take identity, canonical
relative references, and a decision about whether conversion is a copy,
reference, or immutable snapshot.

## DO NOT IMPLEMENT YET

Do not create an Asset database, migrate History, copy generated media, merge
Manga/H3 timelines, or add an Assemble workspace. Preserve only the idea until
a separate integration Card defines ownership and side effects.
