# Graph Report - StreamingCAST  (2026-10-12)

## Corpus Check
- 36 files · ~17,048 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 323 nodes · 790 edges · 11 communities (9 shown, 2 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 100 edges (avg confidence: 0.91)
- Token usage: unknown (null; host extraction usage was unavailable).
- Graphify runtime used `RAPIDFUZZ_IMPLEMENTATION=python` to avoid loading the quarantined optional RapidFuzz extension.

## Community Hubs (Navigation)
- Benchmark Contracts
- Manufactured Model Verification
- ERA5 Forecast Readiness
- Streaming Data Contracts
- Time and Rainfall Contracts
- ERA5 Cache Inspection
- Artifact Storage
- Observation Coupling Verification
- Package Scope
- Knowledge Maintenance
- Graphify Runtime Guidance

## God Nodes (most connected - your core abstractions)
1. `BenchmarkContractError` - 24 edges
2. `utc_hour()` - 22 edges
3. `Ledger` - 18 edges
4. `contract()` - 18 edges
5. `paired_rmse_check()` - 15 edges
6. `demo()` - 15 edges
7. `utc_time()` - 15 edges
8. `rollout_substeps()` - 14 edges
9. `inspect()` - 14 edges
10. `ArtifactStore` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Toy-model substep integration` --references--> `rollout_substeps()`  [EXTRACTED]
  docs/REVIEW_FIX.md → src/streamingcast/physics.py
- `Diurnal and semidiurnal forcing` --references--> `thermal_step()`  [EXTRACTED]
  docs/DESIGN.md → src/streamingcast/physics.py
- `Issuance-time immutable snapshot` --references--> `Snapshot`  [EXTRACTED]
  docs/LOCAL_DATA.md → src/streamingcast/stream.py
- `Six-hour sampling rank limit` --references--> `run()`  [EXTRACTED]
  docs/ERA5_ALIGNED_PLAN.md → scripts/check_benchmarks.py
- `Benchmark product-identity contract` --references--> `paired_rmse_check()`  [EXTRACTED]
  docs/BENCHMARK_REVIEW_FIX.md → src/streamingcast/benchmark_contract.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Source-backed knowledge maintenance cycle** — docs_knowledge_workflow_authority, docs_knowledge_workflow_session_cycle, docs_knowledge_workflow_graphify_refresh, docs_knowledge_workflow_durable_outputs [EXTRACTED 1.00]
- **ERA5 readiness work leading to a D83 adapter** — docs_era5_readiness_global_cache, docs_era5_readiness_d83_gaps, docs_era5_readiness_next_steps, docs_local_data_d83_contract [INFERRED 0.95]
- **P0 manufactured differentiability evidence** — docs_design_toy_equations, docs_design_numerical_differentiation, docs_design_manufactured_learning, docs_verification_manufactured_results [INFERRED 0.95]

## Communities (11 total, 2 thin omitted)

### Community 0 - "Benchmark Contracts"
Cohesion: 0.08
Nodes (56): BenchmarkContractError, run(), canonical_hash(), case_area_mse(), _catalog_definition(), _finite_number(), paired_rmse_check(), require_matched_local() (+48 more)

### Community 1 - "Manufactured Model Verification"
Cohesion: 0.09
Nodes (52): VerificationError, long_rollout_evidence(), refinement_evidence(), run(), atomic_json(), check_boundary(), checked_rollout(), finite_gradients() (+44 more)

### Community 2 - "ERA5 Forecast Readiness"
Cohesion: 0.05
Nodes (48): ForecastStep, Protocol, Tensor, Diurnal and semidiurnal forcing, ForecastStep contract, Manufactured learning and reference, Numerical differentiation checks, Toy-column equations (+40 more)

### Community 3 - "Streaming Data Contracts"
Cohesion: 0.11
Nodes (39): Ledger, Record, check_catalog(), demo(), inspect_local(), main(), atomic_npz(), read_manifest() (+31 more)

### Community 4 - "Time and Rainfall Contracts"
Cohesion: 0.14
Nodes (27): Accumulation, HourlyRain, Snapshot, ForecastWindow, accumulate(), concatenate_hours(), probability(), summarize_members() (+19 more)

### Community 6 - "ERA5 Cache Inspection"
Cohesion: 0.16
Nodes (12): Era5CacheTests, _chunk_inventory(), inspect(), main(), _metadata_digest(), _metadata_paths(), _months_progress(), _read_json() (+4 more)

### Community 7 - "Artifact Storage"
Cohesion: 0.29
Nodes (3): ArtifactStore, Local content-addressed outputs; never overwrite an installed object. One…, Read-only inventory. No orphan is deleted automatically.

### Community 5 - "Observation Coupling Verification"
Cohesion: 0.14
Nodes (27): chain_evidence(), decode_si(), encode_si(), forecast_observations(), validate_observation_weights(), args(), test_artifact_install_idempotency_and_recovery(), test_artifact_invalid_arrays() (+19 more)

### Community 8 - "Knowledge Maintenance"
Cohesion: 0.67
Nodes (3): Knowledge durable outputs, Graphify document refresh, Knowledge session cycle

## Knowledge Gaps
- **15 isolated node(s):** `ERA5 structural inspector`, `Pinned kg v1 schema`, `SQLite idempotent execution ledger`, `Local manifest record contract`, `Hourly precipitation contract` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 65 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `test_benchmark_contract.py` to `Path`?**
  _High betweenness centrality (0.263) - this node is a cross-community bridge._
- **Why does `Matched local evaluation contract` connect `test_benchmark_contract.py` to `StreamingCAST`?**
  _High betweenness centrality (0.155) - this node is a cross-community bridge._
- **Why does `demo()` connect `test_contracts.py` to `verification.py`, `utc_hour`, `Path`, `ArtifactStore`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `BenchmarkContractError` (e.g. with `test_accumulation_interval_is_part_of_matched_protocol()` and `test_area_mask_and_missing_prediction()`) actually correct?**
  _`BenchmarkContractError` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `Ledger` (e.g. with `test_cutoff_revisions_replay_and_freeze()` and `test_geometry_and_snapshot_bypass_rejected()`) actually correct?**
  _`Ledger` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Path` (e.g. with `inspect()` and `_metadata_paths()`) actually correct?**
  _`Path` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ERA5 structural inspector`, `Pinned kg v1 schema`, `SQLite idempotent execution ledger` to the rest of the system?**
  _15 weakly-connected nodes found - possible documentation gaps or missing edges._