package tech.mrnothing.os

import android.app.Activity
import android.app.Application
import android.content.Intent
import android.os.Bundle
import android.os.ParcelFileDescriptor
import android.os.SystemClock
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
            // to AndroidKeyStore, which requires a KeyGenParameterSpec.
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
            shell("input keyevent 66")

            val boundaryReached = if (destroyAfterClaim) fakeStore.commitEntered else fakeStore.finalInspectEntered
            assertTrue(
                "authorized transaction did not reach the expected lifecycle boundary",
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

    private fun awaitCredentialPrompt(activity: OwnerAuthorityTrustActivityTestHost) {
        awaitMainCondition("credential confirmation was not initiated") {
            privateField(activity, "pendingBinding") != null
        }
        val deadline = SystemClock.elapsedRealtime() + 12_000L
        while (SystemClock.elapsedRealtime() < deadline) {
            val root = getInstrumentation().uiAutomation.rootInActiveWindow
            if (root != null) {
                val isSystemUi = root.packageName?.toString() == "com.android.systemui"
                val matches = try {
                    root.findAccessibilityNodeInfosByViewId(
                        "com.android.systemui:id/lockPassword"
                    )
                } catch (_: RuntimeException) {
                    emptyList()
                }
                val visible = isSystemUi && matches.isNotEmpty()
                matches.forEach { it.recycle() }
                root.recycle()
                if (visible) return
            }
            SystemClock.sleep(100)
        }
        fail("credential-only SystemUI prompt did not become visible")
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
