"""ROM-003 focused negative-control tests; no device or signing operations."""
import hashlib
import importlib.util
import json
from unittest.mock import patch
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

    def test_leaf_symlink_rejected_even_if_opened_after_validation(self):
        target = self.apk.with_suffix(".original")
        self.apk.rename(target)
        self.apk.symlink_to(target)
        with self.assertRaises(ValueError):
            self.check()

    def test_replaced_path_after_open_uses_pinned_inode(self):
        original_open = mod.open_regular_file
        moved = False

        def replace_after_open(path):
            nonlocal moved
            handle = original_open(path)
            if path == self.apk and not moved:
                moved = True
                old = self.apk.with_suffix(".pinned")
                self.apk.rename(old)
                self.apk.write_bytes(b"substituted attacker bytes")
            return handle

        with patch.object(mod, "open_regular_file", side_effect=replace_after_open):
            self.assertTrue(self.check())
        self.assertTrue(moved)
        with self.assertRaises(ValueError):
            self.check()

    def test_in_place_apk_mutation_during_zip_check_rejected(self):
        original = mod.reject_apk_signing_block
        def mutate_after_initial_digest(handle):
            original(handle)
            with open(self.apk, "r+b") as writable:
                writable.seek(0)
                writable.write(b"XXXX")
                writable.flush()
        with patch.object(mod, "reject_apk_signing_block", side_effect=mutate_after_initial_digest):
            with self.assertRaisesRegex(ValueError, "mutated during verification"):
                self.check()

    def test_in_place_provenance_mutation_during_zip_check_rejected(self):
        original = mod.reject_apk_signing_block

        def mutate_after_initial_digest(handle):
            original(handle)
            with open(self.prov, "r+b") as writable:
                writable.seek(0)
                writable.write(b"XXXX")
                writable.flush()

        with patch.object(mod, "reject_apk_signing_block", side_effect=mutate_after_initial_digest):
            with self.assertRaisesRegex(ValueError, "mutated during verification"):
                self.check()

    def test_in_place_manifest_mutation_during_zip_check_rejected(self):
        original = mod.reject_apk_signing_block

        def mutate_after_initial_digest(handle):
            original(handle)
            with open(self.manifest, "r+b") as writable:
                writable.seek(0)
                writable.write(b"XXXX")
                writable.flush()

        with patch.object(mod, "reject_apk_signing_block", side_effect=mutate_after_initial_digest):
            with self.assertRaisesRegex(ValueError, "mutated during verification"):
                self.check()

    def test_in_place_record_mutation_during_zip_check_rejected(self):
        original = mod.reject_apk_signing_block

        def mutate_after_initial_digest(handle):
            original(handle)
            with open(self.record, "r+b") as writable:
                writable.seek(0)
                writable.write(b"XXXX")
                writable.flush()

        with patch.object(mod, "reject_apk_signing_block", side_effect=mutate_after_initial_digest):
            with self.assertRaises((ValueError, json.JSONDecodeError)):
                self.check()

    def test_apk_signature_entry_rejected(self):
        with zipfile.ZipFile(self.apk, "a") as z:
            z.writestr("META-INF/CERT.RSA", b"signature")
        self.data["apk_sha256"] = mod.digest(self.apk)
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_excessive_zip_entry_count_rejected(self):
        with zipfile.ZipFile(self.apk, "a") as z:
            for i in range(mod.MAX_ZIP_ENTRIES):
                z.writestr(f"extra/{i}", b"")
        self.data["apk_sha256"] = mod.digest(self.apk)
        self.save()
        with self.assertRaisesRegex(ValueError, "ZIP entry limits"):
            self.check()

    def test_excessive_zip_filename_rejected(self):
        # ZIP names can be long even when the archive itself is small.
        with zipfile.ZipFile(self.apk, "a") as z:
            z.writestr("x" * (mod.MAX_ZIP_NAME_BYTES + 1), b"")
        self.data["apk_sha256"] = mod.digest(self.apk)
        self.save()
        with self.assertRaisesRegex(ValueError, "ZIP entry limits"):
            self.check()

    def test_parent_traversal_zip_entry_rejected(self):
        with zipfile.ZipFile(self.apk, "a") as z:
            z.writestr("assets/../payload", b"test")
        self.data["apk_sha256"] = mod.digest(self.apk)
        self.save()
        with self.assertRaisesRegex(ValueError, "unsafe APK ZIP entry"):
            self.check()

    def test_backslash_zip_entry_rejected(self):
        with zipfile.ZipFile(self.apk, "a") as z:
            z.writestr("assets\\payload", b"test")
        self.data["apk_sha256"] = mod.digest(self.apk)
        self.save()
        with self.assertRaisesRegex(ValueError, "unsafe APK ZIP entry"):
            self.check()

    def inject_block(self, malformed=False):
        raw = self.apk.read_bytes()
        end = raw.rfind(bytes.fromhex("504b0506"))
        off = int.from_bytes(raw[end + 16:end + 20], "little")
        payload = b"synthetic-pair"
        size = len(payload) + 24
        block = size.to_bytes(8, "little") + payload + (size + int(malformed)).to_bytes(8, "little") + b"APK Sig Block 42"
        out = bytearray(raw[:off] + block + raw[off:])
        end += len(block)
        out[end + 16:end + 20] = (off + len(block)).to_bytes(4, "little")
        self.apk.write_bytes(out)
        self.data["apk_sha256"] = mod.digest(self.apk)
        self.save()

    def test_v2_v3_signing_block_rejected(self):
        self.inject_block()
        with self.assertRaisesRegex(ValueError, "signing block"):
            self.check()

    def test_malformed_signing_block_rejected(self):
        self.inject_block(malformed=True)
        with self.assertRaisesRegex(ValueError, "signing block"):
            self.check()


if __name__ == "__main__":
    unittest.main()

