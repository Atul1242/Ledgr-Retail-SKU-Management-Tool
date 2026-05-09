package com.ledgr.scanner.data.api

import com.ledgr.scanner.data.prefs.AppPrefs
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import kotlinx.coroutines.runBlocking
import okhttp3.Cookie
import okhttp3.CookieJar
import okhttp3.HttpUrl
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit

/** In-memory cookie jar — survives process lifetime. Persistent enough for
 *  the demo since the user logs in interactively when the session expires. */
private class InMemoryCookieJar : CookieJar {
    private val store = ConcurrentHashMap<String, MutableList<Cookie>>()
    override fun saveFromResponse(url: HttpUrl, cookies: List<Cookie>) {
        store.getOrPut(url.host) { mutableListOf() }.also { list ->
            // Replace cookies with same name
            val incomingNames = cookies.map { it.name }.toSet()
            list.removeAll { it.name in incomingNames }
            list.addAll(cookies)
        }
    }
    override fun loadForRequest(url: HttpUrl): List<Cookie> =
        store[url.host]?.filter { it.matches(url) } ?: emptyList()

    fun clear() { store.clear() }
}

/** CSRF interceptor: adds X-CSRF-Token to every state-changing request. The
 *  token is fetched from the home page and cached in DataStore. */
private class CsrfInterceptor(private val prefs: AppPrefs) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): okhttp3.Response {
        val req = chain.request()
        val needsToken = req.method !in listOf("GET", "HEAD", "OPTIONS")
        return if (!needsToken) chain.proceed(req) else {
            val token = runBlocking { prefs.csrfToken() } ?: ""
            val tagged = req.newBuilder()
                .header("X-CSRF-Token", token)
                .build()
            chain.proceed(tagged)
        }
    }
}

class ApiHolder(private val prefs: AppPrefs) {
    @Volatile var api: LedgrApi? = null
        private set
    @Volatile var baseUrl: String? = null
        private set

    private val cookieJar = InMemoryCookieJar()

    fun rebuild(serverUrl: String) {
        val base = if (serverUrl.endsWith("/")) serverUrl else "$serverUrl/"
        if (base == baseUrl) return
        val moshi = Moshi.Builder().add(KotlinJsonAdapterFactory()).build()
        val log = HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC }
        val client = OkHttpClient.Builder()
            .cookieJar(cookieJar)
            .addInterceptor(CsrfInterceptor(prefs))
            .addInterceptor(log)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(20, TimeUnit.SECONDS)
            .build()
        val retrofit = Retrofit.Builder()
            .baseUrl(base)
            .client(client)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
        api = retrofit.create(LedgrApi::class.java)
        baseUrl = base
    }

    fun signOut() {
        cookieJar.clear()
        api = null
        baseUrl = null
    }
}
