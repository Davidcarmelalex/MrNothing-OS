package tech.mrnothing.os

import android.app.Activity
import android.app.Application
import android.app.Instrumentation
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.test.InstrumentationTestCase
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/**
 * QA-UX-008: exercises real launcher-entry UI on a disposable emulator.
 * Every step remains display-only. No device executor or permission grant exists.
 */
class AgentPlanPreviewActivityTest : InstrumentationTestCase() {
    private fun findButton(view: View, title: String): Button? {
        if (view is Button && view.text.toString() == title) return view
        if (view is ViewGroup) for (i in 0 until view.childCount) {
            val found = findButton(view.getChildAt(i), title)
            if (found != null) return found
        }
        return null
    }

    private fun texts(view: View): List<String> {
        val values = mutableListOf<String>()
        if (view is TextView) values += view.text.toString()
        if (view is ViewGroup) for (i in 0 until view.childCount) {
            values += texts(view.getChildAt(i))
        }
        return values
    }

    private fun launch(): Pair<MainActivity, AgentPlanPreviewActivity> {
        val instrumentation = getInstrumentation()
        val mainMonitor = Instrumentation.ActivityMonitor(MainActivity::class.java.name, null, false)
        val previewMonitor = Instrumentation.ActivityMonitor(AgentPlanPreviewActivity::class.java.name, null, false)
        instrumentation.addMonitor(mainMonitor)
        instrumentation.addMonitor(previewMonitor)
        try {
            instrumentation.targetContext.startActivity(
                Intent(Intent.ACTION_MAIN)
                    .setClass(instrumentation.targetContext, MainActivity::class.java)
                    .addCategory(Intent.CATEGORY_LAUNCHER)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
            )
            val main = mainMonitor.waitForActivityWithTimeout(10_000) as? MainActivity
            assertNotNull("MainActivity did not launch", main)
            val entry = findButton(main!!.window.decorView, "Offline agent plan preview")
            assertNotNull("Owner-visible launcher entry missing", entry)
            assertTrue("Launcher entry has no accessible description",
                !entry!!.contentDescription.isNullOrBlank())
            instrumentation.runOnMainSync { entry.performClick() }
            val preview = previewMonitor.waitForActivityWithTimeout(10_000) as? AgentPlanPreviewActivity
            assertNotNull("Private preview did not open from launcher", preview)
            return Pair(main, preview!!)
        } finally {
            instrumentation.removeMonitor(previewMonitor)
            instrumentation.removeMonitor(mainMonitor)
        }
    }

    private fun click(activity: AgentPlanPreviewActivity, title: String) {
        val button = findButton(activity.window.decorView, title)
        assertNotNull("Missing sample control: $title", button)
        assertTrue("Sample control lacks accessible description: $title",
            !button!!.contentDescription.isNullOrBlank())
        getInstrumentation().runOnMainSync { button.performClick() }
    }

    private fun assertStatus(activity: AgentPlanPreviewActivity, vararg parts: String) {
        val status = texts(activity.window.decorView)
            .singleOrNull { it.startsWith("Offline sample rehearsal (no AI inference):") }
        assertNotNull("Expected one rehearsal status TextView", status)
        for (part in parts) assertTrue("Missing '$part' in '$status'", status!!.contains(part))
        assertTrue(status!!.contains("Authorized: No"))
        assertTrue(status.contains("Device actions executed: No"))
        assertTrue(status.contains("No consent granted."))
    }

    private fun finish(main: MainActivity?, preview: AgentPlanPreviewActivity?) {
        getInstrumentation().runOnMainSync {
            if (preview != null && !preview.isDestroyed) preview.finish()
            if (main != null && !main.isDestroyed) main.finish()
        }
    }

    fun testSampleReviewProgressionTerminalDenialAndCancellation() {
        var main: MainActivity? = null
        var preview: AgentPlanPreviewActivity? = null
        try {
            val pair = launch()
            main = pair.first
            preview = pair.second
            val screen = pair.second
            click(screen, "Start offline sample rehearsal")
            assertStatus(screen, "State: REVIEW_REQUIRED", "Previewed: 0/3",
                "Supervisor gate: BLOCKED_NO_ACTIVE_STEP")
            click(screen, "Preview next sample step")
            assertStatus(screen, "State: REVIEW_REQUIRED", "Previewed: 0/3")
            click(screen, "Acknowledge simulation instructions")
            assertStatus(screen, "State: READY", "Previewed: 0/3")
            click(screen, "Preview next sample step")
            assertStatus(screen, "State: PREVIEWING", "Step: get_battery",
                "Previewed: 1/3", "Supervisor gate: BLOCKED_NO_VERIFIED_SESSION")
            click(screen, "Preview next sample step")
            assertStatus(screen, "State: PREVIEWING", "Step: open_app", "Previewed: 2/3")
            click(screen, "Preview next sample step")
            assertStatus(screen, "State: COMPLETE", "Step: send_message",
                "Previewed: 3/3", "Supervisor gate: BLOCKED_TERMINAL_REHEARSAL")
            click(screen, "Preview next sample step")
            assertStatus(screen, "State: COMPLETE", "Previewed: 3/3")
            click(screen, "Cancel and clear")
            val cleared = texts(screen.window.decorView)
            assertTrue(cleared.any { it.contains("Preview cleared. No consent, permission or device action granted.") })
            click(screen, "Start offline sample rehearsal")
            assertStatus(screen, "State: REVIEW_REQUIRED", "Previewed: 0/3")
        } finally {
            finish(main, preview)
        }
    }

    fun testSwitchingPreviewModesInvalidatesAcknowledgedRehearsal() {
        var main: MainActivity? = null
        var preview: AgentPlanPreviewActivity? = null
        try {
            val pair = launch()
            main = pair.first
            preview = pair.second
            val screen = pair.second

            click(screen, "Start offline sample rehearsal")
            click(screen, "Acknowledge simulation instructions")
            click(screen, "Preview next sample step")
            assertStatus(screen, "State: PREVIEWING", "Previewed: 1/3")

            click(screen, "Preview battery request")
            assertTrue(texts(screen.window.decorView).any {
                it.contains("Preview only.") && it.contains("Authorized: No")
            })
            click(screen, "Preview next sample step")
            assertStatus(screen, "State: CANCELLED", "Previewed: 0/0",
                "Supervisor gate: BLOCKED_TERMINAL_REHEARSAL")

            click(screen, "Start offline sample rehearsal")
            assertStatus(screen, "State: REVIEW_REQUIRED", "Previewed: 0/3")
            click(screen, "Acknowledge simulation instructions")
            click(screen, "Preview next sample step")
            assertStatus(screen, "State: PREVIEWING", "Previewed: 1/3")

            click(screen, "Preview multi-step plan")
            assertTrue(texts(screen.window.decorView).any {
                it.contains("Fixed sample plan (no AI inference):") &&
                    it.contains("Authorized: No")
            })
            click(screen, "Preview next sample step")
            assertStatus(screen, "State: CANCELLED", "Previewed: 0/0",
                "Supervisor gate: BLOCKED_TERMINAL_REHEARSAL")
        } finally {
            finish(main, preview)
        }
    }

    fun testOnStopClearsActiveRehearsalWithoutGrant() {
        var main: MainActivity? = null
        var preview: AgentPlanPreviewActivity? = null
        val stopped = CountDownLatch(1)
        val application = getInstrumentation().targetContext.applicationContext as Application
        val callback = object : Application.ActivityLifecycleCallbacks {
            override fun onActivityCreated(a: Activity, b: Bundle?) = Unit
            override fun onActivityStarted(a: Activity) = Unit
            override fun onActivityResumed(a: Activity) = Unit
            override fun onActivityPaused(a: Activity) = Unit
            override fun onActivityStopped(a: Activity) {
                if (a is AgentPlanPreviewActivity) stopped.countDown()
            }
            override fun onActivitySaveInstanceState(a: Activity, b: Bundle) = Unit
            override fun onActivityDestroyed(a: Activity) = Unit
        }
        try {
            val pair = launch()
            main = pair.first
            preview = pair.second
            val screen = pair.second
            click(screen, "Start offline sample rehearsal")
            click(screen, "Acknowledge simulation instructions")
            click(screen, "Preview next sample step")
            assertStatus(screen, "State: PREVIEWING", "Previewed: 1/3")
            application.registerActivityLifecycleCallbacks(callback)
            getInstrumentation().runOnMainSync {
                screen.startActivity(Intent(Settings.ACTION_SETTINGS))
            }
            assertTrue("Preview did not stop within eight seconds", stopped.await(8, TimeUnit.SECONDS))
            assertTrue("onStop did not clear the sample",
                texts(screen.window.decorView).any {
                    it.contains("Preview cleared. No consent, permission or device action granted.")
                })
        } finally {
            application.unregisterActivityLifecycleCallbacks(callback)
            finish(main, preview)
        }
    }
}
