package com.example.stream.ui.activity

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
import com.example.stream.data.model.ActivityEvent
import com.example.stream.ui.components.*
import com.example.stream.ui.theme.*

@Composable
fun ActivityScreen(vm: ActivityViewModel = viewModel()) {
    val state by vm.state.collectAsState()
    Box(Modifier.fillMaxSize()) {
        AnimatedGradientBackground()
        Column(Modifier.fillMaxSize().statusBarsPadding().padding(top = 16.dp)) {
            Text("Activity Feed", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 24.sp, modifier = Modifier.padding(horizontal = 16.dp))
            Text("Real-time intelligence events", color = StreamDark.copy(alpha = 0.5f), fontSize = 13.sp, modifier = Modifier.padding(horizontal = 16.dp))
            Spacer(Modifier.height(8.dp))
            Row(Modifier.horizontalScroll(rememberScrollState()).padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf(null to "All Events", "electoral_bond" to "Bonds", "flag_raised" to "Flags", "prediction_made" to "Predictions").forEach { (key, label) -> GlassFilterChip(label, vm.selectedEventType == key) { vm.load(key) } }
            }
            Spacer(Modifier.height(8.dp))
            when (val s = state) {
                is UiState.Loading -> LoadingScreen()
                is UiState.Error -> ErrorScreen(s.message) { vm.load() }
                is UiState.Success -> {
                    if (s.data.activities.isEmpty()) { Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("No events", color = StreamDark.copy(alpha = 0.5f), fontSize = 16.sp) } } else {
                        Text("${s.data.activities.size} events", color = StreamDark.copy(alpha = 0.4f), fontSize = 12.sp, modifier = Modifier.padding(horizontal = 16.dp))
                        Spacer(Modifier.height(4.dp))
                        LazyColumn(contentPadding = PaddingValues(horizontal = 16.dp, vertical = 4.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            items(s.data.activities) { event -> EventCard(event) }
                            item { Spacer(Modifier.height(80.dp)) }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun EventCard(event: ActivityEvent) {
    val accentColor = when (event.riskTier.uppercase()) { "HIGH" -> HighRisk; "MEDIUM" -> MediumRisk; "LOW" -> LowRisk; else -> StreamPurple }
    GlassCard(modifier = Modifier.fillMaxWidth()) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.Top) {
            Surface(shape = RoundedCornerShape(10.dp), color = accentColor.copy(alpha = 0.15f), modifier = Modifier.size(40.dp)) { Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text(if (event.icon == "bond") "B" else "F", fontSize = 20.sp) } }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(event.title, color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 14.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text(event.entityName, color = StreamDark.copy(alpha = 0.7f), fontSize = 13.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                if (event.partyName.isNotEmpty()) { Text("-> ${event.partyName}", color = StreamPurple.copy(alpha = 0.7f), fontSize = 12.sp, fontWeight = FontWeight.SemiBold) }
                Spacer(Modifier.height(4.dp))
                Text(event.subtitle, color = StreamDark.copy(alpha = 0.4f), fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
            Column(horizontalAlignment = Alignment.End) {
                if (event.amountCr > 0) { Text("Rs${String.format("%.0f", event.amountCr)}Cr", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 14.sp) }
                event.riskScore?.let { RiskBadge(event.riskTier) }
            }
        }
    }
}