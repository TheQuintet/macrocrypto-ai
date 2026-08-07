# MacroCrypto AI - Feature Engineering Guide

## AI Service Feature Specifications

### Version 1.0 | Technical Documentation

---

## 1. Overview

This document defines the comprehensive feature set for the MacroCrypto AI forecasting model. The AI service will utilize **5 macroeconomic features** and **5 Bitcoin market features** to generate 24-hour price predictions with confidence intervals.

The feature engineering process transforms raw data into predictive signals that capture both the broader economic environment and crypto-specific market dynamics. This approach ensures the model delivers on the platform's core value proposition: **AI-powered Bitcoin intelligence driven by macroeconomic data**.

---

## 2. Feature Categories

### 2.1 Macroeconomic Features (5)
These features capture the broader economic environment that drives Bitcoin's price movements. They provide the "why" behind market movements and differentiate this platform from competitors.

### 2.2 Bitcoin Market Features (5)
These features capture on-chain and market dynamics specific to Bitcoin, providing real-time sentiment and momentum signals that complement the macro perspective.

---

## 3. Complete Feature Specifications

### 3.1 Macroeconomic Features

#### Feature 1: CPI Inflation Rate (Year-over-Year)

| Attribute | Specification |
|-----------|---------------|
| **Data Source** | FRED (CPIAUCSL) or BLS API |
| **Update Frequency** | Monthly (released around 10th-15th) |
| **Update Latency** | ~2-3 weeks after month-end |
| **Data Type** | Continuous (percentage) |
| **Range** | Typically -2% to 10%+ |
| **Primary Use** | Inflation hedge narrative signal |

**Why This Feature Matters:**

Bitcoin is often positioned as an inflation hedge. Historical data shows that during periods of rising inflation, Bitcoin tends to attract capital from investors seeking to preserve purchasing power. The year-over-year rate captures the trend direction, while month-over-month changes indicate recent momentum. This feature is central to the platform's value proposition of connecting macroeconomic trends to crypto markets.

**Interpretation Guidelines:**

| CPI Condition | Market Implication |
|---------------|-------------------|
| Rising CPI (> 3%) | Bullish for BTC (hedge narrative strengthens) |
| Falling CPI (< 2%) | Bearish pressure (inflation fears subside) |
| CPI > 5% | Strong bull signal (hyperinflation hedge) |
| CPI < 1% | Deflationary concerns (risk-off sentiment) |

**Feature Engineering Approach:**

The monthly CPI value must be forward-filled for daily use. For example, if CPI data for March is released on March 15th, the AI service uses that same value for all days from March 15th to April 14th. This creates a step function that represents the most current known economic condition.

---

#### Feature 2: Federal Funds Rate / Interest Rates

| Attribute | Specification |
|-----------|---------------|
| **Data Source** | FRED (FEDFUNDS) |
| **Update Frequency** | Every 6-8 weeks (FOMC meetings) |
| **Update Latency** | Same day (rate announcements) |
| **Data Type** | Continuous (percentage) |
| **Range** | 0% to 20%+ (historically) |
| **Primary Use** | Risk-on/risk-off sentiment signal |

**Why This Feature Matters:**

Interest rates are the primary tool of central banks and heavily influence investor behavior. When rates are low, capital flows toward risk assets like Bitcoin (the "risk-on" environment). When rates rise, capital shifts to interest-bearing assets like bonds (the "risk-off" environment). The Federal Funds Rate is the benchmark for all other interest rates and directly impacts Bitcoin's attractiveness as an investment.

**Interpretation Guidelines:**

| Interest Rate Condition | Market Implication |
|-------------------------|-------------------|
| Rate cuts | Bullish for BTC (more liquidity, easier money) |
| Rate hikes | Bearish pressure (capital flows to yield) |
| Rate pause | Neutral to slightly bullish (uncertainty reduces) |
| Rates near 0% | Strong bull environment (search for yield) |

**Feature Engineering Approach:**

The rate value remains constant between Federal Open Market Committee (FOMC) meetings. However, the model should also consider expected rate changes by incorporating market-implied probabilities from Fed futures (if data is accessible). The rate of change (momentum) is often as important as the absolute level.

---

#### Feature 3: M2 Money Supply (Year-over-Year Growth)

| Attribute | Specification |
|-----------|---------------|
| **Data Source** | FRED (WM2NS) |
| **Update Frequency** | Monthly |
| **Update Latency** | ~2 weeks after month-end |
| **Data Type** | Continuous (percentage growth) |
| **Range** | -5% to 30%+ |
| **Primary Use** | Liquidity/inflation driver signal |

**Why This Feature Matters:**

M2 money supply measures the total amount of money in circulation, including cash, checking deposits, and easily convertible near-money. During quantitative easing (QE) periods, M2 surges, creating liquidity that often flows into scarce assets like Bitcoin. M2 contraction can signal tightening conditions that reduce speculative capital.

**Interpretation Guidelines:**

| M2 Growth Condition | Market Implication |
|---------------------|-------------------|
| Accelerating growth | Bullish (more liquidity entering markets) |
| Decelerating growth | Bearish pressure (liquidity drying up) |
| Negative growth | Strong bear signal (credit contraction) |
| Growth > 10% | Historical bull market conditions |

**Feature Engineering Approach:**

The year-over-year percentage change is a smoother signal than the absolute value. This removes long-term trends and isolates the relative expansion or contraction of money supply. A 3-month moving average can further smooth monthly volatility.

---

#### Feature 4: US Dollar Index (DXY)

| Attribute | Specification |
|-----------|---------------|
| **Data Source** | FRED (DTWEXBGS) or investing.com |
| **Update Frequency** | Daily (real-time during trading hours) |
| **Update Latency** | Real-time |
| **Data Type** | Continuous (index value) |
| **Range** | 70 to 120+ (historically) |
| **Primary Use** | USD strength/weakness signal |

**Why This Feature Matters:**

Bitcoin is primarily priced in US dollars, creating an inverse relationship between DXY and BTC. When the dollar strengthens (DXY rises), dollar-denominated assets like Bitcoin become more expensive for international buyers. Conversely, when the dollar weakens (DXY falls), BTC often rises. This feature captures global currency flows and international investor behavior.

**Interpretation Guidelines:**

| DXY Condition | Market Implication |
|---------------|-------------------|
| DXY falling | Bullish for BTC (weaker USD) |
| DXY rising | Bearish pressure (stronger USD) |
| DXY consolidating | Neutral to slightly bullish |
| DXY > 105 | Historically bearish for risk assets |

**Feature Engineering Approach:**

The daily closing DXY value is used. However, the 30-day rolling correlation between DXY and BTC can be a powerful leading indicator. When the correlation strengthens, it signals that dollar movements are becoming a dominant factor in Bitcoin price action.

---

#### Feature 5: 10-Year Treasury Yield

| Attribute | Specification |
|-----------|---------------|
| **Data Source** | FRED (DGS10) |
| **Update Frequency** | Daily |
| **Update Latency** | Real-time during trading hours |
| **Data Type** | Continuous (percentage) |
| **Range** | 0.5% to 5%+ (historically) |
| **Primary Use** | Risk-free rate and inflation expectations signal |

**Why This Feature Matters:**

The 10-year Treasury yield represents the "risk-free rate" benchmark for the global financial system. As yields rise, bonds become more attractive relative to non-yield-bearing assets like Bitcoin. Additionally, the 10-year yield is a key component of inflation expectations (breakeven rates), providing insight into market inflation psychology.

**Interpretation Guidelines:**

| Treasury Yield Condition | Market Implication |
|--------------------------|-------------------|
| Rapidly rising yields | Bearish (capital flows to bonds) |
| Flat/dropping yields | Bullish (search for yield/risk assets) |
| Yield curve inversion | Recession signal (complex impact on BTC) |
| Yields > 4% | Historically challenging for risk assets |

**Feature Engineering Approach:**

The daily closing yield is used. The 2-year to 10-year spread (yield curve slope) should be monitored as a secondary signal. An inverted yield curve (2y > 10y) has historically preceded recessions and can trigger risk-off sentiment.

---

### 3.2 Bitcoin Market Features

#### Feature 6: Bitcoin Price (With Lags)

| Attribute | Specification |
|-----------|---------------|
| **Data Source** | CoinGecko API / Binance |
| **Update Frequency** | Real-time |
| **Update Latency** | Real-time |
| **Data Type** | Continuous (USD price) |
| **Range** | $1 to $100,000+ |
| **Primary Use** | Target variable and momentum signal |

**Why This Feature Matters:**

The current and historical prices form the foundation of any forecasting model. The price itself is the target variable (what we're predicting). However, lagged prices (previous days, weeks, months) capture momentum and trend that the model uses to identify patterns.

**Feature Engineering Approach:**

The AI service uses the daily closing price as the target variable (`y` in Prophet). Additionally, the following lag features are created:
- 1-day lag (momentum)
- 7-day lag (weekly trend)
- 30-day lag (monthly trend)
- Rolling returns (1d, 7d, 30d percentage changes)

These lags help the model understand price momentum and mean-reversion tendencies. The log returns (percentage changes) provide a more stable signal than absolute prices.

---

#### Feature 7: 24-Hour Trading Volume

| Attribute | Specification |
|-----------|---------------|
| **Data Source** | CoinGecko API / Binance |
| **Update Frequency** | Real-time |
| **Update Latency** | Real-time |
| **Data Type** | Continuous (USD volume) |
| **Range** | $100M to $50B+ |
| **Primary Use** | Trend confirmation and conviction signal |

**Why This Feature Matters:**

Volume is the fuel behind price movements. High volume on an uptrend confirms strong conviction and suggests the trend will continue. High volume on a downtrend signals panic selling. Low volume on an uptrend indicates weak conviction and potential reversal. Volume spikes often precede major price moves.

**Interpretation Guidelines:**

| Volume Pattern | Market Implication |
|----------------|-------------------|
| High volume + rising price | Bullish continuation (strong conviction) |
| Low volume + rising price | Bearish divergence (weak conviction) |
| High volume + falling price | Bearish continuation (panic selling) |
| Volume spike + flat price | Accumulation or distribution (watch for breakout) |
| Volume drying up | Consolidation (potential breakout ahead) |

**Feature Engineering Approach:**

Absolute volume (USD amount) and volume-to-market-cap ratio provide complementary signals. Rolling averages (7-day, 30-day) smooth the daily noise and reveal underlying trends. The volume relative to its 30-day average indicates whether current activity is abnormal.

---

#### Feature 8: Volatility (7-Day Rolling Standard Deviation)

| Attribute | Specification |
|-----------|---------------|
| **Data Source** | Calculated from BTC price history |
| **Update Frequency** | Daily (after close) |
| **Update Latency** | Real-time |
| **Data Type** | Continuous (percentage) |
| **Range** | 1% to 20%+ |
| **Primary Use** | Uncertainty and risk appetite signal |

**Why This Feature Matters:**

Volatility measures market uncertainty. High volatility often precedes major moves in either direction. Low volatility can signal consolidation periods where the market is "coiling" for a breakout. Bitcoin is historically a volatile asset, making this feature particularly important.

**Interpretation Guidelines:**

| Volatility Level | Market Implication |
|------------------|-------------------|
| High volatility (> 10%) | Increased risk, potential opportunity |
| Medium volatility (5-10%) | Normal trading environment |
| Low volatility (< 5%) | Range-bound, expect breakout soon |
| Volatility spike | Significant market event (news-driven) |

**Feature Engineering Approach:**

Calculate the 7-day rolling standard deviation of daily returns (percentage changes). Multiply by the square root of 252 to annualize for comparability. The VIX-like measure provides insight into market sentiment and option-implied volatility (if data is accessible).

---

#### Feature 9: Market Dominance (BTC Dominance %)

| Attribute | Specification |
|-----------|---------------|
| **Data Source** | CoinGecko API |
| **Update Frequency** | Real-time |
| **Update Latency** | Real-time |
| **Data Type** | Continuous (percentage) |
| **Range** | 30% to 70%+ (historically) |
| **Primary Use** | Capital flow and sentiment signal |

**Why This Feature Matters:**

Bitcoin dominance measures Bitcoin's share of total cryptocurrency market capitalization. Rising dominance indicates capital rotating into Bitcoin (a "flight to safety" in crypto terms). Falling dominance suggests an altcoin season where capital flows into other cryptocurrencies.

**Interpretation Guidelines:**

| Dominance Pattern | Market Implication |
|-------------------|-------------------|
| Dominance increasing | Bullish for BTC (relative strength) |
| Dominance decreasing | Mixed (altcoin rally or BTC weakening) |
| Dominance > 60% | Strong Bitcoin focus (traditionally bullish) |
| Dominance < 40% | Altcoin season (BTC may be lagging) |

**Feature Engineering Approach:**

Use the daily closing dominance percentage. Track the 30-day trend (simple moving average) to identify whether dominance is consistently rising or falling. The rate of change can be a leading indicator for BTC strength.

---

#### Feature 10: On-Chain Active Addresses (7-Day Moving Average)

| Attribute | Specification |
|-----------|---------------|
| **Data Source** | Glassnode (free tier) or CoinGecko API |
| **Update Frequency** | Daily |
| **Update Latency** | ~24 hours |
| **Data Type** | Continuous (count) |
| **Range** | 500K to 1.5M+ |
| **Primary Use** | Network growth and adoption signal |

**Why This Feature Matters:**

Active addresses measure the number of unique addresses participating in Bitcoin transactions on a given day. Rising active addresses indicate growing network utility, adoption, and user engagement. This can be a leading indicator for price appreciation.

**Interpretation Guidelines:**

| Active Addresses Condition | Market Implication |
|---------------------------|-------------------|
| Growing addresses | Bullish (increasing adoption and usage) |
| Declining addresses | Bearish (network activity cooling off) |
| Addresses at all-time high | Strong bull market signal |
| Addresses stagnating | Consolidation (user base plateau) |

**Feature Engineering Approach:**

Use the 7-day moving average to smooth daily noise. Track the month-over-month growth rate to identify adoption trends. The absolute number of addresses also provides context - higher values generally indicate a healthier network.

---

## 4. Feature Engineering Framework

### 4.1 Data Preprocessing (Critical!)

Proper preprocessing ensures the AI model receives clean, normalized signals that capture meaningful patterns rather than noise.

**4.1.1 Forward-Filling for Economic Data**

Economic data is released on a monthly or quarterly schedule, creating gaps between releases. For daily forecasting, we must maintain a continuous data stream.

The forward-filling method carries the most recent available value forward until a new release arrives. For example, if CPI data for March is released on March 15th, the AI service uses the March value for all days from March 15th to April 14th (the day before the April release). This approach is preferred because it reflects the information available to market participants at any given time.

Alternative methods like interpolation (smoothing between values) would introduce data not known to traders at the time and could create unrealistic patterns in the model.

**4.1.2 Handling Stationarity**

Stationarity means that the statistical properties of a time series (mean, variance) do not change over time. Most forecasting models, including Prophet, work better with stationary data because it makes patterns more predictable and reduces the risk of spurious correlations.

For macroeconomic features, stationarity is achieved by using year-over-year percentage changes rather than absolute values. For example, instead of using the absolute CPI value, we use the annual percentage change. This removes the long-term upward trend in prices and isolates the cyclical movement that influences Bitcoin.

For Bitcoin price, the log returns (percentage changes) are naturally more stationary than absolute prices. However, Prophet is designed to work directly with the price series as long as trend and seasonality components are properly modeled.

**4.1.3 Normalization and Scaling**

Features must be on similar scales for the model to treat them equally. Without normalization, a feature with a large range (like price in dollars) could dominate the model over a feature with a small range (like a percentage).

The standardization method subtracts the mean and divides by the standard deviation for each feature. This transforms all features to have a mean of zero and a standard deviation of one. Prophet handles this internally for regressors, but manually normalizing can improve model stability.

The range of the training data must be tracked so that new data can be normalized using the same parameters. This ensures consistency between training and inference phases.

**4.1.4 Managing Missing Data**

Missing data can occur due to API failures, delayed releases, or holidays. The strategy for handling missing values depends on the context.

For economic data, forward-filling is appropriate because values are constant between releases. For market data, forward-filling with the previous known value is acceptable for short gaps of a few hours. For longer gaps (days), interpolation may be necessary, or the model can simply treat the missing period as an observation gap.

The AI service should log all instances of missing data and include this metadata in the model inputs. This transparency helps debug issues and identify data quality problems.

**4.1.5 Outlier Detection and Treatment**

Market data frequently contains outliers from erroneous data points, flash crashes, or unusual events. These outliers can distort the model and lead to poor predictions.

The interquartile range (IQR) method identifies outliers as data points that fall below the 25th percentile minus 1.5 times the IQR or above the 75th percentile plus 1.5 times the IQR. These points should be reviewed and potentially winsorized (capped to a threshold) or excluded from training.

For economic data, outliers are less common but should still be flagged for review. Significant revisions to economic data (e.g., CPI revisions) can create artificial jumps that require manual handling.

### 4.2 Feature Engineering Techniques

Feature engineering transforms raw data into predictive signals that capture the relationships and patterns the model needs to learn.

**4.2.1 Lagged Features**

Lagged features include past values of the target variable (price) and other predictors. They help the model understand momentum and mean-reversion tendencies.

For Bitcoin price, lagged values at 1, 7, 30, and 90 days provide information about short-term momentum, weekly trends, and monthly cycles. The model can learn patterns like "if price rose 10% in the past week, it tends to pull back slightly in the next week."

For volatility, lagged volatility values can indicate whether current high volatility is persistent or just a spike.

**4.2.2 Rolling Averages and Smoothing**

Rolling averages smooth daily noise and reveal underlying trends. They are particularly useful for volatile assets like Bitcoin.

Moving averages at 7, 30, and 90 days provide signals at different time horizons. The 7-day average captures short-term sentiment, the 30-day average shows medium-term trends, and the 90-day average reveals long-term direction.

Moving average crossovers (e.g., 7-day crossing above 30-day) can be powerful predictive signals. These events often correspond to changes in trend and are widely followed by traders.

**4.2.3 Rate of Change (ROC)**

The rate of change measures the speed at which a value is changing. This momentum signal often precedes price movements.

For economic indicators, the rate of change is already captured in the year-over-year calculation. For market data, the ROC can highlight accelerating trends that may not be visible in absolute values.

A ROC near zero indicates a trend that is stalling and may reverse. A high ROC indicates strong momentum that may continue.

**4.2.4 Differencing**

Differencing subtracts the previous value from the current value, effectively measuring the day-to-day change. This technique helps achieve stationarity and focuses the model on changes rather than absolute levels.

For Bitcoin price, daily returns (percentage change) are a form of differencing. For volume, the percentage change in volume can indicate changing conviction.

**4.2.5 Ratios and Normalization**

Ratios normalize features and highlight relative strength or weakness. This provides signals that are more comparable across different market conditions.

For example, the volume-to-market-cap ratio normalizes trading activity by the size of the market. A high ratio indicates significant trading activity relative to the market size, suggesting increased interest.

The dominance percentage is itself a ratio (Bitcoin market cap divided by total crypto market cap). This provides a normalized measure of Bitcoin's relative strength.

**4.2.6 Exponential Weighting**

Exponential weighting gives more weight to recent observations while still incorporating historical data. This is particularly useful for features where recent behavior is more predictive than older patterns.

The exponential moving average (EMA) with a short decay period (e.g., 0.2) responds quickly to new information. The EMA with a longer decay period (e.g., 0.05) provides a smoother trend.

Price tends to follow EMA crossovers, and many traders use these as buy or sell signals.

---

## 5. Feature Importance and Interpretation

### 5.1 Understanding Feature Contributions

After the model is trained, it's possible to analyze which features are most influential in driving predictions. This analysis is crucial for three reasons:

**Building Trust with Users:** When you can explain that "the model is bullish because interest rates are falling and inflation is rising," users understand the reasoning behind the prediction. This transparency differentiates the platform from "black box" AI systems.

**Validating the Model:** If a feature that should be important (like inflation) is not contributing, it may indicate a data quality issue or that the feature needs to be re-engineered. This validation process catches problems early.

**Continuous Improvement:** By tracking which features are most predictive over time, the team can focus on improving the most impactful data sources and consider adding new features in the same category.

### 5.2 Extracting Feature Importance

Prophet provides feature importance through the model coefficients for each regressor. A positive coefficient indicates that increases in that feature lead to higher predicted prices. A negative coefficient indicates that increases in that feature lead to lower predicted prices.

The magnitude of the coefficient indicates the feature's strength. A feature with a coefficient of 0.8 has a stronger impact than a feature with a coefficient of 0.2.

However, coefficients must be interpreted carefully. A feature with a high absolute coefficient but low variability (i.e., it barely changes) may have little practical impact despite its mathematical influence.

The relative importance should also be considered in the context of the feature's business significance. A less important feature that provides strong user narrative (like CPI) may be worth keeping even if its coefficient is modest.

### 5.3 Communication to Users

The AI service should include feature importance in the `forecast_event` payload. This allows the API and dashboard to display:

**Bullish Factors:** "The model is optimistic due to falling interest rates (-2.1 impact) and rising inflation (+1.3 impact)."

**Bearish Factors:** "The model is cautious due to the strengthening dollar (-1.5 impact) and declining active addresses (-0.8 impact)."

This narrative explanation transforms a simple price prediction into an educational tool that helps users understand market dynamics. It also reinforces the platform's value proposition of connecting macroeconomic trends to Bitcoin.

### 5.4 Monitoring Feature Performance Over Time

Feature importance should be tracked over time to identify shifts in market dynamics. For example, during the 2020-2021 bull run, M2 money supply was a highly important feature. During the 2022 bear market, interest rates and DXY became dominant.

This monitoring helps in several ways:

- **Early Warning:** A sudden shift in feature importance may indicate a regime change that requires model retraining.
- **Feature Review:** Features that are consistently unimportant can be removed to simplify the model.
- **Insight Generation:** Understanding which features drive predictions at different times reveals market narratives that can be shared with users.

### 5.5 Feature Drift Detection

Feature drift occurs when the statistical properties of a feature change over time. For example, if Bitcoin volatility increases significantly, the feature's distribution shifts.

Detecting drift is important because the model was trained on a specific distribution. If the distribution changes too much, predictions become unreliable.

The two-sample Kolmogorov-Smirnov test can detect distribution changes between the training data and recent data. If drift is detected, the model should be retrained more frequently or the feature may need to be re-engineered.

Simple thresholds can also be used. For example, if the price exceeds the maximum seen during training, the model is extrapolating and predictions become less reliable.

---

## 6. Model Training and Retraining Strategy

### 6.1 Initial Training Phase

The initial model training uses the complete historical dataset available at launch. The dataset should include at least three years of data to capture multiple market cycles, including both bull and bear markets.

The training data is split into training (80%), validation (10%), and testing (10%) sets. The validation set is used to tune model hyperparameters, and the testing set provides an unbiased evaluation of final model performance.

The model is trained with all 10 features. The training process identifies the optimal coefficients for each feature and the underlying trend and seasonality components.

### 6.2 Periodic Retraining

Markets evolve, and models trained on old data become less effective. Periodic retraining with fresh data ensures the model adapts to changing conditions.

A weekly retraining schedule provides a good balance between adaptation and stability. The retraining process fetches the complete updated dataset and retrains the model from scratch.

The new model version is validated against the most recent testing data. If performance meets or exceeds the current model, the new version is deployed. If performance declines, the current model remains.

### 6.3 Conditional Retraining Triggers

Certain events may warrant immediate retraining regardless of schedule:

**Economic Regime Change:** A significant shift in monetary policy (e.g., rate cuts after a long period of hikes) may render the old model obsolete. The model should be retrained with data that includes the new regime.

**Market Structure Change:** The launch of Bitcoin ETFs, regulatory changes, or major adoption events can fundamentally alter market dynamics. Immediate retraining helps the model adapt.

**Performance Degradation:** If the model's error rate exceeds a threshold (e.g., 10% MAE) for multiple consecutive days, retraining is triggered automatically.

### 6.4 Model Versioning and Rollback

Each trained model is saved with a version identifier (e.g., v1.0.3) and timestamp. This enables easy rollback to a previous version if performance declines.

The AI service loads the latest model version at startup. During retraining, a new version is saved without disrupting the currently running model. The switch to the new version occurs during the next inference cycle.

All predictions include the model version, allowing performance tracking by version. This enables analysis of whether the new model improves predictions.

---

## 7. Data Pipeline Requirements

### 7.1 Data Collection

The Data Service must collect and store all 10 features on a daily basis. Economic data is collected when new releases are available. Market data is collected daily at a consistent time (e.g., 23:59 UTC) to ensure consistency.

All collected data must include a timestamp, source information, and any quality flags (e.g., "preliminary" for economic data revisions).

### 7.2 Data Storage

PostgreSQL tables store historical data for all features. Table structures include:
- `macro_data`: CPI, interest rates, M2, DXY, treasury yields
- `btc_data`: Price, volume, volatility, dominance, active addresses
- `model_features`: Combined dataset ready for training

Time-series optimization (e.g., TimescaleDB extension) improves query performance for the large historical datasets required for retraining.

### 7.3 Data Quality Monitoring

Data quality monitoring ensures the model receives accurate and complete data:

**Completeness:** Are all expected data points present? Missing data should trigger alerts.

**Accuracy:** Are values within expected ranges? Outliers should be flagged.

**Timeliness:** Is data arriving on schedule? Delays should trigger alerts.

**Consistency:** Are values consistent with previous releases? Large revisions should be reviewed.

### 7.4 Data Access for AI Service

The AI Service accesses the feature dataset through a dedicated data access layer. This layer handles:
- Fetching historical data for training
- Fetching the latest data for inference
- Forward-filling economic data
- Normalization and scaling

This abstraction ensures that the AI Service only works with clean, prepared data.

---

## 8. Performance Metrics and Monitoring

### 8.1 Prediction Accuracy Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **MAE** | Mean Absolute Error (average prediction error) | < 5% |
| **RMSE** | Root Mean Squared Error (penalizes large errors) | < 7% |
| **MAPE** | Mean Absolute Percentage Error (relative accuracy) | < 5% |
| **Directional Accuracy** | Percentage of correct direction predictions | > 55% |
| **Confidence Interval Coverage** | Percentage of actual prices within predicted bounds | 95% (expected) |

These metrics are calculated on the testing dataset and monitored daily. Degradation triggers alerts and potentially retraining.

### 8.2 Business Impact Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Forecast Value** | Can users profit from predictions? | Positive net gain |
| **User Engagement** | How often are forecasts viewed? | Daily active users |
| **Trust Score** | Do users trust predictions? | > 80% positive feedback |

These metrics are harder to measure but ultimately determine the platform's success.

### 8.3 Monitoring Dashboard

A dashboard provides visibility into model performance:
- Current model version
- Recent prediction accuracy
- Feature importance over time
- Data quality metrics
- Retraining history

This dashboard is accessible to the team and provides early warning of issues.

---

## 9. Feature Selection and Iteration

### 9.1 Starting with All 10 Features

The initial model is trained with all 10 features. This establishes a baseline performance and identifies which features are most predictive.

### 9.2 Feature Importance Analysis

After initial training, feature importance analysis identifies which features contribute most to predictions. The bottom features are candidates for removal if their contribution is minimal.

### 9.3 Iterative Feature Testing

Features are tested individually:
1. Remove one feature
2. Retrain and measure performance
3. If performance improves or is unchanged, the feature is removed
4. If performance degrades, the feature is kept

This systematic testing ensures the model only includes valuable features.

### 9.4 Adding New Features

When adding a new feature (planned for future phases), the same rigorous testing applies. The feature is added, and performance is measured. If the new feature improves predictions, it's added. If not, it's shelved for future reconsideration.

### 9.5 Avoiding Overfitting

Overfitting occurs when the model learns noise rather than signal. The following practices prevent overfitting:

- **Cross-validation:** Test the model on unseen data
- **Regularization:** Penalize large coefficients
- **Simple models:** Start simple and add complexity only when justified
- **Feature selection:** Remove features that don't add value

The 10-feature set with proper validation provides a good balance between predictive power and generalization.

---

## 10. Conclusion

The 10-feature set (5 macro, 5 BTC) provides a comprehensive foundation for the MacroCrypto AI forecasting model. This carefully curated selection captures both the broader economic environment and Bitcoin-specific market dynamics.

The feature engineering framework ensures that raw data is transformed into clean, normalized, and predictive signals that the model can learn from effectively. The systematic approach to training, retraining, and monitoring maintains model accuracy over time.

By delivering both predictions and feature importance explanations, the AI service fulfills the platform's core value proposition: **AI-powered Bitcoin intelligence driven by macroeconomic data.** Users understand not just what the model predicts, but why, building trust and enabling informed decision-making.

---

## Appendix A: Feature Reference Table

| # | Feature | Data Source | Frequency | Type | Primary Signal |
|---|---------|-------------|-----------|------|----------------|
| 1 | CPI Inflation (YoY) | FRED | Monthly | Macro | Inflation hedge |
| 2 | Federal Funds Rate | FRED | ~Monthly | Macro | Risk-on/off |
| 3 | M2 Money Supply (YoY Growth) | FRED | Monthly | Macro | Liquidity |
| 4 | US Dollar Index (DXY) | FRED | Daily | Macro | USD strength |
| 5 | 10-Year Treasury Yield | FRED | Daily | Macro | Risk-free rate |
| 6 | BTC Price (with lags) | CoinGecko | Real-time | BTC | Momentum |
| 7 | 24-Hour Trading Volume | CoinGecko | Real-time | BTC | Conviction |
| 8 | Volatility (7-day rolling) | Calculated | Daily | BTC | Uncertainty |
| 9 | BTC Dominance % | CoinGecko | Real-time | BTC | Capital flows |
| 10 | Active Addresses (7-day MA) | Glassnode | Daily | BTC | Adoption |

---

## Appendix B: Data Handling Decision Matrix

| Data Issue | Handling Strategy | Responsible Service |
|------------|-------------------|---------------------|
| Delayed economic release | Forward-fill existing value | Data Service |
| Missing daily market data | Forward-fill previous value | Data Service |
| API failure | Retry with exponential backoff | Data Service |
| Outlier price | Winsorize (cap to threshold) | Data Service |
| Outlier economic value | Flag for manual review | Data Service (alert) |
| Data revision (CPI) | Replace history | Data Service |
| Model performance degradation | Trigger retraining | AI Service |
| Feature drift | Retrain and monitor | AI Service |

---

**Document Version:** 1.0  
**Last Updated:** July 31, 2026  
**Reviewers:** AI Service Team, Data Engineering Team  
**Next Review:** After initial model training (estimated ~4 weeks)
