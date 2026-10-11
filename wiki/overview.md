---
title: StreamingCAST project overview
type: meta
date_modified: 2026-10-12
---
# StreamingCAST project overview

StreamingCAST currently implements local streaming input contracts, a SQLite
ledger, frozen issue-time snapshots and a differentiable four-variable
manufactured column model. It does not yet implement an actual global D83 weather
forecast. The prior D83 240-hour synthetic forecast failure remains unresolved.
See [[entities/streamingcast]], [[sources/project-status]] and the original
[project status](../docs/PROJECT_STATUS.md).

The local global ERA5 cache contains 44 complete annual stores for 1979–2022:
5.48 TB, 0.25°, six-hourly, 30 channels. All decoded time coordinates match the
calendar; chunk structure is complete. Only two t2m frames were sampled, so full
payload integrity and weather skill remain unverified. The regional ROAD-yh
archive has 58 missing dates and an index-reported missing GRIB; the small fSCM
hourly/monthly cache is regional/model-level data. See
[[entities/global-era5-cache]] and [ERA5 readiness](../docs/ERA5_READINESS.md).

The current D83 input requires adjacent hourly states, six variables on 13
pressure levels and five surface variables. The global cache lacks hourly
sampling, eight pressure levels, omega and sp; six-hour precipitation cannot be
relabeled observed hourly rain. An independent 2025 evaluation also needs data
through 2026-01-10 18 UTC. See [[entities/d83-schema]] and
[[sources/local-data-boundary]].

[Draft PR #3](https://github.com/gonos2k/StreamingCAST/pull/3) prepares the data
inventory and structural inspector. Its latest engineering evidence records
115 regression tests passed, including eight new structural-inspector tests;
older records of 53 and 107 tests are historical scopes, not contradictory
current counts. This does not approve real ERA5 forecast performance.

The next bounded work is to define an actual hourly global input source and its
required variables, levels, accumulation convention, availability and evaluation
window before conversion or forecasting. Track acceptance checks in [[hot]].

Knowledge management uses the existing pinned kg v1 schema and Graphify's
code/document graph. Follow [[procedures/project-knowledge-cycle]] and verify
claims through graph → wiki → original source. Relationships and communities
are navigation aids, not independent physical evidence. No ontology changes,
heuristic promotions, downloads, GPU jobs or merges occurred in this setup.
