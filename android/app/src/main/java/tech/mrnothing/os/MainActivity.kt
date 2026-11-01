package tech.mrnothing.os

import android.app.Activity
import android.app.role.RoleManager
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.graphics.Color
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/** First runnable HOME experience; deliberately no privileged background control. */
class MainActivity : Activity() {
    private val purple = Color.rgb(174, 139, 255)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        render()
    }

    override fun onResume() {
        super.onResume()
        render()
    }

    private fun render() {
        val scroll = ScrollView(this)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(40, 70, 40, 60)
            setBackgroundColor(Color.rgb(11, 11, 20))
        }
        fun text(value: String, size: Float, color: Int = Color.WHITE): TextView =
            TextView(this).apply {
                this.text = value
                textSize = size
                setTextColor(color)
                setPadding(0, 10, 0, 14)
            }
        fun action(label: String, run: () -> Unit) {
            root.addView(Button(this).apply {
                text = label
                setOnClickListener { run() }
            })
        }

        root.addView(text("MR. NOTHING", 34f, purple))
        root.addView(text("AGENTIC OPERATING SYSTEM  /  DEVELOPER PREVIEW", 12f, Color.LTGRAY))
        root.addView(text("Your phone. Your intelligence.", 20f))
        val info = DeviceDiagnostics.snapshot(this)
        root.addView(text("DEVICE STATUS", 16f, purple))
        root.addView(text(
            "${info.manufacturer} ${info.model} · Android ${info.androidRelease}\n" +
            "Battery: ${info.batteryPercent?.toString() ?: "Unavailable"}%\n" +
            "Home role: ${if (info.homeRoleHeld) "Active" else "Not selected"}\n" +
            "Agent: Offline · SIM audio: Unverified",
            15f, Color.LTGRAY
        ))
        action("Make Mr. Nothing my Home") {
            val manager = getSystemService(RoleManager::class.java)
            if (manager.isRoleAvailable(RoleManager.ROLE_HOME) &&
                !manager.isRoleHeld(RoleManager.ROLE_HOME)) {
                startActivityForResult(manager.createRequestRoleIntent(RoleManager.ROLE_HOME), 100)
            }
        }
        action("Android Settings") { startActivity(Intent(Settings.ACTION_SETTINGS)) }
        root.addView(text("YOUR APPS", 16f, purple))
        AppCatalog.installed(this).filterNot { it.packageName == packageName }.forEach { app ->
            action(app.label) { AppCatalog.launch(this, app.packageName) }
        }
        scroll.addView(root)
        setContentView(scroll)
    }
}
