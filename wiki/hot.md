---
title: StreamingCAST Hot Cache
type: meta
date_modified: 2026-10-12
---
# Hot Cache

## Current Focus
Validate the already-open PR #6 rather than duplicate its changes. This follow-up
starts at `a43342d4e20548702dba408ed71b5728d9ba8cea` and changes only the local
benchmark evaluator, focused tests and their documentation. Work branch:
`work/benchmark-followup-20261012`. Main and PR #6 are not modified or merged.

PR #6 carries the benchmark fixes and the knowledge files from PR #5 toward main.
The latest main observed at this session's start is `b34cd3fd49a4eead90b977327672158087b0799e`.
These are dated observations, not a promise about a future merge state.

## Work and Acceptance Checks
| Work | State | Evidence / limits |
| --- | --- | --- |
| PR #6 inherited product identity, zero-MSE, finite arithmetic | Existing implementation rechecked | Original 181 pytest cases pass; 18 existing warnings and 2 subtests |
| Additional local-definition and numeric coercion checks | Implemented on this follow-up branch | [Details](../docs/BENCHMARK_FOLLOWUP.md), [receipt](../evidence/benchmarks/followup.json) |
| New failure-injection regressions | 28 cases | Against PR #6: 21 fail and 7 pass; after correction all 28 pass |
| All runtime regression tests | 209 pass | All src/scripts/tests, benchmark JSON and Python configuration matched; not whole-wiki/graph validation |
| External reference scores | 63 values unchanged | 60 RMSE and 3 ROCSS; not StreamingCAST weather scores |
| Knowledge/Graphify refresh for this follow-up | PENDING | Prior graph snapshot describes the PR #6 inputs, not the newly changed source |
| R0 local data contracts | Next after review | P6h endpoints/units, sp/static fields, subsurface mask and prior train/test use |
| R1 six-hour persistence/climatology | NOT_RUN | Requires accepted R0 inputs and frozen cases |
| R2 hourly connections / R3 global hourly / R4 expansion | NOT_RUN | Genuine hourly data and independent scientific gates still required |

## What Changed
Matching metadata is insufficient if both descriptions are wrong. Local variable,
unit, vertical-coordinate and temporal definitions now have an explicit registry.
The RMSE gate checks its actual aggregation. Complex/object/bool/string arrays are
not silently cast into real measurements; arithmetic loss of a nonzero squared
contribution is rejected instead of being reported as an exact zero.

Exact dry/perfect-forecast zero MSE remains valid. The evaluator performs no unit
conversion. A zero aggregate baseline still yields a reasoned INSUFFICIENT result.
Published score values and missing records are unchanged. Details and reproducible
commands remain in the primary [follow-up document](../docs/BENCHMARK_FOLLOWUP.md).

## Next Bounded Action
Review the follow-up together with PR #6. Refresh Graphify input hashes and
changed document semantics before claiming the graph is current; do not overwrite
historical immutable Source pages or reinterpret old lint receipts as new tests.
Then produce a local R0 acceptance record for the six-hour cache. If sp remains
unavailable, limit initial evaluation to the documented four surface variables.
No raw data is uploaded and no local availability timestamp is invented.

## Preserved Scientific Boundaries
- Six-hour/30-channel ERA5 is not adjacent-hourly D83. Regional 83 model levels are
  not D83 channels. Inventory/hash checks do not prove payload or physical quality.
- The earlier D83 240h performance failure remains unresolved.
- 2020 regional tuning/pretraining may compromise the proposed 2020 holdout.
- Six-hour sampling cannot alone identify a local semidiurnal sine component.
- ROCSS single-class-cell policy and exact scoring/forecast lineage remain unresolved.
- Real-weather forecasting, actual LAYA weights, external differentiable NWP and
  B200 execution are not validated by these engineering tests.

## Maintenance Debt
- graph_refresh_debt: 1. Graphify extraction was not run in this session.
- reflect_debt: 1. No kg-reflect or full pinned-schema lint was executed here.
- Existing 19 content pages / 14 immutable Source snapshots and prior
  graphify-out/validation.json remain historical PR #6 records.
- Prior graph: 323 nodes / 790 edges / 11 communities, 20 explicit bridges. Those
  counts are not a verification of current changed-code freshness.
