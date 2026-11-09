package tech.mrnothing.os

import android.app.Service
import android.content.Intent
import android.os.IBinder

/**
 * SEC-023B1A: dormant, non-exported native component reservation only.
 *
 * The release manifest MUST keep this service disabled until an independently
 * reviewed Keystore-backed, owner-authenticated implementation exists. There
 * is intentionally no Binder, persistence, memory API, or agent integration.
 */
internal class MemoryVaultService : Service() {
    /** No IPC capability exists, including for same-UID callers. */
    override fun onBind(intent: Intent?): IBinder? = null

    /** Defense in depth if a future manifest accidentally permits a start. */
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        stopSelfResult(startId)
        return START_NOT_STICKY
    }
}
