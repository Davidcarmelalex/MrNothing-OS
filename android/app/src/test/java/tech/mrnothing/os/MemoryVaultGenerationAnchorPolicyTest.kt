package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Test

/** Synthetic snapshots only. Not trusted witness or Android hardware evidence. */
class MemoryVaultGenerationAnchorPolicyTest {
    private val policy = MemoryVaultGenerationAnchorPolicy
    private val blocked = MemoryVaultAnchorOutcome.BLOCKED
    private val recovery = MemoryVaultAnchorOutcome.RECOVERY_REQUIRED_NOT_AUTHORIZED
    private val diagnostic = MemoryVaultAnchorOutcome.CONSISTENT_INPUTS_NOT_AUTHORIZED

    private fun record(gen: Long = 7L, id: ByteArray = ByteArray(32) { 7 },
                       ref: ByteArray = ByteArray(32) { 8 }) =
        MemoryVaultAnchorRecord(gen, id, ref)

    private fun marker(r: MemoryVaultAnchorRecord) =
        MemoryVaultAnchorMarker(r.generation, r.generationId.copyOf())

    private fun witness(r: MemoryVaultAnchorRecord) =
        MemoryVaultAnchorWitness(r.generation, policy.commitment(r)!!)

    @Test fun consistentInputsAreDiagnosticOnly() {
        val r = record()
        assertEquals(diagnostic, policy.inspect(r, marker(r), witness(r)))
    }

    @Test fun simultaneousRecordAndMarkerReplacementCannotMatchPinnedWitness() {
        val original = record()
        val replacement = record(id = ByteArray(32) { 11 }, ref = ByteArray(32) { 12 })
        assertEquals(blocked, policy.inspect(replacement, marker(replacement), witness(original)))
    }

    @Test fun changedReferenceDigestIsRejected() {
        val r = record()
        assertEquals(blocked, policy.inspect(record(ref = ByteArray(32) { 3 }), marker(r), witness(r)))
    }

    @Test fun changedGenerationIdIsRejected() {
        val r = record()
        assertEquals(blocked, policy.inspect(record(id = ByteArray(32) { 3 }), marker(r), witness(r)))
    }

    @Test fun changedWitnessCommitmentIsRejected() {
        val r = record()
        assertEquals(blocked, policy.inspect(r, marker(r),
            MemoryVaultAnchorWitness(7L, ByteArray(32) { 0 })))
    }

    @Test fun markerAheadRequiresRecovery() {
        val r = record()
        assertEquals(recovery, policy.inspect(r,
            MemoryVaultAnchorMarker(8L, r.generationId), witness(r)))
    }

    @Test fun witnessAheadRequiresRecovery() {
        val r = record()
        assertEquals(recovery, policy.inspect(r, marker(r),
            MemoryVaultAnchorWitness(8L, witness(r).commitmentSha256)))
    }

    @Test fun recordAheadOfMarkerIsBlocked() {
        val r = record()
        assertEquals(blocked, policy.inspect(r,
            MemoryVaultAnchorMarker(6L, r.generationId), witness(r)))
    }

    @Test fun recordAheadOfWitnessIsBlocked() {
        val r = record()
        assertEquals(blocked, policy.inspect(r, marker(r),
            MemoryVaultAnchorWitness(6L, witness(r).commitmentSha256)))
    }

    @Test fun missingRecordWithWitnessRequiresRecovery() {
        val r = record()
        assertEquals(recovery, policy.inspect(null, marker(r), witness(r)))
    }

    @Test fun missingRecordWithoutWitnessIsBlocked() {
        val r = record()
        assertEquals(blocked, policy.inspect(null, marker(r), null))
    }

    @Test fun missingWitnessIsBlocked() {
        val r = record()
        assertEquals(blocked, policy.inspect(r, marker(r), null))
    }

    @Test fun missingMarkerIsBlocked() {
        val r = record()
        assertEquals(blocked, policy.inspect(r, null, witness(r)))
    }

    @Test fun malformedReferenceDigestIsBlocked() {
        val r = record(ref = ByteArray(31))
        assertEquals(blocked, policy.inspect(r, marker(r),
            MemoryVaultAnchorWitness(7L, ByteArray(32))))
    }

    @Test fun zeroGenerationIsBlocked() {
        val r = record(gen = 0L)
        assertEquals(blocked, policy.inspect(r, marker(r),
            MemoryVaultAnchorWitness(1L, ByteArray(32))))
    }

    @Test fun maximumGenerationIsBlocked() {
        val r = record(gen = Long.MAX_VALUE)
        assertEquals(blocked, policy.inspect(r, marker(r),
            MemoryVaultAnchorWitness(Long.MAX_VALUE, ByteArray(32))))
    }

    @Test fun forgedWitnessShowsExternalTrustIsRequired() {
        // An attacker replacing ALL three snapshots can forge consistency.
        // This MUST NOT be mistaken for trusted provenance or authorization.
        val forged = record(id = ByteArray(32) { 55 }, ref = ByteArray(32) { 56 })
        assertEquals(diagnostic, policy.inspect(forged, marker(forged), witness(forged)))
    }
}
