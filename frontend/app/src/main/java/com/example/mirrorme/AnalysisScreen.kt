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

val MM_Font: FontFamily by lazy {
    try {
        FontFamily(
            Font(R.font.a2z_1thin, FontWeight.Thin),
            Font(R.font.a2z_2extralight, FontWeight.ExtraLight),
            Font(R.font.a2z_3light, FontWeight.Light),
            Font(R.font.a2z_4regular, FontWeight.Normal),
            Font(R.font.a2z_5medium, FontWeight.Medium),
            Font(R.font.a2z_6semibold, FontWeight.SemiBold),
            Font(R.font.a2z_7bold, FontWeight.Bold),
            Font(R.font.a2z_8extrabold, FontWeight.ExtraBold),
            Font(R.font.a2z_9black, FontWeight.Black)
        )
    } catch (e: Throwable) {
        // Fallback to default font family if resources are temporarily unavailable (common in Previews)
        FontFamily.Default
    }
}


// 디자인 가이드 컬러 정의
private val DeepGreen = Color(0xFF1A3F2C)
private val LightGray = Color(0xFFF5F5F5)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnalysisScreen(
    onNavigateToResult: (SkinAnalysisResponse) -> Unit = {},
    onNavigateToHistory: (String) -> Unit = {}
) {
    val context = LocalContext.current
    val scrollState = rememberScrollState()
    var isLoading by remember { mutableStateOf(false) }
    var showGuidance by remember { mutableStateOf(false) }
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)

    // 히스토리 데이터 정의
    val historyItems = remember {
        listOf(
            "2024-04-27",
            "2024-04-11",
            "2024-03-15",
            "2024-02-28"
        )
    }

    if (showGuidance) {
        ModalBottomSheet(
            onDismissRequest = { showGuidance = false },
            sheetState = sheetState,
            containerColor = Color.Black,
            dragHandle = { BottomSheetDefaults.DragHandle(color = Color.White.copy(alpha = 0.3f)) }
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState())
                    .padding(start = 24.dp, end = 24.dp, bottom = 48.dp)
            ) {
                Text(
                    text = "좋은 예",
                    color = Color.White,
                    fontFamily = MM_Font,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(16.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    GuidanceImage(modifier = Modifier.weight(1f), resId = R.drawable.good_ex1)
                    GuidanceImage(modifier = Modifier.weight(1f), resId = R.drawable.good_ex2)
                }

                Spacer(modifier = Modifier.height(24.dp))

                Text(
                    text = "잘못된 예",
                    color = Color.White,
                    fontFamily = MM_Font,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(16.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    GuidanceImage(modifier = Modifier.weight(1f), resId = R.drawable.bad_ex1)
                    GuidanceImage(modifier = Modifier.weight(1f), resId = R.drawable.bad_ex2)
                }

                Spacer(modifier = Modifier.height(48.dp))

                Button(
                    onClick = {
                        showGuidance = false
                        performUpload(context, { isLoading = it }, onNavigateToResult)
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(75.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color.White,
                        contentColor = Color.Black
                    ),
                    shape = RoundedCornerShape(28.dp)
                ) {
                    Text(
                        text = "확인",
                        fontFamily = MM_Font,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }

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
                        painter = painterResource(id = R.drawable.mirrorme_logo_header_small), // 업로드한 이미지 리소스 ID
                        modifier = Modifier.height(40.dp),
                        contentDescription = "MirrorMe Logo", // 기존 텍스트 크기와 비슷하게 높이 조절
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
                        showGuidance = true
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
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(bottom = 8.dp)
            ) {
                items(historyItems) { dateString ->
                    HistoryCard(date = dateString, onClick = onNavigateToHistory)
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
fun GuidanceImage(modifier: Modifier = Modifier, resId: Int?) {
    Box(
        modifier = modifier
            .aspectRatio(1f)
            .clip(RoundedCornerShape(12.dp))
            .background(Color.DarkGray),
        contentAlignment = Alignment.Center
    ) {
        if (resId != null) {
            Image(
                painter = painterResource(id = resId),
                contentDescription = null,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )
        } else {
            Text("이미지", color = Color.Gray, fontSize = 12.sp)
        }
    }
}

@Composable
fun HistoryCard(date: String, onClick: (String) -> Unit) {
    // 날짜 포맷팅: "2024-04-27" -> "04.27" & "2024"
    val parts = date.split("-")
    val year = parts.getOrNull(0) ?: ""
    val monthDay = if (parts.size >= 3) "${parts[1]}.${parts[2]}" else ""

    Box(
        modifier = Modifier
            .size(150.dp)
            .clip(RoundedCornerShape(16.dp))
            .background(DeepGreen)
            .clickable { onClick(date) }
            .padding(20.dp),
        contentAlignment = Alignment.BottomStart
    ) {
        Column {
            Text(
                text = year,
                color = Color.White.copy(alpha = 0.7f),
                fontFamily = MM_Font,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = monthDay,
                color = Color.White,
                fontFamily = MM_Font,
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                lineHeight = 34.sp
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "자세히 보기 >",
                color = Color.White.copy(alpha = 0.9f),
                fontFamily = MM_Font,
                fontSize = 12.sp,
                fontWeight = FontWeight.Light
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
