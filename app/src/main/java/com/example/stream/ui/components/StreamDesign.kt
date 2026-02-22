package com.example.stream.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowLeft
import androidx.compose.material.icons.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.stream.ui.theme.*

sealed class UiState<out T> {
    object Loading : UiState<Nothing>()
    data class Success<T>(val data: T) : UiState<T>()
    data class Error(val message: String) : UiState<Nothing>()
}

@Composable
fun GlassCard(modifier: Modifier = Modifier, cornerRadius: Dp = 20.dp, content: @Composable ColumnScope.() -> Unit) {
    Card(modifier = modifier, shape = RoundedCornerShape(cornerRadius), colors = CardDefaults.cardColors(containerColor = Color.White.copy(alpha = 0.4f)), elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)) {
        Box(modifier = Modifier.fillMaxWidth().border(1.dp, Color.White.copy(alpha = 0.6f), RoundedCornerShape(cornerRadius))) {
            Column(modifier = Modifier.padding(16.dp).fillMaxWidth(), content = content)
        }
    }
}

@Composable
fun RiskBadge(riskTier: String, modifier: Modifier = Modifier) {
    val (color, label) = when {
        riskTier.contains("High", true) -> HighRisk to "HIGH"
        riskTier.contains("Medium", true) -> MediumRisk to "MEDIUM"
        else -> LowRisk to "LOW"
    }
    Surface(modifier = modifier, shape = RoundedCornerShape(8.dp), color = color.copy(alpha = 0.15f)) {
        Text(text = label, color = color, fontSize = 11.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp))
    }
}

@Composable
fun KpiCard(title: String, value: String, subtitle: String = "", modifier: Modifier = Modifier) {
    GlassCard(modifier = modifier, cornerRadius = 16.dp) {
        Text(title, color = StreamDark.copy(alpha = 0.6f), fontSize = 12.sp, fontWeight = FontWeight.Medium)
        Spacer(Modifier.height(4.dp))
        Text(value, color = StreamDark, fontSize = 22.sp, fontWeight = FontWeight.ExtraBold)
        if (subtitle.isNotEmpty()) { Spacer(Modifier.height(2.dp)); Text(subtitle, color = StreamPurple.copy(alpha = 0.7f), fontSize = 11.sp, fontWeight = FontWeight.SemiBold) }
    }
}

@Composable
fun PaginationBar(currentPage: Int, totalPages: Int, totalItems: Int, onPrev: () -> Unit, onNext: () -> Unit, modifier: Modifier = Modifier) {
    Row(modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).background(Color.White.copy(alpha = 0.4f)).border(1.dp, Color.White.copy(alpha = 0.6f), RoundedCornerShape(14.dp)).padding(horizontal = 12.dp, vertical = 8.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
        IconButton(onClick = onPrev, enabled = currentPage > 1, modifier = Modifier.size(36.dp)) { Icon(Icons.Default.KeyboardArrowLeft, "Previous", tint = if (currentPage > 1) StreamPurple else StreamDark.copy(alpha = 0.2f), modifier = Modifier.size(24.dp)) }
        Column(horizontalAlignment = Alignment.CenterHorizontally) { Text("Page $currentPage of $totalPages", color = StreamDark, fontSize = 13.sp, fontWeight = FontWeight.Bold); Text("$totalItems total items", color = StreamDark.copy(alpha = 0.5f), fontSize = 11.sp) }
        IconButton(onClick = onNext, enabled = currentPage < totalPages, modifier = Modifier.size(36.dp)) { Icon(Icons.Default.KeyboardArrowRight, "Next", tint = if (currentPage < totalPages) StreamPurple else StreamDark.copy(alpha = 0.2f), modifier = Modifier.size(24.dp)) }
    }
}

@Composable
fun GlassFilterChip(label: String, selected: Boolean, onClick: () -> Unit) {
    FilterChip(selected = selected, onClick = onClick, label = { Text(label, fontSize = 12.sp, fontWeight = FontWeight.SemiBold) }, colors = FilterChipDefaults.filterChipColors(selectedContainerColor = StreamPurple.copy(alpha = 0.7f), selectedLabelColor = Color.White, containerColor = Color.White.copy(alpha = 0.4f), labelColor = StreamDark), border = FilterChipDefaults.filterChipBorder(borderColor = Color.White.copy(alpha = 0.6f), enabled = true, selected = false), shape = RoundedCornerShape(12.dp))
}

@Composable
fun SortChip(label: String, isDesc: Boolean?, onClick: () -> Unit) {
    val arrow = when (isDesc) { true -> " v"; false -> " ^"; null -> "" }
    FilterChip(selected = isDesc != null, onClick = onClick, label = { Text("$label$arrow", fontSize = 12.sp, fontWeight = FontWeight.SemiBold) }, colors = FilterChipDefaults.filterChipColors(selectedContainerColor = StreamLavender.copy(alpha = 0.5f), selectedLabelColor = StreamDark, containerColor = Color.White.copy(alpha = 0.3f), labelColor = StreamDark.copy(alpha = 0.6f)), border = FilterChipDefaults.filterChipBorder(borderColor = Color.White.copy(alpha = 0.5f), enabled = true, selected = false), shape = RoundedCornerShape(12.dp))
}

@Composable
fun AnimatedGradientBackground(modifier: Modifier = Modifier) {
    val infiniteTransition = rememberInfiniteTransition(label = "bg")
    val b1X by infiniteTransition.animateFloat(-100f, 200f, infiniteRepeatable(tween(18000), RepeatMode.Reverse), "b1x")
    val b1Y by infiniteTransition.animateFloat(-50f, 300f, infiniteRepeatable(tween(15000, easing = FastOutSlowInEasing), RepeatMode.Reverse), "b1y")
    val b2X by infiniteTransition.animateFloat(300f, -50f, infiniteRepeatable(tween(22000), RepeatMode.Reverse), "b2x")
    val b2Y by infiniteTransition.animateFloat(500f, 100f, infiniteRepeatable(tween(19000, easing = FastOutSlowInEasing), RepeatMode.Reverse), "b2y")
    val b3X by infiniteTransition.animateFloat(100f, -100f, infiniteRepeatable(tween(20000), RepeatMode.Reverse), "b3x")
    val b3Y by infiniteTransition.animateFloat(100f, 500f, infiniteRepeatable(tween(17000, easing = FastOutSlowInEasing), RepeatMode.Reverse), "b3y")
    Box(modifier.fillMaxSize().background(StreamCream)) {
        Box(Modifier.offset(b1X.dp, b1Y.dp).size(400.dp).clip(CircleShape).background(Brush.radialGradient(listOf(StreamLavender.copy(0.4f), Color.Transparent))))
        Box(Modifier.offset(b2X.dp, b2Y.dp).size(350.dp).clip(CircleShape).background(Brush.radialGradient(listOf(StreamPeach.copy(0.5f), Color.Transparent))))
        Box(Modifier.offset(b3X.dp, b3Y.dp).size(450.dp).clip(CircleShape).background(Brush.radialGradient(listOf(StreamPurple.copy(0.25f), Color.Transparent))))
    }
}

@Composable
fun LoadingScreen() { Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator(color = StreamPurple, strokeWidth = 3.dp) } }

@Composable
fun ErrorScreen(message: String, onRetry: () -> Unit) {
    Box(Modifier.fillMaxSize().padding(32.dp), contentAlignment = Alignment.Center) {
        GlassCard {
            Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
                Text("!", fontSize = 40.sp)
                Spacer(Modifier.height(12.dp))
                Text("Something went wrong", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                Spacer(Modifier.height(8.dp))
                Text(message, color = StreamDark.copy(alpha = 0.7f), fontSize = 14.sp, textAlign = TextAlign.Center)
                Spacer(Modifier.height(16.dp))
                Button(onClick = onRetry, colors = ButtonDefaults.buttonColors(containerColor = StreamPurple.copy(alpha = 0.7f)), shape = RoundedCornerShape(12.dp), modifier = Modifier.border(1.dp, Color.White.copy(alpha = 0.5f), RoundedCornerShape(12.dp))) {
                    Icon(Icons.Default.Refresh, null, tint = Color.White, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Retry", color = Color.White, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}