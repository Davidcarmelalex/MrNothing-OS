package tech.mrnothing.os

import android.content.Context

/**
 * Debug-only Activity host for SEC-020B4D instrumentation.
 * Its manifest entry is non-exported and absent from the release manifest.
 */
internal object OwnerAuthorityTrustTestBackend {
    @Volatile
    var store: OwnerAuthorityTrustStorePort? = null
}

class OwnerAuthorityTrustActivityTestHost : OwnerAuthorityTrustActivity() {
    internal override fun createTrustStore(context: Context): OwnerAuthorityTrustStorePort =
        OwnerAuthorityTrustTestBackend.store
            ?: throw IllegalStateException("SEC-020B4D fake trust store was not configured")
}
