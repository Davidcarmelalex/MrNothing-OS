"""ROM-003 focused negative-control tests; no device or signing operations."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rom003", ROOT / "scripts/verify_staged_launcher_apk.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SOURCE = "a" * 40


class StagedApkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.apk = root / "launcher.apk"
        self.record = root / "record.json"
        self.prov = root / "provenance.json"
        self.manifest = root / "release-manifest.json"
        with zipfile.ZipFile(self.apk, "w") as z:
            z.writestr("AndroidManifest.xml", b"manifest")
            z.writestr("classes.dex", b"dex")
        for p in (self.prov, self.manifest):
            p.write_text(json.dumps({"source_commit": SOURCE}), encoding="utf-8")
        self.data = {"schema": "mrnothing-staged-apk-v1", "source_commit": SOURCE,
                     "apk_sha256": mod.digest(self.apk), "apk_kind": "launcher",
                     "build_variant": "release", "unsigned": True,
                     "provenance_sha256": mod.digest(self.prov),
                     "release_manifest_sha256": mod.digest(self.manifest)}
        self.save()

    def save(self):
        self.record.write_text(json.dumps(self.data), encoding="utf-8")

    def check(self):
        return mod.verify(self.apk, self.record, self.prov, self.manifest, SOURCE)

    def test_valid_synthetic_integrity_only(self):
        self.assertTrue(self.check())

    def test_debug_rejected(self):
        self.data["build_variant"] = "debug"
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_signed_flag_rejected(self):
        self.data["unsigned"] = False
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_wrong_source_rejected(self):
        self.data["source_commit"] = "b" * 40
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_apk_tamper_rejected(self):
        self.apk.write_bytes(self.apk.read_bytes() + b"tamper")
        with self.assertRaises(ValueError):
            self.check()

    def test_evidence_tamper_rejected(self):
        self.prov.write_text('{"source_commit":"' + "b" * 40 + '"}')
        with self.assertRaises(ValueError):
            self.check()

    def test_duplicate_record_key_rejected(self):
        self.record.write_text('{"schema":"x","schema":"y"}')
        with self.assertRaises(ValueError):
            self.check()

    def test_missing_artifact_rejected(self):
        self.apk.unlink()
        with self.assertRaises(OSError):
            self.check()

    def test_symlink_rejected(self):
        target = self.apk.with_suffix(".real")
        self.apk.rename(target)
        try:
            self.apk.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        with self.assertRaises(ValueError):
            self.check()

    def test_apk_signature_entry_rejected(self):
        with zipfile.ZipFile(self.apk, "a") as z:
            z.writestr("META-INF/CERT.RSA", b"signature")
        self.data["apk_sha256"] = mod.digest(self.apk)
        self.save()
        with self.assertRaises(ValueError):
            self.check()


if __name__ == "__main__":
    unittest.main()
