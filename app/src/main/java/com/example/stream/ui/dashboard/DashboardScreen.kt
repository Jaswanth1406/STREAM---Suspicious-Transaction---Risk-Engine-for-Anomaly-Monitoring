package com.example.stream.ui.dashboard

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.stream.ui.components.*
import com.example.stream.ui.theme.*

@Composable
fun DashboardScreen(vm: DashboardViewModel = viewModel()) {
    val kpisState by vm.kpis.collectAsState()
    val bondsState by vm.bonds.collectAsState()
    Box(Modifier.fillMaxSize()) {
        AnimatedGradientBackground()
        when (val state = kpisState) {
            is UiState.Loading -> LoadingScreen()
            is UiState.Error -> ErrorScreen(state.message) { vm.load() }
            is UiState.Success -> {
                val kpis = state.data
                Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp).statusBarsPadding()) {
                    Text("STREAM", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 28.sp)
                    Text("Anti-Corruption Intelligence", color = StreamDark.copy(alpha = 0.6f), fontSize = 14.sp)
                    Spacer(Modifier.height(20.dp))
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        KpiCard("Active Flags", "${kpis.activeFlags}", modifier = Modifier.weight(1f))
                        KpiCard("At-Risk Value", "Rs${String.format("%.1f", kpis.atRiskValueCr)}Cr", modifier = Modifier.weight(1f))
                    }
                    Spacer(Modifier.height(12.dp))
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        KpiCard("Vendors Tracked", "${kpis.vendorsTracked}", modifier = Modifier.weight(1f))
                        KpiCard("Model Precision", "${kpis.precisionRate}%", modifier = Modifier.weight(1f))
                    }
                    Spacer(Modifier.height(20.dp))
                    GlassCard {
                        Text("Detection Summary", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                        Spacer(Modifier.height(12.dp))
                        DetectionRow("Bid Rigging Detected", "${kpis.bidRiggingDetected}", HighRisk)
                        DetectionRow("Shell Networks Mapped", "${kpis.shellNetworksMapped}", MediumRisk)
                        DetectionRow("Political Connections", "${kpis.politicalConnections}", StreamPurple)
                    }
                    Spacer(Modifier.height(12.dp))
                    GlassCard {
                        Text("Data Overview", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                        Spacer(Modifier.height(12.dp))
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) { Text("${kpis.totalTenders}", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 20.sp); Text("Tenders", color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp) }
                            Column(horizontalAlignment = Alignment.CenterHorizontally) { Text("${kpis.totalCompanies}", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 20.sp); Text("Companies", color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp) }
                            Column(horizontalAlignment = Alignment.CenterHorizontally) { Text("${String.format("%.1f", kpis.falsePositiveControl)}%", color = LowRisk, fontWeight = FontWeight.ExtraBold, fontSize = 20.sp); Text("FP Control", color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp) }
                        }
                    }
                    Spacer(Modifier.height(12.dp))
                    val bState = bondsState
                    if (bState is UiState.Success) {
                        GlassCard {
                            Text("Electoral Bond Intelligence", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                            Spacer(Modifier.height(12.dp))
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                Column(Modifier.weight(1f)) { Text("Total Value", color = StreamDark.copy(alpha = 0.6f), fontSize = 12.sp); Text("Rs${String.format("%.0f", bState.data.totalValueCr)}Cr", color = StreamDark, fontWeight = FontWeight.ExtraBold, fontSize = 18.sp) }
                                Column(Modifier.weight(1f)) { Text("Purchasers", color = StreamDark.copy(alpha = 0.6f), fontSize = 12.sp); Text("${bState.data.uniquePurchasers}", color = StreamDark, fontWeight = FontWeight.ExtraBold, fontSize = 18.sp) }
                                Column(Modifier.weight(1f)) { Text("Parties", color = StreamDark.copy(alpha = 0.6f), fontSize = 12.sp); Text("${bState.data.uniqueParties}", color = StreamDark, fontWeight = FontWeight.ExtraBold, fontSize = 18.sp) }
                            }
                            Spacer(Modifier.height(8.dp))
                            bState.data.partyBreakdown.take(5).forEach { party ->
                                Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                                    Text(party.partyName, color = StreamDark, fontSize = 12.sp, fontWeight = FontWeight.Medium, modifier = Modifier.weight(1f))
                                    Text("Rs${String.format("%.0f", party.totalValueCr)}Cr", color = StreamPurple, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }
                    Spacer(Modifier.height(80.dp))
                }
            }
        }
    }
}

@Composable
fun DetectionRow(label: String, value: String, color: Color) {
    Row(Modifier.fillMaxWidth().padding(vertical = 6.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
        Text(label, color = StreamDark.copy(alpha = 0.8f), fontSize = 14.sp, fontWeight = FontWeight.Medium)
        Text(value, color = color, fontWeight = FontWeight.ExtraBold, fontSize = 16.sp)
    }
}