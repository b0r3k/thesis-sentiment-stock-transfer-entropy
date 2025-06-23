import os

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller


def create_sentiment_df(prices_path, headlines_path):
    # Load price data with timestamps
    price_df = pd.read_csv(prices_path, parse_dates=["Date"])
    # Load headlines and parse creation times
    headlines_df = pd.read_json(headlines_path)
    headlines_df["versionCreated"] = pd.to_datetime(headlines_df["versionCreated"])

    # Map sentiment labels to scores
    headlines_df["sentiment_score"] = headlines_df["label"].map(
        {"positive": 1, "neutral": 0, "negative": -1}
    )

    # Ensure sorted order for merge_asof
    price_df = price_df.sort_values("Date")
    headlines_df = headlines_df.sort_values("versionCreated")

    # Remove empty rows from price_df
    price_df = price_df[price_df["CLOSE"].notna() & price_df["Date"].notna()]

    # Assign each headline to the next market close timestamp
    merged = pd.merge_asof(
        headlines_df,
        price_df[["Date"]],
        left_on="versionCreated",
        right_on="Date",
        direction="forward",
        allow_exact_matches=True,
    )

    # Drop headlines without an assigned close timestamp
    merged = merged.dropna(subset=["Date"])

    # Sum sentiment scores per timestamp
    sentiment_sum = (
        merged.groupby("Date")["sentiment_score"]
        .sum()
        .reset_index()
        .rename(columns={"sentiment_score": "SENTIMENT"})
    )

    # Merge summed sentiment with price data
    result_df = (
        price_df[["CLOSE", "Date"]]
        .merge(sentiment_sum, on="Date", how="left")
        .fillna({"SENTIMENT": 0})
    )
    result_df["SENTIMENT"] = result_df["SENTIMENT"].astype(int)

    # Crop result to available sentiment dates
    last_date = sentiment_sum["Date"].max()
    result_df = result_df[result_df["Date"] <= last_date]
    return result_df


def test_stationarity(serie, column_name):
    """
    Test the stationarity of a time series using ADF test.
    """
    stationary = True

    adf_result = adfuller(serie.dropna())
    p_value_adf = adf_result[1]
    if p_value_adf >= 0.05:
        stationary = False

    return stationary, p_value_adf


if __name__ == "__main__":
    prices_path = os.path.join("data", "prices")
    headlines_path = os.path.join("data", "filtered_headlines")

    aggregate_path = os.path.join("data", "aggregate")
    os.makedirs(aggregate_path, exist_ok=True)

    for file in os.listdir(prices_path):
        if not file.endswith(".csv"):
            continue

        ticker = file.split(".")[0]
        print(f"Processing {ticker}...")

        df = create_sentiment_df(
            os.path.join(prices_path, file),
            os.path.join(headlines_path, f"{ticker}_headlines.json"),
        )

        # compute log returns on the CLOSE
        df["LOG_RETURNS"] = np.log(df["CLOSE"] / df["CLOSE"].shift(1))

        returns_stationary, returns_p = test_stationarity(
            df["LOG_RETURNS"], "LOG_RETURNS"
        )
        sentiment_stationary, sentiment_p = test_stationarity(
            df["SENTIMENT"], "SENTIMENT"
        )

        if not returns_stationary or not sentiment_stationary:
            print(
                f"\n!!!\nRemoving {ticker} from the dataset due to non-stationarity -- LOG_RETURNS {'non-' if not returns_stationary else ''}stationary (p-value: {returns_p}), SENTIMENT {'non-' if not sentiment_stationary else ''}stationary (p-value: {sentiment_p}).\n!!!\n"
            )
            continue

        df.to_csv(
            os.path.join(aggregate_path, f"{ticker}.csv"),
            index=False,
        )
