# Macro Dashboard

An automated macro-economic regime tracking dashboard.

## Dashboard Access
- **Web Dashboard**: [docs/index.html](docs/index.html) (Viewable via GitHub Pages if enabled)
- **Latest Report**: [reports/latest.md](reports/latest.md)

## How to Run

### 1. Automated (GitHub Action)
The dashboard is scheduled to update automatically every weekday at **11:00 UTC**.
To trigger it manually:
1. Go to the **Actions** tab in your GitHub repository.
2. Select the **"Update Macro Dashboard"** workflow on the left.
3. Click the **"Run workflow"** dropdown button on the right and click the green button.

### 2. Local Execution
If you want to run the dashboard locally:
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the orchestration script:
   ```bash
   python dashboard/build_dashboard.py
   ```
The output will be generated in `docs/`, `reports/`, and `charts/`.

## Directory Structure

```
.
├── data/
│   ├── raw/                 # Pulled data (CSV)
│   ├── processed/           # Cleaned indicators
│   └── history/             # Regime logs
├── indicators/
│   ├── yield_10y.py         # 10Y Yield
│   ├── term_premium.py      # 10Y Term Premium
│   ├── yield_curve.py       # 2s10s Curve
│   ├── fed_balance_sheet.py # Liquidity Trend
│   ├── bank_reserves.py     # Reserve Trend
│   ├── treasury_auctions.py # Auction Quality
│   ├── credit_spread.py     # HY OAS
│   ├── bank_stress.py       # Regional Bank Performance
│   ├── mortgage_30y.py      # Housing Rates
│   ├── equity_breadth.py    # S&P 500 Participation
│   └── gold.py              # Gold vs Real Rates
├── dashboard/
│   ├── build_dashboard.py   # Orchestrates everything
│   ├── signals.py           # Signal mapping
│   └── regime.py            # Regime classification logic
├── charts/
│   └── *.png                # Visualizations
├── docs/
│   └── index.html           # Static HTML dashboard
├── reports/
│   └── latest.md            # Auto-updated summary
├── .github/workflows/
│   └── update.yml           # GitHub Action configuration
├── requirements.txt
└── README.md
```

## Indicators and Thresholds

1. **10Y Treasury Yield**: 3-month change (±25 bps)
2. **10Y Term Premium**: Level (<0%, 0-0.5%, >0.5%)
3. **2s10s Yield Curve**: Steepening source (Bull vs Bear steepener)
4. **Fed Balance Sheet**: 4-week trend
5. **Bank Reserves**: 4-week trend (±$50B)
6. **Treasury Auctions**: Tail and Bid-to-Cover
7. **High Yield Credit Spread**: Level and 1-month change
8. **Bank Stress**: KRE vs SPY 1-month relative performance
9. **30Y Mortgage Rate**: 3-month change (±30 bps)
10. **Equity Breadth**: % of S&P 500 stocks above 200DMA
11. **Gold vs Real Rates**: Gold price vs 10Y Real Yield (Bullish if Gold ↑ and Real Yield ↓)

## Regimes

- 🟢 **EASING / RISK-ON**: ≥5 bullish signals
- 🟡 **TRANSITION**: No dominant cluster
- 🔴 **TIGHT / FRAGILE**: ≥5 bearish signals
- ⚠️ **PRE-STRESS**:
    - ≥3 bearish signals including credit or banks
    - OR **Gold is Bullish while Credit is Neutral-to-Bearish** (Credibility Warning)
