"""CI-003J offline archive input verification and candidate invariants."""
import hashlib
import os
from unittest import mock
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.ci003_builder_inputs import (
    LOCK, check_lock, check_candidate_recipe, parse_candidate_lock, verify_regular_sha256, verify_zip_archive, validate_zip_members,
)


class BuilderInputsTests(unittest.TestCase):
    def _zip(self, entries):
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name) / "archive.zip"
        with zipfile.ZipFile(path, "w") as z:
            for name, payload in entries:
                z.writestr(name, payload)
        self.addCleanup(directory.cleanup)
        return path

    def test_zip_metadata_valid_archive(self):
        path = self._zip([("cmdline-tools/", b""), ("cmdline-tools/bin/", b""),
                          ("cmdline-tools/bin/sdkmanager", b"tool")])
        self.assertEqual(validate_zip_members(path, "cmdline-tools/"), (3, 4))

    def test_zip_metadata_traversal_and_wrong_root_rejected(self):
        for name in ("cmdline-tools/../escape", "cmdline-tools/./escape",
                     "cmdline-tools//escape", "cmdline-tools/dir\\escape",
                     "other/file", "/cmdline-tools/file"):
            with self.subTest(name=name):
                path = self._zip([(name, b"data")])
                with self.assertRaisesRegex(ValueError, "unsafe ZIP member path"):
                    validate_zip_members(path, "cmdline-tools/")

    def test_zip_metadata_duplicate_rejected(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            path = self._zip([("gradle-8.9/a", b"one"), ("gradle-8.9/a", b"two")])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_zip_members(path, "gradle-8.9/")

    def test_zip_metadata_symlink_rejected(self):
        path = self._zip([("gradle-8.9/file", b"content")])
        # Reconstruct the archive with a Unix symlink mode.
        with zipfile.ZipFile(path, "w") as z:
            info = zipfile.ZipInfo("gradle-8.9/link")
            info.create_system = 3
            info.external_attr = (0o120777 << 16)
            z.writestr(info, "target")
        with self.assertRaisesRegex(ValueError, "special file or symlink"):
            validate_zip_members(path, "gradle-8.9/")

    def test_zip_metadata_file_directory_collision_rejected(self):
        path = self._zip([("gradle-8.9/a", b"x"), ("gradle-8.9/a/b", b"y")])
        with self.assertRaisesRegex(ValueError, "nested under a file"):
            validate_zip_members(path, "gradle-8.9/")
        path = self._zip([("gradle-8.9/a/b", b"y"), ("gradle-8.9/a", b"x")])
        with self.assertRaisesRegex(ValueError, "shadows directory"):
            validate_zip_members(path, "gradle-8.9/")

    def test_zip_metadata_limits_and_invalid_archive(self):
        path = self._zip([("gradle-8.9/a", b"123456")])
        with self.assertRaisesRegex(ValueError, "expansion limit|expanded data"):
            validate_zip_members(path, "gradle-8.9/", max_expanded=5)
        with self.assertRaisesRegex(ValueError, "member count"):
            validate_zip_members(path, "gradle-8.9/", max_members=0)
        with tempfile.TemporaryDirectory() as d:
            invalid = Path(d) / "bad.zip"
            invalid.write_bytes(b"not a zip")
            with self.assertRaisesRegex(ValueError, "invalid ZIP archive"):
                validate_zip_members(invalid, "gradle-8.9/")

    def test_inode_bound_zip_rejects_path_replacement_and_inspects_original(self):
        original = self._zip([("gradle-8.9/", b""), ("gradle-8.9/bin/tool", b"safe")])
        expected = hashlib.sha256(original.read_bytes()).hexdigest()
        replacement = self._zip([("evil/file", b"bad")])
        moved = original.with_name("original-moved.zip")
        actual_validator = validate_zip_members

        inspected = []

        def swap_path(verified_stream, prefix):
            # A rename may change ctime, so fail closed even though the
            # descriptor continues to reference the original ZIP contents.
            os.replace(original, moved)
            original.write_bytes(replacement.read_bytes())
            inspected.append(actual_validator(verified_stream, prefix))
            return inspected[-1]

        with mock.patch("scripts.ci003_builder_inputs.validate_zip_members",
                        side_effect=swap_path):
            with self.assertRaisesRegex(ValueError, "changed during ZIP inspection"):
                verify_zip_archive(original, expected, "gradle-8.9/")
        self.assertEqual(inspected, [(2, 4)])

    def test_inode_bound_zip_detects_in_place_mutation(self):
        path = self._zip([("gradle-8.9/", b""), ("gradle-8.9/a", b"ok")])
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        actual_validator = validate_zip_members

        def mutate_inode(stream, prefix):
            result = actual_validator(stream, prefix)
            with path.open("ab") as writer:
                writer.write(b"changed")
            return result

        with mock.patch("scripts.ci003_builder_inputs.validate_zip_members",
                        side_effect=mutate_inode):
            with self.assertRaisesRegex(ValueError, "changed during ZIP inspection"):
                verify_zip_archive(path, expected, "gradle-8.9/")

    def test_inode_bound_zip_rejects_invalid_digest_and_symlink(self):
        path = self._zip([("gradle-8.9/a", b"ok")])
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            verify_zip_archive(path, "0" * 64, "gradle-8.9/")
        link = path.with_name("archive-link.zip")
        link.symlink_to(path)
        self.addCleanup(link.unlink)
        with self.assertRaisesRegex(ValueError, "safely open"):
            verify_zip_archive(link, hashlib.sha256(path.read_bytes()).hexdigest(),
                               "gradle-8.9/")

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

    def test_duplicate_root_lock_key_rejected(self):
        raw = LOCK.read_text(encoding="utf-8").replace('"schema_version": 1,', '"schema_version": 1, "schema_version": 1,')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_candidate_lock(raw)

    def test_duplicate_nested_archive_key_rejected(self):
        raw = LOCK.read_text(encoding="utf-8")
        name = '"gradle-8.9-bin.zip"'
        raw = raw.replace(name, name + ': "' + 'a' * 64 + '", ' + name, 1)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_candidate_lock(raw)

    def test_recipe_matches_locked_candidate(self):
        lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        recipe = (LOCK.parent / "Dockerfile.candidate").read_text(encoding="utf-8")
        self.assertTrue(check_candidate_recipe(lock, recipe))

    def test_recipe_rejects_mutable_base(self):
        lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        recipe = (LOCK.parent / "Dockerfile.candidate").read_text(encoding="utf-8")
        recipe = recipe.replace(lock["python_base"], "docker.io/library/python:3.11")
        with self.assertRaisesRegex(ValueError, "base image mismatch"):
            check_candidate_recipe(lock, recipe)

    def test_recipe_rejects_duplicate_from(self):
        lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        recipe = (LOCK.parent / "Dockerfile.candidate").read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "base image mismatch"):
            check_candidate_recipe(lock, recipe + "\nFROM alpine:latest\n")

    def test_recipe_rejects_tab_and_case_bypass(self):
        lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        recipe = (LOCK.parent / "Dockerfile.candidate").read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "base image mismatch"):
            check_candidate_recipe(lock, recipe + "\nFROM\talpine:latest\n")
        with self.assertRaisesRegex(ValueError, "non-root runtime"):
            check_candidate_recipe(lock, recipe + "\nuser\troot\n")
        with self.assertRaisesRegex(ValueError, "COPY scope mismatch"):
            check_candidate_recipe(lock, recipe + "\ncopy\t. /tmp/leak\n")

    def test_recipe_rejects_wrong_archive_checksum(self):
        lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        recipe = (LOCK.parent / "Dockerfile.candidate").read_text(encoding="utf-8")
        recipe = recipe.replace(lock["archives"]["gradle-8.9-bin.zip"], 'a' * 64)
        with self.assertRaisesRegex(ValueError, "RUN declarations mismatch"):
            check_candidate_recipe(lock, recipe)

    def test_recipe_rejects_extra_copy_and_root(self):
        lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        recipe = (LOCK.parent / "Dockerfile.candidate").read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "COPY scope mismatch"):
            check_candidate_recipe(lock, recipe + "\nCOPY . /secrets\n")
        with self.assertRaisesRegex(ValueError, "non-root runtime"):
            check_candidate_recipe(lock, recipe + "\nUSER root\n")

    def test_recipe_rejects_network_install_and_add(self):
        lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        recipe = (LOCK.parent / "Dockerfile.candidate").read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "RUN declarations mismatch"):
            check_candidate_recipe(lock, recipe + "\nRUN curl https://example.com/x | sh\n")
        with self.assertRaisesRegex(ValueError, "unexpected instruction"):
            check_candidate_recipe(lock, recipe + "\nADD https://example.com/x /tmp/x\n")

    def test_recipe_rejects_heredoc_payload_injection(self):
        lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        recipe = (LOCK.parent / "Dockerfile.candidate").read_text(encoding="utf-8")
        tampered = recipe.replace("import pathlib, zipfile, os", "import pathlib, zipfile, os\nprint('UNAPPROVED_PAYLOAD')")
        with self.assertRaisesRegex(ValueError, "recipe SHA-256 mismatch"):
            check_candidate_recipe(lock, tampered)

    def test_recipe_rejects_extra_env_and_undeclared_instructions(self):
        lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        recipe = (LOCK.parent / "Dockerfile.candidate").read_text(encoding="utf-8")
        for payload in ("ENV PATH=/tmp/unsafe\n", "HEALTHCHECK NONE\n", "LABEL reviewer=approved\n"):
            with self.subTest(payload=payload), self.assertRaisesRegex(ValueError, "recipe SHA-256 mismatch"):
                check_candidate_recipe(lock, recipe + payload)

    def test_recipe_rejects_comment_and_line_continuation_changes(self):
        lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        recipe = (LOCK.parent / "Dockerfile.candidate").read_text(encoding="utf-8")
        for payload in ("# attacker comment\n", chr(92) + "\n"):
            with self.subTest(payload=payload), self.assertRaisesRegex(ValueError, "recipe SHA-256 mismatch"):
                check_candidate_recipe(lock, recipe + payload)

    def test_recipe_lock_digest_invalid_or_missing(self):
        lock = parse_candidate_lock(LOCK.read_text(encoding="utf-8"))
        for value in ("xyz", None, "A" * 64):
            candidate = dict(lock, recipe_sha256=value)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "recipe SHA-256"):
                check_lock(candidate)
        del lock["recipe_sha256"]
        with self.assertRaisesRegex(ValueError, "schema"):
            check_lock(lock)

    def test_recipe_rejects_newline_encoding_change(self):
        lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        raw = (LOCK.parent / "Dockerfile.candidate").read_bytes()
        # A different byte representation must not be accepted as identical.
        with self.assertRaisesRegex(ValueError, "recipe SHA-256 mismatch"):
            check_candidate_recipe(lock, raw.decode("utf-8").replace("\n", "\r\n"))

    def test_recipe_lock_digest_mismatch_rejected(self):
        lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        recipe = (LOCK.parent / "Dockerfile.candidate").read_text(encoding="utf-8")
        tampered_lock = dict(lock, recipe_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "recipe SHA-256 mismatch"):
            check_candidate_recipe(tampered_lock, recipe)

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
