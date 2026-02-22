package com.example.stream.data.api

import com.example.stream.data.model.*
import retrofit2.http.*

interface StreamApi {
    @GET("/dashboard/kpis")
    suspend fun getDashboardKpis(): DashboardKpis
    @GET("/alerts")
    suspend fun getAlerts(@Query("page") page: Int = 1, @Query("page_size") pageSize: Int = 20, @Query("alert_type") alertType: String? = null, @Query("risk_tier") riskTier: String? = null, @Query("sort_by") sortBy: String? = null, @Query("sort_order") sortOrder: String? = null): AlertResponse
    @GET("/vendor/{vendor_id}")
    suspend fun getVendorProfile(@Path("vendor_id") vendorId: String): VendorProfile
    @GET("/vendor/search/{query}")
    suspend fun searchVendors(@Path("query") query: String, @Query("limit") limit: Int = 20): VendorSearchResponse
    @GET("/bid-analysis")
    suspend fun getBidAnalysis(@Query("page") page: Int = 1, @Query("page_size") pageSize: Int = 20, @Query("risk_tier") riskTier: String? = null, @Query("sort_by") sortBy: String? = null, @Query("sort_order") sortOrder: String? = null): BidAnalysisResponse
    @GET("/bid-analysis/summary")
    suspend fun getBidSummary(): BidSummary
    @GET("/activity/recent")
    suspend fun getRecentActivity(@Query("limit") limit: Int = 50, @Query("event_type") eventType: String? = null): ActivityResponse
    @GET("/stats/risk-distribution")
    suspend fun getRiskDistribution(): RiskDistributionStats
    @GET("/stats/top-risk-buyers")
    suspend fun getTopRiskBuyers(@Query("limit") limit: Int = 20): TopRiskBuyersResponse
    @GET("/stats/bond-summary")
    suspend fun getBondSummary(): BondSummary
    @POST("/predict")
    suspend fun predict(@Body request: PredictRequest): PredictResponse
}