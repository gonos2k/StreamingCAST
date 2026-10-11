"""Local benchmark contracts, NOT a replacement for WeatherBench-X.

External paper scores cannot approve a local forecast. No network or data I/O
is performed here. Numeric examples/tests are synthetic unless labelled otherwise.
"""
from __future__ import annotations

from datetime import date
import hashlib
import json
import math
import re
from typing import Any

import numpy as np


class BenchmarkContractError(ValueError):
    """Missing, incompatible or scientifically ambiguous evaluation evidence."""


def canonical_hash(value: Any) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode()).hexdigest()


CATALOG_VARIABLES = {
    "geopotential": ("m2 s-2", True, "RMSE"),
    "temperature": ("K", True, "RMSE"),
    "specific_humidity": ("g kg-1", True, "RMSE"),
    "u": ("m s-1", True, "RMSE"), "v": ("m s-1", True, "RMSE"),
    "t2m": ("K", False, "RMSE"),
    "u10": ("m s-1", False, "RMSE"), "v10": ("m s-1", False, "RMSE"),
    "tp24h_wet90": ("1", False, "ROCSS"),
}


def _finite_number(value) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _catalog_definition(record: dict, sources: dict) -> None:
    required = ("source_id", "model", "metric", "variable", "level_hpa",
                "lead_hours", "units", "value")
    if any(key not in record for key in required):
        raise BenchmarkContractError("Incomplete score definition")
    source = sources.get(record["source_id"])
    if not source or not source.get("url") or not source.get("locator"):
        raise BenchmarkContractError("A primary source and exact location are required")
    if source.get("raw_forecasts_recomputed_here") is not False:
        raise BenchmarkContractError("Imported scores must not assert local re-evaluation")
    spec = CATALOG_VARIABLES.get(record["variable"])
    if spec is None or (record["units"], record["metric"]) != (spec[0], spec[2]):
        raise BenchmarkContractError("Unregistered variable/units/metric combination")
    level = record["level_hpa"]
    if spec[1]:
        if not _finite_number(level) or not 0 < level <= 1100:
            raise BenchmarkContractError("Positive pressure level in hPa required")
    elif level is not None:
        raise BenchmarkContractError("Surface variables require a null pressure level")
    source_levels = source.get("variable_levels_hpa", {}).get(record["variable"])
    if source.get("metric") != record["metric"] or not isinstance(source_levels, list) or level not in source_levels:
        raise BenchmarkContractError("Metric/variable/level must match the primary source axes")
    lead = record["lead_hours"]
    if type(lead) is not int or lead <= 0:
        raise BenchmarkContractError("Positive integer lead required")
    leads = source.get("lead_hours")
    if not isinstance(leads, list) or any(type(v) is not int or v <= 0 for v in leads) or lead not in leads:
        raise BenchmarkContractError("Score lead must match its source definition")
    if not isinstance(record["model"], str) or not record["model"].strip():
        raise BenchmarkContractError("Model identifier required")
    if record["metric"] == "ROCSS":
        fields = ("predictor_transform", "threshold_fit_period", "threshold_hash",
                  "threshold_comparison", "spatial_aggregation", "single_class_cell_policy")
        if any(key not in source for key in fields):
            raise BenchmarkContractError("ROCSS transform and aggregation provenance required")


def validate_catalog(catalog: dict) -> dict:
    if catalog.get("schema") != "streamingcast-external-benchmark-catalog-v1":
        raise BenchmarkContractError("Unknown catalog schema")
    seen = set()
    counts: dict[str, int] = {}
    for record in catalog["records"]:
        _catalog_definition(record, catalog["sources"])
        value = record["value"]
        if type(value) not in (int, float) or not math.isfinite(value):
            raise BenchmarkContractError("Numeric finite score required; no zero-filled missing data")
        if record["metric"] == "RMSE" and value < 0:
            raise BenchmarkContractError("Negative RMSE")
        if record["metric"] == "ROCSS" and not -1 <= value <= 1:
            raise BenchmarkContractError("ROCSS outside [-1,1]")
        if record["metric"] not in ("RMSE", "ROCSS"):
            raise BenchmarkContractError("Metric definition not registered")
        if type(record["lead_hours"]) is not int or record["lead_hours"] <= 0:
            raise BenchmarkContractError("Positive integer lead required")
        key = tuple(record[k] for k in
                    ("source_id", "model", "metric", "variable", "level_hpa", "lead_hours"))
        if key in seen:
            raise BenchmarkContractError("Duplicate metric row")
        seen.add(key)
        counts[record["metric"]] = counts.get(record["metric"], 0) + 1
    for record in catalog.get("missing_records", []):
        _catalog_definition(record, catalog["sources"])
        if record["value"] is not None:
            raise BenchmarkContractError("Missing results must stay null, not zero")
    return {"records": len(seen), "counts": counts,
            "sources": len(catalog["sources"]), "forecast_skill_approved": False}


# Model IDs can differ, but every evaluation condition below must match.
PROTOCOL_FIELDS = (
    "protocol_id", "variable", "units", "lead_hours", "temporal_statistic",
    "forecast_statistic", "ensemble_members", "init_sample_sha256",
    "target_sha256", "initial_analysis", "grid_sha256", "mask_sha256",
    "area_weights_sha256", "climatology_id", "aggregation", "vertical_coordinate",
    "level", "interval_start_offset", "interval_end_offset", "quantile_probability",
    "metric_definition", "preprocessing_digest",
)
HASH_FIELDS = ("init_sample_sha256", "target_sha256", "grid_sha256",
               "mask_sha256", "area_weights_sha256", "model_sha256", "preprocessing_digest")


def require_matched_local(candidate: dict, baseline: dict) -> None:
    for item in (candidate, baseline):
        if item.get("evidence_class") != "local_recomputed":
            raise BenchmarkContractError("Paper tables/unknown lineage cannot approve local skill")
        if item.get("holdout_independence_checked") is not True:
            raise BenchmarkContractError("Pretraining and test overlap must be checked")
        for key in PROTOCOL_FIELDS:
            value = item.get(key)
            if key not in item or (key not in ("level", "quantile_probability") and
                                   (value is None or value == "" or value == "unknown")):
                raise BenchmarkContractError(f"Missing evaluation field: {key}")
        for key in HASH_FIELDS:
            if not isinstance(item.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", item[key]):
                raise BenchmarkContractError(f"SHA-256 required: {key}")
        lead, members = item["lead_hours"], item["ensemble_members"]
        if type(lead) is not int or lead <= 0 or type(members) is not int or members <= 0:
            raise BenchmarkContractError("Positive integer lead and ensemble size required")
        coordinate, level = item["vertical_coordinate"], item["level"]
        if coordinate == "pressure_hpa":
            if not _finite_number(level) or not 0 < level <= 1100:
                raise BenchmarkContractError("Pressure level in hPa required")
        elif coordinate != "surface" or level is not None:
            raise BenchmarkContractError("Surface coordinate requires null level")
        spec = CATALOG_VARIABLES.get(item["variable"])
        if spec and spec[1] != (coordinate == "pressure_hpa"):
            raise BenchmarkContractError("Variable and vertical coordinate disagree")
        start, end = item["interval_start_offset"], item["interval_end_offset"]
        # Offsets are integer hours relative to initialization, not to the lead.
        if type(start) is not int or type(end) is not int or not 0 <= start <= end == lead:
            raise BenchmarkContractError("Explicit interval offsets ending at the lead required")
        temporal = item["temporal_statistic"]
        if temporal == "instantaneous":
            if start != end:
                raise BenchmarkContractError("Instantaneous fields require equal interval endpoints")
        elif temporal != "accumulation" or start >= end:
            raise BenchmarkContractError("Registered accumulation requires a positive interval")
        statistic, probability = item["forecast_statistic"], item["quantile_probability"]
        if statistic == "quantile":
            if not _finite_number(probability) or not 0 < probability < 1:
                raise BenchmarkContractError("Quantile probability in (0,1) required")
        elif statistic not in ("deterministic_point", "ensemble_mean") or probability is not None:
            raise BenchmarkContractError("Non-quantile forecasts require null quantile probability")
        if statistic == "deterministic_point" and members != 1:
            raise BenchmarkContractError("Deterministic point forecasts require one member")
        for key in ("protocol_id", "variable", "units", "initial_analysis",
                    "climatology_id", "aggregation", "metric_definition"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise BenchmarkContractError(f"Text evaluation field required: {key}")
    mismatch = [key for key in PROTOCOL_FIELDS if candidate[key] != baseline[key]]
    if mismatch:
        raise BenchmarkContractError("Incompatible protocols: " + ", ".join(mismatch))


def case_area_mse(prediction, target, weights, mask) -> np.ndarray:
    """Per-initialization spatial MSE; RMSE = sqrt(mean(returned MSE)).

    Arrays: [initialization, ...spatial...]; one variable/level/lead per call.
    The mask is truth/protocol-defined and must be shared between models.
    Any missing prediction on the valid domain is a failure, not a dropped cell.
    This is our local metric contract, not a claim of bitwise WB-X equivalence.
    """
    p, y = np.asarray(prediction, dtype=np.float64), np.asarray(target, dtype=np.float64)
    m, w = np.asarray(mask), np.asarray(weights, dtype=np.float64)
    if p.shape != y.shape or p.ndim < 2 or not p.size:
        raise BenchmarkContractError("Matching nonempty [case,spatial...] required")
    if m.dtype != np.bool_ or m.shape != p.shape:
        raise BenchmarkContractError("An explicit same-shape bool mask is required")
    if w.shape != p.shape[1:] or not np.isfinite(w).all() or (w <= 0).any():
        raise BenchmarkContractError("Positive finite spatial cell areas required")
    if not np.isfinite(p[m]).all() or not np.isfinite(y[m]).all():
        raise BenchmarkContractError("Nonfinite valid prediction/target; do not silently drop")
    axes = tuple(range(1, p.ndim))
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        try:
            # Normalize per case over its valid cells; common area scale cancels.
            valid_w = np.where(m, w, 0.0)
            scale = valid_w.max(axis=axes, keepdims=True)
            if (scale <= 0).any():
                raise BenchmarkContractError("Empty initialization in fixed verification domain")
            valid_w = valid_w / scale
            if (m & (valid_w == 0)).any():
                raise BenchmarkContractError("Area scaling underflow")
            denom = valid_w.sum(axis=axes, keepdims=True)
            normalized = valid_w / denom
            if (m & (normalized == 0)).any():
                raise BenchmarkContractError("Normalized area underflow")
            diff = np.where(m, p, 0.0) - np.where(m, y, 0.0)
            # Weight before squaring so representable weighted errors need not overflow.
            error = diff * np.sqrt(normalized)
            out = np.sum(error * error, axis=axes)
        except FloatingPointError as exc:
            raise BenchmarkContractError("Metric arithmetic overflow") from exc
    if not np.isfinite(out).all():
        raise BenchmarkContractError("Nonfinite metric")
    return out


def paired_rmse_check(candidate_mse, baseline_mse, block_ids,
                      candidate_contract: dict, baseline_contract: dict,
                      *, margin: float = .02, resamples: int = 2000,
                      seed: int = 42, alpha: float = .05) -> dict:
    """Conditional, single-metric block-bootstrap gate. Not release approval.

    Block construction must be frozen from temporal dependence BEFORE scoring.
    Ten blocks is only a refusal floor, not a guarantee of inferential power.
    Every sampled block contributes all its cases. Case hashes must match.
    """
    require_matched_local(candidate_contract, baseline_contract)
    if candidate_contract["metric_definition"] != "RMSE":
        raise BenchmarkContractError("This gate evaluates RMSE only")
    a, b = np.asarray(candidate_mse, float), np.asarray(baseline_mse, float)
    ids = np.asarray(block_ids)
    if a.ndim != 1 or a.shape != b.shape or ids.shape != a.shape or not a.size:
        raise BenchmarkContractError("Matching nonempty case scores and block IDs required")
    if not np.isfinite(a).all() or not np.isfinite(b).all() or (a < 0).any() or (b < 0).any():
        raise BenchmarkContractError("Finite nonnegative scores required")
    if type(resamples) is not int or resamples < 200:
        raise BenchmarkContractError("At least 200 bootstrap replicates required")
    if type(margin) not in (int, float) or not math.isfinite(margin) or not 0 <= margin < 1:
        raise BenchmarkContractError("Finite relative margin in [0,1) required")
    if type(alpha) not in (int, float) or not math.isfinite(alpha) or not 0 < alpha < 1:
        raise BenchmarkContractError("alpha must be in (0,1)")
    blocks = [np.flatnonzero(ids == k) for k in np.unique(ids)]
    if len(blocks) < 10 or any(not len(ix) for ix in blocks):
        return {"metric_status": "INSUFFICIENT_BLOCKS", "blocks": len(blocks),
                "forecast_skill_approved": False}
    if not b.any():
        return {"metric_status": "INSUFFICIENT", "reason": "ZERO_BASELINE_MEAN",
                "relative_rmse_change": None, "interval": None,
                "forecast_skill_approved": False}
    # Common scaling preserves every ratio and bounds block sums by case count.
    scale = max(a.max(), b.max())
    scaled_a, scaled_b = a / scale, b / scale
    if ((a > 0) & (scaled_a == 0)).any() or ((b > 0) & (scaled_b == 0)).any():
        raise BenchmarkContractError("Score scaling underflow")
    a, b = scaled_a, scaled_b
    totals_a = np.array([a[ix].sum() for ix in blocks])
    totals_b = np.array([b[ix].sum() for ix in blocks])
    counts = np.array([len(ix) for ix in blocks])
    draw = np.random.default_rng(seed).integers(0, len(blocks), size=(resamples, len(blocks)))
    # Both sides have the same sampled counts; keep the means explicit.
    ma = totals_a[draw].sum(1) / counts[draw].sum(1)
    mb = totals_b[draw].sum(1) / counts[draw].sum(1)
    if (mb == 0).any():
        return {"metric_status": "INSUFFICIENT", "reason": "ZERO_BOOTSTRAP_BASELINE",
                "relative_rmse_change": None, "interval": None,
                "forecast_skill_approved": False}
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        try:
            changes = np.sqrt(ma) / np.sqrt(mb) - 1
            change = float(np.sqrt(a.mean()) / np.sqrt(b.mean()) - 1)
            lo, hi = np.quantile(changes, [alpha/2, 1-alpha/2])
        except FloatingPointError as exc:
            raise BenchmarkContractError("Bootstrap arithmetic failure") from exc
    if not np.isfinite(changes).all() or not np.isfinite([change, lo, hi]).all():
        raise BenchmarkContractError("Nonfinite bootstrap result")
    status = ("IMPROVED" if hi < 0 else "NONINFERIOR" if hi <= margin
              else "REGRESSION" if lo > margin else "INSUFFICIENT")
    return {"metric_status": status, "relative_rmse_change": change,
            "interval": [float(lo), float(hi)], "blocks": len(blocks),
            "resamples": resamples, "alpha": alpha, "margin": margin,
            "forecast_skill_approved": False,
            "scope": "Single metric; requires independent weather, spectra, rain, tides and numerical gates"}


def storage_bytes(start_year: int, end_year: int, hours: int,
                  lat: int, lon: int, channels: int, bytes_per_value: int = 4) -> dict:
    args = (start_year, end_year, hours, lat, lon, channels, bytes_per_value)
    if any(type(v) is not int for v in args) or not 1 <= start_year <= end_year < 9999:
        raise BenchmarkContractError("Integer calendar and dimensions required")
    if hours <= 0 or 24 % hours or min(lat, lon, channels, bytes_per_value) <= 0:
        raise BenchmarkContractError("Invalid cadence/dimensions")
    ntime = (date(end_year + 1, 1, 1)-date(start_year, 1, 1)).days * (24//hours)
    nbytes = ntime*lat*lon*channels*bytes_per_value
    return {"timesteps": ntime, "bytes": nbytes, "TB_decimal": nbytes/1e12,
            "basis": "Uncompressed arrays, NOT measured disk usage or training cost"}
