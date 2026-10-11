"""Validate the reference registry and reproduce plan arithmetic; no weather data."""
from pathlib import Path
import argparse
import json
import platform
import numpy as np
from streamingcast.benchmark_contract import validate_catalog, storage_bytes, canonical_hash


def run(root: Path) -> dict:
    catalog = json.loads((root/'benchmarks/reference_scores.json').read_text())
    report = {'scope':'Reference-table validation, calendar/storage arithmetic and manufactured sampling example',
              'catalog': validate_catalog(catalog),
              'catalog_sha256': canonical_hash(catalog),
              'environment': {'python':platform.python_version(), 'numpy':np.__version__},
              'real_weather_arrays_read':False,'forecast_models_executed':False,
              'forecast_skill_approved':False}
    report['storage'] = {
        'G30_025deg_6h_1979_2022':storage_bytes(1979,2022,6,721,1440,30),
        'G30_1deg_6h_1979_2022':storage_bytes(1979,2022,6,181,360,30),
        'sp_025deg_6h_1979_2022':storage_bytes(1979,2022,6,721,1440,1),
        'D83_plus_rain_1deg_1h_5years_2018_2022':storage_bytes(2018,2022,1,181,360,84),
        'D83_plus_rain_025deg_1h_1979_2022':storage_bytes(1979,2022,1,721,1440,84),
    }
    report['documented_local_disk_bytes'] = 5477368824476
    report['documented_inventory_reinspected_here'] = False
    rank={}
    for step in (1,6):
        t=np.arange(0,24*30,step)
        x=np.column_stack([np.ones_like(t),np.cos(2*np.pi*t/24),np.sin(2*np.pi*t/24),np.cos(2*np.pi*t/12),np.sin(2*np.pi*t/12)])
        rank[str(step)]={'samples':len(t),'rank':int(np.linalg.matrix_rank(x,tol=1e-10)),
                         'columns':5,'scope':'one point and regular UTC sampling; global spatial constraints not evaluated'}
    report['sampling_manufactured'] = rank
    report['remaining_blocks'] = ['actual cache payload validation','per-model local re-evaluation','1h global inputs',
                                  'checkpoint and initialization lineage','observational precipitation/tidal validation']
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    report=run(args.root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report,indent=2,allow_nan=False))
