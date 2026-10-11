---
title: Project knowledge cycle
instance_of: Procedure
page_kind: procedure-page
epistemic_status: observed
date_created: 2026-10-11
date_modified: 2026-10-11
provenance:
  sources: [AGENTS.md, docs/KNOWLEDGE_WORKFLOW.md]
---
# Project knowledge cycle

## Purpose
Recover project context, execute a bounded task, and leave source-backed knowledge
for the next session.

## Preconditions
- Read `AGENTS.md`; kg and Graphify skills are available.
- The wiki is pinned to schema v1; authoritative source files are readable.

## Steps
1. `/kg-orient`: read [hot](../hot.md), then [overview](../overview.md), then [graph-report](../graph-report.md).
2. Check `graphify-out/source_manifest.json` source hashes and extraction scope.
3. Pick the next bounded action from [hot](../hot.md) and its source acceptance checks.
4. Work and validate; use GPT-6-luna/high for simple/repetitive subtasks and
   Green/Red review when useful. Preserve unresolved failures.
5. `/kg-ingest <source>`: derive pages without changing raw source material;
   preserve immutable Source snapshots and provenance.
6. `/kg-update` for changed code; `/graphify . --update` for document semantics.
   Exclude raw data, credentials, runtime outputs and derived wiki/graph files.
7. `/kg-lint`: validate schema, links, source freshness and graph/report counts.
8. Update [hot](../hot.md), [overview](../overview.md), indexes and the append-only [log](../log.md). After three
   ingests or a major checkpoint, use `/kg-reflect`.

## Postconditions / Verification
- Claims link to raw sources, not only wiki summaries or inferred graph edges.
- Changed sources have matching hashes, or stale layers are explicitly recorded.
- Wiki schema and link checks pass; validation scope remains unchanged.
- No schema change, reclassification, page deletion or heuristic promotion is
  inferred from routine maintenance.

## Connections
[[sources/knowledge-workflow]], [[decisions/2026-10-11-knowledge-management]],
[[entities/streamingcast]]. Primary workflow:
[KNOWLEDGE_WORKFLOW.md](../../docs/KNOWLEDGE_WORKFLOW.md).
