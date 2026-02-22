package com.example.stream.ui.predict

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.stream.ui.components.*
import com.example.stream.ui.theme.*

@Composable
fun PredictScreen(vm: PredictViewModel = viewModel()) {
    val resultState by vm.result.collectAsState()

    var amount by remember { mutableStateOf("") }
    var numTenderers by remember { mutableStateOf("") }
    var durationDays by remember { mutableStateOf("") }
    var procurementMethod by remember { mutableStateOf("") }
    var classification by remember { mutableStateOf("") }
    var buyerName by remember { mutableStateOf("") }

    Box(Modifier.fillMaxSize()) {
        AnimatedGradientBackground()

        Column(
            Modifier.fillMaxSize().statusBarsPadding().verticalScroll(rememberScrollState()).padding(16.dp)
        ) {
            Text("ML Prediction", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 24.sp)
            Text("Score a tender for corruption risk", color = StreamDark.copy(alpha = 0.5f), fontSize = 13.sp)
            Spacer(Modifier.height(20.dp))

            GlassCard {
                PredictField("Amount (INR)", amount, { amount = it }, KeyboardType.Number)
                Spacer(Modifier.height(12.dp))
                PredictField("Number of Tenderers", numTenderers, { numTenderers = it }, KeyboardType.Number)
                Spacer(Modifier.height(12.dp))
                PredictField("Duration (Days)", durationDays, { durationDays = it }, KeyboardType.Number)
                Spacer(Modifier.height(12.dp))
                PredictField("Procurement Method", procurementMethod, { procurementMethod = it })
                Spacer(Modifier.height(12.dp))
                PredictField("Classification", classification, { classification = it })
                Spacer(Modifier.height(12.dp))
                PredictField("Buyer Name", buyerName, { buyerName = it })
                Spacer(Modifier.height(20.dp))

                Button(
                    onClick = {
                        val amt = amount.toDoubleOrNull() ?: 0.0
                        val nT = numTenderers.toIntOrNull() ?: 0
                        val dD = durationDays.toIntOrNull() ?: 0
                        vm.predict(amt, nT, dD, procurementMethod, classification, buyerName)
                    },
                    modifier = Modifier.fillMaxWidth().height(52.dp)
                        .border(1.dp, Color.White.copy(alpha = 0.5f), RoundedCornerShape(14.dp)),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = StreamPurple.copy(alpha = 0.7f)),
                    enabled = amount.isNotEmpty() && numTenderers.isNotEmpty() && durationDays.isNotEmpty()
                ) {
                    val rState = resultState
                    if (rState is UiState.Loading) {
                        CircularProgressIndicator(color = Color.White, modifier = Modifier.size(22.dp), strokeWidth = 2.dp)
                    } else {
                        Text("PREDICT RISK", color = Color.White, fontWeight = FontWeight.ExtraBold, fontSize = 14.sp)
                    }
                }
            }
            Spacer(Modifier.height(16.dp))

            // Result card
            val rState = resultState
            if (rState is UiState.Success) {
                val r = rState.data
                val tierColor = when {
                    r.predictedRiskTier.contains("High", true) -> HighRisk
                    r.predictedRiskTier.contains("Medium", true) -> MediumRisk
                    else -> LowRisk
                }
                GlassCard {
                    Text("Prediction Result", color = StreamDark, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                    Spacer(Modifier.height(12.dp))
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("Risk Tier", color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp)
                            Spacer(Modifier.height(4.dp))
                            Surface(shape = RoundedCornerShape(10.dp), color = tierColor.copy(alpha = 0.15f)) {
                                Text(r.predictedRiskTier, color = tierColor, fontWeight = FontWeight.ExtraBold, fontSize = 18.sp, modifier = Modifier.padding(12.dp))
                            }
                        }
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("Suspicion", color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp)
                            Spacer(Modifier.height(4.dp))
                            Text("${String.format("%.1f", r.suspicionProbability * 100)}%", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 28.sp)
                        }
                    }
                    Spacer(Modifier.height(12.dp))
                    Text(
                        if (r.predictedSuspicious == 1) "⚠️ This tender shows suspicious patterns" else "✅ No significant risk detected",
                        color = StreamDark, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth()
                    )
                }
            }
            if (rState is UiState.Error) {
                Spacer(Modifier.height(8.dp))
                GlassCard {
                    Text("Error: ${rState.message}", color = HighRisk, fontSize = 14.sp)
                }
            }
            Spacer(Modifier.height(80.dp))
        }
    }
}

@Composable
fun PredictField(label: String, value: String, onValueChange: (String) -> Unit, keyboardType: KeyboardType = KeyboardType.Text) {
    Column {
        Text(label, color = StreamDark, fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
        Spacer(Modifier.height(4.dp))
        OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            shape = RoundedCornerShape(14.dp),
            keyboardOptions = KeyboardOptions(keyboardType = keyboardType),
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = StreamDark, unfocusedTextColor = StreamDark,
                focusedBorderColor = StreamPurple, unfocusedBorderColor = Color.White.copy(alpha = 0.6f),
                cursorColor = StreamPurple,
                focusedContainerColor = Color.White.copy(alpha = 0.5f),
                unfocusedContainerColor = Color.White.copy(alpha = 0.3f)
            ),
            placeholder = { Text("Enter $label", color = StreamDark.copy(alpha = 0.4f), fontSize = 13.sp) }
        )
    }
}
