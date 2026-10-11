"""Durable metadata ledger. Receipt time and source availability are separate."""
from dataclasses import dataclass, asdict
from datetime import timedelta
from pathlib import Path
import json
import re
import sqlite3
from .schema import canonical, digest, schema_hash
from .time_contract import utc_hour, utc_time, iso


@dataclass(frozen=True)
class Record:
    event_id: str
    source: str
    revision: int
    valid_time: str
    available_time: str
    received_time: str
    path: str
    sha256: str
    schema: str
    schema_sha256: str
    grid_sha256: str

    def __post_init__(self):
        if any(not isinstance(s,str) or not s for s in
               (self.event_id,self.source,self.path)):
            raise ValueError("Nonempty identifiers/path required")
        if type(self.revision) is not int or self.revision < 0:
            raise ValueError("Nonnegative integer revision required")
        v,a,r=utc_hour(self.valid_time),utc_time(self.available_time),utc_time(self.received_time)
        if not v <= a <= r:
            raise ValueError("Analysis records require valid <= available <= received")
        if any(not isinstance(h,str) or not re.fullmatch(r"[0-9a-f]{64}",h)
               for h in (self.sha256,self.grid_sha256)):
            raise ValueError("SHA-256 required")
        if self.schema_sha256 != schema_hash(self.schema):
            raise ValueError("Schema hash mismatch")
        for key,val in (("valid_time",v),("available_time",a),("received_time",r)):
            object.__setattr__(self,key,iso(val))


@dataclass(frozen=True)
class Snapshot:
    initialization: str
    issue: str
    records: tuple[Record,...]

    def __post_init__(self):
        t,cut=utc_hour(self.initialization),utc_time(self.issue)
        if cut<t or len(self.records)!=2:
            raise ValueError("Snapshot requires two records and a valid issue time")
        if tuple(utc_hour(r.valid_time) for r in self.records)!=(t-timedelta(hours=1),t):
            raise ValueError("Snapshot history must be [-1h,0h]")
        if any(utc_time(r.received_time)>cut or utc_time(r.available_time)>cut for r in self.records):
            raise ValueError("Snapshot contains data unavailable at issue")
        if len({(r.source,r.schema,r.schema_sha256,r.grid_sha256) for r in self.records})!=1:
            raise ValueError("Mixed source, schema or geometry")
        object.__setattr__(self,"initialization",iso(t));object.__setattr__(self,"issue",iso(cut))

    @property
    def fingerprint(self):
        return digest(asdict(self))

    def run_key(self, model_sha256, configuration):
        if not re.fullmatch(r"[0-9a-f]{64}",model_sha256):
            raise ValueError("Model SHA-256 required")
        return digest({"snapshot":self.fingerprint,"model":model_sha256,"config":configuration})


class Ledger:
    """Single SQLite database; not a distributed exactly-once service."""
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path,timeout=10,isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS records (event TEXT PRIMARY KEY, source TEXT, valid TEXT, revision INTEGER, body TEXT, UNIQUE(source,valid,revision))")
        self.db.execute("CREATE TABLE IF NOT EXISTS runs (key TEXT PRIMARY KEY, body TEXT)")

    def close(self):
        self.db.close()

    def ingest(self, record: Record):
        body=canonical(asdict(record))
        self.db.execute("BEGIN IMMEDIATE")
        try:
            old=self.db.execute("SELECT body FROM records WHERE event=?",(record.event_id,)).fetchone()
            if old:
                if old[0] != body: raise ValueError("Conflicting event replay")
                self.db.execute("COMMIT");return False
            self.db.execute("INSERT INTO records VALUES (?,?,?,?,?)",
                            (record.event_id,record.source,record.valid_time,record.revision,body))
            self.db.execute("COMMIT");return True
        except Exception:
            self.db.execute("ROLLBACK");raise

    def snapshot(self, source, initialization, issue):
        t,cut=utc_hour(initialization),utc_time(issue)
        if cut<t: raise ValueError("Issue precedes initialization")
        chosen=[]
        self.db.execute("BEGIN")
        try:
            for valid in (t-timedelta(hours=1),t):
                rows=self.db.execute("SELECT body FROM records WHERE source=? AND valid=? ORDER BY revision DESC",
                                     (source,iso(valid))).fetchall()
                eligible=[Record(**json.loads(row[0])) for row in rows]
                eligible=[r for r in eligible if utc_time(r.available_time)<=cut and utc_time(r.received_time)<=cut]
                if not eligible: raise ValueError("Missing data at the issuance cutoff")
                chosen.append(eligible[0])
            result=Snapshot(iso(t),iso(cut),tuple(chosen))
            self.db.execute("COMMIT");return result
        except Exception:
            self.db.execute("ROLLBACK");raise

    def commit_run(self,key,result):
        """Atomically register small output metadata, not physical prediction arrays."""
        if not re.fullmatch(r"[0-9a-f]{64}",key): raise ValueError("Run key required")
        body=canonical(result)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            old=self.db.execute("SELECT body FROM runs WHERE key=?",(key,)).fetchone()
            if old:
                if old[0]!=body: raise ValueError("Different result for same frozen run")
                self.db.execute("COMMIT");return False
            self.db.execute("INSERT INTO runs VALUES (?,?)",(key,body))
            self.db.execute("COMMIT");return True
        except Exception:
            self.db.execute("ROLLBACK");raise
