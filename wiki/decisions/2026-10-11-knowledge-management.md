---
title: Use kg and Graphify for project knowledge
instance_of: Decision
page_kind: decision-page
date: 2026-10-11
date_created: 2026-10-11
date_modified: 2026-10-11
provenance:
  sources: [AGENTS.md, docs/KNOWLEDGE_WORKFLOW.md]
---
# Use kg and Graphify for project knowledge

## Context
The project owner requested kg and Graphify for ongoing project management after
preparing the local ERA5 inventory PR.

## Decision
Use the existing kg v1 ontology wiki for persistent context and Graphify for
structural/document relationships, with the original repository sources as authority.

## Rationale
Context, source provenance, blockers and acceptance checks must survive across
sessions. A graph supplies navigation; the wiki explains the current work and
its scientific limits. This follows the owner's explicit instruction.

## Alternatives Considered
No alternative tool selection was evaluated in this setup. Existing code and
primary evidence are retained; this adds derived views without replacing them.
Graphify's standalone wiki export is not used as the ontology wiki.

## Consequences
- Read [hot](../hot.md) and [overview](../overview.md) at session start; follow
  [[procedures/project-knowledge-cycle]].
- Maintain source hashes and schema/link checks alongside graph refreshes.
- Keep data payloads and credentials outside the derived knowledge system.
- Do not infer production approval from inventory, toy tests or graph structure.
- Preserve [[sources/knowledge-workflow]] as a snapshot of the raw instructions.
