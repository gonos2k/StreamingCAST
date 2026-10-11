---
title: Local global ERA5 cache
instance_of: Artifact
page_kind: entity-page
epistemic_status: observed
date_created: 2026-10-11
date_modified: 2026-10-11
provenance:
  sources: [docs/ERA5_READINESS.md, evidence/era5/local_observation.json, evidence/era5/structural_check.json]
---
# Local global ERA5 cache

## Role
Read-only local training/research cache at `~/MyThos/data/era5_raw`.

## Key Facts
- 44 Zarr v2 stores cover 1979–2022, six-hourly, 64,284 timesteps.
- Global 0.25° grid: 721 × 1,440; 30 channels and five pressure levels.
- Inventory: 5,477,368,824,476 file bytes; structural inspection of 643,500 chunks
  found no missing, empty or unexpected paths.
- Only time coordinates and two first t2m frames were decoded. Full payload
  quality/hashes, actual availability and forecast skill were not verified.
- The cache cannot provide adjacent hourly D83 states. Missing inputs are listed
  in [ERA5 readiness](../../docs/ERA5_READINESS.md).

## Connections
- [[entities/d83-schema]], [[entities/streamingcast]]
- [[sources/era5-readiness]], [[sources/local-era5-observation]], [[sources/era5-structural-check]]
- Primary inventory: [observation JSON](../../evidence/era5/local_observation.json).
