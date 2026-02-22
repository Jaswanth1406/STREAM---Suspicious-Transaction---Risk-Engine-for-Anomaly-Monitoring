package com.example.stream.ui.login

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Email
import androidx.compose.material.icons.rounded.Lock
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.TransformOrigin
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.stream.ui.theme.StreamTheme
import kotlinx.coroutines.delay

@Composable
fun LoginScreen(modifier: Modifier = Modifier) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(false) }

    // Screen Entrance Animation 
    // This creates a buttery smooth slide-up and fade-in when the UI loads
    var isScreenVisible by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        delay(100)
        isScreenVisible = true
    }

    val animatedAlpha by animateFloatAsState(
        targetValue = if (isScreenVisible) 1f else 0f,
        animationSpec = tween(durationMillis = 800, easing = FastOutSlowInEasing),
        label = "alpha"
    )
    
    val animatedOffsetY by animateFloatAsState(
        targetValue = if (isScreenVisible) 0f else 50f,
        animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy, stiffness = Spring.StiffnessLow),
        label = "offsetY"
    )

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color(0xFFF8FAFC)), // Slate 50 (Off-white)
        contentAlignment = Alignment.Center
    ) {
        // Decorative floating light-themed orbs
        FloatingOrbs(isVisible = isScreenVisible)

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp)
                .graphicsLayer {
                    alpha = animatedAlpha
                    translationY = animatedOffsetY
                }
                .shadow(
                    elevation = 24.dp,
                    shape = RoundedCornerShape(32.dp),
                    spotColor = Color(0xFF4C76EB).copy(alpha = 0.15f) // Soft blue shadow
                ),
            shape = RoundedCornerShape(32.dp),
            colors = CardDefaults.cardColors(
                containerColor = Color.White.copy(alpha = 0.95f) // Almost solid white
            )
        ) {
            Column(
                modifier = Modifier
                    .padding(32.dp)
                    .fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Animated Title Array
                AnimatedVisibility(
                    visible = isScreenVisible,
                    enter = slideInVertically(initialOffsetY = { 20 }, animationSpec = tween(600, delayMillis = 200)) + fadeIn(tween(600, delayMillis = 200))
                ) {
                    Text(
                        text = "Welcome Back",
                        style = MaterialTheme.typography.displaySmall.copy(
                            fontWeight = FontWeight.ExtraBold,
                            color = Color(0xFF1E293B), // Slate 800
                            letterSpacing = (-0.5).sp
                        ),
                        modifier = Modifier.padding(bottom = 8.dp)
                    )
                }

                AnimatedVisibility(
                    visible = isScreenVisible,
                    enter = slideInVertically(initialOffsetY = { 20 }, animationSpec = tween(600, delayMillis = 300)) + fadeIn(tween(600, delayMillis = 300))
                ) {
                    Text(
                        text = "Log in to your account",
                        style = MaterialTheme.typography.bodyLarge.copy(
                            color = Color(0xFF64748B) // Slate 500
                        ),
                        modifier = Modifier.padding(bottom = 40.dp)
                    )
                }

                // Staggered Entrance for Text Fields
                AnimatedVisibility(
                    visible = isScreenVisible,
                    enter = slideInHorizontally(initialOffsetX = { -50 }, animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy, stiffness = Spring.StiffnessLow)) + fadeIn(tween(500, delayMillis = 400))
                ) {
                    CustomAnimatedTextField(
                        value = email,
                        onValueChange = { email = it },
                        label = "Email Address",
                        icon = Icons.Rounded.Email,
                        keyboardType = KeyboardType.Email
                    )
                }
                
                Spacer(modifier = Modifier.height(20.dp))

                AnimatedVisibility(
                    visible = isScreenVisible,
                    enter = slideInHorizontally(initialOffsetX = { 50 }, animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy, stiffness = Spring.StiffnessLow)) + fadeIn(tween(500, delayMillis = 500))
                ) {
                    CustomAnimatedTextField(
                        value = password,
                        onValueChange = { password = it },
                        label = "Password",
                        icon = Icons.Rounded.Lock,
                        isPassword = true,
                        passwordVisible = passwordVisible,
                        onPasswordVisibilityChange = { passwordVisible = !passwordVisible }
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))
                
                // Forgot Password
                AnimatedVisibility(
                    visible = isScreenVisible,
                    enter = fadeIn(tween(500, delayMillis = 600))
                ) {
                    Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.CenterEnd) {
                        TextButton(onClick = { /* Handle Forgot Password */ }) {
                            Text(
                                text = "Forgot Password?", 
                                color = Color(0xFF4C76EB),
                                fontWeight = FontWeight.SemiBold
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))

                // Animated Login Button
                AnimatedVisibility(
                    visible = isScreenVisible,
                    enter = scaleIn(animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy, stiffness = Spring.StiffnessLow)) + fadeIn(tween(500, delayMillis = 700))
                ) {
                    AnimatedLoginButton(
                        isLoading = isLoading,
                        onClick = {
                            isLoading = true
                            // Simulate network req
                        }
                    )
                }

                Spacer(modifier = Modifier.height(24.dp))

                AnimatedVisibility(
                    visible = isScreenVisible,
                    enter = slideInVertically(initialOffsetY = { 20 }, animationSpec = tween(500, delayMillis = 800)) + fadeIn(tween(500, delayMillis = 800))
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Don't have an account?",
                            color = Color(0xFF64748B)
                        )
                        TextButton(onClick = { /* Handle Sign Up */ }) {
                            Text(
                                text = "Sign Up",
                                color = Color(0xFF4C76EB),
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
        }
    }
    
    // reset loading (simulation)
    LaunchedEffect(isLoading) {
        if(isLoading) {
            delay(2000)
            isLoading = false
        }
    }
}

@OptIn(ExperimentalAnimationApi::class)
@Composable
fun CustomAnimatedTextField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    keyboardType: KeyboardType = KeyboardType.Text,
    isPassword: Boolean = false,
    passwordVisible: Boolean = false,
    onPasswordVisibilityChange: () -> Unit = {}
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isFocused by interactionSource.collectIsFocusedAsState()

    // Smoothly animate the icon color, scale, and border color based on focus state
    val iconColor by animateColorAsState(
        targetValue = if (isFocused) Color(0xFF4C76EB) else Color(0xFF94A3B8), // Primary vs Slate 400
        animationSpec = tween(300),
        label = "iconColor"
    )
    
    val borderColor by animateColorAsState(
        targetValue = if (isFocused) Color(0xFF4C76EB) else Color(0xFFE2E8F0), // Primary vs Slate 200
        animationSpec = tween(300),
        label = "borderColor"
    )

    val iconScale by animateFloatAsState(
        targetValue = if (isFocused) 1.25f else 1f,
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioHighBouncy, // More playful bounce
            stiffness = Spring.StiffnessMedium
        ),
        label = "iconScale"
    )
    
    val iconRotation by animateFloatAsState(
        targetValue = if (isFocused && !isPassword) 15f else 0f, // Mail tilts slightly
        animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy),
        label = "iconRotation"
    )

    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        interactionSource = interactionSource,
        placeholder = { Text(label, color = Color(0xFF94A3B8)) },
        leadingIcon = {
            Box(
                modifier = Modifier
                    .padding(start = 12.dp, end = 4.dp)
                    .size(40.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(if (isFocused) Color(0xFF4C76EB).copy(alpha = 0.1f) else Color.Transparent),
                contentAlignment = Alignment.Center
            ) {
                // Here we inject the unlocking animation! 
                // If it's a password field and focused, change icon to LockOpen with a rotate/scale animation.
                if (isPassword) {
                    AnimatedContent(
                        targetState = isFocused || value.isNotEmpty(),
                        transitionSpec = {
                            (scaleIn() + fadeIn() + slideInVertically { it / 2 }).togetherWith(
                                scaleOut() + fadeOut() + slideOutVertically { -it / 2 }
                            )
                        },
                        label = "lockAnimation"
                    ) { unlocked ->
                        Icon(
                            imageVector = if (unlocked) Icons.Rounded.Lock else Icons.Rounded.Lock,
                            contentDescription = "Lock Animated",
                            tint = iconColor,
                            modifier = Modifier.scale(iconScale)
                        )
                    }
                } else {
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = iconColor,
                        modifier = Modifier
                            .scale(iconScale)
                            .graphicsLayer { rotationZ = iconRotation }
                    )
                }
            }
        },
        trailingIcon = if (isPassword) {
            {
                TextButton(onClick = onPasswordVisibilityChange) {
                    AnimatedContent(
                        targetState = passwordVisible,
                        transitionSpec = {
                            fadeIn(tween(200)) togetherWith fadeOut(tween(200))
                        },
                        label = "showHide"
                    ) { isVisible ->
                        Text(
                            text = if (isVisible) "Hide" else "Show",
                            color = Color(0xFF4C76EB),
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        } else null,
        visualTransformation = if (isPassword && !passwordVisible) PasswordVisualTransformation() else VisualTransformation.None,
        keyboardOptions = KeyboardOptions(keyboardType = keyboardType),
        shape = RoundedCornerShape(20.dp),
        modifier = Modifier.fillMaxWidth().graphicsLayer {
            // Slight jump of the entire text field when focused
            translationY = if (isFocused) -4f else 0f
        },
        singleLine = true,
        colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = Color(0xFF1E293B),
            unfocusedTextColor = Color(0xFF1E293B),
            focusedBorderColor = borderColor,
            unfocusedBorderColor = borderColor,
            cursorColor = Color(0xFF4C76EB),
            focusedContainerColor = Color(0xFFF8FAFC),
            unfocusedContainerColor = Color(0xFFF8FAFC)
        )
    )
}

@Composable
fun AnimatedLoginButton(
    isLoading: Boolean,
    onClick: () -> Unit
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    
    val scale by animateFloatAsState(
        targetValue = if (isPressed) 0.95f else 1f,
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioMediumBouncy,
            stiffness = Spring.StiffnessLow
        ),
        label = "buttonScale"
    )

    Button(
        onClick = onClick,
        interactionSource = interactionSource,
        modifier = Modifier
            .fillMaxWidth()
            .height(60.dp)
            .scale(scale)
            .shadow(
                elevation = if (isPressed) 2.dp else 12.dp,
                shape = RoundedCornerShape(20.dp),
                spotColor = Color(0xFF4C76EB).copy(alpha = 0.4f)
            ),
        shape = RoundedCornerShape(20.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = Color.Transparent
        ),
        contentPadding = PaddingValues(0.dp) // Important for gradient background
    ) {
        // Gradient pulsating effect
        val infiniteTransition = rememberInfiniteTransition(label = "btnGrad")
        val gradientShift by infiniteTransition.animateFloat(
            initialValue = 0f,
            targetValue = 1000f,
            animationSpec = infiniteRepeatable(
                animation = tween(3000, easing = LinearEasing),
                repeatMode = RepeatMode.Reverse
            ), label = "gradShift"
        )
        
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    Brush.linearGradient(
                        colors = listOf(Color(0xFF4C76EB), Color(0xFF6B8DF2), Color(0xFF4C76EB)),
                        start = Offset(gradientShift, 0f),
                        end = Offset(gradientShift + 500f, 1000f)
                    )
                ),
            contentAlignment = Alignment.Center
        ) {
            AnimatedContent(
                targetState = isLoading,
                transitionSpec = {
                    (fadeIn(tween(300)) + scaleIn()).togetherWith(fadeOut(tween(300)) + scaleOut())
                },
                label = "loadingAnim"
            ) { isLoad ->
                if (isLoad) {
                    CircularProgressIndicator(
                        color = Color.White,
                        modifier = Modifier.size(28.dp),
                        strokeWidth = 3.dp
                    )
                } else {
                    Text(
                        text = "Sign In",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        letterSpacing = 0.5.sp
                    )
                }
            }
        }
    }
}

@Composable
fun FloatingOrbs(isVisible: Boolean) {
    val infiniteTransition = rememberInfiniteTransition(label = "orbs")
    
    val orb1Y by infiniteTransition.animateFloat(
        initialValue = -50f,
        targetValue = 50f,
        animationSpec = infiniteRepeatable(
            animation = tween(4000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ), label = "orb1Y"
    )

    val orb2Y by infiniteTransition.animateFloat(
        initialValue = 50f,
        targetValue = -50f,
        animationSpec = infiniteRepeatable(
            animation = tween(5000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ), label = "orb2Y"
    )
    
    val orbScale by animateFloatAsState(
        targetValue = if (isVisible) 1f else 0f,
        animationSpec = tween(durationMillis = 1500, easing = FastOutSlowInEasing),
        label = "orbScale"
    )

    Box(modifier = Modifier.fillMaxSize().graphicsLayer {
        scaleX = orbScale
        scaleY = orbScale
        transformOrigin = TransformOrigin(0.5f, 0.5f)
    }) {
        // Top Left Pink Orb
        Box(
            modifier = Modifier
                .offset(x = (-40).dp, y = (50 + orb1Y).dp)
                .size(250.dp)
                .clip(CircleShape)
                .background(
                    Brush.radialGradient(
                        colors = listOf(Color(0xFFFF7EBD).copy(alpha = 0.12f), Color.Transparent)
                    )
                )
        )
        
        // Bottom Right Blue Orb
        Box(
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .offset(x = 60.dp, y = (-80 + orb2Y).dp)
                .size(300.dp)
                .clip(CircleShape)
                .background(
                    Brush.radialGradient(
                        colors = listOf(Color(0xFF4C76EB).copy(alpha = 0.15f), Color.Transparent)
                    )
                )
        )
        
        // Top Right Yellow Orb
        Box(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .offset(x = 80.dp, y = (-20 + orb1Y * 0.5f).dp)
                .size(200.dp)
                .clip(CircleShape)
                .background(
                    Brush.radialGradient(
                        colors = listOf(Color(0xFFFFC043).copy(alpha = 0.1f), Color.Transparent)
                    )
                )
        )
    }
}

@Preview(showBackground = true)
@Composable
fun LoginScreenPreview() {
    StreamTheme {
        LoginScreen()
    }
}
