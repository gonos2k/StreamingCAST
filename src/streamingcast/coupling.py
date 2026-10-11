"""Explicit SI/native/observation chain for FOUR manufactured column variables.
This is not an adapter to KIM/WRF/IFS or a D83 spatial/vertical remapper.
SI order: T[K], q[kg/kg], u/v[m/s]. Native q is g/kg, theta=T-280K.
Rain uses the fixed toy column mass 1000 kg/m2; its output unit is mm.
"""
import torch
from .physics import rollout_substeps


def encode_si(state):
    offset = state.new_tensor([280., 0., 0., 0.])
    scale = state.new_tensor([1., 1000., 1., 1.])
    return (state-offset)*scale


def decode_si(state):
    scale = state.new_tensor([1., 1000., 1., 1.])
    offset = state.new_tensor([280., 0., 0., 0.])
    return state/scale+offset


def validate_observation_weights(weights, points):
    # Boundary-only validation. The operator below stays a pure tensor graph.
    if weights.ndim != 2 or weights.shape[1] != points or weights.shape[0] == 0:
        raise ValueError('Observation weights must be nonempty [observation,point]')
    if not weights.is_floating_point() or not torch.isfinite(weights).all() or (weights < 0).any():
        raise ValueError('Finite nonnegative observation weights required')
    if not torch.allclose(weights.sum(1), torch.ones_like(weights[:, 0]), rtol=0, atol=1e-6):
        raise ValueError('Observation weights must sum to one')


def forecast_observations(state_si, parameters, hour, longitude, latitude,
                          evaporation_kgkg_per_hour, weights, hours=6, *, substeps=4):
    """E -> native M -> P -> H, including 1h rain accumulated before observation.
    No data selection, clipping, input validation or detach in this function.
    Weights are a prescribed linear point operator, NOT validated real geometry.
    """
    states, rain = rollout_substeps(encode_si(state_si), parameters, hour,
                                  longitude, latitude, evaporation_kgkg_per_hour*1000,
                                  hours, substeps=substeps)
    features = torch.cat((decode_si(states[-1]), rain.sum(0)[:, None]), -1)
    return weights @ features
