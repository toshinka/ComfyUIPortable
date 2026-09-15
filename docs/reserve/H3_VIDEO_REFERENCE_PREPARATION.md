STATUS: LOW-PRIORITY RESERVE
NOT PRODUCTION AUTHORITY
NOT AUTHORIZED FOR UI OR RUNTIME INTEGRATION
SAFE TO LEAVE INCOMPLETE
IMPLEMENT ONLY UNDER A FUTURE EXPLICIT CARD

# H3 Video Reference Preparation

## PURPOSE

Validate and summarize subject/reference media before an H3 job while keeping
reference semantics separate from Manga CAST/Reference.

## LIKELY HOME

A read-only H3 local service plus a thin H3 domain adapter, using canonical
media identity, bounded metadata, and the existing H3 reference contracts.

## PREREQUISITES

H3-specific subject/reference meaning, supported media policy, safe locator
rules, frame/time handling, and capability reporting for the eventual route.

## DO NOT IMPLEMENT YET

Do not load models, preprocess or generate media, add Start/End or
multi-reference runtime paths, change Manga behavior, or introduce network
providers. Preparation remains a headless contract until a separate H3 Card.
