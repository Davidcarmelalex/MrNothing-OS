"""Offline CI-003F pinned-image candidate negative controls; no image is built."""
import json
from pathlib import Path
import tempfile
import unittest
from scripts.ci003_pinned_builder import pinned_image, policy_image, workflow_image, validate

IMAGE = "ghcr.io/example/android-builder@sha256:" + "1" * 64
WORKFLOW = "jobs:\n  build:\n    runs-on: ubuntu-24.04\n    container:\n      image: " + IMAGE + "\n    steps:\n      - run: true\n"


class CandidatePinTests(unittest.TestCase):
    def test_valid_literal_is_only_syntax_evidence(self):
        self.assertEqual(pinned_image(IMAGE), IMAGE)

    def test_mutable_and_malformed_images_fail(self):
        for candidate in ("ubuntu:24.04", "ghcr.io/example/builder:latest",
                          "builder@sha256:" + "1" * 64,
                          "ghcr.io/example/builder@sha256:" + "0" * 64,
                          "ghcr.io/example/builder@sha256:" + "A" * 64,
                          "ghcr.io/example/builder@sha256:" + "1" * 63,
                          "$" + "{{ secrets.IMAGE }}"):
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                pinned_image(candidate)

    def test_candidate_workflow_matches(self):
        self.assertEqual(workflow_image(WORKFLOW), IMAGE)

    def test_current_ci003_workflow_is_not_pinned(self):
        workflow = (Path(__file__).resolve().parents[1] /
                    ".github/workflows/ci003-reproducibility.yml").read_text()
        with self.assertRaisesRegex(ValueError, "no unique pinned"):
            workflow_image(workflow)

    def test_missing_duplicate_or_mutable_container_fails(self):
        for workflow in (WORKFLOW.replace("    container:\n      image: " + IMAGE + "\n", ""),
                         WORKFLOW.replace("    container:\n", "    container:\n    container:\n"),
                         WORKFLOW.replace(IMAGE, "ghcr.io/example/builder:latest")):
            with self.subTest(workflow=workflow), self.assertRaises(ValueError):
                workflow_image(workflow)

    def test_policy_schema_and_duplicate_json_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.json"
            for obj in ({"schema_version": True, "platform": "linux/amd64", "image": IMAGE},
                        {"schema_version": 1, "platform": "linux/arm64", "image": IMAGE},
                        {"schema_version": 1, "platform": "linux/amd64", "image": IMAGE, "approved": True}):
                path.write_text(json.dumps(obj))
                with self.subTest(obj=obj), self.assertRaises(ValueError):
                    policy_image(path)
            path.write_text('{"schema_version":1,"schema_version":1,"platform":"linux/amd64","image":"' + IMAGE + '"}')
            with self.assertRaisesRegex(ValueError, "duplicate"):
                policy_image(path)

    def test_policy_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "real.json"
            path.write_text(json.dumps({"schema_version": 1, "platform": "linux/amd64", "image": IMAGE}))
            link = Path(directory) / "link.json"
            link.symlink_to(path)
            with self.assertRaisesRegex(ValueError, "regular"):
                policy_image(link)

    def test_exact_candidate_workflow_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = root / "candidate.json"
            workflow = root / "workflow.yml"
            workflow.write_text(WORKFLOW)
            policy.write_text(json.dumps({"schema_version": 1, "platform": "linux/amd64", "image": IMAGE}))
            self.assertEqual(validate(policy, workflow), "PIN_SYNTAX_VALID_NOT_ATTESTED")
            policy.write_text(json.dumps({"schema_version": 1, "platform": "linux/amd64",
                                          "image": IMAGE.replace("1" * 64, "2" * 64)}))
            with self.assertRaisesRegex(ValueError, "differs"):
                validate(policy, workflow)


if __name__ == "__main__":
    unittest.main()
