"""Exercise product inheritance with GNU make, without pretending to build AOSP."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / "rom/aosp/caiman"


@unittest.skipUnless(shutil.which("make"), "GNU make unavailable on host")
class CaimanProductMakeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vendor = self.root / "device/google/caimito"
        self.vendor.mkdir(parents=True)
        # A fake upstream with deliberately different identity and mandatory
        # recovery packages: tests exercise real make expansion/inheritance.
        (self.vendor / "aosp_caiman.mk").write_text(
            "PRODUCT_NAME := aosp_caiman\nPRODUCT_DEVICE := caiman\n"
            "PRODUCT_PACKAGES += Launcher3QuickStep UpstreamRecovery\n",
            encoding="utf-8")
        self.product = self.root / "device/mrnothing/caiman"
        shutil.copytree(PRODUCT, self.product)
        self.driver = self.root / "driver.mk"
        self.driver.write_text(
            "define inherit-product\n$(eval include $(1))\nendef\n"
            "include device/mrnothing/caiman/mrnothing_caiman.mk\n"
            ".PHONY: inspect\ninspect:\n"
            "\t@echo name=$(PRODUCT_NAME)\n"
            "\t@echo device=$(PRODUCT_DEVICE)\n"
            "\t@echo packages=$(PRODUCT_PACKAGES)\n"
            "\t@echo namespaces=$(PRODUCT_SOONG_NAMESPACES)\n",
            encoding="utf-8")

    def run_make(self, variant):
        return subprocess.run(
            ["make", "--no-print-directory", "-f", "driver.mk", "inspect",
             "TARGET_BUILD_VARIANT=" + variant],
            cwd=self.root, capture_output=True, text=True, timeout=10)

    def test_inherits_hardware_and_preserves_recovery_packages(self):
        result = self.run_make("userdebug")
        self.assertEqual(0, result.returncode, result.stderr)
        lines = dict(line.split("=", 1) for line in result.stdout.splitlines())
        self.assertEqual("mrnothing_caiman", lines["name"])
        self.assertEqual("caiman", lines["device"])
        self.assertEqual(["Launcher3QuickStep", "UpstreamRecovery", "MrNothingLauncher"],
                         lines["packages"].split())
        self.assertIn("device/mrnothing/caiman", lines["namespaces"].split())

    def test_refuses_release_and_eng_variants(self):
        for variant in ("user", "eng", ""):
            with self.subTest(variant=variant):
                result = self.run_make(variant)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("engineering userdebug builds only", result.stderr)

    def test_missing_upstream_is_hard_failure(self):
        (self.vendor / "aosp_caiman.mk").unlink()
        self.assertNotEqual(0, self.run_make("userdebug").returncode)

    def test_registered_product_resolves_to_existing_makefile(self):
        self.driver.write_text(
            "LOCAL_DIR := device/mrnothing/caiman\n"
            "include $(LOCAL_DIR)/AndroidProducts.mk\n"
            "inspect:\n\t@test -f $(PRODUCT_MAKEFILES)\n"
            "\t@echo $(COMMON_LUNCH_CHOICES)\n", encoding="utf-8")
        result = self.run_make("userdebug")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("mrnothing_caiman-trunk_staging-userdebug", result.stdout.strip())
