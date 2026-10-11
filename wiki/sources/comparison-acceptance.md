---
title: "Benchmark Comparison Acceptance Protocol"
instance_of: Source
page_kind: source-page
date_ingested: "2026-10-12"
provenance:
  sources: ["docs/BENCHMARK_PROTOCOL.md"]
  source_sha256: "c3aad6c830613a67802173bc860580504ed8970728d9e0a6f1c40d3c909f974c"
  source_commit: "009a363584aee7d7d053bbfeb284fc476e049039"
relations: []
---
# Benchmark Comparison Acceptance Protocol

## Summary
The protocol defines how historical external results may inform comparison and what evidence a local evaluation must align before supporting a performance claim. It separates historical paper scores from common local reevaluation, prescribes matched samples and scoring conditions, and keeps forecast approval dependent on additional scientific gates.

## Claims
- The protocol transcribes 60 RMSE values and 3 ROCSS values from two primary publications; it reports no newly computed StreamingCAST score and does not treat publication values as local skill. ([`docs/BENCHMARK_PROTOCOL.md`](../../docs/BENCHMARK_PROTOCOL.md), “확보 상태를 세 단계로 분리한다”).
- The cited atmospheric RMSE table uses 2020 00/12 UTC initializations, global evaluation at 1.5°, and 24-hour lead; the separate precipitation ROCSS reference uses 2020, global 1.5°, 00/12 UTC, five-day lead, and 24-hour accumulated precipitation. ([`docs/BENCHMARK_PROTOCOL.md`](../../docs/BENCHMARK_PROTOCOL.md), “확보한 24시간 수치의 대표값” and “강수 벤치마크는 평균 대기장과 별도다”).
- A valid common comparison must record and align protocol ID, initialization sample hash, verification data hash, initial analysis, grid/area/mask, variables/units/levels, lead, interval statistic, output statistic, member count, and climatology/aggregation; different initial conditions make a system-level comparison rather than an architecture-only claim. ([`docs/BENCHMARK_PROTOCOL.md`](../../docs/BENCHMARK_PROTOCOL.md), “승인 가능한 공통 평가 계약”).
- The protocol's staged goals begin with persistence and train-only climatology, then six-hour comparisons, then genuine one-hour comparisons and probabilistic/cost metrics; an initial 2% non-inferiority margin is explicitly a proposal and paired confidence checks do not replace separate precipitation, cycle, physics, or numerical gates. ([`docs/BENCHMARK_PROTOCOL.md`](../../docs/BENCHMARK_PROTOCOL.md), “수학적 지표와 단계별 목표”).
- Neither metadata/schema checks nor external scores establish training history or approve forecast skill; the document says actual ERA5 arrays and external forecast models were not run for these checks. ([`docs/BENCHMARK_PROTOCOL.md`](../../docs/BENCHMARK_PROTOCOL.md), “승인 가능한 공통 평가 계약” and “재현과 현재 한계”).

## Related
- [[entities/global-era5-cache]]
- [[entities/d83-schema]]
- [[entities/streamingcast]]
- [[procedures/project-knowledge-cycle]]
