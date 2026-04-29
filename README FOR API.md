# StockScope

StockScope is a full-stack stock analysis app that lets users query a ticker and evaluate it using growth-focused valuation signals:

- 1-year net income growth rate (computed from Alpha Vantage annual income statement data)
- P/E ratio
- Growth over P/E ratio (growth divided by P/E)
- Lynch-style check (P/E < growth)

It also supports user accounts and user-specific favorite stocks stored in a database with industry tagging and industry-based filtering.

## Features

### Required
- Query stock by ticker symbol
- Calculate 1-year growth rate using:
	- `Growth Rate = ((Ending - Beginning) / Beginning) * 100`
	- Beginning and ending values taken from net income in the latest two annual reports
- Show P/E ratio from provider data
- Show Growth/P-E and indicate Lynch check pass/fail
- Popup error modal if ticker is not found

### Nice to Have (Implemented)
- Favorite a stock and store it in database
- Save industry while storing favorite
- Show user favorites with metrics
- Filter favorites by industry

### Next Level (Partially Implemented)
- Login and routing
- User-specific favorite tracking (not global favorites)
- In-depth stock page route with enhanced info (analyst target, 52-week range)

## Tech Stack
- Backend: Flask, Flask-SQLAlchemy, Flask-Login
- Frontend: Server-rendered HTML templates + vanilla JavaScript + CSS
- Database: SQLite (configurable)
- Testing: Pytest
- Market Data: Alpha Vantage (`OVERVIEW` + `INCOME_STATEMENT`)

## Project Structure

```
StockScope/
	app/
		__init__.py
		config.py
		metrics.py
		models.py
		routes.py
		stock_service.py
		static/
			app.js
			styles.css
		templates/
			base.html
			index.html
			login.html
			register.html
			favorites.html
			stock_detail.html
	docs/
		PROJECT_OUTLINE.md
		PAPER_PROTOTYPE.md
		DEMO_SCRIPT.md
	tests/
		conftest.py
		test_metrics.py
		test_routes.py
	run.py
	requirements.txt
	.env.example
```

## Getting Started

### 1. Create and activate virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` values into your shell or an `.env` file.

Required values:
- `SECRET_KEY`
- `ALPHAVANTAGE_API_KEY`

Notes:
- The default `demo` key is very limited and may not return all symbols.
- Alpha Vantage free tier has strict daily limits.

### 4. Run the app

```powershell
python run.py
```

Open `http://127.0.0.1:5000`.

## API Endpoints

- `POST /api/stock`
	- Body: `{ "ticker": "IBM" }`
	- Returns computed metrics and enrichment fields
- `POST /api/favorites` (auth required)
- `GET /api/favorites?industry=tech` (auth required)
- `DELETE /api/favorites/<ticker>` (auth required)

## Alpha Vantage Data Mapping (IBM Example)

StockScope uses two Alpha Vantage calls for each ticker:

1. Overview call (P/E, 52-week range, industry, target price):

```text
https://www.alphavantage.co/query?function=OVERVIEW&symbol=IBM&apikey=YOUR_KEY
```

2. Income statement call (annual net income history):

```text
https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol=IBM&apikey=YOUR_KEY
```

Then it computes the assignment metrics:

- `growth_rate = ((ending_net_income - beginning_net_income) / beginning_net_income) * 100`
- `pe_ratio = OVERVIEW.PERatio`
- `growth_over_pe = growth_rate / pe_ratio`

Python-style logic used by this project:

```python
reports = sorted(annual_reports, key=lambda r: r["fiscalDateEnding"], reverse=True)
ending = float(reports[0]["netIncome"])
beginning = float(reports[1]["netIncome"])
growth_rate = ((ending - beginning) / beginning) * 100
pe_ratio = float(overview["PERatio"])
growth_over_pe = growth_rate / pe_ratio
```

Notes:
- The free `demo` key can return valid `OVERVIEW` data for IBM but may fail for `INCOME_STATEMENT` on IBM.
- Use your own API key in `.env` (`ALPHAVANTAGE_API_KEY`) for reliable results.

## Testing

Run all tests:

```powershell
pytest -q
```

Current unit tests cover:
- Growth and ratio math
- Stock API success and error paths
- User-scoped favorites
- Favorites filtering by industry

## Submission Deliverables Mapping

- Production-ready README: this file
- Unit tests: `tests/`
- Demo screenshare script: `docs/DEMO_SCRIPT.md`
- Project outline/work tickets: `docs/PROJECT_OUTLINE.md`
- Paper prototype: `docs/PAPER_PROTOTYPE.md`

## Future Improvements

- Add external provider fallback to reduce rate-limit failures
- Add peer-comparison data and earnings calendar
- Add role-based admin analytics dashboard
- Add CI pipeline and deployment config (Docker + cloud hosting)
