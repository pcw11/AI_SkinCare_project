package com.example.mirrorme

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {
    // [PC_IP_ADDRESS]를 실제 서버 IP로 변경하여 사용하세요.
    // 에뮬레이터에서 로컬 서버 접속 시에는 10.0.2.2를 사용합니다.
    private const val BASE_URL = "http://10.0.2.2:5000/"

    val service: SkinApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(SkinApiService::class.java)
    }
}
