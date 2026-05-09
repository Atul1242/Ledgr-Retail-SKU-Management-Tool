package com.ledgr.scanner.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Circle
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ledgr.scanner.ui.theme.Danger
import com.ledgr.scanner.ui.theme.LedgrGold
import com.ledgr.scanner.ui.theme.LedgrSurface
import com.ledgr.scanner.ui.theme.LedgrSurfaceVariant
import com.ledgr.scanner.ui.theme.Success
import com.ledgr.scanner.ui.theme.TextPrimary
import com.ledgr.scanner.ui.theme.TextSecondary
import com.ledgr.scanner.ui.theme.Warning

/** Section header used at the top of every screen. */
@Composable
fun ScreenHeader(eyebrow: String, title: String, subtitle: String? = null) {
    Column(modifier = Modifier.fillMaxWidth().padding(start = 24.dp, end = 24.dp, top = 24.dp, bottom = 16.dp)) {
        Text(eyebrow.uppercase(),
            style = MaterialTheme.typography.labelSmall.copy(color = LedgrGold, fontWeight = FontWeight.Bold))
        Spacer(Modifier.height(6.dp))
        Text(title, style = MaterialTheme.typography.headlineSmall.copy(color = TextPrimary))
        if (subtitle != null) {
            Spacer(Modifier.height(6.dp))
            Text(subtitle, style = MaterialTheme.typography.bodyMedium.copy(color = TextSecondary))
        }
    }
}

/** Consistent surface card used across the app. */
@Composable
fun PanelCard(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(LedgrSurface)
            .border(1.dp, LedgrSurfaceVariant, RoundedCornerShape(16.dp))
            .padding(20.dp),
        content = content,
    )
}

/** Primary CTA button — gold-on-navy, full width. */
@Composable
fun PrimaryAction(
    text: String,
    onClick: () -> Unit,
    enabled: Boolean = true,
    modifier: Modifier = Modifier,
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier.fillMaxWidth().height(52.dp),
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = LedgrGold,
            contentColor = Color(0xFF0D1B2A),
            disabledContainerColor = LedgrSurfaceVariant,
            disabledContentColor = TextSecondary,
        )
    ) {
        Text(text, fontWeight = FontWeight.Bold)
    }
}

/** Secondary outlined button. */
@Composable
fun SecondaryAction(
    text: String,
    onClick: () -> Unit,
    enabled: Boolean = true,
    modifier: Modifier = Modifier,
) {
    OutlinedButton(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier.fillMaxWidth().height(52.dp),
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline),
    ) {
        Text(text, fontWeight = FontWeight.SemiBold, color = TextPrimary)
    }
}

/** Status pill for online/offline/queued states. */
@Composable
fun StatusPill(text: String, kind: PillKind) {
    val color = when (kind) {
        PillKind.OK -> Success
        PillKind.WARN -> Warning
        PillKind.ERR -> Danger
        PillKind.INFO -> LedgrGold
    }
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .background(color.copy(alpha = 0.12f))
            .border(1.dp, color.copy(alpha = 0.4f), RoundedCornerShape(20.dp))
            .padding(horizontal = 12.dp, vertical = 5.dp)
    ) {
        Icon(Icons.Filled.Circle, contentDescription = null, tint = color, modifier = Modifier.size(8.dp))
        Spacer(Modifier.width(6.dp))
        Text(text, style = MaterialTheme.typography.labelSmall.copy(color = color, fontWeight = FontWeight.Bold))
    }
}

enum class PillKind { OK, WARN, ERR, INFO }
