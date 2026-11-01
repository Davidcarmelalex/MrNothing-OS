package tech.mrnothing.os

import android.app.role.RoleManager
import android.content.Context
import android.os.BatteryManager
import android.os.Build

data class DeviceCapabilities(
    val manufacturer: String,
    val model: String,
    val androidRelease: String,
    val apiLevel: Int,
    val homeRoleHeld: Boolean,
    val batteryPercent: Int?,
    val deviceCodename: String
)

object DeviceDiagnostics {
    fun snapshot(context: Context): DeviceCapabilities {
        val roleManager = context.getSystemService(RoleManager::class.java)
        val battery = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        val percent = battery.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        return DeviceCapabilities(
            manufacturer = Build.MANUFACTURER,
            model = Build.MODEL,
            androidRelease = Build.VERSION.RELEASE,
            apiLevel = Build.VERSION.SDK_INT,
            homeRoleHeld = roleManager.isRoleAvailable(RoleManager.ROLE_HOME) &&
                roleManager.isRoleHeld(RoleManager.ROLE_HOME),
            batteryPercent = percent.takeIf { it in 0..100 },
            deviceCodename = Build.DEVICE
        )
    }
}
