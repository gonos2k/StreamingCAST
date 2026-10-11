---
title: StreamingCAST repository
instance_of: Artifact
page_kind: entity-page
epistemic_status: observed
date_created: 2026-10-11
date_modified: 2026-10-11
provenance:
  sources: [README.md, docs/PROJECT_STATUS.md, evidence/era5/structural_check.json]
  code_refs: [src/streamingcast/stream.py, src/streamingcast/physics.py]
---
# StreamingCAST repository

## Role
Repository for local streaming contracts and a differentiable forecast adapter.

## Key Facts
- P0 uses an independent four-variable, single-column manufactured model.
- The latest ERA5-preparation regression run reports 115 passed tests; this is
  engineering evidence, not actual weather skill.
- [PR #3](https://github.com/gonos2k/StreamingCAST/pull/3) is the draft ERA5
  preparation change; merge and deployment are not asserted.
- D83 forecasting, actual hourly global evaluation, LAYA, B200 and external NWP
  integration remain unexecuted/unapproved. Prior D83 long-rollout failure remains.

## Connections
- [[sources/repository-readme]], [[sources/project-status]], [[sources/era5-structural-check]]
- [[sources/mathematical-design]], [[sources/verification-history]], [[sources/local-data-boundary]],
  [[sources/era5-readiness]], [[sources/local-era5-observation]], [[sources/knowledge-workflow]]
- Data: [[entities/global-era5-cache]]; input contract: [[entities/d83-schema]].
- Work cycle: [[procedures/project-knowledge-cycle]].
- Primary evidence: [project status](../../docs/PROJECT_STATUS.md),
  [latest regression record](../../evidence/era5/structural_check.json).
