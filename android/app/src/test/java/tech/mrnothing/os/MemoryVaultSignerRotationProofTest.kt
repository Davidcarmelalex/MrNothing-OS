package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.MessageDigest
import java.security.Signature

/** Synthetic software-key tests only. No Android owner, StrongBox or rollback proof. */
class MemoryVaultSignerRotationProofTest {
    private val old = KeyPairGenerator.getInstance("Ed25519").generateKeyPair()
    private val next = KeyPairGenerator.getInstance("Ed25519").generateKeyPair()
    private val blocked = MemoryVaultSignerRotationOutcome.BLOCKED
    private val diagnostic = MemoryVaultSignerRotationOutcome.DUAL_SIGNATURES_VALID_NOT_AUTHORIZED
    private val policy = MemoryVaultSignerRotationProof
    private fun hash(b: ByteArray) = MessageDigest.getInstance("SHA-256").digest(b)
    private fun sign(pair: KeyPair, message: ByteArray): ByteArray =
        Signature.getInstance("Ed25519").run {
            initSign(pair.private); update(message); sign()
        }

    private fun proof(
        oldPair: KeyPair = old,
        nextPair: KeyPair = next,
        previous: Long = 7,
        candidate: Long = 8,
        owner: Int = 0,
        nonce: String = "a".repeat(64)
    ): MemoryVaultSignerRotationEvidence {
        val unsigned = MemoryVaultSignerRotationEvidence(
            previous, candidate, owner, nonce,
            oldPair.public.encoded, nextPair.public.encoded,
            hash(oldPair.public.encoded), hash(nextPair.public.encoded),
            ByteArray(64), ByteArray(64)
        )
        val message = policy.payload(unsigned) ?: return unsigned
        return unsigned.copy(
            oldSignerSignature = sign(oldPair, message),
            newSignerSignature = sign(nextPair, message)
        )
    }

    @Test fun validDualSignatureIsDiagnosticOnly() {
        assertEquals(diagnostic, policy.inspect(proof()))
    }

    @Test fun missingEvidenceBlocks() { assertEquals(blocked, policy.inspect(null)) }
    @Test fun missingOldSignatureBlocks() {
        assertEquals(blocked, policy.inspect(proof().copy(oldSignerSignature = ByteArray(0))))
    }
    @Test fun missingNewSignatureBlocks() {
        assertEquals(blocked, policy.inspect(proof().copy(newSignerSignature = ByteArray(0))))
    }
    @Test fun wrongOldSignerBlocks() {
        val p = proof()
        val attacker = KeyPairGenerator.getInstance("Ed25519").generateKeyPair()
        val message = policy.payload(p)!!
        assertEquals(blocked, policy.inspect(p.copy(oldSignerSignature = sign(attacker, message))))
    }
    @Test fun wrongNewSignerBlocks() {
        val p = proof()
        val attacker = KeyPairGenerator.getInstance("Ed25519").generateKeyPair()
        assertEquals(blocked, policy.inspect(p.copy(newSignerSignature = sign(attacker, policy.payload(p)!!))))
    }
    @Test fun modifiedOldPinBlocks() {
        assertEquals(blocked, policy.inspect(proof().copy(externallyPinnedOldKeySha256 = ByteArray(32) { 1 })))
    }
    @Test fun modifiedNewPinBlocks() {
        assertEquals(blocked, policy.inspect(proof().copy(expectedNewKeySha256 = ByteArray(32) { 2 })))
    }
    @Test fun changedNonceInvalidatesSignatures() {
        assertEquals(blocked, policy.inspect(proof().copy(requestNonceHex = "b".repeat(64))))
    }
    @Test fun changedGenerationInvalidatesSignatures() {
        assertEquals(blocked, policy.inspect(proof().copy(previousGeneration = 8, candidateGeneration = 9)))
    }
    @Test fun wrongOwnerBlocks() {
        assertEquals(blocked, policy.inspect(proof(owner = 10)))
    }
    @Test fun nonAdjacentGenerationBlocks() {
        assertEquals(blocked, policy.inspect(proof(previous = 7, candidate = 9)))
    }
    @Test fun overflowGenerationBlocks() {
        assertEquals(blocked, policy.inspect(proof(previous = Long.MAX_VALUE - 1, candidate = Long.MAX_VALUE)))
    }
    @Test fun sameSignerKeyBlocks() {
        val p = proof(nextPair = old)
        assertEquals(blocked, policy.inspect(p))
    }
    @Test fun malformedOldPublicKeyBlocks() {
        assertEquals(blocked, policy.inspect(proof().copy(oldPublicKeyX509Der = ByteArray(50))))
    }
    @Test fun malformedNewPublicKeyBlocks() {
        assertEquals(blocked, policy.inspect(proof().copy(newPublicKeyX509Der = ByteArray(50))))
    }
    @Test fun malformedNonceBlocks() {
        assertNull(policy.payload(proof().copy(requestNonceHex = "z".repeat(64))))
    }
    @Test fun uppercaseNonceBlocks() {
        assertEquals(blocked, policy.inspect(proof().copy(requestNonceHex = "A".repeat(64))))
    }
    @Test fun truncatedSignatureBlocks() {
        assertEquals(blocked, policy.inspect(proof().copy(newSignerSignature = ByteArray(63))))
    }
    @Test fun callerSuppliedPinsCannotProveIndependentProvenance() {
        // Matching pins and signatures do not attest who supplied the old pin.
        assertEquals(diagnostic, policy.inspect(proof()))
    }
    @Test fun wholeStateReplayStillPassesOfflineDiagnostics() {
        // Requires a separate trusted monotonic nonce/watermark authority.
        val oldSnapshot = proof()
        assertEquals(diagnostic, policy.inspect(oldSnapshot))
        assertEquals(diagnostic, policy.inspect(oldSnapshot))
    }
    @Test fun mutatedEvidenceAfterSigningBlocks() {
        val p = proof()
        p.expectedNewKeySha256[0] = (p.expectedNewKeySha256[0].toInt() xor 1).toByte()
        assertEquals(blocked, policy.inspect(p))
    }
    @Test fun untrustedBootstrapCannotBeAccepted() {
        // First install cannot supply an independently anchored previous signer.
        assertEquals(blocked, policy.inspect(null))
    }
}
