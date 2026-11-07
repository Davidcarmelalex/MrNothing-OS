import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.android_build_provenance import build_record


class AndroidBuildProvenanceTests(unittest.TestCase):
    def test_known_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app-debug.apk"
            path.write_bytes(b"debug-test")
            record = build_record(path, "a" * 40)
            self.assertEqual(record["artifact_sha256"], hashlib.sha256(b"debug-test").hexdigest())
            self.assertFalse(record["release_ready"])
            self.assertFalse(record["provenance_signed"])

    def test_missing_apk_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                build_record(Path(directory) / "missing.apk", "a" * 40)

    def test_empty_apk_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.apk"
            path.write_bytes(b"")
            with self.assertRaises(ValueError):
                build_record(path, "a" * 40)

    def test_invalid_commit_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app-debug.apk"
            path.write_bytes(b"content")
            with self.assertRaises(ValueError):
                build_record(path, "not-a-sha")


if __name__ == "__main__":
    unittest.main()
