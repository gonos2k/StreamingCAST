"""Executable manufactured evidence. SciPy is imported only by this verifier."""
from pathlib import Path
import hashlib
import json
import math
import platform
import time
import numpy as np
import torch
from .physics import step_tensor, thermal_step, rollout, GAMMA, RADIATIVE_RATE
from .local import atomic_npz
from .guards import VerificationError, require, finite_gradients, atomic_json, check_boundary


def reference_step(x,p,t,lon,lat,evap):
    """Independent DOP853 integration of the SAME manufactured split physics.
    This is not an independent atmospheric truth or real-data reference.
    """
    from scipy.integrate import solve_ivp
    from scipy.special import expit
    x=np.asarray(x);n=len(x);w=2*np.pi/24;r=RADIATIVE_RATE
    def heat(s,y):
        phase=w*(t+s)+lon
        return -r*y+p[1]*np.cos(phase)+p[2]*np.cos(2*phase)
    ta=solve_ivp(heat,(0,1),x[:,0],method='DOP853',rtol=2e-12,atol=2e-13).y[:,-1]
    qa=x[:,1]+evap;rate=(.02+.28*expit(p[0]))*expit((qa-8*np.exp(.06*ta))/1.5)
    f=2*7.292115e-5*np.sin(lat)*3600
    def wet(s,y):
        a=y.reshape(n,4);sink=rate*a[:,1]
        return np.stack((GAMMA*sink,-sink,f*a[:,3],-f*a[:,2]),-1).ravel()
    initial=np.column_stack((ta,qa,x[:,2:]))
    y=solve_ivp(wet,(0,1),initial.ravel(),method='DOP853',rtol=2e-12,atol=2e-13).y[:,-1].reshape(n,4)
    return y,qa-y[:,1]


def sample(seed,n):
    rng=np.random.default_rng(seed)
    x=np.column_stack((rng.uniform(-3,4,n),rng.uniform(6,14,n),rng.normal(0,5,(n,2))))
    return tuple(torch.from_numpy(a).double() for a in
                 (x,rng.uniform(-np.pi,np.pi,n),rng.uniform(-1.2,1.2,n),rng.uniform(.01,.04,n)))


def derivative_evidence():
    torch.manual_seed(711)
    x,lon,lat,ev=sample(5,5);p=torch.tensor([-.4,.25,.12],dtype=torch.float64);t=x.new_tensor(19.)
    area=torch.arange(1,6,dtype=x.dtype);area/=area.sum()
    def fun(a,b):
        states,rain=rollout(a,b,t,lon,lat,ev,6)
        return torch.cat((states[-1],rain.sum(0)[:,None]),-1)
    vx=torch.randn_like(x)*.1;vp=torch.randn_like(p)*.1
    out,jv=torch.func.jvp(fun,(x,p),(vx,vp));cot=torch.randn_like(out)
    wy=area[:,None]/x.new_tensor([4,10,12,12,1]).square()
    wx=area[:,None]/x.new_tensor([4,10,12,12]).square();wp=x.new_tensor([2,3,4])
    _,pullback=torch.func.vjp(fun,x,p);gx,gp=pullback(wy*cot)
    adjx,adjp=gx/wx,gp/wp
    lhs=(jv*wy*cot).sum();rhs=(vx*wx*adjx).sum()+(vp*wp*adjp).sum()
    fd=(fun(x+1e-5*vx,p+1e-5*vp)-fun(x-1e-5*vx,p-1e-5*vp))/(2e-5)
    objective=lambda a,b: .5*(wy*fun(a,b).square()).sum()
    grads=torch.func.grad(objective,argnums=(0,1))(x,p)
    deriv=(grads[0]*vx).sum()+(grads[1]*vp).sum();base=objective(x,p)
    hs=[.04,.02,.01,.005,.0025];remainders=[]
    for h in hs:
        remainders.append(float(abs(objective(x+h*vx,p+h*vp)-base-h*deriv)))
    orders=[math.log(a/b,2) for a,b in zip(remainders,remainders[1:])]
    gc=torch.autograd.gradcheck(lambda a,b: torch.cat(step_tensor(a,b,t,lon,lat,ev)[0:1],-1),
                               (x.requires_grad_(),p.requires_grad_()),eps=1e-6,atol=1e-6,rtol=1e-5)
    result={'weighted_adjoint_relative_error':float(abs(lhs-rhs)/max(abs(lhs),abs(rhs),1e-15)),
            'jvp_central_difference_relative_error':float(torch.linalg.vector_norm(jv-fd)/torch.linalg.vector_norm(jv)),
            'taylor_steps':hs,'taylor_remainders':remainders,'taylor_orders':orders,'gradcheck':gc}
    require(result['weighted_adjoint_relative_error'] < 1e-10, 'Weighted adjoint mismatch')
    require(result['jvp_central_difference_relative_error'] < 2e-7, 'JVP mismatch')
    require(gc and min(orders) > 1.9 and max(orders) < 2.1, 'Taylor/gradcheck failed')
    return result


def tide_evidence():
    t=torch.tensor(31.,dtype=torch.float64);lon=torch.linspace(-2,2,7,dtype=t.dtype)
    amps=torch.tensor([.25,.12],dtype=t.dtype)
    def exact(time):
        ans=torch.zeros_like(lon)
        for j in (1,2):
            w=2*math.pi*j/24;ph=w*time+j*lon;r=RADIATIVE_RATE
            ans+=amps[j-1]*(r*torch.cos(ph)+w*torch.sin(ph))/(r*r+w*w)
        return ans
    x=exact(t);trajectory=[]
    for k in range(240):
        x=thermal_step(x,amps,t+k,lon);trajectory.append(x)
    pred=torch.stack(trajectory);truth=torch.stack([exact(t+k+1) for k in range(240)])
    times=np.arange(32,272);cols=[np.ones(240)]
    for j in (1,2):
        cols.extend([np.cos(j*2*np.pi*times/24),np.sin(j*2*np.pi*times/24)])
    design=np.stack(cols,-1);cp=np.linalg.lstsq(design,pred.numpy(),rcond=None)[0]
    ct=np.linalg.lstsq(design,truth.numpy(),rcond=None)[0];modes={}
    for j,period in ((1,24),(2,12)):
        a,b=cp[2*j-1:2*j+1];u,v=ct[2*j-1:2*j+1]
        phase=np.angle(np.exp(1j*(np.arctan2(b,a)-np.arctan2(v,u))))
        modes[str(period)]={'max_amplitude_ratio_error':float(np.max(abs(np.hypot(a,b)/np.hypot(u,v)-1))),
                            'max_peak_time_error_minutes':float(np.max(abs(phase))*period*60/(2*np.pi))}
    err=float((pred-truth).abs().max());require(err < 1e-11, 'Tidal response failed')
    # A daily-endpoint score can miss a full hourly error.
    e=np.sin(2*np.pi*np.arange(1,241)/24)+.5*np.sin(2*np.pi*np.arange(1,241)/12)
    return {'max_absolute_error_240h':err,'modes':modes,
            'endpoint_counterexample':{'hourly_rmse':float(np.sqrt(np.mean(e**2))),
                                       'daily_endpoint_rmse':float(np.sqrt(np.mean(e[23::24]**2)))}}


def learning_evidence(outdir):
    x,lon,lat,ev=sample(121,96);truthp=x.new_tensor([-.4,.25,.12]);t=x.new_tensor(7.)
    target,rain=reference_step(x.numpy(),truthp.numpy(),7.,lon.numpy(),lat.numpy(),ev.numpy())
    target=torch.from_numpy(target);rain=torch.from_numpy(rain)
    xn,ln,an,en=sample(812,12);tn=x.new_tensor(37.);checks=[]
    for seed in (0,1,2):
        torch.manual_seed(seed)
        p=torch.nn.Parameter(torch.randn(3,dtype=x.dtype)*.2)
        def loss():
            y,r=step_tensor(x,p,t,lon,lat,ev)
            return ((y-target)/x.new_tensor([4,10,12,12])).square().mean()+(r-rain).square().mean()
        first=float(loss().detach());opt=torch.optim.LBFGS([p],lr=1,max_iter=100,
                         tolerance_grad=1e-12,tolerance_change=1e-15,line_search_fn='strong_wolfe')
        calls=[0]
        def closure():
            opt.zero_grad();v=loss()
            require(torch.isfinite(v), 'Nonfinite training loss')
            v.backward();finite_gradients((p,));calls[0]+=1;return v
        opt.step(closure)
        check_boundary(x, p, t, lon, lat, ev)
        with torch.no_grad():
            states,pr=rollout(xn,p,tn,ln,an,en,240)
            # Held-out reference uses independently coded, adaptive SciPy solves each hour.
            ref=xn.numpy().copy();rr=[];xs=[ref]
            for k in range(240):
                ref,rp=reference_step(ref,truthp.numpy(),37+k,ln.numpy(),an.numpy(),en.numpy())
                rr.append(rp);xs.append(ref)
            targetall=torch.from_numpy(np.stack(xs));prref=torch.from_numpy(np.stack(rr))
            error=(states[-1]-targetall[-1]).square().mean(0).sqrt()
            water=(states[-1,:,1]+pr.sum(0)-xn[:,1]-240*en).abs().max()
            heat=[]
            for k in range(240):
                ta=thermal_step(states[k,:,0],p[1:],tn+k,ln)
                heat.append(((states[k+1,:,0]+GAMMA*states[k+1,:,1])-
                             (ta+GAMMA*(states[k,:,1]+en))).abs().max())
            # A fresh persisted state is resumed using the original absolute clock.
            a,ar=rollout(xn,p,tn,ln,an,en,137)
            path=Path(outdir)/f'restart_seed{seed}.npz'
            atomic_npz(path,state=a[-1].numpy(),parameters=p.detach().numpy(),hour=np.array(174.))
            with np.load(path,allow_pickle=False) as z:
                b,br=rollout(torch.from_numpy(z['state']),torch.from_numpy(z['parameters']),
                             torch.tensor(float(z['hour']),dtype=x.dtype),ln,an,en,103)
            restart=torch.equal(states,torch.cat((a,b[1:]))) and torch.equal(pr,torch.cat((ar,br)))
        item={'seed':seed,'parameters':p.detach().tolist(),'initial_loss':first,'final_loss':float(loss().detach()),
              'optimizer_evaluations':calls[0],'test_state_rmse_240h':error.tolist(),
              'test_accumulated_rain_rmse_mm':float(((pr.sum(0)-prref.sum(0))**2).mean().sqrt()),
              'max_column_water_residual_mm':float(water),'max_step_heat_residual_K':float(torch.stack(heat).max()),
              'restart_bitwise':restart}
        require(item['final_loss'] < first*1e-5, 'Learning loss did not meet threshold')
        require(max(item['test_state_rmse_240h']) < 1e-3 and item['test_accumulated_rain_rmse_mm'] < 1e-3, 'Held-out forecast threshold failed')
        require(water < 1e-10 and restart, 'Budget/restart failed')
        checks.append(item)
    return {'parameters':3,'train_pairs':96,'test_cases':12,'horizon_hours':240,
            'truth_parameters':truthp.tolist(),'models':checks,
            'scope':'manufactured split column; same equations, independent ODE integration; not weather skill'}


def _verify(out):
    torch.set_num_threads(1);start=time.perf_counter();out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    result={'scope':'P0 manufactured differentiability/learning evidence, not operational weather',
            'environment':{'python':platform.python_version(),'torch':torch.__version__,
                           'numpy':np.__version__,'device':'cpu','dtype':'float64'},
            'derivatives':derivative_evidence(),'tides':tide_evidence(),
            'learning':learning_evidence(out.parent),'seconds':time.perf_counter()-start,
            'real_data_processed':False,'LAYA_executed':False,'B200_executed':False,
            'previous_D83_240h_failure_resolved':False}
    result['status'] = 'PASS'
    atomic_json(out, result)
    return result



def verify(out):
    """Write explicit FAIL and exit nonzero through the CLI, including under -O."""
    try:
        return _verify(out)
    except Exception as error:
        atomic_json(out, {'status': 'FAIL', 'error_type': type(error).__name__,
                          'message': str(error), 'weather_skill_verified': False})
        if isinstance(error, VerificationError):
            raise
        raise VerificationError('Verification did not complete') from error
