"""Separate issuance/initialization/history/target time contracts; no data download."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

HOUR=timedelta(hours=1)


def utc_time(value: str | datetime) -> datetime:
    if isinstance(value,str):
        value=datetime.fromisoformat(value.replace('Z','+00:00'))
    if not isinstance(value,datetime) or value.utcoffset() is None:
        raise ValueError('Timezone-aware UTC time required')
    if value.utcoffset()!=timedelta(0):
        raise ValueError('Normalize to UTC before this contract boundary')
    return value.astimezone(timezone.utc)


def utc_hour(value: str | datetime) -> datetime:
    value=utc_time(value)
    if value.minute or value.second or value.microsecond:
        raise ValueError('Exact hourly UTC timestamp required')
    return value


def iso(value:datetime)->str:
    return utc_time(value).isoformat().replace('+00:00','Z')


def positive_integer(value:int,name:str)->int:
    if type(value) is not int or value<1:raise ValueError(f'{name}: positive integer required')
    return value


def hourly_range(start:str|datetime,end_exclusive:str|datetime)->tuple[datetime,...]:
    a,b=utc_hour(start),utc_hour(end_exclusive)
    if b<=a:raise ValueError('Empty or reversed time support')
    return tuple(a+j*HOUR for j in range(int((b-a)/HOUR)))


def validate_hourly_index(times:Iterable[str|datetime])->tuple[datetime,...]:
    result=tuple(utc_hour(t) for t in times)
    if not result or any(b-a!=HOUR for a,b in zip(result,result[1:])):
        raise ValueError('Complete, unique, strictly increasing hourly index required')
    return result


@dataclass(frozen=True)
class ForecastWindow:
    initialization:datetime
    history:tuple[datetime,...]
    targets:tuple[datetime,...]


def window(initialization:str|datetime,forecast_hours:int=240,history_hours:int=1)->ForecastWindow:
    t=utc_hour(initialization)
    positive_integer(forecast_hours,'forecast_hours');positive_integer(history_hours,'history_hours')
    return ForecastWindow(t,tuple(t-j*HOUR for j in range(history_hours,-1,-1)),
                          tuple(t+j*HOUR for j in range(1,forecast_hours+1)))


def evaluation_cohort()->tuple[ForecastWindow,...]:
    first,last=utc_hour('2025-01-01T00:00:00Z'),utc_hour('2026-01-01T00:00:00Z')
    return tuple(window(t) for t in hourly_range(first,last)[::6])


def audit_coverage(cohort:Iterable[ForecastWindow],available_times:Iterable[str|datetime])->dict:
    available=set(validate_hourly_index(available_times))
    cases=list(cohort);failures=[]
    for w in cases:
        missing_h=[iso(t) for t in w.history if t not in available]
        missing_y=[iso(t) for t in w.targets if t not in available]
        if missing_h or missing_y:
            failures.append({'init':iso(w.initialization),'missing_history_count':len(missing_h),
                             'missing_targets_count':len(missing_y),
                             'first_missing_history':missing_h[0] if missing_h else None,
                             'first_missing_target':missing_y[0] if missing_y else None})
    return {'cases':len(cases),'complete_cases':len(cases)-len(failures),'incomplete_cases':len(failures),
            'status':'PASS' if not failures else 'FAIL','failures':failures,
            'evidence':'timestamp_manifest_only_not_data_values'}


def validate_initial_inputs(w:ForecastWindow,issue:str|datetime,valid_times,available_times):
    issue=utc_time(issue)
    valid=tuple(utc_hour(t) for t in valid_times); avail=tuple(utc_time(t) for t in available_times)
    if len(valid)!=len(avail) or valid!=w.history:
        raise ValueError('Input timestamps must equal the declared history')
    if issue<w.initialization or any(v>w.initialization for v in valid):
        raise ValueError('Future physical input is forbidden')
    if any(a>issue for a in avail):raise ValueError('Input was unavailable at issuance')


def validate_tail_use(time:str|datetime,purpose:str):
    t=utc_hour(time)
    if purpose not in {'train','select','calibrate','evaluate'}:raise ValueError('Unknown data purpose')
    if utc_hour('2025-01-01T00:00:00Z')<=t<utc_hour('2026-01-10T19:00:00Z') and purpose!='evaluate':
        raise ValueError('Frozen final evaluation targets cannot be used for fitting/selection')
