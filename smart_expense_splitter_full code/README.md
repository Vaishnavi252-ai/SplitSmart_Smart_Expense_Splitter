# SplitSmart

SplitSmart is a customer-facing smart expense splitter built for the Unico Connect assessment brief. It supports shared groups, validated expense entry, balance calculation, settle-up suggestions, expense history filters, natural-language expense parsing, and bill-text parsing with assignable line items.

## Stack

- Backend: `Flask`
- Validation: `Pydantic`
- Database: `SQLite`
- Frontend: responsive HTML/CSS/JavaScript served by Flask
- AI: `OpenAI Responses API` with structured parsing

## What Works

- Group creation with seeded demo users
- User switcher with group filtering
- Manual expense entry with server-side validation
- Split modes: equal all, equal subset, custom amounts, weighted shares
- Group balances and minimum-transfer settle-up view
- Expense history with payer, date-range, and text search filters
- Seeded SQLite data: 3 groups, 8 users, 24 expenses
- Natural-language expense parsing into a reviewable draft
- Bill-text parsing into line items and assignable custom splits
- Graceful AI fallback when the API key is missing or the parse is low confidence
- Unit and API smoke tests

## Not Implemented Yet

- Image OCR for bill photos
- Live multi-user sync across browser sessions
- Multi-currency conversion
- CSV/PDF export
- Recurring expenses
- Activity feed

## Run Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Optional: enable AI features with your own OpenAI key:

```bash
$env:OPENAI_API_KEY="your_key_here"
```

3. Start the app:

```bash
python app.py
```

4. Open `http://127.0.0.1:5000`

The app auto-creates `data/expense_splitter.db` on first run and seeds it when the database is empty.

## Test

```bash
python -m unittest discover -s tests -v
```

## API Overview

- `GET /api/users/`
- `POST /api/users/`
- `GET /api/groups/`
- `POST /api/groups/`
- `GET /api/groups/<group_id>`
- `GET /api/groups/<group_id>/expenses`
- `POST /api/groups/<group_id>/expenses`
- `GET /api/groups/<group_id>/balances`
- `GET /api/groups/<group_id>/settlements`
- `POST /api/groups/<group_id>/ai/parse-expense`
- `POST /api/groups/<group_id>/ai/parse-bill`

## Notes

- Money is stored as integer paise everywhere. No floating-point money is persisted.
- AI output is never saved directly. It always becomes a draft that the user reviews before confirming.
- This build intentionally stays single-command and interview-friendly: no separate frontend build step, no external database setup, and no auth flow.
