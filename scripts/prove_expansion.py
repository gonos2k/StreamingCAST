"""Manufactured E-M-P-H differentiability and temporal refinement evidence.
No real weather, external NWP, LAYA or GPU. Run from the repository root.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.special import expit
import torch
from streamingcast.physics import rollout, rollout_substeps, thermal_step
from streamingcast.guards import require, atomic_json, checked_rollout, VerificationError
from streamingcast.coupling import encode_si,decode_si,forecast_observations,validate_observation_weights
from streamingcast.verification import sample


def chain_evidence():
    torch.manual_seed(207)
    x,lon,lat,ev=sample(147,5)
    si=decode_si(x);p=x.new_tensor([-.4,.25,.12]);t=x.new_tensor(19.)
    weights=x.new_tensor([[.2,.3,.1,.2,.2],[.5,.1,.2,.1,.1],[.05,.1,.15,.3,.4]])
    validate_observation_weights(weights,len(x))
    fun=lambda a,b:forecast_observations(a,b,t,lon,lat,ev/1000,weights,6,substeps=4)
    sx=x.new_tensor([4.,.01,12.,12.]);sy=x.new_tensor([4.,.01,12.,12.,1.])
    vx=torch.randn_like(si)*sx*.03;vp=torch.randn_like(p)*.03
    y,jv=torch.func.jvp(fun,(si,p),(vx,vp));h=1e-4
    fd=(fun(si+h*vx,p+h*vp)-fun(si-h*vx,p-h*vp))/(2*h)
    jerr=float(torch.linalg.vector_norm((jv-fd)/sy)/torch.linalg.vector_norm(jv/sy))
    ax=torch.arange(1.,6.,dtype=x.dtype);ax/=ax.sum()
    ay=x.new_tensor([.2,.3,.5]);wx=ax[:,None]/sx.square();wy=ay[:,None]/sy.square();wp=x.new_tensor([.25,.5,1.])
    cot=torch.randn_like(y)*sy
    _,pullback=torch.func.vjp(fun,si,p);gx,gp=pullback(wy*cot)
    lhs=(jv*wy*cot).sum();rhs=(vx*wx*(gx/wx)).sum()+(vp*wp*(gp/wp)).sum()
    aerr=float(abs(lhs-rhs)/max(abs(lhs),abs(rhs),1e-14))
    center=y.new_tensor([280.,0.,0.,0.,0.])
    objective=lambda a,b:.5*(wy*(fun(a,b)-center).square()).sum()
    g=torch.func.grad(objective,argnums=(0,1))(si,p)
    derivative=(g[0]*vx).sum()+(g[1]*vp).sum();base=objective(si,p)
    hs=[.08,.04,.02,.01,.005]
    remainders=[float(abs(objective(si+k*vx,p+k*vp)-base-k*derivative)) for k in hs]
    orders=[math.log(a/b,2) for a,b in zip(remainders,remainders[1:])]
    require(jerr<2e-7 and aerr<1e-10,'Full-chain derivative mismatch')
    require(all(1.8<o<2.2 for o in orders),'Full-chain Taylor failed')
    return {'scope':'SI temperature/q units -> four-variable native split -> SI state + cumulative mm -> prescribed linear point observation',
            'hours':6,'substeps':4,'jvp_fd_scaled_relative':jerr,'weighted_adjoint_relative':aerr,
            'taylor_h':hs,'taylor_remainders':remainders,'taylor_orders':orders,
            'forecast_output_shape':list(y.shape),'actual_NWP_or_real_geometry':False}


def refinement_evidence():
    x=torch.tensor([[0.,12.,3.,2.]],dtype=torch.float64);p=x.new_tensor([-.4,.25,.12]);v=x.new_tensor([.1,-.2,.15])
    t=x.new_tensor(19.);lon=x.new_tensor([.7]);lat=x.new_tensor([.65]);ev=x.new_tensor([.03]);H=24
    def reference(par,tolerance=2e-12):
        def rhs(ti,a):
            theta,q,u,vv=a;w=2*np.pi/24
            sink=(.02+.28*expit(par[0]))*expit((q-8*np.exp(.06*theta))/1.5)*q
            f=2*7.292115e-5*np.sin(float(lat[0]))*3600
            return [-theta/48+par[1]*np.cos(w*ti+float(lon[0]))+par[2]*np.cos(2*w*ti+2*float(lon[0]))+2.5*sink,
                    float(ev[0])-sink,f*vv,-f*u]
        sol=solve_ivp(rhs,(19,19+H),x.numpy().ravel(),method='DOP853',rtol=tolerance,atol=tolerance/10)
        require(sol.success and np.isfinite(sol.y).all(),'Continuous reference failed')
        return sol.y[:,-1]
    truth=reference(p.numpy());eps=1e-4
    fd=lambda h:(reference((p+h*v).numpy())-reference((p-h*v).numpy()))/(2*h)
    tangent=fd(eps);tangent_half=fd(eps/2)
    rows=[]
    for count in (1,2,4,8,16):
        fun=lambda par:rollout_substeps(x,par,t,lon,lat,ev,H,substeps=count)[0][-1,0]
        state,jv=torch.func.jvp(fun,(p,),(v,))
        delta=state.numpy()-truth;derr=float(np.linalg.norm(jv.numpy()-tangent)/np.linalg.norm(tangent))
        timing=[]
        with torch.no_grad():
            fun(p)
            for _ in range(5):
                start=time.perf_counter();fun(p);timing.append(time.perf_counter()-start)
        rows.append({'substeps':count,'dt_hours':1/count,'theta_error_K':float(delta[0]),
                     'q_error_gkg':float(delta[1]),'native_coordinate_l2_error':float(np.linalg.norm(delta)),
                     'parameter_sensitivity_relative_error':derr,'cpu_24h_median_seconds':statistics.median(timing)})
    for a,b in zip(rows,rows[1:]):
        a['observed_order']=math.log(a['native_coordinate_l2_error']/b['native_coordinate_l2_error'],2)
    require(all(b['native_coordinate_l2_error']<a['native_coordinate_l2_error'] for a,b in zip(rows,rows[1:])),
            'Refinement did not reduce state error in this declared case')
    require(all(b['parameter_sensitivity_relative_error']<a['parameter_sensitivity_relative_error'] for a,b in zip(rows,rows[1:])),
            'Refinement did not reduce sensitivity discrepancy')
    return {'reference':'simultaneous coupled ODE extension, NOT original split truth',
            'scope':'one manufactured initial state, fixed parameters and one parameter direction; not a global convergence theorem',
            'native_l2_warning':'mixed units; used only for this fixed-coordinate convergence ratio',
            'reference_tolerance_change':float(np.max(abs(reference(p.numpy(),5e-13)-truth))),
            'reference_fd_halving_change':float(np.linalg.norm(tangent_half-tangent)/np.linalg.norm(tangent)),
            'rows':rows}


def long_rollout_evidence():
    x,lon,lat,ev=sample(42,3);p=x.new_tensor([-.4,.25,.12]);t=x.new_tensor(500019.)
    a,r=checked_rollout(x,p,t,lon,lat,ev,240,substeps=4)
    b,s=checked_rollout(x,p,t,lon,lat,ev,137,substeps=4)
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'restart.npz'
        np.savez(path,state=b[-1].numpy(),hour=np.array(float(t)+137),parameters=p.numpy())
        with np.load(path,allow_pickle=False) as z:
            c,u=checked_rollout(torch.from_numpy(z['state']),torch.from_numpy(z['parameters']),
                                x.new_tensor(float(z['hour'])),lon,lat,ev,103,substeps=4)
    same=torch.equal(a,torch.cat((b,c[1:]))) and torch.equal(r,torch.cat((s,u)))
    water=float((a[-1,:,1]+r.sum(0)-x[:,1]-240*ev).abs().max())
    require(same and water<1e-10,'Restart/water contract failed')
    # Dry forced thermal response: exact relation, not learned tide skill.
    dry=x.clone();dry[:,1]=0;ev0=ev*0
    means=[]
    for count in (1,4,16):
        z=rollout_substeps(dry,p,t,lon,lat,ev0,240,substeps=count)[0]
        ref=dry[:,0];values=[ref]
        for k in range(240):ref=thermal_step(ref,p[1:],t+k,lon);values.append(ref)
        err=float((z[:,:,0]-torch.stack(values)).abs().max())
        require(err<1e-10,'Substep clock/tidal composition failed')
        means.append({'substeps':count,'max_dry_thermal_difference_K':err})
    # Explicitly retain a known scientific limitation.
    dr=x.new_tensor([[0.,4.,0.,0.]]);zero=x.new_zeros(1)
    _,rain=rollout(dr,x.new_tensor([-.4,0.,0.]),x.new_tensor(0.),zero,zero,zero,240)
    return {'hours':240,'substeps':4,'restart_137_103_bitwise':same,
            'column_water_residual_mm':water,'dry_tidal_composition':means,
            'known_unresolved_subsaturated_240h_rain_mm':float(rain.sum()),
            'real_weather_skill_verified':False}


def run(out):
    torch.set_num_threads(1);start=time.perf_counter()
    try:
        report={'status':'PASS','scope':'manufactured code expansion, not actual NWP',
                'environment':{'python':platform.python_version(),'torch':torch.__version__,
                'numpy':np.__version__,'scipy':scipy.__version__,'device':'cpu','dtype':'float64'},
                'native_observation_chain':chain_evidence(),
                'temporal_refinement':refinement_evidence(),
                'long_rollout':long_rollout_evidence(),
                'real_data_processed':False,'LAYA_executed':False,'B200_executed':False,
                'previous_D83_failure_resolved':False,'seconds':time.perf_counter()-start}
        atomic_json(out,report)
    except Exception as error:
        atomic_json(out,{'status':'FAIL','error_type':type(error).__name__,'message':str(error)})
        raise
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',default='runs/expansion.json')
    args=parser.parse_args(); result=run(args.out)
    print(json.dumps(result,indent=2,allow_nan=False))
