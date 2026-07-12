package com.example.mirrorme

import android.content.Context
import android.widget.Toast
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForwardIos
import androidx.compose.material.icons.automirrored.filled.ExitToApp
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.filled.Upload
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.io.File
import java.io.FileOutputStream
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily

val MM_Font = FontFamily(
    Font(R.font.A2Z_4Regular, FontWeight.Normal),
    Font(R.font.A2Z_7Bold, FontWeight.Bold),
    Font(R.font.A2Z_3Light, FontWeight.Light),
    Font(R.font.A2Z_5Medium, FontWeight.Medium)
)


// 디자인 가이드 컬러 정의
private val DeepGreen = Color(0xFF1A3F2C)
private val LightGray = Color(0xFFF5F5F5)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnalysisScreen(
    onNavigateToResult: (SkinAnalysisResponse) -> Unit = {}
) {
    val context = LocalContext.current
    val scrollState = rememberScrollState()
    var isLoading by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                navigationIcon = {
                    IconButton(onClick = { /* 메뉴 로직 */ }) {
                        Icon(
                            imageVector = Icons.Default.Menu,
                            contentDescription = "Menu",
                            tint = Color.Black
                        )
                    }
                },
                title = {
                    Image(
                        painter = painterResource(id = R.drawable.logo), // 업로드한 이미지 리소스 ID
                        contentDescription = "MirrorMe Logo",
                        modifier = Modifier.height(48.dp), // 기존 텍스트 크기와 비슷하게 높이 조절
                        contentScale = ContentScale.Fit
                    )
                },
                actions = {
                    IconButton(onClick = { /* 로그아웃 로직 */ }) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ExitToApp,
                            contentDescription = "Exit",
                            tint = Color.Black
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.White)
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .background(Color.White)
                .verticalScroll(scrollState)
                .padding(horizontal = 20.dp)
        ) {
            Spacer(modifier = Modifier.height(20.dp))

            // 1. AI로 피부 분석 섹션
            Text(
                text = "AI로 피부 분석",
                fontFamily = MM_Font,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(220.dp)
                    .clip(RoundedCornerShape(16.dp))
                    .background(LightGray)
                    .clickable(enabled = !isLoading) {
                        performUpload(context, { isLoading = it }, onNavigateToResult)
                    },
                contentAlignment = Alignment.Center
            ) {
                if (isLoading) {
                    CircularProgressIndicator(color = DeepGreen)
                } else {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(
                            imageVector = Icons.Default.Upload,
                            contentDescription = "Upload",
                            modifier = Modifier.size(48.dp),
                            tint = Color.Black.copy(alpha = 0.7f)
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = "사진을 업로드하세요",
                            fontFamily = MM_Font,
                            fontSize = 15.sp,
                            fontWeight = FontWeight.Light,
                            color = Color.Black.copy(alpha = 0.6f),
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            // 2. 지난 처방전 섹션
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "지난 처방전",
                    fontFamily = MM_Font,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.width(8.dp))
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.ArrowForwardIos,
                    contentDescription = "Go to History",
                    modifier = Modifier.size(16.dp),
                    tint = Color.Gray
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 가로 스크롤 히스토리 리스트
            val historyItems = listOf("4월 27일", "4월 11일", "3월 15일")
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(bottom = 8.dp)
            ) {
                items(historyItems) { date ->
                    HistoryCard(date)
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            // 3. 오늘의 한 줄 팁 섹션
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = LightGray)
            ) {
                Column(modifier = Modifier.padding(24.dp)) {
                    Text(
                        text = "오늘의 한 줄 팁",
                        color = Color.Gray,
                        fontFamily = MM_Font,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "물 한 잔이 피부를 바꿉니다. 오늘 하루 1.5L 수분 섭취를 목표로 해볼까요?",
                        fontFamily = MM_Font,
                        fontWeight = FontWeight.Medium,
                        lineHeight = 24.sp
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(40.dp))
        }
    }
}

@Composable
fun HistoryCard(date: String) {
    Box(
        modifier = Modifier
            .size(150.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(DeepGreen)
            .padding(20.dp),
        contentAlignment = Alignment.BottomStart
    ) {
        val parts = date.split(" ")
        Column {
            Text(
                text = parts.getOrNull(0) ?: "",
                color = Color.White,
                fontFamily = MM_Font,
                fontSize = 25.sp,
                fontWeight = FontWeight.SemiBold,
                lineHeight = 36.sp
            )
            Text(
                text = parts.getOrNull(1) ?: "",
                color = Color.White,
                fontFamily = MM_Font,
                fontSize = 32.sp,
                fontWeight = FontWeight.ExtraBold,
                lineHeight = 36.sp
            )
        }
    }
}

private fun performUpload(
    context: Context,
    setLoading: (Boolean) -> Unit,
    onSuccess: (SkinAnalysisResponse) -> Unit
) {
    setLoading(true)
    
    // 테스트를 위한 임시 파일 생성 로직
    val file = prepareImageFile(context)
    val requestFile = file.asRequestBody("image/*".toMediaTypeOrNull())
    val body = MultipartBody.Part.createFormData("image", file.name, requestFile)

    RetrofitClient.service.analyzeSkin(body).enqueue(object : Callback<SkinAnalysisResponse> {
        override fun onResponse(
            call: Call<SkinAnalysisResponse>,
            response: Response<SkinAnalysisResponse>
        ) {
            setLoading(false)
            if (response.isSuccessful && response.body() != null) {
                onSuccess(response.body()!!)
            } else {
                Toast.makeText(context, "분석 실패: ${response.code()}", Toast.LENGTH_SHORT).show()
            }
        }

        override fun onFailure(call: Call<SkinAnalysisResponse>, t: Throwable) {
            setLoading(false)
            Toast.makeText(context, "네트워크 오류가 발생했습니다.", Toast.LENGTH_LONG).show()
        }
    })
}

/**
 * 전송할 이미지 파일을 준비하는 헬퍼 함수
 */
fun prepareImageFile(context: Context): File {
    val file = File(context.cacheDir, "skin_analysis_target.jpg")
    try {
        if (file.exists()) file.delete()
        context.assets.open("sample.jpg").use { input ->
            FileOutputStream(file).use { output ->
                input.copyTo(output)
            }
        }
    } catch (e: Exception) {
        file.createNewFile()
    }
    return file
}

@Preview(showBackground = true)
@Composable
fun AnalysisScreenPreview() {
    AnalysisScreen()
}
