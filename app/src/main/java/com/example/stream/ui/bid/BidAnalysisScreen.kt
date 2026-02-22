package com.example.stream.ui.bid

import androidx.compose.foundation.clickable
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.stream.data.model.BidTender
import com.example.stream.ui.components.*
import com.example.stream.ui.theme.*

@Composable
fun BidAnalysisScreen(vm: BidAnalysisViewModel = viewModel(), onTenderClick: () -> Unit = {}) {
    val summaryState by vm.summary.collectAsState()
    val tendersState by vm.tenders.collectAsState()

    Box(Modifier.fillMaxSize()) {
        AnimatedGradientBackground()

        Column(Modifier.fillMaxSize().statusBarsPadding().padding(top = 16.dp)) {
            Text("Bid Analysis", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 24.sp, modifier = Modifier.padding(horizontal = 16.dp))
            Spacer(Modifier.height(8.dp))

            // Summary KPIs
            val sState = summaryState
            if (sState is UiState.Success) {
                val s = sState.data
                Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    KpiCard("Tenders", "${s.totalTenders}", modifier = Modifier.weight(1f))
                    KpiCard("🔴 High", "${s.highRisk}", modifier = Modifier.weight(1f))
                    KpiCard("🟡 Med", "${s.mediumRisk}", modifier = Modifier.weight(1f))
                }
                Spacer(Modifier.height(8.dp))
            }

            // Risk tier + sort chips
            Row(
                Modifier.horizontalScroll(rememberScrollState()).padding(horizontal = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                listOf(null to "All", "High" to "🔴 High", "Medium" to "🟡 Medium", "Low" to "🟢 Low").forEach { (key, label) ->
                    GlassFilterChip(label, vm.selectedRiskTier == key) { vm.filterRisk(key) }
                }
                SortChip("Risk", if (vm.sortBy == "risk_score") vm.sortDesc else null) { vm.toggleSort("risk_score") }
                SortChip("Amount", if (vm.sortBy == "amount") vm.sortDesc else null) { vm.toggleSort("amount") }
            }
            Spacer(Modifier.height(8.dp))

            // Tenders list with pagination
            when (val t = tendersState) {
                is UiState.Loading -> LoadingScreen()
                is UiState.Error -> ErrorScreen(t.message) { vm.load() }
                is UiState.Success -> {
                    LazyColumn(
                        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 4.dp),
                        verticalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        item {
                            PaginationBar(vm.currentPage, t.data.totalPages, t.data.total, { vm.prevPage() }, { vm.nextPage() })
                            Spacer(Modifier.height(8.dp))
                        }
                        items(t.data.tenders) { tender ->
                            BidTenderCard(
                                tender = tender,
                                onClick = {
                                    SelectedTender.tender = tender
                                    onTenderClick()
                                }
                            )
                        }
                        item {
                            Spacer(Modifier.height(8.dp))
                            PaginationBar(vm.currentPage, t.data.totalPages, t.data.total, { vm.prevPage() }, { vm.nextPage() })
                            Spacer(Modifier.height(80.dp))
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun BidTenderCard(tender: BidTender, onClick: () -> Unit) {
    val amountCr = tender.amount / 10_000_000.0
    GlassCard(modifier = Modifier.fillMaxWidth().clickable { onClick() }) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text(tender.tenderId, color = StreamDark.copy(alpha = 0.5f), fontSize = 11.sp, modifier = Modifier.weight(1f))
            RiskBadge(tender.riskTier)
        }
        Spacer(Modifier.height(6.dp))
        Text(tender.title, color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 14.sp, maxLines = 2, overflow = TextOverflow.Ellipsis)
        Text(tender.buyerName, color = StreamDark.copy(alpha = 0.6f), fontSize = 13.sp)
        Text(tender.category, color = StreamLavender.copy(alpha = 0.8f), fontSize = 12.sp, fontWeight = FontWeight.Medium)
        Spacer(Modifier.height(8.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Column {
                Text("Amount", color = StreamDark.copy(alpha = 0.5f), fontSize = 11.sp)
                Text("₹${String.format("%.1f", amountCr)}Cr", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 13.sp)
            }
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text("Bidders", color = StreamDark.copy(alpha = 0.5f), fontSize = 11.sp)
                Text("${tender.numTenderers.toInt()}", color = if (tender.numTenderers <= 1) HighRisk else StreamDark, fontWeight = FontWeight.Bold, fontSize = 13.sp)
            }
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text("Risk", color = StreamDark.copy(alpha = 0.5f), fontSize = 11.sp)
                Text("${String.format("%.1f", tender.riskScore)}", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 13.sp)
            }
            Column(horizontalAlignment = Alignment.End) {
                Text("Suspicion", color = StreamDark.copy(alpha = 0.5f), fontSize = 11.sp)
                Text("${String.format("%.0f", tender.suspicionProbability * 100)}%", color = if (tender.suspicionProbability > 0.7) HighRisk else MediumRisk, fontWeight = FontWeight.ExtraBold, fontSize = 13.sp)
            }
        }
        // Show tap hint
        Spacer(Modifier.height(6.dp))
        Text("Tap for detailed analysis →", color = StreamPurple.copy(alpha = 0.5f), fontSize = 11.sp, fontWeight = FontWeight.Medium)
    }
}
