package com.ledgr.scanner.ui.scanner

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.ledgr.scanner.data.ScanRepository
import com.ledgr.scanner.data.api.ApiHolder
import com.ledgr.scanner.data.api.ScanRequest
import com.ledgr.scanner.data.db.ScanRow
import com.ledgr.scanner.data.prefs.AppPrefs
import com.ledgr.scanner.ui.components.*
import com.ledgr.scanner.ui.theme.*
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun ScannerScreen(
    repo: ScanRepository,
    apiHolder: ApiHolder,
    prefs: AppPrefs,
    onSignOut: () -> Unit,
) {
    val scope = rememberCoroutineScope()
    val authEmail by prefs.authEmailFlow.collectAsState(initial = null)
    val pairedName by prefs.serverNameFlow.collectAsState(initial = null)
    val pairedUrl by prefs.serverUrlFlow.collectAsState(initial = null)

    val recent by repo.recent().collectAsState(initial = emptyList())
    val pending by repo.pendingCount().collectAsState(initial = 0)

    var pendingBarcode by remember { mutableStateOf<String?>(null) }
    var lastDetected by remember { mutableStateOf<String?>(null) }
    var qty by remember { mutableStateOf("1") }
    var toast by remember { mutableStateOf<String?>(null) }
    var syncing by remember { mutableStateOf(false) }

    Column(modifier = Modifier.fillMaxSize().background(LedgrNavy)) {
        // ── Top bar ──
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text("LEDGR SCANNER",
                    style = MaterialTheme.typography.labelSmall.copy(color = LedgrGold, fontWeight = FontWeight.Bold))
                Text(authEmail ?: "—",
                    style = MaterialTheme.typography.bodyMedium.copy(color = TextPrimary),
                    maxLines = 1)
                Text(pairedName ?: pairedUrl ?: "—",
                    style = MaterialTheme.typography.labelSmall.copy(color = TextSecondary),
                    maxLines = 1)
            }
            StatusPill(if (pending > 0) "$pending QUEUED" else "READY",
                if (pending > 0) PillKind.WARN else PillKind.OK)
            Spacer(Modifier.width(8.dp))
            IconButton(onClick = onSignOut) {
                Icon(Icons.Filled.Logout, contentDescription = "Sign out", tint = TextSecondary)
            }
        }

        // ── Camera viewfinder ──
        Box(modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp)
            .height(280.dp)
            .clip(RoundedCornerShape(20.dp))
            .background(Color.Black)
        ) {
            CameraScanner(
                modifier = Modifier.fillMaxSize(),
                reticle = ReticleShape.BarcodeWide,
                enabled = pendingBarcode == null,
                onResult = { value ->
                    if (value == lastDetected || pendingBarcode != null) return@CameraScanner
                    lastDetected = value
                    pendingBarcode = value
                    qty = "1"
                }
            )
            // Hint overlay
            Text(
                "Hold steady · frame the barcode",
                style = MaterialTheme.typography.labelSmall.copy(color = TextSecondary),
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .padding(12.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(Color(0xCC0D1B2A))
                    .padding(horizontal = 8.dp, vertical = 4.dp)
            )
        }
        Spacer(Modifier.height(12.dp))

        // ── Confirm panel (slides up after a scan) ──
        if (pendingBarcode != null) {
            PanelCard(modifier = Modifier.padding(horizontal = 16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Filled.QrCode2, contentDescription = null, tint = LedgrGold)
                    Spacer(Modifier.width(8.dp))
                    Text("Detected", style = MaterialTheme.typography.labelLarge.copy(color = TextSecondary))
                    Spacer(Modifier.weight(1f))
                    StatusPill("BARCODE", PillKind.INFO)
                }
                Spacer(Modifier.height(8.dp))
                Text(pendingBarcode!!,
                    style = MaterialTheme.typography.titleLarge.copy(color = TextPrimary, fontWeight = FontWeight.SemiBold))
                Spacer(Modifier.height(16.dp))
                OutlinedTextField(
                    value = qty,
                    onValueChange = { qty = it.filter { c -> c.isDigit() } },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Quantity received") },
                    leadingIcon = { Icon(Icons.Filled.Inventory2, contentDescription = null) },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                    )
                )
                Spacer(Modifier.height(16.dp))
                Row {
                    OutlinedButton(
                        modifier = Modifier.weight(1f).height(48.dp),
                        shape = RoundedCornerShape(12.dp),
                        onClick = {
                            pendingBarcode = null
                            lastDetected = null
                        }
                    ) { Text("Discard", color = TextPrimary) }
                    Spacer(Modifier.width(10.dp))
                    Button(
                        modifier = Modifier.weight(2f).height(48.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = LedgrGold,
                            contentColor = LedgrNavy,
                        ),
                        onClick = {
                            val sku = pendingBarcode ?: return@Button
                            val q = qty.toIntOrNull()?.coerceAtLeast(1) ?: 1
                            scope.launch {
                                val (_, ok) = repo.captureScan(ScanRequest(sku_code = sku, qty_received = q))
                                toast = if (ok) "Synced · $sku +$q" else "Saved offline · will sync when online"
                                pendingBarcode = null
                                // Allow re-detecting the same code after a short cool-down
                                kotlinx.coroutines.delay(800)
                                lastDetected = null
                            }
                        }
                    ) {
                        Icon(Icons.Filled.Check, contentDescription = null)
                        Spacer(Modifier.width(6.dp))
                        Text("Confirm & save", fontWeight = FontWeight.Bold)
                    }
                }
            }
            Spacer(Modifier.height(12.dp))
        }

        // ── Sync row ──
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                if (pending == 0) "Recent scans"
                else "$pending unsynced — tap Sync now",
                style = MaterialTheme.typography.labelLarge.copy(color = TextSecondary, fontWeight = FontWeight.SemiBold)
            )
            Spacer(Modifier.weight(1f))
            TextButton(
                enabled = !syncing && pending > 0,
                onClick = {
                    syncing = true
                    scope.launch {
                        repo.refreshCsrf()
                        val (ok, fail) = repo.drainQueue()
                        toast = "Synced $ok · failed $fail"
                        syncing = false
                    }
                }
            ) {
                Icon(Icons.Filled.Sync, contentDescription = null)
                Spacer(Modifier.width(6.dp))
                Text("Sync now")
            }
        }

        // ── Recent scans list ──
        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            if (recent.isEmpty()) {
                item {
                    Box(
                        modifier = Modifier.fillMaxWidth().padding(vertical = 32.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text("No scans yet · frame a barcode to begin",
                            style = MaterialTheme.typography.bodyMedium.copy(color = TextSecondary))
                    }
                }
            } else {
                items(recent) { row -> ScanRowItem(row) }
            }
        }

        // Tiny inline toast (last action). The Snackbar would steal focus; this is unobtrusive.
        if (toast != null) {
            LaunchedEffect(toast) {
                kotlinx.coroutines.delay(2200)
                toast = null
            }
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                contentAlignment = Alignment.Center,
            ) {
                Text(toast ?: "",
                    modifier = Modifier
                        .clip(RoundedCornerShape(20.dp))
                        .background(LedgrGold)
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    color = LedgrNavy,
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.labelLarge)
            }
        }
    }
}

@Composable
private fun ScanRowItem(row: ScanRow) {
    val time = remember(row.scanned_at) {
        SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date(row.scanned_at))
    }
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(LedgrSurface)
            .padding(12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            imageVector = if (row.synced) Icons.Filled.CloudDone else Icons.Filled.CloudUpload,
            contentDescription = null,
            tint = if (row.synced) Success else Warning,
            modifier = Modifier.size(20.dp)
        )
        Spacer(Modifier.width(10.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(row.sku_code,
                style = MaterialTheme.typography.bodyLarge.copy(color = TextPrimary, fontWeight = FontWeight.SemiBold),
                maxLines = 1)
            Text("${row.qty_received} units · $time" + (row.error?.let { " · $it" } ?: ""),
                style = MaterialTheme.typography.labelSmall.copy(color = TextSecondary), maxLines = 1)
        }
        if (!row.synced) StatusPill("QUEUED", PillKind.WARN)
        else StatusPill("SYNCED", PillKind.OK)
    }
}
