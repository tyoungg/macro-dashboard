import pandas as pd
import requests
from datetime import datetime

def fetch_treasury_auctions(security_term="10-Year", security_type="Note"):
    # Filter for bid_to_cover_ratio:gt:0 to ensure we only get finalized auction results
    # This avoids records that are announced but have no results yet (values set to 'null')
    # Filter for bid_to_cover_ratio:gt:0 to ensure we only get finalized auction results
#    url = f"https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query?filter=security_type:eq:{security_type},security_term:eq:{security_term},bid_to_cover_ratio:gt:0&limit=1&sort=-auction_date"
    # Use original_security_term to capture reopenings (e.g. 9-Year 10-Month for a 10-Year Note)
    url = f"https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query?filter=security_type:eq:{security_type},original_security_term:eq:{security_term},bid_to_cover_ratio:gt:0&limit=1&sort=-auction_date"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get('data', [])
        return data[0] if data else {}
    return {}

def get_treasury_auctions():
    auc_10y = fetch_treasury_auctions("10-Year", "Note")
    auc_30y = fetch_treasury_auctions("30-Year", "Bond")

    if not auc_10y or not auc_30y:
        return {"indicator": "Treasury Auctions", "signal": "Neutral", "explanation": "No data", "value": 0}

    try:
        btc_10y = float(auc_10y['bid_to_cover_ratio'])
        tail_10y = (float(auc_10y['high_yield']) - float(auc_10y['avg_med_yield'])) * 100

        btc_30y = float(auc_30y['bid_to_cover_ratio'])
        tail_30y = (float(auc_30y['high_yield']) - float(auc_30y['avg_med_yield'])) * 100
    except (ValueError, TypeError, KeyError) as e:
        return {
            "indicator": "Treasury Auctions",
            "signal": "Neutral",
            "explanation": f"Data processing error: {e}",
            "value": 0,
            "last_updated": auc_10y.get('auction_date', 'N/A'),
            "source": "Treasury Fiscal Data"
        }

    avg_btc = (btc_10y + btc_30y) / 2
    max_tail = max(tail_10y, tail_30y)

    if max_tail <= 0 and avg_btc > 2.5:
        signal = "Bullish"
        explanation = f"Strong auctions: Avg BTC {avg_btc:.2f}, no tail"
    elif max_tail > 1.0 or avg_btc < 2.2:
        signal = "Bearish"
        explanation = f"Weak auctions: Avg BTC {avg_btc:.2f}, max tail {max_tail:.1f}bps"
    else:
        signal = "Neutral"
        explanation = f"Mixed auctions: Avg BTC {avg_btc:.2f}, max tail {max_tail:.1f}bps"

    return {
        "indicator": "Treasury Auctions",
        "value": round(avg_btc, 2),
        "signal": signal,
        "explanation": explanation,
        "last_updated": auc_10y['auction_date'],
        "source": "Treasury Fiscal Data"
    }

if __name__ == "__main__":
    print(get_treasury_auctions())
