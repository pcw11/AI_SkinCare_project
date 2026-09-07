package com.example.mirrorme

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.mirrorme.ui.theme.MirrorMeTheme

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LoginScreen(
    onLoginClick: () -> Unit = {},
    onGoogleLoginClick: () -> Unit = {}
) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.White)
            .padding(horizontal = 24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Spacer(modifier = Modifier.height(80.dp))

        // 로고 (Logo)
        Image(
            painter = painterResource(id = R.drawable.mirrorme_logo_header),
            contentDescription = "MirrorMe Logo",
            modifier = Modifier.height(50.dp),
            contentScale = ContentScale.Fit
        )

        Spacer(modifier = Modifier.height(40.dp))

        // 로그인 제목
        Text(
            text = "로그인",
            fontFamily = MM_Font,
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            color = Color.Black
        )

        Spacer(modifier = Modifier.height(24.dp))

        // 이메일 입력
        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            placeholder = { 
                Text(
                    text = "email@domain.com", 
                    color = Color.Gray.copy(alpha = 0.6f),
                    fontFamily = MM_Font
                ) 
            },
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(8.dp),
            colors = OutlinedTextFieldDefaults.colors(
                unfocusedBorderColor = Color.LightGray.copy(alpha = 0.5f),
                focusedBorderColor = Color.Black,
                focusedContainerColor = Color.Transparent,
                unfocusedContainerColor = Color.Transparent
            ),
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email)
        )

        Spacer(modifier = Modifier.height(12.dp))

        // 비밀번호 입력
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            placeholder = { 
                Text(
                    text = "비밀번호", 
                    color = Color.Gray.copy(alpha = 0.6f),
                    fontFamily = MM_Font
                ) 
            },
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(8.dp),
            visualTransformation = PasswordVisualTransformation(),
            colors = OutlinedTextFieldDefaults.colors(
                unfocusedBorderColor = Color.LightGray.copy(alpha = 0.5f),
                focusedBorderColor = Color.Black,
                focusedContainerColor = Color.Transparent,
                unfocusedContainerColor = Color.Transparent
            ),
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password)
        )

        Spacer(modifier = Modifier.height(24.dp))

        // 계속 버튼
        Button(
            onClick = onLoginClick,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color.Black),
            shape = RoundedCornerShape(8.dp)
        ) {
            Text(
                text = "계속",
                fontFamily = MM_Font,
                color = Color.White,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        // 구분선 (Divider with "또는")
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            HorizontalDivider(
                modifier = Modifier.weight(1f),
                thickness = 1.dp,
                color = Color.LightGray.copy(alpha = 0.5f)
            )
            Text(
                text = "또는",
                modifier = Modifier.padding(horizontal = 16.dp),
                color = Color.Gray,
                fontSize = 14.sp,
                fontFamily = MM_Font
            )
            HorizontalDivider(
                modifier = Modifier.weight(1f),
                thickness = 1.dp,
                color = Color.LightGray.copy(alpha = 0.5f)
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        // 구글 로그인 버튼
        Button(
            onClick = onGoogleLoginClick,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFEEEEEE)),
            shape = RoundedCornerShape(8.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                // 구글 아이콘이 있다면 여기에 추가 (현재는 텍스트만)
                // Icon(painter = painterResource(id = R.drawable.ic_google), ...)
                Text(
                    text = "G ",
                    color = Color(0xFF4285F4), // 구글 블루
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp
                )
                Text(
                    text = "Google 계정으로 계속하기",
                    fontFamily = MM_Font,
                    color = Color.Black,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Medium
                )
            }
        }

        Spacer(modifier = Modifier.weight(1f))

        // 푸터 텍스트
        Text(
            text = "계속을 클릭하면 당사의 서비스 이용 약관 및 개인정보 처리방침에 동의하는 것으로 간주됩니다.",
            fontFamily = MM_Font,
            color = Color.Gray,
            fontSize = 12.sp,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(bottom = 32.dp),
            lineHeight = 18.sp
        )
    }
}

@Preview(showBackground = true)
@Composable
fun LoginScreenPreview() {
    MirrorMeTheme {
        LoginScreen()
    }
}
