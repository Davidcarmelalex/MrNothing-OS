package tech.mrnothing.os

import android.app.Activity
import android.app.Application
import android.app.KeyguardManager
import android.content.Context
import android.content.Intent
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
            // the synthetic test PIN through the visible SystemUI PIN field.
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
            shell("input text $TEST_PIN")
            shell("input keyevent KEYCODE_ENTER")
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
            // A wake event exposes the lockscreen; it does not necessarily
            // reveal the PIN pad. Use a normal swipe-up gesture only when the
            // exact system-owned credential field is not already visible.
            if (!hasVisibleSystemCredentialInput()) {
                swipeUpToRevealSystemCredentialEntry()
            }
            awaitSystemCredentialUi("locked emulator did not expose the SystemUI PIN field")
            // Enter the synthetic PIN only after the exact SystemUI field
            // and its expected Android view class have been observed.
            shell("input text $TEST_PIN")
            shell("input keyevent KEYCODE_ENTER")
        }

        val deadline = SystemClock.elapsedRealtime() + 10_000L
        while (SystemClock.elapsedRealtime() < deadline) {
            if (OwnerCredentialSafetyGate.isSafe(context)) return
            SystemClock.sleep(50)
        }
        fail("emulator is not secure, unlocked and interactive: ${safetySnapshot(context)}")
    }

    /**
     * Reveal the secure lockscreen's system-owned credential entry surface.
     *
     * Use Android's ordinary input utility from the unprivileged shell identity
     * already required by QA-005. This is a swipe gesture only; it cannot
     * authenticate or dismiss a secure Keyguard. The caller still requires an
     * exact visible SystemUI credential resource-ID/class match before PIN entry.
     */
    private fun swipeUpToRevealSystemCredentialEntry() {
        val metrics = getInstrumentation().targetContext.resources.displayMetrics
        val width = metrics.widthPixels
        val height = metrics.heightPixels
        assertTrue("emulator display metrics are unavailable", width > 0 && height > 0)

        val centerX = width / 2
        val startY = (height * 0.82f).toInt()
        val endY = (height * 0.28f).toInt()
        val identity = shell("id")
        assertTrue(
            "keyguard gesture requires ordinary adb shell identity; refusing privileged execution",
            identity.contains("uid=2000(shell)")
        )

        val result = shell("input swipe $centerX $startY $centerX $endY 300")
        assertFalse(
            "Android input utility rejected the keyguard swipe: $result",
            result.contains("usage", ignoreCase = true) ||
                result.contains("error", ignoreCase = true)
        )
        SystemClock.sleep(250)
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
        awaitSystemCredentialUi(
            "credential-only SystemUI prompt did not become visible; " +
                "status='$status'; " + safetySnapshot(activity)
        )
    }

    private fun awaitSystemCredentialUi(message: String) {
        val deadline = SystemClock.elapsedRealtime() + 12_000L
        while (SystemClock.elapsedRealtime() < deadline) {
            if (hasVisibleSystemCredentialInput()) return
            SystemClock.sleep(100)
        }
        fail(
            "$message; ${safetySnapshot(getInstrumentation().targetContext)}; " +
                "visibleSystemCredentialInput=${hasVisibleSystemCredentialInput()}"
        )
    }

    /**
     * BiometricPrompt credential UI differs across Android releases and can be
     * hosted in more than the active window. Inspect all accessible windows,
     * but accept an input field only from the system credential packages and
     * known credential-input resource IDs. Never type into an app-owned field.
     */
    private fun hasVisibleSystemCredentialInput(): Boolean {
        val automation = getInstrumentation().uiAutomation
        val roots = try {
            automation.windows.mapNotNull { it.root }.toMutableList()
        } catch (_: RuntimeException) {
            mutableListOf()
        }
        if (roots.isEmpty()) {
            automation.rootInActiveWindow?.let(roots::add)
        }

        val allowedPackages = setOf("com.android.systemui", "com.android.settings")
        // Android 15 AOSP's PIN screen exposes pinEntry as a custom
        // PasswordTextView, not an EditText. Its password screen uses
        // passwordEntry as an EditText. Keep exact ID/class pairs so a
        // generic or app-owned text field can never authorize PIN entry.
        val credentialInputSelectors = listOf(
            "com.android.systemui:id/auth_credential_input" to "android.widget.EditText",
            "com.android.systemui:id/lockPassword" to "android.widget.EditText",
            "com.android.systemui:id/pinEntry" to "com.android.keyguard.PasswordTextView",
            "com.android.systemui:id/passwordEntry" to "android.widget.EditText"
        )
        try {
            for (root in roots) {
                if (root.packageName?.toString() !in allowedPackages) continue
                for ((viewId, expectedClassName) in credentialInputSelectors) {
                    val matches = try {
                        root.findAccessibilityNodeInfosByViewId(viewId)
                    } catch (_: RuntimeException) {
                        emptyList()
                    }
                    try {
                        if (matches.any {
                                it.isVisibleToUser &&
                                    it.className?.toString() == expectedClassName
                            }
                        ) return true
                    } finally {
                        matches.forEach { it.recycle() }
                    }
                }
            }
        } finally {
            roots.forEach { it.recycle() }
        }
        return false
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
                safetySnapshot(activity)
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
