---
title: StreamingCAST Hot Cache
type: meta
date_modified: 2026-10-12
---
# Hot Cache

## Current Focus
Prepare source-backed project knowledge and close the hourly-global/D83 data gap.
Data preparation is [Draft PR #3](https://github.com/gonos2k/StreamingCAST/pull/3).
This knowledge setup is on `work/kg-project-management-20261011`, based on that
PR branch; neither branch is assumed merged.

## Work and Acceptance Checks
| Work | State | Acceptance / evidence |
| --- | --- | --- |
| Local ERA5 inventory and inspector | Prepared; PR #3 awaiting review | [Observation](../evidence/era5/local_observation.json), [structural check](../evidence/era5/structural_check.json): 44 stores, 643,500 chunks, 115 tests; limited engineering scope |
| kg + Graphify management | Configured; schema/link/hash checks passed | Pinned v1, 14 ontology pages, 256-node/632-edge graph; source hashes and wiki/link validation |
| Hourly global input requirements | Next bounded task; not implemented | Specify hourly source, missing eight pressure levels, omega/sp, rain endpoints, genuine availability/receipt and 2025 evaluation coverage |
| ERA5-to-D83 conversion adapter | Pending data requirements | Explicit units/channel order, pressure/wind/geometry verification, masks, geometry/stats hashes and independent samples |
| Real weather evaluation / D83 failure diagnosis | Not run; unresolved | Independent evaluation and long-rollout failure diagnosis; no toy PASS substitution |

## Next Bounded Action
Write the hourly-global data acquisition/conversion requirements using
[ERA5 readiness](../docs/ERA5_READINESS.md) and
[schema.py](../src/streamingcast/schema.py). Produce a channel/time coverage table
and acceptance checks before acquiring or transforming source arrays.

## Key Tensions / Open Questions
- Initial reflection found a code/document navigation gap despite fresh hashes; 12 explicit citations now bridge the two layers. Freshness alone does not establish graph coverage.
- Global data volume is sufficient for inventory but the existing six-hour/30-channel
  schema cannot provide hourly D83 states. [[entities/global-era5-cache]], [[entities/d83-schema]].
- Historical reanalysis timestamps do not prove what was available at a past
  issue time. Preserve acquisition provenance rather than inventing timestamps.
- Regional model levels are not the D83 pressure-channel contract.
- Historical test totals (53/107) and latest 115 tests have different snapshots;
  refer to each raw record's date/scope.

## Recent Activity
- [2026-10-12] Added 12 exact document-to-code citations; rebuilt graph to 256 nodes / 632 edges / 10 communities.
- [2026-10-12] Schema, wiki links and source-hash checks passed; reflection below records the resolved navigation gap.
- [2026-10-11] Local ERA5 inventory and Draft PR #3 prepared.
- [2026-10-11] kg-init pinned the existing v1 schema; source summaries preserve raw hashes.
- [2026-10-11] Graphify built code AST plus document relationships; raw arrays and generated artifacts excluded.

## Maintenance Debt
- reflect_debt: 0 after the initial bounded reflection.
- migration_debt: 0; proposal_debt: 0; schema pin gap: 0.
- Convergence: 14/14 content pages use full v1 frontmatter (100%).
- Graph freshness: check [source manifest](../graphify-out/source_manifest.json); recent mtime alone is insufficient.
