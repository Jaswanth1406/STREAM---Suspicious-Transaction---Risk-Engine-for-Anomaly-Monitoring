package com.example.stream.ui.login

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.animation.graphics.res.animatedVectorResource
import androidx.compose.animation.graphics.res.rememberAnimatedVectorPainter
import androidx.compose.animation.graphics.ExperimentalAnimationGraphicsApi
import androidx.compose.animation.graphics.vector.AnimatedImageVector
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.KeyboardOptions
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
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.stream.R
import com.example.stream.ui.theme.StreamTheme
import kotlinx.coroutines.delay

@OptIn(ExperimentalAnimationGraphicsApi::class)
@Composable
fun LoginScreen(modifier: Modifier = Modifier) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(false) }

    // Screen Entrance Animation 
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
            .background(Color(0xFFFBF5F0)), // Mindfulness background
        contentAlignment = Alignment.Center
    ) {
        // Chakra style sweeping gradient background
        ChakraBackground(isVisible = isScreenVisible)

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp)
                .graphicsLayer {
                    alpha = animatedAlpha
                    translationY = animatedOffsetY
                },
            shape = RoundedCornerShape(24.dp),
            colors = CardDefaults.cardColors(
                containerColor = Color.White.copy(alpha = 0.4f) // Glassmorphism translucent base
            ),
            elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(
                        width = 1.dp,
                        color = Color.White.copy(alpha = 0.6f),
                        shape = RoundedCornerShape(24.dp)
                    )
            ) {
                Column(
                    modifier = Modifier
                        .padding(32.dp)
                        .fillMaxWidth(),
                    horizontalAlignment = Alignment.Start
                ) {
                    // Chakra style align start
                    AnimatedVisibility(
                        visible = isScreenVisible,
                        enter = slideInVertically(initialOffsetY = { 20 }, animationSpec = tween(600, delayMillis = 200)) + fadeIn(tween(600, delayMillis = 200))
                    ) {
                        Text(
                            text = "Welcome Back",
                            style = MaterialTheme.typography.displaySmall.copy(
                                fontWeight = FontWeight.ExtraBold,
                                color = Color(0xFF262335), // Dark high-contrast
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
                            text = "Enter your credentials to access the STREAM anti-corruption engine.",
                            style = MaterialTheme.typography.bodyMedium.copy(
                                color = Color(0xFF463699).copy(alpha = 0.8f) 
                            ),
                            modifier = Modifier.padding(bottom = 32.dp)
                        )
                    }

                // Staggered Entrance for Text Fields
                AnimatedVisibility(
                    visible = isScreenVisible,
                    enter = slideInVertically(initialOffsetY = { 20 }, animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy, stiffness = Spring.StiffnessLow)) + fadeIn(tween(500, delayMillis = 400))
                ) {
                    Column {
                        Text("Email", color = Color(0xFF262335), fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                        Spacer(modifier = Modifier.height(8.dp))
                        CustomAnimatedTextField(
                            value = email,
                            onValueChange = { email = it },
                            placeholder = "Your email address",
                            iconResId = R.drawable.avd_email_anim,
                            keyboardType = KeyboardType.Email
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(20.dp))

                AnimatedVisibility(
                    visible = isScreenVisible,
                    enter = slideInVertically(initialOffsetY = { 20 }, animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy, stiffness = Spring.StiffnessLow)) + fadeIn(tween(500, delayMillis = 500))
                ) {
                    Column {
                        Text("Password", color = Color(0xFF262335), fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                        Spacer(modifier = Modifier.height(8.dp))
                        CustomAnimatedTextField(
                            value = password,
                            onValueChange = { password = it },
                            placeholder = "Your password",
                            iconResId = R.drawable.avd_lock_anim,
                            isPassword = true,
                            passwordVisible = passwordVisible,
                            onPasswordVisibilityChange = { passwordVisible = !passwordVisible }
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))
                
                // Remember Me / Forgot Password row
                AnimatedVisibility(
                    visible = isScreenVisible,
                    enter = fadeIn(tween(500, delayMillis = 600))
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        var rememberMe by remember { mutableStateOf(false) }
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Switch(
                                checked = rememberMe,
                                onCheckedChange = { rememberMe = it },
                                colors = SwitchDefaults.colors(
                                    checkedThumbColor = Color.White,
                                    checkedTrackColor = Color(0xFF463699).copy(alpha = 0.8f),
                                    uncheckedThumbColor = Color(0xFF262335).copy(alpha = 0.7f), // Make thumb visible against light card
                                    uncheckedTrackColor = Color.White.copy(alpha = 0.5f), // Translucent matte track
                                    uncheckedBorderColor = Color(0xFFC7C2CE).copy(alpha = 0.8f) // Subtle grey border so it stands out
                                ),
                                modifier = Modifier.scale(0.8f)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Remember me", color = Color(0xFF262335), fontSize = 14.sp, fontWeight = FontWeight.Medium)
                        }
                        
                        TextButton(onClick = { /* Handle Forgot Password */ }) {
                            Text(
                                text = "Forgot?", 
                                color = Color(0xFF463699),
                                fontWeight = FontWeight.ExtraBold,
                                fontSize = 14.sp
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
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Don't have an account?",
                            color = Color(0xFF262335).copy(alpha = 0.7f),
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Medium
                        )
                        TextButton(onClick = { /* Handle Sign Up */ }) {
                            Text(
                                text = "Sign up",
                                color = Color(0xFF463699),
                                fontWeight = FontWeight.ExtraBold,
                                fontSize = 14.sp
                            )
                        }
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

@OptIn(ExperimentalAnimationGraphicsApi::class)
@Composable
fun CustomAnimatedTextField(
    value: String,
    onValueChange: (String) -> Unit,
    placeholder: String,
    iconResId: Int,
    keyboardType: KeyboardType = KeyboardType.Text,
    isPassword: Boolean = false,
    passwordVisible: Boolean = false,
    onPasswordVisibilityChange: () -> Unit = {}
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isFocused by interactionSource.collectIsFocusedAsState()

    // Smoothly animate the border color based on focus state for glassmorphism
    val borderColor by animateColorAsState(
        targetValue = if (isFocused) Color(0xFF463699) else Color.White.copy(alpha = 0.6f), 
        animationSpec = tween(300),
        label = "borderColor"
    )

    val image = AnimatedImageVector.animatedVectorResource(iconResId)
    val painter = rememberAnimatedVectorPainter(image, atEnd = isFocused)

    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        interactionSource = interactionSource,
        placeholder = { Text(placeholder, color = Color(0xFF262335).copy(alpha = 0.5f), fontSize = 14.sp) },
        leadingIcon = {
            Icon(
                painter = painter,
                contentDescription = null,
                tint = Color.Unspecified 
            )
        },
        trailingIcon = if (isPassword) {
            {
                TextButton(onClick = onPasswordVisibilityChange) {
                    Text(
                        text = if (passwordVisible) "Hide" else "Show",
                        color = Color(0xFF463699),
                        fontWeight = FontWeight.ExtraBold,
                        fontSize = 14.sp
                    )
                }
            }
        } else null,
        visualTransformation = if (isPassword && !passwordVisible) PasswordVisualTransformation() else VisualTransformation.None,
        keyboardOptions = KeyboardOptions(keyboardType = keyboardType),
        shape = RoundedCornerShape(16.dp),
        modifier = Modifier.fillMaxWidth(),
        singleLine = true,
        colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = Color(0xFF262335),
            unfocusedTextColor = Color(0xFF262335),
            focusedBorderColor = borderColor,
            unfocusedBorderColor = borderColor,
            cursorColor = Color(0xFF463699),
            focusedContainerColor = Color.White.copy(alpha = 0.5f), // Translucent inner glass
            unfocusedContainerColor = Color.White.copy(alpha = 0.3f)
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
            .height(56.dp)
            .scale(scale)
            .shadow(
                elevation = if (isPressed) 1.dp else 8.dp,
                shape = RoundedCornerShape(16.dp),
                spotColor = Color(0xFF463699).copy(alpha = 0.3f)
            )
            .border(
                width = 1.dp,
                color = Color.White.copy(alpha = 0.5f), // Inner glass border
                shape = RoundedCornerShape(16.dp)
            ),
        shape = RoundedCornerShape(16.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = Color(0xFF463699).copy(alpha = 0.7f) // Matte glassmorphism translucency
        ),
        contentPadding = PaddingValues(0.dp) 
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
                    modifier = Modifier.size(24.dp),
                    strokeWidth = 3.dp
                )
            } else {
                Text(
                    text = "SIGN IN",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White,
                    letterSpacing = 0.5.sp
                )
            }
        }
    }
}

@Composable
fun ChakraBackground(isVisible: Boolean) {
    val infiniteTransition = rememberInfiniteTransition(label = "bgBubbles")
    
    // Animate bubble positions and sizes to create a flowing, liquid effect
    val bubble1X by infiniteTransition.animateFloat(
        initialValue = -100f,
        targetValue = 200f,
        animationSpec = infiniteRepeatable(
            animation = tween(18000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ), label = "bubble1X"
    )
    val bubble1Y by infiniteTransition.animateFloat(
        initialValue = -50f,
        targetValue = 300f,
        animationSpec = infiniteRepeatable(
            animation = tween(15000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ), label = "bubble1Y"
    )

    val bubble2X by infiniteTransition.animateFloat(
        initialValue = 300f,
        targetValue = -50f,
        animationSpec = infiniteRepeatable(
            animation = tween(22000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ), label = "bubble2X"
    )
    val bubble2Y by infiniteTransition.animateFloat(
        initialValue = 500f,
        targetValue = 100f,
        animationSpec = infiniteRepeatable(
            animation = tween(19000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ), label = "bubble2Y"
    )
    
    val bubble3X by infiniteTransition.animateFloat(
        initialValue = 100f,
        targetValue = -100f,
        animationSpec = infiniteRepeatable(
            animation = tween(20000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ), label = "bubble3X"
    )
    val bubble3Y by infiniteTransition.animateFloat(
        initialValue = 100f,
        targetValue = 500f,
        animationSpec = infiniteRepeatable(
            animation = tween(17000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ), label = "bubble3Y"
    )

    val bgScale by animateFloatAsState(
        targetValue = if (isVisible) 1f else 0.8f,
        animationSpec = tween(durationMillis = 1500, easing = FastOutSlowInEasing),
        label = "bgScale"
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .clip(RectangleShape)
            .background(Color(0xFFFBF5F0)) // Base mindfulness off-white
            .graphicsLayer {
                scaleX = bgScale
                scaleY = bgScale
            }
    ) {
        // Bubble 1: Lavender (#8A83DA)
        Box(
            modifier = Modifier
                .offset(x = bubble1X.dp, y = bubble1Y.dp)
                .size(400.dp)
                .clip(CircleShape)
                .background(
                    Brush.radialGradient(
                        colors = listOf(Color(0xFF8A83DA).copy(alpha = 0.4f), Color.Transparent)
                    )
                )
        )
        
        // Bubble 2: Peach (#FBD5BD)
        Box(
            modifier = Modifier
                .offset(x = bubble2X.dp, y = bubble2Y.dp)
                .size(350.dp)
                .clip(CircleShape)
                .background(
                    Brush.radialGradient(
                        colors = listOf(Color(0xFFFBD5BD).copy(alpha = 0.5f), Color.Transparent)
                    )
                )
        )
        
        // Bubble 3: Primary Purple (#463699)
        Box(
            modifier = Modifier
                .offset(x = bubble3X.dp, y = bubble3Y.dp)
                .size(450.dp)
                .clip(CircleShape)
                .background(
                    Brush.radialGradient(
                        colors = listOf(Color(0xFF463699).copy(alpha = 0.25f), Color.Transparent)
                    )
                )
        )
    }
}
