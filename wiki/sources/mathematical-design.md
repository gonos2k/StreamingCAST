---
title: "Mathematical Design"
instance_of: Source
page_kind: source-page
date_ingested: "2026-10-11"
provenance:
  sources: ["docs/DESIGN.md"]
  source_sha256: "f0a88f1b3288285da06333d6abb68146e3b5a598d1c664ee208077740f734cb6"
relations: []
---
# Mathematical Design

## Summary
The design defines an explicit one-hour tensor API and a small four-variable column model with three learned parameters. Its conservation identities are imposed by the equations, and its differentiation, harmonic, and fitting checks are scoped to sampled toy-model paths rather than full-atmosphere dynamics or real weather skill.

## Claims
- The design separates time, files, retries, and LAYA decisions from the differentiable forecast calculation and defines ForecastStep input/output. (["docs/DESIGN.md"](../../docs/DESIGN.md)) Evidence/location: “`ForecastStep`은 `(state, parameters, hour, longitude, latitude, evaporation) -> (state_next, rain_1h)`다.” (DESIGN.md, “Scope”).
- The column model has only three learned parameters, with no transport, pressure-gradient, or vertical dynamics. (["docs/DESIGN.md"](../../docs/DESIGN.md)) Evidence/location: “학습 파라미터는 p0,a1,a2 3개다. 수송/압력경도/연직역학은 없다.” (DESIGN.md, “Toy equations: what is imposed, what is learned”).
- Adjoint consistency and Taylor/finite-difference checks establish sampled discrete-toy differentiation behavior, not full-atmosphere correctness. (["docs/DESIGN.md"](../../docs/DESIGN.md)) Evidence/location: “전체 대기의 수축성을 강제하지 않는다.” (DESIGN.md, “Numerical differentiation”); the section also says the dot-product test alone cannot rule out both directions differentiating the same incorrect model.
- Exact diurnal/semidiurnal response follows the imposed forcing and is not observational validation of atmospheric tides. (["docs/DESIGN.md"](../../docs/DESIGN.md)) Evidence/location: “실제 대기조석, Hough 구조, 관측 기압 위상의 검증이 아니다.” (DESIGN.md, “Diurnal / semidiurnal”).

## Related
- [[entities/streamingcast]]
