"""SEC-014J: read-only alias collision checks; not Android runtime proof."""
from pathlib import Path
import unittest

SRC = Path(__file__).resolve().parents[1] / "android/app/src/main/java/tech/mrnothing/os"


class OwnerEnrollmentAliasGateSourceTests(unittest.TestCase):
    def test_inspection_does_not_mutate_keys_or_issue_consent(self):
        code = (SRC / "OwnerEnrollmentAliasGate.kt").read_text()
        for required in ("store.containsAlias(OwnerKeystorePreflight.KEY_ALIAS)",
                         "OwnerKeystorePreflight.inspectExisting()",
                         "INSPECTION_FAILED", "UNTRUSTED_EXISTING"):
            self.assertIn(required, code)
        for forbidden in ("generateKeyPair(", "deleteEntry(", "setEntry(",
                          "Signature.getInstance(", "CommandRouter(",
                          "ConsentCapability(", "startActivityForResult("):
            self.assertNotIn(forbidden, code)

    def test_alias_gate_runs_before_credential_prompt(self):
        code = (SRC / "OwnerKeyEnrollmentActivity.kt").read_text()
        self.assertLess(code.index("OwnerEnrollmentAliasGate.inspect()"),
                        code.index("state.begin()"))
        self.assertLess(code.index("OwnerEnrollmentAliasGate.inspect()"),
                        code.index("createConfirmDeviceCredentialIntent("))

    def test_collision_and_inspection_failure_block_with_explicit_status(self):
        code = (SRC / "OwnerKeyEnrollmentActivity.kt").read_text()
        for token in ("OwnerEnrollmentAliasState.UNTRUSTED_EXISTING",
                      "OwnerEnrollmentAliasState.INSPECTION_FAILED",
                      "Untrusted existing key alias. Enrollment refused",
                      "KeyStore inspection unavailable. Enrollment refused"):
            self.assertIn(token, code)


if __name__ == "__main__":
    unittest.main()
