#!/usr/bin/env python3
"""SEC-023B1B2B: source-only MemoryVault integration readiness audit.

This cannot approve cryptography, Android runtime behavior, or a release. Even
with all structural checks satisfied, the strongest result is REVIEW_REQUIRED.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"
PACKAGE = "android/app/src/main/java/tech/mrnothing/os"
MANIFEST = "android/app/src/main/AndroidManifest.xml"
KEY_ALIAS = "mrnothing_memory_vault_aes_gcm_v1"
COMPONENTS = {
    "design": "docs/SEC-023-OWNER-AUTHENTICATED-ENCRYPTED-MEMORY-DESIGN.md",
    "envelope": "core/memory_vault_schema.py",
    "admission": f"{PACKAGE}/MemoryVaultAdmissionPolicy.kt",
    "service": f"{PACKAGE}/MemoryVaultService.kt",
    "keystore_preflight": f"{PACKAGE}/MemoryVaultKeystorePreflight.kt",
    "provisioning": f"{PACKAGE}/MemoryVaultProvisioningPolicy.kt",
    "consent": f"{PACKAGE}/MemoryVaultConsentCeremony.kt",
    "adapter": "PROJECT-ADAPTER.md",
}
ALIAS_SOURCES = ("keystore_preflight", "provisioning", "consent")


def audit(root: Path) -> dict:
    """Return structural findings, never a security approval."""
    root = Path(root)
    findings = []
    missing = sorted(name for name, relative in COMPONENTS.items()
                     if not (root / relative).is_file())
    if missing:
        findings.append("missing_component:" + ",".join(missing))

    manifest_path = root / MANIFEST
    if not manifest_path.is_file():
        findings.append("missing_manifest")
    else:
        try:
            app = ET.parse(manifest_path).getroot().find("application")
            if app is None:
                findings.append("missing_application")
            else:
                services = [node for node in app.findall("service")
                            if node.get(ANDROID_NS + "name") in
                            (".MemoryVaultService", "tech.mrnothing.os.MemoryVaultService")]
                if len(services) != 1:
                    findings.append("memory_vault_service_count_not_one")
                else:
                    service = services[0]
                    if service.get(ANDROID_NS + "enabled") != "false":
                        findings.append("memory_vault_service_not_disabled")
                    if service.get(ANDROID_NS + "exported") != "false":
                        findings.append("memory_vault_service_exported")
                    if list(service.findall("intent-filter")):
                        findings.append("memory_vault_service_has_intent_filter")
        except ET.ParseError:
            findings.append("invalid_manifest_xml")
        except OSError:
            findings.append("unreadable_manifest")

    for name in ALIAS_SOURCES:
        path = root / COMPONENTS[name]
        if not path.is_file():
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            findings.append(f"unreadable_{name}")
            continue
        matches = re.findall(r'\bKEY_ALIAS\s*=\s*"([^"]+)"', source)
        if len(matches) != 1 or matches[0] != KEY_ALIAS:
            findings.append(f"key_alias_mismatch:{name}")

    service_path = root / COMPONENTS["service"]
    if service_path.is_file():
        try:
            service_source = service_path.read_text(encoding="utf-8")
            if not all(token in service_source for token in
                       ("onBind(", "IBinder? = null", "stopSelfResult(startId)",
                        "START_NOT_STICKY")):
                findings.append("service_dormant_source_contract_missing")
        except (OSError, UnicodeError):
            findings.append("unreadable_service")

    consent_path = root / COMPONENTS["consent"]
    if consent_path.is_file():
        try:
            consent_source = consent_path.read_text(encoding="utf-8")
            if "AWAITING_CRYPTOOBJECT_PROOF" not in consent_source:
                findings.append("consent_proof_boundary_missing")
            if any(token in consent_source for token in
                   ("KeyGenerator.getInstance(", "Cipher.getInstance(",
                    "openFileOutput(", "save_memory(")):
                findings.append("consent_unexpected_side_effect_api")
        except (OSError, UnicodeError):
            findings.append("unreadable_consent")

    return {
        "schema": "SEC-023B1B2B-source-audit-v1",
        "status": "BLOCKED" if findings else "REVIEW_REQUIRED",
        "missing_components": missing,
        "findings": sorted(findings),
        "independent_security_review": "PENDING",
        "runtime_crypto_proof": "NOT_EVALUATED",
        "physical_pixel_validation": "NOT_EVALUATED",
        "note": "Source-only preflight. REVIEW_REQUIRED is not authorization, release approval, or proof of integration.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    result = audit(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    # Never return a successful exit code: this tool cannot approve the release.
    return 2 if result["status"] == "BLOCKED" else 3


if __name__ == "__main__":
    sys.exit(main())
