def bank_stress(relative_perf):
    """
    Metric: 1-month relative performance vs S&P
    Signal: Bullish if outperforming, Bearish if underperforming > 5%
    """
    if relative_perf > 0:
        signal = "Bullish"
        explanation = f"Banks outperforming S&P 500 by {relative_perf:.1f}%"
    elif relative_perf < -5:
        signal = "Bearish"
        explanation = f"Banks underperforming S&P 500 by {abs(relative_perf):.1f}%"
    else:
        signal = "Neutral"
        explanation = f"Banks performing in-line with S&P 500 ({relative_perf:+.1f}%)"

    return relative_perf, signal, explanation

def equity_breadth(pct_above_200dma):
    """
    Metric: % of stocks above 200DMA
    Signal: Bullish > 65%, Neutral 40-65%, Bearish < 40%
    """
    if pct_above_200dma > 65:
        signal = "Bullish"
        explanation = f"Broad participation: {pct_above_200dma:.1f}% of stocks above 200DMA"
    elif pct_above_200dma < 40:
        signal = "Bearish"
        explanation = f"Poor participation: only {pct_above_200dma:.1f}% of stocks above 200DMA"
    else:
        signal = "Neutral"
        explanation = f"Average participation: {pct_above_200dma:.1f}% of stocks above 200DMA"

    return pct_above_200dma, signal, explanation
