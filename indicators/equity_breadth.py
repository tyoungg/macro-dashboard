import pandas as pd
import yfinance as yf
import requests
from io import StringIO
from datetime import datetime

def get_sp500_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(response.text))
        df = tables[0]
        return df['Symbol'].tolist()
    except:
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "MA", "PG"]

def get_equity_breadth():
    tickers = get_sp500_tickers()
    tickers = [t.replace('.', '-') for t in tickers]
    # Limit for speed in demonstration, normally use all
    test_tickers = tickers[:50]

    try:
        data = yf.download(test_tickers, period="1y", interval="1d", group_by='ticker', progress=False)
        above_200dma_count = 0
        total_valid = 0

        for ticker in test_tickers:
            try:
                df = data[ticker] if len(test_tickers) > 1 else data
                if len(df) > 200:
                    current_price = df['Close'].iloc[-1]
                    dma200 = df['Close'].rolling(window=200).mean().iloc[-1]

                    if not pd.isna(current_price) and not pd.isna(dma200):
                        total_valid += 1
                        if current_price > dma200:
                            above_200dma_count += 1
            except: continue

        if total_valid == 0:
            return {"indicator": "Equity Breadth", "value": 0, "signal": "Neutral", "explanation": "No valid data", "last_updated": datetime.today().strftime("%Y-%m-%d")}

        pct = (above_200dma_count / total_valid) * 100

        if pct > 65:
            signal = "Bullish"
            explanation = f"Broad participation: {pct:.1f}% of stocks above 200DMA"
        elif pct < 40:
            signal = "Bearish"
            explanation = f"Poor participation: only {pct:.1f}% of stocks above 200DMA"
        else:
            signal = "Neutral"
            explanation = f"Average participation: {pct:.1f}% of stocks above 200DMA"

        return {
            "indicator": "Equity Breadth",
            "value": round(pct, 1),
            "signal": signal,
            "explanation": explanation,
            "last_updated": data.index[-1].strftime("%Y-%m-%d"),
            "source": "S&P 500 (Scraped via Wikipedia/Yahoo)"
        }
    except Exception as e:
        return {"indicator": "Equity Breadth", "value": 0, "signal": "Neutral", "explanation": f"Error: {e}", "last_updated": datetime.today().strftime("%Y-%m-%d")}

if __name__ == "__main__":
    import json
    print(json.dumps(get_equity_breadth(), indent=2))
