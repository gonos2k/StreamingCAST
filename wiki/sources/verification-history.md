---
title: "Verification History"
instance_of: Source
page_kind: source-page
date_ingested: "2026-10-11"
provenance:
  sources: ["docs/VERIFICATION.md"]
  source_sha256: "523d69decfe635792b45579c24b30bc89404458b08c3da1a60a756822ff14e8d"
relations: []
---
# Verification History

## Summary
This P0 evidence record reports a 53-test run and numerical checks on a CPU/FP64 toy path, including sampled differentiation checks and a manufactured 240-hour rollout. It explicitly says these results are not real-weather skill, continuous primitive-equation adjoint validation, or a B200/D83 runtime estimate. Its 53-test record is a distinct snapshot from the README’s historical 107 and the later ERA5 structural record’s 115 full-regression tests.

## Claims
- The P0 execution record reports 53 passing tests on Python 3.13.5 with CPU/FP64 reference calculations. (["docs/VERIFICATION.md"](../../docs/VERIFICATION.md)) Evidence/location: “python -m pytest -q: 53 passed.” (VERIFICATION.md, “Actual runs”).
- The fitted model uses a known three-parameter manufactured equation; its low error is not real weather skill. (["docs/VERIFICATION.md"](../../docs/VERIFICATION.md)) Evidence/location: “This is a simple known-equation inverse problem, NOT real weather skill.” (VERIFICATION.md, “Results”).
- Differentiability results cover sampled discrete-toy paths and do not certify continuous primitive-equation adjoints. (["docs/VERIFICATION.md"](../../docs/VERIFICATION.md)) Evidence/location: “Differentiability tests certify sampled code paths of the discrete toy, not continuous primitive-equation adjoints.” (VERIFICATION.md, “Interpretation”).
- This record’s 53 tests are separate from the README’s historical 107 and the later structural-check record’s 115 full-regression tests. (["docs/VERIFICATION.md"](../../docs/VERIFICATION.md)) Evidence/location: Count locations: “Actual runs”; README.md “PR #2 검토 반영 및 P0.1 확장”; structural_check.json `/full_regression/passed`.

## Related
- [[entities/streamingcast]]
