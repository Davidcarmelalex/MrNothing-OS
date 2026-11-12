import json
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

from scripts.ci003_artifacts import (
    compare_apks, generate_provenance, generate_sbom, inspect_unsigned_apk, verify_bundles
)

COMMIT = "a" * 40
ENVIRONMENT = {
    "operating_system": "ubuntu-24.04", "jdk_distribution": "Temurin",
    "jdk_version": "17.0.13+11", "gradle_version": "8.9", "gradle_sha256": "d" * 64,
    "agp_version": "8.7.3", "kotlin_version": "2.0.21", "compile_sdk": "35",
    "build_tools": "35.0.0", "sdkmanager_version": "19.0",
}

def make_variant_metadata(path: Path, application_id="tech.mrnothing.os"):
    path.write_text(json.dumps({
        "schema": "mrnothing-gradle-release-variant-v1",
        "applicationId": application_id,
        "variantName": "release",
        "buildType": "release",
    }, sort_keys=True) + "\n", encoding="utf-8")
    return path

def make_apk(path: Path, entries=None, timestamp=(2026, 1, 1, 0, 0, 0)):
    entries = entries or {"AndroidManifest.xml": b"manifest", "classes.dex": b"dex"}
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            info = zipfile.ZipInfo(name, date_time=timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)

class CI003ArtifactTests(unittest.TestCase):
    def test_unsigned_apk_inspection(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "app.apk"; make_apk(apk)
            result = inspect_unsigned_apk(apk)
            self.assertEqual(result["signature_status"], "unsigned")
            self.assertEqual(result["entry_count"], 2)

    def test_byte_identical_apks_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "a.apk", Path(directory) / "b.apk"
            make_apk(first); make_apk(second)
            result = compare_apks(first, second)
            self.assertTrue(result["reproducible"])
            self.assertTrue(result["normalized_content_identical"])

    def test_zip_timestamp_variance_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "a.apk", Path(directory) / "b.apk"
            make_apk(first, timestamp=(2026, 1, 1, 0, 0, 0))
            make_apk(second, timestamp=(2026, 1, 2, 0, 0, 0))
            result = compare_apks(first, second)
            self.assertFalse(result["byte_identical"])
            self.assertTrue(result["normalized_content_identical"])
            self.assertFalse(result["reproducible"])

    def test_different_entry_content_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "a.apk", Path(directory) / "b.apk"
            make_apk(first, {"classes.dex": b"one"})
            make_apk(second, {"classes.dex": b"two"})
            self.assertFalse(compare_apks(first, second)["normalized_content_identical"])

    def test_v1_signature_entry_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "signed.apk"
            make_apk(apk, {"META-INF/CERT.SF": b"signature", "classes.dex": b"dex"})
            with self.assertRaisesRegex(ValueError, "v1 signing entry"):
                inspect_unsigned_apk(apk)

    def test_unsafe_zip_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "unsafe.apk"; make_apk(apk, {"../outside": b"bad"})
            with self.assertRaisesRegex(ValueError, "unsafe ZIP entry path"):
                inspect_unsigned_apk(apk)

    def test_duplicate_zip_names_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "duplicate.apk"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(apk, "w") as archive:
                    archive.writestr("classes.dex", b"one"); archive.writestr("classes.dex", b"two")
            with self.assertRaisesRegex(ValueError, "duplicate ZIP entry"):
                inspect_unsigned_apk(apk)

    def test_spdx_sbom_is_deterministic_and_has_checksums(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); inventory = root / "inventory.tsv"
            inventory.write_text("org.example\tengine\t1.2.3\tengine-1.2.3.jar\t" + "b" * 64 + "\n", encoding="utf-8")
            first, second = root / "first.json", root / "second.json"
            document = generate_sbom(inventory, COMMIT, "0.1.0-dev", 1760000000, first)
            generate_sbom(inventory, COMMIT, "0.1.0-dev", 1760000000, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(document["spdxVersion"], "SPDX-2.3")
            self.assertEqual(len(document["packages"]), 2)
            dependency = next(item for item in document["packages"] if item["name"] == "org.example:engine")
            self.assertEqual(dependency["checksums"][0]["checksumValue"], "b" * 64)

    def test_malformed_runtime_inventory_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            inventory = Path(directory) / "inventory.tsv"
            inventory.write_text("org.example\tlib\t1.0\tlib.jar\tbad\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid SHA-256"):
                generate_sbom(inventory, COMMIT, "0.1.0-dev", 1760000000, Path(directory) / "out.json")

    def test_provenance_is_unsigned_and_non_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); apk = root / "app-release-unsigned.apk"; make_apk(apk)
            inventory = root / "inventory.tsv"; inventory.write_text("", encoding="utf-8")
            sbom = root / "sbom.spdx.json"
            generate_sbom(inventory, COMMIT, "0.1.0-dev", 1760000000, sbom)
            variant_metadata = make_variant_metadata(root / "release-variant-metadata.json")
            record = generate_provenance(
                apk, sbom, COMMIT, 1760000000, ENVIRONMENT, variant_metadata, root / "provenance.json"
            )
            self.assertEqual(record["schema"], "mrnothing-ci003-provenance-v2")
            self.assertEqual(record["release_variant"]["application_id"], "tech.mrnothing.os")
            self.assertEqual(record["artifact"]["signature_status"], "unsigned")
            self.assertFalse(record["release_ready"]); self.assertFalse(record["provenance_signed"])

    def test_two_runner_bundles_verify(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); bundles = [root / "runner-a", root / "runner-b"]
            for bundle in bundles:
                bundle.mkdir(); apk = bundle / "app-release-unsigned.apk"; make_apk(apk)
                inventory = bundle / "release-runtime-dependencies.tsv"; inventory.write_text("", encoding="utf-8")
                sbom = bundle / "sbom.spdx.json"
                generate_sbom(inventory, COMMIT, "0.1.0-dev", 1760000000, sbom)
                variant_metadata = make_variant_metadata(bundle / "release-variant-metadata.json")
                generate_provenance(
                    apk, sbom, COMMIT, 1760000000, ENVIRONMENT, variant_metadata, bundle / "provenance.json"
                )
            report = verify_bundles(bundles[0], bundles[1], COMMIT)
            self.assertTrue(report["reproducible"]); self.assertFalse(report["release_ready"])
            self.assertTrue(report["checks"]["release_variant_identical"])
            self.assertEqual(report["release_variant"]["application_id"], "tech.mrnothing.os")

    def test_two_runner_bundle_commit_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); bundles = [root / "runner-a", root / "runner-b"]
            for bundle in bundles:
                bundle.mkdir(); apk = bundle / "app-release-unsigned.apk"; make_apk(apk)
                inventory = bundle / "release-runtime-dependencies.tsv"; inventory.write_text("", encoding="utf-8")
                sbom = bundle / "sbom.spdx.json"
                generate_sbom(inventory, COMMIT, "0.1.0-dev", 1760000000, sbom)
                variant_metadata = make_variant_metadata(bundle / "release-variant-metadata.json")
                generate_provenance(
                    apk, sbom, COMMIT, 1760000000, ENVIRONMENT, variant_metadata, bundle / "provenance.json"
                )
            with self.assertRaisesRegex(ValueError, "source commit"):
                verify_bundles(bundles[0], bundles[1], "c" * 40)

    def test_bundle_variant_metadata_must_match_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); bundles = [root / "runner-a", root / "runner-b"]
            for bundle in bundles:
                bundle.mkdir(); apk = bundle / "app-release-unsigned.apk"; make_apk(apk)
                inventory = bundle / "release-runtime-dependencies.tsv"; inventory.write_text("", encoding="utf-8")
                sbom = bundle / "sbom.spdx.json"
                generate_sbom(inventory, COMMIT, "0.1.0-dev", 1760000000, sbom)
                variant_metadata = make_variant_metadata(bundle / "release-variant-metadata.json")
                generate_provenance(
                    apk, sbom, COMMIT, 1760000000, ENVIRONMENT, variant_metadata, bundle / "provenance.json"
                )
            make_variant_metadata(bundles[1] / "release-variant-metadata.json", "tech.mrnothing.other")
            with self.assertRaisesRegex(ValueError, "does not match provenance"):
                verify_bundles(bundles[0], bundles[1], COMMIT)

if __name__ == "__main__":
    unittest.main()
