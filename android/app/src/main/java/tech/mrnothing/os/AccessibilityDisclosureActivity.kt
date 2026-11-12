package tech.mrnothing.os

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Color
import android.os.Bundle
import android.provider.Settings
import android.util.TypedValue
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import kotlin.math.roundToInt

/**
 * Owner-visible accessibility disclosure and Settings handoff.
 * This Activity does not register or enable an AccessibilityService.
 */
class AccessibilityDisclosureActivity : Activity() {
    private val backgroundColor = Color.rgb(10, 12, 22)
    private val primaryTextColor = Color.WHITE
    private val secondaryTextColor = Color.rgb(206, 210, 226)
    private val accentColor = Color.rgb(190, 164, 255)
    private val buttonColor = Color.rgb(46, 43, 83)
    private lateinit var statusView: TextView

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).roundToInt()

    private fun addLabel(
        root: LinearLayout,
        value: String,
        sizeSp: Float,
        color: Int,
        heading: Boolean = false
    ): TextView = TextView(this).apply {
        text = value
        setTextSize(TypedValue.COMPLEX_UNIT_SP, sizeSp)
        setTextColor(color)
        setPadding(0, dp(8), 0, dp(8))
        if (heading) isAccessibilityHeading = true
    }.also { root.addView(it) }

    private fun addAction(root: LinearLayout, title: String, description: String, action: () -> Unit) {
        val button = Button(this).apply {
            text = title
            contentDescription = description
            isAllCaps = false
            minHeight = dp(56)
            setPadding(dp(12), dp(10), dp(12), dp(10))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            setTextColor(primaryTextColor)
            backgroundTintList = ColorStateList.valueOf(buttonColor)
            filterTouchesWhenObscured = true
            setOnTouchListener { _, event ->
                if (!OwnerConsentTouchGate.isUnobscured(event.flags)) {
                    statusView.text = "Settings were not opened because the touch was obscured."
                    true
                } else false
            }
            setOnClickListener { action() }
        }
        root.addView(button, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(8) })
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(24), dp(20), dp(24))
            setBackgroundColor(backgroundColor)
        }
        addLabel(root, "Accessibility access", 26f, accentColor, heading = true)
        addLabel(root, "Owner-controlled · optional · no service registered in this build", 14f, secondaryTextColor)
        addLabel(root, "What this access can mean", 20f, accentColor, heading = true)
        addLabel(
            root,
            "Android Accessibility access is powerful. A registered service may observe interface " +
                "content and perform user-interface actions within its declared scope. It must never " +
                "be treated as proof of owner consent.",
            16f,
            primaryTextColor
        )
        addLabel(root, "Current service status", 20f, accentColor, heading = true)
        statusView = addLabel(root, "Checking Android service status…", 16f, primaryTextColor)
        statusView.accessibilityLiveRegion = TextView.ACCESSIBILITY_LIVE_REGION_POLITE
        addLabel(
            root,
            "This build cannot read your screen or control other apps through Accessibility. " +
                "No Mr. Nothing AccessibilityService is registered in the app manifest.",
            16f,
            secondaryTextColor
        )
        addLabel(root, "Owner control and revocation", 20f, accentColor, heading = true)
        addLabel(
            root,
            "Android Settings is the only place to enable or disable an AccessibilityService. " +
                "Mr. Nothing never toggles this access programmatically. If a future reviewed build " +
                "registers a service, you can switch it off in Android Settings under Accessibility. " +
                "Return here to refresh the status.",
            16f,
            primaryTextColor
        )
        addLabel(
            root,
            "Opening Settings is optional and does not grant access. Because this build registers " +
                "no service, no Mr. Nothing entry will appear in the installed-services list.",
            14f,
            secondaryTextColor
        )
        addAction(
            root,
            "Review Android Accessibility settings",
            "Open Android Accessibility settings; no service is enabled by this action"
        ) { openAccessibilitySettings() }
        addAction(root, "Return to launcher", "Return to the Mr. Nothing launcher") { finish() }
        setContentView(ScrollView(this).apply {
            isFillViewport = true
            isVerticalScrollBarEnabled = true
            addView(root)
        })
        refreshStatus()
    }

    override fun onResume() {
        super.onResume()
        if (::statusView.isInitialized) refreshStatus()
    }

    /** Fresh status read on every resume; no cached enabled/connected Boolean. */
    private fun refreshStatus() {
        val current = AccessibilityDisclosureReader(AndroidAccessibilityDisclosureProbe(this)).read()
        statusView.text = when (current) {
            AccessibilityDisclosureStatus.NOT_REGISTERED ->
                "Accessibility service status: No accessibility service is registered in this build."
            AccessibilityDisclosureStatus.REGISTERED_DISABLED ->
                "Accessibility service status: Registered but disabled in Android settings."
            AccessibilityDisclosureStatus.ENABLED_IN_SETTINGS ->
                "Accessibility service status: Enabled in Android settings. This does not prove a live connection."
            AccessibilityDisclosureStatus.UNAVAILABLE ->
                "Accessibility service status: Unavailable. Android state could not be verified; treat access as unavailable."
        }
    }

    private fun openAccessibilitySettings() {
        try {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        } catch (_: ActivityNotFoundException) {
            openGeneralSettings()
        } catch (_: SecurityException) {
            openGeneralSettings()
        }
    }

    private fun openGeneralSettings() {
        statusView.text =
            "Accessibility settings could not be opened. Opening general Android Settings; no access was granted."
        try {
            startActivity(Intent(Settings.ACTION_SETTINGS))
        } catch (_: ActivityNotFoundException) {
            statusView.text = "Android Settings is unavailable. No access was granted."
        } catch (_: SecurityException) {
            statusView.text = "Android Settings launch was denied. No access was granted."
        }
    }
}
