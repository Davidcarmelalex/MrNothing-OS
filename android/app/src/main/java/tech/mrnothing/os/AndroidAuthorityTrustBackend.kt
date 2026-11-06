package tech.mrnothing.os

import android.content.Context
import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyInfo
import android.security.keystore.KeyProperties
import android.util.AtomicFile
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileNotFoundException
import java.io.FileOutputStream
import java.io.IOException
import java.nio.charset.StandardCharsets
import java.security.GeneralSecurityException
import java.security.KeyStore
import java.security.MessageDigest
import java.util.Enumeration
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.Mac
import javax.crypto.SecretKey
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.GCMParameterSpec

/**
 * SEC-020B1 Android backend. It refuses to fall back from StrongBox to TEE or
 * software. Marker aliases are append-only; ordinary rotation never deletes them.
 */
private const val DEFAULT_AES_ALIAS = "mrnothing_authority_record_aes_v1"
private const val DEFAULT_MARKER_PREFIX = "mrnothing_authority_marker_v1_"

/**
 * Alias overrides are a test-isolation seam only. Production construction uses
 * the original defaults; instrumentation tests supply a unique disposable namespace.
 */
internal class AndroidAuthorityTrustCrypto(
    private val markerPrefix: String = DEFAULT_MARKER_PREFIX,
    private val aesAlias: String = DEFAULT_AES_ALIAS
) : AuthorityTrustCrypto {
    init {
        require(markerPrefix.isNotBlank())
        require(aesAlias.isNotBlank())
        require(!aesAlias.startsWith(markerPrefix))
    }
    override fun highestObservedGeneration(): Long? = synchronized(LOCK) {
        try {
            val store = loadKeyStore() ?: return@synchronized null
            highestObservedGeneration(store)
        } catch (_: GeneralSecurityException) {
            null
        } catch (_: IOException) {
            null
        } catch (_: RuntimeException) {
            null
        }
    }

    override fun createGenerationMarker(record: AuthorityTrustRecord): ByteArray? =
        synchronized(LOCK) {
            try {
                val store = loadKeyStore() ?: return@synchronized null
                val highest = highestObservedGeneration(store) ?: return@synchronized null
                if (highest == Long.MAX_VALUE || record.generation != highest + 1L) {
                    return@synchronized null
                }
                if (!validRecord(record)) return@synchronized null
                val alias = markerAlias(record.generation)
                if (store.containsAlias(alias)) return@synchronized null

                val generator = KeyGenerator.getInstance(HMAC_ALGORITHM, ANDROID_KEYSTORE)
                generator.init(
                    KeyGenParameterSpec.Builder(
                        alias,
                        KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
                    )
                        .setDigests(KeyProperties.DIGEST_SHA256)
                        .setIsStrongBoxBacked(true)
                        .build()
                )
                val key = generator.generateKey()
                if (!isStrongBoxBacked(key)) return@synchronized null
                hmac(key, markerPayload(record))
            } catch (_: GeneralSecurityException) {
                null
            } catch (_: IOException) {
                null
            } catch (_: RuntimeException) {
                null
            }
        }

    override fun verifyGenerationMarker(
        record: AuthorityTrustRecord,
        proof: ByteArray
    ): Boolean = synchronized(LOCK) {
        if (proof.size != AuthorityTrustStoreLimits.MARKER_PROOF_BYTES ||
            !validRecord(record)
        ) return@synchronized false
        try {
            val store = loadKeyStore() ?: return@synchronized false
            val key = store.getKey(markerAlias(record.generation), null) as? SecretKey
                ?: return@synchronized false
            if (!isStrongBoxBacked(key)) return@synchronized false
            MessageDigest.isEqual(proof, hmac(key, markerPayload(record)))
        } catch (_: GeneralSecurityException) {
            false
        } catch (_: IOException) {
            false
        } catch (_: RuntimeException) {
            false
        }
    }

    override fun encrypt(plaintext: ByteArray, associatedData: ByteArray): ByteArray? =
        synchronized(LOCK) {
            try {
                val store = loadKeyStore() ?: return@synchronized null
                val highest = highestObservedGeneration(store) ?: return@synchronized null
                if (highest <= 0L) return@synchronized null
                val key = getOrCreateEncryptionKey(store) ?: return@synchronized null
                val cipher = Cipher.getInstance(AES_TRANSFORMATION)
                cipher.init(Cipher.ENCRYPT_MODE, key)
                cipher.updateAAD(associatedData)
                val encrypted = cipher.doFinal(plaintext)
                val iv = cipher.iv
                if (iv.size != GCM_IV_BYTES) return@synchronized null
                ByteArray(iv.size + encrypted.size).also {
                    System.arraycopy(iv, 0, it, 0, iv.size)
                    System.arraycopy(encrypted, 0, it, iv.size, encrypted.size)
                }
            } catch (_: GeneralSecurityException) {
                null
            } catch (_: IOException) {
                null
            } catch (_: RuntimeException) {
                null
            }
        }

    override fun decrypt(envelope: ByteArray, associatedData: ByteArray): ByteArray? =
        synchronized(LOCK) {
            if (envelope.size < GCM_IV_BYTES + GCM_TAG_BYTES ||
                envelope.size > AuthorityTrustStoreLimits.MAX_ENVELOPE_BYTES
            ) return@synchronized null
            try {
                val store = loadKeyStore() ?: return@synchronized null
                val highest = highestObservedGeneration(store) ?: return@synchronized null
                if (highest <= 0L) return@synchronized null
                val key = store.getKey(aesAlias, null) as? SecretKey
                    ?: return@synchronized null
                if (!isStrongBoxBacked(key)) return@synchronized null
                val iv = envelope.copyOfRange(0, GCM_IV_BYTES)
                val ciphertext = envelope.copyOfRange(GCM_IV_BYTES, envelope.size)
                val cipher = Cipher.getInstance(AES_TRANSFORMATION)
                cipher.init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(GCM_TAG_BITS, iv))
                cipher.updateAAD(associatedData)
                cipher.doFinal(ciphertext)
            } catch (_: GeneralSecurityException) {
                null
            } catch (_: IOException) {
                null
            } catch (_: RuntimeException) {
                null
            }
        }

    private fun highestObservedGeneration(store: KeyStore): Long? {
        // KeyInfo.securityLevel is required to distinguish StrongBox from TEE.
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return null
        var highest = 0L
        val aliases: Enumeration<String> = store.aliases()
        while (aliases.hasMoreElements()) {
            val alias = aliases.nextElement()
            if (!alias.startsWith(markerPrefix)) continue
            val suffix = alias.removePrefix(markerPrefix)
            val generation = suffix.toLongOrNull() ?: return null
            if (generation <= 0L || generation.toString() != suffix) return null
            val key = store.getKey(alias, null) as? SecretKey ?: return null
            if (!isStrongBoxBacked(key)) return null
            if (generation > highest) highest = generation
        }
        // An encryption key without any generation marker is an inconsistent
        // partial state, not a fresh installation.
        if (highest == 0L && store.containsAlias(aesAlias)) return null
        return highest
    }

    private fun getOrCreateEncryptionKey(store: KeyStore): SecretKey? {
        if (store.containsAlias(aesAlias)) {
            val existing = store.getKey(aesAlias, null) as? SecretKey ?: return null
            return if (isStrongBoxBacked(existing)) existing else null
        }
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE)
        generator.init(
            KeyGenParameterSpec.Builder(
                aesAlias,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            )
                .setKeySize(AES_KEY_BITS)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .setIsStrongBoxBacked(true)
                .build()
        )
        val generated = generator.generateKey()
        return if (isStrongBoxBacked(generated)) generated else null
    }

    private fun isStrongBoxBacked(key: SecretKey): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return false
        val factory = SecretKeyFactory.getInstance(key.algorithm, ANDROID_KEYSTORE)
        val info = factory.getKeySpec(key, KeyInfo::class.java) as KeyInfo
        return info.securityLevel == KeyProperties.SECURITY_LEVEL_STRONGBOX
    }

    private fun loadKeyStore(): KeyStore? {
        val store = KeyStore.getInstance(ANDROID_KEYSTORE)
        store.load(null)
        return store
    }

    private fun validRecord(record: AuthorityTrustRecord): Boolean =
        record.generation > 0L &&
            OwnerAuthorityTrustCeremony.fingerprintForOwner(record.publicKeySpkiDer) ==
                record.fingerprint

    private fun markerAlias(generation: Long) = markerPrefix + generation.toString()

    private fun markerPayload(record: AuthorityTrustRecord): ByteArray {
        val bytes = ByteArrayOutputStream()
        java.io.DataOutputStream(bytes).use { output ->
            output.write(MARKER_DOMAIN)
            output.writeLong(record.generation)
            writeField(output, record.keyId.toByteArray(StandardCharsets.US_ASCII))
            writeField(output, record.publicKeySpkiDer)
            writeField(output, record.fingerprint.toByteArray(StandardCharsets.US_ASCII))
        }
        return bytes.toByteArray()
    }

    private fun writeField(output: java.io.DataOutputStream, value: ByteArray) {
        output.writeInt(value.size)
        output.write(value)
    }

    private fun hmac(key: SecretKey, payload: ByteArray): ByteArray =
        Mac.getInstance(HMAC_ALGORITHM).run {
            init(key)
            doFinal(payload)
        }

    private companion object {
        const val ANDROID_KEYSTORE = "AndroidKeyStore"
        const val HMAC_ALGORITHM = "HmacSHA256"
        const val AES_TRANSFORMATION = "AES/GCM/NoPadding"
        const val AES_KEY_BITS = 256
        const val GCM_IV_BYTES = 12
        const val GCM_TAG_BITS = 128
        const val GCM_TAG_BYTES = GCM_TAG_BITS / 8
        val MARKER_DOMAIN =
            "MRNOTHING-AUTHORITY-GENERATION-MARKER-V1\u0000"
                .toByteArray(StandardCharsets.US_ASCII)
        val LOCK = Any()
    }
}

/** Private, no-backup app storage using Android AtomicFile's replace protocol. */
internal class AndroidAtomicAuthorityRecordPersistence(
    context: Context
) : AuthorityRecordPersistence {
    private val directory = context.applicationContext.noBackupFilesDir
    private val file = File(directory, FILE_NAME)
    private val atomicFile = AtomicFile(file)

    override fun read(): AuthorityRecordRead = synchronized(LOCK) {
        val input = try {
            atomicFile.openRead()
        } catch (_: FileNotFoundException) {
            return@synchronized AuthorityRecordRead.Missing
        } catch (_: IOException) {
            return@synchronized AuthorityRecordRead.Failed
        } catch (_: RuntimeException) {
            return@synchronized AuthorityRecordRead.Failed
        }
        try {
            input.use { stream ->
                val output = ByteArrayOutputStream()
                val buffer = ByteArray(512)
                var total = 0
                while (true) {
                    val count = stream.read(buffer)
                    if (count < 0) break
                    total += count
                    if (total > AuthorityTrustStoreLimits.MAX_ENVELOPE_BYTES) {
                        return@synchronized AuthorityRecordRead.Failed
                    }
                    output.write(buffer, 0, count)
                }
                AuthorityRecordRead.Present(output.toByteArray())
            }
        } catch (_: IOException) {
            AuthorityRecordRead.Failed
        } catch (_: RuntimeException) {
            AuthorityRecordRead.Failed
        }
    }

    override fun writeAtomically(bytes: ByteArray): Boolean = synchronized(LOCK) {
        if (bytes.isEmpty() || bytes.size > AuthorityTrustStoreLimits.MAX_ENVELOPE_BYTES) {
            return@synchronized false
        }
        var output: FileOutputStream? = null
        try {
            if (!directory.exists() && !directory.mkdirs()) return@synchronized false
            output = atomicFile.startWrite()
            output.write(bytes)
            output.fd.sync()
            atomicFile.finishWrite(output)
            output = null
            true
        } catch (_: IOException) {
            output?.let {
                try { atomicFile.failWrite(it) } catch (_: RuntimeException) { }
            }
            false
        } catch (_: RuntimeException) {
            output?.let {
                try { atomicFile.failWrite(it) } catch (_: RuntimeException) { }
            }
            false
        }
    }

    private companion object {
        const val FILE_NAME = "owner-authority-trust-v1.enc"
        val LOCK = Any()
    }
}

internal class AndroidOwnerAuthorityTrustStore(context: Context) : OwnerAuthorityTrustStorePort {
    private val delegate = OwnerAuthorityTrustStore(
        AndroidAuthorityTrustCrypto(),
        AndroidAtomicAuthorityRecordPersistence(context)
    )

    override fun inspect(): AuthorityTrustStoreState = delegate.inspect()

    override fun commit(proposal: AuthorityTrustDecision.Ready): AuthorityTrustStoreCommit =
        delegate.commit(proposal)
}
