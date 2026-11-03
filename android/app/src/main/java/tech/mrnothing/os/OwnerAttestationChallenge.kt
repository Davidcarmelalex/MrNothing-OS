package tech.mrnothing.os

import java.security.MessageDigest
import java.security.SecureRandom

/**
 * SEC-014K: local attestation-challenge matching only. The untrusted X.509
 * extension is NOT evidence of a trusted certificate chain or remote owner.
 * No command signing, owner binding, agent permission or network access.
 */
internal object OwnerAttestationChallenge {
    const val EXTENSION_OID = "1.3.6.1.4.1.11129.2.1.17"
    private const val NONCE_BYTES = 32
    private const val MAX_EXTENSION_BYTES = 8192

    fun create(): ByteArray = ByteArray(NONCE_BYTES).also {
        SecureRandom().nextBytes(it)
    }

    /**
     * Android X.509 getExtensionValue returns a DER OCTET STRING containing
     * the Android KeyDescription SEQUENCE. Check nonce and both security-level
     * ENUMERATED fields (2=StrongBox), not certificate trust or verified boot.
     */
    fun matchesLocalEvidence(extension: ByteArray?, expected: ByteArray): Boolean {
        if (expected.size != NONCE_BYTES || extension == null ||
            extension.isEmpty() || extension.size > MAX_EXTENSION_BYTES
        ) return false
        return try {
            val outer = DerCursor(extension)
            val description = outer.read(0x04) ?: return false
            if (!outer.finished()) return false
            val document = DerCursor(description)
            val sequence = document.read(0x30) ?: return false
            if (!document.finished()) return false
            val key = DerCursor(sequence)
            if (!key.integerPresent()) return false
            if (key.securityLevel() != 2) return false
            if (!key.integerPresent()) return false
            if (key.securityLevel() != 2) return false
            val nonce = key.read(0x04) ?: return false
            if (!MessageDigest.isEqual(nonce, expected)) return false
            if (key.read(0x04) == null) return false // uniqueId
            if (key.read(0x30) == null) return false // softwareEnforced
            if (key.read(0x30) == null) return false // teeEnforced
            key.finished()
        } catch (_: RuntimeException) {
            false
        }
    }

    /** Strict, size-bounded DER cursor; rejects indefinite/nonminimal lengths. */
    private class DerCursor(private val data: ByteArray) {
        private var index = 0
        fun finished() = index == data.size

        fun read(tag: Int): ByteArray? {
            if (index >= data.size || (data[index++].toInt() and 255) != tag ||
                index >= data.size
            ) return null
            val initial = data[index++].toInt() and 255
            val length = if (initial < 128) initial else {
                val count = initial and 127
                if (count == 0 || count > 2 || index + count > data.size ||
                    (data[index].toInt() and 255) == 0
                ) return null
                var n = 0
                repeat(count) { n = (n shl 8) or (data[index++].toInt() and 255) }
                if (n < 128 || (count == 2 && n < 256)) return null
                n
            }
            if (length > data.size - index) return null
            val value = data.copyOfRange(index, index + length)
            index += length
            return value
        }

        fun integerPresent(): Boolean {
            val value = read(0x02) ?: return false
            return value.isNotEmpty() && value.size <= 4 &&
                (value[0].toInt() and 0x80) == 0 &&
                !(value.size > 1 && value[0] == 0.toByte() &&
                    (value[1].toInt() and 0x80) == 0)
        }

        fun securityLevel(): Int? {
            val value = read(0x0a) ?: return null
            return if (value.size == 1) value[0].toInt() and 255 else null
        }
    }
}
