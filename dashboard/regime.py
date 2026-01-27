def classify(signals_dict):
    """
    signals_dict: { 'indicator_name': (value, signal, explanation), ... }
    """
    signals_list = [v[1] for v in signals_dict.values()]
    bearish_count = signals_list.count("Bearish")
    bullish_count = signals_list.count("Bullish")

    # Identify specific signals for PRE-STRESS rules
    hy_spread_signal = signals_dict.get('High Yield Credit Spread', (0, "Neutral", ""))[1]
    auctions_signal = signals_dict.get('Treasury Auctions', (0, "Neutral", ""))[1]
    bank_stress_signal = signals_dict.get('Bank Stress', (0, "Neutral", ""))[1]
    gold_signal = signals_dict.get('Gold vs Real Rates', (0, "Neutral", ""))[1]

    credit_bearish = hy_spread_signal == "Bearish" or auctions_signal == "Bearish"
    bank_bearish = bank_stress_signal == "Bearish"

    # Rule 1: PRE-STRESS if >= 3 bearish including credit or banks
    if bearish_count >= 3 and (credit_bearish or bank_bearish):
        return "PRE-STRESS"

    # Rule 2: If gold is Bullish and credit is Neutral-to-Bearish -> elevate to PRE-STRESS
    # "Neutral-to-Bearish" usually means NOT Bullish.
    credit_not_bullish = hy_spread_signal != "Bullish" and auctions_signal != "Bullish"
    if gold_signal == "Bullish" and credit_not_bullish:
        return "PRE-STRESS"

    if bearish_count >= 5:
        return "TIGHT / FRAGILE"
    elif bullish_count >= 5:
        return "EASING / RISK-ON"
    else:
        return "TRANSITION"

def get_regime_emoji(regime):
    if regime == "EASING / RISK-ON":
        return "🟢"
    elif regime == "TRANSITION":
        return "🟡"
    elif regime == "TIGHT / FRAGILE":
        return "🔴"
    elif regime == "PRE-STRESS":
        return "⚠️"
    return "❓"
