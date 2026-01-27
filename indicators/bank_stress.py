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
        kre_return = (kre['Close'].iloc[-1] / kre['Close'].iloc[idx]) - 1
        spy_return = (spy['Close'].iloc[-1] / spy['Close'].iloc[idx]) - 1

        # Handle cases where result is a Series
        if isinstance(kre_return, pd.Series): kre_return = kre_return.iloc[0]
        if isinstance(spy_return, pd.Series): spy_return = spy_return.iloc[0]

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
            "last_updated": end.strftime("%Y-%m-%d"),
            "source": "Yahoo Finance (KRE vs SPY)"
        }
    except Exception as e:
        return {"indicator": "Bank Stress", "signal": "Neutral", "explanation": f"Error: {e}", "value": 0}

if __name__ == "__main__":
    print(get_bank_stress())
