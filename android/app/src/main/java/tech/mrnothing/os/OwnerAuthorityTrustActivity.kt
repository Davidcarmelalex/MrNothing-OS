package tech.mrnothing.os

import android.app.Activity
import android.content.Context
import android.app.KeyguardManager
import android.hardware.biometrics.BiometricManager
import android.hardware.biometrics.BiometricPrompt
import android.content.res.ColorStateList
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.os.CancellationSignal
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.text.InputType
import android.util.TypedValue
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import kotlin.math.roundToInt

/**
 * SEC-020B2: owner-visible, offline authority import and trust transition.
 * This Activity never grants Android permissions or connects enrollment/execution.
 */
open class OwnerAuthorityTrustActivity : Activity() {
    private val confirmation = OwnerAuthorityConfirmationState(
        SystemClock::elapsedRealtimeNanos
    )
    private var credentialCancellation: CancellationSignal? = null
    private val mainHandler = Handler(Looper.getMainLooper())
    private val operationGate = OwnerAuthorityOperationGate()
    private var activeOperationToken: Long? = null
    private var trustStateLoaded = false

    private lateinit var keyIdField: EditText
    private lateinit var generationField: EditText
    private lateinit var spkiField: EditText
    private lateinit var rotationSignatureField: EditText
    private lateinit var fingerprintField: EditText
    private lateinit var independentFingerprintConfirmed: CheckBox
    private lateinit var fingerprintStatus: TextView
    private lateinit var trustState: TextView
    private lateinit var status: TextView
    private lateinit var previewButton: Button
    private lateinit var confirmButton: Button
    private var pendingBinding: String? = null

    /**
     * Test substitution is provided only by a non-exported debug Activity host.
     * The production Activity always uses the Android Keystore/AtomicFile backend.
     */
    internal open fun createTrustStore(context: Context): OwnerAuthorityTrustStorePort =
        AndroidOwnerAuthorityTrustStore(context)

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).roundToInt()

    private fun label(root: LinearLayout, value: String, heading: Boolean = false) {
        root.addView(TextView(this).apply {
            text = value
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, if (heading) 22f else 15f)
            setPadding(0, dp(8), 0, dp(4))
            if (heading) isAccessibilityHeading = true
        })
    }

    private fun field(
        root: LinearLayout,
        title: String,
        hint: String,
        inputType: Int,
        multiline: Boolean = false
    ): EditText {
        val edit = EditText(this).apply {
            id = View.generateViewId()
            this.hint = hint
            this.inputType = inputType
            setSingleLine(!multiline)
            minHeight = dp(if (multiline) 88 else 56)
            setPadding(dp(12), dp(10), dp(12), dp(10))
            setTextColor(Color.WHITE)
            setHintTextColor(Color.rgb(180, 184, 200))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            backgroundTintList = ColorStateList.valueOf(Color.rgb(190, 164, 255))
            filterTouchesWhenObscured = true
            setOnTouchListener { _, event ->
                if (!OwnerConsentTouchGate.isUnobscured(event.flags)) {
                    if (cancelPending(false)) {
                        status.text = "Obscured touch refused. Authority confirmation canceled."
                    }
                    true
                } else false
            }
        }
        root.addView(TextView(this).apply {
            text = title
            labelFor = edit.id
            setTextColor(Color.rgb(206, 210, 226))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
            setPadding(0, dp(8), 0, dp(2))
        })
        root.addView(edit, LinearLayout.LayoutParams(-1, -2).apply {
            bottomMargin = dp(6)
        })
        return edit
    }

    private fun addButton(
        root: LinearLayout,
        title: String,
        description: String,
        action: () -> Unit
    ): Button {
        val button = Button(this).apply {
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
                    if (cancelPending(false)) {
                        status.text = "Obscured touch refused. Authority confirmation canceled."
                    }
                    true
                } else false
            }
            setOnClickListener { action() }
        }
        root.addView(button, LinearLayout.LayoutParams(-1, -2).apply {
            bottomMargin = dp(8)
        })
        return button
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(24), dp(20), dp(24))
            setBackgroundColor(Color.rgb(10, 12, 22))
        }
        label(root, "Offline authority trust", heading = true)
        label(
            root,
            "This local ceremony imports a public authority key only. It does not create " +
                "an owner key, grant Android permissions, enroll a remote device or enable an agent."
        )

        trustState = TextView(this).apply {
            setTextColor(Color.rgb(206, 210, 226))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f)
            accessibilityLiveRegion = TextView.ACCESSIBILITY_LIVE_REGION_POLITE
            setPadding(0, dp(8), 0, dp(12))
        }
        root.addView(trustState)

        keyIdField = field(
            root, "Authority key identifier", "Example: authority-2026-01",
            InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS
        )
        generationField = field(
            root, "Generation", "Positive decimal integer, no leading zeros",
            InputType.TYPE_CLASS_NUMBER
        )
        spkiField = field(
            root, "Ed25519 public-key SPKI DER (canonical Base64)",
            "Paste one canonical Base64 line",
            InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS or
                InputType.TYPE_TEXT_FLAG_MULTI_LINE,
            multiline = true
        )
        rotationSignatureField = field(
            root, "Current-authority rotation signature (Base64)",
            "Required only when rotating an existing authority",
            InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS or
                InputType.TYPE_TEXT_FLAG_MULTI_LINE,
            multiline = true
        )
        fingerprintField = field(
            root, "Independently obtained SHA-256 fingerprint",
            "SHA256: followed by 64 uppercase hexadecimal characters",
            InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS
        )

        fingerprintStatus = TextView(this).apply {
            setTextColor(Color.rgb(190, 164, 255))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f)
            accessibilityLiveRegion = TextView.ACCESSIBILITY_LIVE_REGION_POLITE
            setPadding(0, dp(8), 0, dp(8))
        }
        root.addView(fingerprintStatus)

        independentFingerprintConfirmed = CheckBox(this).apply {
            text = "I compared this fingerprint with a separate trusted out-of-band source."
            contentDescription = text
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f)
            minHeight = dp(56)
            filterTouchesWhenObscured = true
            setOnTouchListener { _, event ->
                if (!OwnerConsentTouchGate.isUnobscured(event.flags)) {
                    if (cancelPending(false)) {
                        status.text = "Obscured touch refused. Authority confirmation canceled."
                    }
                    true
                } else false
            }
        }
        root.addView(independentFingerprintConfirmed)

        status = TextView(this).apply {
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            accessibilityLiveRegion = TextView.ACCESSIBILITY_LIVE_REGION_POLITE
            setPadding(0, dp(12), 0, dp(12))
        }
        root.addView(status)

        previewButton = addButton(
            root, "Calculate candidate fingerprint",
            "Calculate the fingerprint of the entered Ed25519 public key"
        ) { updateFingerprintPreview() }

        confirmButton = addButton(
            root, "Confirm and store authority",
            "Require separate fingerprint confirmation and fresh Android device credential"
        ) { beginConfirmation() }

        addButton(
            root, "Cancel and clear",
            "Cancel any pending trust ceremony and clear imported public-key fields"
        ) { if (cancelPending(true)) status.text = "Canceled. No trust change was made." }

        addButton(
            root, "Return to launcher",
            "Return to Mr. Nothing without changing authority trust"
        ) { if (cancelPending(true)) finish() }

        setContentView(ScrollView(this).apply {
            isFillViewport = true
            addView(root)
        })
        refreshTrustState()
        status.text = "No authority change is pending. Compare the fingerprint independently."
    }

    private fun updateFingerprintPreview() {
        val fingerprint = AuthorityTrustImportParser.fingerprintPreview(
            keyIdField.text.toString(),
            generationField.text.toString(),
            spkiField.text.toString()
        )
        fingerprintStatus.text = if (fingerprint == null) {
            "Candidate fingerprint unavailable. Check the key identifier, generation and canonical Base64."
        } else {
            "Candidate fingerprint:\n" + fingerprint +
                "\nObtain the same value through a separate trusted channel before confirming."
        }
    }

    private fun parseInput(): ParsedAuthorityTrustImport? {
        return when (val parsed = AuthorityTrustImportParser.parse(
            keyIdField.text.toString(),
            generationField.text.toString(),
            spkiField.text.toString(),
            rotationSignatureField.text.toString(),
            fingerprintField.text.toString()
        )) {
            is AuthorityTrustImportParseResult.Valid -> parsed.value
            is AuthorityTrustImportParseResult.Invalid -> {
                status.text = "Import refused: " + parsed.reason.name
                null
            }
        }
    }

    private fun beginConfirmation() {
        if (pendingBinding != null || activeOperationToken != null) {
            status.text = "A trust confirmation or store operation is already pending."
            return
        }
        if (!trustStateLoaded) {
            status.text = "Trust state is still being checked. Wait before confirming."
            return
        }
        if (!OwnerCredentialSafetyGate.isSafe(this)) {
            status.text = "Secure, unlocked and interactive device state required. Refused."
            return
        }
        if (!OwnerCredentialAuthenticationPolicy.supportsCredentialOnlyPrompt(
                Build.VERSION.SDK_INT
            )
        ) {
            status.text = "Android 11 or later is required for credential-only confirmation. Refused."
            return
        }
        if (!independentFingerprintConfirmed.isChecked) {
            status.text = "Separate out-of-band fingerprint comparison is required."
            return
        }
        val parsed = parseInput() ?: return
        val token = operationGate.begin()
        if (token == null) {
            status.text = "Another trust-store operation is active. Refused."
            return
        }
        activeOperationToken = token
        setFormEnabled(false)
        status.text = "Checking trust state before credential confirmation..."
        val appContext = applicationContext
        OwnerAuthorityIoCoordinator.execute {
            if (!operationGate.isActive(token)) return@execute
            val current = try {
                createTrustStore(appContext).inspect()
            } catch (_: RuntimeException) {
                AuthorityTrustStoreState.Unavailable
            }
            mainHandler.post {
                if (!operationGate.isActive(token) || isFinishing || isDestroyed) {
                    operationGate.finish(token)
                    return@post
                }
                continueConfirmation(token, parsed, current)
            }
        }
    }

    private fun continueConfirmation(
        token: Long,
        parsed: ParsedAuthorityTrustImport,
        current: AuthorityTrustStoreState
    ) {
        if (!OwnerCredentialSafetyGate.isSafe(this)) {
            finishOperation(token)
            setFormEnabled(true)
            status.text = "Device became unsafe while checking trust state. Refused."
            return
        }
        val snapshot = storeSnapshot(current)
        val mode = modeForState(current)
        if (snapshot == null || mode == null) {
            finishOperation(token)
            setFormEnabled(true)
            status.text = "Trust state is unavailable or corrupt. Refused."
            refreshTrustState()
            return
        }
        val preview = prepareDecision(current, parsed, ownerConfirmation = false)
        if (preview !is AuthorityTrustDecision.Blocked ||
            preview.reason != AuthorityTrustBlockReason.OWNER_CONFIRMATION_REQUIRED
        ) {
            finishOperation(token)
            setFormEnabled(true)
            status.text = "Proposal refused: " + decisionDescription(preview)
            return
        }
        val binding = AuthorityTrustImportParser.confirmationBinding(
            mode, snapshot, parsed.inputBinding
        )
        if (!confirmation.begin(binding)) {
            finishOperation(token)
            setFormEnabled(true)
            status.text = "Confirmation state unavailable or already pending. Refused."
            return
        }
        pendingBinding = binding

        val keyguard = getSystemService(KeyguardManager::class.java)
        if (keyguard == null || !keyguard.isDeviceSecure) {
            cancelPending(false)
            status.text = "Android device credential is not configured. Refused."
            return
        }
        val biometricManager = getSystemService(BiometricManager::class.java)
        if (biometricManager == null ||
            biometricManager.canAuthenticate(
                BiometricManager.Authenticators.DEVICE_CREDENTIAL
            ) != BiometricManager.BIOMETRIC_SUCCESS
        ) {
            cancelPending(false)
            status.text = "Android device credential is unavailable. Refused."
            return
        }

        val prompt = try {
            OwnerCredentialPromptFactory.create(
                this,
                "Mr. Nothing authority trust",
                "Device credential required",
                "Confirm this offline authority trust change. No device action will be enabled."
            )
        } catch (_: IllegalArgumentException) {
            cancelPending(false)
            status.text = "Credential-only system prompt unavailable. Refused."
            return
        }

        val cancellation = CancellationSignal()
        credentialCancellation = cancellation
        try {
            prompt.authenticate(
                cancellation,
                mainExecutor,
                object : BiometricPrompt.AuthenticationCallback() {
                    override fun onAuthenticationSucceeded(
                        result: BiometricPrompt.AuthenticationResult
                    ) {
                        val credentialOnly =
                            OwnerCredentialAuthenticationPolicy.acceptsDeviceCredential(
                                Build.VERSION.SDK_INT,
                                result.authenticationType,
                                BiometricPrompt.AUTHENTICATION_RESULT_TYPE_DEVICE_CREDENTIAL
                            )
                        completeCredentialConfirmation(binding, credentialOnly)
                    }

                    override fun onAuthenticationError(
                        errorCode: Int,
                        errString: CharSequence
                    ) {
                        completeCredentialConfirmation(binding, credentialApproved = false)
                    }

                    override fun onAuthenticationFailed() {
                        if (pendingBinding == binding &&
                            activeOperationToken == token &&
                            operationGate.isActive(token)
                        ) {
                            status.text =
                                "Device credential was not accepted. No trust change made."
                        }
                    }
                }
            )
        } catch (_: IllegalArgumentException) {
            cancelPending(false)
            status.text = "Credential-only system prompt rejected. Refused."
        } catch (_: SecurityException) {
            cancelPending(false)
            status.text = "Credential-only system prompt denied. Refused."
        }
    }

    private fun completeCredentialConfirmation(
        expectedBinding: String,
        credentialApproved: Boolean
    ) {
        val token = activeOperationToken ?: return
        if (!operationGate.isActive(token) || pendingBinding != expectedBinding) return
        credentialCancellation = null
        pendingBinding = null

        val credentialResultAccepted = credentialApproved &&
            independentFingerprintConfirmed.isChecked &&
            OwnerCredentialSafetyGate.isSafe(this)
        if (!confirmation.finish(expectedBinding, credentialResultAccepted)) {
            finishOperation(token)
            setFormEnabled(true)
            status.text =
                "Device credential canceled, expired, mismatched or unsafe. No trust change made."
            return
        }

        val parsed = parseInput()
        if (parsed == null) {
            finishOperation(token)
            setFormEnabled(true)
            return
        }

        setFormEnabled(false)
        status.text = "Revalidating trust state before the authorized transaction..."
        val appContext = applicationContext
        OwnerAuthorityIoCoordinator.execute {
            var committed: AuthorityTrustStoreCommit? = null
            var failureMessage: String? = null
            var refreshAfter = false
            try {
                if (!operationGate.isActive(token)) return@execute
                val trustStore = createTrustStore(appContext)
                val current = trustStore.inspect()
                if (!operationGate.isActive(token)) return@execute
                val snapshot = storeSnapshot(current)
                val mode = modeForState(current)
                if (snapshot == null || mode == null) {
                    failureMessage = "Trust state changed or became unavailable. No change made."
                    refreshAfter = true
                } else {
                    val actualBinding = AuthorityTrustImportParser.confirmationBinding(
                        mode, snapshot, parsed.inputBinding
                    )
                    if (actualBinding != expectedBinding) {
                        failureMessage =
                            "Trust state or imported material changed during credential prompt. Refused."
                        refreshAfter = true
                    } else {
                        val decision = prepareDecision(current, parsed, ownerConfirmation = true)
                        if (decision !is AuthorityTrustDecision.Ready) {
                            failureMessage =
                                "Trust transition refused after credential confirmation: " +
                                    decisionDescription(decision)
                        } else if (!OwnerCredentialSafetyGate.isSafe(appContext)) {
                            failureMessage =
                                "Device became unsafe before the trust transaction. No change made."
                        } else if (!operationGate.claimCommit(token)) {
                            failureMessage =
                                "Trust transaction canceled before its commit boundary. No change made."
                        } else {
                            // Claiming this boundary means the already-authorized atomic transaction
                            // has started. Cancellation/destruction before the claim suppresses commit.
                            committed = trustStore.commit(decision)
                            refreshAfter = true
                        }
                    }
                }
            } catch (_: RuntimeException) {
                failureMessage = "Trust-store operation failed. No success reported."
                refreshAfter = true
            }

            mainHandler.post {
                if (!operationGate.isDeliverable(token) || isFinishing || isDestroyed) {
                    finishOperation(token)
                    return@post
                }
                finishOperation(token)
                setFormEnabled(true)
                independentFingerprintConfirmed.isChecked = false
                status.text = when (val result = committed) {
                    is AuthorityTrustStoreCommit.Committed ->
                        "Authority trust committed at generation " +
                            result.record.generation +
                            ". No enrollment or agent access was enabled."
                    is AuthorityTrustStoreCommit.Refused ->
                        "Trust-store transition refused: " + result.reason.name
                    is AuthorityTrustStoreCommit.Failed ->
                        "Trust-store transaction failed: " + result.reason.name +
                            ". Inspect recovery state before retrying."
                    null -> failureMessage ?: "Trust transaction did not complete. No success reported."
                }
                if (refreshAfter) refreshTrustState()
            }
        }
    }

    private fun finishOperation(token: Long) {
        operationGate.finish(token)
        if (activeOperationToken == token) activeOperationToken = null
    }

    private fun prepareDecision(
        state: AuthorityTrustStoreState,
        parsed: ParsedAuthorityTrustImport,
        ownerConfirmation: Boolean
    ): AuthorityTrustDecision = when (state) {
        AuthorityTrustStoreState.Empty -> {
            if (parsed.rotationSignature.isNotEmpty()) {
                AuthorityTrustDecision.Blocked(AuthorityTrustBlockReason.INVALID_CANDIDATE)
            } else {
                OwnerAuthorityTrustCeremony.prepareFirstInstall(
                    parsed.candidate,
                    parsed.independentlyObservedFingerprint,
                    ownerConfirmation,
                    highestObservedGeneration = 0L
                )
            }
        }
        is AuthorityTrustStoreState.Active -> {
            OwnerAuthorityTrustCeremony.prepareRotation(
                state.record,
                parsed.candidate,
                parsed.rotationSignature,
                parsed.independentlyObservedFingerprint,
                ownerConfirmation,
                highestObservedGeneration = state.record.generation
            )
        }
        is AuthorityTrustStoreState.RecoveryRequired -> {
            if (parsed.rotationSignature.isNotEmpty()) {
                AuthorityTrustDecision.Blocked(
                    AuthorityTrustBlockReason.RECOVERY_NOT_ELIGIBLE
                )
            } else {
                OwnerAuthorityTrustCeremony.prepareRecovery(
                    parsed.candidate,
                    parsed.independentlyObservedFingerprint,
                    ownerConfirmation,
                    highestObservedGeneration = state.highestObservedGeneration,
                    activeRecordPresent = false
                )
            }
        }
        AuthorityTrustStoreState.Unavailable ->
            AuthorityTrustDecision.Blocked(AuthorityTrustBlockReason.INVALID_ACTIVE_RECORD)
        is AuthorityTrustStoreState.Corrupt ->
            AuthorityTrustDecision.Blocked(AuthorityTrustBlockReason.INVALID_ACTIVE_RECORD)
    }

    private fun storeSnapshot(state: AuthorityTrustStoreState): String? = when (state) {
        AuthorityTrustStoreState.Empty -> "EMPTY"
        is AuthorityTrustStoreState.Active ->
            "ACTIVE|" + state.record.generation + "|" + state.record.keyId + "|" +
                state.record.fingerprint + "|" +
                AuthorityTrustImportParser.sha256Hex(state.record.publicKeySpkiDer)
        is AuthorityTrustStoreState.RecoveryRequired ->
            "RECOVERY|" + state.highestObservedGeneration + "|" + state.reason.name
        AuthorityTrustStoreState.Unavailable -> null
        is AuthorityTrustStoreState.Corrupt -> null
    }

    private fun modeForState(state: AuthorityTrustStoreState): AuthorityTrustMode? =
        when (state) {
            AuthorityTrustStoreState.Empty -> AuthorityTrustMode.FIRST_INSTALL
            is AuthorityTrustStoreState.Active -> AuthorityTrustMode.ROTATION
            is AuthorityTrustStoreState.RecoveryRequired -> AuthorityTrustMode.RECOVERY
            else -> null
        }

    private fun decisionDescription(decision: AuthorityTrustDecision): String =
        when (decision) {
            is AuthorityTrustDecision.Blocked -> decision.reason.name
            is AuthorityTrustDecision.Ready -> "READY"
        }

    private fun refreshTrustState() {
        if (!::trustState.isInitialized || isFinishing || isDestroyed) return
        trustStateLoaded = false
        confirmButton.isEnabled = false
        trustState.text = "Trust state: checking..."
        val token = operationGate.begin() ?: return
        val appContext = applicationContext
        OwnerAuthorityIoCoordinator.execute {
            if (!operationGate.isActive(token)) return@execute
            val current = try {
                createTrustStore(appContext).inspect()
            } catch (_: RuntimeException) {
                AuthorityTrustStoreState.Unavailable
            }
            mainHandler.post {
                if (!operationGate.isActive(token) || isFinishing || isDestroyed) {
                    operationGate.finish(token)
                    return@post
                }
                renderTrustState(current)
                trustStateLoaded = true
                operationGate.finish(token)
                confirmButton.isEnabled =
                    current !== AuthorityTrustStoreState.Unavailable &&
                    current !is AuthorityTrustStoreState.Corrupt
            }
        }
    }

    private fun renderTrustState(current: AuthorityTrustStoreState) {
        trustState.text = when (current) {
            AuthorityTrustStoreState.Empty ->
                "Trust state: empty. First install requires generation 1."
            is AuthorityTrustStoreState.Active ->
                "Trust state: active generation " + current.record.generation +
                    " · " + current.record.fingerprint +
                    ". Rotation requires a signature from this current authority."
            is AuthorityTrustStoreState.RecoveryRequired ->
                "Trust state: recovery required at watermark " +
                    current.highestObservedGeneration + " · " + current.reason.name +
                    ". Recovery must advance exactly one generation."
            AuthorityTrustStoreState.Unavailable ->
                "Trust state: unavailable. All mutations are refused."
            is AuthorityTrustStoreState.Corrupt ->
                "Trust state: corrupt · " + current.reason.name +
                    ". All mutations are refused."
        }
    }

    private fun setFormEnabled(enabled: Boolean) {
        keyIdField.isEnabled = enabled
        generationField.isEnabled = enabled
        spkiField.isEnabled = enabled
        rotationSignatureField.isEnabled = enabled
        fingerprintField.isEnabled = enabled
        independentFingerprintConfirmed.isEnabled = enabled
        previewButton.isEnabled = enabled
        confirmButton.isEnabled = enabled
    }

    private fun cancelPending(clearImport: Boolean): Boolean {
        val token = activeOperationToken
        if (token != null && operationGate.isCommitClaimed(token)) {
            status.text =
                "The authorized trust transaction has started and cannot be canceled safely. Wait for completion."
            return false
        }
        if (token != null) {
            operationGate.cancel(token)
            activeOperationToken = null
        }
        val activeCancellation = credentialCancellation
        credentialCancellation = null
        confirmation.revoke()
        pendingBinding = null
        // Revoke the operation and one-shot binding before cancel(), which may dispatch a callback.
        activeCancellation?.cancel()
        if (::keyIdField.isInitialized) setFormEnabled(true)
        if (clearImport && ::keyIdField.isInitialized) {
            keyIdField.text.clear()
            generationField.text.clear()
            spkiField.text.clear()
            rotationSignatureField.text.clear()
            fingerprintField.text.clear()
            independentFingerprintConfirmed.isChecked = false
            fingerprintStatus.text = ""
        }
        return true
    }

    override fun onDestroy() {
        // Pending/queued operations are invalidated. A transaction already claimed
        // after credential and safety revalidation is allowed to finish atomically;
        // its UI callback is suppressed after destruction.
        operationGate.destroy()
        activeOperationToken = null
        val activeCancellation = credentialCancellation
        credentialCancellation = null
        confirmation.revoke()
        pendingBinding = null
        activeCancellation?.cancel()
        super.onDestroy()
    }
}
