<p align="center">
  <h1 align="center">🛡️ STREAM</h1>
  <p align="center"><strong>Suspicious Transaction — Risk Engine for Anomaly Monitoring</strong></p>
  <p align="center">
    An AI-powered Android application for anti-corruption intelligence, bid rigging detection, and vendor risk analysis.
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Android-green?logo=android" alt="Platform" />
  <img src="https://img.shields.io/badge/Language-Kotlin-blue?logo=kotlin" alt="Language" />
  <img src="https://img.shields.io/badge/UI-Jetpack%20Compose-4285F4?logo=jetpackcompose" alt="UI" />
  <img src="https://img.shields.io/badge/Material-3-purple" alt="Material 3" />
  <img src="https://img.shields.io/badge/Min%20SDK-24-orange" alt="Min SDK" />
  <img src="https://img.shields.io/badge/Target%20SDK-35-brightgreen" alt="Target SDK" />
</p>

---

## 📖 Overview

**STREAM** is a comprehensive anti-corruption intelligence platform built as a native Android application. It leverages machine learning models and real-time data analysis to detect suspicious patterns in government procurement, electoral bond transactions, and vendor networks. Designed for investigators, auditors, and compliance teams, STREAM surfaces actionable insights through a sleek, modern mobile interface.

---

## ✨ Features

### 📊 Dashboard
- Real-time Key Performance Indicators (KPIs) — active flags, at-risk value, vendors tracked, model precision
- Detection summary for bid rigging, shell networks, and political connections
- Electoral bond intelligence with party-wise breakdown

### 🔍 Bid Analysis
- Browse and filter flagged tender bids with risk-tier classification
- Detailed bid view with vendor, buyer, and anomaly breakdown
- Sorting and pagination support

### 🏢 Vendor Profiling
- Risk score breakdown with sub-scores (financial, network, behavioral)
- Vendor connection mapping and recent tender history
- Search vendors by name or ID

### 🚨 Alerts
- Real-time alert feed with risk-tier filtering (Critical, High, Medium, Low)
- Sortable and paginated alert list

### 🤖 Predictive Analysis
- On-demand risk prediction via ML model endpoint
- Submit tender/vendor parameters and receive instant risk assessment

### 💬 AI Chat
- Conversational AI interface for natural-language querying of the intelligence database

### 📋 Activity Logs
- Chronological audit trail of system events
- Filter by event type

### 🔐 Authentication
- Login screen with session management

---

## 🏗️ Architecture

```
com.example.stream
├── MainActivity.kt                  # Entry point, auth gating
├── data/
│   ├── api/
│   │   ├── StreamApi.kt             # Retrofit API interface (REST endpoints)
│   │   └── RetrofitClient.kt        # OkHttp + Gson client configuration
│   ├── model/
│   │   └── Models.kt                # Data classes for all API responses
│   └── repository/
│       └── StreamRepository.kt      # Data repository layer
└── ui/
    ├── components/
    │   └── StreamDesign.kt          # Reusable composables (GlassCard, KpiCard, RiskBadge, etc.)
    ├── theme/
    │   ├── Color.kt                 # Custom color palette
    │   ├── Theme.kt                 # MaterialTheme configuration
    │   └── Type.kt                  # Typography definitions
    ├── navigation/
    │   └── MainScreen.kt            # Bottom nav + navigation graph
    ├── dashboard/                   # Dashboard screen + ViewModel
    ├── bid/                         # Bid analysis screen, detail view + ViewModel
    ├── vendor/                      # Vendor profiling screen + ViewModel
    ├── alerts/                      # Alerts screen + ViewModel
    ├── predict/                     # Prediction screen + ViewModel
    ├── chat/                        # AI chat screen + ViewModel
    ├── activity/                    # Activity logs screen + ViewModel
    └── login/                       # Login screen
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Kotlin |
| **UI Framework** | Jetpack Compose with Material 3 |
| **Navigation** | Navigation Compose |
| **Networking** | Retrofit 2 + OkHttp (with logging interceptor) |
| **Serialization** | Gson (with custom deserializers) |
| **State Management** | ViewModel + StateFlow |
| **Design System** | Custom glassmorphism components with animated gradients |
| **Min SDK** | 24 (Android 7.0) |
| **Target SDK** | 35 (Android 15) |

---

## 🚀 Getting Started

### Prerequisites

- **Android Studio** Ladybug (2024.2+) or later
- **JDK 8+**
- **Android SDK** with API level 35 installed
- A running STREAM backend API server

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Jaswanth1406/STREAM---Suspicious-Transaction---Risk-Engine-for-Anomaly-Monitoring.git
   cd STREAM---Suspicious-Transaction---Risk-Engine-for-Anomaly-Monitoring
   ```

2. **Open in Android Studio**
   - File → Open → select the project root directory

3. **Configure the API endpoint**
   - Open `app/src/main/java/com/example/stream/data/api/RetrofitClient.kt`
   - Update the `BASE_URL` to point to your STREAM backend server

4. **Build & Run**
   ```bash
   ./gradlew assembleDebug
   ```
   Or press ▶️ **Run** in Android Studio with an emulator or connected device.

---

## 📡 API Endpoints

The app communicates with the following REST API endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard/kpis` | Dashboard KPI metrics |
| `GET` | `/alerts` | Paginated alerts with filters |
| `GET` | `/vendor/{vendor_id}` | Vendor risk profile |
| `GET` | `/vendor/search/{query}` | Search vendors |
| `GET` | `/bid-analysis` | Paginated bid analysis with filters |
| `GET` | `/bid-analysis/summary` | Bid analysis summary statistics |
| `GET` | `/activity/recent` | Recent system activity events |
| `GET` | `/stats/risk-distribution` | Risk tier distribution |
| `GET` | `/stats/top-risk-buyers` | Top risk buyers ranking |
| `GET` | `/stats/bond-summary` | Electoral bond summary |
| `POST` | `/predict` | ML-based risk prediction |

---

## 🎨 Design System

STREAM uses a custom **glassmorphism-inspired** design system built on Material 3:

- **`GlassCard`** — Frosted glass card with blur and border effects
- **`KpiCard`** — Metric display card for dashboards
- **`RiskBadge`** — Color-coded risk tier indicator (Critical / High / Medium / Low)
- **`AnimatedGradientBackground`** — Smooth animated gradient canvas
- **`GlassFilterChip`** / **`SortChip`** — Styled filter and sort controls
- **`PaginationBar`** — Paginated list navigation
- **`LoadingScreen`** / **`ErrorScreen`** — Consistent loading and error states

---

## 📂 Project Structure

```
Stream/
├── app/
│   └── src/main/
│       ├── java/com/example/stream/   # Kotlin source code
│       ├── res/                        # Android resources (layouts, drawables, strings)
│       └── AndroidManifest.xml         # App manifest
├── gradle/                             # Gradle wrapper
├── build.gradle.kts                    # Root build config
├── settings.gradle.kts                 # Project settings
└── README.md
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Built with ❤️ for transparency and accountability
</p>
