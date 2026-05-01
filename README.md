# StockScope

A full-stack stock analysis web app. Search any ticker to view growth-focused valuation metrics, save favorites, and filter by industry.

## Features

- Authenticated search — login required before accessing stock data
- Per-user favorites with industry filtering
- Metrics: 1-year Net Income Growth Rate, P/E Ratio, Growth/P/E (PEG-style signal)
- Additional context: 52-week range, analyst target price, latest reported quarter
- Error handling with fallback data providers (Finnhub → yFinance)

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask, Flask-Login, boto3 |
| Frontend | Jinja2 templates, vanilla JS, CSS |
| Database | DynamoDB Local (Docker) |
| Market Data | Finnhub (primary), yFinance (fallback) |
| Testing | pytest |

## Getting Started

**Requires:** Docker Desktop running.

**1. Navigate to the project folder**
```powershell
cd C:\Users\rakes\Downloads\StockScope
```

**2. Start all services**
```powershell
docker compose up -d
```

**3. Initialize DynamoDB tables** *(first time only)*
```powershell
docker compose run --rm app python scripts/init_dynamodb.py
```

**4. Open the app in your browser**
```
http://127.0.0.1:5000
```

**5. Stop the app**
```powershell
docker compose down
```

## Run Tests

```powershell
docker compose run --rm app python -m pytest -q
```

## Other Useful Commands

```powershell
# View live app logs
docker compose logs -f app

# Rebuild after code changes
docker compose up -d --build app
```

## Metrics

```
Growth Rate     = (Net Income this year - last year) / last year × 100
Growth / P/E    = Growth Rate / P/E Ratio
```

A Growth/P/E above 1.0 is a Lynch-style buy signal.

## Environment

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session secret |
| `FINNHUB_API_KEY` | Finnhub API key |
| `STOCK_DATA_PROVIDER` | `finnhub` (recommended) |
