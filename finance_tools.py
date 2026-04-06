import numpy as np
import yfinance as yf


TA125_TICKER = "^TA125.TA"


def get_ta125_change(days: int = 2) -> dict[str, float] | None:
    """
    Calculate the latest percentage change in the TA-125 index.

    The function fetches recent historical data and computes the change
    between the last two available closing prices.

    Args:
        days (int): Number of recent days to fetch.
                    Default is 2 (minimum needed for comparison).

    Returns:
        dict[str, float] | None:
            {
                "previous_close": float,
                "last_close": float,
                "change_pct": float
            }
            Returns None if data could not be retrieved.

    Notes:
        - Automatically retries with a longer period to handle weekends
          and market holidays.
        - Requires at least 2 valid closing prices.
    """
    ticker = yf.Ticker(TA125_TICKER)

    # Step 1: Try fetching minimal required period
    hist = ticker.history(period=f"{days}d")

    # Step 2: Retry with extended range if needed
    if hist.empty or len(hist) < 2:
        extended_days = days + 3  # buffer for non-trading days
        hist = ticker.history(period=f"{extended_days}d")

        # Still not enough usable data → fail gracefully
        if hist.empty or len(hist) < 2:
            return None

    # Step 3: Extract last two closing prices
    # Using tail ensures robustness even if extra rows exist
    last_two = hist["Close"].dropna().tail(2)

    if len(last_two) < 2:
        return None

    prev_close, last_close = last_two.iloc[0], last_two.iloc[1]

    # Step 4: Compute change
    change = last_close - prev_close
    change_pct = (change / prev_close) * 100

    # Step 5: Format result
    return {
        "previous_close": float(np.round(prev_close, 2)),
        "last_close": float(np.round(last_close, 2)),
        "change_pct": float(np.round(change_pct, 2)),
    }


if __name__ == "__main__":
    # Simple manual test
    print(get_ta125_change())