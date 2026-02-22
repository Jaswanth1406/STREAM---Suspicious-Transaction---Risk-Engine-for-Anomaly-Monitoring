package com.example.stream.ui.predict

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.stream.data.model.PredictRequest
import com.example.stream.data.model.PredictResponse
import com.example.stream.data.repository.StreamRepository
import com.example.stream.ui.components.UiState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class PredictViewModel : ViewModel() {
    private val repo = StreamRepository()
    private val _result = MutableStateFlow<UiState<PredictResponse>?>(null)
    val result = _result.asStateFlow()

    fun predict(
        amount: Double, numTenderers: Int, durationDays: Int,
        procurementMethod: String, classification: String, buyerName: String
    ) {
        viewModelScope.launch {
            _result.value = UiState.Loading
            repo.predict(PredictRequest(amount, numTenderers, durationDays, procurementMethod, classification, buyerName)).fold(
                { _result.value = UiState.Success(it) },
                { _result.value = UiState.Error(it.localizedMessage ?: "Prediction failed") }
            )
        }
    }

    fun reset() { _result.value = null }
}
