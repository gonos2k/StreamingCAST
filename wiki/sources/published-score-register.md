---
title: "Published Benchmark Score Register"
instance_of: Source
page_kind: source-page
date_ingested: "2026-10-12"
provenance:
  sources: ["benchmarks/reference_scores.json"]
  source_sha256: "a966299f955bf2427c0d093bdd733485c221a869fadcc77dcf082bfc9c4ad739"
  source_commit: "009a363584aee7d7d053bbfeb284fc476e049039"
relations: []
---
# Published Benchmark Score Register

## Summary
The JSON register holds historical published references with their source, period, units, scope, and limitations. Its 60 RMSE and 3 ROCSS entries come from primary-paper reports; public result-file locations were identified but not fully retrieved and decoded, and no StreamingCAST forecast skill was measured.

## Claims
- The register contains 63 scored records: 60 RMSE and 3 ROCSS from two publication sources. These are historical references, not scores computed from StreamingCAST forecasts. ([`benchmarks/reference_scores.json`](../../benchmarks/reference_scores.json), `records`, `sources`, and `purpose`).
- The ArchesWeatherGen RMSE reference is for 2020, 00/12 UTC initializations, global 1.5° evaluation and 24-hour lead, with published rounding retained; checkpoint digests, exact sample hashes, and mask/aggregation lineage were not independently verified in the register. ([`benchmarks/reference_scores.json`](../../benchmarks/reference_scores.json), `sources.arches_table1_2020`).
- The precipitation reference is a 2020, five-day lead ROCSS for 24-hour precipitation events, with an event threshold fit on 2020 targets; the register cautions that this is a historical retrospective protocol and not directly equivalent to a prospective threshold protocol. ([`benchmarks/reference_scores.json`](../../benchmarks/reference_scores.json), `sources.hydro_wet90_2020`).
- WeatherBench result storage and two GenCast metric-file locations are recorded as locators, but direct retrieval failed and the GenCast responses were not fully decoded or validated; no GenCast numeric score is registered. ([`benchmarks/reference_scores.json`](../../benchmarks/reference_scores.json), `raw_score_locators` and `acquisition_limits`).
- The catalog states that no row is an operational approval threshold and requires a matching local reevaluation and uncertainty estimate; it also records `raw_forecasts_recomputed: false` for both paper sources. ([`benchmarks/reference_scores.json`](../../benchmarks/reference_scores.json), `comparability` and `sources`).

## Related
- [[entities/global-era5-cache]]
- [[entities/d83-schema]]
- [[entities/streamingcast]]
- [[procedures/project-knowledge-cycle]]
