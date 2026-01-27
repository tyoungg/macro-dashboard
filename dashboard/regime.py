def classify(signals_dict):
    """
    signals_dict: { 'indicator_name': (value, signal, explanation), ... }
    """
    signals_list = [v[1] for v in signals_dict.values()]
    bearish_count = signals_list.count("Bearish")
    bullish_count = signals_list.count("Bullish")

    # Identify specific signals for PRE-STRESS rule
    # Credit indicators: High Yield Credit Spread, Treasury Auctions
    # Bank indicators: Bank Stress
    credit_bearish = signals_dict.get('High Yield Credit Spread', (0, "Neutral", ""))[1] == "Bearish" or \
                     signals_dict.get('Treasury Auctions', (0, "Neutral", ""))[1] == "Bearish"
    bank_bearish = signals_dict.get('Bank Stress', (0, "Neutral", ""))[1] == "Bearish"

    # Rule: PRE-STRESS if >= 3 bearish including credit or banks
    if bearish_count >= 3 and (credit_bearish or bank_bearish):
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
