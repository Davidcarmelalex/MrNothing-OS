package tech.mrnothing.os

import android.content.Context
import android.content.pm.PackageManager
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyInfo
import android.security.keystore.KeyProperties
import android.test.InstrumentationTestCase
import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.io.IOException
import java.nio.charset.StandardCharsets
import java.security.GeneralSecurityException
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.util.Enumeration
import java.util.UUID
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.SecretKeyFactory
import org.bouncycastle.jce.provider.BouncyCastleProvider

/**
 * SEC-020B6: exercises emulator-verifiable AndroidKeyStore failure paths.
 *
 * Every test uses a unique alias namespace and removes only aliases it created.
 * No production authority alias, credential, permission or trust record is touched.
 * Emulator results do not prove StrongBox hardware behavior.
 */
class AndroidAuthorityTrustCryptoFailureModeTest : InstrumentationTestCase() {
    fun testStrongBoxRequestNeverFallsBackToTeeWhenFeatureIsUnavailable() =
        withIsolatedCrypto { crypto, store, markerPrefix, _, context ->
            val record = validRecord()
            val strongBoxAdvertised = context.packageManager.hasSystemFeature(
                PackageManager.FEATURE_STRONGBOX_KEYSTORE
            )
            val proof = crypto.createGenerationMarker(record)
            val alias = markerPrefix + "1"

            if (strongBoxAdvertised) {
                assertNotNull("advertised StrongBox must produce a verifiable marker", proof)
                assertEquals(
                    KeyProperties.SECURITY_LEVEL_STRONGBOX,
                    securityLevel(store, alias)
                )
                assertTrue(crypto.verifyGenerationMarker(record, proof!!))
            } else {
                assertNull("StrongBox absence must fail closed", proof)
                assertFalse("no TEE marker alias may be created as a fallback", store.containsAlias(alias))
                assertEquals(0L, crypto.highestObservedGeneration())
            }
        }

    fun testMissingMarkerAliasCannotVerifyAProof() =
        withIsolatedCrypto { crypto, _, _, _, _ ->
            assertFalse(
                crypto.verifyGenerationMarker(
                    validRecord(),
                    ByteArray(AuthorityTrustStoreLimits.MARKER_PROOF_BYTES)
                )
            )
        }

    fun testMalformedMarkerSuffixMakesTrustStoreUnavailable() =
        withIsolatedCrypto { crypto, _, markerPrefix, _, _ ->
            createTeeHmac(markerPrefix + "not-a-generation")
            assertEquals(
                AuthorityTrustStoreState.Unavailable,
                OwnerAuthorityTrustStore(crypto, MissingPersistence).inspect()
            )
        }

    fun testNonCanonicalGenerationSuffixMakesTrustStoreUnavailable() =
        withIsolatedCrypto { crypto, _, markerPrefix, _, _ ->
            createTeeHmac(markerPrefix + "01")
            assertEquals(
                AuthorityTrustStoreState.Unavailable,
                OwnerAuthorityTrustStore(crypto, MissingPersistence).inspect()
            )
        }

    fun testZeroGenerationMarkerMakesTrustStoreUnavailable() =
        withIsolatedCrypto { crypto, _, markerPrefix, _, _ ->
            createTeeHmac(markerPrefix + "0")
            assertEquals(
                AuthorityTrustStoreState.Unavailable,
                OwnerAuthorityTrustStore(crypto, MissingPersistence).inspect()
            )
        }

    fun testTeeOnlyMarkerCannotBecomeGenerationWatermark() =
        withIsolatedCrypto { crypto, store, markerPrefix, _, _ ->
            val alias = markerPrefix + "1"
            createTeeHmac(alias)
            assertFalse(
                "test key must not be StrongBox-backed",
                securityLevel(store, alias) == KeyProperties.SECURITY_LEVEL_STRONGBOX
            )
            assertEquals(
                AuthorityTrustStoreState.Unavailable,
                OwnerAuthorityTrustStore(crypto, MissingPersistence).inspect()
            )
        }

    fun testEncryptionKeyWithoutAnyMarkerIsNotFreshInstall() =
        withIsolatedCrypto { crypto, _, _, aesAlias, _ ->
            createTeeAes(aesAlias)
            assertEquals(
                AuthorityTrustStoreState.Unavailable,
                OwnerAuthorityTrustStore(crypto, MissingPersistence).inspect()
            )
        }

    fun testWrongKeyTypeUnderMarkerPrefixIsRejected() =
        withIsolatedCrypto { crypto, _, markerPrefix, _, _ ->
            createTeeEcKeyPair(markerPrefix + "1")
            assertEquals(
                AuthorityTrustStoreState.Unavailable,
                OwnerAuthorityTrustStore(crypto, MissingPersistence).inspect()
            )
        }

    fun testKeyInfoGeneralSecurityExceptionMakesTrustStoreUnavailable() =
        withIsolatedCrypto(throwingKeyInfoReader(GeneralSecurityException("injected KeyInfo failure"))) {
                crypto, _, markerPrefix, _, _ ->
            createTeeHmac(markerPrefix + "1")
            assertNull(crypto.highestObservedGeneration())
            assertEquals(
                AuthorityTrustStoreState.Unavailable,
                OwnerAuthorityTrustStore(crypto, MissingPersistence).inspect()
            )
        }

    fun testKeyInfoRuntimeExceptionMakesTrustStoreUnavailable() =
        withIsolatedCrypto(throwingKeyInfoReader(IllegalStateException("injected provider failure"))) {
                crypto, _, markerPrefix, _, _ ->
            createTeeHmac(markerPrefix + "1")
            assertNull(crypto.highestObservedGeneration())
            assertEquals(
                AuthorityTrustStoreState.Unavailable,
                OwnerAuthorityTrustStore(crypto, MissingPersistence).inspect()
            )
        }

    fun testKeyStoreLoadGeneralSecurityExceptionMakesTrustStoreUnavailable() =
        withIsolatedCrypto(
            keyStoreReader = throwingKeyStoreLoadReader(
                GeneralSecurityException("injected AndroidKeyStore load failure")
            )
        ) { crypto, store, markerPrefix, aesAlias, _ ->
            assertNull(crypto.highestObservedGeneration())
            assertEquals(
                AuthorityTrustStoreState.Unavailable,
                OwnerAuthorityTrustStore(crypto, MissingPersistence).inspect()
            )
            assertNull(crypto.createGenerationMarker(validRecord()))
            assertFalse(store.containsAlias(markerPrefix + "1"))
            assertFalse(store.containsAlias(aesAlias))
        }

    fun testKeyStoreLoadIOExceptionMakesTrustStoreUnavailable() =
        withIsolatedCrypto(
            keyStoreReader = throwingKeyStoreLoadReader(
                IOException("injected AndroidKeyStore I/O failure")
            )
        ) { crypto, store, markerPrefix, aesAlias, _ ->
            assertNull(crypto.highestObservedGeneration())
            assertEquals(
                AuthorityTrustStoreState.Unavailable,
                OwnerAuthorityTrustStore(crypto, MissingPersistence).inspect()
            )
            assertNull(crypto.createGenerationMarker(validRecord()))
            assertFalse(store.containsAlias(markerPrefix + "1"))
            assertFalse(store.containsAlias(aesAlias))
        }

    fun testKeyStoreLoadRuntimeExceptionMakesTrustStoreUnavailable() =
        withIsolatedCrypto(
            keyStoreReader = throwingKeyStoreLoadReader(
                IllegalStateException("injected AndroidKeyStore provider failure")
            )
        ) { crypto, store, markerPrefix, aesAlias, _ ->
            assertNull(crypto.highestObservedGeneration())
            assertEquals(
                AuthorityTrustStoreState.Unavailable,
                OwnerAuthorityTrustStore(crypto, MissingPersistence).inspect()
            )
            assertNull(crypto.createGenerationMarker(validRecord()))
            assertFalse(store.containsAlias(markerPrefix + "1"))
            assertFalse(store.containsAlias(aesAlias))
        }

    fun testKeyStoreAliasEnumerationGeneralSecurityExceptionMakesTrustStoreUnavailable() =
        withIsolatedCrypto(
            keyStoreReader = throwingKeyStoreAliasReader(
                GeneralSecurityException("injected AndroidKeyStore alias enumeration failure")
            )
        ) { crypto, store, markerPrefix, aesAlias, _ ->
            assertNull(crypto.highestObservedGeneration())
            assertEquals(
                AuthorityTrustStoreState.Unavailable,
                OwnerAuthorityTrustStore(crypto, MissingPersistence).inspect()
            )
            assertNull(crypto.createGenerationMarker(validRecord()))
            assertFalse(store.containsAlias(markerPrefix + "1"))
            assertFalse(store.containsAlias(aesAlias))
        }

    fun testKeyStoreAliasEnumerationRuntimeExceptionMakesTrustStoreUnavailable() =
        withIsolatedCrypto(
            keyStoreReader = throwingKeyStoreAliasReader(
                IllegalStateException("injected AndroidKeyStore enumeration provider failure")
            )
        ) { crypto, store, markerPrefix, aesAlias, _ ->
            assertNull(crypto.highestObservedGeneration())
            assertEquals(
                AuthorityTrustStoreState.Unavailable,
                OwnerAuthorityTrustStore(crypto, MissingPersistence).inspect()
            )
            assertNull(crypto.createGenerationMarker(validRecord()))
            assertFalse(store.containsAlias(markerPrefix + "1"))
            assertFalse(store.containsAlias(aesAlias))
        }

    fun testMissingAesKeyWithGenerationMarkerRequiresRecovery() =
        withIsolatedCrypto(SyntheticStrongBoxKeyInfoReader) {
                crypto, store, markerPrefix, aesAlias, _ ->
            createTeeHmac(markerPrefix + "1")
            createTeeAes(aesAlias)
            assertTrue("test AES alias must exist before simulated key loss", store.containsAlias(aesAlias))
            store.deleteEntry(aesAlias)
            assertFalse("AES alias must be absent after simulated key loss", store.containsAlias(aesAlias))

            val envelope = encodeEnvelopeForTest(1L, ByteArray(28))
            assertEquals(
                AuthorityTrustStoreState.RecoveryRequired(
                    1L,
                    AuthorityRecoveryReason.ACTIVE_RECORD_UNREADABLE
                ),
                OwnerAuthorityTrustStore(crypto, PresentPersistence(envelope)).inspect()
            )
        }

    private fun validRecord(): AuthorityTrustRecord {
        val pair = KeyPairGenerator.getInstance("Ed25519", BouncyCastleProvider()).generateKeyPair()
        val spki = pair.public.encoded
        val fingerprint = OwnerAuthorityTrustCeremony.fingerprintForOwner(spki)
        assertNotNull("synthetic Ed25519 public key must be accepted by the policy parser", fingerprint)
        return AuthorityTrustRecord("sec020b6-test", 1L, spki, fingerprint!!)
    }

    private fun createTeeHmac(alias: String): SecretKey {
        val generator = KeyGenerator.getInstance("HmacSHA256", ANDROID_KEYSTORE)
        generator.init(
            KeyGenParameterSpec.Builder(
                alias,
                KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
            ).setDigests(KeyProperties.DIGEST_SHA256).build()
        )
        return generator.generateKey()
    }

    private fun createTeeAes(alias: String) {
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE)
        generator.init(
            KeyGenParameterSpec.Builder(
                alias,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            )
                .setKeySize(256)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build()
        )
        generator.generateKey()
    }

    private fun createTeeEcKeyPair(alias: String) {
        val generator = KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_EC, ANDROID_KEYSTORE)
        generator.initialize(
            KeyGenParameterSpec.Builder(
                alias,
                KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
            ).setDigests(KeyProperties.DIGEST_SHA256).build()
        )
        generator.generateKeyPair()
    }

    private fun securityLevel(store: KeyStore, alias: String): Int {
        val candidate = store.getKey(alias, null)
        if (candidate !is SecretKey) {
            throw AssertionError("expected AndroidKeyStore SecretKey for isolated test alias")
        }
        val key = candidate
        val factory = SecretKeyFactory.getInstance(key.algorithm, ANDROID_KEYSTORE)
        val info = factory.getKeySpec(key, KeyInfo::class.java) as KeyInfo
        return info.securityLevel
    }

    private fun withIsolatedCrypto(
        keyInfoReader: AndroidAuthorityKeyInfoReader? = null,
        keyStoreReader: AndroidAuthorityKeyStoreReader? = null,
        block: (AndroidAuthorityTrustCrypto, KeyStore, String, String, Context) -> Unit
    ) {
        val context = getInstrumentation().targetContext
        val token = UUID.randomUUID().toString().replace("-", "")
        val markerPrefix = "mrnothing_sec020b6_${token}_marker_"
        val aesAlias = "mrnothing_sec020b6_${token}_aes"
        val crypto = AndroidAuthorityTrustCrypto(
            markerPrefix,
            aesAlias,
            keyInfoReader ?: PlatformAndroidAuthorityKeyInfoReader,
            keyStoreReader ?: PlatformAndroidAuthorityKeyStoreReader
        )
        val store = KeyStore.getInstance(ANDROID_KEYSTORE)
        store.load(null)
        try {
            block(crypto, store, markerPrefix, aesAlias, context)
        } finally {
            val cleanup = KeyStore.getInstance(ANDROID_KEYSTORE)
            cleanup.load(null)
            val aliases = cleanup.aliases()
            while (aliases.hasMoreElements()) {
                val alias = aliases.nextElement()
                if (alias.startsWith(markerPrefix)) cleanup.deleteEntry(alias)
            }
            if (cleanup.containsAlias(aesAlias)) cleanup.deleteEntry(aesAlias)
        }
    }

    private fun throwingKeyStoreLoadReader(failure: Exception): AndroidAuthorityKeyStoreReader =
        object : AndroidAuthorityKeyStoreReader {
            override fun load(): KeyStore = throw failure

            override fun aliases(store: KeyStore): Enumeration<String> = store.aliases()
        }

    private fun throwingKeyStoreAliasReader(failure: Exception): AndroidAuthorityKeyStoreReader =
        object : AndroidAuthorityKeyStoreReader {
            override fun load(): KeyStore {
                val store = KeyStore.getInstance(ANDROID_KEYSTORE)
                store.load(null)
                return store
            }

            override fun aliases(store: KeyStore): Enumeration<String> = throw failure
        }

    private fun throwingKeyInfoReader(failure: Exception): AndroidAuthorityKeyInfoReader =
        object : AndroidAuthorityKeyInfoReader {
            override fun securityLevel(key: SecretKey): Int {
                throw failure
            }
        }

    private object SyntheticStrongBoxKeyInfoReader : AndroidAuthorityKeyInfoReader {
        // Metadata-only test double. It does not create or claim a StrongBox key.
        override fun securityLevel(key: SecretKey): Int = KeyProperties.SECURITY_LEVEL_STRONGBOX
    }

    private fun encodeEnvelopeForTest(generation: Long, encrypted: ByteArray): ByteArray {
        val bytes = ByteArrayOutputStream()
        DataOutputStream(bytes).use { output ->
            output.write("MRAENV01".toByteArray(StandardCharsets.US_ASCII))
            output.writeLong(generation)
            output.writeInt(encrypted.size)
            output.write(encrypted)
        }
        return bytes.toByteArray()
    }

    private class PresentPersistence(private val bytes: ByteArray) : AuthorityRecordPersistence {
        override fun read(): AuthorityRecordRead = AuthorityRecordRead.Present(bytes.copyOf())
        override fun writeAtomically(bytes: ByteArray): Boolean = false
    }

    private object MissingPersistence : AuthorityRecordPersistence {
        override fun read(): AuthorityRecordRead = AuthorityRecordRead.Missing
        override fun writeAtomically(bytes: ByteArray): Boolean = false
    }

    private companion object {
        const val ANDROID_KEYSTORE = "AndroidKeyStore"
    }
}
