package tech.mrnothing.os

import java.nio.charset.StandardCharsets
import java.security.MessageDigest

/** Closed, typed v2 action argument set. No arbitrary JSON or shell strings. */
internal sealed interface OwnerActionArguments {
    data object ReadScreen : OwnerActionArguments
    data class Navigate(val targetPackage: String) : OwnerActionArguments
    data class Scroll(val direction: String, val distanceDp: Int) : OwnerActionArguments
}

internal object OwnerActionArgumentsCanonicalizer {
    private const val DOMAIN = "mrnothing-owner-action-arguments-v2\u0000"
    private val packageName = Regex("^[A-Za-z][A-Za-z0-9_]*(\\.[A-Za-z][A-Za-z0-9_]*)+$")

    /** Exact ASCII JSON displayed to the owner and hashed into the signed challenge. */
    fun canonicalJson(action: String, arguments: OwnerActionArguments?): String? =
        when {
            action == "read_screen" && arguments === OwnerActionArguments.ReadScreen -> "{}"
            action == "navigate" && arguments is OwnerActionArguments.Navigate &&
                arguments.targetPackage.length in 1..255 &&
                packageName.matches(arguments.targetPackage) ->
                "{\"target_package\":\"${arguments.targetPackage}\"}"
            action == "scroll" && arguments is OwnerActionArguments.Scroll &&
                arguments.direction in setOf("up", "down") &&
                arguments.distanceDp in 1..1_000 ->
                "{\"direction\":\"${arguments.direction}\",\"distance_dp\":${arguments.distanceDp}}"
            else -> null
        }

    fun sha256(action: String, arguments: OwnerActionArguments?): String? {
        val canonical = canonicalJson(action, arguments) ?: return null
        val input = (DOMAIN + action + "\u0000" + canonical)
            .toByteArray(StandardCharsets.US_ASCII)
        return MessageDigest.getInstance("SHA-256").digest(input)
            .joinToString("") { byte -> "%02x".format(byte.toInt() and 0xff) }
    }
}
