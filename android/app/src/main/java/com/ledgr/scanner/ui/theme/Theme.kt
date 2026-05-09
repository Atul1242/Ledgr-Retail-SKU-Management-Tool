package com.ledgr.scanner.ui.theme

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.view.WindowCompat
import android.app.Activity

// ── Industrial palette ──
val LedgrGold = Color(0xFFFACC15)
val LedgrGoldDim = Color(0xFFCA8A04)
val LedgrNavy = Color(0xFF0D1B2A)
val LedgrNavy2 = Color(0xFF1E293B)
val LedgrSlate = Color(0xFF334155)
val LedgrSurface = Color(0xFF111827)
val LedgrSurfaceVariant = Color(0xFF1F2937)
val LedgrOutline = Color(0xFF374151)
val TextPrimary = Color(0xFFF8FAFC)
val TextSecondary = Color(0xFF94A3B8)
val Success = Color(0xFF22C55E)
val Warning = Color(0xFFF59E0B)
val Danger = Color(0xFFEF4444)

private val LedgrColors = darkColorScheme(
    primary = LedgrGold,
    onPrimary = LedgrNavy,
    primaryContainer = LedgrGoldDim,
    onPrimaryContainer = TextPrimary,
    secondary = LedgrSlate,
    onSecondary = TextPrimary,
    background = LedgrNavy,
    onBackground = TextPrimary,
    surface = LedgrSurface,
    onSurface = TextPrimary,
    surfaceVariant = LedgrSurfaceVariant,
    onSurfaceVariant = TextSecondary,
    outline = LedgrOutline,
    error = Danger,
    onError = TextPrimary,
)

private val LedgrTypography = Typography(
    displayLarge = TextStyle(fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.Bold, fontSize = 32.sp, letterSpacing = (-0.4).sp),
    headlineSmall = TextStyle(fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.SemiBold, fontSize = 22.sp, letterSpacing = (-0.2).sp),
    titleLarge = TextStyle(fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.SemiBold, fontSize = 18.sp),
    titleMedium = TextStyle(fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.SemiBold, fontSize = 15.sp),
    bodyLarge = TextStyle(fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.Normal, fontSize = 15.sp),
    bodyMedium = TextStyle(fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.Normal, fontSize = 14.sp, color = TextSecondary),
    labelLarge = TextStyle(fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, letterSpacing = 0.5.sp),
    labelSmall = TextStyle(fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.SemiBold, fontSize = 11.sp, letterSpacing = 0.6.sp),
)

private val LedgrShapes = Shapes(
    extraSmall = RoundedCornerShape(4.dp),
    small = RoundedCornerShape(8.dp),
    medium = RoundedCornerShape(12.dp),
    large = RoundedCornerShape(16.dp),
    extraLarge = RoundedCornerShape(24.dp),
)

@Composable
fun LedgrTheme(content: @Composable () -> Unit) {
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            (view.context as? Activity)?.window?.let { w ->
                w.statusBarColor = LedgrNavy.toArgb()
                w.navigationBarColor = LedgrNavy.toArgb()
                WindowCompat.getInsetsController(w, view).isAppearanceLightStatusBars = false
            }
        }
    }
    MaterialTheme(
        colorScheme = LedgrColors,
        typography = LedgrTypography,
        shapes = LedgrShapes,
        content = content,
    )
}
