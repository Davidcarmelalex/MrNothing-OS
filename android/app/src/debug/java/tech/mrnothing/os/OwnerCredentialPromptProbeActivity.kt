package tech.mrnothing.os

import android.app.Activity
import android.hardware.biometrics.BiometricManager
import android.hardware.biometrics.BiometricPrompt
import android.os.Build
import android.os.Bundle
import android.os.CancellationSignal
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

/**
 * Debug-variant-only runtime probe for the exact prompt factory used by SEC-020B3.
 * It never reads or mutates the authority trust store, grants permissions, or invokes an agent.
 */
class OwnerCredentialPromptProbeActivity : Activity() {
    private lateinit var status: TextView
    private var cancellation: CancellationSignal? = null

    private fun button(root: LinearLayout, label: String, action: () -> Unit) {
        root.addView(Button(this).apply {
            text = label
            contentDescription = label
            isAllCaps = false
            minHeight = 56
            setOnClickListener { action() }
        }, LinearLayout.LayoutParams(-1, -2))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 24, 24, 24)
        }
        root.addView(TextView(this).apply {
            text = "Device credential prompt probe"
            textSize = 22f
            isAccessibilityHeading = true
        })
        status = TextView(this).apply {
            text = "STATUS: READY"
            textSize = 16f
            accessibilityLiveRegion = TextView.ACCESSIBILITY_LIVE_REGION_POLITE
        }
        root.addView(status)
        button(root, "Authenticate with device credential") { authenticate() }
        button(root, "Cancel prompt") { cancelPrompt() }
        root.addView(TextView(this).apply {
            text = "Debug probe only. No trust store, permissions or device actions are connected."
            textSize = 14f
        })
        setContentView(root)
    }

    private fun authenticate() {
        if (cancellation != null) {
            status.text = "STATUS: PROMPT_ALREADY_ACTIVE"
            return
        }
        if (!OwnerCredentialAuthenticationPolicy.supportsCredentialOnlyPrompt(
                Build.VERSION.SDK_INT
            )
        ) {
            status.text = "STATUS: API_UNSUPPORTED"
            return
        }
        if (!OwnerCredentialSafetyGate.isSafe(this)) {
            status.text = "STATUS: DEVICE_SAFETY_REFUSED"
            return
        }
        val manager = getSystemService(BiometricManager::class.java)
        if (manager == null ||
            manager.canAuthenticate(
                BiometricManager.Authenticators.DEVICE_CREDENTIAL
            ) != BiometricManager.BIOMETRIC_SUCCESS
        ) {
            status.text = "STATUS: DEVICE_CREDENTIAL_UNAVAILABLE"
            return
        }
        val prompt = try {
            OwnerCredentialPromptFactory.create(
                this,
                "Mr. Nothing QA credential probe",
                "Test-only emulator PIN",
                "This disposable emulator probe performs no trust or device action."
            )
        } catch (_: RuntimeException) {
            status.text = "STATUS: PROMPT_BUILD_REFUSED"
            return
        }
        val signal = CancellationSignal()
        cancellation = signal
        status.text = "STATUS: PROMPT_ACTIVE"
        try {
            prompt.authenticate(
                signal,
                mainExecutor,
                object : BiometricPrompt.AuthenticationCallback() {
                    override fun onAuthenticationSucceeded(
                        result: BiometricPrompt.AuthenticationResult
                    ) {
                        cancellation = null
                        val accepted =
                            OwnerCredentialAuthenticationPolicy.acceptsDeviceCredential(
                                Build.VERSION.SDK_INT,
                                result.authenticationType,
                                BiometricPrompt.AUTHENTICATION_RESULT_TYPE_DEVICE_CREDENTIAL
                            ) && OwnerCredentialSafetyGate.isSafe(this@OwnerCredentialPromptProbeActivity)
                        status.text = if (accepted) {
                            "STATUS: DEVICE_CREDENTIAL_ACCEPTED"
                        } else {
                            "STATUS: UNEXPECTED_AUTHENTICATOR_OR_UNSAFE"
                        }
                    }

                    override fun onAuthenticationError(
                        errorCode: Int,
                        errString: CharSequence
                    ) {
                        cancellation = null
                        status.text = "STATUS: PROMPT_ERROR:$errorCode"
                    }

                    override fun onAuthenticationFailed() {
                        status.text = "STATUS: AUTHENTICATION_FAILED"
                    }
                }
            )
        } catch (_: RuntimeException) {
            cancellation = null
            status.text = "STATUS: PROMPT_START_REFUSED"
        }
    }

    private fun cancelPrompt() {
        val active = cancellation
        if (active == null) {
            status.text = "STATUS: NO_ACTIVE_PROMPT"
            return
        }
        active.cancel()
        status.text = "STATUS: CANCEL_REQUESTED"
    }

    override fun onDestroy() {
        cancellation?.cancel()
        cancellation = null
        super.onDestroy()
    }
}
