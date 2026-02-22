package com.example.stream.ui.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.stream.data.model.BondSummary
import com.example.stream.data.model.DashboardKpis
import com.example.stream.data.repository.StreamRepository
import com.example.stream.ui.components.UiState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class DashboardViewModel : ViewModel() {
    private val repo = StreamRepository()
    private val _kpis = MutableStateFlow<UiState<DashboardKpis>>(UiState.Loading)
    val kpis = _kpis.asStateFlow()
    private val _bonds = MutableStateFlow<UiState<BondSummary>>(UiState.Loading)
    val bonds = _bonds.asStateFlow()
    init { load() }
    fun load() {
        viewModelScope.launch { repo.getDashboardKpis().fold({ _kpis.value = UiState.Success(it) }, { _kpis.value = UiState.Error(it.localizedMessage ?: "Failed") }) }
        viewModelScope.launch { repo.getBondSummary().fold({ _bonds.value = UiState.Success(it) }, { _bonds.value = UiState.Error(it.localizedMessage ?: "Failed") }) }
    }
}