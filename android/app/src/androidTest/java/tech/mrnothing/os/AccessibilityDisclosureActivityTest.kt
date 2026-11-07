package tech.mrnothing.os

import android.app.Activity
import android.app.Instrumentation
import android.content.Intent
import android.content.IntentFilter
import android.provider.Settings
import android.test.InstrumentationTestCase
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView

class AccessibilityDisclosureActivityTest : InstrumentationTestCase() {
    private fun launchMainActivity(): MainActivity {
        val intent = Intent(getInstrumentation().targetContext, MainActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        return getInstrumentation().startActivitySync(intent) as MainActivity
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
            getInstrumentation().waitForIdleSync()
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
            getInstrumentation().waitForIdleSync()
            assertEquals(0, settingsMonitor.hits)
            val button = findButton(activity!!.window.decorView, "Review Android Accessibility settings")
            assertNotNull(button)
            getInstrumentation().runOnMainSync { button!!.performClick() }
            getInstrumentation().waitForIdleSync()
            assertTrue("explicit tap did not request Accessibility settings", settingsMonitor.hits > 0)
        } finally {
            getInstrumentation().removeMonitor(settingsMonitor)
            finishActivities(activity, launcher)
        }
    }
}
