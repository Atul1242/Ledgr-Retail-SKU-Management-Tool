package com.ledgr.scanner.ui.pairing

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ledgr.scanner.ui.components.PanelCard
import com.ledgr.scanner.ui.components.PrimaryAction
import com.ledgr.scanner.ui.components.ScreenHeader
import com.ledgr.scanner.ui.components.SecondaryAction
import com.ledgr.scanner.ui.scanner.CameraScanner
import com.ledgr.scanner.ui.scanner.ReticleShape
import com.ledgr.scanner.ui.theme.LedgrNavy
import com.ledgr.scanner.ui.theme.TextPrimary
import com.ledgr.scanner.ui.theme.TextSecondary
import com.ledgr.scanner.util.QrPayload

@Composable
fun PairingScreen(onPaired: (url: String, name: String?) -> Unit) {
    var mode by remember { mutableStateOf(Mode.Camera) }
    var manualUrl by remember { mutableStateOf("http://192.168.1.10:5000") }
    var error by remember { mutableStateOf<String?>(null) }
    var lastScanned by remember { mutableStateOf<String?>(null) }

    Column(modifier = Modifier.fillMaxSize().background(LedgrNavy)) {
        ScreenHeader(
            eyebrow = "Step 1 of 2",
            title = "Pair this device",
            subtitle = "On your Ledgr server, open SKU Management → Add via Barcode and scan the QR code shown there. Or enter the server URL by hand."
        )

        when (mode) {
            Mode.Camera -> {
                Box(modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp)
                    .aspectRatio(1f)               // QR is square
                    .clip(RoundedCornerShape(20.dp))
                ) {
                    CameraScanner(
                        modifier = Modifier.fillMaxSize(),
                        reticle = ReticleShape.Square,
                        onResult = { value ->
                            if (value == lastScanned) return@CameraScanner
                            lastScanned = value
                            val parsed = QrPayload.parse(value)
                            if (parsed != null) onPaired(parsed.baseUrl, parsed.name)
                            else error = "QR didn't look like a Ledgr server URL — try Manual."
                        }
                    )
                }
                if (error != null) {
                    Spacer(Modifier.height(8.dp))
                    Text(error!!, color = MaterialTheme.colorScheme.error,
                        modifier = Modifier.padding(horizontal = 24.dp))
                }
                Spacer(Modifier.height(20.dp))
                Column(modifier = Modifier.padding(horizontal = 24.dp)) {
                    SecondaryAction("Enter server URL manually", onClick = { mode = Mode.Manual })
                }
            }
            Mode.Manual -> {
                PanelCard(modifier = Modifier.padding(horizontal = 24.dp)) {
                    Text("Server URL", style = MaterialTheme.typography.labelLarge.copy(color = TextSecondary))
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(
                        value = manualUrl,
                        onValueChange = { manualUrl = it; error = null },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        placeholder = { Text("http://192.168.1.10:5000") },
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedTextColor = TextPrimary,
                            unfocusedTextColor = TextPrimary,
                        )
                    )
                    if (error != null) {
                        Spacer(Modifier.height(8.dp))
                        Text(error!!, color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodyMedium)
                    }
                    Spacer(Modifier.height(20.dp))
                    PrimaryAction("Pair", onClick = {
                        val parsed = QrPayload.parse(manualUrl.trim())
                        if (parsed != null) onPaired(parsed.baseUrl, null)
                        else error = "Enter a full http(s)://… URL."
                    })
                    Spacer(Modifier.height(10.dp))
                    SecondaryAction("Use camera instead", onClick = { mode = Mode.Camera })
                }
            }
        }

        Spacer(Modifier.weight(1f))

        Text(
            "Ledgr Scanner · industrial barcode capture for FMCG distributors",
            style = MaterialTheme.typography.labelSmall.copy(color = TextSecondary, fontWeight = FontWeight.Medium),
            modifier = Modifier.fillMaxWidth().padding(24.dp),
        )
    }
}

private enum class Mode { Camera, Manual }
