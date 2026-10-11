---
title: Project knowledge workflow source
instance_of: Source
page_kind: source-page
date_ingested: 2026-10-11
date_created: 2026-10-11
date_modified: 2026-10-11
source_sha256: 0637f0ca7dbc299381053392e6e798d08485e6ab858dc798f5ae6175cf62a204
provenance:
  sources: [docs/KNOWLEDGE_WORKFLOW.md]
---
# Project knowledge workflow source

## Summary
The owner requested kg and Graphify. The workflow assigns authority to original
sources, pins the existing v1 schema, uses hot/overview for task context, and keeps
raw data and derived artifacts out of graph extraction.

## Claims
- A current graph is a navigation view; relationship confidence is not weather
  validation. Verify through graph → wiki → original source.
- Source summaries retain their original source hash/date; routine knowledge
  bookkeeping does not approve ontology changes or scientific claims.
- Code-only updates and document semantic refresh are separate operations.

## Related
[[procedures/project-knowledge-cycle]], [[decisions/2026-10-11-knowledge-management]].
Original source: [KNOWLEDGE_WORKFLOW.md](../../docs/KNOWLEDGE_WORKFLOW.md).
