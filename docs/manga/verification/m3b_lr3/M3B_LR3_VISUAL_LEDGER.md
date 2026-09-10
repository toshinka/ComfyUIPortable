# M3B-LR3 Visual Ledger

Date: 2026-09-10 JST  
Card: M3B-LR3 — Derived Clean Guide A/B Research Slice  
Live viewer: local ComfyUI `/view`, browser review PASS  
Contact sheet: `M3B_LR3_CONTACT_SHEET.png`

The six outputs use the fixed LR2R1 document and `input_mode: simple`. OFF
bypasses ControlNet. RAW uses the existing Rough Guide bridge image. CLEAN
uses the Figure-geometry-derived black flat-silhouette image. Both ON
conditions use strength `0.75`, interval `0.0-1.0`, and no preprocessor.

## Seed 42

| Condition | Evidence | SHA256 | Placement | Quality | Visual review |
|---|---|---|---|---|---|
| OFF | `SEED_A_OFF.png` | `b155435e08fce06968c580dc0704e93870b71de2e68efbc8e34d36536afed48c` | NONE | USABLE | Multi-panel page; no stable left/right two-Figure composition. |
| RAW | `SEED_A_RAW.png` | `9275aa7fdfec88e4feeb29cf18d411d92136ac6ba908b57b8564b0c0591485aa` | DEGRADED | DEGRADED | Left/right figures appear in the central classroom panel, but raw-guide lines and box geometry are intrusive; extra close-up panels remain. |
| CLEAN | `SEED_A_CLEAN.png` | `d9e9c066b18fab6632c8c99bef2dd7ea4f2bac7cab064b6855ec0a89ed267d73` | CLEAR | USABLE | Two figures are clearly left/right in one classroom image. Raw-guide geometry is absent. Both render standing rather than the requested seated-right variation. |

Seed 42 CLEAN improves intended placement against OFF and RAW and materially
reduces the RAW artifact geometry.

## Seed 77

| Condition | Evidence | SHA256 | Placement | Quality | Visual review |
|---|---|---|---|---|---|
| OFF | `SEED_B_OFF.png` | `55801e8335ca17fa57ddffd738388b5f17e288fbfa414cd91d1cb763c441484f` | NONE | USABLE | Multi-panel/group composition without stable intended two-Figure placement. |
| RAW | `SEED_B_RAW.png` | `81eeb9ad29276f40dc71a975e1e9965dd691fb5a86953e2ce55c0fe2e1414a27` | DEGRADED | DEGRADED | Intrusive raw-guide box and zig-zag line remain; three visible people make the intended association unstable. |
| CLEAN | `SEED_B_CLEAN.png` | `625dbc9f5125bca3d328864b2303017255818090c4eb510b0edb5ee41ae34c44` | NONE | USABLE | Clean classroom image with no raw-guide artifact, but only one visible person; the second Figure is lost. |

Seed 77 CLEAN is visually cleaner than RAW but does not preserve the intended
two-Figure placement. This is the decisive counterexample to a BOTH-seed
support classification.

## Cross-seed findings

- Raw-guide artifacts are present in both RAW outputs: line/box geometry is
  visibly reproduced by the generation.
- CLEAN removes that raw-guide geometry in both seeds.
- CLEAN placement is seed-sensitive: CLEAR for Seed 42 and NONE for Seed 77.
- The generated images retain meaningful seed variation: Seed 42 and Seed 77
  differ visually and by hash for OFF, RAW, and CLEAN.
- The clean Figure masks and `instance_id` links are provenance only. The
  ControlNet image is applied to the whole page; no regional ControlNet or
  Character Instance-specific conditioning is used.

## Enum summary

| Measure | Result |
|---|---|
| RAW placement | DEGRADED |
| RAW quality | DEGRADED |
| CLEAN placement | WEAK (Seed 42 CLEAR, Seed 77 NONE) |
| CLEAN quality | USABLE |
| Seed variation | PRESENT |
| Option A provisional result | `OPTION_A_INCONCLUSIVE` |

The result is INCONCLUSIVE under the Card rule because only one of the two
seeds improves intended placement. It does not reject derived Guides in
general, ControlNet in general, or any setting outside this fixed
flat-silhouette / strength `0.75` / full-interval / whole-page experiment.
