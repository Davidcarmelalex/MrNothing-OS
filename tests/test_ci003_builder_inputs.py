"""CI-003J offline archive input verification and candidate invariants."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.ci003_builder_inputs import LOCK, check_lock, verify_regular_sha256


class BuilderInputsTests(unittest.TestCase):
    def test_valid_small_regular_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sample.zip"
            path.write_bytes(b"test payload")
            self.assertEqual(verify_regular_sha256(path, hashlib.sha256(b"test payload").hexdigest()), 12)

    def test_modified_content_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sample.zip"
            path.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "mismatch"):
                verify_regular_sha256(path, hashlib.sha256(b"expected").hexdigest())

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sample.zip"
            path.write_bytes(b"abc")
            link = Path(d) / "link.zip"
            link.symlink_to(path)
            with self.assertRaisesRegex(ValueError, "safely open"):
                verify_regular_sha256(link, hashlib.sha256(b"abc").hexdigest())

    def test_directory_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "regular"):
                verify_regular_sha256(Path(d), hashlib.sha256(b"abc").hexdigest())

    def test_oversized_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sample.zip"
            path.write_bytes(b"abc")
            with self.assertRaisesRegex(ValueError, "bounded"):
                verify_regular_sha256(path, hashlib.sha256(b"abc").hexdigest(), maximum=2)

    def test_empty_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sample.zip"
            path.touch()
            with self.assertRaisesRegex(ValueError, "bounded"):
                verify_regular_sha256(path, hashlib.sha256(b"").hexdigest())

    def test_invalid_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, "expected SHA"):
            verify_regular_sha256(Path("/missing"), "abc")

    def test_locked_candidate_schema(self):
        lock = check_lock(json.loads(LOCK.read_text(encoding="utf-8")))
        self.assertEqual(lock["status"], "UNAPPROVED_CANDIDATE")

    def test_mutable_base_rejected(self):
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        lock["python_base"] = "docker.io/library/python:3.11"
        with self.assertRaisesRegex(ValueError, "digest-pinned"):
            check_lock(lock)

    def test_unknown_lock_key_rejected(self):
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        lock["allow_root"] = True
        with self.assertRaisesRegex(ValueError, "schema"):
            check_lock(lock)

    def test_build_context_excludes_repository_files(self):
        rules = (LOCK.parent / "Dockerfile.candidate.dockerignore").read_text().splitlines()
        self.assertEqual(rules[0], "**")
        self.assertEqual(set(rules[1:]), {
            "!builder/", "!builder/inputs/",
            "!builder/inputs/commandlinetools-linux-16111833_latest.zip",
            "!builder/inputs/gradle-8.9-bin.zip",
        })

    def test_dockerfile_matches_lock(self):
        lock = check_lock(json.loads(LOCK.read_text(encoding="utf-8")))
        text = (LOCK.parent / "Dockerfile.candidate").read_text(encoding="utf-8")
        for key in ("python_base", "jdk_base"):
            self.assertIn(lock[key], text)
        for sha in lock["archives"].values():
            self.assertIn(sha, text)
        self.assertIn("USER 10001:10001", text)
        self.assertNotIn("apt-get", text)
        self.assertNotIn("sdkmanager --licenses", text)
        self.assertNotIn("RUN curl", text)


if __name__ == "__main__":
    unittest.main()
