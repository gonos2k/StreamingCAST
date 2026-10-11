"""Bounded Green/Red audit of StreamingCAST PR #2; original source is not modified.
Run: python audit_checks.py --source source/StreamingCAST --out results/audit.json
All meteorological/numerical fields here are manufactured, not real weather data.
"""
from __future__ import annotations
import argparse, dataclasses, hashlib, json, math, os, pathlib, platform, subprocess, sys, tempfile, time
import numpy as np

def default_source():
    here=pathlib.Path(__file__).resolve().parent
    local=here/'source'/'StreamingCAST'
    return local if local.is_dir() else here.parents[1]

import torch
from scipy.integrate import solve_ivp
from scipy.special import expit


def optimize_gate(source):
    script = """import json,torch
from streamingcast.verification import derivative_evidence
torch.set_num_threads(1)
torch.autograd.gradcheck=lambda *args,**kwargs: False  # controlled diagnostic fault
r=derivative_evidence()
print(json.dumps({'gradcheck':r['gradcheck'],'jvp_error':r['jvp_central_difference_relative_error']}))
"""
    env=os.environ.copy();env['PYTHONPATH']=str(source/'src');result={}
    for name,args in [('normal',[]),('optimized',['-O'])]:
        c=subprocess.run([sys.executable,*args,'-c',script],env=env,capture_output=True,text=True,timeout=45)
        result[name]={'returncode':c.returncode,'stdout':c.stdout.strip(),'stderr_tail':c.stderr[-1400:]}
    return result


def make_record(event,valid,revision=0,received='2026-01-02T00:12:00Z',path='unused.npz'):
    from streamingcast.stream import Record
    from streamingcast.schema import schema_hash
    return Record(event,'audit',revision,valid,'2026-01-02T00:10:00Z',received,path,'a'*64,
                  'toy-column-v1',schema_hash('toy-column-v1'),'b'*64)


def snapshot_mutability():
    from streamingcast.stream import Snapshot
    records=[make_record('prev','2026-01-01T23:00:00Z'),make_record('current','2026-01-02T00:00:00Z')]
    snap=Snapshot('2026-01-02T00:00:00Z','2026-01-02T00:15:00Z',records)
    before=snap.fingerprint
    records[1]=dataclasses.replace(records[1],event_id='late',revision=1,received_time='2026-01-02T01:00:00Z')
    generated=snap.run_key('c'*64,{'horizon':1})
    explicit_revalidation_rejected=False
    try: Snapshot(snap.initialization,snap.issue,snap.records)
    except ValueError: explicit_revalidation_rejected=True
    return {'accepted_mutable_sequence':isinstance(snap.records,list),'fingerprint_changed':before!=snap.fingerprint,
            'late_record_present':snap.records[1].received_time,'run_key_generated':generated,
            'fresh_constructor_rejects_same_content':explicit_revalidation_rejected,
            'scope':'public constructor; Ledger.snapshot itself currently supplies a tuple'}


def manifest_asof_isolation(tmp):
    from streamingcast.cli import demo,inspect_local
    root=tmp/'demo';baseline=demo(root)
    manifest=root/'manifest.json';records=json.loads(manifest.read_text())
    later=records[-1].copy();later.update(event_id='future-missing',revision=2,path='not-arrived.npz',
        available_time='2026-01-02T00:45:00Z',received_time='2026-01-02T00:46:00Z')
    records.append(later); manifest.write_text(json.dumps(records))
    try:
        inspect_local(manifest,root,root/'ledger.sqlite','manufactured-local','2026-01-02T00:00:00Z','2026-01-02T00:15:00Z')
        status='unexpected_success'
    except Exception as exc:status=type(exc).__name__+': '+str(exc)
    from streamingcast.stream import Ledger
    db=Ledger(root/'ledger.sqlite')
    try: existing=db.snapshot('manufactured-local','2026-01-02T00:00:00Z','2026-01-02T00:15:00Z')
    finally:db.close()
    return {'initial_inspect_passed':baseline['status'],'reinspect_after_unavailable_record':status,
            'unchanged_eligible_snapshot_still_available':existing.fingerprint==baseline['snapshot'],
            'scope':'availability/isolation of local inspection; not future data leakage'}


def wet_comparison_principle():
    from streamingcast.physics import step_tensor,validate_inputs,RADIATIVE_RATE
    p=torch.tensor([10.,0.,0.],dtype=torch.float64)
    qa=26.;ta=math.log(qa/8)/.06;theta=ta/math.exp(-RADIATIVE_RATE)
    x=torch.tensor([[theta,qa,3.,2.]],dtype=p.dtype,requires_grad=True)
    zero=torch.zeros(1,dtype=p.dtype);t=torch.tensor(0.,dtype=p.dtype)
    validate_inputs(x,p,zero,zero,zero)
    y,r=step_tensor(x,p,t,zero,zero,zero)
    g=torch.autograd.grad(y[0,1],x)[0][0,1].item()
    beta=.02+.28*expit(10.);h=beta/2
    formula=math.exp(-h)*(1-qa*beta/6)
    # Comparator is scalar, fixed-temperature depletion with rate recomputed as q changes.
    # Do NOT treat this as the full coupled atmospheric comparison principle.
    def ref(q):
        return solve_ivp(lambda s,z:-beta*expit((z-qa)/1.5)*z,(0,1),[q],method='DOP853',rtol=1e-12,atol=1e-13).y[0,-1]
    eps=1e-4;scalar_fd=(ref(qa+eps)-ref(qa-eps))/(2*eps)
    return {'input_theta_K':theta,'input_q_gkg':qa,'q_s_gkg':qa,'validated':True,
            'next_q_gkg':y[0,1].item(),'rain_mm':r[0].item(),
            'autograd_dqnext_dq':g,'analytical_dqnext_dq':formula,'continuous_scalar_dqnext_dq':scalar_fd,
            'comparison_scope':'frozen temperature scalar sink; full moist coupled system not claimed monotone'}


def unsafe_domain_and_clock():
    from streamingcast.physics import step_tensor,rollout,validate_inputs
    cases=[]
    for dt in (torch.float32,torch.float64):
        x=torch.tensor([[0.,12.,3.,2.]],dtype=dt,requires_grad=True);p=torch.tensor([-.4,.25,.12],dtype=dt,requires_grad=True)
        lon=torch.zeros(1,dtype=dt);lat=lon.clone();ev=torch.full_like(lon,1e5)
        validate_inputs(x,p,lon,lat,ev)
        ys,rs=rollout(x,p,torch.tensor(0.,dtype=dt),lon,lat,ev,3)
        gs=torch.autograd.grad(ys[-1].sum()+rs.sum(),(x,p))
        cases.append({'dtype':str(dt),'initial_validation_passed':True,'evap_gkg_per_h':1e5,
            'forward_finite':bool(torch.isfinite(ys).all() and torch.isfinite(rs).all()),
            'all_gradients_finite':all(bool(torch.isfinite(g).all()) for g in gs),
            'nan_gradient_elements':sum(int(torch.isnan(g).sum()) for g in gs),
            'theta_max':ys[...,0].max().item(), 'q_max':ys[...,1].max().item()})
    x=torch.tensor([[0.,10.,3.,2.]],dtype=torch.float64);p=x.new_tensor([-.4,.25,.12]);lon=x.new_zeros(1);ev=lon.clone()
    validate_inputs(x,p,lon,lon,ev)
    out=step_tensor(x,p,x.new_tensor(float('nan')),lon,lon,ev)[0]
    return {'manufactured_extreme_source':cases,'nan_hour_not_in_validator':not bool(torch.isfinite(out).all()),
        'scope':'missing checked adapter/domain contract, not a realistic evaporation forecast; pure tensor core should remain branchless'}


def subsaturated_drizzle():
    from streamingcast.physics import rollout
    cases=[]
    for q in (2.,4.,6.,8.):
        x=torch.tensor([[0.,q,0.,0.]],dtype=torch.float64);p=x.new_tensor([-.4,0.,0.]);z=x.new_zeros(1)
        s,r=rollout(x,p,x.new_tensor(0.),z,z,z,240)
        cases.append({'q_initial_gkg':q,'initial_qsat_gkg':8.,'initial_ratio':q/8.,
                      'rain_1h_mm':r[0,0].item(),'rain_240h_mm':r[:,0].sum().item(),
                      'q_final_gkg':s[-1,0,1].item(),'theta_final_K':s[-1,0,0].item()})
    return {'cases':cases,'known_in_docs':True,'scope':'smooth manufactured sigmoid sink, not a wet/dry microphysics model'}


def continuous_rhs(t,x,p,lon,lat,ev):
    theta,q,u,v=x;w=2*np.pi/24;r=1/48
    beta=.02+.28*expit(p[0]);s=beta*expit((q-8*np.exp(.06*theta))/1.5)*q
    f=2*7.292115e-5*np.sin(lat)*3600
    return np.array([-r*theta+p[1]*np.cos(w*t+lon)+p[2]*np.cos(2*w*t+2*lon)+2.5*s,ev-s,f*v,-f*u])


def split_dt(x,p,t,lon,lat,ev,dt):
    d=math.exp(-dt/48);ta=d*x[0]
    for j in (1,2):
        w=2*math.pi*j/24;ph=w*t+j*lon;a,b=math.cos(w*dt)-d,math.sin(w*dt)
        re=(a/48+b*w)/(1/48**2+w*w);im=(b/48-a*w)/(1/48**2+w*w)
        ta=ta+p[j]*(re*torch.cos(ph)-im*torch.sin(ph))
    qa=x[1]+dt*ev;beta=.02+.28*torch.sigmoid(p[0]);h=beta*torch.sigmoid((qa-8*torch.exp(.06*ta))/1.5)
    rain=-qa*torch.expm1(-dt*h);ang=2*7.292115e-5*torch.sin(lat)*3600*dt
    return torch.stack((ta+2.5*rain,qa-rain,torch.cos(ang)*x[2]+torch.sin(ang)*x[3],-torch.sin(ang)*x[2]+torch.cos(ang)*x[3]))


def coupled_limit_test():
    from streamingcast.physics import step_tensor
    x=torch.tensor([0.,12.,3.,2.],dtype=torch.float64);p=x.new_tensor([-.4,.25,.12]);v=x.new_tensor([.1,-.2,.15]);t=x.new_tensor(19.);lon=x.new_tensor(.7);lat=x.new_tensor(.65);ev=x.new_tensor(.03)
    check=step_tensor(x[None],p,t,lon[None],lat[None],ev[None])[0][0]
    equality=float(torch.max(torch.abs(check-split_dt(x,p,t,lon,lat,ev,1.))))
    total=24
    def ref(par,tol=2e-12):
        return solve_ivp(lambda ti,xi:continuous_rhs(ti,xi,par,float(lon),float(lat),float(ev)),
            (19,19+total),x.numpy(),method='DOP853',rtol=tol,atol=tol/10).y[:,-1]
    yr=ref(p.numpy());eps=1e-4
    def fd(h):return (ref((p+h*v).numpy())-ref((p-h*v).numpy()))/(2*h)
    gradref=fd(eps);g2=fd(eps/2)
    results=[]
    for dt in (1.,.5,.25,.125,.0625):
        def pred(par):
            s=x
            for k in range(round(total/dt)):s=split_dt(s,par,t+k*dt,lon,lat,ev,dt)
            return s
        yy,jv=torch.func.jvp(pred,(p,),(v,))
        results.append({'dt_hours':dt,'value_L2_error':float(np.linalg.norm(yy.numpy()-yr)),
            'theta_error_K':float(yy[0])-yr[0],'q_error_gkg':float(yy[1])-yr[1],
            'sensitivity_relative_error':float(np.linalg.norm(jv.numpy()-gradref)/np.linalg.norm(gradref))})
    for a,b in zip(results,results[1:]):a['value_order_to_next']=math.log(a['value_L2_error']/b['value_L2_error'],2)
    return {'scope':'audit-only dt refinement; simultaneous ODE is an extension, NOT original truth; mixed-unit L2 is only a fixed-coordinate refinement diagnostic',
        'dt1_matches_original_max_abs':equality,'reference_state':yr.tolist(),'reference_sensitivity':gradref.tolist(),
        'reference_fd_halving_relative_change':float(np.linalg.norm(g2-gradref)/np.linalg.norm(gradref)),
        'reference_tolerance_change':float(np.max(abs(ref(p.numpy(),5e-13)-yr))),'results':results}


def extended_derivatives():
    from streamingcast.physics import rollout
    from streamingcast.verification import sample
    results=[]
    for seed in (41,42,43):
        torch.manual_seed(seed)
        x,lon,lat,ev=sample(seed,3);p=x.new_tensor([-.4,.25,.12]);t=x.new_tensor(19.)
        vx=torch.randn_like(x)*.1;vp=torch.randn_like(p)*.1
        for H in (1,24,240):
            def f(xx,pp):
                ss,rr=rollout(xx,pp,t,lon,lat,ev,H)
                return torch.cat((ss[-1],rr.sum(0)[:,None]),-1)
            y,jv=torch.func.jvp(f,(x,p),(vx,vp));hh=2e-5
            fd=(f(x+hh*vx,p+hh*vp)-f(x-hh*vx,p-hh*vp))/(2*hh)
            cot=torch.randn_like(y);_,pb=torch.func.vjp(f,x,p);a,b=pb(cot)
            lhs=float((cot*jv).sum());rhs=float((a*vx).sum()+(b*vp).sum())
            results.append({'seed':seed,'hours':H,'jvp_fd_relative':float(torch.linalg.vector_norm(jv-fd)/torch.linalg.vector_norm(jv)),
                            'adjoint_relative':abs(lhs-rhs)/max(abs(lhs),abs(rhs),1e-12)})
    return results


def moisture_jvp_identities():
    from streamingcast.physics import step_tensor,thermal_step,GAMMA
    from streamingcast.verification import sample
    torch.manual_seed(33);x,lon,lat,ev=sample(44,7);p=x.new_tensor([-.4,.25,.12]);t=x.new_tensor(4.)
    vx=torch.randn_like(x)*.1;vp=torch.randn_like(p)*.1
    def f(a,b):
        y,r=step_tensor(a,b,t,lon,lat,ev);ta=thermal_step(a[:,0],b[1:],t,lon)
        return torch.stack((y[:,1]+r-a[:,1]-ev,y[:,0]+GAMMA*y[:,1]-ta-GAMMA*(a[:,1]+ev)),0)
    value,jv=torch.func.jvp(f,(x,p),(vx,vp))
    return {'max_primal_residual':float(value.abs().max()),'max_tangent_residual':float(jv.abs().max())}


def sqlite_wal_and_idempotence(tmp):
    from streamingcast.stream import Ledger
    a=Ledger(tmp/'wal.sqlite');b=Ledger(tmp/'wal.sqlite')
    try:
        a.ingest(make_record('a','2026-01-01T23:00:00Z'));a.ingest(make_record('b','2026-01-02T00:00:00Z'))
        a.db.execute('BEGIN');before=a.db.execute('SELECT COUNT(*) FROM records').fetchone()[0]
        b.ingest(make_record('b-new','2026-01-02T00:00:00Z',revision=1))
        during=a.db.execute('SELECT COUNT(*) FROM records').fetchone()[0];a.db.execute('COMMIT')
        after=a.db.execute('SELECT COUNT(*) FROM records').fetchone()[0]
        first=a.commit_run('f'*64,{'out':'same'});duplicate=b.commit_run('f'*64,{'out':'same'})
        conflict=False
        try:b.commit_run('f'*64,{'out':'different'})
        except ValueError:conflict=True
        return {'count_before':before,'count_during_other_connection_commit':during,'count_after_end':after,
                'first_insert':first,'duplicate_insert':duplicate,'conflicting_result_rejected':conflict}
    finally:a.close();b.close()


def atomic_overwrite_receipt(tmp):
    from streamingcast.stream import Ledger
    from streamingcast.local import atomic_npz
    path=tmp/'artifact.npz';db=Ledger(tmp/'artifact.sqlite')
    try:
        atomic_npz(path,state=np.array([1.]));old=hashlib.sha256(path.read_bytes()).hexdigest()
        payload={'artifact':path.name,'sha256':old};db.commit_run('a'*64,payload)
        atomic_npz(path,state=np.array([2.]));new=hashlib.sha256(path.read_bytes()).hexdigest()
        status=db.commit_run('a'*64,payload)
        return {'file_overwritten':old!=new,'old_receipt_duplicate_result':status,
            'old_receipt_matches_current_bytes':old==hashlib.sha256(path.read_bytes()).hexdigest(),
            'scope':'disclosed separation of arrays/ledger; fresh-root demo prevents this exact overwrite path'}
    finally:db.close()


def identifiability():
    from streamingcast.verification import sample
    from streamingcast.physics import step_tensor
    x,lon,lat,ev=sample(121,96);p=x.new_tensor([-.4,.25,.12]);t=x.new_tensor(7.)
    def measure(xx,ee):
        def response(par):
            y,r=step_tensor(xx,par,t,lon,lat,ee)
            return torch.cat(((y/xx.new_tensor([4,10,12,12])).flatten(),r.flatten()))
        jac=torch.func.jacrev(response)(p)
        singular=torch.linalg.svdvals(jac)
        return {'singular_values':singular.tolist(),'rank':int(torch.linalg.matrix_rank(jac)),
                'p0_column_norm':float(torch.linalg.vector_norm(jac[:,0]))}
    dry=x.clone();dry[:,1]=0
    return {'original_training_distribution':measure(x,ev),'exactly_dry_no_source':measure(dry,torch.zeros_like(ev)),
            'scope':'local sensitivity rank, not global parameter identifiability or optimizer convergence proof'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=pathlib.Path,default=default_source());parser.add_argument('--out',type=pathlib.Path,default=pathlib.Path('results/audit.json'));args=parser.parse_args()
    source=args.source.resolve();sys.path.insert(0,str(source/'src'));torch.set_num_threads(1);start=time.perf_counter()
    with tempfile.TemporaryDirectory() as d:
        tmp=pathlib.Path(d)
        result={'source_commit':'2c21bccb58bc5dc9a967880ebf3494d82d1b44d3',
                'environment':{'python':platform.python_version(),'torch':torch.__version__,'numpy':np.__version__,'device':'cpu','threads':1},
                'real_data_used':False,'source_modified':False,
                'optimized_gate':optimize_gate(source),'snapshot_mutability':snapshot_mutability(),
                'asof_inspection':manifest_asof_isolation(tmp),'moisture_comparison':wet_comparison_principle(),
                'domain_and_clock':unsafe_domain_and_clock(),'subsat_drizzle':subsaturated_drizzle(),
                'coupled_limit':coupled_limit_test(),'extended_derivatives':extended_derivatives(),
                'tangent_budgets':moisture_jvp_identities(),'identifiability':identifiability(),'sqlite':sqlite_wal_and_idempotence(tmp),
                'artifact_ledger':atomic_overwrite_receipt(tmp),'seconds':None}
    result['seconds']=time.perf_counter()-start;args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))
if __name__=='__main__':main()
