STATUS: LOW-PRIORITY RESERVE
NOT PRODUCTION AUTHORITY
NOT AUTHORIZED FOR UI OR RUNTIME INTEGRATION
SAFE TO LEAVE INCOMPLETE
IMPLEMENT ONLY UNDER A FUTURE EXPLICIT CARD

# H3 Frame / Time Helpers

## PURPOSE

Keep H3 frame index, timestamp, duration, playback, Start/End, and continuation
metadata consistent across future media operations.

## LIKELY HOME

A pure H3 media/time core owned by the H3 domain. It must not become a shared
timeline or Manga dependency.

## PREREQUISITES

An H3-owned timebase/FPS contract, rounding rules, frame numbering, and clear
handling of missing or variable-duration media.

## DO NOT IMPLEMENT YET

Do not add timeline UI, editing, Start/End generation, cross-domain time
conversion, or runtime graph changes. A future Card must provide H3-specific
fixtures and Owner/runtime evidence where needed.
