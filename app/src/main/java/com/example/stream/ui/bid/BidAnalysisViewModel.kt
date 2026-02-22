package com.example.stream.ui.bid

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.stream.data.model.BidAnalysisResponse
import com.example.stream.data.model.BidSummary
import com.example.stream.data.repository.StreamRepository
import com.example.stream.ui.components.UiState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class BidAnalysisViewModel : ViewModel() {
    private val repo = StreamRepository()
    private val _summary = MutableStateFlow<UiState<BidSummary>>(UiState.Loading)
    val summary = _summary.asStateFlow()
    private val _tenders = MutableStateFlow<UiState<BidAnalysisResponse>>(UiState.Loading)
    val tenders = _tenders.asStateFlow()
    var selectedRiskTier: String? = null; private set
    var sortBy: String? = null; private set
    var sortDesc: Boolean? = null; private set
    var currentPage = 1; private set
    init { load() }
    fun load() {
        viewModelScope.launch { repo.getBidSummary().fold({ _summary.value = UiState.Success(it) }, { _summary.value = UiState.Error(it.localizedMessage ?: "Failed") }) }
        fetchPage()
    }
    fun filterRisk(tier: String?) { selectedRiskTier = tier; currentPage = 1; fetchPage() }
    fun toggleSort(field: String) {
        if (sortBy == field) { sortDesc = when (sortDesc) { null -> true; true -> false; false -> null }; if (sortDesc == null) sortBy = null } else { sortBy = field; sortDesc = true }
        currentPage = 1; fetchPage()
    }
    fun nextPage() { currentPage++; fetchPage() }
    fun prevPage() { if (currentPage > 1) { currentPage--; fetchPage() } }
    private fun fetchPage() {
        viewModelScope.launch {
            _tenders.value = UiState.Loading
            val order = when (sortDesc) { true -> "desc"; false -> "asc"; null -> null }
            repo.getBidAnalysis(currentPage, 20, selectedRiskTier, sortBy, order).fold({ _tenders.value = UiState.Success(it) }, { _tenders.value = UiState.Error(it.localizedMessage ?: "Failed") })
        }
    }
}