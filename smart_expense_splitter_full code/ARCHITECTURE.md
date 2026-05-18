# Architecture

## Why Python + Flask

I chose Python over Node for this assessment because the app has three pressure points that benefit from Python’s ergonomics:

- Fast iteration on data-heavy logic: the settle-up algorithm, split validation, and seeded ledger setup are concise and easy to test in Python.
- Structured validation: `Pydantic` gives strict request validation without adding a heavier framework dependency.
- AI integration speed: the OpenAI Python SDK’s structured parsing flow fits the natural-language and bill-parsing features well.

I used `Flask` instead of a larger backend framework to keep the app single-command, lightweight, and easy to explain in a 5-hour build. The UI is served directly from Flask so the evaluator can run everything without a frontend build pipeline.

## Money Handling

All money is stored as integer paise (`amount_paise`). The UI accepts rupee inputs for usability, then converts them to paise before sending them to the API. The backend validates integer totals and never stores floats.

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

### AI
- `POST /api/groups/<group_id>/ai/parse-expense`
- `POST /api/groups/<group_id>/ai/parse-bill`

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
- `static/app.js`: state management, rendering, fetch calls, manual/AI flows
- `static/styles.css`: mobile-first styling

## Split Validation Rules

The backend validates every expense request:

- amount must be positive
- payer must belong to the group
- currency must match the group currency in this version
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

### Bill-text parsing

The bill parser extracts:
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
- The UI never auto-saves AI results

## Seed Data

The database seeds:
- 8 users
- 3 groups
- 24 realistic expenses

The sample data includes equal, subset, custom, and weighted splits, plus bill-style seeded expenses with line items for demoing history and parsing flows.

## What I’d Improve With More Time

- real auth and invitation flows
- image upload + OCR bill parsing
- websocket or SSE live updates across multiple browser sessions
- exports, recurring expenses, and activity feed
- more frontend inline validation and optimistic updates
- stronger automated API coverage and UI tests
