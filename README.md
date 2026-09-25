# Financial Research AI Agent

A higher-level Streamlit financial research dashboard for Indian stock market analysis.

## Features

- Indian stock lookup using Yahoo Finance symbols such as `RELIANCE.NS`, `TCS.NS`, and `INFY.NS`
- Stock price chatbot with symbol extraction
- Cached market data fetching for faster reloads and fewer API calls
- Candlestick chart with volume, 20-day SMA, 50-day SMA, and Bollinger Bands
- RSI and MACD technical indicators
- Risk analytics: total return, annual volatility, Sharpe ratio, max drawdown, best day, worst day, and positive-day ratio
- Normalized comparison against another stock and a benchmark such as `^NSEI`
- CSV export and downloadable text research report
- Modular Python architecture under `src/`
- GitHub Actions CI for compile checks and unit tests
- Educational disclaimer for responsible financial analysis

## Tech Stack

- Python
- Streamlit
- yfinance
- Plotly
- pandas
- numpy

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run Locally

```bash
python -m streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## Example Symbols

- `RELIANCE.NS`
- `TCS.NS`
- `INFY.NS`
- `HDFCBANK.NS`
- `SBIN.NS`
- `^NSEI`

## Project Structure

```text
financial-research-ai-agent/
  app.py
  requirements.txt
  src/
    data.py
    indicators.py
    metrics.py
    reporting.py
  tests/
    test_indicators.py
  .github/workflows/ci.yml
```

## Run Tests

```bash
python -m unittest discover tests
```

## Deployment

This project is ready for Streamlit Community Cloud deployment.

1. Push this folder to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app from the GitHub repository.
4. Select `app.py` as the entry file.
5. Deploy.

## Live Demo

Streamlit App: https://financial-research-ai-agent-lj5i2bxh7tj6csoia6ga4t.streamlit.app/

## Demo Video

Demo video is included with the final submission.

## Disclaimer

This app provides educational financial analysis only. It does not provide investment advice. Consult a registered financial advisor before making investment decisions.
## Screenshots

### Overview
![Overview](screenshots/overview.png)

### Charts
![Charts](screenshots/charts.png)

### Risk Metrics
![Risk](screenshots/risk.png)

### Comparison
![Comparison](screenshots/comparison.png)

### Watchlist
![Watchlist](screenshots/watchlist.png)

### Fundamentals
![Fundamentals](screenshots/fundamentals.png)

### News Sentiment
![News Sentiment](screenshots/news.png)

### Export
![Export](screenshots/export.png)
