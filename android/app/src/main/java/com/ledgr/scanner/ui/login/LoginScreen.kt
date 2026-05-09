package com.ledgr.scanner.ui.login

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Email
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.ledgr.scanner.data.ScanRepository
import com.ledgr.scanner.data.api.ApiHolder
import com.ledgr.scanner.data.prefs.AppPrefs
import com.ledgr.scanner.ui.components.*
import com.ledgr.scanner.ui.theme.LedgrNavy
import com.ledgr.scanner.ui.theme.TextPrimary
import com.ledgr.scanner.ui.theme.TextSecondary
import kotlinx.coroutines.launch

@Composable
fun LoginScreen(
    apiHolder: ApiHolder,
    prefs: AppPrefs,
    repo: ScanRepository,
    onLoggedIn: () -> Unit,
    onUnpair: () -> Unit,
) {
    val scope = rememberCoroutineScope()
    val pairedTo by prefs.serverNameFlow.collectAsState(initial = null)
    val pairedUrl by prefs.serverUrlFlow.collectAsState(initial = null)

    var email by remember { mutableStateOf("salesman@sunrise.com") }
    var password by remember { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    Column(modifier = Modifier.fillMaxSize().background(LedgrNavy)) {
        ScreenHeader(
            eyebrow = "Step 2 of 2",
            title = "Sign in",
            subtitle = "Use your Ledgr salesman credentials. The session is bound to this device until you sign out."
        )

        PanelCard(modifier = Modifier.padding(horizontal = 24.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                StatusPill("PAIRED", PillKind.OK)
                Spacer(Modifier.width(10.dp))
                Text(
                    pairedTo ?: pairedUrl ?: "—",
                    style = MaterialTheme.typography.bodyMedium.copy(color = TextPrimary),
                    maxLines = 1,
                )
            }
            Spacer(Modifier.height(20.dp))

            OutlinedTextField(
                value = email, onValueChange = { email = it },
                label = { Text("Email") },
                leadingIcon = { Icon(Icons.Filled.Email, contentDescription = null) },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = TextPrimary,
                    unfocusedTextColor = TextPrimary,
                )
            )
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(
                value = password, onValueChange = { password = it },
                label = { Text("Password") },
                leadingIcon = { Icon(Icons.Filled.Lock, contentDescription = null) },
                visualTransformation = PasswordVisualTransformation(),
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = TextPrimary,
                    unfocusedTextColor = TextPrimary,
                )
            )

            if (error != null) {
                Spacer(Modifier.height(10.dp))
                Text(error!!, color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodyMedium)
            }

            Spacer(Modifier.height(20.dp))
            PrimaryAction(
                text = if (loading) "Signing in…" else "Sign in",
                enabled = !loading && email.isNotBlank() && password.isNotBlank(),
                onClick = {
                    loading = true; error = null
                    scope.launch {
                        try {
                            val api = apiHolder.api
                                ?: run { error = "Not paired. Tap Unpair and re-scan."; loading = false; return@launch }
                            val resp = api.login(email.trim(), password)
                            // /login redirects (302) to /. Cookie jar caches the session cookie.
                            if (resp.code() == 302 || resp.isSuccessful) {
                                prefs.saveAuthEmail(email.trim())
                                // Pull a CSRF token for subsequent POST /api/sku/scan
                                repo.refreshCsrf()
                                onLoggedIn()
                            } else {
                                error = "Sign in failed (HTTP ${resp.code()}). Check credentials."
                            }
                        } catch (e: Exception) {
                            error = "Could not reach server: ${e.message ?: "network error"}"
                        } finally {
                            loading = false
                        }
                    }
                }
            )
            Spacer(Modifier.height(10.dp))
            SecondaryAction("Unpair this device", onClick = onUnpair)
        }

        Spacer(Modifier.weight(1f))
        Text(
            "Tip: in dev, Owner password is sunrise2024 · Salesman password is sales2024",
            style = MaterialTheme.typography.labelSmall.copy(color = TextSecondary),
            modifier = Modifier.fillMaxWidth().padding(24.dp),
        )
    }
}
