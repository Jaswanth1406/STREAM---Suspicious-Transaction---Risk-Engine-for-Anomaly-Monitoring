package com.example.stream.ui.vendor

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.stream.data.model.VendorProfile
import com.example.stream.ui.components.*
import com.example.stream.ui.theme.*

@Composable
fun VendorScreen(vendorId: String, onBack: () -> Unit, vm: VendorViewModel = viewModel()) {
    LaunchedEffect(vendorId) { vm.loadVendor(vendorId) }
    val state by vm.profile.collectAsState()

    Box(Modifier.fillMaxSize()) {
        AnimatedGradientBackground()
        Column(Modifier.fillMaxSize().statusBarsPadding()) {
            // Top bar
            Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onBack) {
                    Icon(Icons.Default.ArrowBack, null, tint = StreamPurple)
                }
                Text("Vendor Profile", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 20.sp)
            }

            when (val s = state) {
                is UiState.Loading -> LoadingScreen()
                is UiState.Error -> ErrorScreen(s.message) { vm.loadVendor(vendorId) }
                is UiState.Success -> VendorContent(s.data)
            }
        }
    }
}

@Composable
fun VendorContent(vendor: VendorProfile) {
    Column(Modifier.verticalScroll(rememberScrollState()).padding(horizontal = 16.dp)) {
        // Header card
        GlassCard {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.Top) {
                Column(Modifier.weight(1f)) {
                    Text(vendor.companyName, color = StreamDark, fontWeight = FontWeight.ExtraBold, fontSize = 18.sp)
                    Spacer(Modifier.height(4.dp))
                    Text(vendor.cin, color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp)
                    Text("${vendor.industry} · ${vendor.status}", color = StreamDark.copy(alpha = 0.6f), fontSize = 13.sp)
                }
                RiskBadge(vendor.riskTier)
            }
            Spacer(Modifier.height(12.dp))
            // Overall Risk Score
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column {
                    Text("Risk Score", color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp)
                    Text("${vendor.overallRiskScore}/100", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 24.sp)
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text("Tenders", color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp)
                    Text("${vendor.totalTenders}", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 20.sp)
                }
            }
        }
        Spacer(Modifier.height(12.dp))

        // Sub-scores
        GlassCard {
            Text("Risk Sub-Scores", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 16.sp)
            Spacer(Modifier.height(12.dp))
            SubScoreBar("Bid Pattern", vendor.subScores.bidPattern)
            SubScoreBar("Shell Risk", vendor.subScores.shellRisk)
            SubScoreBar("Political", vendor.subScores.political)
            SubScoreBar("Financials", vendor.subScores.financials)
        }
        Spacer(Modifier.height(12.dp))

        // Connections
        if (vendor.connections.isNotEmpty()) {
            GlassCard {
                Text("Connections (${vendor.connectionsCount})", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                Spacer(Modifier.height(8.dp))
                vendor.connections.forEach { conn ->
                    Row(
                        Modifier.fillMaxWidth().padding(vertical = 6.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(Modifier.weight(1f)) {
                            Text(conn.entityName, color = StreamDark, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                            Text(conn.detail, color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp)
                        }
                        RiskBadge(conn.riskLevel)
                    }
                }
            }
        }
        Spacer(Modifier.height(12.dp))

        // Recent Tenders
        if (vendor.recentTenders.isNotEmpty()) {
            GlassCard {
                Text("Recent Tenders", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                Spacer(Modifier.height(8.dp))
                vendor.recentTenders.forEach { t ->
                    Row(
                        Modifier.fillMaxWidth().padding(vertical = 6.dp),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column(Modifier.weight(1f)) {
                            Text(t.title, color = StreamDark, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                            Text(t.date, color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp)
                        }
                        Text("${t.riskScore}", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 16.sp)
                    }
                }
            }
        }
        Spacer(Modifier.height(80.dp))
    }
}

@Composable
fun SubScoreBar(label: String, score: Int) {
    val color = when {
        score >= 70 -> HighRisk
        score >= 40 -> MediumRisk
        else -> LowRisk
    }
    Row(
        Modifier.fillMaxWidth().padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(label, color = StreamDark.copy(alpha = 0.7f), fontSize = 13.sp, modifier = Modifier.width(90.dp))
        LinearProgressIndicator(
            progress = { score / 100f },
            modifier = Modifier.weight(1f).height(8.dp),
            color = color,
            trackColor = Color.White.copy(alpha = 0.3f)
        )
        Spacer(Modifier.width(8.dp))
        Text("$score", color = color, fontWeight = FontWeight.Bold, fontSize = 14.sp)
    }
}
