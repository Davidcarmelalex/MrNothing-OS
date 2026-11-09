package tech.mrnothing.os

import android.app.Activity
import android.app.Application
import android.content.Intent
import android.os.Bundle
import android.test.InstrumentationTestCase
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/**
 * SEC-020B4C: exercises the real Activity destruction path while its initial
 * trust-store inspection is queued behind an occupied I/O worker.
 *
 * No credentials are entered and no trust-store mutation is attempted.
 */
class OwnerAuthorityTrustActivityLifecycleTest : InstrumentationTestCase() {
    fun testActivityDestructionInvalidatesQueuedTrustInspection() {
        val workerStarted = CountDownLatch(1)
        val releaseWorker = CountDownLatch(1)
        val queueDrained = CountDownLatch(1)
        var activity: OwnerAuthorityTrustActivity? = null

        OwnerAuthorityIoCoordinator.execute {
            workerStarted.countDown()
            if (!releaseWorker.await(10, TimeUnit.SECONDS)) {
                throw IllegalStateException("test worker release timed out")
            }
        }
        assertTrue("blocking I/O task did not start", workerStarted.await(5, TimeUnit.SECONDS))

        try {
            val intent = Intent(
                getInstrumentation().targetContext,
                OwnerAuthorityTrustActivity::class.java
            ).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            activity = getInstrumentation().startActivitySync(intent) as OwnerAuthorityTrustActivity
            getInstrumentation().waitForIdleSync()

            val gate = privateField(activity!!, "operationGate") as OwnerAuthorityOperationGate
            val token = privateField(gate, "activeToken") as? Long
            assertNotNull("Activity did not queue its initial trust inspection", token)
            val operationToken = token!!
            assertTrue("queued operation should be active before destruction", gate.isActive(operationToken))

            val targetActivity = activity!!
            val application = getInstrumentation().targetContext.applicationContext as Application
            val destroyed = CountDownLatch(1)
            val lifecycleCallbacks = object : Application.ActivityLifecycleCallbacks {
                override fun onActivityCreated(activity: Activity, state: Bundle?) = Unit
                override fun onActivityStarted(activity: Activity) = Unit
                override fun onActivityResumed(activity: Activity) = Unit
                override fun onActivityPaused(activity: Activity) = Unit
                override fun onActivityStopped(activity: Activity) = Unit
                override fun onActivitySaveInstanceState(activity: Activity, state: Bundle) = Unit
                override fun onActivityDestroyed(activity: Activity) {
                    if (activity === targetActivity) destroyed.countDown()
                }
            }
            application.registerActivityLifecycleCallbacks(lifecycleCallbacks)
            try {
                getInstrumentation().runOnMainSync { targetActivity.finish() }
                assertTrue(
                    "Activity onDestroy callback was not observed",
                    destroyed.await(5, TimeUnit.SECONDS)
                )
                assertTrue("Activity did not reach destroyed state", targetActivity.isDestroyed)
                assertFalse("destroyed Activity must invalidate queued work", gate.isActive(operationToken))
                assertFalse("destroyed Activity must not receive a queued callback", gate.isDeliverable(operationToken))
            } finally {
                application.unregisterActivityLifecycleCallbacks(lifecycleCallbacks)
            }
        } finally {
            releaseWorker.countDown()
            val current = activity
            if (current != null && !current.isDestroyed) {
                getInstrumentation().runOnMainSync { current.finish() }
            }
            OwnerAuthorityIoCoordinator.execute { queueDrained.countDown() }
            assertTrue("queued trust I/O did not drain after release", queueDrained.await(5, TimeUnit.SECONDS))
        }
    }

    private fun privateField(target: Any, name: String): Any? {
        val field = target.javaClass.getDeclaredField(name)
        field.isAccessible = true
        return field.get(target)
    }
}
