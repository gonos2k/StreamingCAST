"""Bounded follow-up to PR #6: matching definitions must also be valid.
All inputs are manufactured. Passing these tests never approves weather skill.
"""
from copy import deepcopy
import json

import numpy as np
import pytest

from streamingcast.benchmark_contract import (
    BenchmarkContractError, case_area_mse, paired_rmse_check, require_matched_local,
)
from test_benchmark_contract import contract


@pytest.mark.parametrize("changes", [
    {"units": "hPa"},
    {"variable": "unregistered_variable"},
    {"temporal_statistic": "accumulation", "interval_start_offset": 0},
    {"variable": "tp", "units": "mm"},
])
def test_equal_invalid_definitions_are_rejected(changes):
    a = contract(); a.update(changes)
    with pytest.raises(BenchmarkContractError):
        require_matched_local(a, deepcopy(a))


def test_rmse_gate_rejects_equal_but_wrong_aggregation():
    a = contract(); a["aggregation"] = "mean_rmse"
    with pytest.raises(BenchmarkContractError):
        paired_rmse_check([.81]*12, [1.]*12, np.arange(12), a, a, resamples=200)


@pytest.mark.parametrize("name,units,coordinate,level,temporal,start", [
    ("t2m", "K", "surface", None, "instantaneous", 24),
    ("specific_humidity", "kg kg-1", "pressure_hpa", 700, "instantaneous", 24),
    ("specific_humidity", "g kg-1", "pressure_hpa", 700, "instantaneous", 24),
    ("sp", "Pa", "surface", None, "instantaneous", 24),
    ("omega", "Pa s-1", "pressure_hpa", 500, "instantaneous", 24),
    ("tp", "mm", "surface", None, "accumulation", 18),
])
def test_registered_physical_definitions_remain_usable(name, units, coordinate, level, temporal, start):
    a = contract(); a.update(variable=name, units=units, vertical_coordinate=coordinate,
                             level=level, temporal_statistic=temporal, interval_start_offset=start)
    b = deepcopy(a); b["model_sha256"] = "a"*64
    result = paired_rmse_check([0.]+[.81]*11, [0.]+[1.]*11, np.arange(12), a, b, resamples=200)
    assert result["metric_status"] == "IMPROVED"
    assert result["relative_rmse_change"] == pytest.approx(-.1)
    assert result["forecast_skill_approved"] is False


@pytest.mark.parametrize("field", ["prediction", "target", "weights"])
@pytest.mark.parametrize("dtype", ["complex128", "object", "bool", "U8"])
def test_physical_metric_rejects_lossy_or_nonnumeric_coercion(field, dtype):
    args = {"prediction": np.ones((1,2)), "target": np.zeros((1,2)), "weights": np.ones(2)}
    args[field] = args[field].astype(dtype)
    if dtype == "complex128":
        args[field] += 100j
    with pytest.raises(BenchmarkContractError):
        case_area_mse(**args, mask=np.ones((1,2), bool))


@pytest.mark.parametrize("side", ["candidate", "baseline"])
def test_paired_metric_rejects_complex_scores(side):
    a, b = np.ones(12), np.ones(12)
    if side == "candidate": a = a + 10j
    else: b = b + 10j
    with pytest.raises(BenchmarkContractError):
        paired_rmse_check(a, b, np.arange(12), contract(), contract(), resamples=200)


@pytest.mark.parametrize("error", [1e-200, float(np.sqrt(np.nextafter(0., 1.)))])
def test_nonzero_errors_are_not_silently_turned_into_perfect_forecasts(error):
    # Even a representable final subnormal may be refused when its terms underflow.
    # Explicit refusal is preferred to an incorrect exact zero.
    p = np.full((1,16), error)
    with pytest.raises(BenchmarkContractError, match="underflow"):
        case_area_mse(p, np.zeros_like(p), np.ones(16), np.ones_like(p, bool))


def test_exact_zeros_masked_nan_and_large_areas_are_still_valid():
    p = np.array([[0., 0., np.nan], [.5, .5, np.nan]])
    m = np.array([[True, True, False]]*2)
    got = case_area_mse(p, np.zeros_like(p), np.full(3, 1e308), m)
    assert got == pytest.approx([0., .25])
    identical = paired_rmse_check(np.full(12,1e308), np.full(12,1e308), np.arange(12),
                                 contract(), contract(), resamples=200)
    assert identical["metric_status"] == "NONINFERIOR"
    assert identical["interval"] == pytest.approx([0., 0.])
    empty_ratio = paired_rmse_check(np.zeros(12), np.zeros(12), np.arange(12),
                                   contract(), contract(), resamples=200)
    assert empty_ratio["reason"] == "ZERO_BASELINE_MEAN"
    json.dumps([identical, empty_ratio], allow_nan=False)
