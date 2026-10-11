---
title: D83 input schema
instance_of: Artifact
page_kind: entity-page
epistemic_status: observed
date_created: 2026-10-11
date_modified: 2026-10-11
provenance:
  sources: [docs/LOCAL_DATA.md, docs/ERA5_READINESS.md]
  code_refs: [src/streamingcast/schema.py, src/streamingcast/stream.py]
---
# D83 input schema

## Role
Canonical `d83-v1` channel/unit contract defined in `schema.py`.

## Key Facts
- T / Phi / u / v / omega / q at 13 pressure levels plus t2m / msl / u10 / v10 / sp
  form 83 channels. 83 model levels are a different quantity.
- Snapshot selection requires initialization−1h and initialization with genuine
  issue-time availability and receipt metadata.
- Global cached levels are 1000, 850, 700, 500, 250 hPa; missing levels are
  50, 100, 150, 200, 300, 400, 600, 925 hPa. Omega and sp are also absent.
- Six-hour precipitation in m cannot be relabeled as observed hourly mm totals.
- Channel validation does not prove remapping, wind basis, masks or weather skill.

## Connections
- [[entities/global-era5-cache]], [[sources/local-data-boundary]], [[sources/era5-readiness]]
- Primary code: [schema](../../src/streamingcast/schema.py),
  [snapshot selection](../../src/streamingcast/stream.py).
