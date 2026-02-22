package com.example.stream.data.api

import com.example.stream.data.model.BidTender
import com.google.gson.*
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.lang.reflect.Type
import java.util.concurrent.TimeUnit

class BidTenderDeserializer : JsonDeserializer<BidTender> {
    override fun deserialize(json: JsonElement, type: Type, ctx: JsonDeserializationContext): BidTender {
        val o = json.asJsonObject
        return BidTender(
            ocid = o.get("ocid")?.asString ?: "",
            tenderId = o.get("tender_id")?.asString ?: o.get("tender/id")?.asString ?: "",
            title = o.get("tender_title")?.asString ?: o.get("tender/title")?.asString ?: "",
            buyerName = o.get("buyer_name")?.asString ?: o.get("buyer/name")?.asString ?: "",
            category = o.get("category")?.asString ?: o.get("tenderclassification/description")?.asString ?: "",
            procurementMethod = o.get("procurement_method")?.asString ?: o.get("tender/procurementMethod")?.asString ?: "",
            amount = o.get("amount")?.asDouble ?: 0.0,
            numTenderers = o.get("num_tenderers")?.asDouble ?: 0.0,
            durationDays = o.get("duration_days")?.asInt ?: 0,
            flagSingleBidder = o.get("flag_single_bidder")?.asInt ?: 0,
            flagZeroBidders = o.get("flag_zero_bidders")?.asInt ?: 0,
            flagShortWindow = o.get("flag_short_window")?.asInt ?: 0,
            flagNonOpen = o.get("flag_non_open")?.asInt ?: 0,
            flagHighValue = o.get("flag_high_value")?.asInt ?: 0,
            flagBuyerConcentration = o.get("flag_buyer_concentration")?.asInt ?: 0,
            flagRoundAmount = o.get("flag_round_amount")?.asInt ?: 0,
            mlAnomalyFlag = o.get("ml_anomaly_flag")?.asInt ?: 0,
            anomalyScore = o.get("anomaly_score")?.asDouble ?: 0.0,
            riskScore = o.get("risk_score")?.asDouble ?: 0.0,
            riskTier = o.get("risk_tier")?.asString ?: "",
            riskExplanation = o.get("risk_explanation")?.asString ?: "",
            predictedSuspicious = o.get("predicted_suspicious")?.asInt ?: 0,
            suspicionProbability = o.get("suspicion_probability")?.asDouble ?: 0.0,
            predictedRiskTier = o.get("predicted_risk_tier")?.asString ?: ""
        )
    }
}

object RetrofitClient {
    private const val BASE_URL = "http://192.168.114.61:8000/"
    private val loggingInterceptor = HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC }
    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(60, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .retryOnConnectionFailure(true)
        .build()

    private val gson: Gson = GsonBuilder()
        .registerTypeAdapter(BidTender::class.java, BidTenderDeserializer())
        .create()

    private val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create(gson))
        .build()

    val api: StreamApi = retrofit.create(StreamApi::class.java)
}