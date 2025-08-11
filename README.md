# Transfer Entropy Analysis of Extracted News Sentiment and Stock Returns

This repository contains the accompanying code for the master thesis [*Causal Information Flow in European Financial Markets: Transfer Entropy Analysis of News Sentiment and STOXX50 Returns*](https://vskp.vse.cz/98345_tok-informaci-na-evropskych-financnich-trzich-analyza-prenosove-entropie-mezi-sentimentem-novinovych-titulku-a-cenami-akcii-firem-indexu-stoxx50) that analyzes the relationship between financial news sentiment and stock price movements using transfer entropy analysis on STOXX 50 constituents. 

The final logs of our own analysis can be found in `transfer_entropy_20250622_111804.log`.

## Overview

The project implements a complete pipeline from financial news data collection to transfer entropy analysis:

1. **Data Collection**: Downloads financial headlines and stock prices for STOXX 50 constituents using the Eikon API
2. **Sentiment Analysis**: Applies FinBERT models to classify news headlines sentiment 
3. **Data Processing**: Filters automated news, aggregates sentiment scores with price data
4. **Transfer Entropy Analysis**: Analyzes directional information flow between sentiment and stock returns

## Table of Contents

- [Transfer Entropy Analysis of Extracted News Sentiment and Stock Returns](#transfer-entropy-analysis-of-extracted-news-sentiment-and-stock-returns)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [Requirements](#requirements)
    - [Platform Support](#platform-support)
    - [Eikon API Setup](#eikon-api-setup)
    - [Dependencies](#dependencies)
  - [Data Availability](#data-availability)
  - [Installation](#installation)
  - [Pipeline Execution Order](#pipeline-execution-order)
    - [1. Download Constituent Data](#1-download-constituent-data)
    - [2. Download Headlines and Prices](#2-download-headlines-and-prices)
    - [3. Run Sentiment Predictions](#3-run-sentiment-predictions)
    - [4. Filter Headlines](#4-filter-headlines)
    - [5. Add Market Timestamps](#5-add-market-timestamps)
    - [6. Aggregate Data](#6-aggregate-data)
    - [7. Transfer Entropy Analysis (Docker Required)](#7-transfer-entropy-analysis-docker-required)
  - [Sentiment Analysis Benchmarking](#sentiment-analysis-benchmarking)
    - [Ground Truth Creation](#ground-truth-creation)
    - [Model Benchmarking](#model-benchmarking)
  - [Project Structure](#project-structure)
  - [Citation](#citation)
  - [License](#license)


## Requirements

### Platform Support
- Most of the pipeline can be run on any platform using the `uv` package manager
- We provide a Dockerfile for the final transfer entropy analysis due to complex dependencies, but you can also install [`idtxl`](https://github.com/pwollstadt/IDTxl) and its dependencies manually if you prefer not to use Docker

### Eikon API Setup
To download financial data, you need:
1. **Eikon Application**: The Eikon desktop application must be running (the API uses it as a proxy)
2. **Environment Variables**: Create a `.env` file with your Eikon API key (you can copy and edit the provided `.env.example` file):
   ```
   EIKON_APP_KEY=your_api_key_here
   ```

### Dependencies
- [`uv` package manager](https://docs.astral.sh/uv/getting-started/installation/)
- **Eikon Terminal** subscription and [application](https://eikon.refinitiv.com/)
- [**Docker**](https://docs.docker.com/desktop/) with GPU support ([Windows](https://docs.docker.com/desktop/features/gpu/), [Linux](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)) (optional, for transfer entropy analysis only)

## Data Availability

**Important Note**: We cannot release the underlying financial data as it is proprietary and belongs to Refinitiv/LSEG. The data includes:
- Financial news headlines from the Eikon news feed
- Stock price data for STOXX 50 constituents
- Any derived datasets

If you have access to Eikon, you can reproduce the entire analysis by following the pipeline below.

## Installation

1. **Clone the repository** (skip this step if you obtained the code through other means):
   ```bash
   git clone <repository-url>
   cd thesis-sentiment-stock-transfer-entropy
   ```

2. **Install dependencies using uv** (note the `--frozen` flag that ensures exact reproducibility):
   ```bash
   uv sync --frozen
   ```

3. **Set up environment variables**:
   ```bash
   # Create .env file with your Eikon API key
   echo "EIKON_APP_KEY=your_api_key_here" > .env
   ```

## Pipeline Execution Order

To reproduce the complete analysis, run the scripts in the following order:

### 1. Download Constituent Data
```bash
uv run --frozen download_rics.py
```
Downloads the list of STOXX 50 constituents and their RIC identifiers.

### 2. Download Headlines and Prices
```bash
uv run --frozen download_headlines_prices.py
```
Downloads financial headlines and daily stock prices for each constituent. **Requires Eikon application to be running.**

### 3. Run Sentiment Predictions
```bash
uv run --frozen predict.py
```
Applies FinBERT sentiment analysis to all downloaded headlines.

### 4. Filter Headlines
```bash
uv run --frozen filter_headlines.py
```
Removes automated/technical news that most probably don't carry meaningful sentiment signals (e.g., filing notifications, technical updates).

### 5. Add Market Timestamps
```bash
uv run --frozen add_timestamps.py
```
Adds proper market trading timestamps to the price data using exchange calendars.

### 6. Aggregate Data
```bash
uv run --frozen aggregate_test.py
```
Combines sentiment scores with price returns, creating the final dataset for transfer entropy analysis. Tests the time series for stationarity using ADF tests.

### 7. Transfer Entropy Analysis (Docker Required)
```bash
# Build the Docker image
docker build -t idtxl_image .

# Run transfer entropy analysis with GPU support
docker run -d --rm --name idtxl_container -v ./:/opt/analysis --gpus all idtxl_image bash -c "cd /opt/analysis && /opt/.venv/bin/python3 transfer_entropy.py > /opt/analysis/transfer_entropy_$(date +%Y%m%d_%H%M%S).log 2>&1"
```

**Why Docker?** The transfer entropy analysis uses [IDTxl](https://github.com/pwollstadt/IDTxl), which has complex dependencies including:
- OpenCL for GPU acceleration
- Java Virtual Machine integration
- Specific versions of scientific libraries
- OpenMPI for parallel processing

While you can install these dependencies manually, Docker provides a reliable, reproducible environment. If you don't have GPU support, you can run the container without the `--gpus all` and change the estimator in `transfer_entropy.py` to `JidtKraskovCMI` (CPU-based), but performance will degrade.

## Sentiment Analysis Benchmarking

The project includes a microbenchmark to evaluate different sentiment analysis models:

### Ground Truth Creation
- **Dataset**: 300 randomly selected headlines from our data (`data/random_headlines.json`)
- **Labeling**: Pseudolabeled using OpenAI's o1 model with the prompt in `prompt.txt`
- **Prompt Design**: Specifically crafted for few-shot financial sentiment analysis

### Model Benchmarking
We benchmarked several models:

**Hugging Face Models**:
```bash
uv run --frozen benchmark_models.py
```
Tests:
- `mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis`
- `ProsusAI/finbert` 
- `yiyanghkust/finbert-tone`

**Qwen3:8B Model**:
```bash
uv run --frozen benchmark_qwen.py
```
Tests the Qwen3:8B model via [Ollama API](https://ollama.com/download) for comparison with smaller alternatives.

Benchmark results are saved in `data/benchmark/` with accuracy metrics against the pseudolabels.

## Project Structure

```
master-finsent/
├── README.md
├── pyproject.toml          # Python dependencies
├── uv.lock                 # Dependency lock file
├── Dockerfile              # Docker environment for transfer entropy
├── .env                    # Eikon API configuration (create yourself)
│
├── download_rics.py        # Step 1: Download constituent list
├── download_headlines_prices.py # Step 2: Download data from Eikon
├── predict.py              # Step 3: Run sentiment predictions  
├── filter_headlines.py     # Step 4: Filter automated news
├── add_timestamps.py       # Step 5: Add market timestamps
├── aggregate_test.py       # Step 6: Combine sentiment & prices, test stationarity
├── transfer_entropy.py     # Step 7: Transfer entropy analysis
│
├── benchmark_models.py     # Benchmark HF models
├── benchmark_qwen.py       # Benchmark Qwen model
├── prompt.txt              # Sentiment labeling prompt for o1
│
└── data/
    ├── constituents.csv    # STOXX 50 constituent list
    ├── random_headlines.json # Benchmark dataset (300 headlines)
    ├── headlines/          # Raw headlines from Eikon
    ├── headlines_preds/    # Headlines with sentiment predictions
    ├── filtered_headlines/ # Filtered headlines  
    ├── prices/             # Stock price data
    ├── aggregate/          # Final combined datasets
    └── benchmark/          # Model benchmark results
```

## Citation

If you find any of this useful in your research, please cite the associated master's thesis (details to be added upon publication).

## License

This project is licensed under the MIT license. However, it integrates the Eikon Data API, which is licensed separately and requires a valid subscription from LSEG. This project also uses multiple packages that are licensed under various open-source licenses (MIT, Apache 2.0, BSD-3-Clause, GPL-3.0). Please refer to the respective licenses for more details.
