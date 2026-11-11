package tech.mrnothing.os

import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import android.test.InstrumentationTestCase

/**
 * SEC-023B1A-QA: inspect the installed/merged manifest, not only source XML.
 * These tests do not bind, start, enable, authenticate or persist anything.
 * Emulator evidence cannot substitute for physical Pixel 9 Pro validation.
 */
class MemoryVaultManifestBoundaryTest : InstrumentationTestCase() {
    fun testInstalledVaultServiceIsDisabledAndPrivate() {
        val context = getInstrumentation().targetContext
        val manager = context.packageManager
        val component = ComponentName(context.packageName, "tech.mrnothing.os.MemoryVaultService")
        val info = manager.getServiceInfo(component, PackageManager.GET_DISABLED_COMPONENTS)
        assertEquals(context.packageName, info.packageName)
        assertEquals(component.className, info.name)
        assertFalse("installed MemoryVault service must be disabled", info.enabled)
        assertFalse("installed MemoryVault service must not be exported", info.exported)
        assertFalse("vault must not be available before unlock", info.directBootAware)
        assertNull("vault must not declare special service permissions", info.permission)
        assertEquals("vault must not run in a separate process",
            info.applicationInfo.processName, info.processName)
        assertEquals("test must not override component state",
            PackageManager.COMPONENT_ENABLED_STATE_DEFAULT,
            manager.getComponentEnabledSetting(component))
    }

    fun testNoImplicitVaultIntentCanResolve() {
        val context = getInstrumentation().targetContext
        val query = Intent("tech.mrnothing.os.MEMORY_VAULT_PROBE")
            .setPackage(context.packageName)
        assertTrue("disabled vault must not expose implicit entry points",
            context.packageManager.queryIntentServices(query, 0).isEmpty())
    }
}
