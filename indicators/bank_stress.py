import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def get_bank_stress():
    end = datetime.today()
    start = end - timedelta(days=60)

    try:
        kre = yf.download("KRE", start=start, end=end, progress=False)
        spy = yf.download("SPY", start=start, end=end, progress=False)

        if kre.empty or spy.empty:
            return {"indicator": "Bank Stress", "signal": "Neutral", "explanation": "No data", "value": 0}

        # 1-month relative performance (approx 21 trading days)
        idx = -21 if len(kre) >= 21 else 0

        # Ensure we get scalar values for division
        latest_kre = kre['Close'].iloc[-1]
        prior_kre = kre['Close'].iloc[idx]
        latest_spy = spy['Close'].iloc[-1]
        prior_spy = spy['Close'].iloc[idx]

        if isinstance(latest_kre, pd.Series): latest_kre = latest_kre.iloc[0]
        if isinstance(prior_kre, pd.Series): prior_kre = prior_kre.iloc[0]
        if isinstance(latest_spy, pd.Series): latest_spy = latest_spy.iloc[0]
        if isinstance(prior_spy, pd.Series): prior_spy = prior_spy.iloc[0]

        kre_return = (latest_kre / prior_kre) - 1
        spy_return = (latest_spy / prior_spy) - 1

        rel_perf = (kre_return - spy_return) * 100

        if rel_perf > 0:
            signal = "Bullish"
            explanation = f"Banks outperforming S&P 500 by {rel_perf:.1f}%"
        elif rel_perf < -5:
            signal = "Bearish"
            explanation = f"Banks underperforming S&P 500 by {abs(rel_perf):.1f}%"
        else:
            signal = "Neutral"
            explanation = f"Banks performing in-line with S&P 500 ({rel_perf:+.1f}%)"

        return {
            "indicator": "Bank Stress",
            "value": round(rel_perf, 2),
            "signal": signal,
            "explanation": explanation,
            "last_updated": kre.index[-1].strftime("%Y-%m-%d"),
            "source": "Yahoo Finance (KRE vs SPY)"
        }
    except Exception as e:
        return {"indicator": "Bank Stress", "signal": "Neutral", "explanation": f"Error: {e}", "value": 0}

if __name__ == "__main__":
    import json
    print(json.dumps(get_bank_stress(), indent=2))
