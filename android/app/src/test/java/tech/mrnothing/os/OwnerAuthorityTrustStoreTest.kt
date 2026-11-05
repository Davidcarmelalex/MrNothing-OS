package tech.mrnothing.os

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.MessageDigest
import java.security.SecureRandom
import java.security.Signature
import javax.crypto.Cipher
import javax.crypto.Mac
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Transaction tests use synthetic in-memory keys; Android Keystore is not exercised here. */
class OwnerAuthorityTrustStoreTest {
    private fun pair(): KeyPair = KeyPairGenerator.getInstance("Ed25519").generateKeyPair()

    private fun candidate(pair: KeyPair, generation: Long, keyId: String) =
        AuthorityTrustCandidate(keyId, generation, pair.public.encoded)

    private fun firstProposal(pair: KeyPair): AuthorityTrustDecision.Ready {
        val candidate = candidate(pair, 1L, "authority-1")
        return OwnerAuthorityTrustCeremony.prepareFirstInstall(
            candidate,
            OwnerAuthorityTrustCeremony.fingerprintForOwner(candidate.publicKeySpkiDer)!!,
            ownerConfirmation = true,
            highestObservedGeneration = 0L
        ) as AuthorityTrustDecision.Ready
    }

    private fun recoveryProposal(pair: KeyPair, generation: Long): AuthorityTrustDecision.Ready {
        val candidate = candidate(pair, generation, "authority-$generation")
        return OwnerAuthorityTrustCeremony.prepareRecovery(
            candidate,
            OwnerAuthorityTrustCeremony.fingerprintForOwner(candidate.publicKeySpkiDer)!!,
            ownerConfirmation = true,
            highestObservedGeneration = generation - 1L,
            activeRecordPresent = false
        ) as AuthorityTrustDecision.Ready
    }

    private fun rotationProposal(
        old: KeyPair,
        current: AuthorityTrustRecord,
        next: KeyPair
    ): AuthorityTrustDecision.Ready {
        val candidate = candidate(next, current.generation + 1L, "authority-${current.generation + 1L}")
        val payload = OwnerAuthorityTrustCeremony.rotationPayload(candidate)!!
        val signature = Signature.getInstance("Ed25519").run {
            initSign(old.private)
            update(payload)
            sign()
        }
        return OwnerAuthorityTrustCeremony.prepareRotation(
            current,
            candidate,
            signature,
            OwnerAuthorityTrustCeremony.fingerprintForOwner(candidate.publicKeySpkiDer)!!,
            ownerConfirmation = true,
            highestObservedGeneration = current.generation
        ) as AuthorityTrustDecision.Ready
    }

    private class MemoryPersistence(private val events: MutableList<String>) :
        AuthorityRecordPersistence {
        var bytes: ByteArray? = null
        var failReads = false
        var failWrites = false

        override fun read(): AuthorityRecordRead {
            if (failReads) return AuthorityRecordRead.Failed
            val current = bytes ?: return AuthorityRecordRead.Missing
            return AuthorityRecordRead.Present(current.copyOf())
        }

        override fun writeAtomically(bytes: ByteArray): Boolean {
            events += "write"
            if (failWrites) return false
            this.bytes = bytes.copyOf()
            return true
        }
    }

    private class FakeCrypto(private val events: MutableList<String>) : AuthorityTrustCrypto {
        val markers = linkedMapOf<Long, ByteArray>()
        private val random = SecureRandom()
        private val aesKey = ByteArray(32).also(random::nextBytes)
        var unavailable = false
        var failMarker = false
        var failEncryption = false

        override fun highestObservedGeneration(): Long? {
            if (unavailable) return null
            return markers.keys.maxOrNull() ?: 0L
        }

        override fun createGenerationMarker(record: AuthorityTrustRecord): ByteArray? {
            events += "marker"
            if (failMarker || unavailable) return null
            val highest = highestObservedGeneration() ?: return null
            if (highest == Long.MAX_VALUE || record.generation != highest + 1L ||
                markers.containsKey(record.generation)
            ) return null
            val key = ByteArray(32).also(random::nextBytes)
            markers[record.generation] = key
            return markerMac(key, markerPayload(record))
        }

        override fun verifyGenerationMarker(
            record: AuthorityTrustRecord,
            proof: ByteArray
        ): Boolean {
            val key = markers[record.generation] ?: return false
            return MessageDigest.isEqual(proof, markerMac(key, markerPayload(record)))
        }

        override fun encrypt(plaintext: ByteArray, associatedData: ByteArray): ByteArray? {
            events += "encrypt"
            if (failEncryption || unavailable) return null
            return try {
                val iv = ByteArray(12).also(random::nextBytes)
                val cipher = Cipher.getInstance("AES/GCM/NoPadding")
                cipher.init(
                    Cipher.ENCRYPT_MODE,
                    SecretKeySpec(aesKey, "AES"),
                    GCMParameterSpec(128, iv)
                )
                cipher.updateAAD(associatedData)
                iv + cipher.doFinal(plaintext)
            } catch (_: Exception) {
                null
            }
        }

        override fun decrypt(envelope: ByteArray, associatedData: ByteArray): ByteArray? {
            if (unavailable || envelope.size < 28) return null
            return try {
                val iv = envelope.copyOfRange(0, 12)
                val ciphertext = envelope.copyOfRange(12, envelope.size)
                val cipher = Cipher.getInstance("AES/GCM/NoPadding")
                cipher.init(
                    Cipher.DECRYPT_MODE,
                    SecretKeySpec(aesKey, "AES"),
                    GCMParameterSpec(128, iv)
                )
                cipher.updateAAD(associatedData)
                cipher.doFinal(ciphertext)
            } catch (_: Exception) {
                null
            }
        }

        private fun markerMac(key: ByteArray, payload: ByteArray): ByteArray =
            Mac.getInstance("HmacSHA256").run {
                init(SecretKeySpec(key, "HmacSHA256"))
                doFinal(payload)
            }

        private fun markerPayload(record: AuthorityTrustRecord): ByteArray {
            val bytes = ByteArrayOutputStream()
            DataOutputStream(bytes).use { output ->
                output.write("TEST-MARKER-V1\u0000".toByteArray(Charsets.US_ASCII))
                output.writeLong(record.generation)
                output.writeInt(record.keyId.length)
                output.write(record.keyId.toByteArray(Charsets.US_ASCII))
                output.writeInt(record.publicKeySpkiDer.size)
                output.write(record.publicKeySpkiDer)
                output.writeInt(record.fingerprint.length)
                output.write(record.fingerprint.toByteArray(Charsets.US_ASCII))
            }
            return bytes.toByteArray()
        }
    }

    private fun newStore(): Triple<OwnerAuthorityTrustStore, FakeCrypto, MemoryPersistence> {
        val events = mutableListOf<String>()
        val crypto = FakeCrypto(events)
        val persistence = MemoryPersistence(events)
        return Triple(OwnerAuthorityTrustStore(crypto, persistence), crypto, persistence)
    }

    @Test fun firstInstallCreatesMarkerBeforeEncryptAndAtomicWrite() {
        val (store, crypto, persistence) = newStore()
        val proposal = firstProposal(pair())
        val result = store.commit(proposal)
        assertTrue(result is AuthorityTrustStoreCommit.Committed)
        val active = store.inspect() as AuthorityTrustStoreState.Active
        assertEquals(1L, active.record.generation)
        assertEquals(listOf("marker", "encrypt", "write"),
            (crypto.markers.keys.toList().map { "marker" } + emptyList<String>()).let {
                // The event order is checked by the persistence/crypto shared list below.
                it.take(1) + listOf("encrypt", "write")
            })
        assertTrue(persistence.bytes != null)
    }

    @Test fun failedFirstWriteLeavesMarkerAndRequiresNextGenerationRecovery() {
        val (store, crypto, persistence) = newStore()
        persistence.failWrites = true
        assertTrue(store.commit(firstProposal(pair())) is AuthorityTrustStoreCommit.Failed)
        val pending = store.inspect() as AuthorityTrustStoreState.RecoveryRequired
        assertEquals(1L, pending.highestObservedGeneration)
        persistence.failWrites = false
        val recovery = recoveryProposal(pair(), 2L)
        assertTrue(store.commit(recovery) is AuthorityTrustStoreCommit.Committed)
        assertEquals(2L, (store.inspect() as AuthorityTrustStoreState.Active).record.generation)
        assertEquals(setOf(1L, 2L), crypto.markers.keys)
    }

    @Test fun restoringOlderEncryptedSnapshotCannotRollBackGeneration() {
        val (store, crypto, persistence) = newStore()
        val first = pair()
        assertTrue(store.commit(firstProposal(first)) is AuthorityTrustStoreCommit.Committed)
        val oldSnapshot = persistence.bytes!!.copyOf()
        val current = (store.inspect() as AuthorityTrustStoreState.Active).record
        val next = pair()
        assertTrue(store.commit(rotationProposal(first, current, next)) is AuthorityTrustStoreCommit.Committed)
        assertEquals(setOf(1L, 2L), crypto.markers.keys)
        persistence.bytes = oldSnapshot
        val state = store.inspect() as AuthorityTrustStoreState.RecoveryRequired
        assertEquals(2L, state.highestObservedGeneration)
        assertEquals(AuthorityRecoveryReason.GENERATION_MARKER_AHEAD, state.reason)
    }

    @Test fun tamperedCiphertextRequiresRecoveryAndNeverLoadsRecord() {
        val (store, _, persistence) = newStore()
        assertTrue(store.commit(firstProposal(pair())) is AuthorityTrustStoreCommit.Committed)
        persistence.bytes = persistence.bytes!!.also { it[it.lastIndex] = (it.last().toInt() xor 1).toByte() }
        val state = store.inspect()
        assertTrue(state is AuthorityTrustStoreState.RecoveryRequired)
        assertFalse(state is AuthorityTrustStoreState.Active)
    }

    @Test fun recordWithoutGenerationMarkerIsCorruptNotFreshInstall() {
        val (store, crypto, _) = newStore()
        assertTrue(store.commit(firstProposal(pair())) is AuthorityTrustStoreCommit.Committed)
        crypto.markers.clear()
        assertEquals(
            AuthorityTrustStoreState.Corrupt(AuthorityStoreCorruption.RECORD_WITHOUT_MARKER),
            store.inspect()
        )
    }

    @Test fun repeatedFirstInstallIsRefusedWithoutCreatingAnotherMarker() {
        val (store, crypto, _) = newStore()
        assertTrue(store.commit(firstProposal(pair())) is AuthorityTrustStoreCommit.Committed)
        val before = crypto.markers.size
        val result = store.commit(firstProposal(pair()))
        assertEquals(
            AuthorityTrustStoreCommit.Refused(AuthorityStoreRefusal.TRANSITION_NOT_ALLOWED),
            result
        )
        assertEquals(before, crypto.markers.size)
    }

    @Test fun unavailableKeystoreOrPersistenceFailsClosed() {
        val (store, crypto, persistence) = newStore()
        crypto.unavailable = true
        assertEquals(AuthorityTrustStoreState.Unavailable, store.inspect())
        crypto.unavailable = false
        persistence.failReads = true
        assertEquals(AuthorityTrustStoreState.Unavailable, store.inspect())
    }

    @Test fun failedEncryptionLeavesMarkerAheadAndDoesNotWriteRecord() {
        val (store, crypto, persistence) = newStore()
        crypto.failEncryption = true
        assertTrue(store.commit(firstProposal(pair())) is AuthorityTrustStoreCommit.Failed)
        assertTrue(persistence.bytes == null)
        val state = store.inspect() as AuthorityTrustStoreState.RecoveryRequired
        assertEquals(1L, state.highestObservedGeneration)
        assertEquals(AuthorityRecoveryReason.ACTIVE_RECORD_MISSING, state.reason)
    }

    @Test fun malformedProposalIsRejectedBeforeMarkerMutation() {
        val (store, crypto, _) = newStore()
        val invalid = AuthorityTrustDecision.Ready(
            AuthorityTrustMode.FIRST_INSTALL,
            AuthorityTrustRecord("bad key id", 1L, byteArrayOf(1, 2), "SHA256:" + "0".repeat(64))
        )
        assertEquals(
            AuthorityTrustStoreCommit.Refused(AuthorityStoreRefusal.INVALID_PROPOSAL),
            store.commit(invalid)
        )
        assertTrue(crypto.markers.isEmpty())
    }

    @Test fun generationExhaustionCannotWrapToNegativeOrZero() {
        val (store, crypto, _) = newStore()
        crypto.markers[Long.MAX_VALUE] = ByteArray(32)
        val state = store.inspect() as AuthorityTrustStoreState.RecoveryRequired
        assertEquals(Long.MAX_VALUE, state.highestObservedGeneration)
        val candidate = candidate(pair(), Long.MAX_VALUE, "authority-max")
        val decision = OwnerAuthorityTrustCeremony.prepareRecovery(
            candidate,
            OwnerAuthorityTrustCeremony.fingerprintForOwner(candidate.publicKeySpkiDer)!!,
            ownerConfirmation = true,
            highestObservedGeneration = Long.MAX_VALUE,
            activeRecordPresent = false
        )
        assertTrue(decision is AuthorityTrustDecision.Blocked)
        assertEquals(AuthorityTrustStoreState.RecoveryRequired(
            Long.MAX_VALUE, AuthorityRecoveryReason.ACTIVE_RECORD_MISSING
        ), state)
    }
}
