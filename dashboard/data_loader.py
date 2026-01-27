import pandas as pd
import requests
import yfinance as yf
from io import StringIO
import datetime
import numpy as np

FRED_BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

def fetch_fred_series(series_id):
    url = f"{FRED_BASE_URL}{series_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text), index_col=0, parse_dates=True)
            df = df.replace('.', np.nan)
            df = df.apply(pd.to_numeric, errors='coerce')
            df = df.dropna()
            return df
        else:
            print(f"Failed to fetch FRED series {series_id}: HTTP {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching FRED series {series_id}: {e}")
        return pd.DataFrame()

def fetch_treasury_auctions(security_term="10-Year", security_type="Note"):
    url = f"https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query?filter=security_type:eq:{security_type},security_term:eq:{security_term}&limit=5&sort=-auction_date"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json().get('data', [])
            return pd.DataFrame(data)
        else:
            print(f"Failed to fetch auctions for {security_term}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching auctions: {e}")
        return pd.DataFrame()

def get_sp500_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        # Set User-Agent to avoid 403
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(response.text))
        df = tables[0]
        return df['Symbol'].tolist()
    except Exception as e:
        print(f"Error scraping S&P 500 tickers: {e}")
        # Fallback to a few major tickers
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "MA", "PG"]

def get_equity_breadth(tickers=None):
    if tickers is None:
        tickers = get_sp500_tickers()

    tickers = [t.replace('.', '-') for t in tickers]
    test_tickers = tickers[:50] # Reduced for speed

    try:
        # yfinance download uses 'progress' not 'silent'
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
            except:
                continue

        if total_valid == 0:
            return 0
        return (above_200dma_count / total_valid) * 100
    except Exception as e:
        print(f"Error calculating equity breadth: {e}")
        return 0

def get_bank_stress():
    try:
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=60)

        kre = yf.download("KRE", start=start, end=end, progress=False)
        spy = yf.download("SPY", start=start, end=end, progress=False)

        if kre.empty or spy.empty:
            return 0

        # Ensure we have enough data
        idx = -21 if len(kre) >= 21 else 0
        kre_return = (kre['Close'].iloc[-1] / kre['Close'].iloc[idx]) - 1
        spy_return = (spy['Close'].iloc[-1] / spy['Close'].iloc[idx]) - 1

        if isinstance(kre_return, pd.Series): kre_return = kre_return.iloc[0]
        if isinstance(spy_return, pd.Series): spy_return = spy_return.iloc[0]

        return (kre_return - spy_return) * 100
    except Exception as e:
        print(f"Error calculating bank stress: {e}")
        return 0
