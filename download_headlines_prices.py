import datetime
import json
import os
import re
import time

import eikon as ek
import pandas as pd
from dotenv import load_dotenv

# Use the STOXX 50 (wide, not eurozone only) index
INDEX_RIC = ".STOXX50"


def get_headlines_one_batch(
    rics: list[str], date_from: datetime.datetime, date_to: datetime.datetime
) -> list[dict]:
    query_build = [f"R:{ric}" for ric in rics]
    query_build = " OR ".join(query_build)

    headlines = ek.get_news_headlines(
        query=f"({query_build}) AND Language:LEN",
        count=100,
        date_from=date_from,
        date_to=date_to,
        raw_output=True,
    )

    return headlines


def download_instrument_headlines(
    main_ric: str,
    all_rics: list[str],
    max_retries: int = 10,
    out_dir: str = os.path.join("data", "headlines"),
):
    # Make sure the output directory exists
    os.makedirs(out_dir, exist_ok=True)

    # Prepare the date range
    starting_date = datetime.datetime.fromisoformat("2025-01-20T07:00:34.166+00:00")
    ending_date = datetime.datetime(2025, 6, 14, 23, 59, 59)

    with open(
        os.path.join(out_dir, f"{main_ric.replace('.', '-')}_headlines.json"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("[\n")

        retries, count = 0, 0
        while retries < max_retries:
            try:
                headlines = get_headlines_one_batch(
                    [main_ric], starting_date, ending_date
                )["headlines"]

            except Exception as e:
                retries += 1
                print(f"Error getting headlines for {main_ric}: {e}")
                print(f"Retrying... ({retries}/{max_retries})")
                # Sleep for 3 seconds before retrying
                time.sleep(3)
                continue

            if not headlines:
                break

            count += len(headlines)
            print(f"Downloading headlines for {main_ric}:\t\t{count}")

            for headline in headlines:
                f.write(json.dumps(headline, ensure_ascii=False))
                f.write(",\n")

            # Prepare next iteration
            retries = 0
            ending_date = headlines[-1]["versionCreated"]
            ending_date = (
                f"{ending_date[:-1]}+00:00" if ending_date[-1] == "Z" else ending_date
            )
            ending_date = datetime.datetime.fromisoformat(ending_date).replace(
                microsecond=0
            ) - datetime.timedelta(seconds=1)

        f.write("]\n")

        if retries == max_retries:
            f.write("FAILED\n")
            print(
                f"Probably failed to get all headlines for {main_ric} after {max_retries} retries"
            )


def get_instrument_stock_prices(
    instrument_ric: str, max_retries: int = 10
) -> pd.DataFrame:
    retries = 0
    while retries < max_retries:
        try:
            res = ek.get_timeseries(
                rics=instrument_ric,
                start_date=datetime.datetime(
                    2023, 10, 23
                ),  # Date of our first headlines
                end_date=datetime.datetime(
                    2025, 6, 14, 23, 59, 59
                ),  # Date of our last headlines
                interval="daily",
                fields=["TIMESTAMP", "CLOSE"],
                calendar="tradingdays",
                corax="adjusted",
            )

            if res is None or res.empty:
                raise ValueError(f"No data returned for {instrument_ric}")

            return res

        except Exception as e:
            retries += 1
            print(f"Error getting stock prices for {instrument_ric}: {e}")
            print(f"Retrying... ({retries}/{max_retries})")
            # Sleep for 3 seconds before retrying
            time.sleep(3)

    print(
        f"Failed to get stock prices for {instrument_ric} after {max_retries} retries"
    )


def fix_json_files(directory: str = os.path.join("data", "headlines")) -> None:
    # Check if directory exists
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist")
        return

    # Process all JSON files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)

            try:
                # Read the file content
                with open(filepath, "r", encoding="utf-8") as file:
                    content = file.read()

                # Fix the trailing comma issue: replace },] with }] (handling arbitrary whitespace)
                fixed_content = re.sub(r"},\s*]$", "}\n]", content)

                # Write the fixed content back to the file
                with open(filepath, "w", encoding="utf-8") as file:
                    file.write(fixed_content)

                print(f"Fixed: {filename}")

            except Exception as e:
                print(f"Error processing {filename}: {e}")


def main() -> None:
    load_dotenv()
    ek.set_app_key(os.getenv("EIKON_APP_KEY"))

    constituents_path = os.path.join("data", "constituents.csv")

    # Get the constituents of the index
    if os.path.exists(constituents_path):
        constituents = pd.read_csv(constituents_path)

    else:
        print("Download the constituents of the index with rics first.")
        exit()

    # Download headlines and stock prices for each constituent
    for _, row in constituents.iterrows():
        ric, all_rics = row["Instrument"], row["All RICs"].split(";")
        print(f"\n\nInstrument: {ric}")

        download_instrument_headlines(ric, all_rics)

        # We're getting prices one by one to avoid hitting API limits
        get_instrument_stock_prices(ric).to_csv(
            os.path.join("data", "prices", f"{ric.replace('.', '-')}.csv"), index=True
        )
        print("Downloaded stock price data")

    # Fix the generated JSON files
    fix_json_files()


if __name__ == "__main__":
    main()
