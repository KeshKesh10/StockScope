# StockScope

StockScope is a student-built full-stack stock analysis platform designed to demonstrate product thinking, API integration, and data-driven decision support.

The app allows a user to search a stock ticker, compute growth-focused valuation metrics, and manage a personalized favorites portfolio with authentication and industry filtering.

## Project Summary

- Built by students as a portfolio-ready web application
- Focuses on practical investing metrics:
  - 1-year Net Income Growth Rate
  - P/E Ratio
  - Growth over P/E (PEG-style signal)
  - Lynch-style validation (P/E < Growth)
- Includes user login/signup and user-scoped favorites storage
- Supports industry-based filtering via DynamoDB GSI query paths

## Key Features

- Login and signup flow before accessing the search experience
- Home search screen and dedicated stock results screen
- Error modal for ticker lookup failures
- Favorites saved per user (not shared globally)
- Industry filter for favorited stocks
- Enhanced stock context (52-week range, target price, latest reported period)

## Tech Stack

- Backend: Flask, Flask-Login, boto3
- Frontend: HTML templates, vanilla JavaScript, CSS
- Database: DynamoDB (DynamoDB Local in Docker for development)
- Testing: pytest
- Market Data Providers:
  - Finnhub (primary)
  - Alpha Vantage (supported)
  - yfinance fallback

## Requirements

- Docker Desktop
- Docker Compose
- Optional local Python 3.10+ for non-container workflows

## Environment Setup

Create a local .env file from .env.example and provide required keys.

Required variables:

- SECRET_KEY
- STOCK_DATA_PROVIDER (recommended: finnhub)
- FINNHUB_API_KEY
- ALPHAVANTAGE_API_KEY (optional when not using alpha)
- DynamoDB settings (already provided in .env.example)

## Run the Application (Recommended: Docker)

From project root:

```powershell
docker compose up -d dynamodb
docker compose run --rm app python scripts/init_dynamodb.py
docker compose up -d --build app
```

Open:

```text
http://127.0.0.1:5000
```

## Run Tests

Containerized test command:

```powershell
docker compose run --rm app python -m pytest -q
```

## API Endpoints

- POST /api/stock
- POST /api/auth/register
- POST /api/auth/login
- POST /api/favorites
- GET /api/favorites
- DELETE /api/favorites/<ticker>
- GET /api/signups
- POST /api/signups

## Metric Formula Used

Growth Rate = ((Ending Net Income - Beginning Net Income) / Beginning Net Income) * 100

Growth over P/E = Growth Rate / P/E Ratio

## Portfolio and Deliverables

Supporting project artifacts are included in docs:

- docs/PROJECT_OUTLINE.md
- docs/PAPER_PROTOTYPE.md
- docs/DEMO_SCRIPT.md

## Student Notes

This project was built as a student application to practice:

- full-stack architecture
- authentication and protected routing
- cloud-style data modeling with GSIs
- robust API error handling and provider fallback strategy
- test-driven validation of backend behavior
