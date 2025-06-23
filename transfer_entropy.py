from datetime import datetime
import os

import matplotlib.pyplot as plt
import pandas as pd
from idtxl.data import Data
from idtxl.multivariate_te import MultivariateTE
from idtxl.visualise_graph import plot_network


def prepare_data():
    # Load data
    aggregate_dir = os.path.join("data", "aggregate")

    dfs = []
    all_dates = set()

    # First pass: collect all unique dates and prepare dataframes
    for file in os.listdir(aggregate_dir):
        if not file.endswith(".csv"):
            continue

        file_path = os.path.join(aggregate_dir, file)

        # Load the CSV
        temp_df = pd.read_csv(file_path, parse_dates=["Date"])
        temp_df.dropna(subset=["LOG_RETURNS"], inplace=True)
        temp_df.drop(columns=["CLOSE"], inplace=True)
        # Keep only the date part from the 'Date' column
        temp_df["Date"] = temp_df["Date"].dt.date

        # Collect all dates
        all_dates.update(temp_df["Date"])

        # Set Date as index
        temp_df.set_index("Date", inplace=True)

        # Prepend column names with filename
        temp_df.columns = [f"{file.split('.')[0]}_{col}" for col in temp_df.columns]

        dfs.append(temp_df)

    # Create a complete date range
    all_dates = sorted(all_dates)
    complete_date_index = pd.Index(all_dates, name="Date")

    # Reindex all dataframes to have the complete date range and forward fill
    aligned_dfs = []
    for temp_df in dfs:
        # Reindex to complete date range
        temp_df_aligned = temp_df.reindex(complete_date_index)
        # Forward fill missing values (use values from closest previous date)
        temp_df_aligned = temp_df_aligned.fillna(method="ffill")
        aligned_dfs.append(temp_df_aligned)

    # Merge all dataframes horizontally
    df = pd.concat(aligned_dfs, axis=1)

    # Sort columns alphabetically
    df = df.sort_index(axis=1)

    print(df.head())

    # Check for NaN values in the dataframe
    nan_counts = df.isna().sum()
    print("NaN counts per column:")
    print(nan_counts[nan_counts > 0])

    return df


if __name__ == "__main__":
    df = prepare_data()

    # Print the column names with their indices
    print("Columns in the DataFrame:")
    print([f"{i}: {col}" for i, col in enumerate(df.columns)])

    # exit()

    data = Data(df, dim_order="sp")

    # Initialise analysis object and define settings
    network_analysis = MultivariateTE()

    settings = {
        "cmi_estimator": "OpenCLKraskovCMI",
        "kraskov_k": 4,
        "noise_level": 0.0,
        "max_lag_sources": 5,
        "min_lag_sources": 1,
        "max_lag_target": 5,
        "tau_sources": 1,
        "tau_target": 1,
        "n_perm_max_stat": 500,
        "n_perm_min_stat": 500,
        "n_perm_omnibus": 20000,
        "n_perm_max_seq": 20000,
        "alpha_max_stat": 0.05,
        "alpha_min_stat": 0.05,
        "alpha_omnibus": 0.05,
        "alpha_max_seq": 0.05,
        "alpha_fdr": 0.05,
        "fdr_correction": True,
        "fdr_constant": 2,
        "correct_by_target": True,
        "verbose": True,
    }

    print(f"Startging analysis with settings: {settings}")

    # Run analysis
    results = network_analysis.analyse_network(settings=settings, data=data)

    # Plot inferred network to console and via matplotlib
    print("FDR uncorrected edge list:")
    results.print_edge_list(weights="max_te_lag", fdr=False)
    print("FDR corrected edge list:")
    results.print_edge_list(weights="max_te_lag", fdr=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_network(results=results, weights="max_te_lag", fdr=False)
    plt.savefig(f"uncorrected_network_plot_{timestamp}.pdf", bbox_inches="tight")
    plot_network(results=results, weights="max_te_lag", fdr=True)
    plt.savefig(f"corrected_network_plot_{timestamp}.pdf", bbox_inches="tight")

    print("FDR uncorrected source variables:")
    source_vars = results.get_source_variables(fdr=False)
    print(source_vars)
    print("FDR corrected source variables:")
    source_vars_fdr = results.get_source_variables(fdr=True)
    print(source_vars_fdr)
