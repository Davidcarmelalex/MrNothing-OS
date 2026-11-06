import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from types import SimpleNamespace

from scripts.build_environment_sbom import (
    attach_provenance,
    collect_inventory,
    make_spdx,
    parse_action_pins,
    parse_dpkg_inventory,
    parse_gradle_inputs,
    parse_python_packages,
    parse_sdkmanager_packages,
    run_negative_control,
    validate_inventory_and_sbom,
    verify_bundles,
)


COMMIT = "a" * 40
GRADLE_BYTES = b"pinned-gradle-distribution-fixture"


class BuildEnvironmentSbomTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.sdk = self.root / "sdk"
        for relative, revision in (
            ("platforms/android-35", "2"),
            ("build-tools/35.0.0", "35.0.0"),
            ("cmdline-tools/latest", "12.0"),
            ("platform-tools", "35.0.2"),
        ):
            directory = self.sdk / relative
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "source.properties").write_text(
                f"Pkg.Revision={revision}\n", encoding="utf-8"
            )
        self.gradle_zip = self.root / "gradle-8.9-bin.zip"
        self.gradle_zip.write_bytes(GRADLE_BYTES)
        self.gradle_sha = hashlib.sha256(GRADLE_BYTES).hexdigest()
        self.workflow = self.root / "ci003.yml"
        self.workflow.write_text(
            "\n".join([
                "steps:",
                "  - uses: actions/checkout@" + "1" * 40,
                "  - uses: actions/setup-java@" + "2" * 40,
                "  - uses: actions/setup-python@" + "3" * 40,
                "  - uses: actions/upload-artifact@" + "4" * 40,
                "  - uses: actions/download-artifact@" + "5" * 40,
                f'    run: echo "{self.gradle_sha} $RUNNER_TEMP/gradle-8.9-bin.zip" | sha256sum --check',
                '    run: sdkmanager "platforms;android-35" "build-tools;35.0.0"',
            ]) + "\n",
            encoding="utf-8",
        )
        self.root_gradle = self.root / "build.gradle.kts"
        self.root_gradle.write_text(
            'plugins {\n'
            '    id("com.android.application") version "8.7.3" apply false\n'
            '    id("org.jetbrains.kotlin.android") version "2.0.21" apply false\n'
            '}\n',
            encoding="utf-8",
        )
        self.app_gradle = self.root / "app-build.gradle.kts"
        self.app_gradle.write_text("android {\n    compileSdk = 35\n}\n", encoding="utf-8")
        self.os_release = self.root / "os-release"
        self.os_release.write_text(
            'ID=ubuntu\nVERSION_ID="24.04"\nPRETTY_NAME="Ubuntu 24.04 LTS"\n',
            encoding="utf-8",
        )
        self.dpkg = self.root / "dpkg.tsv"
        self.dpkg.write_text(
            "ii \tlibc6:amd64\t2.39-0ubuntu8\n"
            "ii \tca-certificates:all\t20240203\n"
            "rc \told-package:amd64\t1.0\n",
            encoding="utf-8",
        )
        self.pip = self.root / "pip.json"
        self.pip.write_text(
            json.dumps([{"name": "Pip", "version": "24.0"}, {"name": "setuptools", "version": "70.0"}]),
            encoding="utf-8",
        )
        self.sdk_packages = self.root / "sdk-packages.txt"
        self.sdk_packages.write_text(
            "Installed packages:\n"
            "  Path | Version | Description\n"
            "  build-tools;35.0.0 | 35.0.0 | Android SDK Build-Tools 35\n"
            "  cmdline-tools;latest | 12.0 | Android SDK Command-line Tools\n"
            "  platform-tools | 35.0.2 | Android SDK Platform-Tools\n"
            "  platforms;android-35 | 2 | Android SDK Platform 35\n",
            encoding="utf-8",
        )
        self.gradle_version = self.root / "gradle-version.txt"
        self.gradle_version.write_text("Gradle 8.9\nBuild time: fixture\n", encoding="utf-8")
        self.java_properties = self.root / "java-properties.txt"
        self.java_properties.write_text(
            "    java.vendor = Eclipse Adoptium\n"
            "    java.runtime.version = 17.0.13+11\n"
            "    java.version = 17.0.13\n"
            "    java.vm.name = OpenJDK 64-Bit Server VM\n",
            encoding="utf-8",
        )
        self.inventory_path = self.root / "build-environment.inventory.json"
        self.sbom_path = self.root / "build-environment.spdx.json"
        self.args = SimpleNamespace(
            commit=COMMIT,
            created_epoch=1760000000,
            runner_label="ubuntu-24.04",
            runner_image_os="ubuntu24",
            runner_image_version="20261105.1",
            jdk_version="openjdk version 17.0.13 2024-10-15",
            python_version="Python 3.11.13",
            os_release_file=self.os_release,
            dpkg_packages_file=self.dpkg,
            python_packages_file=self.pip,
            sdk_packages_file=self.sdk_packages,
            sdk_root=self.sdk,
            gradle_zip=self.gradle_zip,
            gradle_version_file=self.gradle_version,
            java_properties_file=self.java_properties,
            workflow_file=self.workflow,
            root_gradle_file=self.root_gradle,
            app_gradle_file=self.app_gradle,
            output_inventory=self.inventory_path,
            output_sbom=self.sbom_path,
        )

    def tearDown(self):
        self.temp.cleanup()

    def write_bundle(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        inventory = collect_inventory(self.args)
        (directory / "build-environment.inventory.json").write_text(
            json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        inventory_path = directory / "build-environment.inventory.json"
        sbom = make_spdx(inventory, hashlib.sha256(inventory_path.read_bytes()).hexdigest())
        (directory / "build-environment.spdx.json").write_text(
            json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        provenance = {
            "schema": "mrnothing-ci003-provenance-v2",
            "source_commit": COMMIT,
            "build_environment": {
                key: inventory["toolchain"][key]
                for key in (
                    "operating_system", "jdk_distribution", "jdk_version", "gradle_version",
                    "gradle_sha256", "agp_version", "kotlin_version", "compile_sdk",
                    "build_tools", "sdkmanager_version",
                )
            },
        }
        (directory / "provenance.json").write_text(
            json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        attach_provenance(
            inventory_path,
            directory / "build-environment.spdx.json",
            directory / "provenance.json",
            COMMIT,
        )
        return directory

    def test_dpkg_parser_includes_only_installed_packages(self):
        records = parse_dpkg_inventory(self.dpkg.read_text(encoding="utf-8"))
        self.assertEqual(len(records), 2)
        self.assertTrue(any("libc6" in item["purl"] for item in records))

    def test_dpkg_duplicate_installed_package_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicates"):
            parse_dpkg_inventory("ii \tlibc6:amd64\t1\nii \tlibc6:amd64\t1\n")

    def test_python_package_names_are_normalized(self):
        records = parse_python_packages('[{"name":"My_Pkg.Name","version":"1.2"}]')
        self.assertEqual(records[0]["name"], "my-pkg-name")

    def test_duplicate_python_package_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate Python"):
            parse_python_packages('[{"name":"my_pkg","version":"1"},{"name":"my-pkg","version":"2"}]')

    def test_sdkmanager_parser_captures_installed_package_rows(self):
        records = parse_sdkmanager_packages(self.sdk_packages.read_text(encoding="utf-8"))
        self.assertEqual(len(records), 4)
        self.assertIn("platforms;android-35", {item["package_id"] for item in records})

    def test_duplicate_sdk_package_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate Android SDK"):
            parse_sdkmanager_packages("x;one | 1 | first\nx;one | 1 | duplicate\n")

    def test_mutable_action_reference_rejected(self):
        workflow = self.workflow.read_text(encoding="utf-8").replace("actions/checkout@" + "1" * 40, "actions/checkout@v7")
        with self.assertRaisesRegex(ValueError, "full lowercase commit SHA"):
            parse_action_pins(workflow)

    def test_gradle_inputs_require_pinned_plugins_and_checksum(self):
        result = parse_gradle_inputs(
            self.root_gradle.read_text(encoding="utf-8"),
            self.app_gradle.read_text(encoding="utf-8"),
            self.workflow.read_text(encoding="utf-8"),
        )
        self.assertEqual(result["agp_version"], "8.7.3")
        self.assertEqual(result["kotlin_version"], "2.0.21")
        self.assertEqual(result["compile_sdk"], "35")
        self.assertEqual(result["gradle_sha256_expected"], self.gradle_sha)

    def test_full_inventory_and_spdx_are_deterministic(self):
        inventory = collect_inventory(self.args)
        first = self.root / "first.inventory.json"
        second = self.root / "second.inventory.json"
        first.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        second.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        sbom = make_spdx(inventory, hashlib.sha256(first.read_bytes()).hexdigest())
        sbom_path = self.root / "first.spdx.json"
        sbom_path.write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        validated_inventory, validated_sbom = validate_inventory_and_sbom(first, sbom_path, COMMIT)
        self.assertEqual(validated_inventory["source_commit"], COMMIT)
        self.assertEqual(validated_sbom["spdxVersion"], "SPDX-2.3")
        self.assertGreater(len(validated_inventory["components"]), 5)

    def test_gradle_distribution_digest_mismatch_rejected(self):
        self.gradle_zip.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "workflow-pinned SHA-256"):
            collect_inventory(self.args)

    def test_missing_required_sdk_package_rejected(self):
        self.sdk_packages.write_text(
            "Installed packages:\n"
            "build-tools;35.0.0 | 35.0.0 | Build Tools\n"
            "cmdline-tools;latest | 12.0 | Command Line Tools\n"
            "platform-tools | 35.0.2 | Platform Tools\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "required Android SDK packages"):
            collect_inventory(self.args)


    def test_cmdline_tools_and_platform_tools_are_inventoried_when_list_omits_them(self):
        self.sdk_packages.write_text(
            "Installed packages:\n"
            "build-tools;35.0.0 | 35.0.0 | Build Tools\n"
            "platforms;android-35 | 2 | Android Platform\n",
            encoding="utf-8",
        )
        inventory = collect_inventory(self.args)
        sdk_names = {
            item["name"] for item in inventory["components"]
            if item["kind"] == "android-sdk-package"
        }
        self.assertIn("cmdline-tools;12.0", sdk_names)
        self.assertIn("platform-tools", sdk_names)

    def test_workflow_negative_control_rejects_mutable_action(self):
        result = run_negative_control(self.workflow)
        self.assertEqual(result["negative_control"], "passed")
        self.assertIn("@v7", result["rejected_reference"])

    def test_provenance_attachment_is_idempotent(self):
        bundle = self.write_bundle(self.root / "bundle")
        provenance = bundle / "provenance.json"
        before = json.loads(provenance.read_text(encoding="utf-8"))
        attach_provenance(
            bundle / "build-environment.inventory.json",
            bundle / "build-environment.spdx.json",
            provenance,
            COMMIT,
        )
        after = json.loads(provenance.read_text(encoding="utf-8"))
        self.assertEqual(before, after)

    def test_two_runner_build_environment_verification(self):
        first = self.write_bundle(self.root / "runner-a")
        second = self.write_bundle(self.root / "runner-b")
        output = self.root / "verification.json"
        result = verify_bundles(first, second, COMMIT, output)
        self.assertTrue(result["build_environment_identical"])
        self.assertTrue(result["checks"]["spdx_sbom_identical"])
        self.assertTrue(output.is_file())

    def test_tampered_second_runner_inventory_rejected(self):
        first = self.write_bundle(self.root / "runner-a")
        second = self.write_bundle(self.root / "runner-b")
        path = second / "build-environment.inventory.json"
        path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "namespace does not bind|hashes do not match"):
            verify_bundles(first, second, COMMIT, self.root / "verification.json")

    def test_runner_image_mismatch_fails_cross_runner_gate(self):
        first = self.write_bundle(self.root / "runner-a")
        second = self.write_bundle(self.root / "runner-b")
        inventory_path = second / "build-environment.inventory.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        inventory["runner"]["image_version"] = "different-image"
        inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        sbom = make_spdx(inventory, hashlib.sha256(inventory_path.read_bytes()).hexdigest())
        sbom_path = second / "build-environment.spdx.json"
        sbom_path.write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        provenance_path = second / "provenance.json"
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        provenance.pop("build_environment_sbom", None)
        provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        attach_provenance(inventory_path, sbom_path, provenance_path, COMMIT)
        with self.assertRaisesRegex(ValueError, "not identical"):
            verify_bundles(first, second, COMMIT, self.root / "verification.json")


class WorkflowIntegrationTests(unittest.TestCase):
    def test_ci003_workflow_generates_attaches_and_verifies_build_environment_sbom(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/ci003-reproducibility.yml").read_text(encoding="utf-8")
        self.assertIn("build_environment_sbom.py generate", workflow)
        self.assertIn('cat /etc/os-release > "$RUNNER_TEMP/ci003-os-release.txt"', workflow)
        self.assertIn('--os-release-file "$RUNNER_TEMP/ci003-os-release.txt"', workflow)
        self.assertIn("--root-gradle-file build.gradle.kts", workflow)
        self.assertIn("build_environment_sbom.py attach", workflow)
        self.assertIn("build_environment_sbom.py negative-control", workflow)
        self.assertIn("build_environment_sbom.py verify", workflow)
        self.assertIn("build-environment.inventory.json", workflow)
        self.assertIn("build-environment.spdx.json", workflow)
        self.assertIn("build-environment-verification.json", workflow)


if __name__ == "__main__":
    unittest.main()
