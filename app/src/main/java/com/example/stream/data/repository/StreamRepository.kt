package com.example.stream.data.repository

import com.example.stream.data.api.RetrofitClient
import com.example.stream.data.model.*

class StreamRepository {
    private val api = RetrofitClient.api
    suspend fun getDashboardKpis(): Result<DashboardKpis> = runCatching { api.getDashboardKpis() }
    suspend fun getAlerts(page: Int = 1, pageSize: Int = 20, alertType: String? = null, riskTier: String? = null, sortBy: String? = null, sortOrder: String? = null): Result<AlertResponse> = runCatching { api.getAlerts(page, pageSize, alertType, riskTier, sortBy, sortOrder) }
    suspend fun getVendorProfile(vendorId: String): Result<VendorProfile> = runCatching { api.getVendorProfile(vendorId) }
    suspend fun searchVendors(query: String): Result<VendorSearchResponse> = runCatching { api.searchVendors(query) }
    suspend fun getBidAnalysis(page: Int = 1, pageSize: Int = 20, riskTier: String? = null, sortBy: String? = null, sortOrder: String? = null): Result<BidAnalysisResponse> = runCatching { api.getBidAnalysis(page, pageSize, riskTier, sortBy, sortOrder) }
    suspend fun getBidSummary(): Result<BidSummary> = runCatching { api.getBidSummary() }
    suspend fun getRecentActivity(limit: Int = 50, eventType: String? = null): Result<ActivityResponse> = runCatching { api.getRecentActivity(limit, eventType) }
    suspend fun getRiskDistribution(): Result<RiskDistributionStats> = runCatching { api.getRiskDistribution() }
    suspend fun getTopRiskBuyers(): Result<TopRiskBuyersResponse> = runCatching { api.getTopRiskBuyers() }
    suspend fun getBondSummary(): Result<BondSummary> = runCatching { api.getBondSummary() }
    suspend fun predict(request: PredictRequest): Result<PredictResponse> = runCatching { api.predict(request) }
}