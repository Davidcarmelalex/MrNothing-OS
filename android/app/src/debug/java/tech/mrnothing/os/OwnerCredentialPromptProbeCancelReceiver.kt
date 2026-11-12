package tech.mrnothing.os

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/** Debug-only receiver; the debug manifest requires android.permission.DUMP. */
class OwnerCredentialPromptProbeCancelReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != ACTION_CANCEL) return
        val accepted = OwnerCredentialPromptProbeControl.cancelActive()
        Log.i(TAG, "QA-020B3 cancellation signal accepted=$accepted")
    }

    companion object {
        const val ACTION_CANCEL = "tech.mrnothing.os.debug.CANCEL_CREDENTIAL_PROMPT"
        private const val TAG = "MrNothingCredentialProbe"
    }
}
