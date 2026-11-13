package tech.mrnothing.os

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.nio.charset.StandardCharsets
import java.security.MessageDigest

/**
 * SEC-023B1B2A: dormant, one-shot, owner-visible encrypted-memory consent intent.
 *
 * This is a pure policy/preview, NOT an Android credential prompt or a grant.
 * Inputs are caller assertions; the eventual Activity must derive profile, signing
 * identity, device state, nonce and consent from trusted Android APIs/UI.
 * Even a positive finish result MUST NOT create a key or enable persistence:
 * a separate genuine Android Keystore CryptoObject proof and independent
 * security review are required. No memory is read, written or retained here.
 */
internal data class MemoryVaultConsentSnapshot(
    val ownerUserId: Int,
    val appSigningSha256: String,
    val retentionDays: Int,
    val requestNonceHex: String,
    val foregroundOwnerUi: Boolean,
    val deviceUnlocked: Boolean,
    val secureCredentialConfigured: Boolean,
    val explicitCheckboxChecked: Boolean,
    val strongBoxAdvertised: Boolean,
    val aliasAbsent: Boolean
)

internal data class MemoryVaultConsentPreview(
    val title: String,
    val disclosure: String,
    val retentionDays: Int,
    val bindingSha256: String
)

internal enum class MemoryVaultConsentProgress {
    BLOCKED,
    AWAITING_CRYPTOOBJECT_PROOF
}


/**
 * SEC-023B1B2A-N: reusable local CSPRNG nonce formatting for a future trusted UI.
 * Reuses the existing 32-byte Android owner-attestation challenge generator;
 * does NOT attest the UI, device identity, user presence or consent.
 * The UI must call this locally for each new ceremony, not accept agent input.
 */
internal object MemoryVaultConsentNonce {
    fun freshHex(): String {
        val bytes = OwnerAttestationChallenge.create()
        return try {
            check(bytes.size == 32) { "Unexpected nonce size" }
            bytes.joinToString("") { "%02x".format(it.toInt() and 0xff) }
        } finally {
            bytes.fill(0)
        }
    }
}

/**
 * One attempt per instance. Reuses the existing 30-second monotonic,
 * consume-on-mismatch OwnerAuthorityConfirmationState instead of inventing
 * a second timeout/token implementation.
 */
internal class MemoryVaultConsentCeremony(clockNanos: () -> Long) {
    private val confirmation = OwnerAuthorityConfirmationState(clockNanos)
    private var attempted = false

    @Synchronized
    fun begin(snapshot: MemoryVaultConsentSnapshot): MemoryVaultConsentPreview? {
        if (attempted) return null
        attempted = true
        val binding = bindingFor(snapshot) ?: return null
        if (!confirmation.begin(binding)) return null
        return MemoryVaultConsentPreview(
            title = "Enable encrypted memory on this device?",
            disclosure = "Requires a fresh owner credential and hardware-backed key. " +
                "No cloud sync. You can revoke future storage; retention is limited " +
                "to the selected number of days. Nothing is enabled by this preview.",
            retentionDays = snapshot.retentionDays,
            bindingSha256 = binding
        )
    }

    /** Reported credential success is only a prerequisite, NEVER proof of key use. */
    @Synchronized
    fun finish(
        snapshot: MemoryVaultConsentSnapshot,
        platformCredentialReported: Boolean
    ): MemoryVaultConsentProgress {
        val binding = bindingFor(snapshot) ?: ""
        return if (confirmation.finish(binding, platformCredentialReported)) {
            MemoryVaultConsentProgress.AWAITING_CRYPTOOBJECT_PROOF
        } else {
            MemoryVaultConsentProgress.BLOCKED
        }
    }

    /** Cancel, backgrounding, owner change and process lifecycle teardown call this. */
    @Synchronized
    fun revoke() {
        attempted = true
        confirmation.revoke()
    }

    companion object {
        // SEC-023B1B1 key-spec is present in this draft stack; no runtime key use is enabled.
        private const val PURPOSE = "MRNOTHING-MEMORY-OWNER-CONSENT-V1"
        private const val KEY_ALIAS = "mrnothing_memory_vault_aes_gcm_v1"
        private val sha256Hex = Regex("^[0-9a-f]{64}$")

        /**
         * Domain-separated, unambiguous length-prefixed ASCII serialization.
         * The 256-bit request nonce must come from a CSPRNG in the eventual
         * trusted Android UI. This class cannot attest to entropy/provenance.
         */
        internal fun bindingFor(snapshot: MemoryVaultConsentSnapshot): String? {
            if (snapshot.ownerUserId != 0 ||
                snapshot.retentionDays !in 1..90 ||
                !sha256Hex.matches(snapshot.appSigningSha256) ||
                !sha256Hex.matches(snapshot.requestNonceHex) ||
                !snapshot.foregroundOwnerUi ||
                !snapshot.deviceUnlocked ||
                !snapshot.secureCredentialConfigured ||
                !snapshot.explicitCheckboxChecked ||
                !snapshot.strongBoxAdvertised ||
                !snapshot.aliasAbsent
            ) return null

            val bytes = ByteArrayOutputStream()
            DataOutputStream(bytes).use { out ->
                listOf(
                    PURPOSE,
                    KEY_ALIAS,
                    snapshot.ownerUserId.toString(),
                    snapshot.appSigningSha256,
                    snapshot.retentionDays.toString(),
                    snapshot.requestNonceHex
                ).forEach { field ->
                    val encoded = field.toByteArray(StandardCharsets.US_ASCII)
                    out.writeInt(encoded.size)
                    out.write(encoded)
                }
            }
            return MessageDigest.getInstance("SHA-256").digest(bytes.toByteArray())
                .joinToString("") { "%02x".format(it.toInt() and 0xff) }
        }
    }
}
