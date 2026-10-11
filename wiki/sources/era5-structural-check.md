---
title: "ERA5 Structural Check"
instance_of: Source
page_kind: source-page
date_ingested: "2026-10-11"
provenance:
  sources: ["evidence/era5/structural_check.json"]
  source_sha256: "6eb49825fa60798b9d9080b445845708873bd16545ed836d7ce78a9e3a1e6d50"
relations: []
---
# ERA5 Structural Check

## Summary
The structural-check record reports that a local metadata and chunk inventory passed for 44 stores, 616 arrays, and 643,500 expected chunks, with no missing, empty, unexpected chunks, or reported errors. It also records eight focused regression tests and a later full regression count of 115. The record scopes the check to metadata/chunk structure and explicitly excludes payload integrity and D83 verification.

## Claims
- The structural inventory reports 44 stores, 616 arrays, and 643,500 present chunks with no missing, empty, unexpected chunks, or errors. (["evidence/era5/structural_check.json"](../../evidence/era5/structural_check.json)) Evidence/location: JSON pointers `/ok`, `/stores`, `/arrays`, `/chunks_present`, `/chunks_missing`, `/chunks_empty`, `/chunks_unexpected`, `/errors`.
- The check’s declared scope is Zarr metadata and optional chunk inventory only. (["evidence/era5/structural_check.json"](../../evidence/era5/structural_check.json)) Evidence/location: JSON pointer `/scope`: “Zarr metadata and optional chunk inventory only; payload integrity and D83 are not verified.”
- The record lists eight focused tests and 115 passing tests in the full regression run. (["evidence/era5/structural_check.json"](../../evidence/era5/structural_check.json)) Evidence/location: JSON pointers `/focused_tests/passed` and `/full_regression/passed`; the latter is later than and distinct from the README’s historical 107-test note and the P0 verification record’s 53-test run.

## Related
- [[entities/global-era5-cache]]
- [[entities/d83-schema]]
