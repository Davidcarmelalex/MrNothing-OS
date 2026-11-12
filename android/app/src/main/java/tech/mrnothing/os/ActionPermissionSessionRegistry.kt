package tech.mrnothing.os

/**
 * The kind of app-owned platform session whose live lifecycle is observed.
 * These values are prerequisites only; they never represent owner consent.
 */
internal enum class ActionPermissionSessionKind {
    ACCESSIBILITY,
    PROJECTION
}

/**
 * Process-local, fail-closed lifecycle registry for future app-owned platform
 * session providers.
 *
 * A provider may call [begin] only from a successful Android lifecycle callback:
 * AccessibilityService.onServiceConnected, or after a user-approved
 * MediaProjection has been obtained and its stop callback registered. It must
 * call [end] from the matching disconnect/stop callback. Request/agent data
 * must never create or renew a lease.
 *
 * This is deliberately not authentication, owner consent, permission state,
 * or an authorization capability. A lease is an in-process lifecycle handle.
 * Process death clears all state; callers must not persist or restore leases.
 */
internal class ActionPermissionSessionRegistry(
    private val expectedPackageName: String
) {
    /** Opaque identity handle; identity, not caller-supplied fields, controls revocation. */
    internal class SessionLease private constructor(
        internal val kind: ActionPermissionSessionKind,
        internal val ownerPackageName: String,
        internal val generation: Long
    ) {
        companion object {
            internal fun issue(
                kind: ActionPermissionSessionKind,
                ownerPackageName: String,
                generation: Long
            ): SessionLease = SessionLease(kind, ownerPackageName, generation)
        }
    }

    private val lock = Any()
    private val active = mutableMapOf<ActionPermissionSessionKind, SessionLease>()
    private var lastGeneration = 0L
    private var generationExhausted = false

    init {
        require(PACKAGE_NAME.matches(expectedPackageName)) {
            "expected package name must be a valid Android application id"
        }
    }

    /**
     * Starts/replaces the current session for [kind]. A mismatched callback
     * package or exhausted generation counter fails closed and returns null.
     */
    fun begin(
        kind: ActionPermissionSessionKind,
        callbackPackageName: String
    ): SessionLease? = synchronized(lock) {
        if (callbackPackageName != expectedPackageName) return@synchronized null
        if (generationExhausted || lastGeneration == Long.MAX_VALUE) {
            generationExhausted = true
            return@synchronized null
        }
        lastGeneration += 1
        SessionLease.issue(kind, expectedPackageName, lastGeneration).also {
            active[kind] = it
        }
    }

    /**
     * Ends only the exact currently-active lease. A late disconnect/stop
     * callback from a replaced session cannot revoke its newer replacement.
     */
    fun end(
        kind: ActionPermissionSessionKind,
        callbackPackageName: String,
        lease: SessionLease
    ): Boolean = synchronized(lock) {
        if (callbackPackageName != expectedPackageName ||
            lease.kind != kind ||
            lease.ownerPackageName != expectedPackageName ||
            active[kind] !== lease
        ) return@synchronized false
        active.remove(kind)
        true
    }

    /** Fresh, exact-package observation. No result is cached outside this call. */
    fun isActive(
        kind: ActionPermissionSessionKind,
        callbackPackageName: String
    ): Boolean = synchronized(lock) {
        callbackPackageName == expectedPackageName &&
            active[kind]?.ownerPackageName == expectedPackageName
    }

    /** Adapter for the existing action-specific permission probe. */
    fun accessibilityConnectionProbe(): AccessibilityServiceConnectionProbe =
        AccessibilityServiceConnectionProbe { packageName ->
            isActive(ActionPermissionSessionKind.ACCESSIBILITY, packageName)
        }

    /** Adapter for the existing action-specific permission probe. */
    fun projectionSessionProbe(): UserApprovedProjectionSessionProbe =
        UserApprovedProjectionSessionProbe { packageName ->
            isActive(ActionPermissionSessionKind.PROJECTION, packageName)
        }

    private companion object {
        val PACKAGE_NAME = Regex("^[A-Za-z][A-Za-z0-9_]*(?:\\.[A-Za-z][A-Za-z0-9_]*)+$")
    }
}
