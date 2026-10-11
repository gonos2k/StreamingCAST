"""One canonical schema; conversion/regridding remain local adapter responsibilities."""
import hashlib
import json

LEVELS = (50,100,150,200,250,300,400,500,600,700,850,925,1000)
D83 = tuple((f"{v}_{p}hPa", u) for v,u in
            (("t","K"),("z","m2 s-2"),("u","m s-1"),("v","m s-1"),
             ("omega","Pa s-1"),("q","kg kg-1")) for p in LEVELS) + (
    ("t2m","K"),("msl","Pa"),("u10","m s-1"),("v10","m s-1"),("sp","Pa"))
TOY = (("theta","K_anomaly_280K"),("q","g kg-1"),("u","m s-1"),("v","m s-1"))
SCHEMAS = {"d83-v1": D83, "toy-column-v1": TOY}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def schema_hash(name):
    if name not in SCHEMAS:
        raise ValueError("Unknown schema")
    return digest(SCHEMAS[name])
