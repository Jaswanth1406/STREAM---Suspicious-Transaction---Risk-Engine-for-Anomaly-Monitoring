package com.example.stream.ui.alerts

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.stream.data.model.AlertItem
import com.example.stream.ui.components.*
import com.example.stream.ui.theme.*

@Composable
fun AlertsScreen(vm: AlertsViewModel = viewModel(), onVendorClick: (String) -> Unit = {}) {
    val state by vm.state.collectAsState()
    Box(Modifier.fillMaxSize()) {
        AnimatedGradientBackground()
        Column(Modifier.fillMaxSize().statusBarsPadding().padding(top = 16.dp)) {
            Text("Fraud Alerts", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 24.sp, modifier = Modifier.padding(horizontal = 16.dp))
            Spacer(Modifier.height(8.dp))
            Row(Modifier.horizontalScroll(rememberScrollState()).padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf(null to "All", "bid_rigging" to "Bid Rigging", "political" to "Political", "shell_network" to "Shell Network", "high_value" to "High Value").forEach { (key, label) -> GlassFilterChip(label, vm.selectedFilter == key) { vm.load(key) } }
            }
            Spacer(Modifier.height(6.dp))
            Row(Modifier.horizontalScroll(rememberScrollState()).padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf(null to "All Risks", "High" to "High", "Medium" to "Medium", "Low" to "Low").forEach { (key, label) -> GlassFilterChip(label, vm.selectedRiskTier == key) { vm.filterRisk(key) } }
                SortChip("Risk", if (vm.sortBy == "risk_score") vm.sortDesc else null) { vm.toggleSort("risk_score") }
                SortChip("Amount", if (vm.sortBy == "amount") vm.sortDesc else null) { vm.toggleSort("amount") }
            }
            Spacer(Modifier.height(8.dp))
            when (val s = state) {
                is UiState.Loading -> LoadingScreen()
                is UiState.Error -> ErrorScreen(s.message) { vm.load(vm.selectedFilter) }
                is UiState.Success -> {
                    if (s.data.alerts.isEmpty()) { Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("No alerts found", color = StreamDark.copy(alpha = 0.5f), fontSize = 16.sp) } } else {
                        LazyColumn(contentPadding = PaddingValues(horizontal = 16.dp, vertical = 4.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            item { PaginationBar(vm.currentPage, s.data.totalPages, s.data.total, { vm.prevPage() }, { vm.nextPage() }); Spacer(Modifier.height(8.dp)) }
                            items(s.data.alerts) { alert -> AlertCard(alert) }
                            item { Spacer(Modifier.height(8.dp)); PaginationBar(vm.currentPage, s.data.totalPages, s.data.total, { vm.prevPage() }, { vm.nextPage() }); Spacer(Modifier.height(80.dp)) }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun AlertCard(alert: AlertItem) {
    GlassCard(modifier = Modifier.fillMaxWidth()) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Surface(shape = RoundedCornerShape(8.dp), color = StreamPurple.copy(alpha = 0.12f)) { Text(alert.alertType.uppercase().replace("_", " "), color = StreamPurple, fontSize = 11.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)) }
            RiskBadge(alert.riskTier)
        }
        Spacer(Modifier.height(8.dp))
        Text(alert.title, color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 15.sp, maxLines = 2, overflow = TextOverflow.Ellipsis)
        Spacer(Modifier.height(4.dp))
        Text(alert.displayEntity, color = StreamDark.copy(alpha = 0.6f), fontSize = 13.sp)
        Spacer(Modifier.height(8.dp))
        if (alert.isProcurement) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column { Text("Amount", color = StreamDark.copy(alpha = 0.5f), fontSize = 11.sp); Text(alert.displayAmount, color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 14.sp) }
                Column(horizontalAlignment = Alignment.CenterHorizontally) { Text("Bidders", color = StreamDark.copy(alpha = 0.5f), fontSize = 11.sp); val b = alert.numTenderers?.toInt() ?: 0; Text("$b", color = if (b <= 1) HighRisk else StreamDark, fontWeight = FontWeight.Bold, fontSize = 14.sp) }
                Column(horizontalAlignment = Alignment.End) { Text("Risk", color = StreamDark.copy(alpha = 0.5f), fontSize = 11.sp); Text("${String.format("%.1f", alert.riskScore)}", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 14.sp) }
            }
            if (!alert.category.isNullOrEmpty()) { Spacer(Modifier.height(4.dp)); Text(alert.category ?: "", color = StreamLavender, fontSize = 12.sp, fontWeight = FontWeight.Medium) }
        } else {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column { Text("Bond Value", color = StreamDark.copy(alpha = 0.5f), fontSize = 11.sp); Text(alert.displayAmount, color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 14.sp) }
                Column(horizontalAlignment = Alignment.CenterHorizontally) { Text("Bonds", color = StreamDark.copy(alpha = 0.5f), fontSize = 11.sp); Text("${alert.totalBonds ?: 0}", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 14.sp) }
                Column(horizontalAlignment = Alignment.End) { Text("Risk", color = StreamDark.copy(alpha = 0.5f), fontSize = 11.sp); Text("${alert.riskScore.toInt()}", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 14.sp) }
            }
            alert.partiesFunded?.let { p -> if (p.isNotEmpty()) { Spacer(Modifier.height(6.dp)); Text("Parties: ${p.take(3).joinToString(", ")}", color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp, maxLines = 2, overflow = TextOverflow.Ellipsis) } }
        }
        if (alert.flagsTriggered.isNotEmpty()) { Spacer(Modifier.height(6.dp)); Text("Flags: ${alert.flagsTriggered.joinToString(" | ")}", color = HighRisk.copy(alpha = 0.7f), fontSize = 11.sp, fontWeight = FontWeight.SemiBold) }
        if (alert.explanation.isNotEmpty()) { Spacer(Modifier.height(4.dp)); Text(alert.explanation, color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp, maxLines = 2, overflow = TextOverflow.Ellipsis, lineHeight = 16.sp) }
    }
}