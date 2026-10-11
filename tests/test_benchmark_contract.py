"""Synthetic checks of evidence/metric contracts; not weather skill certification."""
from copy import deepcopy
from pathlib import Path
import json
import numpy as np
import pytest
from streamingcast.benchmark_contract import (
    BenchmarkContractError, validate_catalog, require_matched_local, case_area_mse,
    paired_rmse_check, storage_bytes,
)

ROOT=Path(__file__).resolve().parents[1]


def contract():
    return {
      'evidence_class':'local_recomputed','holdout_independence_checked':True,
      'protocol_id':'synthetic-guard-test','variable':'t2m','units':'K','lead_hours':24,
      'temporal_statistic':'instantaneous','forecast_statistic':'deterministic_point',
      'ensemble_members':1,'init_sample_sha256':'1'*64,'target_sha256':'2'*64,
      'initial_analysis':'same-synthetic-input','grid_sha256':'3'*64,
      'mask_sha256':'4'*64,'weights_sha256':'5'*64,'climatology_id':'not-applicable-rmse',
      'aggregation':'mean_case_area_mse_then_sqrt','model_sha256':'6'*64,
    }


def test_published_catalog_counts_and_precise_values():
    c=json.loads((ROOT/'benchmarks/reference_scores.json').read_text())
    r=validate_catalog(c)
    assert r['counts']=={'RMSE':60,'ROCSS':3}
    assert not r['forecast_skill_approved']
    assert len(c['missing_records'])==4
    gc=[x for x in c['records'] if x['model']=='GraphCast' and x['variable']=='geopotential']
    assert len(gc)==1 and gc[0]['value']==39.78 and gc[0]['units']=='m2 s-2'
    assert all(x['variable'] not in ('sp','msl') for x in c['records'])


@pytest.mark.parametrize('bad',[float('nan'),float('inf'),None,True,-1])
def test_bad_rmse_catalog_rejected(bad):
    c=json.loads((ROOT/'benchmarks/reference_scores.json').read_text())
    c['records'][0]['value']=bad
    with pytest.raises(BenchmarkContractError): validate_catalog(c)


def test_duplicate_catalog_rejected():
    c=json.loads((ROOT/'benchmarks/reference_scores.json').read_text())
    c['records'].append(deepcopy(c['records'][0]))
    with pytest.raises(BenchmarkContractError):validate_catalog(c)


@pytest.mark.parametrize('key,new',[
    ('units','hPa'),('lead_hours',120),('grid_sha256','a'*64),
    ('init_sample_sha256','a'*64),('target_sha256','a'*64),('mask_sha256','a'*64),
    ('initial_analysis','different-analysis'),('temporal_statistic','24h_sum'),
    ('forecast_statistic','ensemble_mean'),('climatology_id','different-climatology'),
    ('aggregation','mean_rmse'),('ensemble_members',50),
])
def test_unmatched_conditions_rejected(key,new):
    a,b=contract(),contract();b[key]=new
    with pytest.raises(BenchmarkContractError):require_matched_local(a,b)


@pytest.mark.parametrize('key,value',[
    ('evidence_class','primary_paper_table_transcription'),
    ('holdout_independence_checked',False),('target_sha256',None),
    ('model_sha256','unknown'),
])
def test_incomplete_or_external_evidence_rejected(key,value):
    a,b=contract(),contract();a[key]=value
    with pytest.raises(BenchmarkContractError): require_matched_local(a,b)


def test_different_checkpoints_allowed_for_equal_protocol():
    a,b=contract(),contract();b['model_sha256']='a'*64
    require_matched_local(a,b)


def test_sqrt_after_case_mean_not_mean_of_rmse():
    p=np.array([[0.,0.],[2.,2.]])
    m=case_area_mse(p,np.zeros_like(p),np.ones(2),np.ones_like(p,dtype=bool))
    assert np.sqrt(m.mean())==pytest.approx(np.sqrt(2))
    assert np.sqrt(m).mean()==1


def test_area_mask_and_missing_prediction():
    p=np.array([[1.,2.,np.nan],[2.,1.,np.nan]])
    truth=np.zeros_like(p);mask=np.array([[True,True,False]]*2)
    got=case_area_mse(p,truth,np.array([1.,3.,1.]),mask)
    assert np.allclose(got,[3.25,1.75])
    mask[0,2]=True
    with pytest.raises(BenchmarkContractError):case_area_mse(p,truth,np.ones(3),mask)


def test_empty_initialization_and_overflow_rejected():
    p=np.zeros((2,3));mask=np.ones_like(p,dtype=bool);mask[0]=False
    with pytest.raises(BenchmarkContractError):case_area_mse(p,p,np.ones(3),mask)
    with pytest.raises(BenchmarkContractError):case_area_mse(p+1e300,p,np.ones(3),np.ones_like(mask))


def test_paired_bootstrap_checks_but_never_releases_model():
    a,b=contract(),contract();ids=np.repeat(np.arange(12),2)
    base=np.linspace(.7,1.3,24)
    good=paired_rmse_check(base*.81,base,ids,a,b,resamples=300)
    assert good['metric_status']=='IMPROVED'
    assert good['relative_rmse_change']==pytest.approx(-.1)
    assert not good['forecast_skill_approved']
    bad=paired_rmse_check(base*1.21,base,ids,a,b,resamples=300)
    assert bad['metric_status']=='REGRESSION'
    same=paired_rmse_check(base,base,ids,a,b,resamples=300)
    assert same['metric_status']=='NONINFERIOR'


def test_too_few_blocks_not_a_pass():
    got=paired_rmse_check([.1]*12,[1.]*12,[0]*12,contract(),contract(),resamples=300)
    assert got['metric_status']=='INSUFFICIENT_BLOCKS'


@pytest.mark.parametrize('kwargs',[{'margin':True},{'margin':float('nan')},{'resamples':True},{'alpha':0}])
def test_bad_bootstrap_arguments(kwargs):
    with pytest.raises(BenchmarkContractError):
        paired_rmse_check([1.]*12,[1.]*12,list(range(12)),contract(),contract(),**kwargs)


def test_actual_inventory_calendar_arithmetic():
    result=storage_bytes(1979,2022,6,721,1440,30)
    assert result['timesteps']==64284
    assert result['bytes']==64284*721*1440*30*4
    assert storage_bytes(2020,2020,6,1,1,1)['timesteps']==1464


@pytest.mark.parametrize('args',[(True,2022,6,1,1,30),(2022,1979,6,1,1,30),(1979,2022,5,1,1,30),(1979,2022,6,0,1,30)])
def test_bad_storage_arguments(args):
    with pytest.raises(BenchmarkContractError): storage_bytes(*args)


def test_hourly_semidiurnal_rank_counterexample():
    ranks=[]
    for dt in [1,6]:
        t=np.arange(0,24*30,dt)
        design=np.stack([np.ones_like(t),np.cos(2*np.pi*t/24),np.sin(2*np.pi*t/24),np.cos(2*np.pi*t/12),np.sin(2*np.pi*t/12)],-1)
        ranks.append(np.linalg.matrix_rank(design,tol=1e-10))
    assert ranks==[5,4]


def test_target_contract_keeps_hourly_and_d83_blocked():
    t=json.loads((ROOT/'benchmarks/development_targets.json').read_text())
    assert t['profiles']['global-g29-p6h-research']['instantaneous_channels']==29
    assert t['profiles']['global-d83-p1h-target']['status']=='BLOCKED_MISSING_GLOBAL_HOURLY_INPUTS'
    assert not t['approval']['published_table_can_approve']
    assert not t['future_test']['local_data_available']
