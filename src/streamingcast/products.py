"""Trajectory-first rain aggregation. This does not calibrate a probability model."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from .time_contract import utc_time,utc_hour,validate_hourly_index,HOUR,iso

HOURLY_STATS={'point_estimate','conditional_mean','ensemble_mean','ensemble_trajectory','quantile','exceedance_probability'}


def probability(value):
    if isinstance(value,(bool,np.bool_)) or not isinstance(value,(int,float,np.integer,np.floating)):
        raise ValueError('A finite probability in [0,1] is required')
    p=float(value)
    if not np.isfinite(p) or not 0<=p<=1:raise ValueError('Probability outside [0,1]')
    return p


@dataclass(frozen=True)
class HourlyRain:
    values:np.ndarray
    ends:tuple[datetime,...]
    init:datetime
    conditioning_issue:datetime
    statistic:str
    unit:str='mm'
    ensemble_id:str|None=None
    member_ids:tuple[str,...]=()
    probability_level:float|None=None
    trajectory_certified:bool=False  # declaration, not a proof of meteorological calibration

    def __post_init__(self):
        ends=validate_hourly_index(self.ends)
        init=utc_hour(self.init);issue=utc_time(self.conditioning_issue)
        if issue<init or ends[0]<=init:raise ValueError('Bad initialization/forecast time relationship')
        if self.statistic not in HOURLY_STATS:raise ValueError('Unknown forecast statistic')
        if self.unit!=('1' if self.statistic=='exceedance_probability' else 'mm'):
            raise ValueError('Wrong product unit')
        raw=np.asarray(self.values)
        if raw.dtype.kind not in 'fiu':raise ValueError('Numeric values required')
        a=np.array(raw,dtype=np.float64,copy=True)
        axis=1 if self.statistic=='ensemble_trajectory' else 0
        if a.ndim<=axis or a.shape[axis]!=len(ends) or a.size==0:
            raise ValueError('Values and hourly interval count disagree')
        if not np.isfinite(a).all() or np.any(a<0):
            raise ValueError('No nonfinite/negative precipitation or silently dropped members')
        if self.statistic=='ensemble_trajectory':
            if not self.ensemble_id or not self.trajectory_certified:raise ValueError('Explicit trajectory provenance required')
            if len(self.member_ids)!=a.shape[0] or len(set(self.member_ids))!=a.shape[0] or any(not s for s in self.member_ids):
                raise ValueError('Unique ordered member IDs required for every trajectory')
        elif self.member_ids:raise ValueError('Only member trajectories carry a member dimension')
        if self.statistic=='quantile':probability(self.probability_level)
        elif self.probability_level is not None:raise ValueError('Probability level belongs only to a quantile')
        if self.statistic=='exceedance_probability' and np.any(a>1):raise ValueError('Probability exceeds one')
        a.setflags(write=False)
        object.__setattr__(self,'values',a);object.__setattr__(self,'ends',ends)
        object.__setattr__(self,'init',init);object.__setattr__(self,'conditioning_issue',issue)


@dataclass(frozen=True)
class Accumulation:
    values:np.ndarray
    start:datetime
    end:datetime
    conditioning_issue:datetime
    statistic:str
    ensemble_id:str|None
    member_ids:tuple[str,...]

    def __post_init__(self):
        start,end=utc_hour(self.start),utc_hour(self.end)
        issue=utc_time(self.conditioning_issue)
        if end<=start:raise ValueError('Nonempty accumulation interval required')
        if self.statistic not in {'point_estimate','conditional_mean','ensemble_mean','ensemble_trajectory'}:
            raise ValueError('Only additive statistics may be accumulated')
        values=np.array(self.values,dtype=np.float64,copy=True)
        if values.size==0 or not np.isfinite(values).all() or (values<0).any():
            raise ValueError('Finite nonnegative accumulated values required')
        if self.statistic=='ensemble_trajectory':
            if not self.ensemble_id or values.ndim<1 or len(self.member_ids)!=values.shape[0] or len(set(self.member_ids))!=values.shape[0]:
                raise ValueError('Accumulation lost member identity')
        elif self.member_ids:raise ValueError('Point/mean accumulation has no member axis')
        values.setflags(write=False)
        object.__setattr__(self,'values',values)
        object.__setattr__(self,'start',start);object.__setattr__(self,'end',end)
        object.__setattr__(self,'conditioning_issue',issue)

    def metadata(self)->dict:
        return {'interval_start':iso(self.start),'interval_end':iso(self.end),'interval':'(start,end]',
                'conditioning_issue_time':iso(self.conditioning_issue),'statistic':self.statistic,
                'ensemble_id':self.ensemble_id,'member_ids':list(self.member_ids),'unit':'mm',
                'forecast_skill_or_calibration_verified':False}


def concatenate_hours(chunks:list[HourlyRain])->HourlyRain:
    if not chunks:raise ValueError('At least one chunk required')
    first=chunks[0]
    for c in chunks:
        if (c.init,c.conditioning_issue,c.statistic,c.unit,c.ensemble_id,c.member_ids,c.probability_level,c.trajectory_certified)!=(
             first.init,first.conditioning_issue,first.statistic,first.unit,first.ensemble_id,first.member_ids,first.probability_level,first.trajectory_certified):
            raise ValueError('Cannot mix issuance, ensemble identity/order or product statistics')
    axis=1 if first.statistic=='ensemble_trajectory' else 0
    return HourlyRain(np.concatenate([c.values for c in chunks],axis=axis),tuple(t for c in chunks for t in c.ends),
                       first.init,first.conditioning_issue,first.statistic,first.unit,first.ensemble_id,
                       first.member_ids,first.probability_level,first.trajectory_certified)


def accumulate(hourly:HourlyRain,*,start:str|datetime,end:str|datetime)->Accumulation:
    # Revalidate public arrays/metadata even if callers circumvented frozen dataclasses.
    hourly=HourlyRain(**{k:getattr(hourly,k) for k in hourly.__dataclass_fields__})
    if hourly.statistic in {'quantile','exceedance_probability'}:
        raise ValueError('Marginal quantiles/probabilities cannot be summed into cumulative ones')
    start,end=utc_hour(start),utc_hour(end)
    if end<=start:raise ValueError('Positive accumulation interval required')
    expected=tuple(start+j*HOUR for j in range(1,int((end-start)/HOUR)+1))
    indices=[i for i,t in enumerate(hourly.ends) if start<t<=end]
    if tuple(hourly.ends[i] for i in indices)!=expected:
        raise ValueError('Incomplete accumulation interval; missing hour is not zero rain')
    axis=1 if hourly.statistic=='ensemble_trajectory' else 0
    with np.errstate(over='raise',invalid='raise'):
        values=np.take(hourly.values,indices,axis=axis).sum(axis=axis,dtype=np.float64)
    if not np.isfinite(values).all():raise FloatingPointError('Cumulative precipitation overflow')
    return Accumulation(values,start,end,hourly.conditioning_issue,hourly.statistic,hourly.ensemble_id,hourly.member_ids)


def summarize_members(total:Accumulation,*,statistic:str,level:float|None=None,threshold_mm:float|None=None)->dict:
    if statistic!='quantile' and level is not None:raise ValueError('Extraneous quantile level')
    if statistic!='exceedance_probability' and threshold_mm is not None:raise ValueError('Extraneous exceedance threshold')
    if total.statistic!='ensemble_trajectory' or len(total.member_ids)!=total.values.shape[0]:
        raise ValueError('A distribution requires complete member trajectories, not point values')
    if not np.isfinite(total.values).all():raise ValueError('Invalid accumulated member')
    meta=total.metadata();meta.pop('member_ids');meta.update({'statistic':statistic,'effective_members':len(total.member_ids)})
    if statistic=='mean':
        result=total.values.mean(axis=0)
    elif statistic=='quantile':
        p=probability(level)
        result=np.quantile(total.values,p,axis=0,method='inverted_cdf')
        meta.update({'probability_level':p,'quantile_definition':'empirical_inverse_cdf_equal_weights'})
    elif statistic=='exceedance_probability':
        if isinstance(threshold_mm,bool) or threshold_mm is None or not np.isfinite(threshold_mm) or threshold_mm<0:
            raise ValueError('Nonnegative finite threshold required')
        result=(total.values>threshold_mm).mean(axis=0)
        meta.update({'threshold_mm':float(threshold_mm),'comparison':'>','unit':'1'})
    else:raise ValueError('Unsupported summary')
    if not np.isfinite(result).all():raise FloatingPointError('Summary overflow')
    return {'metadata':meta,'values':np.asarray(result).tolist()}
