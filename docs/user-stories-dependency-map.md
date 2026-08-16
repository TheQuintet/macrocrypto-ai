## 📂 DEPENDENCY MAP — DIRECTORY TREE FORMAT (with Full Story Titles)

```
macrocrypto-ai/
│
├── 📁 FOUNDATION LAYER (No Dependencies)
│   │
│   ├── 📄 S1 — [Platform User] View macroeconomic indicators alongside BTC data
│   │   └── (None — Foundation)
│   │
│   ├── 📄 S2 — [Platform User] Access BTC predictions and macro data via API
│   │   └── (None — Foundation)
│   │
│   └── 📄 S3 — [Platform User] View economic calendar of upcoming events
│       └── (None — Foundation)
│
├── 📁 DATA LAYER
│   │
│   ├── 📄 T4 — [BTC Trader] View real-time BTC price updates
│   │   └── (None — External API)
│   │
│   ├── 📄 T1 — [BTC Trader] View 24-hour BTC price predictions
│   │   └── 📌 T4: [BTC Trader] View real-time BTC price updates
│   │
│   └── 📄 T2 — [BTC Trader] View 7-day BTC price predictions
│       ├── 📌 T1: [BTC Trader] View 24-hour BTC price predictions
│       └── 📌 T3: [BTC Trader] View confidence intervals alongside each prediction
│
├── 📁 FEATURE LAYER
│   │
│   ├── 📄 T3 — [BTC Trader] View confidence intervals alongside each prediction
│   │   ├── 📌 T1: [BTC Trader] View 24-hour BTC price predictions
│   │   └── 📌 T2: [BTC Trader] View 7-day BTC price predictions
│   │
│   ├── 📄 T5 — [BTC Trader] View historical prediction accuracy
│   │   ├── 📌 T1: [BTC Trader] View 24-hour BTC price predictions
│   │   ├── 📌 T2: [BTC Trader] View 7-day BTC price predictions
│   │   └── 📌 T4: [BTC Trader] View real-time BTC price updates
│   │
│   ├── 📄 T6 — [BTC Trader] View clear trade recommendations based on predictions
│   │   ├── 📌 T1: [BTC Trader] View 24-hour BTC price predictions
│   │   ├── 📌 T2: [BTC Trader] View 7-day BTC price predictions
│   │   ├── 📌 T3: [BTC Trader] View confidence intervals alongside each prediction
│   │   └── 📌 S1: [Platform User] View macroeconomic indicators alongside BTC data
│   │
│   ├── 📄 T7 — [BTC Trader] Receive alerts when BTC reaches key price levels
│   │   └── 📌 T4: [BTC Trader] View real-time BTC price updates
│   │
│   ├── 📄 T8 — [BTC Trader] Receive alerts for significant prediction changes
│   │   ├── 📌 T1: [BTC Trader] View 24-hour BTC price predictions
│   │   └── 📌 T2: [BTC Trader] View 7-day BTC price predictions
│   │
│   └── 📄 T9 — [BTC Trader] Receive alerts before major economic events
│       ├── 📌 S1: [Platform User] View macroeconomic indicators alongside BTC data
│       └── 📌 S3: [Platform User] View economic calendar of upcoming events
│
└── 📁 ANALYTICS LAYER
    │
    ├── 📄 A1 — [Investment Analyst] View BTC-macro correlation analysis
    │   ├── 📌 S1: [Platform User] View macroeconomic indicators alongside BTC data
    │   ├── 📌 FRED API (external)
    │   └── 📌 CoinGecko API (external)
    │
    ├── 📄 A2 — [Investment Analyst] Export BTC and macro correlation data
    │   ├── 📌 S1: [Platform User] View macroeconomic indicators alongside BTC data
    │   ├── 📌 A1: [Investment Analyst] View BTC-macro correlation analysis
    │   ├── 📌 A3: [Investment Analyst] View historical BTC patterns across macro regimes
    │   └── 📌 S2: [Platform User] Access BTC predictions and macro data via API
    │
    ├── 📄 A3 — [Investment Analyst] View historical BTC patterns across macro regimes
    │   ├── 📌 S1: [Platform User] View macroeconomic indicators alongside BTC data
    │   └── 📌 A1: [Investment Analyst] View BTC-macro correlation analysis
    │
    ├── 📄 A4 — [Investment Analyst] View methodology behind predictions and correlations
    │   └── (None — Documentation-only)
    │
    └── 📄 A5 — [Investment Analyst] View historical event impact analysis on BTC
        ├── 📌 S3: [Platform User] View economic calendar of upcoming events
        └── 📌 T4: [BTC Trader] View real-time BTC price updates
```



Sprint 1:  S1, S3, T4

Sprint 2:  T1

Sprint 3:  T2, T3

Sprint 4:  T5, S2

Sprint 5:  T6, T7

Sprint 6:  T8, T9

Sprint 7:  A1, A3

Sprint 8:  A2, A4, A5