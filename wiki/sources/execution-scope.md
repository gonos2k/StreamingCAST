---
title: "Benchmark Revision Execution Scope"
instance_of: Source
page_kind: source-page
date_ingested: "2026-10-12"
provenance:
  sources: ["evidence/benchmarks/execution.json"]
  source_sha256: "9417bd192d707e804c35b7d1c6fb0f210da86a087bd9f27bf5a6664450713170"
  source_commit: "009a363584aee7d7d053bbfeb284fc476e049039"
relations: []
---
# Benchmark Revision Execution Scope

## Summary
This evidence record scopes the benchmark-contract checks reported for the 2026-10-11 revision. It distinguishes 40 synthetic contract tests from a 147-test historical composition, explicitly records that eight inventory-inspector tests were not reexecuted in that composition, and records no real-array or forecast-model run and no forecast-skill approval.

## Claims
- The benchmark-contract command reported 40 passing tests for synthetic metric/contracts, table validation, storage/calendar, and sampling checks. ([`evidence/benchmarks/execution.json`](../../evidence/benchmarks/execution.json), `new_tests`).
- A separate recorded regression run reported 147 passes, composed of 107 tests from verified implementation snapshot `9200b321` plus 40 new tests; the record says this was not a complete checkout of current main inventory additions. ([`evidence/benchmarks/execution.json`](../../evidence/benchmarks/execution.json), `local_regression`).
- The eight main-inventory structural-inspector tests were not reexecuted in that 147-test composition. This is the scope stated by the evidence record, not a claim about a later full-suite run. ([`evidence/benchmarks/execution.json`](../../evidence/benchmarks/execution.json), `local_regression.main_inventory_eight_tests_reexecuted_here`).
- The execution record says real weather arrays were not read, forecasts were not recomputed, hourly D83 inputs were unavailable, and `weather_skill_approved` was false. ([`evidence/benchmarks/execution.json`](../../evidence/benchmarks/execution.json), top-level fields and `benchmarks`).
- The record counts the published references as 60 RMSE and 3 ROCSS from two primary publications and says raw forecasts and raw metric files were not decoded. ([`evidence/benchmarks/execution.json`](../../evidence/benchmarks/execution.json), `benchmarks`).

## Related
- [[entities/global-era5-cache]]
- [[entities/d83-schema]]
- [[entities/streamingcast]]
- [[procedures/project-knowledge-cycle]]
