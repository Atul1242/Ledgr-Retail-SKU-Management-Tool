package com.ledgr.scanner

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.ledgr.scanner.data.ScanRepository
import com.ledgr.scanner.ui.theme.LedgrTheme
import com.ledgr.scanner.ui.login.LoginScreen
import com.ledgr.scanner.ui.pairing.PairingScreen
import com.ledgr.scanner.ui.scanner.ScannerScreen
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setTheme(R.style.Theme_LedgrScanner)
        setContent { LedgrTheme { Root() } }
    }
}

@Composable
private fun Root() {
    val container = (LocalContext.current.applicationContext as LedgrApp).container
    val scope = rememberCoroutineScope()
    val nav = rememberNavController()

    val serverUrl by container.prefs.serverUrlFlow.collectAsState(initial = null)
    val authEmail by container.prefs.authEmailFlow.collectAsState(initial = null)

    val scanRepo = remember { ScanRepository(container.db, container.prefs, container.apiHolder) }

    // Reactively rebuild Retrofit when the paired URL changes.
    LaunchedEffect(serverUrl) {
        serverUrl?.takeIf { it.isNotBlank() }?.let { container.apiHolder.rebuild(it) }
    }

    val start = when {
        serverUrl.isNullOrBlank() -> "pair"
        authEmail.isNullOrBlank()  -> "login"
        else                       -> "scanner"
    }

    Surface(modifier = Modifier.fillMaxSize()) {
        NavHost(navController = nav, startDestination = start) {
            composable("pair") {
                PairingScreen(
                    onPaired = { url, name ->
                        scope.launch {
                            container.prefs.saveServer(url, name)
                            container.apiHolder.rebuild(url)
                            nav.navigate("login") { popUpTo("pair") { inclusive = true } }
                        }
                    }
                )
            }
            composable("login") {
                LoginScreen(
                    apiHolder = container.apiHolder,
                    prefs = container.prefs,
                    repo = scanRepo,
                    onLoggedIn = {
                        nav.navigate("scanner") { popUpTo("login") { inclusive = true } }
                    },
                    onUnpair = {
                        scope.launch {
                            container.prefs.clearAll()
                            container.apiHolder.signOut()
                            nav.navigate("pair") { popUpTo("login") { inclusive = true } }
                        }
                    }
                )
            }
            composable("scanner") {
                ScannerScreen(
                    repo = scanRepo,
                    apiHolder = container.apiHolder,
                    prefs = container.prefs,
                    onSignOut = {
                        scope.launch {
                            container.apiHolder.signOut()
                            container.prefs.clearAll()
                            nav.navigate("pair") { popUpTo("scanner") { inclusive = true } }
                        }
                    }
                )
            }
        }
    }
}
