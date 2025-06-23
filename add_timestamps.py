import os
import time

import eikon as ek
import pandas as pd
import pandas_market_calendars as mcal
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    ek.set_app_key(os.getenv("EIKON_APP_KEY"))

    directory = os.path.join(__file__, "..", "data", "prices")

    for file in os.listdir(directory):
        if not file.endswith(".csv"):
            continue

        # Get the instrument RIC
        ric = file.split(".")[0].replace("-", ".")
        print(f"Processing RIC: {ric}")

        # Get the exchange for the RIC
        success = False
        while not success:
            try:
                exchange = ek.get_data(
                    instruments=[ric],
                    fields=["TR.ExchangeMarketIdCode"],
                    field_name=True,
                )[0]["TR.EXCHANGEMARKETIDCODE"][0]
                print(f"\tFound exchange: {exchange}")
                success = True

            except Exception as e:
                print(f"\tError getting exchange for {ric}: {e}")
                print("\tRetrying...")
                # Sleep for 3 seconds before retrying
                time.sleep(3)

        # Handle edge cases
        if exchange == "MTAA":
            exchange = "XMIL"

        file_path = os.path.join(directory, file)
        df = pd.read_csv(file_path, parse_dates=["Date"], index_col="Date")

        # Get the trading calendar for the exchange
        sched = mcal.get_calendar(exchange)
        extended_sched = sched.schedule(start_date="2023-10-23", end_date="2025-06-11")
        # Use market close times for timestamps
        trading_days = extended_sched["market_close"]

        # Build a map from plain dates to close‐of‐day timestamps
        td = trading_days.copy()
        td.index = td.index.normalize()

        # Replace the date‐only index with the corresponding timestamps
        df.index = df.index.map(td.to_dict())

        # Save the df
        df.to_csv(file_path, index=True)

        print(f"Processed {file} with timestamps.")
