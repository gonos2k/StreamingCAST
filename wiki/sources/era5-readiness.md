---
title: "ERA5 Readiness"
instance_of: Source
page_kind: source-page
date_ingested: "2026-10-11"
provenance:
  sources: ["docs/ERA5_READINESS.md"]
  source_sha256: "93fdc349e4e3decfd2b028b5662a5cfc7b7c8017051d35d791209bbea0fa2fc4"
relations: []
---
# ERA5 Readiness

## Summary
The readiness report inventories local global and regional ERA5 holdings and compares them with the hourly D83 input contract. The global cache is observed on disk for 1979–2022, superseding a historical note that stopped at 1992, but it is six-hourly with five pressure levels and does not satisfy the hourly D83 requirements. Inventory and selected sample checks do not establish full payload integrity, preprocessing correctness, or forecast skill.

## Claims
- The local global cache covers 1979–2022; a historical MyThos note stopping at 1992 is superseded by this inventory. (["docs/ERA5_READINESS.md"](../../docs/ERA5_READINESS.md)) Evidence/location: “A historical MyThos note stopping coverage at 1992 is superseded by the on-disk 1979–2022 inventory.” (ERA5_READINESS.md, “Available data”).
- The global store has 44 annual Zarr stores, 6-hourly data, 30 channels, and five pressure levels. (["docs/ERA5_READINESS.md"](../../docs/ERA5_READINESS.md)) Evidence/location: “Global 0.25° grid, 6-hourly, 30 channels”; “Pressure levels are 1000, 850, 700, 500, 250 hPa.” (ERA5_READINESS.md, “Available data” and “Global cache: what was checked”).
- The available cache cannot supply adjacent hourly D83 states and lacks several pressure levels and surface pressure. (["docs/ERA5_READINESS.md"](../../docs/ERA5_READINESS.md)) Evidence/location: The gap table states “Six-hour samples” for adjacent states and lists seven missing pressure levels plus missing `sp` (ERA5_READINESS.md, “Gap to StreamingCAST”).
- The inspection did not full-scan payload quality or hash the 5.48 TB cache. (["docs/ERA5_READINESS.md"](../../docs/ERA5_READINESS.md)) Evidence/location: “No full-array quality scan or content hashing of the 5.48 TB cache was performed.” (ERA5_READINESS.md, “Global cache: what was checked”).

## Related
- [[entities/global-era5-cache]]
- [[entities/d83-schema]]
