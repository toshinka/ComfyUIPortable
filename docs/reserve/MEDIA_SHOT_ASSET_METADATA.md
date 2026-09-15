STATUS: LOW-PRIORITY RESERVE
NOT PRODUCTION AUTHORITY
NOT AUTHORIZED FOR UI OR RUNTIME INTEGRATION
SAFE TO LEAVE INCOMPLETE
IMPLEMENT ONLY UNDER A FUTURE EXPLICIT CARD

# Media / Shot Asset Metadata

## PURPOSE

Keep a result associated with a shot, take, duration, media type, and source
identity so later Asset/Assemble work does not lose provenance.

## LIKELY HOME

A bounded local service at the future Asset/Assemble boundary, consuming
existing H3 or Manga result/take identities without merging their semantics.

## PREREQUISITES

An Asset/Assemble owner, field vocabulary, canonical media identity, and a
decision about immutable versus editable metadata.

## DO NOT IMPLEMENT YET

Do not design the complete Asset schema, create a shot database, change
generation history, add timeline behavior, or build an Assemble workspace.
Record only the provenance need until a separate Card defines the boundary.
