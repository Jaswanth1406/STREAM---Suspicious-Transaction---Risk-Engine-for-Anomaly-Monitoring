package com.example.stream.ui.chat

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.stream.ui.components.AnimatedGradientBackground
import com.example.stream.ui.theme.*
import kotlinx.coroutines.launch

@Composable
fun ChatScreen(vm: ChatViewModel = viewModel()) {
    val messages by vm.messages.collectAsState()
    val isTyping by vm.isTyping.collectAsState()
    var input by remember { mutableStateOf("") }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()

    LaunchedEffect(messages.size, messages.lastOrNull()?.content) {
        if (messages.isNotEmpty()) listState.animateScrollToItem(messages.size - 1)
    }

    Box(Modifier.fillMaxSize()) {
        AnimatedGradientBackground()
        Column(Modifier.fillMaxSize().statusBarsPadding()) {
            // Header
            Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Surface(shape = CircleShape, color = StreamPurple.copy(alpha = 0.15f), modifier = Modifier.size(40.dp)) {
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("AI", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 16.sp) }
                }
                Spacer(Modifier.width(12.dp))
                Column {
                    Text("STREAM AI", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 18.sp)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(Modifier.size(8.dp).clip(CircleShape).background(if (isTyping) MediumRisk else LowRisk))
                        Spacer(Modifier.width(6.dp))
                        Text(if (isTyping) "Analyzing..." else "Online", color = StreamDark.copy(alpha = 0.5f), fontSize = 12.sp)
                    }
                }
            }
            Divider(color = Color.White.copy(alpha = 0.4f), thickness = 1.dp)

            // Messages
            LazyColumn(
                state = listState,
                modifier = Modifier.weight(1f).padding(horizontal = 12.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
                contentPadding = PaddingValues(vertical = 12.dp)
            ) {
                items(messages, key = { it.id }) { msg ->
                    AnimatedVisibility(visible = true, enter = slideInVertically(initialOffsetY = { it }) + fadeIn()) {
                        when (msg.role) {
                            MessageRole.SYSTEM -> SystemBubble(msg)
                            MessageRole.USER -> UserBubble(msg)
                            MessageRole.ASSISTANT -> AssistantBubble(msg, onRetry = { vm.retryLast() })
                        }
                    }
                }
                if (isTyping && messages.lastOrNull()?.isStreaming != true) {
                    item { TypingIndicator() }
                }
            }

            // Suggestions row
            if (messages.size <= 2) {
                Row(Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 4.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("Top risky tenders", "Bond summary", "Recent flags").forEach { s ->
                        SuggestionChip(s) { input = s; vm.sendMessage(s); input = "" }
                    }
                }
            }

            // Input bar
            Row(
                Modifier.fillMaxWidth().padding(12.dp).clip(RoundedCornerShape(24.dp)).background(Color.White.copy(alpha = 0.5f)).border(1.dp, Color.White.copy(alpha = 0.7f), RoundedCornerShape(24.dp)).padding(horizontal = 8.dp, vertical = 4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                TextField(
                    value = input,
                    onValueChange = { input = it },
                    placeholder = { Text("Ask STREAM AI...", color = StreamDark.copy(alpha = 0.4f), fontSize = 14.sp) },
                    colors = TextFieldDefaults.colors(focusedContainerColor = Color.Transparent, unfocusedContainerColor = Color.Transparent, focusedIndicatorColor = Color.Transparent, unfocusedIndicatorColor = Color.Transparent),
                    modifier = Modifier.weight(1f),
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                    keyboardActions = KeyboardActions(onSend = { if (input.isNotBlank() && !isTyping) { vm.sendMessage(input); input = "" } }),
                    maxLines = 3,
                    textStyle = LocalTextStyle.current.copy(fontSize = 14.sp)
                )
                IconButton(
                    onClick = { if (input.isNotBlank() && !isTyping) { vm.sendMessage(input); input = "" } },
                    enabled = input.isNotBlank() && !isTyping,
                    modifier = Modifier.size(40.dp).clip(CircleShape).background(if (input.isNotBlank() && !isTyping) StreamPurple else StreamDark.copy(alpha = 0.1f))
                ) {
                    Icon(Icons.Default.Send, null, tint = if (input.isNotBlank() && !isTyping) Color.White else StreamDark.copy(alpha = 0.3f), modifier = Modifier.size(20.dp))
                }
            }
            Spacer(Modifier.navigationBarsPadding())
        }
    }
}

@Composable
fun SystemBubble(msg: ChatMessage) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) {
        Surface(shape = RoundedCornerShape(16.dp), color = StreamPurple.copy(alpha = 0.08f), modifier = Modifier.padding(horizontal = 24.dp)) {
            Column(Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                Text("STREAM AI", color = StreamPurple, fontWeight = FontWeight.ExtraBold, fontSize = 14.sp)
                Spacer(Modifier.height(4.dp))
                Text(msg.content, color = StreamDark.copy(alpha = 0.7f), fontSize = 13.sp, lineHeight = 18.sp, textAlign = androidx.compose.ui.text.style.TextAlign.Center)
            }
        }
    }
}

@Composable
fun UserBubble(msg: ChatMessage) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
        Column(horizontalAlignment = Alignment.End) {
            Surface(shape = RoundedCornerShape(20.dp, 20.dp, 4.dp, 20.dp), color = StreamPurple) {
                Text(msg.content, color = Color.White, fontSize = 14.sp, modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp).widthIn(max = 280.dp), lineHeight = 20.sp)
            }
            Spacer(Modifier.height(2.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                val timeStr = remember(msg.timestamp) { java.text.SimpleDateFormat("hh:mm a", java.util.Locale.getDefault()).format(java.util.Date(msg.timestamp)) }
                Text(timeStr, color = StreamDark.copy(alpha = 0.4f), fontSize = 10.sp)
                Spacer(Modifier.width(4.dp))
                TickIndicator(msg.status)
            }
        }
    }
}

@Composable
fun AssistantBubble(msg: ChatMessage, onRetry: () -> Unit) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Start) {
        Surface(shape = CircleShape, color = StreamPurple.copy(alpha = 0.12f), modifier = Modifier.size(28.dp)) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("AI", color = StreamPurple, fontSize = 10.sp, fontWeight = FontWeight.ExtraBold) }
        }
        Spacer(Modifier.width(8.dp))
        Column(Modifier.widthIn(max = 300.dp)) {
            // Tool call cards
            msg.toolCalls.forEach { tc -> ToolCallCard(tc) }
            // Message content
            if (msg.content.isNotEmpty()) {
                Surface(shape = RoundedCornerShape(4.dp, 20.dp, 20.dp, 20.dp), color = Color.White.copy(alpha = 0.6f)) {
                    Column(Modifier.padding(horizontal = 16.dp, vertical = 10.dp).border(0.dp, Color.Transparent)) {
                        Text(msg.content, color = StreamDark.copy(alpha = 0.9f), fontSize = 14.sp, lineHeight = 20.sp)
                        if (msg.isStreaming) {
                            val alpha by rememberInfiniteTransition(label = "cursor").animateFloat(1f, 0f, infiniteRepeatable(tween(500), RepeatMode.Reverse), label = "c")
                            Text("|", color = StreamPurple.copy(alpha = alpha), fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        }
                    }
                }
            }
            // Error retry
            if (msg.status == MessageStatus.ERROR) {
                Spacer(Modifier.height(4.dp))
                TextButton(onClick = onRetry) {
                    Icon(Icons.Default.Refresh, null, tint = HighRisk, modifier = Modifier.size(14.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("Retry", color = HighRisk, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                }
            }
            // Timestamp
            if (!msg.isStreaming && msg.content.isNotEmpty()) {
                val timeStr = remember(msg.timestamp) { java.text.SimpleDateFormat("hh:mm a", java.util.Locale.getDefault()).format(java.util.Date(msg.timestamp)) }
                Text(timeStr, color = StreamDark.copy(alpha = 0.3f), fontSize = 10.sp, modifier = Modifier.padding(top = 2.dp))
            }
        }
    }
}

@Composable
fun ToolCallCard(tc: ToolCallInfo) {
    Surface(shape = RoundedCornerShape(12.dp), color = StreamLavender.copy(alpha = 0.15f), modifier = Modifier.fillMaxWidth().padding(bottom = 6.dp)) {
        Row(Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
            if (tc.isRunning) {
                val scale by rememberInfiniteTransition(label = "tool").animateFloat(0.8f, 1.2f, infiniteRepeatable(tween(600), RepeatMode.Reverse), label = "s")
                Box(Modifier.size(8.dp).scale(scale).clip(CircleShape).background(MediumRisk))
            } else {
                Box(Modifier.size(8.dp).clip(CircleShape).background(LowRisk))
            }
            Spacer(Modifier.width(8.dp))
            Column {
                Text(if (tc.isRunning) "Running: ${tc.tool}" else "Done: ${tc.tool}", color = StreamDark, fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
                if (tc.input.isNotEmpty()) { Text(tc.input, color = StreamDark.copy(alpha = 0.5f), fontSize = 10.sp, maxLines = 1, overflow = TextOverflow.Ellipsis) }
                if (tc.outputPreview.isNotEmpty()) { Text(tc.outputPreview.take(80) + "...", color = StreamDark.copy(alpha = 0.4f), fontSize = 10.sp, maxLines = 2, overflow = TextOverflow.Ellipsis) }
            }
        }
    }
}

@Composable
fun TickIndicator(status: MessageStatus) {
    when (status) {
        MessageStatus.SENDING -> Text("~", color = StreamDark.copy(alpha = 0.3f), fontSize = 12.sp)
        MessageStatus.SENT -> Text("ok", color = StreamDark.copy(alpha = 0.4f), fontSize = 9.sp, fontWeight = FontWeight.Bold)
        MessageStatus.DELIVERED -> Text("ok", color = StreamPurple, fontSize = 9.sp, fontWeight = FontWeight.Bold)
        MessageStatus.ERROR -> Text("!", color = HighRisk, fontSize = 12.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
fun TypingIndicator() {
    val transition = rememberInfiniteTransition(label = "dots")
    val d1 by transition.animateFloat(0.3f, 1f, infiniteRepeatable(tween(400), RepeatMode.Reverse), label = "d1")
    val d2 by transition.animateFloat(0.3f, 1f, infiniteRepeatable(tween(400, delayMillis = 150), RepeatMode.Reverse), label = "d2")
    val d3 by transition.animateFloat(0.3f, 1f, infiniteRepeatable(tween(400, delayMillis = 300), RepeatMode.Reverse), label = "d3")
    Row(Modifier.padding(start = 36.dp)) {
        Surface(shape = RoundedCornerShape(16.dp), color = Color.White.copy(alpha = 0.5f)) {
            Row(Modifier.padding(horizontal = 16.dp, vertical = 10.dp), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                listOf(d1, d2, d3).forEach { a ->
                    Box(Modifier.size(8.dp).scale(a).clip(CircleShape).background(StreamPurple.copy(alpha = a)))
                }
            }
        }
    }
}

@Composable
fun SuggestionChip(text: String, onClick: () -> Unit) {
    Surface(onClick = onClick, shape = RoundedCornerShape(20.dp), color = Color.White.copy(alpha = 0.4f), border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.6f))) {
        Text(text, color = StreamPurple, fontSize = 12.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp))
    }
}