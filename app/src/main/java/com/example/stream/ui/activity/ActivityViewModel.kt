package com.example.stream.ui.activity

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.stream.data.model.ActivityResponse
import com.example.stream.data.repository.StreamRepository
import com.example.stream.ui.components.UiState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class ActivityViewModel : ViewModel() {
    private val repo = StreamRepository()
    private val _state = MutableStateFlow<UiState<ActivityResponse>>(UiState.Loading)
    val state = _state.asStateFlow()
    var selectedEventType: String? = null
        private set
    init { load() }
    fun load(eventType: String? = null) {
        selectedEventType = eventType
        viewModelScope.launch {
            _state.value = UiState.Loading
            repo.getRecentActivity(limit = 50, eventType = eventType).fold(
                { _state.value = UiState.Success(it) },
                { _state.value = UiState.Error(it.localizedMessage ?: "Failed to load activity") }
            )
        }
    }
}