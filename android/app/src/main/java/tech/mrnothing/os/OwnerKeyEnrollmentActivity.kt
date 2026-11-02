package tech.mrnothing.os

import android.app.Activity
import android.app.KeyguardManager
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Color
import android.os.Bundle
import android.os.SystemClock
import android.util.TypedValue
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import kotlin.math.roundToInt

/**
 * Non-exported, foreground-only enrollment. A local tap and system credential
 * are required. No command executor, key signing or consent issuer is connected.
 */
class OwnerKeyEnrollmentActivity : Activity() {
    private val state = OwnerEnrollmentState(SystemClock::elapsedRealtimeNanos)
    private val credentialRequest = 41015
    private lateinit var status: TextView
    private fun dp(n: Int) = (n * resources.displayMetrics.density).roundToInt()

    private fun addButton(root: LinearLayout, title: String, description: String, run: () -> Unit) {
        root.addView(Button(this).apply {
            text = title
            contentDescription = description
            isAllCaps = false
            minHeight = dp(56)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            setTextColor(Color.WHITE)
            backgroundTintList = ColorStateList.valueOf(Color.rgb(46, 43, 83))
            filterTouchesWhenObscured = true
            setOnTouchListener { _, event ->
                if (!OwnerConsentTouchGate.isUnobscured(event.flags)) {
                    state.revoke()
                    status.text = "Obscured touch refused. Enrollment canceled."
                    true
                } else false
            }
            setOnClickListener { run() }
        }, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(8) })
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(24), dp(20), dp(24))
            setBackgroundColor(Color.rgb(10, 12, 22))
        }
        root.addView(TextView(this).apply {
            text = "Local security-key enrollment"
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 24f)
            isAccessibilityHeading = true
        })
        status = TextView(this).apply {
            text = "Optional: create a hardware-protected local key after device-credential " +
                "confirmation. Requires Android 12+ and StrongBox. No agent access, " +
                "screen permission or consent is granted. Existing keys are never replaced."
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            setPadding(0, dp(16), 0, dp(16))
            accessibilityLiveRegion = TextView.ACCESSIBILITY_LIVE_REGION_POLITE
        }
        root.addView(status)
        addButton(root, "Enroll local security key",
            "Confirm device credential to create a local hardware security key only") {
            beginEnrollment()
        }
        addButton(root, "Cancel enrollment", "Cancel pending security key enrollment") {
            state.revoke()
            status.text = "Enrollment canceled. No agent access granted."
        }
        addButton(root, "Return to launcher", "Return without enabling agent access") {
            state.revoke()
            finish()
        }
        setContentView(ScrollView(this).apply { addView(root) })
    }

    @Suppress("DEPRECATION")
    private fun beginEnrollment() {
        if (!OwnerCredentialSafetyGate.isSafe(this)) {
            state.revoke()
            status.text = "Unlocked, active device with secure lock required. Refused."
            return
        }
        if (OwnerKeystorePreflight.inspectExisting() != OwnerKeyReadiness.BLOCKED) {
            status.text = "A verified local key already exists. No replacement attempted."
            return
        }
        if (!state.begin()) {
            status.text = "Enrollment already pending. Cancel before retrying."
            return
        }
        val manager = getSystemService(KeyguardManager::class.java)
        val prompt = manager?.createConfirmDeviceCredentialIntent(
            "Local security-key enrollment",
            "Confirm device credential; no agent access will be enabled"
        )
        if (prompt == null) {
            state.revoke()
            status.text = "System credential prompt unavailable. Refused."
            return
        }
        try {
            startActivityForResult(prompt, credentialRequest)
        } catch (_: ActivityNotFoundException) {
            state.revoke()
            status.text = "Credential prompt unavailable. Refused."
        } catch (_: SecurityException) {
            state.revoke()
            status.text = "Credential prompt denied. Refused."
        }
    }

    @Deprecated("Credential result is not a consent grant")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != credentialRequest) return
        if (!state.finish(resultCode == RESULT_OK && OwnerCredentialSafetyGate.isSafe(this))) {
            status.text = "Credential canceled, expired or unsafe. No key enrolled."
            return
        }
        status.text = when (OwnerKeyEnrollment.enrollAfterCredential(this)) {
            OwnerEnrollmentResult.ENROLLED_LOCAL_KEY_ONLY ->
                "Local StrongBox key verified. No agent permission or consent granted."
            OwnerEnrollmentResult.EXISTING_ALIAS_NOT_OVERWRITTEN ->
                "Existing key alias preserved. No replacement attempted."
            OwnerEnrollmentResult.BLOCKED_UNSAFE_DEVICE ->
                "Device lock state unsafe. Enrollment refused."
            OwnerEnrollmentResult.BLOCKED_UNSUPPORTED_PLATFORM ->
                "Android version unsupported. Enrollment refused."
            OwnerEnrollmentResult.BLOCKED_KEYSTORE ->
                "StrongBox unavailable or key verification failed. Enrollment blocked."
        }
    }

    override fun onDestroy() {
        state.revoke()
        super.onDestroy()
    }
}
