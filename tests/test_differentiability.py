import math
import numpy as np
import pytest
import torch
from streamingcast.physics import step_tensor,thermal_step,rollout,validate_inputs,GAMMA
from streamingcast.verification import sample,derivative_evidence,tide_evidence,reference_step

torch.set_num_threads(1)


def inputs():
    x,lon,lat,ev=sample(4,6);p=x.new_tensor([-.4,.25,.12]);t=x.new_tensor(19.)
    return x,p,t,lon,lat,ev


def test_reference_independent_integrator():
    x,p,t,lon,lat,ev=inputs();out,rain=step_tensor(x,p,t,lon,lat,ev)
    y,r=reference_step(x.numpy(),p.numpy(),float(t),lon.numpy(),lat.numpy(),ev.numpy())
    assert np.max(abs(out.numpy()-y))<1e-9
    assert np.max(abs(rain.numpy()-r))<1e-9


def test_derivative_suite():
    d=derivative_evidence();assert min(d['taylor_orders'])>1.9


def test_tides_and_endpoint_counterexample():
    d=tide_evidence();assert d['endpoint_counterexample']['daily_endpoint_rmse']<1e-12
    assert d['endpoint_counterexample']['hourly_rmse']>.7


def test_water_heat_and_kinetic_invariants():
    x,p,t,lon,lat,ev=inputs();y,r=step_tensor(x,p,t,lon,lat,ev)
    ta=thermal_step(x[:,0],p[1:],t,lon)
    torch.testing.assert_close(y[:,1]+r,x[:,1]+ev,rtol=0,atol=5e-14)
    torch.testing.assert_close(y[:,0]+GAMMA*y[:,1],ta+GAMMA*(x[:,1]+ev),rtol=0,atol=5e-14)
    torch.testing.assert_close(y[:,2:].square().sum(-1),x[:,2:].square().sum(-1),rtol=1e-13,atol=1e-13)
    assert (r>=0).all() and (y[:,1]>=0).all()


def test_commit_once_and_restart():
    x,p,t,lon,lat,ev=inputs();a,r=rollout(x,p,t,lon,lat,ev,24)
    b,s=rollout(x,p,t,lon,lat,ev,13);c,u=rollout(b[-1],p,t+13,lon,lat,ev,11)
    assert torch.equal(a,torch.cat((b,c[1:])))
    assert torch.equal(r,torch.cat((s,u)))
    assert r.shape==(24,6)


def test_clock_is_absolute_and_longitude_periodic():
    x,p,t,lon,lat,ev=inputs()
    a=step_tensor(x,p,t,lon,lat,ev)[0]
    torch.testing.assert_close(a,step_tensor(x,p,t+24,lon,lat,ev)[0],rtol=0,atol=1e-14)
    torch.testing.assert_close(a,step_tensor(x,p,t,lon+2*math.pi,lat,ev)[0],rtol=0,atol=1e-14)
    assert not torch.allclose(a,step_tensor(x,p,t*0,lon,lat,ev)[0])


def test_rollout_gradients_are_not_detached():
    x,p,t,lon,lat,ev=inputs();x.requires_grad_();p.requires_grad_()
    ys,rs=rollout(x,p,t,lon,lat,ev,12)
    gs=torch.autograd.grad(ys[-1].square().mean()+rs.square().mean(),(x,p))
    assert all(torch.isfinite(g).all() and g.abs().sum()>0 for g in gs)


def test_branchless_moisture_gradient():
    x,p,t,lon,lat,ev=inputs();p.requires_grad_()
    _,r=step_tensor(x,p,t,lon,lat,ev)
    g=torch.autograd.grad(r.sum(),p)[0]
    assert torch.isfinite(g).all() and abs(g[0])>1e-8


@pytest.mark.parametrize('hours',[0,-1,True,241,1.5])
def test_invalid_horizon(hours):
    with pytest.raises(ValueError):rollout(*inputs(),hours)


@pytest.mark.parametrize('fault',['negative_q','nan','dtype','parameters','latitude','d83'])
def test_toy_boundary(fault):
    x,p,t,lon,lat,ev=inputs()
    if fault=='negative_q':x[0,1]=-1
    if fault=='nan':x[0,0]=float('nan')
    if fault=='dtype':p=p.float()
    if fault=='parameters':p=p[:2]
    if fault=='latitude':lat[0]=90
    if fault=='d83':x=torch.ones(6,83,dtype=x.dtype)
    with pytest.raises(ValueError):validate_inputs(x,p,lon,lat,ev)
