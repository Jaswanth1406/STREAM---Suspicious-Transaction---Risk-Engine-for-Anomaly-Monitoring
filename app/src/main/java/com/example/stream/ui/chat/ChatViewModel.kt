package com.example.stream.ui.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.util.UUID
import java.util.concurrent.TimeUnit

enum class MessageStatus { SENDING, SENT, DELIVERED, ERROR }
enum class MessageRole { USER, ASSISTANT, SYSTEM }

data class ToolCallInfo(val tool: String, val input: String = "", val outputPreview: String = "", val isRunning: Boolean = true)

data class ChatMessage(
    val id: String = UUID.randomUUID().toString(),
    val role: MessageRole = MessageRole.USER,
    val content: String = "",
    val status: MessageStatus = MessageStatus.SENDING,
    val timestamp: Long = System.currentTimeMillis(),
    val toolCalls: List<ToolCallInfo> = emptyList(),
    val isStreaming: Boolean = false
)

class ChatViewModel : ViewModel() {
    private val _messages = MutableStateFlow<List<ChatMessage>>(listOf(
        ChatMessage(role = MessageRole.SYSTEM, content = "Hello! I'm STREAM AI, your anti-corruption intelligence assistant. Ask me anything about tenders, vendors, bid rigging patterns, or electoral bonds.", status = MessageStatus.DELIVERED)
    ))
    val messages = _messages.asStateFlow()
    private val _isTyping = MutableStateFlow(false)
    val isTyping = _isTyping.asStateFlow()
    private var sessionId: String = UUID.randomUUID().toString()
    private val client = OkHttpClient.Builder().connectTimeout(60, TimeUnit.SECONDS).readTimeout(120, TimeUnit.SECONDS).writeTimeout(30, TimeUnit.SECONDS).build()
    private val baseUrl = "http://192.168.114.61:8000"

    fun sendMessage(text: String) {
        if (text.isBlank()) return
        val userMsg = ChatMessage(role = MessageRole.USER, content = text.trim(), status = MessageStatus.SENT)
        _messages.value = _messages.value + userMsg
        val botMsgId = UUID.randomUUID().toString()
        val botMsg = ChatMessage(id = botMsgId, role = MessageRole.ASSISTANT, content = "", status = MessageStatus.SENDING, isStreaming = true)
        _messages.value = _messages.value + botMsg
        _isTyping.value = true

        viewModelScope.launch(Dispatchers.IO) {
            try {
                val json = JSONObject()
                val msgs = JSONArray()
                val userJson = JSONObject()
                userJson.put("role", "user")
                userJson.put("content", text.trim())
                msgs.put(userJson)
                json.put("messages", msgs)
                json.put("session_id", sessionId)
                val body = json.toString().toRequestBody("application/json".toMediaType())
                val request = Request.Builder().url("$baseUrl/agent/chat/stream").post(body).build()
                val response = client.newCall(request).execute()
                if (!response.isSuccessful) {
                    updateBotMessage(botMsgId, "Error: Server returned ${response.code}", MessageStatus.ERROR, false, emptyList())
                    _isTyping.value = false
                    return@launch
                }
                val reader = BufferedReader(InputStreamReader(response.body?.byteStream()))
                var fullContent = ""
                val toolCalls = mutableListOf<ToolCallInfo>()
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    val l = line ?: continue
                    if (!l.startsWith("data: ")) continue
                    val data = l.removePrefix("data: ").trim()
                    if (data.isEmpty()) continue
                    try {
                        val event = JSONObject(data)
                        when (event.optString("type")) {
                            "token" -> {
                                fullContent += event.optString("content", "")
                                updateBotMessage(botMsgId, fullContent, MessageStatus.SENDING, true, toolCalls.toList())
                            }
                            "tool_start" -> {
                                val tc = ToolCallInfo(tool = event.optString("tool", ""), input = event.optString("input", ""), isRunning = true)
                                toolCalls.add(tc)
                                updateBotMessage(botMsgId, fullContent, MessageStatus.SENDING, true, toolCalls.toList())
                            }
                            "tool_end" -> {
                                val toolName = event.optString("tool", "")
                                val idx = toolCalls.indexOfLast { it.tool == toolName && it.isRunning }
                                if (idx >= 0) { toolCalls[idx] = toolCalls[idx].copy(outputPreview = event.optString("output_preview", ""), isRunning = false) }
                                updateBotMessage(botMsgId, fullContent, MessageStatus.SENDING, true, toolCalls.toList())
                            }
                            "done" -> {
                                updateBotMessage(botMsgId, fullContent, MessageStatus.DELIVERED, false, toolCalls.toList())
                                _isTyping.value = false
                            }
                        }
                    } catch (e: Exception) { /* skip malformed SSE lines */ }
                }
                reader.close()
                if (_isTyping.value) {
                    updateBotMessage(botMsgId, if (fullContent.isEmpty()) "Response received." else fullContent, MessageStatus.DELIVERED, false, toolCalls.toList())
                    _isTyping.value = false
                }
            } catch (e: Exception) {
                updateBotMessage(botMsgId, "Connection error: ${e.localizedMessage ?: "Unknown error"}", MessageStatus.ERROR, false, emptyList())
                _isTyping.value = false
            }
        }
    }

    fun retryLast() {
        val last = _messages.value.lastOrNull { it.role == MessageRole.USER }
        if (last != null) {
            _messages.value = _messages.value.dropLast(1).let { if (it.lastOrNull()?.role == MessageRole.USER) it else it }
            sendMessage(last.content)
        }
    }

    private fun updateBotMessage(id: String, content: String, status: MessageStatus, isStreaming: Boolean, toolCalls: List<ToolCallInfo>) {
        _messages.value = _messages.value.map { if (it.id == id) it.copy(content = content, status = status, isStreaming = isStreaming, toolCalls = toolCalls) else it }
    }
}