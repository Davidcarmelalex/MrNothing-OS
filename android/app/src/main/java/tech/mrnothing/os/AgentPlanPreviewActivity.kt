package tech.mrnothing.os

import android.app.Activity
import android.content.res.ColorStateList
import android.graphics.Color
import android.os.Bundle
import android.util.TypedValue
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import kotlin.math.roundToInt

/**
 * Owner-visible, offline sample-plan preview. No LLM, network, device
 * command, Android permission, enrollment, or agent executor is connected.
 */
class AgentPlanPreviewActivity : Activity() {
    private lateinit var status: TextView
    private fun dp(n: Int): Int = (n * resources.displayMetrics.density).roundToInt()

    private fun button(root: LinearLayout, text: String, hint: String, run: () -> Unit) {
        root.addView(Button(this).apply {
            this.text = text
            contentDescription = hint
            isAllCaps = false
            minHeight = dp(56)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            setTextColor(Color.WHITE)
            backgroundTintList = ColorStateList.valueOf(Color.rgb(46, 43, 83))
            setOnClickListener { run() }
        }, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(8) })
    }

    private fun preview(action: String) {
        val decision = AgentPlanPreview.inspect(action)
        status.text = "Sample: ${decision.action}\nRisk: ${decision.risk}\n" +
            "${decision.description}\n" +
            "Authorized: No · Device actions executed: No · Preview only."
    }

    private fun previewPlan() {
        val plan = AgentPlanPreviewPlan.inspect(
            listOf("get_battery", "open_app", "send_message")
        )
        val lines = plan.steps.mapIndexed { index, step ->
            (index + 1).toString() + ". " + step.action + ": " + step.risk
        }.joinToString("\n")
        status.text = "Fixed sample plan (no AI inference):\n" + lines + "\n" +
            "Whole-plan risk: " + plan.risk + "\n" + plan.description + "\n" +
            "Authorized: No · Device actions executed: No · Preview only."
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(24), dp(20), dp(24))
            setBackgroundColor(Color.rgb(10, 12, 22))
        }
        root.addView(TextView(this).apply {
            text = "Offline agent plan preview"
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 24f)
            isAccessibilityHeading = true
        })
        status = TextView(this).apply {
            text = "Select a fixed sample action. This is not AI inference, " +
                "owner consent or device control. Nothing will run."
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            setPadding(0, dp(16), 0, dp(16))
            accessibilityLiveRegion = TextView.ACCESSIBILITY_LIVE_REGION_POLITE
        }
        root.addView(status)
        button(root, "Preview battery request", "Inspect sample battery action; no device read") {
            preview("get_battery")
        }
        button(root, "Preview app-opening request", "Inspect sample app action; no app is opened") {
            preview("open_app")
        }
        button(root, "Preview message request", "Inspect sample message action; no message is sent") {
            preview("send_message")
        }
        button(root, "Preview unknown request", "Inspect rejected sample action") {
            preview("root_shell")
        }
        button(root, "Preview multi-step plan",
            "Inspect three fixed sample steps; no device action is executed") {
            previewPlan()
        }
        button(root, "Cancel and clear", "Clear the sample plan preview") {
            clear()
        }
        button(root, "Return to launcher", "Close preview without any device action") {
            clear()
            finish()
        }
        setContentView(ScrollView(this).apply { addView(root) })
    }

    private fun clear() {
        status.text = "Preview cleared. No consent, permission or device action granted."
    }

    override fun onStop() {
        clear()
        super.onStop()
    }
}
