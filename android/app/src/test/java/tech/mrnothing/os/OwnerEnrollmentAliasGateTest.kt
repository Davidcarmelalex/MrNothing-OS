package tech.mrnothing.os

import org.junit.Assert.assertEquals
import org.junit.Test

/** Pure JVM policy tests; no Android Keystore or device is exercised. */
class OwnerEnrollmentAliasGateTest {
    @Test fun absentAndBlockedReadinessAllowsOnlyPromptPreflight() {
        assertEquals(OwnerEnrollmentAliasState.ABSENT,
            OwnerEnrollmentAliasGate.evaluate(false, OwnerKeyReadiness.BLOCKED))
    }

    @Test fun verifiedExistingAliasIsPreserved() {
        assertEquals(OwnerEnrollmentAliasState.VERIFIED_EXISTING,
            OwnerEnrollmentAliasGate.evaluate(
                true, OwnerKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH))
    }

    @Test fun malformedOrTeeOnlyExistingAliasIsNeverTreatedAsAbsent() {
        assertEquals(OwnerEnrollmentAliasState.UNTRUSTED_EXISTING,
            OwnerEnrollmentAliasGate.evaluate(true, OwnerKeyReadiness.BLOCKED))
    }

    @Test fun inconsistentAbsentButReadySignalsFailClosed() {
        assertEquals(OwnerEnrollmentAliasState.INSPECTION_FAILED,
            OwnerEnrollmentAliasGate.evaluate(
                false, OwnerKeyReadiness.EXISTING_KEY_REQUIRES_OWNER_AUTH))
    }
}
