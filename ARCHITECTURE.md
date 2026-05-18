# Architecture

## Why Python + Flask

I chose Python over Node for this assessment because the app has three pressure points that benefit from Python’s ergonomics:

- Fast iteration on data-heavy logic: the settle-up algorithm, split validation, and seeded ledger setup are concise and easy to test in Python.
- Structured validation: `Pydantic` gives strict request validation without adding a heavier framework dependency.
- AI integration speed: the OpenAI Python SDK’s structured parsing flow fits the natural-language and bill-parsing features well.

I used `Flask` instead of a larger backend framework to keep the app single-command, lightweight, and easy to explain in a 5-hour build. The UI is served directly from Flask so the evaluator can run everything without a frontend build pipeline.

## Money Handling

All money is stored as integer minor units. For an INR group the canonical ledger amount is `amount_paise`; the frontend parses decimal-looking user input into integer minor units before sending it to the API, and the backend validates that split totals match exactly. No persisted amount uses floating point.

Multi-currency expenses are converted into the group's base currency before they enter the ledger. The original currency and original minor-unit amount are retained on the expense as `original_currency_code` and `original_amount_minor`, and the integer conversion rate is stored as `exchange_rate_ppm` (parts per million). This keeps balances deterministic and auditable. The current build uses a small static rate table suitable for the assessment; production should replace it with a dated FX-rate provider and store the provider/rate timestamp.

## Database Schema

### `users`
- `id`
- `name`
- `email`
- `created_at`

### `groups`
- `id`
- `name`
- `description`
- `currency_code`
- `created_by_user_id`
- `created_at`
- `updated_at`

### `group_members`
- `group_id`
- `user_id`
- `role`
- `joined_at`

### `expenses`
- `id`
- `group_id`
- `payer_user_id`
- `created_by_user_id`
- `description`
- `amount_paise`
- `currency_code`
- `original_amount_minor`
- `original_currency_code`
- `exchange_rate_ppm`
- `expense_date`
- `split_mode`
- `source_type`
- `notes`
- `ai_confidence`
- `created_at`

### `expense_shares`
- `id`
- `expense_id`
- `user_id`
- `amount_paise`
- `weight`
- `share_order`
- `created_at`

### `expense_items`
- `id`
- `expense_id`
- `item_name`
- `amount_paise`
- `assigned_user_ids_json`
- `created_at`

### `recurring_expenses`
- monthly templates for rent/subscriptions
- stores payer, creator, split mode, participants JSON, next run date, and active flag

### `activity_events`
- group-scoped audit trail used by the activity feed and polling version endpoint

## API Endpoints

### Users
- `GET /api/users/`
- `POST /api/users/`

### Groups
- `GET /api/groups/`
- `POST /api/groups/`
- `GET /api/groups/<group_id>`

### Expenses
- `GET /api/groups/<group_id>/expenses`
- `POST /api/groups/<group_id>/expenses`
- `GET /api/groups/<group_id>/balances`
- `GET /api/groups/<group_id>/settlements`
- `GET /api/groups/<group_id>/activity`
- `GET /api/groups/<group_id>/version`
- `GET /api/groups/<group_id>/export.csv`
- `GET /api/groups/<group_id>/export.pdf`
- `GET /api/groups/<group_id>/recurring`
- `POST /api/groups/<group_id>/recurring`
- `POST /api/groups/<group_id>/recurring/run-due`
- `GET /api/groups/<group_id>/currencies`

### AI
- `POST /api/groups/<group_id>/ai/parse-expense`
- `POST /api/groups/<group_id>/ai/parse-bill`
- `POST /api/groups/<group_id>/ai/parse-bill-image`

## Component Structure

### Backend
- `app.py`: app factory, config, blueprint registration, error handling
- `db.py`: SQLite connection management, schema creation, seed trigger
- `schemas.py`: request validation models
- `services/ledger_service.py`: split computation, balance calculation, settle-up algorithm
- `services/expense_service.py`: CRUD and query orchestration
- `services/ai_service.py`: structured AI parsing and fallback behavior
- `services/seed_service.py`: inserts sample users, groups, and expenses
- `routes/`: REST and page routes

### Frontend
- `templates/index.html`: shell layout
- `static/app.js`: React app, state management, polling, exports, manual/AI/recurring flows
- `static/styles.css`: premium mobile-first responsive styling with dark mode

## Split Validation Rules

The backend validates every expense request:

- amount must be positive
- payer must belong to the group
- converted ledger currency must match the group currency
- participants must belong to the group
- custom splits must sum exactly to the total
- weighted splits must use positive integer weights
- bill-based custom splits must match assigned line-item totals exactly

## Settle-Up Algorithm

The settle-up flow is:

1. Compute each member’s net balance:
   payer gets credited with the full expense amount; each participant is debited by their share.
2. Split the group into creditors and debtors.
3. Sort both lists by absolute amount descending.
4. Greedily match the largest debtor against the largest creditor until one side is exhausted.

This greedy debt-graph reduction is deterministic, easy to explain in interview conditions, and produces a minimum-number-of-transfers result for this netting model.

## AI Features

### Natural-language expense entry

The text parser sends:
- today’s date
- current user identity
- the allowed group members
- explicit rules for structured output

The model returns a typed draft with:
- payer
- description
- amount in paise
- date
- split mode
- participant details
- confidence
- warnings

If confidence is low, members are unresolved, or critical fields are missing, the endpoint returns a manual fallback response instead of silently accepting bad data.

### Bill-text and bill-photo parsing

The bill parser extracts from pasted text or an uploaded image:
- merchant/description
- bill date
- total
- line items in paise
- warnings/confidence

The frontend then asks the user to assign each parsed line item to members. That assignment becomes a custom split. The backend re-validates that assigned line-item totals exactly match the final custom shares.

## Failure Handling

- Missing or invalid API input returns `400`
- Missing resources return `404`
- AI unavailable or low-confidence parse returns `422` with a clear fallback message
- Empty states are rendered for no groups, no expenses, and fully settled groups
- Polling failures are silent so a temporary network blip does not interrupt the active screen
- Split mismatches are blocked both in React preview and again by backend validation
- The UI never auto-saves AI results

## Seed Data

The database seeds:
- 8 users
- 3 groups
- 24 realistic expenses

The sample data includes equal, subset, custom, and weighted splits, plus bill-style seeded expenses with line items for demoing history and parsing flows.

## What I’d Improve With More Time

- real auth and invitation flows
- real WebSocket/SSE transport instead of lightweight polling
- production exchange-rate provider with dated rates
- more frontend inline validation and optimistic updates
- stronger automated API coverage and UI tests
