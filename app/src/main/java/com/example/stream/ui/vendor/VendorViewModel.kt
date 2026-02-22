package com.example.stream.ui.vendor

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.stream.data.model.VendorProfile
import com.example.stream.data.model.VendorSearchResponse
import com.example.stream.data.repository.StreamRepository
import com.example.stream.ui.components.UiState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class VendorViewModel : ViewModel() {
    private val repo = StreamRepository()
    private val _profile = MutableStateFlow<UiState<VendorProfile>>(UiState.Loading)
    val profile = _profile.asStateFlow()
    private val _search = MutableStateFlow<UiState<VendorSearchResponse>?>(null)
    val search = _search.asStateFlow()

    fun loadVendor(vendorId: String) {
        viewModelScope.launch {
            _profile.value = UiState.Loading
            repo.getVendorProfile(vendorId).fold(
                { _profile.value = UiState.Success(it) },
                { _profile.value = UiState.Error(it.localizedMessage ?: "Vendor not found") }
            )
        }
    }

    fun searchVendors(query: String) {
        if (query.length < 2) return
        viewModelScope.launch {
            _search.value = UiState.Loading
            repo.searchVendors(query).fold(
                { _search.value = UiState.Success(it) },
                { _search.value = UiState.Error(it.localizedMessage ?: "Search failed") }
            )
        }
    }
}
