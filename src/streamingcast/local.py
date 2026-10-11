"""Offline NPZ adapter. No remote fetch, pickle, implicit unit conversion or upload."""
from pathlib import Path
from hashlib import sha256
from io import BytesIO
import json
import os
import tempfile
import numpy as np
from .schema import SCHEMAS
from .stream import Record


def read_record(record: Record, root, max_bytes=256*1024**2):
    root=Path(root).resolve()
    path=(root/record.path).resolve()
    if not path.is_relative_to(root): raise ValueError("Data path escapes local root")
    if path.stat().st_size>max_bytes: raise ValueError("File exceeds adapter limit")
    raw=path.read_bytes()
    if sha256(raw).hexdigest()!=record.sha256: raise ValueError("Input content changed")
    # Validate exactly the bytes that were hashed: no second path read (TOCTOU).
    import zipfile
    with zipfile.ZipFile(BytesIO(raw)) as z:
        if sum(i.file_size for i in z.infolist())>max_bytes:
            raise ValueError("Expanded file exceeds adapter limit")
    with np.load(BytesIO(raw),allow_pickle=False) as data:
        if set(data.files)!={"state","mask","channels","units"}:
            raise ValueError("Expected state/mask/channels/units arrays only")
        state,mask=data["state"],data["mask"]
        names=tuple(data["channels"].tolist());units=tuple(data["units"].tolist())
        contract=SCHEMAS[record.schema]
        if names!=tuple(n for n,u in contract) or units!=tuple(u for n,u in contract):
            raise ValueError("Channel order or units mismatch; convert explicitly offline")
        if state.dtype.kind!='f' or state.ndim!=2 or state.shape[1]!=len(contract) or not state.size:
            raise ValueError("Expected floating [point,channel] state")
        if mask.dtype!=np.bool_ or mask.shape!=state.shape:
            raise ValueError("Explicit boolean mask with matching shape required")
        if not mask.any(axis=0).all() or not np.isfinite(state[mask]).all():
            raise ValueError("Empty channel or invalid unmasked value")
        if np.isinf(state).any(): raise ValueError("Infinity is never a missing marker")
        return state.copy(),mask.copy()


def read_manifest(path):
    records=json.loads(Path(path).read_text())
    if not isinstance(records,list) or not records: raise ValueError("Nonempty record list required")
    return tuple(Record(**r) for r in records)


def atomic_npz(path, **arrays):
    """Local forecast/restart artifact. Atomic replacement, separate from the run ledger."""
    dest=Path(path);dest.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=dest.parent,prefix='.'+dest.name)
    try:
        with os.fdopen(fd,'wb') as handle:
            np.savez(handle,**arrays);handle.flush();os.fsync(handle.fileno())
        os.replace(tmp,dest)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
