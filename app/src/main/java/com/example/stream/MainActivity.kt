package com.example.stream

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.example.stream.ui.login.LoginScreen
import com.example.stream.ui.navigation.MainScreen
import com.example.stream.ui.theme.StreamTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            StreamTheme(dynamicColor = false) {
                var isLoggedIn by remember { mutableStateOf(false) }

                if (isLoggedIn) {
                    MainScreen()
                } else {
                    LoginScreen(
                        modifier = Modifier,
                        onLoginSuccess = { isLoggedIn = true }
                    )
                }
            }
        }
    }
}