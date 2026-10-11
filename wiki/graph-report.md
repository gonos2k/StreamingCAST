# Graph Report - StreamingCAST  (2026-10-12)

## Corpus Check
- Corpus is ~11,539 words - fits in a single context window. You may not need a graph.

## Summary
- 256 nodes · 632 edges · 10 communities (8 shown, 2 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 78 edges (avg confidence: 0.9)
- Token usage: unavailable from host-session sub-agent tools; zero placeholders are not measured usage. No external semantic LLM API was invoked.

## Community Hubs (Navigation)
- Manufactured numerical verification
- Local inputs and schemas
- Forecast science and ERA5 readiness
- Hourly time and rainfall contracts
- SI and observation coupling tests
- ERA5 structural inspection
- Content addressed artifacts
- Knowledge management cycle
- Package scope
- Agent guidelines

## God Nodes (most connected - your core abstractions)
1. `utc_hour()` - 22 edges
2. `Ledger` - 18 edges
3. `demo()` - 15 edges
4. `utc_time()` - 15 edges
5. `inspect()` - 14 edges
6. `rollout_substeps()` - 14 edges
7. `ArtifactStore` - 13 edges
8. `checked_rollout()` - 13 edges
9. `record()` - 13 edges
10. `read_record()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `Diurnal and semidiurnal forcing` --references--> `thermal_step()`  [EXTRACTED]
  docs/DESIGN.md → src/streamingcast/physics.py
- `Toy-model substep integration` --references--> `rollout_substeps()`  [EXTRACTED]
  docs/REVIEW_FIX.md → src/streamingcast/physics.py
- `Review hardening controls` --references--> `check_boundary()`  [EXTRACTED]
  docs/REVIEW_FIX.md → src/streamingcast/guards.py
- `Review hardening controls` --references--> `checked_rollout()`  [EXTRACTED]
  docs/REVIEW_FIX.md → src/streamingcast/guards.py
- `Issuance-time immutable snapshot` --references--> `Snapshot`  [EXTRACTED]
  docs/LOCAL_DATA.md → src/streamingcast/stream.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **P0 manufactured differentiability evidence** — docs_design_toy_equations, docs_design_numerical_differentiation, docs_design_manufactured_learning, docs_verification_manufactured_results [INFERRED 0.95]
- **ERA5 readiness work leading to a D83 adapter** — docs_era5_readiness_global_cache, docs_era5_readiness_d83_gaps, docs_era5_readiness_next_steps, docs_local_data_d83_contract [INFERRED 0.95]
- **Source-backed knowledge maintenance cycle** — docs_knowledge_workflow_authority, docs_knowledge_workflow_session_cycle, docs_knowledge_workflow_graphify_refresh, docs_knowledge_workflow_durable_outputs [EXTRACTED 1.00]

## Communities (10 total, 2 thin omitted)

### Community 0 - "Manufactured numerical verification"
Cohesion: 0.10
Nodes (48): RuntimeError, long_rollout_evidence(), Manufactured E-M-P-H differentiability and temporal refinement evidence. No…, refinement_evidence(), run(), atomic_json(), check_boundary(), checked_rollout() (+40 more)

### Community 1 - "Local inputs and schemas"
Cohesion: 0.10
Nodes (42): check_catalog(), demo(), inspect_local(), main(), Local entry points. Real-data manifests are inspected, never silently forecast…, Explicit ingest-all validation, intentionally separate from as-of inspect., atomic_npz(), Offline NPZ adapter. No remote fetch, pickle, implicit unit conversion or… (+34 more)

### Community 2 - "Forecast science and ERA5 readiness"
Cohesion: 0.05
Nodes (47): Diurnal and semidiurnal forcing, External NWP differentiation boundary, ForecastStep contract, Manufactured learning and reference, Numerical differentiation checks, PyTorch JVP documentation, PyTorch VJP documentation, Taylor verification documentation (+39 more)

### Community 3 - "Hourly time and rainfall contracts"
Cohesion: 0.18
Nodes (24): accumulate(), Accumulation, concatenate_hours(), HourlyRain, probability(), datetime, Trajectory-first rain aggregation. This does not calibrate a probability model., summarize_members() (+16 more)

### Community 4 - "SI and observation coupling tests"
Cohesion: 0.14
Nodes (27): chain_evidence(), decode_si(), encode_si(), forecast_observations(), Explicit SI/native/observation chain for FOUR manufactured column variables.…, E -> native M -> P -> H, including 1h rain accumulated before observation. No…, validate_observation_weights(), args() (+19 more)

### Community 5 - "ERA5 structural inspection"
Cohesion: 0.15
Nodes (12): Path, _chunk_inventory(), inspect(), main(), _metadata_digest(), _metadata_paths(), _months_progress(), Return the month numbers recorded in a text or JSON progress marker. (+4 more)

### Community 6 - "Content addressed artifacts"
Cohesion: 0.33
Nodes (3): ArtifactStore, Local content-addressed outputs; never overwrite an installed object. One…, Read-only inventory. No orphan is deleted automatically.

### Community 7 - "Knowledge management cycle"
Cohesion: 0.67
Nodes (3): Knowledge durable outputs, Graphify document refresh, Knowledge session cycle

## Knowledge Gaps
- **12 isolated node(s):** `Agent Working Guidelines`, `Four-variable toy-column model`, `PyTorch JVP documentation`, `PyTorch VJP documentation`, `Taylor verification documentation` (+7 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 49 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `StreamingCAST` connect `Forecast science and ERA5 readiness` to `ERA5 structural inspection`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `utc_hour()` connect `Hourly time and rainfall contracts` to `Local inputs and schemas`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `demo()` connect `Local inputs and schemas` to `Manufactured numerical verification`, `Hourly time and rainfall contracts`, `ERA5 structural inspection`, `Content addressed artifacts`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Ledger` (e.g. with `test_cutoff_revisions_replay_and_freeze()` and `test_geometry_and_snapshot_bypass_rejected()`) actually correct?**
  _`Ledger` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Path` (e.g. with `inspect()` and `_metadata_paths()`) actually correct?**
  _`Path` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Agent Working Guidelines`, `Four-variable toy-column model`, `PyTorch JVP documentation` to the rest of the system?**
  _12 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Manufactured numerical verification` be split into smaller, more focused modules?**
  _Cohesion score 0.09796806966618288 - nodes in this community are weakly interconnected._

## Scope and Freshness
- Graphify 0.9.53; local AST plus GPT-6-luna/high document extraction.
- Inputs: 18 code files and 12 repository documents. Raw arrays, evidence JSON, credentials, runtime outputs, wiki and graph outputs excluded.
- 12 explicit document-to-code references connect original citations to existing AST nodes; no duplicate code nodes added.
- Source hashes: `source_manifest.json`. Graph edges and communities are derived navigation, not independent scientific evidence.
- Host skill instructions are v0.8.39; installed package is v0.9.53. Installed API signatures were checked; the skill was not overwritten.
