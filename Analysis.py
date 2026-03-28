import logging

import pandas as pd

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = ["MA7", "MA30", "Daily_Return", "Volatility"]
REQUIRED_COLUMNS = ["Date", "Ticker", "Close", "Volume"]


def _empty_analyzed_frame(columns: list[str] | None = None) -> pd.DataFrame:
    base_columns = columns or REQUIRED_COLUMNS
    ordered_columns = list(dict.fromkeys(base_columns + FEATURE_COLUMNS))
    return pd.DataFrame(columns=ordered_columns)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return _empty_analyzed_frame(list(df.columns))

    enriched = df.copy().sort_values("Date").reset_index(drop=True)
    enriched["MA7"] = enriched["Close"].rolling(window=7, min_periods=1).mean()
    enriched["MA30"] = enriched["Close"].rolling(window=30, min_periods=1).mean()
    enriched["Daily_Return"] = enriched["Close"].pct_change().mul(100).fillna(0.0)
    enriched["Volatility"] = (
        enriched["Daily_Return"].rolling(window=7, min_periods=2).std().fillna(0.0)
    )
    return enriched


def analyze_market_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        logger.warning("Received empty market data; returning empty analysis frame")
        return _empty_analyzed_frame()

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        logger.error("Market data is missing required columns: %s", ", ".join(missing_columns))
        return _empty_analyzed_frame(list(df.columns))

    analyzed_frames = []
    for ticker, ticker_df in df.groupby("Ticker", sort=True):
        logger.info("Analyzing %s with %s rows", ticker, len(ticker_df))
        analyzed_frames.append(add_features(ticker_df))

    if not analyzed_frames:
        logger.warning("No grouped ticker data was available for analysis")
        return _empty_analyzed_frame(list(df.columns))

    analyzed = pd.concat(analyzed_frames, ignore_index=True)
    return analyzed.sort_values(["Ticker", "Date"]).reset_index(drop=True)
