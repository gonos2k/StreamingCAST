"""Pure tensor toy column. A differentiable NWP boundary, NOT an NWP model.
State: theta [K anomaly from 280K], q [g/kg], u/v [m/s]. Column mass 1000 kg/m2.
Time is hours; latitude/longitude are radians. Rain is mm per interval.
No data selection, I/O, detach, clipping, scalar extraction or halting in this core.
"""
from typing import Protocol
import math
import torch
from torch import Tensor

GAMMA=2.5  # K per g/kg, manufactured latent-heat conversion
RADIATIVE_RATE=1/48  # h^-1; fixed in this verification problem


class ForecastStep(Protocol):
    def __call__(self, state: Tensor, parameters: Tensor, hour: Tensor,
                 longitude: Tensor, latitude: Tensor, evaporation: Tensor
                 ) -> tuple[Tensor,Tensor]: ...


def thermal_step(theta, amplitudes, hour, longitude):
    """Exact linear damped response to mean-solar S1/S2 over one hour."""
    d=math.exp(-RADIATIVE_RATE)
    result=d*theta
    for j in (1,2):
        w=2*math.pi*j/24
        phase=w*torch.remainder(hour,24)+j*longitude
        # Re[e^(i phase) (e^(iw)-d)/(rate+iw)] -- all real arithmetic.
        a,b=math.cos(w)-d,math.sin(w)
        re=(a*RADIATIVE_RATE+b*w)/(RADIATIVE_RATE**2+w*w)
        im=(b*RADIATIVE_RATE-a*w)/(RADIATIVE_RATE**2+w*w)
        result=result+amplitudes[j-1]*(re*torch.cos(phase)-im*torch.sin(phase))
    return result


def step_tensor(state, parameters, hour, longitude, latitude, evaporation):
    theta,q,u,v=state.unbind(-1)
    ta=thermal_step(theta,parameters[1:],hour,longitude)
    qa=q+evaporation
    beta=0.02+0.28*torch.sigmoid(parameters[0])
    qsat=8*torch.exp(0.06*ta)
    hazard=beta*torch.sigmoid((qa-qsat)/1.5)
    rain=-qa*torch.expm1(-hazard)
    angle=2*7.292115e-5*torch.sin(latitude)*3600
    c,s=torch.cos(angle),torch.sin(angle)
    nxt=torch.stack((ta+GAMMA*rain,qa-rain,c*u+s*v,-s*u+c*v),-1)
    return nxt,rain


def validate_inputs(state, parameters, longitude, latitude, evaporation):
    if state.ndim!=2 or state.shape[-1]!=4 or state.numel()==0:
        raise ValueError("Toy column needs nonempty [point,4]; D83 is not this model")
    if parameters.shape!=(3,): raise ValueError("Three toy parameters required")
    for a in (state,parameters,longitude,latitude,evaporation):
        if a.dtype!=state.dtype or a.device!=state.device or not torch.isfinite(a).all():
            raise ValueError("Finite matching dtype/device required")
    if state.dtype not in (torch.float32,torch.float64): raise ValueError("FP32/FP64 required")
    if any(a.shape!=(state.shape[0],) for a in (longitude,latitude,evaporation)):
        raise ValueError("Coordinate/source shape mismatch")
    if (state[:,1]<0).any() or (evaporation<0).any(): raise ValueError("Negative moisture/source")
    if (latitude.abs()>math.pi/2).any(): raise ValueError("Latitude must be radians in range")
    if (state[:,0].abs()>50).any() or (state[:,1]>30).any() or (parameters.abs()>10).any():
        raise ValueError("Outside declared toy domain, not meteorologically impossible")


def rollout(state,parameters,hour,longitude,latitude,evaporation,hours):
    """Differentiable free rollout; initial state included. No teacher resets."""
    if type(hours) is not int or not 1<=hours<=240: raise ValueError("hours must be 1..240")
    states=[state];rain=[]
    for k in range(hours):
        state,p=step_tensor(state,parameters,hour+k,longitude,latitude,evaporation)
        states.append(state);rain.append(p)
    return torch.stack(states),torch.stack(rain)



def check_substeps(substeps):
    if type(substeps) is not int or substeps not in (1, 2, 4, 8, 16):
        raise ValueError("substeps must be one of 1,2,4,8,16")


def step_interval(state, parameters, hour, longitude, latitude, evaporation, dt):
    """Frozen-hazard split over dt hours, E is g/kg/hour (NOT interval total).
    First-order approximation to simultaneous moist/thermal coupling as dt -> 0.
    dt=1 dispatches the original kernel verbatim; no silent model replacement.
    """
    if type(dt) not in (int, float) or not math.isfinite(dt) or not 0 < dt <= 1:
        raise ValueError("dt must be finite and in (0,1]")
    if dt == 1:
        return step_tensor(state, parameters, hour, longitude, latitude, evaporation)
    theta, q, u, v = state.unbind(-1)
    d = math.exp(-RADIATIVE_RATE * dt)
    ta = d * theta
    for j in (1, 2):
        w = 2 * math.pi * j / 24
        phase = w * torch.remainder(hour, 24) + j * longitude
        a, b = math.cos(w * dt) - d, math.sin(w * dt)
        re = (a * RADIATIVE_RATE + b * w) / (RADIATIVE_RATE**2 + w*w)
        im = (b * RADIATIVE_RATE - a * w) / (RADIATIVE_RATE**2 + w*w)
        ta = ta + parameters[j] * (re * torch.cos(phase) - im * torch.sin(phase))
    qa = q + dt * evaporation
    beta = 0.02 + 0.28 * torch.sigmoid(parameters[0])
    hazard = beta * torch.sigmoid((qa - 8 * torch.exp(0.06 * ta)) / 1.5)
    rain = -qa * torch.expm1(-dt * hazard)
    angle = 2 * 7.292115e-5 * torch.sin(latitude) * 3600 * dt
    c, s = torch.cos(angle), torch.sin(angle)
    return torch.stack((ta + GAMMA*rain, qa-rain, c*u+s*v, -s*u+c*v), -1), rain


def step_substeps(state, parameters, hour, longitude, latitude, evaporation, *, substeps=1):
    check_substeps(substeps)
    if substeps == 1:
        return step_tensor(state, parameters, hour, longitude, latitude, evaporation)
    rain = torch.zeros_like(state[..., 1])
    dt = 1.0 / substeps
    for j in range(substeps):
        state, part = step_interval(state, parameters, hour+j*dt,
                                    longitude, latitude, evaporation, dt)
        rain = rain + part
    return state, rain


def rollout_substeps(state, parameters, hour, longitude, latitude, evaporation,
                     hours, *, substeps=1):
    """Pure differentiable hourly output; internal dt and rainfall are explicit."""
    if type(hours) is not int or not 1 <= hours <= 240:
        raise ValueError("hours must be 1..240")
    check_substeps(substeps)
    if substeps == 1:
        return rollout(state, parameters, hour, longitude, latitude, evaporation, hours)
    states, rain = [state], []
    for k in range(hours):
        state, part = step_substeps(state, parameters, hour+k, longitude,
                                   latitude, evaporation, substeps=substeps)
        states.append(state)
        rain.append(part)
    return torch.stack(states), torch.stack(rain)
