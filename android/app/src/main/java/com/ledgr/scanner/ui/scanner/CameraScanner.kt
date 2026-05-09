package com.ledgr.scanner.ui.scanner

import android.Manifest
import android.content.pm.PackageManager
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.google.mlkit.vision.barcode.BarcodeScanner
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import java.util.concurrent.Executors

/** Shape of the framing reticle. QR codes are square; retail barcodes
 *  (EAN/UPC/Code-128) are wide rectangles. Picking the right one matters
 *  for both UX and detection rate. */
enum class ReticleShape(val ratio: Float) {
    Square(1f),
    BarcodeWide(1.7f),
}

@androidx.annotation.OptIn(androidx.camera.core.ExperimentalGetImage::class)
@Composable
fun CameraScanner(
    modifier: Modifier = Modifier,
    formats: IntArray = intArrayOf(
        Barcode.FORMAT_EAN_13, Barcode.FORMAT_EAN_8, Barcode.FORMAT_UPC_A,
        Barcode.FORMAT_UPC_E, Barcode.FORMAT_CODE_128, Barcode.FORMAT_CODE_39,
        Barcode.FORMAT_QR_CODE, Barcode.FORMAT_ITF, Barcode.FORMAT_DATA_MATRIX,
    ),
    reticle: ReticleShape = ReticleShape.BarcodeWide,
    enabled: Boolean = true,
    onResult: (String) -> Unit,
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    val granted = remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA)
                == PackageManager.PERMISSION_GRANTED
        )
    }
    PermissionRequester(granted)

    Box(modifier = modifier.background(Color.Black)) {
        if (!granted.value) {
            // Camera permission not yet granted; viewfinder stays dark.
            return@Box
        }

        // ── Live camera preview ──
        AndroidView(
            modifier = Modifier
                .fillMaxSize()
                .clip(RoundedCornerShape(20.dp)),
            factory = { ctx ->
                PreviewView(ctx).apply { scaleType = PreviewView.ScaleType.FILL_CENTER }
            },
            update = { previewView ->
                if (!enabled) return@AndroidView
                val cameraProviderFuture = ProcessCameraProvider.getInstance(previewView.context)
                cameraProviderFuture.addListener({
                    try {
                        val provider = cameraProviderFuture.get()
                        val preview = Preview.Builder().build().also {
                            it.setSurfaceProvider(previewView.surfaceProvider)
                        }
                        val options = BarcodeScannerOptions.Builder()
                            .setBarcodeFormats(formats.first(), *formats.drop(1).toIntArray())
                            .build()
                        val scanner: BarcodeScanner = BarcodeScanning.getClient(options)
                        val analysisExec = Executors.newSingleThreadExecutor()

                        val analyzer = ImageAnalysis.Builder()
                            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                            .build()
                        analyzer.setAnalyzer(analysisExec) { proxy ->
                            val mediaImage = proxy.image
                            if (mediaImage != null) {
                                val image = InputImage.fromMediaImage(mediaImage, proxy.imageInfo.rotationDegrees)
                                scanner.process(image)
                                    .addOnSuccessListener { results ->
                                        results.firstOrNull()?.rawValue?.let { value ->
                                            onResult(value)
                                        }
                                    }
                                    .addOnCompleteListener { proxy.close() }
                            } else {
                                proxy.close()
                            }
                        }

                        provider.unbindAll()
                        provider.bindToLifecycle(
                            lifecycleOwner,
                            CameraSelector.DEFAULT_BACK_CAMERA,
                            preview,
                            analyzer,
                        )
                    } catch (_: Exception) { /* swallow — viewfinder stays dark */ }
                }, ContextCompat.getMainExecutor(previewView.context))
            }
        )

        // ── Industrial overlay: dim outside the reticle, corner brackets,
        //    sweeping scan line. Aspect ratio matches the code type. ──
        ReticleOverlay(reticle = reticle)
    }
}

@Composable
private fun BoxScope.ReticleOverlay(reticle: ReticleShape) {
    val transition = rememberInfiniteTransition(label = "scanline")
    val sweep by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 1800),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "scanline-sweep",
    )

    val gold = Color(0xFFFACC15)
    val dim = Color(0xCC000000)

    val widthFraction = if (reticle == ReticleShape.Square) 0.62f else 0.84f

    Box(
        modifier = Modifier
            .fillMaxWidth(widthFraction)
            .aspectRatio(reticle.ratio)
            .align(Alignment.Center)
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val cornerLen = size.minDimension * 0.18f
            val stroke = 4.dp.toPx()
            val r = 12.dp.toPx()

            // Four L-shaped corner brackets.
            // Top-left
            drawLine(gold, Offset(0f, r + cornerLen), Offset(0f, r), stroke)
            drawArc(
                color = gold, startAngle = 180f, sweepAngle = 90f, useCenter = false,
                topLeft = Offset(0f, 0f), size = Size(2 * r, 2 * r),
                style = Stroke(width = stroke),
            )
            drawLine(gold, Offset(r, 0f), Offset(r + cornerLen, 0f), stroke)
            // Top-right
            drawLine(gold, Offset(size.width - r - cornerLen, 0f), Offset(size.width - r, 0f), stroke)
            drawArc(
                color = gold, startAngle = 270f, sweepAngle = 90f, useCenter = false,
                topLeft = Offset(size.width - 2 * r, 0f), size = Size(2 * r, 2 * r),
                style = Stroke(width = stroke),
            )
            drawLine(gold, Offset(size.width, r), Offset(size.width, r + cornerLen), stroke)
            // Bottom-right
            drawLine(gold, Offset(size.width, size.height - r - cornerLen), Offset(size.width, size.height - r), stroke)
            drawArc(
                color = gold, startAngle = 0f, sweepAngle = 90f, useCenter = false,
                topLeft = Offset(size.width - 2 * r, size.height - 2 * r), size = Size(2 * r, 2 * r),
                style = Stroke(width = stroke),
            )
            drawLine(gold, Offset(size.width - r, size.height), Offset(size.width - r - cornerLen, size.height), stroke)
            // Bottom-left
            drawLine(gold, Offset(r, size.height), Offset(r + cornerLen, size.height), stroke)
            drawArc(
                color = gold, startAngle = 90f, sweepAngle = 90f, useCenter = false,
                topLeft = Offset(0f, size.height - 2 * r), size = Size(2 * r, 2 * r),
                style = Stroke(width = stroke),
            )
            drawLine(gold, Offset(0f, size.height - r), Offset(0f, size.height - r - cornerLen), stroke)

            // Sweeping scan line — fading gradient, soft glow at the edge.
            val y = size.height * sweep
            drawRect(
                brush = Brush.verticalGradient(
                    colors = listOf(gold.copy(alpha = 0f), gold.copy(alpha = 0.25f), gold.copy(alpha = 0f)),
                    startY = y - 22f,
                    endY = y + 22f,
                ),
                topLeft = Offset(stroke, y - 22f),
                size = Size(size.width - 2 * stroke, 44f),
            )
            drawLine(gold.copy(alpha = 0.85f),
                Offset(stroke + 6f, y), Offset(size.width - stroke - 6f, y), 1.5f)
        }
    }
}

@Composable
private fun PermissionRequester(state: MutableState<Boolean>) {
    val launcher = androidx.activity.compose.rememberLauncherForActivityResult(
        contract = androidx.activity.result.contract.ActivityResultContracts.RequestPermission()
    ) { isGranted -> state.value = isGranted }
    LaunchedEffect(Unit) { if (!state.value) launcher.launch(Manifest.permission.CAMERA) }
}
