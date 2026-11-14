import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.rom_input_preflight import KINDS, check, unique_object


class RomInputPreflightTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = {"schema": "mrnothing-rom-inputs-v1", "device": "caiman", "inputs": []}
        for kind in sorted(KINDS):
            entry = {"kind": kind}
            for key, hash_key in (("path", "sha256"), ("review_path", "review_sha256")):
                name = kind + "-" + key
                content = ("synthetic fixture " + name).encode()
                (self.root / name).write_bytes(content)
                entry[key] = name
                entry[hash_key] = hashlib.sha256(content).hexdigest()
            self.data["inputs"].append(entry)

    def test_integrity_never_grants_acceptance(self):
        result = check(self.data, self.root)
        self.assertTrue(result.pop("input_integrity_passed"))
        for field in ("compatibility_verified", "license_approval_verified", "bootable_rom_verified", "release_ready", "flash_authorized"):
            self.assertIs(result[field], False)

    def test_missing_each_dependency(self):
        for index in range(6):
            data = copy.deepcopy(self.data)
            del data["inputs"][index]
            with self.assertRaises(ValueError):
                check(data, self.root)

    def test_reject_wrong_device(self):
        self.data["device"] = "komodo"
        with self.assertRaises(ValueError):
            check(self.data, self.root)

    def test_reject_duplicate_kind(self):
        self.data["inputs"][1] = self.data["inputs"][0]
        with self.assertRaises(ValueError):
            check(self.data, self.root)

    def test_reject_unreviewed_or_tampered_inputs(self):
        for key in ("path", "review_path"):
            path = self.root / self.data["inputs"][0][key]
            original = path.read_bytes()
            path.write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                check(self.data, self.root)
            path.write_bytes(original)

    def test_reject_unsafe_paths(self):
        for value in ("../escape", "/etc/passwd", "C:/x", "a\\b", "a//b", "./a", ""):
            self.data["inputs"][0]["path"] = value
            with self.assertRaises(ValueError):
                check(self.data, self.root)

    def test_reject_self_review(self):
        self.data["inputs"][0]["review_path"] = self.data["inputs"][0]["path"]
        with self.assertRaises(ValueError):
            check(self.data, self.root)

    def test_reject_missing_file(self):
        (self.root / self.data["inputs"][0]["path"]).unlink()
        with self.assertRaises(ValueError):
            check(self.data, self.root)

    def test_reject_empty_even_with_matching_hash(self):
        item = self.data["inputs"][0]
        (self.root / item["path"]).write_bytes(b"")
        item["sha256"] = hashlib.sha256(b"").hexdigest()
        with self.assertRaises(ValueError):
            check(self.data, self.root)

    def test_reject_symlink(self):
        item = self.data["inputs"][0]
        link = self.root / "link"
        try:
            link.symlink_to(self.root / item["path"])
        except OSError:
            self.skipTest("host does not permit unprivileged symlink creation")
        item["path"] = "link"
        with self.assertRaises(ValueError):
            check(self.data, self.root)

    def test_reject_noncanonical_digest(self):
        for value in (None, True, "0" * 63, "A" * 64):
            self.data["inputs"][0]["sha256"] = value
            with self.assertRaises(ValueError):
                check(self.data, self.root)

    def test_reject_duplicate_json_fields(self):
        with self.assertRaises(ValueError):
            json.loads('{"device":"caiman","device":"caiman"}', object_pairs_hook=unique_object)

    def test_reject_invented_approval(self):
        self.data["release_ready"] = True
        with self.assertRaises(ValueError):
            check(self.data, self.root)
