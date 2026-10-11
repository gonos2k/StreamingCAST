from datetime import timedelta
from dataclasses import replace
from hashlib import sha256
import json
import sqlite3
import numpy as np
import pytest
from streamingcast.time_contract import utc_hour,utc_time,window,validate_tail_use,iso
from streamingcast.products import HourlyRain,accumulate,summarize_members
from streamingcast.schema import SCHEMAS,D83,schema_hash
from streamingcast.stream import Record,Ledger
from streamingcast.local import read_record,atomic_npz
from streamingcast.cli import demo,inspect_local

T='2026-01-02T00:00:00Z';ISSUE='2026-01-02T00:15:00Z'


def record(event='b',revision=0,valid=T,available='2026-01-02T00:10:00Z',received='2026-01-02T00:12:00Z'):
    return Record(event,'local',revision,valid,available,received,'b.npz','a'*64,'toy-column-v1',schema_hash('toy-column-v1'),'b'*64)


def file_record(tmp_path,schema='toy-column-v1'):
    names,units=zip(*SCHEMAS[schema]);n=len(names)
    p=tmp_path/'b.npz';a=np.ones((4,n));m=np.ones_like(a,dtype=bool)
    atomic_npz(p,state=a,mask=m,channels=np.array(names),units=np.array(units))
    return replace(record(),sha256=sha256(p.read_bytes()).hexdigest(),schema=schema,schema_sha256=schema_hash(schema))


@pytest.mark.parametrize('value',['2026-01-01','2026-01-01T00:30:00Z','2026-01-01T00:00:00+09:00'])
def test_bad_valid_time(value):
    with pytest.raises(ValueError):utc_hour(value)


def test_receipt_can_be_subhour():
    assert utc_time('2026-01-01T00:40:10Z').second==10


@pytest.mark.parametrize('rev',[True,-1,1.0])
def test_revision_contract(rev):
    with pytest.raises(ValueError):record(revision=rev)


@pytest.mark.parametrize('change',[{'received_time':'2026-01-02T00:00:00Z'},
                                     {'schema_sha256':'a'*64},{'sha256':'abc'},{'event_id':''}])
def test_bad_record(change):
    with pytest.raises(ValueError):replace(record(),**change)


def test_cutoff_revisions_replay_and_freeze(tmp_path):
    db=Ledger(tmp_path/'events.sqlite')
    early=record('a',valid='2026-01-01T23:00:00Z');r=record()
    assert db.ingest(r);assert db.ingest(early);assert not db.ingest(r)
    old=db.snapshot('local',T,ISSUE);f=old.fingerprint
    delayed=record('b-r1',1,received='2026-01-02T00:25:00Z')
    assert db.ingest(delayed)
    assert db.snapshot('local',T,ISSUE).fingerprint==f
    assert db.snapshot('local',T,'2026-01-02T00:30:00Z').records[-1].revision==1
    assert old.records[-1].revision==0
    with pytest.raises(ValueError):db.ingest(replace(r,sha256='b'*64))
    with pytest.raises(sqlite3.IntegrityError):db.ingest(replace(r,event_id='same-version'))
    db.close()


def test_missing_current_not_filled_by_future(tmp_path):
    db=Ledger(tmp_path/'e.sqlite')
    db.ingest(record('a',valid='2026-01-01T23:00:00Z'))
    with pytest.raises(ValueError):db.snapshot('local',T,ISSUE)
    db.close()


def test_ledger_restart_and_idempotency(tmp_path):
    p=tmp_path/'e.sqlite';db=Ledger(p);r=record();db.ingest(r)
    key='b'*64
    assert db.commit_run(key,{'ok':True});assert not db.commit_run(key,{'ok':True})
    with pytest.raises(ValueError):db.commit_run(key,{'ok':False})
    with pytest.raises(ValueError):db.commit_run('c'*64,{'value':float('nan')})
    db.close();db=Ledger(p)
    assert not db.ingest(r);assert not db.commit_run(key,{'ok':True});db.close()


@pytest.mark.parametrize('schema',['toy-column-v1','d83-v1'])
def test_local_schema_read(tmp_path,schema):
    r=file_record(tmp_path,schema);x,m=read_record(r,tmp_path)
    assert x.shape==(4,len(SCHEMAS[schema]));assert m.all()
    assert len(D83)==83 and D83[-1]==('sp','Pa')


def test_modified_file_and_escape(tmp_path):
    r=file_record(tmp_path);p=tmp_path/'b.npz'
    with pytest.raises(ValueError):read_record(replace(r,path='../b.npz'),tmp_path)
    p.write_bytes(p.read_bytes()+b'changed')
    with pytest.raises(ValueError):read_record(r,tmp_path)


@pytest.mark.parametrize('fault',['units','order','mask','nan','shape','oversize'])
def test_local_rejects_bad_arrays(tmp_path,fault):
    r=file_record(tmp_path);p=tmp_path/'b.npz'
    with np.load(p,allow_pickle=False) as z:d={k:z[k] for k in z.files}
    if fault=='units':d['units'][0]='Pa'
    if fault=='order':d['channels']=d['channels'][::-1]
    if fault=='mask':d['mask']=d['mask'].astype(int)
    if fault=='nan':d['state'][0,0]=np.nan
    if fault=='shape':d['state']=d['state'][:,:2]
    atomic_npz(p,**d);r=replace(r,sha256=sha256(p.read_bytes()).hexdigest())
    with pytest.raises(ValueError):read_record(r,tmp_path,max_bytes=1 if fault=='oversize' else 2**20)


def test_masked_nan_is_not_zero(tmp_path):
    r=file_record(tmp_path);p=tmp_path/'b.npz'
    with np.load(p,allow_pickle=False) as z:d={k:z[k] for k in z.files}
    d['mask'][0,0]=False;d['state'][0,0]=np.nan;atomic_npz(p,**d)
    r=replace(r,sha256=sha256(p.read_bytes()).hexdigest());x,m=read_record(r,tmp_path)
    assert np.isnan(x[0,0]) and not m[0,0]


def test_quantile_is_computed_after_accumulation():
    t=utc_hour(T);ends=(t+timedelta(hours=1),t+timedelta(hours=2))
    p=HourlyRain(np.array([[10.,0.],[0.,10.]]),ends,t,utc_time(ISSUE),
                 'ensemble_trajectory',ensemble_id='ens',member_ids=('a','b'),trajectory_certified=True)
    total=accumulate(p,start=t,end=ends[-1])
    assert summarize_members(total,statistic='quantile',level=.9)['values']==10
    marginal=HourlyRain(np.array([10.,10.]),ends,t,utc_time(ISSUE),'quantile',probability_level=.9)
    with pytest.raises(ValueError):accumulate(marginal,start=t,end=ends[-1])


@pytest.mark.parametrize('bad',[-1.,float('nan'),float('inf')])
def test_bad_rain(bad):
    t=utc_hour(T)
    with pytest.raises(ValueError):HourlyRain(np.array([bad]),(t+timedelta(hours=1),),t,utc_time(ISSUE),'point_estimate')


def test_tail_and_bool_horizon():
    w=window('2025-12-31T18:00:00Z')
    assert iso(w.targets[-1])=='2026-01-10T18:00:00Z'
    with pytest.raises(ValueError):validate_tail_use(w.targets[-1],'train')
    with pytest.raises(ValueError):window(T,True)


def test_local_end_to_end(tmp_path):
    result=demo(tmp_path/'demo')
    assert result['hours']==240 and result['output_shape']==[241,8,4]
    assert result['first_commit'] and not result['duplicate_commit_added']
    assert not result['weather_skill_verified']
    assert (tmp_path/'demo'/'forecast.npz').exists()


def test_geometry_and_snapshot_bypass_rejected(tmp_path):
    from streamingcast.stream import Snapshot
    db=Ledger(tmp_path/'e.sqlite');a=record('a',valid='2026-01-01T23:00:00Z');b=record()
    db.ingest(a);db.ingest(replace(b,grid_sha256='c'*64))
    with pytest.raises(ValueError):db.snapshot('local',T,ISSUE)
    with pytest.raises(ValueError):Snapshot(T,ISSUE,(b,))
    with pytest.raises(ValueError):Snapshot(T,'2026-01-02T00:01:00Z',(a,b))
    db.close()


def test_snapshot_data_modified_after_issuance(tmp_path):
    r=file_record(tmp_path);db=Ledger(tmp_path/'e.sqlite')
    db.ingest(replace(r,event_id='a',valid_time='2026-01-01T23:00:00Z'));db.ingest(r)
    snap=db.snapshot('local',T,ISSUE)
    (tmp_path/'b.npz').write_bytes(b'invalid replacement')
    with pytest.raises(ValueError):read_record(snap.records[-1],tmp_path)
    db.close()


def test_model_identity_is_in_run_key(tmp_path):
    db=Ledger(tmp_path/'e.sqlite');db.ingest(record('a',valid='2026-01-01T23:00:00Z'));db.ingest(record())
    s=db.snapshot('local',T,ISSUE)
    assert s.run_key('a'*64,{'steps':1})!=s.run_key('b'*64,{'steps':1})
    assert s.run_key('a'*64,{'steps':1})!=s.run_key('a'*64,{'steps':2})
    db.close()


def test_consumer_does_not_import_training_or_scipy(tmp_path):
    import os,sys,subprocess
    from pathlib import Path
    code=("import sys; sys.modules['scipy']=None; "
          "sys.modules['streamingcast.verification']=None; "
          "from streamingcast.cli import demo; "
          "r=demo(sys.argv[1]); assert r['hours']==240")
    env=os.environ.copy();env['PYTHONPATH']=str(Path(__file__).parents[1]/'src')
    done=subprocess.run([sys.executable,'-c',code,str(tmp_path/'consumer')],env=env,capture_output=True,text=True)
    assert done.returncode==0,done.stderr
