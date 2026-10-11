---
title: "ERA5-Aligned Staged Roadmap"
instance_of: Source
page_kind: source-page
date_ingested: "2026-10-12"
provenance:
  sources: ["docs/ERA5_ALIGNED_PLAN.md"]
  source_sha256: "72a877d5a9d144500c6c5b5b66e7fb859bb65f9ac81b640972e9eb4296b13b1e"
  source_commit: "009a363584aee7d7d053bbfeb284fc476e049039"
relations: []
---
# ERA5-Aligned Staged Roadmap

## Summary
The plan separates reuse of the existing six-hourly global cache from the eventual hourly D83 target, and orders work through inventory, a six-hour baseline, regional hourly connection, a global hourly pilot, and broader seasonal/year evaluation. It records the split and resource assumptions while stating that required hourly D83 inputs are not yet available and that no forecast model or new ERA5 payload was run as part of the plan revision.

## Claims
- The existing global cache is a 1979–2022, 44-year, 30-channel, six-hourly profile; the intended final D83+P1h profile needs 83 instantaneous state channels plus separate hourly precipitation. The document explicitly says the cache profile is not the current D83 hourly snapshot contract. ([`docs/ERA5_ALIGNED_PLAN.md`](../../docs/ERA5_ALIGNED_PLAN.md), “두 자료 프로파일을 분리한다”).
- The plan's development order is R0 inventory/contract, R1 six-hour baseline, R2 regional hourly connection, R3 global hourly pilot, then R4 seasonal/year expansion after the listed hourly, precipitation, phase, vertical-relation, and sensitivity checks. ([`docs/ERA5_ALIGNED_PLAN.md`](../../docs/ERA5_ALIGNED_PLAN.md), “기존 자료를 사용하는 단계별 작업”).
- The historical benchmark split assigns 1979–2017 to training/normalization, 2018 to structural/loss selection, 2019 to probability/threshold calibration, and 2020 to a final 00/12 UTC test; use of 2020 fSCM data for model or threshold selection requires revisiting its independence. ([`docs/ERA5_ALIGNED_PLAN.md`](../../docs/ERA5_ALIGNED_PLAN.md), “데이터 분할을 공개 벤치마크에 맞춰 다시 고정한다”).
- The plan retains the 2025 four-initializations-per-day target through 2026-01-10 18 UTC as an unmet data requirement and says not to combine it with the 2020 historical test as one sample. ([`docs/ERA5_ALIGNED_PLAN.md`](../../docs/ERA5_ALIGNED_PLAN.md), same section).
- The revision records no new ERA5 payload, model weights, external model inference, or 6h/1h forecast model execution; its local inventory measurements are recorded evidence, not a fresh payload reinspection. ([`docs/ERA5_ALIGNED_PLAN.md`](../../docs/ERA5_ALIGNED_PLAN.md), “근거와 확인 범위” and “이번 변경의 실행 범위”).

## Related
- [[entities/global-era5-cache]]
- [[entities/d83-schema]]
- [[entities/streamingcast]]
- [[procedures/project-knowledge-cycle]]
