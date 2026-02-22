package com.example.stream.ui.bid

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.stream.data.model.BidTender
import com.example.stream.ui.components.*
import com.example.stream.ui.theme.*

@Composable
fun BidDetailScreen(onBack: () -> Unit) {
    val tender = SelectedTender.tender

    Box(Modifier.fillMaxSize()) {
        AnimatedGradientBackground()

        if (tender == null) {
            ErrorScreen("No tender selected") { onBack() }
        } else {
            Column(Modifier.fillMaxSize().statusBarsPadding()) {
                // Top bar
                Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, null, tint = StreamPurple)
                    }
                    Text("Bid Intelligence", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 20.sp)
                }

                Column(
                    Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp)
                ) {
                    BidDetailContent(tender)
                    Spacer(Modifier.height(80.dp))
                }
            }
        }
    }
}

@Composable
fun BidDetailContent(t: BidTender) {
    val amountCr = t.amount / 10_000_000.0

    // === Header Card ===
    GlassCard {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.Top) {
            Column(Modifier.weight(1f)) {
                Text(t.title, color = StreamDark, fontWeight = FontWeight.ExtraBold, fontSize = 16.sp)
                Spacer(Modifier.height(4.dp))
                Text(t.tenderId, color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp)
            }
            RiskBadge(t.riskTier)
        }
        Spacer(Modifier.height(8.dp))
        Text(t.buyerName, color = StreamDark.copy(alpha = 0.7f), fontSize = 14.sp, fontWeight = FontWeight.Medium)
        Text(t.category, color = StreamLavender, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
        Text("Method: ${t.procurementMethod}", color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp)
    }
    Spacer(Modifier.height(12.dp))

    // === Risk Score Gauge ===
    GlassCard {
        Text("Risk Analysis", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 16.sp)
        Spacer(Modifier.height(12.dp))

        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
            // Risk Score
            RiskGauge("Risk Score", t.riskScore, 100.0)
            // Anomaly Score
            RiskGauge("Anomaly", t.anomalyScore * 100, 100.0)
            // Suspicion
            RiskGauge("Suspicion", t.suspicionProbability * 100, 100.0)
        }
        Spacer(Modifier.height(12.dp))
        // Predicted tier
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) {
            Text("Predicted: ", color = StreamDark.copy(alpha = 0.6f), fontSize = 13.sp)
            RiskBadge(t.predictedRiskTier)
            if (t.predictedSuspicious == 1) {
                Spacer(Modifier.width(8.dp))
                Text("⚠️ Suspicious", color = HighRisk, fontWeight = FontWeight.Bold, fontSize = 13.sp)
            }
        }
    }
    Spacer(Modifier.height(12.dp))

    // === Key Metrics ===
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        KpiCard("Amount", "₹${String.format("%.1f", amountCr)}Cr", modifier = Modifier.weight(1f))
        KpiCard("Bidders", "${t.numTenderers.toInt()}", subtitle = if (t.numTenderers <= 1) "⚠️ Low" else "Normal", modifier = Modifier.weight(1f))
    }
    Spacer(Modifier.height(12.dp))
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        KpiCard("Duration", "${t.durationDays} days", modifier = Modifier.weight(1f))
        KpiCard("OCID", t.ocid.takeLast(15), modifier = Modifier.weight(1f))
    }
    Spacer(Modifier.height(12.dp))

    // === Flags Breakdown ===
    GlassCard {
        Text("Flag Analysis", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 16.sp)
        Spacer(Modifier.height(12.dp))
        FlagRow("🎯", "Single Bidder", t.flagSingleBidder == 1, "Only 1 bidder submitted")
        FlagRow("🚫", "Zero Bidders", t.flagZeroBidders == 1, "No bidders recorded")
        FlagRow("⏱️", "Short Window", t.flagShortWindow == 1, "Submission window too short")
        FlagRow("🔒", "Non-Open", t.flagNonOpen == 1, "Not open procurement")
        FlagRow("💰", "High Value", t.flagHighValue == 1, "Above 95th percentile value")
        FlagRow("🏢", "Buyer Concentration", t.flagBuyerConcentration == 1, "Buyer dominates >70%")
        FlagRow("🔢", "Round Amount", t.flagRoundAmount == 1, "Suspiciously round pricing")
        FlagRow("🤖", "ML Anomaly", t.mlAnomalyFlag == 1, "Statistical outlier detected")

        val totalFlags = t.flagSingleBidder + t.flagZeroBidders + t.flagShortWindow +
            t.flagNonOpen + t.flagHighValue + t.flagBuyerConcentration + t.flagRoundAmount + t.mlAnomalyFlag
        Spacer(Modifier.height(8.dp))
        Text("$totalFlags of 8 flags triggered", color = StreamPurple, fontWeight = FontWeight.Bold, fontSize = 13.sp)
    }
    Spacer(Modifier.height(12.dp))

    // === Risk Explanation ===
    if (t.riskExplanation.isNotEmpty()) {
        GlassCard {
            Text("Risk Explanation", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 16.sp)
            Spacer(Modifier.height(8.dp))
            val reasons = t.riskExplanation.split(";").map { it.trim() }.filter { it.isNotEmpty() }
            reasons.forEach { reason ->
                Row(Modifier.padding(vertical = 4.dp)) {
                    Text("•", color = HighRisk, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    Spacer(Modifier.width(8.dp))
                    Text(reason, color = StreamDark.copy(alpha = 0.8f), fontSize = 13.sp, lineHeight = 18.sp)
                }
            }
        }
    }
}

@Composable
fun RiskGauge(label: String, value: Double, max: Double) {
    val color = when {
        value >= 70 -> HighRisk
        value >= 40 -> MediumRisk
        else -> LowRisk
    }
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Box(contentAlignment = Alignment.Center) {
            CircularProgressIndicator(
                progress = { (value / max).toFloat().coerceIn(0f, 1f) },
                modifier = Modifier.size(64.dp),
                color = color,
                trackColor = Color.White.copy(alpha = 0.3f),
                strokeWidth = 6.dp
            )
            Text(
                "${String.format("%.0f", value)}",
                color = color,
                fontWeight = FontWeight.ExtraBold,
                fontSize = 16.sp
            )
        }
        Spacer(Modifier.height(4.dp))
        Text(label, color = StreamDark.copy(alpha = 0.6f), fontSize = 11.sp, fontWeight = FontWeight.Medium)
    }
}

@Composable
fun FlagRow(icon: String, name: String, triggered: Boolean, description: String) {
    Row(
        Modifier.fillMaxWidth().padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(icon, fontSize = 16.sp)
        Spacer(Modifier.width(8.dp))
        Column(Modifier.weight(1f)) {
            Text(name, color = StreamDark, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
            Text(description, color = StreamDark.copy(alpha = 0.4f), fontSize = 11.sp)
        }
        Surface(
            shape = RoundedCornerShape(8.dp),
            color = if (triggered) HighRisk.copy(alpha = 0.15f) else LowRisk.copy(alpha = 0.1f)
        ) {
            Text(
                if (triggered) "TRIGGERED" else "CLEAR",
                color = if (triggered) HighRisk else LowRisk,
                fontSize = 10.sp,
                fontWeight = FontWeight.ExtraBold,
                modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
            )
        }
    }
}
