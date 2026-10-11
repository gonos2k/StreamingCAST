"""Local entry points. Real-data manifests are inspected, never silently forecast by the toy."""
from pathlib import Path
from dataclasses import asdict
from datetime import datetime,timezone
import argparse
import hashlib
import json
import numpy as np
import torch
from .schema import SCHEMAS,schema_hash
from .stream import Ledger,Record
from .local import read_manifest,read_record,atomic_npz
from .time_contract import utc_hour
from .physics import validate_inputs,rollout


def inspect_local(manifest,root,ledger,source,initialization,issue):
    db=Ledger(ledger)
    try:
        for r in read_manifest(manifest):
            read_record(r,root)  # validate before cataloguing, no array data stored in DB
            db.ingest(r)
        snap=db.snapshot(source,initialization,issue)
        arrays=[read_record(r,root) for r in snap.records]
        if arrays[0][0].shape!=arrays[1][0].shape: raise ValueError("History grid mismatch")
        return {'snapshot':snap.fingerprint,'schema':snap.records[-1].schema,
                'shape':list(arrays[-1][0].shape),'selected_events':[r.event_id for r in snap.records],
                'status':'INPUT_CONTRACT_PASS','weather_skill_verified':False}
    finally:
        db.close()


def demo(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    n=8;lon=torch.linspace(-3,3,n,dtype=torch.float64);lat=torch.linspace(-1,1,n,dtype=lon.dtype)
    state=torch.stack((torch.linspace(-1,2,n,dtype=lon.dtype),torch.linspace(8,12,n,dtype=lon.dtype),
                       torch.ones(n,dtype=lon.dtype)*3,torch.ones(n,dtype=lon.dtype)*2),-1)
    records=[]
    for j,valid in enumerate(('2026-01-01T23:00:00Z','2026-01-02T00:00:00Z')):
        p=root/f'input{j}.npz';contract=SCHEMAS['toy-column-v1']
        atomic_npz(p,state=state.numpy(),mask=np.ones((n,4),dtype=bool),
                   channels=np.array([x[0] for x in contract]),units=np.array([x[1] for x in contract]))
        r=Record(f'demo-{j}','manufactured-local',0,valid,'2026-01-02T00:10:00Z',
                 '2026-01-02T00:12:00Z',p.name,hashlib.sha256(p.read_bytes()).hexdigest(),
                 'toy-column-v1',schema_hash('toy-column-v1'),
                 hashlib.sha256(lon.numpy().tobytes()+lat.numpy().tobytes()).hexdigest());records.append(asdict(r))
    manifest=root/'manifest.json';manifest.write_text(json.dumps(records,indent=2))
    args=(manifest,root,root/'ledger.sqlite','manufactured-local',records[-1]['valid_time'],'2026-01-02T00:15:00Z')
    summary=inspect_local(*args)
    db=Ledger(root/'ledger.sqlite')
    try:
        snap=db.snapshot(args[3],args[4],args[5]);s,mask=read_record(snap.records[-1],root)
        if not mask.all(): raise ValueError("Toy cannot consume missing state")
        state=torch.from_numpy(s);par=torch.tensor([-.4,.25,.12],dtype=state.dtype);ev=torch.full((n,),.02,dtype=state.dtype)
        validate_inputs(state,par,lon,lat,ev)
        hours=(utc_hour(snap.initialization)-datetime(1970,1,1,tzinfo=timezone.utc)).total_seconds()/3600
        with torch.no_grad(): states,rain=rollout(state,par,torch.tensor(hours,dtype=state.dtype),lon,lat,ev,240)
        if not torch.isfinite(states).all() or not torch.isfinite(rain).all() or (rain<0).any():
            raise ValueError("Invalid output; do not publish")
        key=snap.run_key(hashlib.sha256(par.numpy().tobytes()).hexdigest(),
                        {'horizon':240,'implementation':'toy-column-v1',
                         'code_hash':hashlib.sha256((Path(__file__).with_name('physics.py')).read_bytes()).hexdigest(),
                         'evaporation_hash':hashlib.sha256(ev.numpy().tobytes()).hexdigest(),'geometry_hash':hashlib.sha256(lon.numpy().tobytes()+lat.numpy().tobytes()).hexdigest()})
        path=root/'forecast.npz';atomic_npz(path,state=states.numpy(),rain_1h_mm=rain.numpy())
        payload={'artifact':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'status':'SYNTHETIC_ONLY'}
        first=db.commit_run(key,payload);repeat=db.commit_run(key,payload)
        summary.update({'hours':240,'output_shape':list(states.shape),'first_commit':first,
                        'duplicate_commit_added':repeat,'run_key':key,'not_a_real_data_forecast':True})
    finally:
        db.close()
    (root/'receipt.json').write_text(json.dumps(summary,indent=2));return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    d=sub.add_parser('demo');d.add_argument('--root',required=True)
    v=sub.add_parser('prove');v.add_argument('--out',required=True)
    s=sub.add_parser('inspect');
    for key in ('manifest','root','ledger','source','initialization','issue'): s.add_argument('--'+key,required=True)
    a=parser.parse_args()
    if a.command=='demo': result=demo(a.root)
    elif a.command=='prove':
        from .verification import verify
        result=verify(a.out)
    else: result=inspect_local(a.manifest,a.root,a.ledger,a.source,a.initialization,a.issue)
    print(json.dumps(result,indent=2,allow_nan=False))

if __name__=='__main__': main()
