# StreamingCAST P0 status

Tracking issue: #1. Updated: 2026-10-11.

## Implemented in this change

- v0.1.1 time_contract.py/products.py selected migration with source hashes.
- D83/1h rain contract, immutable issuance snapshot, late revision and replay handling.
- Local-only NPZ boundary; no real-data download or upload.
- Pure tensor toy forecast API; JVP/VJP, weighted adjoint, finite difference and Taylor checks.
- 3-parameter manufactured learning, 240h independent-initial-state forecast, diurnal/semidiurnal and restart checks.
- Source, tests, environment and numerical evidence in the repository.

## Approval boundary

`P0_contracts = PASS`, `P0_toy_differentiability = PASS`, `P0_manufactured_learning = PASS`.
These labels are limited to evidence/proof.json and the tests in this commit.

Previous D83 240h synthetic prediction was worse than persistence. That failure is preserved, NOT fixed by this toy.
D83 neural forecasting, ERA5 preprocessing/streaming, full scalar/vector remapping, actual tidal and rainfall skill,
LAYA weights/policy, B200, and external differentiable NWP integration remain NOT_RUN/UNAPPROVED.
The new model is not a replacement for the original D83 model.

## Inventory-aligned plan and external benchmarks

The inventory in [ERA5_READINESS.md](ERA5_READINESS.md) changes the acquisition and training order.
[ERA5_ALIGNED_PLAN.md](ERA5_ALIGNED_PLAN.md) now separates a planned 6h G29+P6h research path,
regional hourly operator tests, and the final hourly D83+P1h target. The 6h adapter/model is not implemented
by this planning change. Raw ERA5 stays local; the existing hourly Snapshot is not weakened.

[BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md) and `benchmarks/` contain 60 reported RMSE values
and 3 reported precipitation ROCSS values from two primary publications, with provenance and missingness.
They are historical references, not local reproduced forecasts or current universal rankings.
`benchmark_contract.py` rejects mismatched or incomplete local comparison conditions and never grants
whole-model approval from a single score. New tests cover these contracts and plan arithmetic only.

The historical comparison split is train 1979-2017, model selection 2018, calibration 2019, test 2020,
with test targets through 2021-01-10 12 UTC. Pretraining and prior use must still be checked.
The separate final 2025 initialization window through the 2026-01-10 target tail is not locally available.
The old 134 TB / B200 full-training scenario is not a measured cost for the existing 30-channel cache.

## Next bounded work

1. Locally verify payloads, rainfall intervals, surface pressure/static fields and archive gaps without altering the source cache.
2. Freeze source/grid/statistics hashes and implement a separate 6h profile; do not call it hourly D83.
3. Compute persistence/climatology and fixed-model forecasts on matched held-out cases before claiming benchmark improvement.
4. Validate regional hybrid-pressure and observation adapters with JVP/VJP/Taylor; global hourly targets remain a separate acquisition gate.
5. Retain hourly rain, S1/S2 uncertainty, native spectra and differentiable-NWP gates even when public RMSE improves.
6. Compare fixed/unshared and looped structures, then optional LAYA. No automatic production approval.

## Repository operation

Code changes go to the work branch and a review PR, not a direct main overwrite.
No model arrays, real data, credentials, heavy CI, GPU job submission or automatic merge is added.
Only a local SQLite ledger is implemented: distributed exactly-once publication is NOT claimed.
