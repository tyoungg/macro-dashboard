import requests
from datetime import datetime
import time

def get_treasury_auctions():
    # Fetch the 5 most recent finalized nominal auctions (Notes, Bonds, and Bills)
    # We filter for bid_to_cover_ratio:gt:0 to ensure results are finalized.
    # inflation_index_security:eq:No and floating_rate:eq:No filter for nominal fixed-rate securities.
    # Add a timestamp to the URL to prevent server-side caching.
    timestamp = int(time.time())
    url = (
        "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query"
        f"?filter=bid_to_cover_ratio:gt:0,inflation_index_security:eq:No,floating_rate:eq:No"
        f"&limit=5&sort=-auction_date&_ts={timestamp}"
    )

    try:
        response = requests.get(url)
        if response.status_code != 200:
            return {"indicator": "Treasury Auctions", "signal": "Neutral", "explanation": f"API Error: {response.status_code}", "value": 0}

        data = response.json().get('data', [])
        if not data:
            return {"indicator": "Treasury Auctions", "signal": "Neutral", "explanation": "No data returned from API", "value": 0}

        total_btc = 0
        total_tail = 0
        valid_auctions = 0
        last_updated = data[0]['auction_date']

        for auction in data:
            try:
                btc = float(auction['bid_to_cover_ratio'])

                # Determine tail based on security type
                # Bills use discount rate; Notes/Bonds use yield
                if auction['security_type'] == 'Bill':
                    high = auction.get('high_discnt_rate')
                    avg_med = auction.get('avg_med_discnt_rate')
                else:
                    high = auction.get('high_yield')
                    avg_med = auction.get('avg_med_yield')

                if high and avg_med and high != 'null' and avg_med != 'null':
                    tail = (float(high) - float(avg_med)) * 100
                else:
                    tail = 0 # Assume no tail if data is missing but BTC is present

                total_btc += btc
                total_tail += tail
                valid_auctions += 1
            except (ValueError, TypeError, KeyError):
                continue

        if valid_auctions == 0:
            return {"indicator": "Treasury Auctions", "signal": "Neutral", "explanation": "Could not process auction data", "value": 0}

        avg_btc = total_btc / valid_auctions
        avg_tail = total_tail / valid_auctions

        # Signal logic based on averaged metrics
        if avg_tail <= 0.2 and avg_btc > 2.5:
            signal = "Bullish"
            explanation = f"Strong demand (Avg of 5): BTC {avg_btc:.2f}, Tail {avg_tail:.1f}bps"
        elif avg_tail > 1.0 or avg_btc < 2.3:
            signal = "Bearish"
            explanation = f"Weak demand (Avg of 5): BTC {avg_btc:.2f}, Tail {avg_tail:.1f}bps"
        else:
            signal = "Neutral"
            explanation = f"Stable demand (Avg of 5): BTC {avg_btc:.2f}, Tail {avg_tail:.1f}bps"

        return {
            "indicator": "Treasury Auctions",
            "value": round(avg_btc, 2),
            "signal": signal,
            "explanation": explanation,
            "last_updated": last_updated,
            "source": "Treasury Fiscal Data"
        }

    except Exception as e:
        return {
            "indicator": "Treasury Auctions",
            "signal": "Neutral",
            "explanation": f"Unexpected error: {str(e)}",
            "value": 0
        }

if __name__ == "__main__":
    import json
    print(json.dumps(get_treasury_auctions(), indent=2))
