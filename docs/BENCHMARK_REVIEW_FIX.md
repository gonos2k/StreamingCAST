# Benchmark comparison review fixes

The post-merge review of PR #4 found that its passing synthetic tests did not
cover product identity, legitimate zero errors or extreme finite arithmetic.
This follow-up preserves the 63 historical reference values and tightens the
local comparison contract. PR #4's historical execution receipt remains unchanged.

## Product identity and contract migration

Local submissions now explicitly provide `vertical_coordinate` (`surface` or
`pressure_hpa`), `level`, `interval_start_offset`, `interval_end_offset`,
`forecast_statistic`, `quantile_probability`, `metric_definition` and
`preprocessing_digest`. Offsets are integer hours from initialization and end
at `lead_hours`; instantaneous fields have equal endpoints and accumulated
fields have a positive interval. Quantiles require a finite probability strictly
between zero and one; other statistics require an explicit null probability.
Surface fields require an explicit null level. Leads and member counts are
positive integers, excluding booleans.

The ambiguous `weights_sha256` evaluation field is replaced by
`area_weights_sha256`, which identifies the scoring cell-area weights and must
match. `model_sha256` identifies each model/checkpoint and may differ; both sides
must still record a valid hash. Existing submissions must migrate these fields;
an opaque protocol ID or full-array target hash does not identify a selected
pressure level or accumulation window.

[`require_matched_local`](../src/streamingcast/benchmark_contract.py) rejects
product differences before bootstrap scoring. `paired_rmse_check` accepts RMSE
contracts only. None of its single-metric states approves a weather model.

## Zero errors and arithmetic

Individual candidate and baseline case MSE may be zero. Cases are preserved.
An entirely zero baseline, or any sampled zero-baseline bootstrap replicate,
returns `INSUFFICIENT` with an explicit reason and null relative interval; no
epsilon is added and no replicate is silently removed.

Cell areas are normalized over each case's valid domain before summation.
Paired MSE values share a common scale before block sums and ratios. These
changes preserve the mathematical metric while preventing intermediate overflow
for equal large finite inputs. Unrepresentable arithmetic, including positive
values lost during scaling, raises `BenchmarkContractError`; results must not
contain NaN or infinity. Missing valid-domain predictions remain errors.

## Published definitions and unresolved reproduction

Catalog validation now checks variable/unit/metric combinations, positive
pressure levels versus null surface levels, primary-source metric/layer axes,
and source lead times. Missing results keep null values and undergo the same
definition checks.

The precipitation source records its binary predictor transform, threshold
comparison and fit period, spatial aggregation, threshold hash and single-class
cell policy. Unknown artifacts or unspecified policy remain explicitly unknown;
historical paper values do not become reproducible local comparisons merely
because this metadata is present. See [the protocol](BENCHMARK_PROTOCOL.md) and
[registry](../benchmarks/reference_scores.json).

## Validation and project integration

Regression cases cover differing pressure levels, quantiles and intervals,
invalid types, zero-error cases, extreme finite weights/scores and catalog
definition corruption. Executed results and source hashes are recorded separately
under `evidence/knowledge/`; these are engineering checks, not weather skill.

This review branch combines current main's ERA5-aligned plan with the KG files
that PR #5 merged into the prior data branch. Existing Source pages retain
their original source commit/hash, including historical project status. The
graph is rebuilt against the current working inputs and its input manifest.

On this Mac, Graphify's RapidFuzz compiled extension was blocked by Gatekeeper.
Graphify commands use `RAPIDFUZZ_IMPLEMENTATION=python`; quarantine and macOS
security settings are preserved. This affects graph string matching, not the
forecast comparison implementation.
