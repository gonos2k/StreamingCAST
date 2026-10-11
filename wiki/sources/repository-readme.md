---
title: "Repository README"
instance_of: Source
page_kind: source-page
date_ingested: "2026-10-11"
provenance:
  sources: ["README.md"]
  source_sha256: "5123a3058a309619274fdcec3481daec0ac60d6239d263cc9ed4ebba76f6bb7b"
relations: []
---
# Repository README

## Summary
The README describes StreamingCAST as a P0 research repository for connecting a differentiable numerical forecast interface to real one-hour forecasting. Its implemented path is a four-variable manufactured column toy plus local data contracts; it explicitly leaves real ERA5 validation, LAYA inference, B200 training, and external NWP integration unrun.

## Claims
- The current model is a four-variable independent-column manufactured problem, not D83 or an operational weather model. (["README.md"](../../README.md)) Evidence/location: “현재 실행모델은 4변수 독립 단층 제조문제다. D83 예보모델, 구면 신경망, 실제 대기조석 또는 운영 강수모델이 아니다.” (README.md, “현재 구현”).
- Real ERA5/observation validation, LAYA weight inference, B200 training, and external NWP integration are not yet executed. (["README.md"](../../README.md)) Evidence/location: “실제 ERA5/관측 검증, LAYA 가중치 추론, B200 학습과 외부 NWP 통합은 아직 미실행이다.” (README.md, “현재 구현”).
- The README records 107 regression tests as part of the historical PR #2 expansion account. (["README.md"](../../README.md)) Evidence/location: “107개 회귀시험” (README.md, “PR #2 검토 반영 및 P0.1 확장”); this is a historical count, distinct from later evidence records.

## Related
- [[entities/streamingcast]]
- [[entities/d83-schema]]
