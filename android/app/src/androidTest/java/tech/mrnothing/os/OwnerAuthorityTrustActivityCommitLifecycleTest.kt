package tech.mrnothing.os

import android.app.Activity
import android.app.Application
import android.app.KeyguardManager
import android.content.Context
import android.content.Intent
import android.graphics.Rect
import android.hardware.biometrics.BiometricManager
import android.os.Bundle
import android.os.ParcelFileDescriptor
import android.os.PowerManager
import android.os.SystemClock
import android.os.UserManager
import android.test.InstrumentationTestCase
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.TextView
import android.view.accessibility.AccessibilityNodeInfo
import java.util.Base64
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/**
 * SEC-020B4D: exercises the real owner-trust Activity around its commit claim.
 *
 * The test host uses an in-memory fake store. The QA-005 workflow provisions
 * and clears a synthetic emulator PIN around this instrumentation task so the
 * production credential-only prompt and callback run without a real user credential.
 */
class OwnerAuthorityTrustActivityCommitLifecycleTest : InstrumentationTestCase() {
    private var lastCredentialPreflightDiagnostics = "not-started"
    private var lastCredentialEntryDiagnostics = "not-started"

    fun testDestroyBeforeCommitClaimPreventsFakeStoreMutation() {
        runScenario(destroyAfterClaim = false)
    }

    fun testDestroyAfterCommitClaimAllowsAtomicFakeCommitButSuppressesUiDelivery() {
        runScenario(destroyAfterClaim = true)
    }

    private fun runScenario(destroyAfterClaim: Boolean) {
        val fakeStore = BlockingFakeTrustStore(
            blockInspectCall = if (destroyAfterClaim) null else 3,
            blockCommit = destroyAfterClaim
        )
        OwnerAuthorityTrustTestBackend.store = fakeStore

        var activity: OwnerAuthorityTrustActivityTestHost? = null
        var application: Application? = null
        var lifecycleCallbacks: Application.ActivityLifecycleCallbacks? = null

        try {
            // A headless emulator may be non-interactive after boot. Wake it and,
            // only if the disposable emulator is actually keyguard-locked, enter
            // the synthetic test PIN through the visible SystemUI credential surface.
            // Never dismiss/bypass Keyguard or type into an app-owned field.
            prepareInteractiveUnlockedEmulator()

            val intent = Intent(
                getInstrumentation().targetContext,
                OwnerAuthorityTrustActivityTestHost::class.java
            ).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            activity = getInstrumentation().startActivitySync(intent)
                as OwnerAuthorityTrustActivityTestHost
            val target = activity!!

            awaitMainCondition("initial fake trust state was not loaded") {
                (privateField(target, "confirmButton") as Button).isEnabled
            }

            // RFC 8032 test vector 1 public key (public material only). Avoid
            // provider-default key generation: Android may route Ed25519 generation
            // to AndroidKeyStore and require provider-specific initialization.
            val spki = Base64.getDecoder().decode(
                "MCowBQYDK2VwAyEA11qYAYKxCrfVS/7TyWQHOg7hcvPapiMlrwIaaPcHURo="
            )
            val fingerprint = OwnerAuthorityTrustCeremony.fingerprintForOwner(spki)
                ?: throw AssertionError("synthetic Ed25519 fingerprint unavailable")

            getInstrumentation().runOnMainSync {
                (privateField(target, "keyIdField") as EditText).setText("sec020b4d-test-authority")
                (privateField(target, "generationField") as EditText).setText("1")
                (privateField(target, "spkiField") as EditText)
                    .setText(Base64.getEncoder().encodeToString(spki))
                (privateField(target, "rotationSignatureField") as EditText).setText("")
                (privateField(target, "fingerprintField") as EditText).setText(fingerprint)
                (privateField(target, "independentFingerprintConfirmed") as CheckBox).isChecked = true
                (privateField(target, "confirmButton") as Button).performClick()
            }

            awaitCredentialPrompt(target)
            enterSyntheticBiometricPromptPin()
            awaitCredentialRevalidation(target)

            val boundaryReached = if (destroyAfterClaim) fakeStore.commitEntered else fakeStore.finalInspectEntered
            assertTrue(
                "authorized transaction did not reach the expected lifecycle boundary; " +
                    "status='${activityStatus(target)}'; " +
                    "commitEntered=${fakeStore.commitEntered.count}; " +
                    "finalInspectEntered=${fakeStore.finalInspectEntered.count}",
                boundaryReached.await(12, TimeUnit.SECONDS)
            )

            val gate = privateField(target, "operationGate") as OwnerAuthorityOperationGate
            val token = privateField(target, "activeOperationToken") as? Long
                ?: throw AssertionError("Activity operation token missing at boundary")
            val statusView = privateField(target, "status") as TextView
            val statusBeforeDestroy = statusView.text.toString()
            assertTrue(statusBeforeDestroy.startsWith("Revalidating trust state"))

            application = getInstrumentation().targetContext.applicationContext as Application
            val destroyed = CountDownLatch(1)
            val observer = object : Application.ActivityLifecycleCallbacks {
                override fun onActivityCreated(activity: Activity, state: Bundle?) = Unit
                override fun onActivityStarted(activity: Activity) = Unit
                override fun onActivityResumed(activity: Activity) = Unit
                override fun onActivityPaused(activity: Activity) = Unit
                override fun onActivityStopped(activity: Activity) = Unit
                override fun onActivitySaveInstanceState(activity: Activity, state: Bundle) = Unit
                override fun onActivityDestroyed(activity: Activity) {
                    if (activity === target) destroyed.countDown()
                }
            }
            lifecycleCallbacks = observer
            application!!.registerActivityLifecycleCallbacks(observer)

            getInstrumentation().runOnMainSync { target.finish() }
            assertTrue(
                "Activity onDestroy callback was not observed",
                destroyed.await(5, TimeUnit.SECONDS)
            )
            assertTrue("Activity did not reach destroyed state", target.isDestroyed)
            assertFalse("destroyed Activity must suppress transaction UI delivery", gate.isDeliverable(token))

            if (destroyAfterClaim) {
                assertTrue(
                    "commit claim must remain non-cancelable while fake atomic commit is blocked",
                    gate.isCommitClaimed(token)
                )
            } else {
                assertFalse("destroyed Activity must invalidate pre-claim work", gate.isActive(token))
            }

            fakeStore.releaseBoundary()
            val queueDrained = CountDownLatch(1)
            OwnerAuthorityIoCoordinator.execute { queueDrained.countDown() }
            assertTrue("trust I/O worker did not drain after boundary release",
                queueDrained.await(10, TimeUnit.SECONDS))
            getInstrumentation().waitForIdleSync()

            if (destroyAfterClaim) {
                assertEquals("claimed transaction must finish exactly once", 1, fakeStore.commitCount.get())
                assertTrue("fake atomic commit should complete after claim",
                    fakeStore.currentState is AuthorityTrustStoreState.Active)
                assertFalse("completed commit token should be retired", gate.isCommitClaimed(token))
            } else {
                assertEquals("pre-claim destruction must prevent commit", 0, fakeStore.commitCount.get())
                assertSame(AuthorityTrustStoreState.Empty, fakeStore.currentState)
            }
            assertEquals(
                "destroyed Activity must not receive a late trust-store result",
                statusBeforeDestroy,
                statusView.text.toString()
            )
        } finally {
            fakeStore.releaseBoundary()
            val current = activity
            if (current != null && !current.isDestroyed) {
                getInstrumentation().runOnMainSync { current.finish() }
            }
            if (application != null && lifecycleCallbacks != null) {
                application!!.unregisterActivityLifecycleCallbacks(lifecycleCallbacks!!)
            }
            OwnerAuthorityTrustTestBackend.store = null
        }
    }

    private fun prepareInteractiveUnlockedEmulator() {
        val context = getInstrumentation().targetContext
        val keyguard = context.getSystemService(KeyguardManager::class.java)
            ?: throw AssertionError("KeyguardManager unavailable")
        assertTrue(
            "synthetic test PIN was not configured on the disposable emulator",
            keyguard.isDeviceSecure
        )

        shell("input keyevent KEYCODE_WAKEUP")
        SystemClock.sleep(250)
        if (keyguard.isDeviceLocked || keyguard.isKeyguardLocked) {
            // This is the device lockscreen, not the later BiometricPrompt dialog.
            // Click the exact SystemUI device-entry affordance and verify the complete PIN pad before input.
            if (!hasVisibleKeyguardPinPad()) {
                lastCredentialPreflightDiagnostics = clickSystemDeviceEntryIconToRevealCredentialEntry()
            } else {
                lastCredentialPreflightDiagnostics = "exact SystemUI Keyguard PIN pad was already visible"
            }
            awaitKeyguardPinPad("locked emulator did not expose the complete SystemUI Keyguard PIN pad")
            val identity = shell("id")
            assertTrue(
                "synthetic PIN entry requires ordinary adb shell identity; refusing privileged execution",
                identity.contains("uid=2000(shell)")
            )
            lastCredentialPreflightDiagnostics += "; synthetic-pin-entry-identity=" + identity.trim()
            enterSyntheticKeyguardPin(identity)
        }

        val deadline = SystemClock.elapsedRealtime() + 10_000L
        while (SystemClock.elapsedRealtime() < deadline) {
            if (OwnerCredentialSafetyGate.isSafe(context)) return
            SystemClock.sleep(50)
        }
        fail("emulator is not secure, unlocked and interactive: ${safetySnapshot(context)}")
    }

    /**
     * Unlock only the disposable emulator's actual Keyguard PIN pad. Each digit
     * is sent as a bounded tap to an exact visible SystemUI resource-ID control.
     */
    private fun enterSyntheticKeyguardPin(identityFromCaller: String? = null) {
        val identity = identityFromCaller ?: shell("id")
        assertTrue(
            "synthetic PIN entry requires ordinary adb shell identity; refusing privileged execution",
            identity.contains("uid=2000(shell)")
        )
        assertTrue("exact SystemUI Keyguard PIN pad is not visible", hasVisibleKeyguardPinPad())
        SystemClock.sleep(250)
        var tappedDigits = 0
        for (digit in TEST_PIN) {
            val viewId = "com.android.systemui:id/key$digit"
            assertTrue(
                "exact clickable SystemUI Keyguard PIN key was not available: key$digit",
                tapVisibleSystemUiNode(viewId)
            )
            tappedDigits += 1
            SystemClock.sleep(120)
        }
        assertTrue(
            "exact clickable SystemUI Keyguard PIN submit key was not available",
            tapVisibleSystemUiNode("com.android.systemui:id/key_enter")
        )
        lastCredentialPreflightDiagnostics += "; keyguardDigitKeysTapped=$tappedDigits; submitKeyTapped=true"
        SystemClock.sleep(250)
    }

    /**
     * Enter the workflow's synthetic PIN only into Android 15 BiometricPrompt's
     * focused SystemUI ImeAwareEditText. This is ordinary input to the visible
     * platform credential field, not a Keyguard or BiometricPrompt bypass.
     */
    private fun enterSyntheticBiometricPromptPin(identityFromCaller: String? = null) {
        lastCredentialEntryDiagnostics = "starting"
        val identity = identityFromCaller ?: shell("id")
        assertTrue(
            "synthetic PIN entry requires ordinary adb shell identity; refusing privileged execution",
            identity.contains("uid=2000(shell)")
        )
        assertTrue(
            "focused SystemUI BiometricPrompt credential field is not visible",
            hasVisibleBiometricPromptCredentialField()
        )

        val textResult = shell("input text $TEST_PIN")
        assertFalse(
            "Android input utility rejected the SystemUI credential-field text input",
            textResult.contains("usage", ignoreCase = true) ||
                textResult.contains("error", ignoreCase = true)
        )
        val submitResult = shell("input keyevent KEYCODE_ENTER")
        assertFalse(
            "Android input utility rejected the SystemUI credential-field submit key",
            submitResult.contains("usage", ignoreCase = true) ||
                submitResult.contains("error", ignoreCase = true)
        )
        // Deliberately omit the synthetic PIN value from diagnostics and artifacts.
        lastCredentialEntryDiagnostics =
            "focusedSystemUiImeField=true; syntheticPinInputSent=true; submitKeyEventSent=true"
        SystemClock.sleep(250)
    }

    private fun tapVisibleSystemUiNode(viewId: String): Boolean {
        val allowedViewIds = (0..9).map { "com.android.systemui:id/key$it" } +
            "com.android.systemui:id/key_enter"
        if (viewId !in allowedViewIds) return false

        val automation = getInstrumentation().uiAutomation
        val roots = try {
            automation.windows.mapNotNull { it.root }.toMutableList()
        } catch (_: RuntimeException) {
            mutableListOf()
        }
        if (roots.isEmpty()) automation.rootInActiveWindow?.let(roots::add)

        val pinViewId = "com.android.systemui:id/keyguard_pin_view"
        val containerId = "com.android.systemui:id/pin_container"
        val metrics = getInstrumentation().targetContext.resources.displayMetrics
        if (metrics.widthPixels <= 0 || metrics.heightPixels <= 0) {
            roots.forEach { it.recycle() }
            return false
        }

        try {
            for (root in roots) {
                if (root.packageName?.toString() != "com.android.systemui") continue
                val pinViews = try {
                    root.findAccessibilityNodeInfosByViewId(pinViewId)
                } catch (_: RuntimeException) {
                    emptyList()
                }
                try {
                    for (pinView in pinViews) {
                        if (pinView.viewIdResourceName != pinViewId ||
                            !pinView.isVisibleToUser || !pinView.isEnabled
                        ) continue
                        val containers = try {
                            pinView.findAccessibilityNodeInfosByViewId(containerId)
                        } catch (_: RuntimeException) {
                            emptyList()
                        }
                        try {
                            for (container in containers) {
                                if (container.viewIdResourceName != containerId ||
                                    !container.isVisibleToUser || !container.isEnabled
                                ) continue
                                val matches = try {
                                    container.findAccessibilityNodeInfosByViewId(viewId)
                                } catch (_: RuntimeException) {
                                    emptyList()
                                }
                                try {
                                    for (node in matches) {
                                        if (node.packageName?.toString() != "com.android.systemui" ||
                                            node.viewIdResourceName != viewId ||
                                            !node.isVisibleToUser ||
                                            !node.isEnabled ||
                                            !node.isClickable
                                        ) continue
                                        val bounds = Rect()
                                        node.getBoundsInScreen(bounds)
                                        if (bounds.width() <= 0 || bounds.height() <= 0 ||
                                            bounds.left < 0 || bounds.top < 0 ||
                                            bounds.right > metrics.widthPixels ||
                                            bounds.bottom > metrics.heightPixels
                                        ) continue
                                        val output = shell(
                                            "input tap ${bounds.centerX()} ${bounds.centerY()}"
                                        )
                                        return !output.contains("usage", ignoreCase = true) &&
                                            !output.contains("error", ignoreCase = true)
                                    }
                                } finally {
                                    matches.forEach { it.recycle() }
                                }
                            }
                        } finally {
                            containers.forEach { it.recycle() }
                        }
                    }
                } finally {
                    pinViews.forEach { it.recycle() }
                }
            }
        } finally {
            roots.forEach { it.recycle() }
        }
        return false
    }

    /**
     * Fallback used only when the Keyguard PIN bouncer is not already visible.
     * It invokes ACTION_CLICK only on the exact visible, long-clickable
     * SystemUI device-entry node with screen-bounded accessibility bounds.
     */
    private fun clickSystemDeviceEntryIconToRevealCredentialEntry(): String {
        val metrics = getInstrumentation().targetContext.resources.displayMetrics
        val width = metrics.widthPixels
        val height = metrics.heightPixels
        assertTrue("emulator display metrics are unavailable", width > 0 && height > 0)

        val identity = shell("id")
        assertTrue(
            "keyguard entry click requires ordinary adb shell identity; refusing privileged execution",
            identity.contains("uid=2000(shell)")
        )

        val automation = getInstrumentation().uiAutomation
        val viewId = "com.android.systemui:id/device_entry_icon_view"
        val targetBounds = Rect()
        var targetFound = false
        var clickAccepted = false
        var observedMatches = "no matching resource ID observed"
        var attempts = 0
        val deadline = SystemClock.elapsedRealtime() + 5_000L

        // SystemUI can publish its post-wake accessibility tree after the display
        // becomes interactive. Retry only the exact resource lookup; never guess coordinates.
        while (!targetFound && SystemClock.elapsedRealtime() < deadline) {
            attempts += 1
            val roots = try {
                automation.windows.mapNotNull { it.root }.toMutableList()
            } catch (_: RuntimeException) {
                mutableListOf()
            }
            if (roots.isEmpty()) {
                automation.rootInActiveWindow?.let(roots::add)
            }

            try {
                for (root in roots) {
                    if (root.packageName?.toString() != "com.android.systemui") continue
                    val matches = try {
                        root.findAccessibilityNodeInfosByViewId(viewId)
                    } catch (_: RuntimeException) {
                        emptyList()
                    }
                    try {
                        if (matches.isNotEmpty()) {
                            observedMatches = matches.take(4).joinToString(" | ") { node ->
                                val bounds = Rect()
                                node.getBoundsInScreen(bounds)
                                "class=${node.className}; visible=${node.isVisibleToUser}; " +
                                    "enabled=${node.isEnabled}; clickable=${node.isClickable}; " +
                                    "longClickable=${node.isLongClickable}; bounds=$bounds"
                            }
                        }
                        val target = matches.singleOrNull {
                            it.viewIdResourceName == viewId &&
                                it.className?.toString() == "android.widget.FrameLayout" &&
                                it.isVisibleToUser && it.isEnabled &&
                                it.isClickable
                        }
                        if (target != null) {
                            val bounds = Rect()
                            target.getBoundsInScreen(bounds)
                            if (bounds.width() > 0 && bounds.height() > 0 &&
                                bounds.left >= 0 && bounds.top >= 0 &&
                                bounds.right <= width && bounds.bottom <= height
                            ) {
                                targetBounds.set(bounds)
                                targetFound = true
                                clickAccepted = target.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                                break
                            }
                        }
                    } finally {
                        matches.forEach { it.recycle() }
                    }
                    if (targetFound) break
                }
            } finally {
                roots.forEach { it.recycle() }
            }

            if (!targetFound) SystemClock.sleep(100)
        }

        if (!targetFound) {
            fail(
                "one visible, clickable SystemUI device-entry icon was not found within 5 seconds; " +
                    "refusing coordinate guessing; attempts=$attempts; observedMatches=$observedMatches; " +
                    "ui=${credentialUiSnapshot()}"
            )
        }
        if (!clickAccepted) {
            fail(
                "SystemUI device-entry icon rejected ACTION_CLICK; target=$viewId " +
                    "bounds=$targetBounds; ui=${credentialUiSnapshot()}"
            )
        }
        SystemClock.sleep(250)
        return "identity=" + identity.trim() +
            "; target=$viewId class=android.widget.FrameLayout bounds=$targetBounds" +
            "; action=ACTION_CLICK accepted=true; attempts=$attempts"
    }

    private fun awaitCredentialPrompt(activity: OwnerAuthorityTrustActivityTestHost) {
        val deadline = SystemClock.elapsedRealtime() + 10_000L
        var status = ""
        var bindingPresent = false
        while (SystemClock.elapsedRealtime() < deadline) {
            getInstrumentation().runOnMainSync {
                bindingPresent = privateField(activity, "pendingBinding") != null
                status = (privateField(activity, "status") as TextView).text.toString()
            }
            if (bindingPresent) break
            SystemClock.sleep(50)
        }
        if (!bindingPresent) {
            fail(
                "credential confirmation was not initiated; status='$status'; " +
                    safetySnapshot(activity)
            )
        }
        awaitBiometricPromptCredentialField(
            "credential-only BiometricPrompt SystemUI input did not become visible; " +
                "status='$status'; " + safetySnapshot(activity)
        )
    }

    /**
     * Bounded read-only accessibility/window snapshot for diagnosing a missing
     * system credential surface. It records at most 96 nodes and 14 KB; every
     * AccessibilityNodeInfo acquired from UiAutomation is recycled.
     */
    private fun credentialUiSnapshot(): String {
        val automation = getInstrumentation().uiAutomation
        val windows = try {
            automation.windows
        } catch (error: RuntimeException) {
            return "windows-error=${error.javaClass.simpleName}"
        }
        val roots = windows.mapNotNull { it.root }.toMutableList()
        if (roots.isEmpty()) {
            automation.rootInActiveWindow?.let(roots::add)
        }

        val output = StringBuilder("windowCount=${windows.size}; rootCount=${roots.size}")
        var visited = 0
        for ((windowIndex, root) in roots.withIndex()) {
            val pending = java.util.ArrayDeque<Pair<AccessibilityNodeInfo, Int>>()
            pending.addLast(root to 0)
            while (pending.isNotEmpty() && visited < 96) {
                val (node, depth) = pending.removeFirst()
                output.append("\nwindow[").append(windowIndex).append("] ")
                    .append("  ".repeat(depth.coerceAtMost(8)))
                    .append(credentialNodeSummary(node, depth))
                visited += 1
                if (depth < 7) {
                    val childCount = try { node.childCount } catch (_: RuntimeException) { 0 }
                    for (index in 0 until childCount) {
                        val child = try { node.getChild(index) } catch (_: RuntimeException) { null }
                        if (child != null) pending.addLast(child to depth + 1)
                    }
                }
                node.recycle()
            }
            while (pending.isNotEmpty()) {
                pending.removeFirst().first.recycle()
            }
        }

        val focusSummary = try {
            shell("dumpsys window windows").lineSequence()
                .filter {
                    it.contains("mCurrentFocus", ignoreCase = true) ||
                        it.contains("mFocusedApp", ignoreCase = true) ||
                        it.contains("Keyguard", ignoreCase = true) ||
                        it.contains("StatusBar", ignoreCase = true)
                }
                .take(16)
                .joinToString(" | ")
        } catch (error: RuntimeException) {
            "window-dump-error=${error.javaClass.simpleName}"
        }
        output.append("\nwindowFocus=").append(focusSummary.take(1800))
        return output.toString().take(14_000)
    }

    /**
     * Emit structural SystemUI metadata without copying lockscreen text or
     * notification content into CI artifacts. Resource IDs and bounds let QA
     * distinguish a lockscreen surface from a credential-entry surface.
     */
    private fun credentialNodeSummary(node: AccessibilityNodeInfo, depth: Int): String {
        val bounds = Rect()
        node.getBoundsInScreen(bounds)
        val resourceId = try {
            node.viewIdResourceName ?: "-"
        } catch (_: RuntimeException) {
            "unavailable"
        }
        return "  ".repeat(depth.coerceAtMost(8)) +
            "id=" + resourceId +
            " class=" + (node.className?.toString() ?: "-") +
            " visible=" + node.isVisibleToUser +
            " enabled=" + node.isEnabled +
            " focusable=" + node.isFocusable +
            " focused=" + node.isFocused +
            " clickable=" + node.isClickable +
            " longClickable=" + node.isLongClickable +
            " password=" + node.isPassword +
            " children=" + node.childCount +
            " bounds=" + bounds
    }

    private fun awaitKeyguardPinPad(message: String) {
        val deadline = SystemClock.elapsedRealtime() + 12_000L
        while (SystemClock.elapsedRealtime() < deadline) {
            if (hasVisibleKeyguardPinPad()) return
            SystemClock.sleep(100)
        }
        fail(
            "$message; ${safetySnapshot(getInstrumentation().targetContext)}; " +
                "preflight=$lastCredentialPreflightDiagnostics; " +
                "visibleKeyguardPinPad=${hasVisibleKeyguardPinPad()}; " +
                "ui=${credentialUiSnapshot()}"
        )
    }

    private fun awaitBiometricPromptCredentialField(message: String) {
        val deadline = SystemClock.elapsedRealtime() + 12_000L
        while (SystemClock.elapsedRealtime() < deadline) {
            if (hasVisibleBiometricPromptCredentialField()) return
            SystemClock.sleep(100)
        }
        fail(
            "$message; ${safetySnapshot(getInstrumentation().targetContext)}; " +
                "preflight=$lastCredentialPreflightDiagnostics; " +
                "focusedBiometricPromptField=${hasVisibleBiometricPromptCredentialField()}; " +
                "ui=${credentialUiSnapshot()}"
        )
    }

    /**
     * Recognize the lockscreen PIN bouncer only. The full Keyguard PIN hierarchy
     * and all ten visible/clickable NumPadKey controls must share one SystemUI root.
     */
    private fun hasVisibleKeyguardPinPad(): Boolean {
        val automation = getInstrumentation().uiAutomation
        val roots = try {
            automation.windows.mapNotNull { it.root }.toMutableList()
        } catch (_: RuntimeException) {
            mutableListOf()
        }
        if (roots.isEmpty()) automation.rootInActiveWindow?.let(roots::add)
        try {
            return roots.any { root ->
                root.packageName?.toString() == "com.android.systemui" &&
                    hasVisibleSystemPinPad(root)
            }
        } finally {
            roots.forEach { it.recycle() }
        }
    }

    /**
     * Recognize the separate Android 15 BiometricPrompt credential form.
     * AOSP exposes auth_credential_input as a FrameLayout containing the focused
     * lockPassword field. The API 35 Google APIs emulator's accessibility tree
     * reports that exact SystemUI field as android.widget.EditText, while other
     * builds may expose android.widget.ImeAwareEditText. Accept only those two
     * exact classes under the SystemUI package, container and resource ID.
     * A Keyguard pinEntry behind this dialog is never accepted as this prompt.
     */
    private fun hasVisibleBiometricPromptCredentialField(): Boolean {
        val automation = getInstrumentation().uiAutomation
        val roots = try {
            automation.windows.mapNotNull { it.root }.toMutableList()
        } catch (_: RuntimeException) {
            mutableListOf()
        }
        if (roots.isEmpty()) automation.rootInActiveWindow?.let(roots::add)

        val containerId = "com.android.systemui:id/auth_credential_input"
        val fieldId = "com.android.systemui:id/lockPassword"
        try {
            for (root in roots) {
                if (root.packageName?.toString() != "com.android.systemui") continue
                val containers = try {
                    root.findAccessibilityNodeInfosByViewId(containerId)
                } catch (_: RuntimeException) {
                    emptyList()
                }
                try {
                    for (container in containers) {
                        if (container.viewIdResourceName != containerId ||
                            container.className?.toString() != "android.widget.FrameLayout" ||
                            !container.isVisibleToUser ||
                            !container.isEnabled
                        ) continue

                        val fields = try {
                            container.findAccessibilityNodeInfosByViewId(fieldId)
                        } catch (_: RuntimeException) {
                            emptyList()
                        }
                        try {
                            if (fields.any { field ->
                                    val fieldClass = field.className?.toString()
                                    if (field.viewIdResourceName != fieldId ||
                                        (fieldClass != "android.widget.ImeAwareEditText" &&
                                            fieldClass != "android.widget.EditText") ||
                                        !field.isVisibleToUser ||
                                        !field.isEnabled ||
                                        !field.isFocusable ||
                                        !field.isFocused ||
                                        !field.isPassword
                                    ) {
                                        false
                                    } else {
                                        val bounds = Rect()
                                        field.getBoundsInScreen(bounds)
                                        bounds.width() > 0 && bounds.height() > 0
                                    }
                                }
                            ) return true
                        } finally {
                            fields.forEach { it.recycle() }
                        }
                    }
                } finally {
                    containers.forEach { it.recycle() }
                }
            }
        } finally {
            roots.forEach { it.recycle() }
        }
        return false
    }

    private fun hasVisibleSystemPinPad(root: AccessibilityNodeInfo): Boolean {
        if (root.packageName?.toString() != "com.android.systemui") return false

        val pinViewId = "com.android.systemui:id/keyguard_pin_view"
        val containerId = "com.android.systemui:id/pin_container"
        val pinViews = try {
            root.findAccessibilityNodeInfosByViewId(pinViewId)
        } catch (_: RuntimeException) {
            emptyList()
        }
        try {
            for (pinView in pinViews) {
                if (pinView.viewIdResourceName != pinViewId ||
                    !pinView.isVisibleToUser || !pinView.isEnabled
                ) continue
                val containers = try {
                    pinView.findAccessibilityNodeInfosByViewId(containerId)
                } catch (_: RuntimeException) {
                    emptyList()
                }
                try {
                    for (container in containers) {
                        if (container.viewIdResourceName != containerId ||
                            !container.isVisibleToUser || !container.isEnabled
                        ) continue
                        // UIAutomator may report a platform View's superclass rather than
                        // its custom AOSP class. Exact SystemUI IDs and ancestor containment
                        // are the stable identity; visibility/clickability remain mandatory.
                        val controlIds = (0..9).map {
                            "com.android.systemui:id/key$it"
                        } + "com.android.systemui:id/key_enter"
                        if (controlIds.all { viewId ->
                                hasVisibleSystemUiNode(
                                    container,
                                    viewId,
                                    requireClickable = true
                                )
                            }
                        ) return true
                    }
                } finally {
                    containers.forEach { it.recycle() }
                }
            }
        } finally {
            pinViews.forEach { it.recycle() }
        }
        return false
    }

    private fun hasVisibleSystemUiNode(
        parent: AccessibilityNodeInfo,
        viewId: String,
        requireClickable: Boolean = false
    ): Boolean {
        val matches = try {
            parent.findAccessibilityNodeInfosByViewId(viewId)
        } catch (_: RuntimeException) {
            emptyList()
        }
        try {
            return matches.any { node ->
                if (node.packageName?.toString() != "com.android.systemui" ||
                    node.viewIdResourceName != viewId ||
                    !node.isVisibleToUser ||
                    !node.isEnabled ||
                    (requireClickable && !node.isClickable)
                ) {
                    false
                } else {
                    val bounds = Rect()
                    node.getBoundsInScreen(bounds)
                    bounds.width() > 0 && bounds.height() > 0
                }
            }
        } finally {
            matches.forEach { it.recycle() }
        }
    }

    private fun awaitCredentialRevalidation(activity: OwnerAuthorityTrustActivityTestHost) {
        val deadline = SystemClock.elapsedRealtime() + 10_000L
        var status = ""
        while (SystemClock.elapsedRealtime() < deadline) {
            getInstrumentation().runOnMainSync {
                status = (privateField(activity, "status") as TextView).text.toString()
            }
            if (status.startsWith("Revalidating trust state before the authorized transaction")) {
                return
            }
            if (status.startsWith("Device credential canceled") ||
                status.startsWith("Credential-only system prompt") ||
                status.startsWith("Device became unsafe")
            ) {
                break
            }
            SystemClock.sleep(50)
        }
        fail(
            "credential callback did not reach final trust revalidation; status='$status'; " +
                "pinEntry=$lastCredentialEntryDiagnostics; " + safetySnapshot(activity) +
                "; ui=${credentialUiSnapshot()}"
        )
    }

    private fun activityStatus(activity: OwnerAuthorityTrustActivityTestHost): String {
        var status = ""
        getInstrumentation().runOnMainSync {
            status = (privateField(activity, "status") as TextView).text.toString()
        }
        return status
    }

    private fun safetySnapshot(context: Context): String {
        val keyguard = context.getSystemService(KeyguardManager::class.java)
        val power = context.getSystemService(PowerManager::class.java)
        val user = context.getSystemService(UserManager::class.java)
        val biometric = context.getSystemService(BiometricManager::class.java)
        val canAuthenticate = biometric?.canAuthenticate(
            BiometricManager.Authenticators.DEVICE_CREDENTIAL
        ) ?: -1
        return "secure=${keyguard?.isDeviceSecure}, " +
            "deviceLocked=${keyguard?.isDeviceLocked}, " +
            "keyguardLocked=${keyguard?.isKeyguardLocked}, " +
            "userUnlocked=${user?.isUserUnlocked}, " +
            "interactive=${power?.isInteractive}, " +
            "deviceCredentialCanAuthenticate=$canAuthenticate"
    }

    private fun awaitMainCondition(message: String, condition: () -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + 10_000L
        while (SystemClock.elapsedRealtime() < deadline) {
            var satisfied = false
            getInstrumentation().runOnMainSync { satisfied = condition() }
            if (satisfied) return
            SystemClock.sleep(50)
        }
        fail(message)
    }

    private fun shell(command: String): String {
        val descriptor = getInstrumentation().uiAutomation.executeShellCommand(command)
        return ParcelFileDescriptor.AutoCloseInputStream(descriptor)
            .bufferedReader()
            .use { it.readText() }
    }

    private fun privateField(target: Any, name: String): Any? {
        var type: Class<*>? = target.javaClass
        while (type != null) {
            try {
                return type.getDeclaredField(name).apply { isAccessible = true }.get(target)
            } catch (_: NoSuchFieldException) {
                type = type.superclass
            }
        }
        throw NoSuchFieldException(name)
    }

    private class BlockingFakeTrustStore(
        private val blockInspectCall: Int?,
        private val blockCommit: Boolean
    ) : OwnerAuthorityTrustStorePort {
        private val inspectCount = AtomicInteger()
        val finalInspectEntered = CountDownLatch(1)
        val commitEntered = CountDownLatch(1)
        private val release = CountDownLatch(1)
        private val commits = AtomicInteger()

        @Volatile
        var currentState: AuthorityTrustStoreState = AuthorityTrustStoreState.Empty
            private set

        val commitCount: AtomicInteger
            get() = commits

        override fun inspect(): AuthorityTrustStoreState {
            val call = inspectCount.incrementAndGet()
            if (call == blockInspectCall) {
                finalInspectEntered.countDown()
                if (!release.await(15, TimeUnit.SECONDS)) {
                    throw IllegalStateException("fake final inspection release timed out")
                }
            }
            return currentState
        }

        override fun commit(
            proposal: AuthorityTrustDecision.Ready
        ): AuthorityTrustStoreCommit {
            commits.incrementAndGet()
            commitEntered.countDown()
            if (blockCommit && !release.await(15, TimeUnit.SECONDS)) {
                throw IllegalStateException("fake atomic commit release timed out")
            }
            currentState = AuthorityTrustStoreState.Active(proposal.record)
            return AuthorityTrustStoreCommit.Committed(proposal.record)
        }

        fun releaseBoundary() {
            release.countDown()
        }
    }

    private companion object {
        const val TEST_PIN = "2468"
    }
}
