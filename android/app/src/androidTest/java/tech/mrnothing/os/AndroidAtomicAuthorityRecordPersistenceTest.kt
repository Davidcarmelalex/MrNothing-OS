package tech.mrnothing.os

import android.content.Context
import android.content.ContextWrapper
import android.test.InstrumentationTestCase
import android.util.AtomicFile
import java.io.File

/**
 * SEC-020B5: exercises the real Android AtomicFile adapter in an isolated
 * app-private directory. These tests do not invoke Android Keystore or
 * StrongBox and do not target the user's noBackupFilesDir.
 */
class AndroidAtomicAuthorityRecordPersistenceTest : InstrumentationTestCase() {
    fun testAtomicWritesRoundTripAndReplaceTheCommittedRecord() = withPersistence { persistence, _ ->
        val first = "committed-record-one".toByteArray(Charsets.US_ASCII)
        val second = "committed-record-two".toByteArray(Charsets.US_ASCII)

        assertTrue("first atomic write failed", persistence.writeAtomically(first))
        assertBytes(first, presentBytes(persistence.read()))

        assertTrue("replacement atomic write failed", persistence.writeAtomically(second))
        assertBytes(second, presentBytes(persistence.read()))
    }

    fun testInterruptedReplacementRestoresPreviousCommittedRecord() = withPersistence { persistence, directory ->
        val previous = "previous-committed-record".toByteArray(Charsets.US_ASCII)
        val partial = "incomplete-replacement".toByteArray(Charsets.US_ASCII)
        assertTrue("baseline atomic write failed", persistence.writeAtomically(previous))

        // Simulate the interruption window after AtomicFile.startWrite() has
        // moved the old base file to its backup but before finishWrite().
        // Closing the descriptor is deliberate: do not call finishWrite() or
        // failWrite(); the next openRead() must perform backup recovery.
        val interruptedFile = AtomicFile(File(directory, RECORD_FILE_NAME))
        val output = interruptedFile.startWrite()
        try {
            output.write(partial)
            output.fd.sync()
        } finally {
            output.close()
        }

        assertBytes(previous, presentBytes(persistence.read()))
        assertFalse(
            "AtomicFile backup should be consumed by recovery",
            File(directory, "$RECORD_FILE_NAME.bak").exists()
        )
    }

    fun testInterruptedFirstWriteLeavesNoCommittedRecordButMarkerRequiresRecovery() =
        withPersistence { persistence, directory ->
            val partial = "partial-first-write".toByteArray(Charsets.US_ASCII)
            val interruptedFile = AtomicFile(File(directory, RECORD_FILE_NAME))
            val output = interruptedFile.startWrite()
            try {
                output.write(partial)
                output.fd.sync()
            } finally {
                // Do not finish or fail the write: AtomicFile must discard the
                // uncommitted first-write staging file during the next openRead().
                output.close()
            }

            assertEquals(
                "an uncommitted first write has no committed base record",
                AuthorityRecordRead.Missing,
                persistence.read()
            )
            val state = OwnerAuthorityTrustStore(
                MarkerOnlyCrypto(highestGeneration = 1L),
                persistence
            ).inspect()
            assertEquals(
                AuthorityTrustStoreState.RecoveryRequired(
                    1L,
                    AuthorityRecoveryReason.ACTIVE_RECORD_MISSING
                ),
                state
            )
        }

    fun testOversizedStoredRecordFailsClosed() = withPersistence { persistence, directory ->
        File(directory, RECORD_FILE_NAME).writeBytes(
            ByteArray(AuthorityTrustStoreLimits.MAX_ENVELOPE_BYTES + 1) { 0x5a.toByte() }
        )
        assertEquals(AuthorityRecordRead.Failed, persistence.read())
    }

    fun testInvalidWriteBoundsPreservePreviousRecord() = withPersistence { persistence, _ ->
        val previous = "preserve-this-record".toByteArray(Charsets.US_ASCII)
        assertTrue("baseline atomic write failed", persistence.writeAtomically(previous))
        assertFalse("empty record must be refused", persistence.writeAtomically(ByteArray(0)))
        assertFalse(
            "oversized record must be refused",
            persistence.writeAtomically(
                ByteArray(AuthorityTrustStoreLimits.MAX_ENVELOPE_BYTES + 1)
            )
        )
        assertBytes(previous, presentBytes(persistence.read()))
    }

    private class MarkerOnlyCrypto(private val highestGeneration: Long) : AuthorityTrustCrypto {
        override fun highestObservedGeneration(): Long = highestGeneration
        override fun createGenerationMarker(record: AuthorityTrustRecord): ByteArray? = null
        override fun verifyGenerationMarker(record: AuthorityTrustRecord, proof: ByteArray): Boolean = false
        override fun encrypt(plaintext: ByteArray, associatedData: ByteArray): ByteArray? = null
        override fun decrypt(envelope: ByteArray, associatedData: ByteArray): ByteArray? = null
    }
    private fun withPersistence(
        block: (AndroidAtomicAuthorityRecordPersistence, File) -> Unit
    ) {
        val target = getInstrumentation().targetContext
        val directory = File(target.cacheDir, "sec020b5-${System.nanoTime()}")
        assertTrue("could not create isolated test directory", directory.mkdirs())
        try {
            val isolatedContext = IsolatedNoBackupContext(target, directory)
            block(AndroidAtomicAuthorityRecordPersistence(isolatedContext), directory)
        } finally {
            directory.deleteRecursively()
        }
    }

    private fun presentBytes(result: AuthorityRecordRead): ByteArray {
        assertTrue("expected a present record, got $result", result is AuthorityRecordRead.Present)
        return (result as AuthorityRecordRead.Present).bytes
    }

    private fun assertBytes(expected: ByteArray, actual: ByteArray) {
        assertTrue("record bytes differ", expected.contentEquals(actual))
    }

    private class IsolatedNoBackupContext(
        base: Context,
        private val directory: File
    ) : ContextWrapper(base) {
        override fun getApplicationContext(): Context = this
        override fun getNoBackupFilesDir(): File = directory
    }

    private companion object {
        const val RECORD_FILE_NAME = "owner-authority-trust-v1.enc"
    }
}
