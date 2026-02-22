package com.example.stream.ui.bid

import com.example.stream.data.model.BidTender

/**
 * Simple holder for the currently selected tender.
 * Used to pass the tender object between BidAnalysisScreen and BidDetailScreen
 * without serialization through Navigation arguments.
 */
object SelectedTender {
    var tender: BidTender? = null
}
