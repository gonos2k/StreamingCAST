"""Regression tests for PR2 review findings and the explicit adapter extension."""
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
import torch
from streamingcast.stream import Ledger, Snapshot
from streamingcast.artifacts import ArtifactStore
from streamingcast.cli import demo, inspect_local, check_catalog
from streamingcast.guards import checked_rollout, finite_gradients, VerificationError
from streamingcast.physics import rollout, rollout_substeps, step_interval, thermal_step
from streamingcast.coupling import encode_si, decode_si, forecast_observations, validate_observation_weights
from streamingcast.verification import sample
from test_contracts import record, T, ISSUE


def args():
    x, lon, lat, ev = sample(66, 3)
    return x, x.new_tensor([-.4,.25,.12]), x.new_tensor(19.), lon, lat, ev


def test_snapshot_copies_mutable_input():
    records = [record('a', valid='2026-01-01T23:00:00Z'), record()]
    snap = Snapshot(T, ISSUE, records)
    before = snap.fingerprint
    records[1] = replace(records[1], received_time='2026-01-02T01:00:00Z')
    assert type(snap.records) is tuple and snap.fingerprint == before
    assert snap.records[1].received_time.endswith('00:12:00Z')


@pytest.mark.parametrize('records', [None, iter([]), ['not-a-record'], {'x': 1}])
def test_snapshot_rejects_invalid_container_elements(records):
    with pytest.raises(ValueError): Snapshot(T, ISSUE, records)


@pytest.mark.parametrize('optimize', [False, True])
def test_false_gradcheck_blocks_and_writes_fail_under_optimization(tmp_path, optimize):
    report = tmp_path/'report.json'
    report.write_text('{"status":"PASS"}')
    program = """
import sys, torch
from streamingcast.verification import verify
torch.autograd.gradcheck = lambda *a, **kw: False
verify(sys.argv[1])
"""
    env=os.environ.copy(); env['PYTHONPATH']=str(Path(__file__).parents[1]/'src')
    cmd=[sys.executable]+(['-O'] if optimize else [])+['-c',program,str(report)]
    done=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=40)
    assert done.returncode != 0 and 'VerificationError' in done.stderr
    assert json.loads(report.read_text())['status']=='FAIL'


@pytest.mark.parametrize('fault', ['nan_hour','vector_hour','half_hour','large_hour',
                                  'dtype_hour','huge_source','nan_source','extreme_wind'])
def test_checked_boundary_rejects_review_cases(fault):
    x,p,t,lon,lat,ev=args(); original=x.clone()
    if fault=='nan_hour': t=t.new_tensor(float('nan'))
    if fault=='vector_hour': t=t.repeat(3)
    if fault=='half_hour': t=t+.5
    if fault=='large_hour': t=t.new_tensor(2**25)
    if fault=='dtype_hour': t=t.float()
    if fault=='huge_source': ev=torch.full_like(ev,1e5)
    if fault=='nan_source': ev[0]=float('nan')
    if fault=='extreme_wind': x=x.clone();x[0,2]=301;original=x.clone()
    with pytest.raises(ValueError): checked_rollout(x,p,t,lon,lat,ev,3)
    assert torch.equal(x,original)


def test_checked_boundary_catches_intermediate_output(monkeypatch):
    import streamingcast.guards as module
    def broken(x,*args):
        y=x.clone();y[0,0]=float('inf')
        return y, torch.zeros_like(x[:,1])
    monkeypatch.setattr(module,'step_interval',broken)
    with pytest.raises(VerificationError): checked_rollout(*args(),2)


@pytest.mark.parametrize('gradient', [None, float('nan'), float('inf')])
def test_gradient_gate(gradient):
    p=torch.nn.Parameter(torch.ones(1))
    if gradient is not None:p.grad=torch.tensor([gradient])
    with pytest.raises(VerificationError): finite_gradients([p])
    p.grad=torch.tensor([0.])
    finite_gradients([p])  # zero can be scientifically unidentifiable, not automatically invalid


@pytest.mark.parametrize('substeps',[1,2,4,8])
def test_checked_pure_equivalence_and_water(substeps):
    a=args()
    expected=rollout_substeps(*a,6,substeps=substeps)
    actual=checked_rollout(*a,6,substeps=substeps)
    assert all(torch.equal(x,y) for x,y in zip(actual,expected))
    states,rain=actual
    torch.testing.assert_close(states[-1,:,1]+rain.sum(0),a[0][:,1]+6*a[-1],atol=1e-12,rtol=0)
    assert rain.shape==(6,3)


def test_substeps_one_is_original_bitwise():
    a=args()
    assert all(torch.equal(x,y) for x,y in zip(rollout(*a,24),rollout_substeps(*a,24,substeps=1)))


@pytest.mark.parametrize('count',[True,0,-1,3,1.0,32])
def test_invalid_substeps(count):
    with pytest.raises(ValueError):rollout_substeps(*args(),1,substeps=count)


@pytest.mark.parametrize('dt',[True,0.,-1.,float('nan'),float('inf'),1.1])
def test_invalid_dt(dt):
    with pytest.raises(ValueError):step_interval(*args(),dt)


def test_si_roundtrip_and_scaled_derivative():
    x=args()[0];si=decode_si(x)
    torch.testing.assert_close(encode_si(si),x,atol=5e-14,rtol=0)
    v=torch.ones_like(si)
    _,jv=torch.func.jvp(encode_si,(si,),(v,))
    assert torch.equal(jv,torch.tensor([1.,1000.,1.,1.],dtype=x.dtype).expand_as(x))


@pytest.mark.parametrize('fault',['negative','row_sum','shape','nan'])
def test_observation_contract(fault):
    weights=torch.tensor([[.2,.3,.5]])
    if fault=='negative':weights[0,0]=-1
    if fault=='row_sum':weights[0,0]=2
    if fault=='shape':weights=weights.ravel()
    if fault=='nan':weights[0,0]=float('nan')
    with pytest.raises(ValueError):validate_observation_weights(weights,3)


def test_full_unit_model_observation_chain_gradcheck():
    x,p,t,lon,lat,ev=args();si=decode_si(x).requires_grad_();p=p.requires_grad_()
    weights=x.new_tensor([[.2,.3,.5],[.7,.1,.2]])
    validate_observation_weights(weights,3)
    fun=lambda a,b:forecast_observations(a,b,t,lon,lat,ev/1000,weights,2,substeps=2)
    assert torch.autograd.gradcheck(fun,(si,p),eps=1e-6,atol=1e-5,rtol=1e-5)


def test_fine_rollout_restart():
    x,p,t,lon,lat,ev=args()
    all_s,all_r=rollout_substeps(x,p,t,lon,lat,ev,24,substeps=4)
    a,ar=rollout_substeps(x,p,t,lon,lat,ev,13,substeps=4)
    b,br=rollout_substeps(a[-1],p,t+13,lon,lat,ev,11,substeps=4)
    assert torch.equal(all_s,torch.cat((a,b[1:])))
    assert torch.equal(all_r,torch.cat((ar,br)))


def test_late_missing_payload_does_not_break_past_inspect(tmp_path):
    root=tmp_path/'demo';demo(root)
    manifest=root/'manifest.json';records=json.loads(manifest.read_text())
    late=dict(records[-1],event_id='late',revision=1,path='missing.npz',
              available_time='2026-01-02T00:20:00Z',received_time='2026-01-02T00:25:00Z')
    records.append(late);manifest.write_text(json.dumps(records))
    a=inspect_local(manifest,root,root/'ledger.sqlite','manufactured-local',T,ISSUE)
    assert a['selected_events']==['demo-0','demo-1']
    with pytest.raises(FileNotFoundError):
        inspect_local(manifest,root,root/'ledger.sqlite','manufactured-local',T,'2026-01-02T00:30:00Z')
    with pytest.raises(FileNotFoundError):check_catalog(manifest,root,root/'ledger.sqlite')


def test_selected_corrupt_payload_has_no_silent_fallback(tmp_path):
    root=tmp_path/'demo';demo(root)
    manifest=root/'manifest.json';records=json.loads(manifest.read_text())
    r=dict(records[-1],event_id='eligible-r1',revision=1,path='corrupt.npz')
    (root/r['path']).write_bytes(b'corrupt')
    records.append(r);manifest.write_text(json.dumps(records))
    with pytest.raises(ValueError):inspect_local(manifest,root,root/'ledger.sqlite','manufactured-local',T,ISSUE)


def test_artifact_install_idempotency_and_recovery(tmp_path):
    store=ArtifactStore(tmp_path/'store');ledger=Ledger(tmp_path/'ledger.sqlite')
    r=store.put_npz(state=np.ones((2,4)))
    assert store.put_npz(state=np.ones((2,4)))==r
    assert store.recovery_report(ledger)['orphan_sha256']==[r['sha256']]
    assert store.register(ledger,'a'*64,r,{'status':'SYNTHETIC_ONLY'})
    assert not store.register(ledger,'a'*64,r,{'status':'SYNTHETIC_ONLY'})
    assert store.recovery_report(ledger)['orphan_sha256']==[]
    np.testing.assert_array_equal(store.load(r)['state'],np.ones((2,4)))
    p=store.root/r['path'];raw=p.read_bytes();p.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
    with pytest.raises(ValueError):store.register(ledger,'a'*64,r,{'status':'SYNTHETIC_ONLY'})
    with pytest.raises(ValueError):store.load(r)
    with pytest.raises(ValueError):store.put_npz(state=np.ones((2,4)))
    assert len(store.recovery_report(ledger)['broken_runs'])==1
    assert p.read_bytes()!=raw  # corruption detected, not silently repaired
    ledger.close()


@pytest.mark.parametrize('fault',['path','size_bool','size_limit','digest','symlink'])
def test_artifact_receipt_guards(tmp_path,fault):
    store=ArtifactStore(tmp_path/'s');r=store.put_npz(x=np.ones(3))
    if fault=='path':r['path']='../outside.npz'
    if fault=='size_bool':r['bytes']=True
    if fault=='size_limit':r['bytes']=10**12
    if fault=='digest':r['sha256']='bad'
    if fault=='symlink':
        p=store.root/r['path'];outside=tmp_path/'outside';outside.write_bytes(p.read_bytes());p.unlink();p.symlink_to(outside)
    with pytest.raises(ValueError):store.load(r)


@pytest.mark.parametrize('bad',[np.array([object()]),np.array([np.nan]),np.array([np.inf])])
def test_artifact_invalid_arrays(tmp_path,bad):
    with pytest.raises(ValueError):ArtifactStore(tmp_path).put_npz(x=bad)
