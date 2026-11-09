"""Independent SHA-256 reference vectors for dormant MemoryVault consent binding.

Does not import or execute Kotlin. The hosted Android/JUnit job checks Kotlin
against these fixed constants; this suite protects the independently derived
serialization contract against accidental edits.
"""
import hashlib
import struct
import unittest


PURPOSE = "MRNOTHING-MEMORY-OWNER-CONSENT-V1"
ALIAS = "mrnothing_memory_vault_aes_gcm_v1"
VECTOR_A = "a813f8bf88f1a515d7e3b1a0e9964430f96a15de43929e8c63d5ecad2afd8ed4"
VECTOR_B = "159612156d4e2fd250882f3840ade57d9ccc0f4949b82840e3312637084547d3"


def reference_digest(*fields):
    out = bytearray()
    for field in fields:
        encoded = field.encode("ascii")
        out += struct.pack(">I", len(encoded))
        out += encoded
    return hashlib.sha256(out).hexdigest()


class MemoryVaultConsentVectorsTest(unittest.TestCase):
    def test_default_retention_reference_vector(self):
        self.assertEqual(
            VECTOR_A,
            reference_digest(PURPOSE, ALIAS, "0", "a" * 64, "30", "b" * 64),
        )

    def test_second_reference_vector(self):
        self.assertEqual(
            VECTOR_B,
            reference_digest(PURPOSE, ALIAS, "0", "c" * 64, "90", "d" * 64),
        )

    def test_ambiguous_delimiter_format_must_not_match(self):
        fields = (PURPOSE, ALIAS, "0", "a" * 64, "30", "b" * 64)
        self.assertNotEqual(
            VECTOR_A, hashlib.sha256("|".join(fields).encode("ascii")).hexdigest()
        )

    def test_little_endian_length_prefix_must_not_match(self):
        fields = (PURPOSE, ALIAS, "0", "a" * 64, "30", "b" * 64)
        payload = b"".join(
            struct.pack("<I", len(s)) + s.encode("ascii") for s in fields
        )
        self.assertNotEqual(VECTOR_A, hashlib.sha256(payload).hexdigest())


if __name__ == "__main__":
    unittest.main()
