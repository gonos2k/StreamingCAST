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

## Next bounded work

Local ERA5 inventory is now recorded in [ERA5_READINESS.md](ERA5_READINESS.md).
The 1979–2022 global cache exists, but its six-hourly 30-channel schema cannot
supply adjacent hourly D83 states. Structural inventory is not preprocessing,
real-data forecast validation, or approval of the outstanding work below.

1. User-side local preprocessing produces canonical records and verified geometry/stats hashes.
2. An adapter converts that schema into the selected model's native tensors without breaking gradients.
3. Add a spatial physical model and compare tangent/adjoint/Taylor with independent references.
4. Integrate the previously patched D83 neural core only after its separate long-rollout failure is diagnosed.
5. Compare fixed/unshared and looped structures, then optional LAYA. No automatic production approval.

## Repository operation

Code changes go to the work branch and a review PR, not a direct main overwrite.
No model arrays, real data, credentials, heavy CI, GPU job submission or automatic merge is added.
Only a local SQLite ledger is implemented: distributed exactly-once publication is NOT claimed.
