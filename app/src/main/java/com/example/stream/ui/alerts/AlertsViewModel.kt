package com.example.stream.ui.alerts

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.stream.data.model.AlertResponse
import com.example.stream.data.repository.StreamRepository
import com.example.stream.ui.components.UiState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class AlertsViewModel : ViewModel() {
    private val repo = StreamRepository()
    private val _state = MutableStateFlow<UiState<AlertResponse>>(UiState.Loading)
    val state = _state.asStateFlow()
    var selectedFilter: String? = null; private set
    var selectedRiskTier: String? = null; private set
    var sortBy: String? = null; private set
    var sortDesc: Boolean? = null; private set
    var currentPage = 1; private set
    init { load() }
    fun load(alertType: String? = selectedFilter) { selectedFilter = alertType; currentPage = 1; fetchPage() }
    fun filterRisk(tier: String?) { selectedRiskTier = tier; currentPage = 1; fetchPage() }
    fun toggleSort(field: String) {
        if (sortBy == field) { sortDesc = when (sortDesc) { null -> true; true -> false; false -> null }; if (sortDesc == null) sortBy = null } else { sortBy = field; sortDesc = true }
        currentPage = 1; fetchPage()
    }
    fun nextPage() { currentPage++; fetchPage() }
    fun prevPage() { if (currentPage > 1) { currentPage--; fetchPage() } }
    private fun fetchPage() {
        viewModelScope.launch {
            _state.value = UiState.Loading
            val order = when (sortDesc) { true -> "desc"; false -> "asc"; null -> null }
            repo.getAlerts(currentPage, 20, selectedFilter, selectedRiskTier, sortBy, order).fold({ _state.value = UiState.Success(it) }, { _state.value = UiState.Error(it.localizedMessage ?: "Failed") })
        }
    }
}