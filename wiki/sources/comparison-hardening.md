---
title: Benchmark comparison hardening source
instance_of: Source
page_kind: source-page
date_ingested: 2026-10-12
provenance:
  sources: [docs/BENCHMARK_REVIEW_FIX.md]
  source_sha256: c0462074a0f5915f1af4b625d157ffa6fc5725daf05a7e9362ea0232f40f7154
---
# Benchmark comparison hardening source

## Summary
The post-merge review identified product-identity omissions and numerical edge
cases despite passing earlier tests. The follow-up separates metadata compatibility
from local weather approval and carries the KG branch into a main-based review.

## Claims
- Product matching explicitly includes pressure level, quantile probability and
  accumulation endpoints, with typed values and a preprocessing digest.
- Area-weight hashes must match while model/checkpoint hashes may differ; the
  former ambiguous field requires migration.
- Zero case errors remain in the population. Undefined zero-baseline relative
  comparisons return reasoned INSUFFICIENT results; no epsilon or sample removal.
- Common scaling protects area and bootstrap arithmetic; failures raise explicit
  errors rather than producing NaN or infinity.
- Published source axes are validated, and ROCSS preprocessing/aggregation and
  unresolved reproduction policy are recorded without turning references into
  local forecast approval.

All claims cite [the fix specification](../../docs/BENCHMARK_REVIEW_FIX.md),
sections Product identity, Zero errors and Published definitions.

## Related
[[sources/comparison-acceptance]], [[sources/published-score-register]],
[[sources/execution-scope]], [[entities/streamingcast]],
[[procedures/project-knowledge-cycle]].
