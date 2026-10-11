# P0 execution evidence — 2026-10-11

## Actual runs

- Python 3.13.5, PyTorch 2.10.0+cpu, NumPy 2.3.5, SciPy 1.17.0; CPU, FP64 reference.
- `python -m pytest -q`: 53 passed. Torch-internal deprecation warnings are recorded in evidence/pytest.txt.
- `streamingcast demo`: creates two local synthetic NPZ records, validates issuance history,
  runs 240 one-hour toy steps, writes only local output, and registers the same run twice with one insertion.
- `streamingcast prove`: trains 3 parameter initializations, tests independent cases with a separate DOP853 reference,
  differentiates a 6h rollout, verifies harmonic response and 137+103h restart.
- No GPU, actual weather data, external model or LAYA API was used.

## Results (raw: evidence/proof.json)

Weighted-adjoint relative mismatch: 0 in this FP64 direction test.
JVP versus central finite difference relative error: 3.8120e-10.
Second-order Taylor slopes: 1.98925, 1.99465, 1.99733, 1.99867.
Autograd gradcheck: passed.
Dry 24h/12h thermal response, 240h maximum absolute error: 2.1344e-14 K.
Daily endpoint counterexample: hourly RMSE 0.790569, daily endpoint RMSE 7.20e-15.

Three fitted parameters use 96 one-hour state pairs. All three initializations are retained.
The final independent manufactured test contains 12 cases and 240 hourly transitions.
Maximum of the three models' 240h state RMSE: theta 3.8791e-7 K, q 4.7766e-8 g/kg.
Maximum accumulated-rain RMSE: 4.7766e-8 mm. This is a simple known-equation inverse problem, NOT real weather skill.
The column water residual is about 1.1e-13 mm; restart arrays match bitwise in this environment.

## Interpretation

The dry exact tide test is a property of the imposed operator, not a learned full-atmosphere result.
Small fitting error is expected because the forward law has only three unknown coefficients and is known structurally.
Differentiability tests certify sampled code paths of the discrete toy, not continuous primitive-equation adjoints.
Unit tests include rejection/counterexample checks; count is not a scientific safety score.
Metadata cutoff/hash checks cannot prove that a local collector reported truthful availability or correct physical preprocessing.

## Reproduction

```bash
python -m pip install -e '.[test]'
python -m pytest -q
streamingcast demo --root local_data/fresh_demo
streamingcast prove --out runs/new_proof/proof.json
```

Use a fresh directory for demo. In prove, timing can vary; scientific arrays/metrics are compared separately.
Do not interpret this CPU runtime as a B200 or D83 full-model estimate.
