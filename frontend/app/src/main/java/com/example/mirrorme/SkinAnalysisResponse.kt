package com.example.mirrorme

import com.google.gson.annotations.SerializedName

data class SkinAnalysisResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("total_score") val totalScore: Int,
    @SerializedName("scores") val scores: SkinDetails,
    @SerializedName("raw_values") val rawValues: Map<String, Any>? = null
)

data class SkinDetails(
    @SerializedName("acne") val acne: Int,
    @SerializedName("pigmentation") val pigmentation: Int,
    @SerializedName("pore") val pore: Int,
    @SerializedName("sebum") val sebum: Int
)
