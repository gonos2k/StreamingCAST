"""These tests reproduce both strengths and defects; PASS is NOT model approval."""
import json
from pathlib import Path
import subprocess,sys,os
import numpy as np
import pytest
from audit_checks import default_source

@pytest.fixture(scope='session')
def r(tmp_path_factory):
    out=tmp_path_factory.mktemp('audit')/'result.json'
    env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    done=subprocess.run([sys.executable,str(Path(__file__).with_name('audit_checks.py')),'--source',str(default_source()),'--out',str(out)],env=env,capture_output=True,text=True,timeout=90)
    assert done.returncode==0,done.stderr
    return json.loads(out.read_text())

def test_existing_diagnostic_runs_fail_closed_only_without_optimization(r):
    assert r['optimized_gate']['normal']['returncode']!=0
    assert r['optimized_gate']['optimized']['returncode']==0
    assert json.loads(r['optimized_gate']['optimized']['stdout'])['gradcheck'] is False

def test_reproduce_mutable_public_snapshot(r):
    s=r['snapshot_mutability']
    assert s['accepted_mutable_sequence'] and s['fingerprint_changed']
    assert s['fresh_constructor_rejects_same_content']

def test_reproduce_unavailable_file_blocks_asof_inspect(r):
    assert r['asof_inspection']['unchanged_eligible_snapshot_still_available']
    assert r['asof_inspection']['reinspect_after_unavailable_record'].startswith('FileNotFoundError')

def test_positive_q_does_not_imply_scalar_comparison_principle(r):
    q=r['moisture_comparison'];assert q['next_q_gkg']>0 and q['autograd_dqnext_dq']<0
    assert q['autograd_dqnext_dq']==pytest.approx(q['analytical_dqnext_dq'],abs=1e-12)
    assert q['continuous_scalar_dqnext_dq']>0

@pytest.mark.parametrize('index',[0,1])
def test_reproduce_finite_values_nonfinite_gradient(r,index):
    s=r['domain_and_clock']['manufactured_extreme_source'][index]
    assert s['initial_validation_passed'] and s['forward_finite']
    assert not s['all_gradients_finite'] and s['nan_gradient_elements']>0

def test_hour_is_missing_from_checked_boundary(r):
    assert r['domain_and_clock']['nan_hour_not_in_validator']

def test_disclosed_subsaturated_sink_is_not_negligible_in_long_rollout(r):
    s=r['subsat_drizzle']['cases'][1]
    assert s['initial_ratio']==.5 and s['rain_240h_mm']>2

def test_dt_one_matches_original(r):
    assert r['coupled_limit']['dt1_matches_original_max_abs']<1e-12

def test_coupled_reference_is_numerically_resolved(r):
    s=r['coupled_limit'];assert s['reference_tolerance_change']<1e-9
    assert s['reference_fd_halving_relative_change']<1e-6

def test_split_converges_first_order_to_separate_coupled_problem(r):
    rows=r['coupled_limit']['results']
    assert all(.95<x['value_order_to_next']<1.05 for x in rows[:-1])
    assert all(abs(b['theta_error_K'])<abs(a['theta_error_K']) for a,b in zip(rows,rows[1:]))

def test_discrete_sensitivity_converges_but_is_not_continuous_sensitivity(r):
    rows=r['coupled_limit']['results']
    assert rows[0]['sensitivity_relative_error']>.03
    assert all(b['sensitivity_relative_error']<a['sensitivity_relative_error'] for a,b in zip(rows,rows[1:]))

@pytest.mark.parametrize('index',range(9))
def test_extended_discrete_derivative_consistency(r,index):
    d=r['extended_derivatives'][index]
    assert d['jvp_fd_relative']<1e-7 and d['adjoint_relative']<1e-10

def test_budget_identity_and_its_tangent(r):
    assert r['tangent_budgets']['max_primal_residual']<1e-12
    assert r['tangent_budgets']['max_tangent_residual']<1e-12

def test_parameter_excitation_is_needed(r):
    d=r['identifiability'];assert d['original_training_distribution']['rank']==3
    assert d['exactly_dry_no_source']['rank']==2
    assert d['exactly_dry_no_source']['p0_column_norm']==0

def test_sqlite_read_snapshot_and_duplicate(r):
    d=r['sqlite'];assert [d['count_before'],d['count_during_other_connection_commit'],d['count_after_end']]==[2,2,3]
    assert d['first_insert'] and not d['duplicate_insert'] and d['conflicting_result_rejected']

def test_disclosed_file_ledger_separation(r):
    d=r['artifact_ledger'];assert d['file_overwritten']
    assert not d['old_receipt_matches_current_bytes'] and not d['old_receipt_duplicate_result']
