package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Test
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.MessageDigest
import java.security.Signature

/** Software-key JVM tests only: no independent trust domain or Pixel hardware. */
class MemoryVaultSignedWitnessPolicyTest {
    private val policy = MemoryVaultSignedWitnessPolicy
    private val blocked = MemoryVaultSignedWitnessOutcome.BLOCKED
    private val recovery = MemoryVaultSignedWitnessOutcome.RECOVERY_REQUIRED_NOT_AUTHORIZED
    private val diagnostic = MemoryVaultSignedWitnessOutcome.VERIFIED_PROVENANCE_NOT_AUTHORIZED
    private val pair: KeyPair = KeyPairGenerator.getInstance("Ed25519").generateKeyPair()
    private val record = MemoryVaultAnchorRecord(7L, ByteArray(32) { 7 }, ByteArray(32) { 8 })
    private val marker = MemoryVaultAnchorMarker(7L, record.generationId.copyOf())
    private val witness = MemoryVaultAnchorWitness(7L, MemoryVaultGenerationAnchorPolicy.commitment(record)!!)
    private val pub = pair.public.encoded
    private val pin = MessageDigest.getInstance("SHA-256").digest(pub)

    private fun sign(w: MemoryVaultAnchorWitness = witness, signingPair: KeyPair = pair): MemoryVaultSignedWitness {
        val signer = Signature.getInstance("Ed25519")
        signer.initSign(signingPair.private)
        signer.update(policy.payload(w)!!)
        return MemoryVaultSignedWitness(w, signer.sign())
    }

    private fun check(
        signed: MemoryVaultSignedWitness? = sign(),
        key: ByteArray? = pub,
        fingerprint: ByteArray? = pin,
        watermark: Long? = 7L,
        active: MemoryVaultAnchorRecord? = record,
        activeMarker: MemoryVaultAnchorMarker? = marker
    ) = policy.inspect(active, activeMarker, signed, key, fingerprint, watermark)

    @Test fun validSignatureIsDiagnosticNotAuthorization() {
        assertEquals(diagnostic, check())
    }

    @Test fun missingSignedWitnessBlocks() {
        assertEquals(blocked, check(signed = null))
    }

    @Test fun wrongSigningKeyBlocks() {
        val attacker = KeyPairGenerator.getInstance("Ed25519").generateKeyPair()
        assertEquals(blocked, check(signed = sign(signingPair = attacker)))
    }

    @Test fun wrongPinnedPublicKeyBlocks() {
        assertEquals(blocked, check(fingerprint = ByteArray(32) { 9 }))
    }

    @Test fun modifiedCommitmentBlocks() {
        val changed = MemoryVaultAnchorWitness(7L, ByteArray(32) { 4 })
        assertEquals(blocked, check(signed = sign(changed)))
    }

    @Test fun tamperedSignatureBlocks() {
        val signed = sign()
        val tampered = signed.signature.copyOf().also { it[0] = (it[0].toInt() xor 1).toByte() }
        assertEquals(blocked, check(signed = MemoryVaultSignedWitness(witness, tampered)))
    }

    @Test fun signedOldWitnessRequiresRecovery() {
        assertEquals(recovery, check(watermark = 8L))
    }

    @Test fun signedFutureWitnessBlocks() {
        assertEquals(blocked, check(watermark = 6L))
    }

    @Test fun forgedAllSnapshotsWithUnpinnedKeyBlocks() {
        val attacker = KeyPairGenerator.getInstance("Ed25519").generateKeyPair()
        val forged = MemoryVaultAnchorRecord(7L, ByteArray(32) { 10 }, ByteArray(32) { 11 })
        val forgedWitness = MemoryVaultAnchorWitness(7L, MemoryVaultGenerationAnchorPolicy.commitment(forged)!!)
        assertEquals(blocked, check(signed = sign(forgedWitness, attacker), active = forged,
            activeMarker = MemoryVaultAnchorMarker(7L, forged.generationId)))
    }

    @Test fun malformedPublicKeyBlocks() {
        assertEquals(blocked, check(key = ByteArray(50) { 0 }))
    }

    @Test fun invalidHighWatermarkBlocks() {
        assertEquals(blocked, check(watermark = 0L))
    }

    @Test fun truncatedSignatureBlocks() {
        assertEquals(blocked, check(signed = MemoryVaultSignedWitness(witness, ByteArray(63))))
    }
}
