import json
from pathlib import Path
import unittest

from scripts.inspect_era5_cache import inspect, main


def make_store(root: Path, year=2001, shape=(3, 3), chunks=(2, 2)):
    store = root / f"era5_{year}.zarr"
    array = store / "surface" / "temperature"
    array.mkdir(parents=True)
    (store / ".zgroup").write_text('{"zarr_format":2}')
    (store / "_DONE").touch()
    (store / "_PROGRESS").write_text(json.dumps({"completed_months": list(range(1, 13))}))
    (array / ".zarray").write_text(json.dumps({
        "zarr_format": 2, "shape": list(shape), "chunks": list(chunks),
        "dtype": "<f4", "compressor": None, "fill_value": 0,
        "order": "C", "filters": None,
    }))
    (array / ".zattrs").write_text(json.dumps({"units": "K", "long_name": "temperature"}))
    return store, array


class Era5CacheTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_inventory_success_includes_metadata_and_edge_chunks(self):
        _, array = make_store(self.root)
        for key in ("0.0", "0.1", "1.0", "1.1"):
            (array / key).write_bytes(b"chunk")
        report = inspect(self.root, 2001, 2001, check_chunks=True)
        self.assertTrue(report["ok"])
        self.assertTrue(report["years"][0]["metadata_sha256"])
        entry = report["years"][0]["arrays"][0]
        self.assertEqual((entry["name"], entry["shape"], entry["dtype"], entry["units"]),
                         ("surface/temperature", [3, 3], "<f4", "K"))
        self.assertEqual(entry["chunk_inventory"], {
            "expected": 4, "present": 4, "missing": 0, "empty": 0, "bytes": 20,
            "unexpected": 0, "unexpected_examples": [],
        })

    def test_missing_empty_extra_chunks_and_missing_store_are_reported(self):
        _, array = make_store(self.root)
        (array / "0.0").touch()
        (array / "0.1").write_bytes(b"ok")
        (array / "1.0").write_bytes(b"ok")
        (array / "8.8").write_bytes(b"extra")
        report = inspect(self.root, 2001, 2002, check_chunks=True)
        self.assertFalse(report["ok"])
        self.assertEqual(report["missing_stores"], [2002])
        inv = report["years"][0]["arrays"][0]["chunk_inventory"]
        self.assertEqual((inv["missing"], inv["empty"], inv["unexpected"]), (1, 1, 1))
        self.assertEqual(inv["unexpected_examples"], ["8.8"])

    def test_invalid_metadata_and_incomplete_markers_are_errors(self):
        store, array = make_store(self.root)
        (array / ".zarray").write_text('{"shape":[-1],"chunks":[0],"dtype":"<f4"}')
        (store / "_PROGRESS").write_text("01\n02\n")
        (store / "_DONE").unlink()
        report = inspect(self.root, 2001, 2001)
        self.assertFalse(report["ok"])
        self.assertTrue(any("invalid metadata" in e for e in report["errors"]))
        self.assertTrue(any("_DONE marker missing" in e for e in report["errors"]))
        self.assertTrue(any("_PROGRESS" in e for e in report["errors"]))

    def test_cli_refuses_output_inside_input_root(self):
        with self.assertRaises(SystemExit) as exc:
            main(["--root", str(self.root), "--start-year", "2001", "--end-year", "2001",
                  "--out", str(self.root / "inventory.json")])
        self.assertEqual(exc.exception.code, 2)

    def test_cli_rejects_negative_year_and_reversed_range(self):
        for args in (["--root", str(self.root), "--start-year", "-1", "--end-year", "0"],
                     ["--root", str(self.root), "--start-year", "2", "--end-year", "1"]):
            with self.subTest(args=args), self.assertRaises(SystemExit) as exc:
                main(args)
            self.assertEqual(exc.exception.code, 2)

    def test_consolidated_metadata_rejects_stale_broken_or_external_entries(self):
        store, array = make_store(self.root)
        entries = {p.relative_to(store).as_posix(): json.loads(p.read_text())
                   for p in store.rglob("*") if p.name in {".zgroup", ".zarray", ".zattrs"}}
        doc = {"zarr_consolidated_format": 1, "metadata": entries}
        path = store / ".zmetadata"
        path.write_text(json.dumps(doc))
        (store / "_PROGRESS").write_text("1 2 3 4 5 6 7 8 9 10 11 12")
        self.assertTrue(inspect(self.root, 2001, 2001)["ok"])
        attrs = entries.pop("surface/temperature/.zattrs")
        path.write_text(json.dumps(doc))
        self.assertFalse(inspect(self.root, 2001, 2001)["ok"])
        entries["surface/temperature/.zattrs"] = attrs
        entries["surface/temperature/.zarray"]["shape"] = [999, 999]
        path.write_text(json.dumps(doc))
        self.assertFalse(inspect(self.root, 2001, 2001)["ok"])
        path.write_text("{broken")
        self.assertFalse(inspect(self.root, 2001, 2001)["ok"])
        doc["metadata"] = {"../.zarray": {}}
        path.write_text(json.dumps(doc))
        self.assertFalse(inspect(self.root, 2001, 2001)["ok"])

    def test_empty_or_noncanonical_chunk_alone_fails(self):
        _, array = make_store(self.root, shape=(1,), chunks=(1,))
        (array / "0").touch()
        self.assertFalse(inspect(self.root, 2001, 2001, True)["ok"])
        (array / "0").unlink()
        (array / "00").write_bytes(b"data")
        report = inspect(self.root, 2001, 2001, True)
        inv = report["years"][0]["arrays"][0]["chunk_inventory"]
        self.assertFalse(report["ok"])
        self.assertEqual((inv["missing"], inv["unexpected"]), (1, 1))

    def test_cli_creates_output_parent_outside_cache(self):
        cache = self.root / "cache"
        make_store(cache)
        output = self.root / "report" / "inventory.json"
        result = main(["--root", str(cache), "--start-year", "2001", "--end-year", "2001",
                       "--out", str(output)])
        self.assertEqual(result, 0)
        self.assertTrue(json.loads(output.read_text())["ok"])
