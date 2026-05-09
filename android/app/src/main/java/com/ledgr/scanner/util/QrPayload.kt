package com.ledgr.scanner.util

import com.squareup.moshi.JsonClass
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory

/** Two pairing payload formats are accepted from the QR code:
 *  1. Plain URL: "http://192.168.1.20:5000/mobile/" (the existing PWA QR)
 *     → strip /mobile/ to get the API base.
 *  2. JSON: `{"server_url":"http://...","name":"Sunrise Pune"}`
 *     (the dedicated /api/qr-pairing endpoint shipped server-side).
 *  Anything else is treated as invalid input. */
object QrPayload {
    @JsonClass(generateAdapter = true)
    data class Pair(val server_url: String, val name: String? = null)

    private val moshi = Moshi.Builder().add(KotlinJsonAdapterFactory()).build()
    private val adapter = moshi.adapter(Pair::class.java)

    data class Parsed(val baseUrl: String, val name: String?)

    fun parse(raw: String): Parsed? {
        val trimmed = raw.trim()
        if (trimmed.startsWith("{")) {
            return try {
                val p = adapter.fromJson(trimmed) ?: return null
                if (!isHttp(p.server_url)) null else Parsed(stripMobile(p.server_url), p.name)
            } catch (_: Exception) { null }
        }
        if (isHttp(trimmed)) return Parsed(stripMobile(trimmed), null)
        return null
    }

    private fun isHttp(s: String) = s.startsWith("http://") || s.startsWith("https://")

    private fun stripMobile(url: String): String {
        val u = url.trimEnd('/')
        return when {
            u.endsWith("/mobile") -> u.removeSuffix("/mobile")
            else -> u
        }
    }
}
