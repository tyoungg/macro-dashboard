import pandas as pd
import yfinance as yf
import requests
from io import StringIO
from datetime import datetime, timedelta

# -----------------------------
# Configuration
# -----------------------------
REAL_YIELD_ID = "DFII10"  # 10Y Real Yield (TIPS)
GOLD_TICKER = "GC=F"      # Gold Futures
LOOKBACK_DAYS = 60       # Enough for 1 month change

def fetch_fred_data(series_id, days):
    end = datetime.today()
    start = end - timedelta(days=days)
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start.strftime('%Y-%m-%d')}&coed={end.strftime('%Y-%m-%d')}"
    response = requests.get(url)
    if response.status_code == 200:
        df = pd.read_csv(StringIO(response.text), index_col=0, parse_dates=True)
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
        return df
    return pd.DataFrame()

def get_gold_signal():
    """
    Metric: Gold price vs 10Y real yield (TIPS)
    Signal: Bullish if Gold up while real yields down, Bearish if Gold down while real yields up.
    """
    end = datetime.today()
    start = end - timedelta(days=LOOKBACK_DAYS)

    try:
        # Fetch Gold
        gold = yf.download(GOLD_TICKER, start=start, end=end, progress=False)
        # Fetch Real Yield
        real_yield = fetch_fred_data(REAL_YIELD_ID, LOOKBACK_DAYS)

        if gold.empty or real_yield.empty:
            return {
                "indicator": "Gold vs Real Rates",
                "value": 0,
                "signal": "Neutral",
                "explanation": "Data unavailable",
                "last_updated": end.strftime("%Y-%m-%d"),
                "source": "Yahoo/FRED"
            }

        # 1-month change
        latest_gold_series = gold['Close'].iloc[-1]
        prior_gold_series = gold['Close'].iloc[-21] if len(gold) >= 21 else gold['Close'].iloc[0]

        gold_latest = float(latest_gold_series.iloc[0]) if isinstance(latest_gold_series, pd.Series) else float(latest_gold_series)
        gold_prior = float(prior_gold_series.iloc[0]) if isinstance(prior_gold_series, pd.Series) else float(prior_gold_series)
        gold_change = (gold_latest / gold_prior) - 1

        # Real Yield change
        ry_latest = float(real_yield.iloc[-1].iloc[0])
        ry_prior = float(real_yield.iloc[-21].iloc[0]) if len(real_yield) >= 21 else float(real_yield.iloc[0].iloc[0])
        ry_change = ry_latest - ry_prior

        if gold_change > 0 and ry_change < 0:
            signal = "Bullish"
            explanation = f"Gold rising ({gold_change*100:+.1f}%) as real yields fall ({ry_change:+.2f}%)"
        elif gold_change < 0 and ry_change > 0:
            signal = "Bearish"
            explanation = f"Rising real rates ({ry_change:+.2f}%) pressuring gold ({gold_change*100:+.1f}%)"
        else:
            signal = "Neutral"
            explanation = f"Gold ({gold_change*100:+.1f}%) aligned with real rates ({ry_change:+.2f}%)"

        # Use the earliest of the two last dates to be safe about the signal validity
        last_date = min(gold.index[-1], real_yield.index[-1]).strftime("%Y-%m-%d")

        return {
            "indicator": "Gold vs Real Rates",
            "value": round(gold_latest, 2),
            "real_yield_val": round(ry_latest, 2),
            "signal": signal,
            "explanation": explanation,
            "last_updated": last_date,
            "source": "Yahoo (Gold) / FRED (TIPS)"
        }
    except Exception as e:
        return {
            "indicator": "Gold vs Real Rates",
            "value": 0,
            "signal": "Neutral",
            "explanation": f"Error: {e}",
            "last_updated": end.strftime("%Y-%m-%d"),
            "source": "Error"
        }

if __name__ == "__main__":
    import json
    print(json.dumps(get_gold_signal(), indent=2))
