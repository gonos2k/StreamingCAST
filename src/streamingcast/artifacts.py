"""Local content-addressed outputs; never overwrite an installed object.
One filesystem + SQLite only. Hash verification detects later edits; it does not
protect against a malicious owner or make a distributed transaction atomic.
"""
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile
import numpy as np


class ArtifactStore:
    def __init__(self, root, max_bytes=256 * 1024**2):
        if type(max_bytes) is not int or max_bytes <= 0:
            raise ValueError("Positive integer artifact byte limit required")
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes

    def _path(self, digest):
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Artifact SHA-256 required")
        path = self.root / 'sha256' / digest[:2] / (digest + '.npz')
        if not path.resolve().is_relative_to(self.root) or path.is_symlink():
            raise ValueError("Artifact path escapes root or is a symlink")
        return path

    def verify(self, receipt):
        if not isinstance(receipt, dict) or set(receipt) != {'path', 'sha256', 'bytes'}:
            raise ValueError("Invalid artifact receipt")
        if type(receipt['bytes']) is not int or not 0 < receipt['bytes'] <= self.max_bytes:
            raise ValueError("Invalid artifact size")
        path = self._path(receipt['sha256'])
        if receipt['path'] != path.relative_to(self.root).as_posix():
            raise ValueError("Noncanonical artifact path")
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
        with os.fdopen(os.open(path, flags), 'rb') as handle:
            if os.fstat(handle.fileno()).st_size != receipt['bytes']:
                raise ValueError("Artifact size changed")
            raw = handle.read(self.max_bytes + 1)
        if len(raw) != receipt['bytes'] or sha256(raw).hexdigest() != receipt['sha256']:
            raise ValueError("Artifact content changed")
        return raw

    def put_npz(self, **arrays):
        if not arrays:
            raise ValueError("Empty artifact")
        for value in arrays.values():
            a = np.asarray(value)
            if a.dtype.hasobject or (a.dtype.kind in 'fc' and not np.isfinite(a).all()):
                raise ValueError("Pickle/nonfinite output forbidden")
        buffer = BytesIO()
        np.savez(buffer, **arrays)
        raw = buffer.getvalue()
        if len(raw) > self.max_bytes:
            raise ValueError("Artifact exceeds local adapter limit")
        digest = sha256(raw).hexdigest()
        path = self._path(digest)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Recheck after directory creation. Cooperative writers only.
        path = self._path(digest)
        receipt = {'path': path.relative_to(self.root).as_posix(),
                   'sha256': digest, 'bytes': len(raw)}
        fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.pending-')
        try:
            with os.fdopen(fd, 'wb') as handle:
                handle.write(raw); handle.flush(); os.fsync(handle.fileno())
            try:
                os.link(temp, path)  # same-filesystem atomic install-if-absent
            except FileExistsError:
                pass
            if hasattr(os, 'O_DIRECTORY'):
                directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
            self.verify(receipt)  # collision/corruption is never silently replaced
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        return receipt

    def load(self, receipt):
        raw = self.verify(receipt)
        with zipfile.ZipFile(BytesIO(raw)) as archive:
            if sum(i.file_size for i in archive.infolist()) > self.max_bytes:
                raise ValueError("Expanded artifact exceeds limit")
        with np.load(BytesIO(raw), allow_pickle=False) as data:
            return {name: data[name].copy() for name in data.files}

    def register(self, ledger, run_key, receipt, metadata=None):
        self.verify(receipt)  # repeat registration verifies bytes, not just DB body
        return ledger.commit_run(run_key, {'artifact': receipt, 'metadata': metadata or {}})

    def recovery_report(self, ledger):
        """Read-only inventory. No orphan is deleted automatically."""
        used, broken, legacy = set(), [], []
        for key, body in ledger.db.execute('SELECT key,body FROM runs'):
            result = json.loads(body)
            receipt = result.get('artifact')
            if not isinstance(receipt, dict):
                legacy.append(key); continue
            if isinstance(receipt.get('sha256'), str):
                used.add(receipt['sha256'])
            try:
                self.verify(receipt)
            except (ValueError, OSError) as error:
                broken.append({'run_key': key, 'error_type': type(error).__name__})
        present = {p.stem for p in self.root.glob('sha256/*/*.npz')}
        return {'orphan_sha256': sorted(present-used), 'broken_runs': broken,
                'legacy_runs_not_verified': legacy,
                'scope': 'quiescent local inventory; not distributed exactly-once'}
