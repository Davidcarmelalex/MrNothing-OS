package tech.mrnothing.os

import android.app.Activity
import android.app.role.RoleManager
import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.graphics.Color

/** Minimal functional HOME-role shell. Not a ROM or autonomous agent yet. */
class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(40, 80, 40, 40)
            setBackgroundColor(Color.rgb(10, 10, 18))
        }
        val title = TextView(this).apply {
            text = "MR. NOTHING OS"
            textSize = 30f
            setTextColor(Color.WHITE)
        }
        val status = TextView(this).apply {
            text = "Phase 1 developer preview • Android HOME shell\nAgent: not connected\nTelephony: not connected"
            textSize = 16f
            setTextColor(Color.LTGRAY)
            setPadding(0, 32, 0, 32)
        }
        val home = Button(this).apply {
            text = "Set as default Home"
            setOnClickListener {
                val roles = getSystemService(RoleManager::class.java)
                if (roles.isRoleAvailable(RoleManager.ROLE_HOME) &&
                    !roles.isRoleHeld(RoleManager.ROLE_HOME)) {
                    startActivityForResult(roles.createRequestRoleIntent(RoleManager.ROLE_HOME), 100)
                }
            }
        }
        val apps = Button(this).apply {
            text = "Open Android Settings"
            setOnClickListener { startActivity(Intent(android.provider.Settings.ACTION_SETTINGS)) }
        }
        root.addView(title)
        root.addView(status)
        root.addView(home)
        root.addView(apps)
        setContentView(root)
    }
}
