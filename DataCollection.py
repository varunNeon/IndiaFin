import logging
import time

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# Our watchlist - 8 Indian stocks
STOCKS = {
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Zomato": "ETERNAL.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Adani Ports": "ADANIPORTS.NS",
    "Wipro": "WIPRO.NS",
    "ITC": "ITC.NS",
}

BASE_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume", "Ticker"]


def empty_market_data() -> pd.DataFrame:
    return pd.DataFrame(columns=BASE_COLUMNS)


def _normalize_history_frame(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if df.empty:
        return empty_market_data()

    history = df.reset_index().copy()
    history = history.rename(columns={history.columns[0]: "Date"})
    history = history[["Date", "Open", "High", "Low", "Close", "Volume"]]
    history["Ticker"] = ticker
    history["Date"] = pd.to_datetime(history["Date"], errors="coerce")
    history = history.dropna(subset=["Date", "Close"]).sort_values("Date").reset_index(drop=True)
    return history


def fetch_stock_data(ticker: str, period: str = "6mo", max_retries: int = 3, retry_delay: float = 1.0) -> pd.DataFrame:
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Fetching data for %s (attempt %s/%s)", ticker, attempt, max_retries)
            stock = yf.Ticker(ticker)
            history = stock.history(period=period)
            if history.empty:
                logger.warning("No data found for %s", ticker)
                return empty_market_data()
            return _normalize_history_frame(history, ticker)
        except Exception:
            logger.exception("Fetch failed for %s on attempt %s/%s", ticker, attempt, max_retries)
            if attempt < max_retries:
                time.sleep(retry_delay * attempt)

    logger.error("Giving up on %s after %s attempts", ticker, max_retries)
    return empty_market_data()


def fetch_all_stock_data(stocks: dict[str, str] | None = None, period: str = "6mo") -> pd.DataFrame:
    watchlist = stocks or STOCKS
    all_data = []

    for name, ticker in watchlist.items():
        logger.info("Starting fetch for %s (%s)", name, ticker)
        data = fetch_stock_data(ticker, period=period)
        if data.empty:
            logger.warning("Skipping %s because no usable rows were returned", ticker)
            continue
        all_data.append(data)

    if not all_data:
        logger.error("No stock data could be fetched for the configured watchlist")
        return empty_market_data()

    combined = pd.concat(all_data, ignore_index=True)
    combined = combined.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    logger.info("Fetched %s rows across %s tickers", len(combined), combined["Ticker"].nunique())
    return combined
