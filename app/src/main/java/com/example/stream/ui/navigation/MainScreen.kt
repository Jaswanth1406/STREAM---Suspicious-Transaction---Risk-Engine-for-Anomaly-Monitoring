package com.example.stream.ui.navigation

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.*
import androidx.navigation.navArgument
import com.example.stream.ui.alerts.AlertsScreen
import com.example.stream.ui.activity.ActivityScreen
import com.example.stream.ui.bid.BidAnalysisScreen
import com.example.stream.ui.bid.BidDetailScreen
import com.example.stream.ui.chat.ChatScreen
import com.example.stream.ui.dashboard.DashboardScreen
import com.example.stream.ui.predict.PredictScreen
import com.example.stream.ui.vendor.VendorScreen
import com.example.stream.ui.theme.*

sealed class Screen(val route: String, val title: String, val icon: ImageVector) {
    object Dashboard : Screen("dashboard", "Home", Icons.Default.Dashboard)
    object Alerts : Screen("alerts", "Alerts", Icons.Default.Warning)
    object BidAnalysis : Screen("bid_analysis", "Bids", Icons.Default.Assessment)
    object Chat : Screen("chat", "AI Chat", Icons.Default.Chat)
    object Activity : Screen("activity", "Feed", Icons.Default.Timeline)
    object Predict : Screen("predict", "Predict", Icons.Default.Psychology)
    object Vendor : Screen("vendor/{vendorId}", "Vendor", Icons.Default.Person)
    object BidDetail : Screen("bid_detail", "Bid Detail", Icons.Default.Assessment)
}

val bottomNavItems = listOf(Screen.Dashboard, Screen.Alerts, Screen.BidAnalysis, Screen.Chat, Screen.Activity)

@Composable
fun MainScreen() {
    val navController = rememberNavController()
    val currentRoute = navController.currentBackStackEntryAsState().value?.destination?.route
    val hideBottomBar = currentRoute?.startsWith("vendor") == true || currentRoute == "bid_detail"

    Scaffold(
        containerColor = Color.Transparent,
        bottomBar = { if (currentRoute != null && !hideBottomBar) { GlassBottomBar(navController, currentRoute) } }
    ) { innerPadding ->
        NavHost(navController = navController, startDestination = Screen.Dashboard.route, modifier = Modifier.padding(innerPadding)) {
            composable(Screen.Dashboard.route) { DashboardScreen() }
            composable(Screen.Alerts.route) { AlertsScreen(onVendorClick = { vendorId -> navController.navigate("vendor/$vendorId") }) }
            composable(Screen.BidAnalysis.route) { BidAnalysisScreen(onTenderClick = { navController.navigate("bid_detail") }) }
            composable(Screen.Chat.route) { ChatScreen() }
            composable(Screen.Activity.route) { ActivityScreen() }
            composable(Screen.Predict.route) { PredictScreen() }
            composable(Screen.Vendor.route, arguments = listOf(navArgument("vendorId") { type = NavType.StringType })) { backStackEntry ->
                val vendorId = backStackEntry.arguments?.getString("vendorId") ?: ""
                VendorScreen(vendorId = vendorId, onBack = { navController.popBackStack() })
            }
            composable(Screen.BidDetail.route) { BidDetailScreen(onBack = { navController.popBackStack() }) }
        }
    }
}

@Composable
fun GlassBottomBar(navController: NavHostController, currentRoute: String?) {
    NavigationBar(containerColor = Color.White.copy(alpha = 0.5f), tonalElevation = 0.dp, modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp).clip(RoundedCornerShape(20.dp)).border(1.dp, Color.White.copy(alpha = 0.6f), RoundedCornerShape(20.dp))) {
        bottomNavItems.forEach { screen ->
            val selected = currentRoute == screen.route
            NavigationBarItem(
                selected = selected,
                onClick = { if (currentRoute != screen.route) { navController.navigate(screen.route) { popUpTo(Screen.Dashboard.route) { saveState = true }; launchSingleTop = true; restoreState = true } } },
                icon = { Icon(screen.icon, contentDescription = screen.title, modifier = Modifier.size(22.dp)) },
                label = { Text(screen.title, fontSize = 10.sp, fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium) },
                colors = NavigationBarItemDefaults.colors(selectedIconColor = StreamPurple, selectedTextColor = StreamPurple, unselectedIconColor = StreamDark.copy(alpha = 0.5f), unselectedTextColor = StreamDark.copy(alpha = 0.5f), indicatorColor = StreamPurple.copy(alpha = 0.12f))
            )
        }
    }
}