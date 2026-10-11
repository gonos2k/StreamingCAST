---
title: "Local ERA5 Observation"
instance_of: Source
page_kind: source-page
date_ingested: "2026-10-11"
provenance:
  sources: ["evidence/era5/local_observation.json"]
  source_sha256: "26218676812d529207745b1c59a25809fbd893f86c093a59f590273d21468718"
relations: []
---
# Local ERA5 Observation

## Summary
This machine-local observation record summarizes inventory counts, decoded six-hour time coordinates, metadata hashes, and two sampled 2 m temperature frames. It records 44 global stores spanning 1979–2022 and notes that full-array values, raw payload hashes, rainfall endpoints, streaming availability, D83 conversion, and forecast skill were not verified.

## Claims
- The observed global cache has 44 stores, 64,284 six-hour timesteps, and spans 1979-01-01 00 UTC to 2022-12-31 18 UTC. (["evidence/era5/local_observation.json"](../../evidence/era5/local_observation.json)) Evidence/location: JSON pointers `/global/stores`, `/global/timesteps`, `/global/time_start_utc`, `/global/time_end_utc`.
- Every annual decoded time coordinate matched its complete six-hour calendar, while only the first 2 m temperature frame in 1979 and 2022 was sampled for finite-value checks. (["evidence/era5/local_observation.json"](../../evidence/era5/local_observation.json)) Evidence/location: JSON pointers `/global/time_coordinate_check` and `/global/sample_t2m_first_frames`.
- The record explicitly leaves full-array values, raw payload hashes, rainfall endpoints, availability, D83 conversion, and forecast skill unchecked. (["evidence/era5/local_observation.json"](../../evidence/era5/local_observation.json)) Evidence/location: JSON pointer `/not_verified`.

## Related
- [[entities/global-era5-cache]]
- [[entities/d83-schema]]
