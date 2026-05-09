package com.ledgr.scanner.data.api

import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.Field
import retrofit2.http.FormUrlEncoded
import retrofit2.http.GET
import retrofit2.http.POST

/** Subset of the Flask app's API surface used by the Android scanner. */
interface LedgrApi {

    @FormUrlEncoded
    @POST("login")
    suspend fun login(
        @Field("email") email: String,
        @Field("password") password: String,
    ): Response<ResponseBody>

    /** Returns the rendered dashboard so we can extract the CSRF meta tag. */
    @GET("/")
    suspend fun home(): Response<ResponseBody>

    /** Posts a single scan to /api/sku/scan. The OkHttp interceptor adds the
     *  X-CSRF-Token header from the cached value automatically. */
    @POST("api/sku/scan")
    suspend fun scan(@Body req: ScanRequest): Response<ScanResponse>

    @GET("login")
    suspend fun ping(): Response<ResponseBody>
}
