package tech.mrnothing.os

import android.app.Activity
import android.app.KeyguardManager
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Color
import android.os.Bundle
import android.os.SystemClock
import android.view.WindowManager
import android.util.TypedValue
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import kotlin.math.roundToInt

/** Non-exported owner-facing credential PREVIEW; no agent execution or permissions. */
class OwnerConsentPreviewActivity : Activity() {
    private val state = ConsentPreviewState(SystemClock::elapsedRealtimeNanos)
    private lateinit var status: TextView
    private var action: String? = null
    private val credentialRequest = 41014
    private fun dp(n: Int) = (n * resources.displayMetrics.density).roundToInt()

    private fun addButton(root: LinearLayout, title: String, hint: String, run: () -> Unit) {
        root.addView(Button(this).apply {
            text = title
            contentDescription = hint
            isAllCaps = false
            filterTouchesWhenObscured = true
            setOnTouchListener { _, event ->
                if (!OwnerConsentTouchGate.isUnobscured(event.flags)) {
                    state.revoke()
                    action = null
                    status.text = "Obscured touch refused. Preview cleared; no device access granted."
                    true
                } else false
            }
            minHeight = dp(56)
            setTextColor(Color.WHITE)
            backgroundTintList = ColorStateList.valueOf(Color.rgb(46, 43, 83))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            setOnClickListener { run() }
        }, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(8) })
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // This is a sensitive credential-adjacent screen, even though it cannot grant consent.
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(24), dp(20), dp(24))
            setBackgroundColor(Color.rgb(10, 12, 22))
        }
        root.addView(TextView(this).apply {
            text = "Owner consent safety preview"
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 24f)
            isAccessibilityHeading = true
        })
        status = TextView(this).apply {
            text = "Credential verification only. No screen reading, UI control, Android " +
                "permission or consent capability can be granted here."
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            setPadding(0, dp(16), 0, dp(16))
            accessibilityLiveRegion = TextView.ACCESSIBILITY_LIVE_REGION_POLITE
        }
        root.addView(status)
        addButton(root, "Screen-reading preview", "Verify device credential for screen-reading preview only") {
            begin("read_screen")
        }
        addButton(root, "Navigation preview", "Verify device credential for navigation preview only") {
            begin("navigate")
        }
        addButton(root, "Scrolling preview", "Verify device credential for scrolling preview only") {
            begin("scroll")
        }
        addButton(root, "Cancel and clear preview", "Clear any pending local credential preview") {
            state.revoke()
            action = null
            status.text = "Preview cleared. No device access granted."
        }
        addButton(root, "Return to launcher", "Return to Mr. Nothing launcher") {
            state.revoke()
            action = null
            finish()
        }
        setContentView(ScrollView(this).apply { addView(root) })
    }

    @Suppress("DEPRECATION")
    private fun begin(scope: String) {
        // Real local Android state, not an approval flag from an agent request.
        if (!OwnerCredentialSafetyGate.isSafe(this)) {
            state.revoke()
            action = null
            status.text = "Device must be unlocked, active and secured. Preview refused."
            return
        }
        val keyguard = getSystemService(KeyguardManager::class.java)
        if (keyguard == null || !keyguard.isDeviceSecure) {
            status.text = "Secure device lock is not configured. Preview refused."
            return
        }
        if (!state.begin(scope)) {
            status.text = "A preview is pending. Cancel before retrying."
            return
        }
        val prompt = keyguard.createConfirmDeviceCredentialIntent(
            "Mr. Nothing safety preview", "Verify credential; no device access will be enabled"
        )
        if (prompt == null) {
            state.revoke()
            status.text = "System credential prompt unavailable. Preview refused."
            return
        }
        action = scope
        try {
            startActivityForResult(prompt, credentialRequest)
        } catch (_: ActivityNotFoundException) {
            state.revoke()
            action = null
            status.text = "System credential prompt unavailable. Preview refused."
        } catch (_: SecurityException) {
            state.revoke()
            action = null
            status.text = "System credential prompt denied. Preview refused."
        }
    }

    @Deprecated("System credential result; never issues a capability")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != credentialRequest) return
        val scope = action
        action = null
        // Re-check after returning from the system credential UI: lock state
        // may have changed while the prompt was visible.
        val verified = state.finish(
            resultCode == RESULT_OK && OwnerCredentialSafetyGate.isSafe(this)
        )
        status.text = if (verified && scope != null) {
            "Device credential verified for $scope preview only. No consent capability " +
                "or Android permission issued. Screen and UI actions remain disabled."
        } else "Preview canceled, expired or refused. No device access granted."
    }

    override fun onDestroy() {
        state.revoke()
        action = null
        super.onDestroy()
    }
}
