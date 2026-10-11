"""Checked boundary, never called inside torch.func transforms of the pure core.
Limits define this manufactured problem, not what is possible in real weather.
"""
import json
import os
from pathlib import Path
import tempfile
import torch
from .physics import validate_inputs, step_interval, check_substeps


class VerificationError(RuntimeError):
    """An explicit verification failure; remains active under python -O."""


def require(condition, message):
    if not bool(condition):
        raise VerificationError(message)


def atomic_json(path, result):
    # Serialize before replacing an earlier report. No NaN/Infinity allowed.
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".report-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def finite_gradients(parameters):
    parameters = tuple(parameters)
    require(bool(parameters), "No parameters supplied for gradient validation")
    for parameter in parameters:
        require(parameter.grad is not None, "Missing required parameter gradient")
        require(torch.isfinite(parameter.grad).all(), "Nonfinite gradient; abort before update")


def check_boundary(state, parameters, hour, longitude, latitude, evaporation):
    validate_inputs(state, parameters, longitude, latitude, evaporation)
    if not isinstance(hour, torch.Tensor) or hour.ndim != 0:
        raise ValueError("Scalar tensor hour required")
    if hour.dtype != state.dtype or hour.device != state.device or not torch.isfinite(hour):
        raise ValueError("Finite matching clock dtype/device required")
    if hour.abs() > 1_000_000 or hour + 1 == hour:
        raise ValueError("Outside tested clock domain or unresolved one-hour increment")
    if (evaporation > 0.5).any() or (state[:, 2:].abs() > 300).any():
        raise ValueError("Outside manufactured source/wind domain")
    if (longitude.abs() > 2 * torch.pi).any():
        raise ValueError("Longitude must be radians within +/-2pi")


def checked_rollout(state, parameters, hour, longitude, latitude, evaporation,
                    hours, *, substeps=1):
    """Validate before/after every substep; publish hourly state/rain only.
    Checks do not detach outputs, but their discrete decisions are NOT differentiated.
    Use physics.rollout_substeps for JVP/VJP after validating the primal inputs.
    """
    if type(hours) is not int or not 1 <= hours <= 240:
        raise ValueError("hours must be 1..240")
    check_substeps(substeps)
    check_boundary(state, parameters, hour, longitude, latitude, evaporation)
    if hour != hour.round():
        raise ValueError("Outer forecast initialization must be a UTC whole hour")
    states, rain = [state], []
    cumulative = torch.zeros_like(state[:, 1])
    dt = 1.0 / substeps
    for k in range(hours):
        hourly = torch.zeros_like(cumulative)
        for j in range(substeps):
            clock = hour + k + j * dt
            check_boundary(state, parameters, clock, longitude, latitude, evaporation)
            candidate, interval_rain = step_interval(
                state, parameters, clock, longitude, latitude, evaporation, dt)
            require(candidate.shape == state.shape, "State shape changed")
            require(interval_rain.shape == cumulative.shape, "Rain shape changed")
            require(interval_rain.dtype == state.dtype and interval_rain.device == state.device,
                    "Rain dtype/device changed")
            require(torch.isfinite(candidate).all() and torch.isfinite(interval_rain).all(),
                    "Nonfinite candidate; no commit")
            require((interval_rain >= 0).all(), "Negative rain; no commit")
            check_boundary(candidate, parameters, clock + dt, longitude, latitude, evaporation)
            defect = candidate[:, 1] + interval_rain - state[:, 1] - dt * evaporation
            tol = 5e-5 if state.dtype == torch.float32 else 1e-11
            require(defect.abs().max() <= tol, "Toy water identity failed")
            pending = hourly + interval_rain
            require(torch.isfinite(pending).all(), "Hourly accumulation overflow")
            state, hourly = candidate, pending
        pending = cumulative + hourly
        require(torch.isfinite(pending).all(), "Forecast accumulation overflow")
        cumulative = pending
        states.append(state)
        rain.append(hourly)
    return torch.stack(states), torch.stack(rain)
