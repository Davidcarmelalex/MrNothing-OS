package tech.mrnothing.os

import android.app.Activity
import android.app.Application
import android.app.Instrumentation
import android.content.Intent
import android.content.IntentFilter
import android.provider.Settings
import android.os.Bundle
import android.test.InstrumentationTestCase
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

class AccessibilityDisclosureActivityTest : InstrumentationTestCase() {
    /**
     * Launch without Instrumentation.startActivitySync/waitForIdleSync, whose
     * global-idle wait can hang the whole QA job when the emulator UI is stuck.
     * Both activity observation and resume are bounded so a failure is localised.
     */
    private fun launchMainActivity(): MainActivity {
        val instrumentation = getInstrumentation()
        val monitor = Instrumentation.ActivityMonitor(MainActivity::class.java.name, null, false)
        val application = instrumentation.targetContext.applicationContext as Application
        val resumed = CountDownLatch(1)
        val lifecycle = object : Application.ActivityLifecycleCallbacks {
            override fun onActivityCreated(activity: Activity, savedInstanceState: Bundle?) = Unit
            override fun onActivityStarted(activity: Activity) = Unit
            override fun onActivityResumed(activity: Activity) {
                if (activity is MainActivity) resumed.countDown()
            }
            override fun onActivityPaused(activity: Activity) = Unit
            override fun onActivityStopped(activity: Activity) = Unit
            override fun onActivitySaveInstanceState(activity: Activity, outState: Bundle) = Unit
            override fun onActivityDestroyed(activity: Activity) = Unit
        }
        instrumentation.addMonitor(monitor)
        application.registerActivityLifecycleCallbacks(lifecycle)
        try {
            // ActivityMonitor's action-filter matching can consume an actionless Intent.
            // Use the real launcher action so the Accessibility Settings monitor below cannot
            // intercept this explicit MainActivity launch.
            val intent = Intent(Intent.ACTION_MAIN)
                .setClass(instrumentation.targetContext, MainActivity::class.java)
                .addCategory(Intent.CATEGORY_LAUNCHER)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
            assertEquals(
                "launcher test Intent must not be actionless while an action-filtered Settings monitor is active",
                Intent.ACTION_MAIN,
                intent.action
            )
            assertTrue(
                "launcher test Intent must carry the LAUNCHER category",
                intent.hasCategory(Intent.CATEGORY_LAUNCHER)
            )
            instrumentation.targetContext.startActivity(intent)
            val activity = monitor.waitForActivityWithTimeout(10_000)
            assertNotNull("launcher MainActivity was not observed within 10 seconds", activity)
            assertTrue(
                "launcher MainActivity did not resume within 10 seconds",
                resumed.await(10, TimeUnit.SECONDS)
            )
            return activity as MainActivity
        } finally {
            application.unregisterActivityLifecycleCallbacks(lifecycle)
            instrumentation.removeMonitor(monitor)
        }
    }

    /** Exercise the real owner-visible launcher entry into this non-exported Activity. */
    private fun openDisclosureFromLauncher(main: MainActivity): AccessibilityDisclosureActivity {
        val monitor = Instrumentation.ActivityMonitor(
            AccessibilityDisclosureActivity::class.java.name,
            null,
            false
        )
        getInstrumentation().addMonitor(monitor)
        try {
            val entry = findButton(main.window.decorView, "Accessibility access & revocation")
            assertNotNull("launcher disclosure entry is missing", entry)
            getInstrumentation().runOnMainSync { entry!!.performClick() }
            val activity = monitor.waitForActivityWithTimeout(5_000)
            assertNotNull("launcher entry did not open the private disclosure Activity", activity)
            return activity as AccessibilityDisclosureActivity
        } finally {
            getInstrumentation().removeMonitor(monitor)
        }
    }

    private fun allText(root: View): List<String> {
        val values = mutableListOf<String>()
        if (root is TextView) values += root.text.toString()
        if (root is ViewGroup) for (index in 0 until root.childCount) values += allText(root.getChildAt(index))
        return values
    }

    private fun findButton(root: View, title: String): Button? {
        if (root is Button && root.text.toString() == title) return root
        if (root is ViewGroup) for (index in 0 until root.childCount) {
            val match = findButton(root.getChildAt(index), title)
            if (match != null) return match
        }
        return null
    }

    private fun finishActivities(
        activity: AccessibilityDisclosureActivity?,
        launcher: MainActivity?
    ) {
        getInstrumentation().runOnMainSync {
            if (activity != null && !activity.isDestroyed) activity.finish()
            if (launcher != null && !launcher.isDestroyed) launcher.finish()
        }
    }

    fun testCurrentBuildClearlyDisclosesNoAccessibilityService() {
        var launcher: MainActivity? = null
        var activity: AccessibilityDisclosureActivity? = null
        try {
            launcher = launchMainActivity()
            activity = openDisclosureFromLauncher(launcher!!)
            val text = allText(activity!!.window.decorView)
            assertTrue(text.any { it.contains("No accessibility service is registered in this build.") })
            assertTrue(text.any { it.contains("cannot read your screen or control other apps through Accessibility") })
            assertNotNull(findButton(activity!!.window.decorView, "Review Android Accessibility settings"))
            assertFalse(text.any { it.contains("Enable Mr. Nothing accessibility") })
        } finally {
            finishActivities(activity, launcher)
        }
    }

    fun testAccessibilitySettingsIntentIsIssuedOnlyAfterExplicitTap() {
        val settingsMonitor = Instrumentation.ActivityMonitor(
            IntentFilter(Settings.ACTION_ACCESSIBILITY_SETTINGS),
            Instrumentation.ActivityResult(Activity.RESULT_OK, null),
            true
        )
        getInstrumentation().addMonitor(settingsMonitor)
        var launcher: MainActivity? = null
        var activity: AccessibilityDisclosureActivity? = null
        try {
            launcher = launchMainActivity()
            activity = openDisclosureFromLauncher(launcher!!)
            assertEquals(0, settingsMonitor.hits)
            val button = findButton(activity!!.window.decorView, "Review Android Accessibility settings")
            assertNotNull(button)
            getInstrumentation().runOnMainSync { button!!.performClick() }
            assertTrue("explicit tap did not request Accessibility settings", settingsMonitor.hits > 0)
        } finally {
            getInstrumentation().removeMonitor(settingsMonitor)
            finishActivities(activity, launcher)
        }
    }
}
