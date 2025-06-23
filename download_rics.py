import os

import eikon as ek
import pandas as pd
from dotenv import load_dotenv
from eikon import TR_Field

# Use the STOXX 50 (wide, not eurozone only) index
INDEX_RIC = ".STOXX50"


def get_constituents_of_index(index_ric: str) -> pd.DataFrame:
    print("Getting constituents for index:", index_ric)
    constituents, err = ek.get_data(
        instruments=index_ric,
        fields=[
            TR_Field("TR.IndexConstituentRIC"),
        ],
    )

    if err is not None:
        raise ValueError(f"Error getting index constituents: {err}")

    details, err = ek.get_data(
        constituents["Constituent RIC"].tolist(),
        fields=[
            TR_Field("TR.CommonName"),
            TR_Field("TR.BussinessSummary"),
            TR_Field("TR.TRBCEconomicSector"),
            TR_Field("TR.HeadquartersCountry"),
            TR_Field(
                "TR.CompanyMarketCap", {"Scale": 6, "Curn": "USD"}, sort_dir="desc"
            ),
        ],
    )

    if err is not None:
        raise ValueError(f"Error getting constituents details: {err}")

    return details


def find_all_rics(main_ric: str) -> list[str]:
    print("Getting all RICs for original main RIC:", main_ric)
    isin = ek.get_symbology(main_ric, from_symbol_type="RIC", to_symbol_type="ISIN")[
        "ISIN"
    ].iloc[0]
    return ek.get_symbology(
        isin, from_symbol_type="ISIN", to_symbol_type="RIC", best_match=False
    )["RICs"].iloc[0]


def main() -> None:
    load_dotenv()
    ek.set_app_key(os.getenv("EIKON_APP_KEY"))

    constituents_path = os.path.join("data", "constituents.csv")

    constituents = get_constituents_of_index(INDEX_RIC)

    for i, main_ric in enumerate(constituents["Instrument"]):
        all_rics = find_all_rics(main_ric)
        # Add the rics to the dataframe as new column
        constituents.loc[i, "All RICs"] = ";".join(all_rics)

    # Save the data
    constituents.to_csv(constituents_path, index=False)


if __name__ == "__main__":
    main()
