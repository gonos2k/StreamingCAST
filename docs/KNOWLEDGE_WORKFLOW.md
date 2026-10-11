# Project knowledge workflow

StreamingCAST uses the **kg** skills for a persistent ontology wiki and the
**Graphify** skill for code/document relationships. This workflow was requested
by the project owner on 2026-10-11 and is recorded in `AGENTS.md`.

## Authority and scope

Original code, documentation and evidence remain authoritative. `wiki/` and
`graphify-out/` are derived views. Verify an important claim through
**graph → wiki → original source**, including the original validation scope.
Graph confidence describes relationship extraction, not scientific truth.

The project pins the existing kg v1 schema in `wiki/.schema/`; it does not add a
Task class or change the ontology. Current tasks and blockers live in the hot
cache and overview, linked to decisions, procedures and sources. Existing schema
approval rules govern future schema changes and heuristic promotion.

Graph inputs are repository code (`src/`, `scripts/`, `tests/`) and project
documents (`README.md`, `AGENTS.md`, `docs/`). Exclude `wiki/`, `graphify-out/`,
raw data, credentials and runtime outputs. Do not ingest ERA5 array payloads.
Small committed evidence JSON may be cited by wiki pages, but is not a weather
validation result beyond its stated scope.

## Session cycle

1. Run `/kg-orient`; read `wiki/hot.md`, then `wiki/overview.md` and the graph
   report. Check source hashes and extraction dates before relying on a graph.
2. Select one bounded task and confirm its source-backed acceptance checks.
3. Do complex work in the primary agent; use GPT-6-luna/high sub-agents for
   simple or repetitive work. Use Green and Red teams at useful checkpoints.
4. Validate the change and preserve failures, outstanding limitations and actual
   results. An inventory PASS must never become a forecast-skill PASS.
5. Use `/kg-ingest <source>` for new documentation or evidence. Preserve old
   contradictory claims with source references rather than silently replacing
   them. Source summary pages retain their original source hash/date.
6. Use `/kg-update` for code updates. The CLI is code-only; use
   `/graphify . --update` for document semantic refresh. Apply the input excludes
   above on every run and record any unrefreshed layer in the audit log.
7. Run `/kg-lint`; update navigation, `wiki/hot.md` and the append-only log.
   Consider `/kg-reflect` after three ingests or a substantive checkpoint.

## Query and impact review

```bash
graphify query "Snapshot D83 hourly ERA5" --budget 1500
graphify explain "Snapshot"
```

Use returned source locations to inspect the original code or document.
Community assignments and inferred bridges are navigation aids and can change
after a rebuild. The graph may not resolve every dynamic Python call.

## Durable outputs

- `wiki/index.md`: ontology page catalog and graph snapshot.
- `wiki/hot.md`: active task, blockers, next action and maintenance debt.
- `wiki/overview.md`: project synthesis under 500 words.
- `wiki/sources/`: one immutable summary per ingested raw source snapshot.
- `wiki/entities/`, `wiki/decisions/`, `wiki/procedures/`: artifact facts, explicit
  judgments and reproducible steps with provenance.
- `wiki/log.md`: append-only knowledge-operation audit trail.
- `graphify-out/graph.json`, `GRAPH_REPORT.md`, `graph.html`: graph and exploration.
- `graphify-out/source_manifest.json`: source hashes and extraction scope;
  check these rather than interpreting a recent file mtime as proof of freshness.

Generated caches, host-specific interpreter/root memos and temporary extraction
files are local-only. Retain the portable graph/report/manifest and ontology wiki
for review; never overwrite a kg wiki with Graphify's separate wiki export.

## Current work

[PR #3](https://github.com/gonos2k/StreamingCAST/pull/3) prepares the ERA5
inventory and structural inspector. The global 1979–2022 cache is six-hourly and
30-channel. The next bounded data task is to specify an actual hourly global
source and close the pressure-level, omega, surface-pressure and hourly-rain
gaps before implementing a D83 adapter. See [ERA5 readiness](ERA5_READINESS.md)
and [project status](PROJECT_STATUS.md). No real-weather forecast approval is
implied by initializing the knowledge system.
