#!/usr/bin/env python3
"""Inspect annual local Zarr v2 cache structure without loading array data."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys

META = {".zarray", ".zattrs", ".zgroup", ".zmetadata"}


def _read_json(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def _months_progress(path):
    """Return the month numbers recorded in a text or JSON progress marker."""
    raw = path.read_text(encoding="utf-8")
    try:
        value = json.loads(raw)
        if isinstance(value, dict):
            value = value.get("completed_months", value.get("months", []))
        if isinstance(value, list):
            return {int(m) for m in value if str(m).isdigit() and 1 <= int(m) <= 12}
    except (ValueError, TypeError):
        pass
    found = set()
    for token in re.split(r"[\s,]+", raw.strip()):
        match = re.fullmatch(r"(?:\d{4}[-/])?(\d{1,2})", token)
        if match and 1 <= int(match.group(1)) <= 12:
            found.add(int(match.group(1)))
    return found


def _metadata_digest(store, paths):
    digest = hashlib.sha256()
    for path in sorted(set(paths)):
        digest.update(path.relative_to(store).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _metadata_paths(store):
    return sorted(Path(directory) / name
                  for directory, _, names in os.walk(store)
                  for name in names if name in META)


def _chunk_inventory(array_path, meta):
    shape, chunks = meta["shape"], meta["chunks"]
    counts = [math.ceil(s / c) for s, c in zip(shape, chunks)]
    expected = math.prod(counts) if counts else 1
    sep = meta.get("dimension_separator", ".")
    pattern = re.compile(r"\d+(?:[./]\d+)*\Z")
    seen, empty, byte_count, unexpected, examples = set(), 0, 0, 0, []
    for path in array_path.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(array_path).as_posix()
        if rel in META:
            continue
        key = rel.replace("/", ".")
        parts = key.split(".")
        valid = (pattern.fullmatch(rel) and (sep == "." and "/" not in rel or
                  sep == "/" and "." not in rel) and len(parts) == len(counts))
        if not counts:
            valid = rel == "0"
        if valid:
            indices = tuple(map(int, parts))
            valid = (all(i < n for i, n in zip(indices, counts))
                     and rel == sep.join(map(str, indices)))
        if not valid or indices in seen:
            unexpected += 1
            if len(examples) < 5:
                examples.append(rel)
            continue
        seen.add(indices)
        size = path.stat().st_size
        byte_count += size
        empty += size == 0
    return {"expected": expected, "present": len(seen), "missing": max(0, expected - len(seen)),
            "empty": empty, "bytes": byte_count, "unexpected": unexpected,
            "unexpected_examples": examples}


def inspect(root, start_year=1979, end_year=2022, check_chunks=False):
    if start_year < 0 or end_year < start_year:
        raise ValueError("invalid year range")
    root = Path(root).expanduser().resolve()
    report = {"root": str(root), "years": [], "missing_stores": [], "errors": [],
              "integrity_scope": "Zarr metadata and optional chunk inventory only; payload integrity and D83 are not verified."}
    for year in range(start_year, end_year + 1):
        candidates = [root / f"era5_{year}.zarr", root / f"{year}.zarr", root / str(year)]
        store = next((p for p in candidates if p.is_dir()), None)
        if store is None:
            report["missing_stores"].append(year)
            report["errors"].append(f"{year}: annual store missing")
            continue
        item = {"year": year, "path": str(store), "metadata_sha256": None,
                "arrays": [], "markers": {}}
        try:
            group = _read_json(store / ".zgroup")
            if not isinstance(group, dict) or group.get("zarr_format") != 2:
                raise ValueError("expected a Zarr v2 group")
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            report["errors"].append(f"{year}: invalid or missing .zgroup ({exc})")
        for marker in ("_DONE", "_PROGRESS"):
            item["markers"][marker] = (store / marker).is_file()
        if not item["markers"]["_DONE"]:
            report["errors"].append(f"{year}: _DONE marker missing")
        progress = store / "_PROGRESS"
        if not progress.is_file() or _months_progress(progress) != set(range(1, 13)):
            report["errors"].append(f"{year}: _PROGRESS does not record all 12 months")
        consolidated = store / ".zmetadata"
        entries = {}
        try:
            paths = _metadata_paths(store)
            if consolidated.is_file():
                doc = _read_json(consolidated)
                if not isinstance(doc, dict) or doc.get("zarr_consolidated_format") != 1:
                    raise ValueError("expected consolidated Zarr v2 metadata")
                entries = doc.get("metadata")
                if not isinstance(entries, dict):
                    raise ValueError("metadata must be an object")
                local_keys = {p.relative_to(store).as_posix() for p in paths if p != consolidated}
                if set(entries) != local_keys:
                    raise ValueError("consolidated metadata entries differ from local metadata files")
                for key, value in entries.items():
                    path = Path(key)
                    if path.is_absolute() or ".." in path.parts or path.name not in META:
                        raise ValueError("invalid metadata path")
                    if not (store / path).resolve().is_relative_to(store.resolve()):
                        raise ValueError("metadata path leaves store")
                    if _read_json(store / path) != value:
                        raise ValueError(f"stale consolidated metadata: {key}")
            array_meta_paths = sorted(store / key for key in entries if Path(key).name == ".zarray")
            if not consolidated.is_file():
                array_meta_paths = [p for p in paths if p.name == ".zarray"]
            item["metadata_sha256"] = _metadata_digest(store, paths)
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            report["errors"].append(f"{year}: invalid consolidated metadata ({exc})")
            array_meta_paths = []
        if not array_meta_paths:
            report["errors"].append(f"{year}: no arrays found")
        for metadata_path in array_meta_paths:
            rel = metadata_path.parent.relative_to(store).as_posix()
            try:
                meta = _read_json(metadata_path)
                if not isinstance(meta, dict) or meta.get("zarr_format") != 2:
                    raise ValueError("expected a Zarr v2 metadata object")
                shape, chunks = meta.get("shape"), meta.get("chunks")
                dtype = meta.get("dtype")
                attrs_path = metadata_path.parent / ".zattrs"
                attrs = _read_json(attrs_path) if attrs_path.is_file() else {}
                if (not isinstance(shape, list) or not isinstance(chunks, list) or len(shape) != len(chunks)
                        or any(type(n) is not int or n < 0 for n in shape)
                        or any(type(n) is not int or n <= 0 for n in chunks)
                        or not isinstance(dtype, str) or not dtype or not isinstance(attrs, dict)):
                    raise ValueError("invalid shape, chunks, or dtype")
                if meta.get("dimension_separator", ".") not in (".", "/"):
                    raise ValueError("invalid dimension_separator")
                array = {"name": rel, "shape": shape, "chunks": chunks, "dtype": dtype,
                         "attrs": attrs, "units": attrs.get("units")}
                if check_chunks:
                    array["chunk_inventory"] = _chunk_inventory(metadata_path.parent, meta)
                    inv = array["chunk_inventory"]
                    if inv["missing"] or inv["empty"] or inv["unexpected"]:
                        report["errors"].append(f"{year}/{rel}: chunk inventory has missing, empty, or unexpected chunks")
                item["arrays"].append(array)
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                report["errors"].append(f"{year}/{rel}: invalid metadata ({exc})")
        report["years"].append(item)
    report["ok"] = not report["errors"]
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--start-year", type=int, default=1979)
    parser.add_argument("--end-year", type=int, default=2022)
    parser.add_argument("--check-chunks", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.start_year < 0 or args.end_year < 0 or args.start_year > args.end_year:
        parser.error("years must be nonnegative and start-year must not exceed end-year")
    root = args.root.expanduser().resolve()
    if args.out:
        out = args.out.expanduser().resolve()
        if out == root or root in out.parents:
            parser.error("--out must be outside the input root")
    report = inspect(root, args.start_year, args.end_year, args.check_chunks)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        output_path = args.out.expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
