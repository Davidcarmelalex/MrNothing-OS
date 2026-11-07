package tech.mrnothing.os

import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.content.pm.PackageManager
import android.view.accessibility.AccessibilityManager

/** Read-only exact-component Android observations; never enables or connects a service. */
internal class AndroidAccessibilityDisclosureProbe(context: Context) : AccessibilityDisclosureProbe {
    private val appContext = context.applicationContext ?: context

    @Suppress("DEPRECATION")
    override fun isDeclared(): Boolean {
        val packageInfo = try {
            appContext.packageManager.getPackageInfo(appContext.packageName, PackageManager.GET_SERVICES)
        } catch (error: PackageManager.NameNotFoundException) {
            throw IllegalStateException("own application package could not be inspected", error)
        }
        return packageInfo.services.orEmpty().any { service ->
            service.packageName == appContext.packageName &&
                service.name == AccessibilityServiceContract.COMPONENT_CLASS_NAME
        }
    }

    override fun isEnabled(): Boolean {
        val manager = appContext.getSystemService(AccessibilityManager::class.java)
            ?: throw IllegalStateException("AccessibilityManager unavailable")
        return manager.getEnabledAccessibilityServiceList(
            AccessibilityServiceInfo.FEEDBACK_ALL_MASK
        ).any { enabledService ->
            val info = enabledService.resolveInfo?.serviceInfo
            info != null &&
                info.packageName == appContext.packageName &&
                info.name == AccessibilityServiceContract.COMPONENT_CLASS_NAME
        }
    }
}
