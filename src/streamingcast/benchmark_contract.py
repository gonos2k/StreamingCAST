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


def validate_catalog(catalog: dict) -> dict:
    if catalog.get("schema") != "streamingcast-external-benchmark-catalog-v1":
        raise BenchmarkContractError("Unknown catalog schema")
    seen = set()
    counts: dict[str, int] = {}
    for record in catalog["records"]:
        source = catalog["sources"].get(record["source_id"])
        if source is None or not source.get("url") or not source.get("locator"):
            raise BenchmarkContractError("A primary source and exact location are required")
        if source.get("raw_forecasts_recomputed_here") is not False:
            raise BenchmarkContractError("This imported catalog must not assert local re-evaluation")
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
        if record["value"] is not None:
            raise BenchmarkContractError("Missing results must stay null, not zero")
    return {"records": len(seen), "counts": counts,
            "sources": len(catalog["sources"]), "forecast_skill_approved": False}


# Model IDs can differ, but every evaluation condition below must match.
PROTOCOL_FIELDS = (
    "protocol_id", "variable", "units", "lead_hours", "temporal_statistic",
    "forecast_statistic", "ensemble_members", "init_sample_sha256",
    "target_sha256", "initial_analysis", "grid_sha256", "mask_sha256",
    "weights_sha256", "climatology_id", "aggregation",
)
HASH_FIELDS = ("init_sample_sha256", "target_sha256", "grid_sha256",
               "mask_sha256", "weights_sha256", "model_sha256")


def require_matched_local(candidate: dict, baseline: dict) -> None:
    for item in (candidate, baseline):
        if item.get("evidence_class") != "local_recomputed":
            raise BenchmarkContractError("Paper tables/unknown lineage cannot approve local skill")
        if item.get("holdout_independence_checked") is not True:
            raise BenchmarkContractError("Pretraining and test overlap must be checked")
        for key in PROTOCOL_FIELDS:
            value = item.get(key)
            if value is None or value == "" or value == "unknown":
                raise BenchmarkContractError(f"Missing evaluation field: {key}")
        for key in HASH_FIELDS:
            if not isinstance(item.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", item[key]):
                raise BenchmarkContractError(f"SHA-256 required: {key}")
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
    denom = np.sum(m * w, axis=axes)
    if (denom <= 0).any():
        raise BenchmarkContractError("Empty initialization in fixed verification domain")
    with np.errstate(over="raise", invalid="raise"):
        try:
            diff = np.where(m, p, 0.0) - np.where(m, y, 0.0)
            out = np.sum(diff * diff * w, axis=axes) / denom
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
    a, b = np.asarray(candidate_mse, float), np.asarray(baseline_mse, float)
    ids = np.asarray(block_ids)
    if a.ndim != 1 or a.shape != b.shape or ids.shape != a.shape or not a.size:
        raise BenchmarkContractError("Matching nonempty case scores and block IDs required")
    if not np.isfinite(a).all() or not np.isfinite(b).all() or (a < 0).any() or (b <= 0).any():
        raise BenchmarkContractError("Finite scores required; baseline MSE must be positive")
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
    totals_a = np.array([a[ix].sum() for ix in blocks])
    totals_b = np.array([b[ix].sum() for ix in blocks])
    counts = np.array([len(ix) for ix in blocks])
    draw = np.random.default_rng(seed).integers(0, len(blocks), size=(resamples, len(blocks)))
    # Both sides have the same sampled counts; keep the means explicit.
    ma = totals_a[draw].sum(1) / counts[draw].sum(1)
    mb = totals_b[draw].sum(1) / counts[draw].sum(1)
    changes = np.sqrt(ma / mb) - 1
    lo, hi = np.quantile(changes, [alpha/2, 1-alpha/2])
    status = ("IMPROVED" if hi < 0 else "NONINFERIOR" if hi <= margin
              else "REGRESSION" if lo > margin else "INSUFFICIENT")
    return {"metric_status": status, "relative_rmse_change": float(np.sqrt(a.mean()/b.mean())-1),
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
