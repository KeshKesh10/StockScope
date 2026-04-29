# Project Outline and Work Items

## Scope
Build a stock analysis web app that supports ticker search, valuation metrics, user favorites, and user-specific saved portfolios.

## Tickets
1. Setup Flask app skeleton, dependencies, config, and database wiring.
2. Build Alpha Vantage integration for OVERVIEW + INCOME_STATEMENT.
3. Implement growth-rate formula from net income over last two years.
4. Implement P/E and growth-over-P/E (PEG-style check) calculations.
5. Add ticker-not-found popup error UX.
6. Implement user auth (register/login/logout).
7. Persist favorites by current user with industry metadata.
8. Build favorites page with metrics and industry filtering.
9. Add in-depth stock route with enhanced metrics (target price, 52-week range).
10. Write unit tests for math and API routes.
11. Write deployment-ready README and demo script.

## Suggested Team Split
- Member A: Backend APIs, metrics calculation, provider integration.
- Member B: Frontend UX, popup/error handling, in-depth page.
- Member C: Auth, database models, favorites and filtering.
- Member D: Tests, QA, README, demo and presentation assets.
