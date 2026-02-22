package com.example.stream.data.model

import com.google.gson.annotations.SerializedName

data class DashboardKpis(
    @SerializedName("active_flags") val activeFlags: Int = 0,
    @SerializedName("at_risk_value") val atRiskValue: Double = 0.0,
    @SerializedName("at_risk_value_cr") val atRiskValueCr: Double = 0.0,
    @SerializedName("vendors_tracked") val vendorsTracked: Int = 0,
    @SerializedName("precision_rate") val precisionRate: Double = 0.0,
    @SerializedName("bid_rigging_detected") val bidRiggingDetected: Int = 0,
    @SerializedName("shell_networks_mapped") val shellNetworksMapped: Int = 0,
    @SerializedName("political_connections") val politicalConnections: Int = 0,
    @SerializedName("false_positive_control") val falsePositiveControl: Double = 0.0,
    @SerializedName("total_tenders") val totalTenders: Int = 0,
    @SerializedName("total_companies") val totalCompanies: Int = 0
)

data class AlertResponse(
    val total: Int = 0, val page: Int = 1,
    @SerializedName("page_size") val pageSize: Int = 20,
    @SerializedName("total_pages") val totalPages: Int = 1,
    val alerts: List<AlertItem> = emptyList()
)

data class AlertItem(
    @SerializedName("alert_id") val alertId: String = "",
    @SerializedName("alert_type") val alertType: String = "",
    @SerializedName("sub_type") val subType: String = "",
    @SerializedName("risk_score") val riskScore: Double = 0.0,
    val confidence: Double = 0.0,
    @SerializedName("risk_tier") val riskTier: String = "",
    val title: String = "",
    @SerializedName("tender_id") val tenderId: String? = null,
    @SerializedName("buyer_name") val buyerName: String? = null,
    val category: String? = null,
    @SerializedName("procurement_method") val procurementMethod: String? = null,
    val amount: Double? = null,
    @SerializedName("amount_cr") val amountCr: Double? = null,
    @SerializedName("num_tenderers") val numTenderers: Double? = null,
    @SerializedName("duration_days") val durationDays: Int? = null,
    @SerializedName("purchaser_name") val purchaserName: String? = null,
    @SerializedName("total_bond_value") val totalBondValue: Double? = null,
    @SerializedName("total_bond_value_cr") val totalBondValueCr: Double? = null,
    @SerializedName("total_bonds") val totalBonds: Int? = null,
    @SerializedName("parties_funded") val partiesFunded: List<String>? = null,
    @SerializedName("flags_triggered") val flagsTriggered: List<String> = emptyList(),
    val explanation: String = "",
    @SerializedName("evidence_strength") val evidenceStrength: Double = 0.0
) {
    val isProcurement: Boolean get() = tenderId != null
    val displayEntity: String get() = buyerName ?: purchaserName ?: ""
    val displayAmount: String get() = when {
        amountCr != null -> "Rs${String.format("%.1f", amountCr)}Cr"
        totalBondValueCr != null -> "Rs${String.format("%.0f", totalBondValueCr)}Cr"
        else -> ""
    }
}

data class VendorProfile(
    @SerializedName("vendor_id") val vendorId: String = "",
    @SerializedName("company_name") val companyName: String = "",
    val cin: String = "", val status: String = "",
    @SerializedName("registered_address") val registeredAddress: String = "",
    val industry: String = "",
    @SerializedName("overall_risk_score") val overallRiskScore: Int = 0,
    @SerializedName("risk_tier") val riskTier: String = "",
    @SerializedName("sub_scores") val subScores: SubScores = SubScores(),
    @SerializedName("total_tenders") val totalTenders: Int = 0,
    @SerializedName("total_contract_value") val totalContractValue: Double = 0.0,
    @SerializedName("flags_triggered") val flagsTriggered: Int = 0,
    @SerializedName("connections_count") val connectionsCount: Int = 0,
    val connections: List<VendorConnection> = emptyList(),
    @SerializedName("recent_tenders") val recentTenders: List<RecentTender> = emptyList()
)
data class SubScores(@SerializedName("bid_pattern") val bidPattern: Int = 0, @SerializedName("shell_risk") val shellRisk: Int = 0, val political: Int = 0, val financials: Int = 0)
data class VendorConnection(val type: String = "", @SerializedName("entity_name") val entityName: String = "", val detail: String = "", val amount: String? = null, val date: String? = null, @SerializedName("risk_level") val riskLevel: String = "")
data class RecentTender(@SerializedName("tender_id") val tenderId: String = "", val title: String = "", val amount: Double = 0.0, @SerializedName("risk_score") val riskScore: Int = 0, val date: String = "")
data class VendorSearchResponse(val query: String = "", val count: Int = 0, val results: List<VendorSearchResult> = emptyList())
data class VendorSearchResult(@SerializedName("vendor_id") val vendorId: String = "", @SerializedName("company_name") val companyName: String = "", val cin: String = "", @SerializedName("overall_risk_score") val overallRiskScore: Int = 0, @SerializedName("risk_tier") val riskTier: String = "", val source: String = "")

data class BidAnalysisResponse(val total: Int = 0, val page: Int = 1, @SerializedName("page_size") val pageSize: Int = 20, @SerializedName("total_pages") val totalPages: Int = 1, val tenders: List<BidTender> = emptyList())

data class BidTender(
    val ocid: String = "",
    val tenderId: String = "",
    val title: String = "",
    val buyerName: String = "",
    val category: String = "",
    val procurementMethod: String = "",
    val amount: Double = 0.0,
    val numTenderers: Double = 0.0,
    val durationDays: Int = 0,
    val flagSingleBidder: Int = 0,
    val flagZeroBidders: Int = 0,
    val flagShortWindow: Int = 0,
    val flagNonOpen: Int = 0,
    val flagHighValue: Int = 0,
    val flagBuyerConcentration: Int = 0,
    val flagRoundAmount: Int = 0,
    val mlAnomalyFlag: Int = 0,
    val anomalyScore: Double = 0.0,
    val riskScore: Double = 0.0,
    val riskTier: String = "",
    val riskExplanation: String = "",
    val predictedSuspicious: Int = 0,
    val suspicionProbability: Double = 0.0,
    val predictedRiskTier: String = ""
)

data class BidSummary(
    @SerializedName("total_tenders") val totalTenders: Int = 0,
    @SerializedName("risk_distribution") val riskDistribution: Map<String, Int> = emptyMap(),
    @SerializedName("flag_counts") val flagCounts: FlagCounts = FlagCounts(),
    @SerializedName("top_categories") val topCategories: List<TopCategory> = emptyList(),
    @SerializedName("top_buyers") val topBuyers: List<TopBuyer> = emptyList(),
    @SerializedName("amount_stats") val amountStats: AmountStats = AmountStats()
) {
    val highRisk: Int get() = riskDistribution.entries.find { it.key.contains("High") }?.value ?: 0
    val mediumRisk: Int get() = riskDistribution.entries.find { it.key.contains("Medium") }?.value ?: 0
    val lowRisk: Int get() = riskDistribution.entries.find { it.key.contains("Low") }?.value ?: 0
}

data class FlagCounts(@SerializedName("single_bidder") val singleBidder: Int = 0, @SerializedName("zero_bidders") val zeroBidders: Int = 0, @SerializedName("short_window") val shortWindow: Int = 0, @SerializedName("non_open") val nonOpen: Int = 0, @SerializedName("high_value") val highValue: Int = 0, @SerializedName("buyer_concentration") val buyerConcentration: Int = 0, @SerializedName("round_amount") val roundAmount: Int = 0, @SerializedName("ml_anomaly") val mlAnomaly: Int = 0)
data class TopCategory(@SerializedName("tenderclassification/description") val category: String = "", val total: Int = 0, val flagged: Int = 0, @SerializedName("avg_risk") val avgRisk: Double = 0.0, @SerializedName("total_value") val totalValue: Double = 0.0)
data class TopBuyer(@SerializedName("buyer/name") val buyerName: String = "", val total: Int = 0, val flagged: Int = 0, @SerializedName("avg_risk") val avgRisk: Double = 0.0, @SerializedName("total_value") val totalValue: Double = 0.0)
data class AmountStats(val total: Double = 0.0, val mean: Double = 0.0, val median: Double = 0.0, val max: Double = 0.0)

data class ActivityResponse(val total: Int = 0, val activities: List<ActivityEvent> = emptyList())
data class ActivityEvent(@SerializedName("event_type") val eventType: String = "", val icon: String = "", val title: String = "", val subtitle: String = "", @SerializedName("risk_tier") val riskTier: String = "", @SerializedName("risk_score") val riskScore: Double? = null, @SerializedName("amount_cr") val amountCr: Double = 0.0, @SerializedName("entity_name") val entityName: String = "", @SerializedName("party_name") val partyName: String = "", @SerializedName("sort_key") val sortKey: Double = 0.0)

data class RiskDistributionStats(val bins: List<Double> = emptyList(), val counts: List<Int> = emptyList(), val mean: Double = 0.0, val median: Double = 0.0, val std: Double = 0.0)
data class TopRiskBuyersResponse(val buyers: List<TopRiskBuyer> = emptyList())
data class TopRiskBuyer(@SerializedName("buyer_name") val buyerName: String = "", @SerializedName("avg_risk_score") val avgRiskScore: Double = 0.0, @SerializedName("total_tenders") val totalTenders: Int = 0, @SerializedName("flagged_tenders") val flaggedTenders: Int = 0, @SerializedName("total_value_cr") val totalValueCr: Double = 0.0, @SerializedName("dominant_category") val dominantCategory: String = "")

data class BondSummary(@SerializedName("total_flows") val totalFlows: Int = 0, @SerializedName("total_value") val totalValue: Double = 0.0, @SerializedName("total_value_cr") val totalValueCr: Double = 0.0, @SerializedName("unique_purchasers") val uniquePurchasers: Int = 0, @SerializedName("unique_parties") val uniqueParties: Int = 0, @SerializedName("party_breakdown") val partyBreakdown: List<BondParty> = emptyList())
data class BondParty(@SerializedName("party_name") val partyName: String = "", @SerializedName("total_value") val totalValue: Long = 0, @SerializedName("total_bonds") val totalBonds: Int = 0, @SerializedName("unique_purchasers") val uniquePurchasers: Int = 0) { val totalValueCr: Double get() = totalValue / 10000000.0 }

data class PredictRequest(@SerializedName("tender/value/amount") val amount: Double, @SerializedName("tender/numberOfTenderers") val numTenderers: Int, @SerializedName("tender/tenderPeriod/durationInDays") val durationDays: Int, @SerializedName("tender/procurementMethod") val procurementMethod: String, @SerializedName("tenderclassification/description") val classification: String, @SerializedName("buyer/name") val buyerName: String)
data class PredictResponse(@SerializedName("predicted_suspicious") val predictedSuspicious: Int = 0, @SerializedName("suspicion_probability") val suspicionProbability: Double = 0.0, @SerializedName("predicted_risk_tier") val predictedRiskTier: String = "")