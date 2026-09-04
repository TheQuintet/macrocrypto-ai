# Capstone Checkpoint — Dr. Robert Steele — 4 Sep 2026

| | |
|---|---|
| **Date** | Thu 4 Sep 2026 |
| **Type** | Capstone checkpoint with faculty advisor |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu, Richard Owusu, Mael Taye Deneke, Dr. Robert Steele |
| **Facilitator** | Sid Ahmed Mahieddine (presentation lead) |
| **Advisor** | Dr. Robert Steele |

---

## Summary

The team evaluated its Bitcoin price-forecasting MVP and capstone strategy.

- Prophet is a reasonable baseline, not a confirmed final model.
- Daily retraining and hourly inference are currently planned.
- Model alternatives and feature sets require empirical evaluation.
- Backtesting will compare accuracy using MAE, RMSE, MAPE, and MSE.
- The project is valuable but highly competitive.
- The service should be described as ML-based, not AI-based.
- The team will continue toward a strong capstone implementation.

---

## Action Items

Track progress by checking items off in GitHub or locally as they are completed.

| Done | Owner | Action |
|:----:|-------|--------|
| [ ] | Richard | Research current Bitcoin forecasting literature and identify relevant ML model alternatives to Prophet. |
| [ ] | Richard | Compare fresh-from-scratch training with continued training using the project’s historical data if a thorough evaluation is desired. |
| [ ] | Richard | Review published research to validate and refine the selected Bitcoin price-prediction features. |
| [ ] | Sid Ahmed | Present the team’s implementation progress in a subsequent meeting. |
| [ ] | Team | Compare the model’s performance with relevant alternatives and explain how the selected approach ranks. |
| [ ] | Team | Document how the model was evaluated, why the chosen methods were used, and why the resulting system is considered good. |
| [ ] | Team | Conduct additional research on existing market players and competing solutions. |
| [ ] | Team | Develop the project to a strong capstone standard. |
| [ ] | Richard | Improve the model’s predictive performance as much as possible. |
| [ ] | Team | Describe the ML-based implementation as an ML service rather than an AI service. |
| [ ] | Team | Continue developing the Bitcoin price-prediction project. |

---

## Key Discussion Points

### Project Presentation and Forecasting Architecture

Sid Ahmed introduced the team and presented an event-driven Bitcoin forecasting service that receives feature data through RabbitMQ. The proposed system uses ten inputs and provides recurring forecasts, prompting Robert Steele to ask whether the underlying implementation is an ML model or a broader AI service.

### Clarifying ML Versus AI

Robert questioned the use of “AI service” for a numerical price-prediction system and explained that structured time-series data is generally addressed with machine-learning models. The team clarified that the architecture exists, but the prediction model has not yet been implemented and that the terminology had caused confusion.

### Prophet Model, Data Pipeline, and MVP Scope

Sid confirmed that the team had made an initial design decision and intended to train Meta’s Prophet model on project-specific data covering ten selected features. The proposed pipeline uses 90 to 180 days of historical data, daily retraining at 06:00 UTC, and hourly inference, while the team identified the project as an MVP.

### Model Currency and Research Direction

Robert emphasized that Prophet is an ML model rather than an AI model and noted that its original release was around 2017. He considered it appropriate for the structured forecasting problem but advised the team to consider whether newer capabilities and current Bitcoin forecasting research should influence the final model choice.

### Comparing Training Strategies

Sid presented an option to train a fresh Prophet model from scratch whenever new data arrives instead of retraining the existing model. Robert explained that the better approach cannot be known in advance and recommended evaluating both strategies empirically on the team’s data if a thorough comparison is desired.

### Feature Selection for Bitcoin Forecasting

Sid asked whether the ten selected features were sufficient. Robert explained that Bitcoin prices can be influenced by a broad and potentially unpredictable set of macroeconomic, market, geopolitical, and news factors, and recommended reviewing published research to identify a defensible set of predominant features.

### Prediction Accuracy and Evaluation

The discussion distinguished between the inherent uncertainty of future price prediction and the need to measure model accuracy rigorously. Robert recommended training and evaluating multiple model variations, selecting the approach with the lowest appropriate error, and documenting the evaluation process.

### Current Scope and Planned Model Features

Sid described how the team incorporated feedback into its planned implementation. The current version includes prediction availability, confidence intervals, feature importance, walk-forward backtesting, performance metrics, model monitoring, and daily retraining, while further features were deferred to a later version to preserve the graduation timeline.

### Competitive Landscape and Capstone Expectations

Robert explained that Bitcoin prediction is valuable but difficult because many users and major financial organizations compete in the space. He encouraged the team to understand the scale of the problem while clarifying that the capstone only needs to deliver a good, well-evaluated system rather than a state-of-the-art commercial product.

### Market Positioning and Comparative Evaluation

Sid proposed targeting customers who cannot afford expensive services such as Bloomberg by offering a lower-cost product with transparent accuracy metrics. Robert agreed that this could be viable but stressed the importance of quantifying performance against real-world alternatives and communicating honestly how the model ranks.

### Business Model Considerations and Cryptocurrency Alternatives

The team discussed continuing collaboration after graduation and the challenges of competing in the global market. Robert questioned whether organizations with highly effective prediction models would sell them or use them internally for trading, while Sid suggested that other cryptocurrencies could provide alternative opportunities because their characteristics differ.

### Research, Positioning, and Closing Feedback

Richard and Robert emphasized researching existing market players, evaluating available options, and determining how the team’s system compares internationally. Robert reiterated the capstone standards, and the discussion ended with Kingson requesting Robert’s broader assessment of the team’s attempt to build a solution.

### Value and Difficulty of Bitcoin Price Prediction

Robert Steele characterized accurate Bitcoin price prediction as an extremely valuable objective, while emphasizing that market prediction is difficult because prices can be influenced by an almost unlimited range of external factors. He also noted that Bitcoin’s large global user base makes the market active but highly competitive.

### Competitive and Established Research Area

Robert explained that Bitcoin price prediction is not a new problem and has been studied for approximately 15–20 years. He contrasted the crowded market-prediction field with newer AI-enabled problem areas that may provide fresher research opportunities.

### Team Rationale and Project Evaluation

Kingson explained that the team wanted to merge its accumulated learning with a crypto specialization. Robert reiterated that the project was valid and potentially high-value, but urged the team to assess its competitiveness and established nature objectively before moving forward.

### Project Guidance and Closing

The participants indicated that there were no further questions and moved to close the meeting. Robert encouraged the team to develop the work to a strong capstone standard, maximize model quality, use accurate ML terminology, continue the project, and submit the completed work.

---

## Notes

- Source: checkpoint meeting summary, action items, and discussion notes (4 Sep 2026).
- Prior session: [2 Sep 2026 Review, Refinement & Planning](./2026-09-02-review-and-planning.md).
- Capstone criteria: [Quantic grading](../quantic/grading.md) · [Deliverables](../quantic/deliverables.md).
