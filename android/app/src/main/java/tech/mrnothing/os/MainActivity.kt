package tech.mrnothing.os

import android.app.Activity
import android.app.role.RoleManager
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
import android.widget.Toast
import kotlin.math.roundToInt

/**
 * User-selected Android HOME launcher preview.
 * No privileged actions, background screen capture or autonomous device control.
 */
class MainActivity : Activity() {
    // All foreground colors meet WCAG AA normal-text contrast against the dark surface.
    private val backgroundColor = Color.rgb(10, 12, 22)
    private val primaryTextColor = Color.WHITE
    private val secondaryTextColor = Color.rgb(206, 210, 226)
    private val accentColor = Color.rgb(190, 164, 255)
    private val buttonColor = Color.rgb(46, 43, 83)
    private var lastHomeRoleHeld: Boolean? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        render()
    }

    override fun onResume() {
        super.onResume()
        // Do not recreate the view tree on every resume: preserve TalkBack focus and scroll.
        if (lastHomeRoleHeld != homeRoleHeld()) render()
    }

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).roundToInt()

    private fun homeRoleHeld(): Boolean {
        val manager = getSystemService(RoleManager::class.java)
        return manager.isRoleAvailable(RoleManager.ROLE_HOME) &&
            manager.isRoleHeld(RoleManager.ROLE_HOME)
    }

    private fun label(value: String, sizeSp: Float, color: Int, heading: Boolean = false): TextView =
        TextView(this).apply {
            text = value
            setTextSize(TypedValue.COMPLEX_UNIT_SP, sizeSp)
            setTextColor(color)
            setPadding(0, dp(8), 0, dp(8))
            if (heading) isAccessibilityHeading = true
        }

    private fun addAction(
        root: LinearLayout,
        label: String,
        accessibilityLabel: String,
        run: () -> Unit
    ) {
        val button = Button(this).apply {
            text = label
            contentDescription = accessibilityLabel
            isAllCaps = false
            minHeight = dp(56)
            setPadding(dp(12), dp(10), dp(12), dp(10))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            setTextColor(primaryTextColor)
            backgroundTintList = ColorStateList.valueOf(buttonColor)
            setOnClickListener { run() }
        }
        root.addView(button, LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        ).apply { bottomMargin = dp(8) })
    }

    private fun openHomeSelection() {
        // Explicit recovery path: the owner selects the stock launcher in Android Settings.
        // Never silently change the HOME role or disable the stock launcher.
        try {
            startActivity(Intent(Settings.ACTION_HOME_SETTINGS))
        } catch (_: ActivityNotFoundException) {
            startActivity(Intent(Settings.ACTION_SETTINGS))
        } catch (_: SecurityException) {
            Toast.makeText(this, "Home settings unavailable; open Android Settings", Toast.LENGTH_LONG).show()
            startActivity(Intent(Settings.ACTION_SETTINGS))
        }
    }

    private fun render() {
        val selected = homeRoleHeld()
        lastHomeRoleHeld = selected
        val scroll = ScrollView(this).apply {
            isFillViewport = true
            isVerticalScrollBarEnabled = true
        }
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(32), dp(20), dp(32))
            setBackgroundColor(backgroundColor)
        }

        root.addView(label("MR. NOTHING", 32f, accentColor, heading = true))
        root.addView(label("AGENTIC OS  ·  DEVELOPER PREVIEW", 14f, secondaryTextColor))
        root.addView(label("Your phone. Your intelligence.", 20f, primaryTextColor))

        root.addView(label("Device status", 22f, accentColor, heading = true))
        val info = DeviceDiagnostics.snapshot(this)
        val battery = info.batteryPercent?.let { "$"+"{it}%" } ?: "Unavailable"
        root.addView(label(
            "$"+"{info.manufacturer} $"+"{info.model} · Android $"+"{info.androidRelease}\n" +
                "Battery: $"+"{battery}\n" +
                "Default Home: $"+"{if (selected) "Mr. Nothing" else "Another launcher"}\n" +
                "Agent: Offline · Cellular AI audio: Unverified",
            16f,
            secondaryTextColor
        ))

        if (!selected) {
            addAction(root, "Choose Mr. Nothing as Home",
                "Open Android confirmation to select Mr. Nothing as the default Home app") {
                val manager = getSystemService(RoleManager::class.java)
                if (manager.isRoleAvailable(RoleManager.ROLE_HOME)) {
                    startActivityForResult(manager.createRequestRoleIntent(RoleManager.ROLE_HOME), 100)
                }
            }
        }

        addAction(root, "Switch default Home app",
            "Recovery: open Android Home app settings to select the stock launcher") {
            openHomeSelection()
        }
        addAction(root, "Android Settings", "Open Android system settings") {
            startActivity(Intent(Settings.ACTION_SETTINGS))
        }

        root.addView(label("Installed apps", 22f, accentColor, heading = true))
        root.addView(label("Select an app to open it. No app is controlled without your action.",
            14f, secondaryTextColor))
        val apps = AppCatalog.installed(this).filterNot { it.packageName == packageName }
        if (apps.isEmpty()) {
            root.addView(label("No launchable apps were found.", 16f, secondaryTextColor))
        } else {
            apps.forEach { app ->
                addAction(root, app.label,
                    "Open $"+"{app.label}, package $"+"{app.packageName}") {
                    AppCatalog.launch(this, app.packageName)
                }
            }
        }
        scroll.addView(root)
        setContentView(scroll)
    }
}
