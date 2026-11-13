package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Test

/** Pure-JVM synthetic state transitions, NOT durable storage or Pixel evidence. */
class MemoryVaultEnrollmentCrashPolicyTest {
    private fun snapshot(
        previous: Long = 7L, candidate: Long = 8L, staged: Long? = null,
        marker: Long = 7L, witness: Long = 7L, watermark: Long = 7L, active: Long = 7L
    ) = MemoryVaultEnrollmentSnapshot(previous, candidate, staged, marker, witness, watermark, active)

    private fun check(s: MemoryVaultEnrollmentSnapshot?) = MemoryVaultEnrollmentCrashPolicy.inspect(s)
    private val blocked = MemoryVaultEnrollmentCrashOutcome.BLOCKED
    private val recovery = MemoryVaultEnrollmentCrashOutcome.RECOVERY_REQUIRED_NOT_AUTHORIZED

    @Test fun untouchedStateIsNotAuthorized() {
        assertEquals(MemoryVaultEnrollmentCrashOutcome.UNCHANGED_NOT_AUTHORIZED, check(snapshot()))
    }

    @Test fun stagedCandidateRequiresOwnerReview() {
        assertEquals(MemoryVaultEnrollmentCrashOutcome.STAGED_ABORT_REQUIRES_OWNER_REVIEW,
            check(snapshot(staged = 8L)))
    }

    @Test fun markerFirstCrashRequiresOwnerRecovery() {
        assertEquals(recovery, check(snapshot(staged = 8L, marker = 8L)))
    }

    @Test fun witnessPublicationCrashRequiresOwnerRecovery() {
        assertEquals(recovery, check(snapshot(staged = 8L, marker = 8L, witness = 8L)))
    }

    @Test fun watermarkAdvanceCrashRequiresOwnerRecovery() {
        assertEquals(recovery, check(snapshot(staged = 8L, marker = 8L, witness = 8L, watermark = 8L)))
    }

    @Test fun completeSequenceIsStillNotAuthorization() {
        assertEquals(MemoryVaultEnrollmentCrashOutcome.STRUCTURALLY_COMPLETE_NOT_AUTHORIZED,
            check(snapshot(staged = 8L, marker = 8L, witness = 8L, watermark = 8L, active = 8L)))
    }

    @Test fun skippingStagingBlocks() {
        assertEquals(blocked, check(snapshot(marker = 8L)))
    }

    @Test fun witnessAheadOfMarkerBlocks() {
        assertEquals(blocked, check(snapshot(staged = 8L, witness = 8L)))
    }

    @Test fun watermarkAheadOfWitnessBlocks() {
        assertEquals(blocked, check(snapshot(staged = 8L, marker = 8L, watermark = 8L)))
    }

    @Test fun activeAheadOfWatermarkBlocks() {
        assertEquals(blocked, check(snapshot(staged = 8L, marker = 8L, witness = 8L, active = 8L)))
    }

    @Test fun missingStagedCandidateBlocks() {
        assertEquals(blocked, check(snapshot(staged = null, marker = 8L, witness = 8L)))
    }

    @Test fun stagedWrongGenerationBlocks() {
        assertEquals(blocked, check(snapshot(staged = 9L)))
    }

    @Test fun nonAdjacentRotationBlocks() {
        assertEquals(blocked, check(snapshot(candidate = 9L)))
    }

    @Test fun invalidOrOverflowGenerationBlocks() {
        assertEquals(blocked, check(snapshot(previous = 0L, candidate = 1L)))
        assertEquals(blocked, check(snapshot(previous = Long.MAX_VALUE - 1L, candidate = Long.MAX_VALUE)))
        assertEquals(blocked, check(snapshot(previous = Long.MAX_VALUE, candidate = Long.MIN_VALUE)))
    }

    @Test fun rollbackBelowPreviousBlocks() {
        assertEquals(blocked, check(snapshot(watermark = 6L)))
        assertEquals(blocked, check(snapshot(active = 6L)))
    }

    @Test fun skippedWitnessWithAdvancedActiveBlocks() {
        assertEquals(blocked, check(snapshot(staged = 8L, marker = 8L, watermark = 8L, active = 8L)))
    }

    @Test fun unknownFutureGenerationBlocks() {
        assertEquals(blocked, check(snapshot(staged = 8L, marker = 9L)))
        assertEquals(blocked, check(snapshot(staged = 8L, marker = 8L, witness = 9L)))
    }

    @Test fun oldSnapshotCanAppearUntouchedWithoutExternalRollbackAnchor() {
        // This is a counterexample, NOT a successful rollback-defense test.
        // Replaying all old values is indistinguishable from a never-started rotation.
        assertEquals(MemoryVaultEnrollmentCrashOutcome.UNCHANGED_NOT_AUTHORIZED, check(snapshot()))
    }

    @Test fun nullSnapshotBlocks() {
        assertEquals(blocked, check(null))
    }
}
