package com.example.mirrorme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.example.mirrorme.ui.theme.MirrorMeTheme

sealed interface Screen {
    object Analysis : Screen
    data class Report(val response: SkinAnalysisResponse) : Screen
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MirrorMeTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    var currentScreen by remember { mutableStateOf<Screen>(Screen.Analysis) }

                    when (val screen = currentScreen) {
                        is Screen.Analysis -> {
                            AnalysisScreen(
                                onNavigateToResult = { response ->
                                    currentScreen = Screen.Report(response)
                                },
                                onNavigateToHistory = { date ->
                                    // 해당 날짜에 맞는 더미 데이터 생성하여 ReportScreen으로 이동
                                    val dummyResponse = SkinAnalysisResponse(
                                        success = true,
                                        totalScore = when(date) {
                                            "2024-04-27" -> 78
                                            "2024-04-11" -> 72
                                            "2024-03-15" -> 65
                                            else -> 60
                                        },
                                        scores = SkinDetails(acne = 75, pigmentation = 60, pore = 70, sebum = 55)
                                    )
                                    currentScreen = Screen.Report(dummyResponse)
                                }
                            )
                        }
                        is Screen.Report -> {
                            ReportScreen(
                                response = screen.response,
                                onBackClick = {
                                    currentScreen = Screen.Analysis
                                }
                            )
                        }
                    }
                }
            }
        }
    }
}