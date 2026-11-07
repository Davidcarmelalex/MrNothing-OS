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
    private fun launchDisclosure(): AccessibilityDisclosureActivity {
        val intent = Intent(getInstrumentation().targetContext, AccessibilityDisclosureActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        return getInstrumentation().startActivitySync(intent) as AccessibilityDisclosureActivity
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

    fun testCurrentBuildClearlyDisclosesNoAccessibilityService() {
        var activity: AccessibilityDisclosureActivity? = null
        try {
            activity = launchDisclosure()
            getInstrumentation().waitForIdleSync()
            val text = allText(activity!!.window.decorView)
            assertTrue(text.any { it.contains("No accessibility service is registered in this build.") })
            assertTrue(text.any { it.contains("cannot read your screen or control other apps through Accessibility") })
            assertNotNull(findButton(activity!!.window.decorView, "Review Android Accessibility settings"))
            assertFalse(text.any { it.contains("Enable Mr. Nothing accessibility") })
        } finally {
            val current = activity
            if (current != null && !current.isDestroyed) getInstrumentation().runOnMainSync { current.finish() }
        }
    }

    fun testAccessibilitySettingsIntentIsIssuedOnlyAfterExplicitTap() {
        val monitor = Instrumentation.ActivityMonitor(
            IntentFilter(Settings.ACTION_ACCESSIBILITY_SETTINGS),
            Instrumentation.ActivityResult(Activity.RESULT_OK, null),
            true
        )
        getInstrumentation().addMonitor(monitor)
        var activity: AccessibilityDisclosureActivity? = null
        try {
            activity = launchDisclosure()
            getInstrumentation().waitForIdleSync()
            assertEquals(0, monitor.hits)
            val button = findButton(activity!!.window.decorView, "Review Android Accessibility settings")
            assertNotNull(button)
            getInstrumentation().runOnMainSync { button!!.performClick() }
            getInstrumentation().waitForIdleSync()
            assertTrue("explicit tap did not request Accessibility settings", monitor.hits > 0)
        } finally {
            getInstrumentation().removeMonitor(monitor)
            val current = activity
            if (current != null && !current.isDestroyed) getInstrumentation().runOnMainSync { current.finish() }
        }
    }
}
