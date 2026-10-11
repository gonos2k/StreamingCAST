---
title: StreamingCAST Hot Cache
type: meta
date_modified: 2026-10-12
---
# Hot Cache

## Current Focus
Integrate the ERA5-aligned staged roadmap and historical external benchmark
references into source-backed project management. PR #3 and PR #4 are merged
into main (checked through GitHub on 2026-10-12). PR #5 was merged into the data
branch, not main. This review branch combines that knowledge setup with current
main; it does not publish a merge to main.

## Work and Acceptance Checks
| Work | State | Acceptance / evidence |
| --- | --- | --- |
| ERA5 inventory / structural inspector | PR #3 merged | 44 stores, 643,500 chunks; original 115-test scope, limited engineering evidence |
| ERA5-aligned plan / comparison contracts | PR #4 merged | [[sources/staged-roadmap]], [[sources/comparison-acceptance]], [[sources/execution-scope]]; original 40 new tests and historical 147-test subset |
| External reference registry | 63 published numbers; local weather scores NOT_RUN | [[sources/published-score-register]]: 60 RMSE at 24h and 3 ROCSS at 120h; differing protocols remain distinct |
| Pre-fix combined engineering regression | 155 passed; 18 deprecation warnings, 2 subtests | [Integration receipt](../evidence/knowledge/integration_check.json); synthetic/contracts only, no raw weather run |
| Post-review regression | 181 passed; 18 deprecation warnings, 2 subtests | [Review-fix receipt](../evidence/knowledge/review_fix_check.json), with working-source hashes; real weather NOT_RUN |
| Benchmark review hardening | 66 contract tests passed; Red review passed | [[sources/comparison-hardening]]; pressure/quantile/interval identity, zero MSE, finite arithmetic and source axes |
| kg + Graphify integration | Main-based review branch; schema/link/hash/graph checks passed | Preserve original Source snapshots, refresh changed code/document relationships and input hashes |
| R0 local data/time contracts | Next bounded task | Confirm P6h endpoints/units, sp/static fields/subsurface masks, variable quality and independent split history |
| R1 G29+P6h baseline | After accepted R0 contracts | Persistence and train-only climatology on fixed held-out cases; 1 degree development and 1.5 degree evaluation scored separately |
| R2 regional / R3 true hourly / R4 expansion | Planned, unimplemented | Genuine continuous hourly windows, pressure/geometry conversion, S1/S2 and hourly-rain validation before expansion |
| Real weather / D83 failure diagnosis | Unrun; unresolved | No published reference, synthetic contract test or graph check substitutes for independent forecasts |

## Next Bounded Action
Produce an R0 acceptance record for the existing six-hour cache: verify the actual
precipitation interval and units from its generating code/metadata; identify sp,
static fields and a validated subsurface mask; record time/variable sample quality
and train1979–2017 / select2018 / calibrate2019 / test2020 usage history.
If sp remains unavailable, limit the first evaluation path to four surface
variables. Then compute persistence and train-only climatology on frozen cases.
See [revised plan](../docs/ERA5_ALIGNED_PLAN.md) sections 2, 5 and 6.

## Key Tensions / Open Questions
- The earlier hourly-first next action is a historical plan. The new staged roadmap
  uses existing G29+P6h for a six-hour baseline while retaining true D83+P1h goals.
- Published 2020 reference scores are historical targets; conditions, raw cases,
  checkpoint lineage and independent training history must match before comparison.
- 2020 regional pilot tuning can compromise the proposed 2020 independent test.
- Six-hour sampling does not identify local semidiurnal sine phase; temporal
  interpolation is derived data, not observed hourly truth.
- ROCSS threshold artifact hash is verified, but single-class-cell handling and exact scoring revision/forecast lineage remain unresolved; historical references cannot approve local skill.
- Availability timestamps, precipitation endpoints and missing pressure/mask inputs
  remain data contracts to verify. Full payload integrity and weather skill are unproved.
- 115 (inventory), 147 (PR #4 historical subset) and any new combined run have
  distinct code snapshots; retain their provenance rather than replacing counts.

## Recent Activity
- [2026-10-12] Confirmed live GitHub merge state and combined main's benchmark plan with the knowledge branch for review.
- [2026-10-12] Ingested four new Source snapshots; original pages and evidence preserved.
- [2026-10-12] Pre-fix combined 155-test regression passed; benchmark arithmetic matches the original non-environment results.
- [2026-10-12] Post-merge review led to 26 additional regression cases; 66 benchmark tests, 181 full regression tests and Red code review passed.
- [2026-10-12] Final Graphify snapshot: 323 nodes / 790 edges / 11 communities; 20 exact document-to-code references.
- [2026-10-12] Final validation passed for 19 content pages, 14 Source snapshots, 36 graph inputs, 7 auxiliary hashes and 2 policy hashes.
- [2026-10-11] Local ERA5 inventory and knowledge setup prepared.

## Maintenance Debt
- reflect_debt: 0 after the bounded post-ingest reflection.
- migration_debt: 0; proposal_debt: 0; schema pin gap: 0.
- Convergence: 19/19 content pages use pinned v1 frontmatter (100%).
- Graph: 323 nodes / 790 edges / 11 communities; 20 exact document-to-code references.
- Verify current graph input hashes separately from historical Source commit/hash pairs; see the validation receipt.
