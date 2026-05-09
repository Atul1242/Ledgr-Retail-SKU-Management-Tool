package com.ledgr.scanner.data.api

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class ScanRequest(
    val sku_code: String,
    val product_name: String? = null,
    val qty_received: Int = 1,
    val batch_expiry: String? = null,
    val scanned_at: String? = null,
)

@JsonClass(generateAdapter = true)
data class ScanResponse(
    val status: String,
    val message: String? = null,
)
