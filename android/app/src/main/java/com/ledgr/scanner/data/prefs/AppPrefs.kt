package com.ledgr.scanner.data.prefs

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "ledgr_prefs")

/** Persists the paired server URL and any auth state (CSRF token, etc.). */
class AppPrefs(private val context: Context) {

    private val keyServerUrl = stringPreferencesKey("server_url")
    private val keyServerName = stringPreferencesKey("server_name")
    private val keyCsrfToken  = stringPreferencesKey("csrf_token")
    private val keyAuthEmail  = stringPreferencesKey("auth_email")

    val serverUrlFlow: Flow<String?> = context.dataStore.data.map { it[keyServerUrl] }
    val serverNameFlow: Flow<String?> = context.dataStore.data.map { it[keyServerName] }
    val authEmailFlow: Flow<String?> = context.dataStore.data.map { it[keyAuthEmail] }
    val csrfTokenFlow: Flow<String?> = context.dataStore.data.map { it[keyCsrfToken] }

    suspend fun serverUrl(): String? = serverUrlFlow.first()
    suspend fun authEmail(): String? = authEmailFlow.first()
    suspend fun csrfToken(): String? = csrfTokenFlow.first()

    suspend fun saveServer(url: String, name: String? = null) {
        context.dataStore.edit { p ->
            p[keyServerUrl] = url.trimEnd('/')
            if (name != null) p[keyServerName] = name
        }
    }
    suspend fun saveCsrf(token: String) { context.dataStore.edit { it[keyCsrfToken] = token } }
    suspend fun saveAuthEmail(email: String) { context.dataStore.edit { it[keyAuthEmail] = email } }

    suspend fun clearAll() { context.dataStore.edit { it.clear() } }
}
