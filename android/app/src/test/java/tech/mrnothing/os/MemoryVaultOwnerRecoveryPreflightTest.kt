package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

/** Synthetic owner-intent policy tests, not real owner presence or Pixel proof. */
class MemoryVaultOwnerRecoveryPreflightTest {
    private var now = 1_000L
    private fun gate() = MemoryVaultOwnerRecoveryPreflight { now }
    private fun snapshot(
        enrollment: MemoryVaultEnrollmentSnapshot = MemoryVaultEnrollmentSnapshot(7, 8, 8, 8, 7, 7, 7),
        observedPin: ByteArray = ByteArray(32) { 42 },
        externalPin: ByteArray = ByteArray(32) { 42 },
        watermark: Long = 7,
        nonce: String = "a".repeat(64),
        owner: Int = 0,
        foreground: Boolean = true,
        unlocked: Boolean = true,
        credential: Boolean = true,
        acknowledged: Boolean = true
    ) = MemoryVaultOwnerRecoverySnapshot(enrollment, observedPin, externalPin, watermark,
        nonce, owner, foreground, unlocked, credential, acknowledged)

    private val blocked = MemoryVaultOwnerRecoveryOutcome.BLOCKED
    private val reviewed = MemoryVaultOwnerRecoveryOutcome.OWNER_REVIEW_RECORDED_NOT_AUTHORIZED

    @Test fun markerCrashRecordsIntentButDoesNotAuthorize() {
        val g = gate(); val s = snapshot()
        assertNotNull(g.begin(s)); assertEquals(reviewed, g.finish(s, true))
    }

    @Test fun stagedCandidateCanRequestReview() {
        val g = gate(); val s = snapshot(enrollment = MemoryVaultEnrollmentSnapshot(7, 8, 8, 7, 7, 7, 7))
        assertNotNull(g.begin(s)); assertEquals(reviewed, g.finish(s, true))
    }

    @Test fun unchangedStateCannotRequestRecovery() {
        assertNull(gate().begin(snapshot(enrollment = MemoryVaultEnrollmentSnapshot(7, 8, null, 7, 7, 7, 7))))
    }

    @Test fun completeRotationCannotRequestRecovery() {
        assertNull(gate().begin(snapshot(enrollment = MemoryVaultEnrollmentSnapshot(7, 8, 8, 8, 8, 8, 8), watermark = 8)))
    }

    @Test fun malformedCrashStateCannotRequestRecovery() {
        assertNull(gate().begin(snapshot(enrollment = MemoryVaultEnrollmentSnapshot(7, 9, 9, 9, 7, 7, 7))))
    }

    @Test fun nonOwnerIsRejected() { assertNull(gate().begin(snapshot(owner = 10))) }
    @Test fun backgroundUiIsRejected() { assertNull(gate().begin(snapshot(foreground = false))) }
    @Test fun lockedDeviceIsRejected() { assertNull(gate().begin(snapshot(unlocked = false))) }
    @Test fun missingCredentialIsRejected() { assertNull(gate().begin(snapshot(credential = false))) }
    @Test fun missingAcknowledgementIsRejected() { assertNull(gate().begin(snapshot(acknowledged = false))) }
    @Test fun changedPinIsRejected() { assertNull(gate().begin(snapshot(externalPin = ByteArray(32) { 41 }))) }
    @Test fun malformedPinIsRejected() { assertNull(gate().begin(snapshot(observedPin = ByteArray(31)))) }
    @Test fun staleExternalWatermarkIsRejected() { assertNull(gate().begin(snapshot(watermark = 6))) }
    @Test fun futureExternalWatermarkIsRejected() { assertNull(gate().begin(snapshot(watermark = 8))) }
    @Test fun malformedNonceIsRejected() { assertNull(gate().begin(snapshot(nonce = "Z".repeat(64)))) }

    @Test fun forgedBothPinsAreNotIndependentProvenance() {
        // An attacker-controlled pair of matching pins is indistinguishable here.
        val g = gate(); val forged = ByteArray(32) { 99 }
        val s = snapshot(observedPin = forged, externalPin = forged.copyOf())
        assertNotNull(g.begin(s))
        assertEquals(reviewed, g.finish(s, true)) // still never authorization
    }

    @Test fun replayedAllInputsCannotProveRollbackResistance() {
        // A replay of every caller assertion can pass an offline consistency check.
        val g = gate(); val oldSnapshot = snapshot()
        assertNotNull(g.begin(oldSnapshot))
        assertEquals(reviewed, g.finish(oldSnapshot, true)) // not recovery permission
    }

    @Test fun credentialFailureConsumesAttempt() {
        val g = gate(); val s = snapshot()
        assertNotNull(g.begin(s)); assertEquals(blocked, g.finish(s, false))
        assertEquals(blocked, g.finish(s, true)); assertNull(g.begin(s))
    }

    @Test fun mutatedSnapshotConsumesAttempt() {
        val g = gate(); val s = snapshot()
        assertNotNull(g.begin(s)); assertEquals(blocked, g.finish(snapshot(nonce = "b".repeat(64)), true))
        assertEquals(blocked, g.finish(s, true))
    }

    @Test fun mutatedPinConsumesAttempt() {
        val g = gate(); val s = snapshot()
        assertNotNull(g.begin(s)); s.observedSignerPinSha256[0] = 0
        assertEquals(blocked, g.finish(s, true))
    }

    @Test fun replayIsRejected() {
        val g = gate(); val s = snapshot()
        assertNotNull(g.begin(s)); assertEquals(reviewed, g.finish(s, true))
        assertEquals(blocked, g.finish(s, true)); assertNull(g.begin(s))
    }

    @Test fun cancellationIsTerminal() {
        val g = gate(); val s = snapshot()
        assertNotNull(g.begin(s)); g.revoke()
        assertEquals(blocked, g.finish(s, true)); assertNull(g.begin(s))
    }

    @Test fun processRecreationDoesNotResumeOldAttempt() {
        val s = snapshot(); assertNotNull(gate().begin(s))
        assertEquals(blocked, gate().finish(s, true))
    }

    @Test fun expiryRejectsIntent() {
        val g = gate(); val s = snapshot()
        assertNotNull(g.begin(s)); now += OwnerAuthorityConfirmationState.MAX_AGE_NANOS + 1
        assertEquals(blocked, g.finish(s, true))
    }

    @Test fun clockRegressionRejectsIntent() {
        val g = gate(); val s = snapshot()
        assertNotNull(g.begin(s)); now -= 1
        assertEquals(blocked, g.finish(s, true))
    }
}
