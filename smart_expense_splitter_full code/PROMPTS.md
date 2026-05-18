# AI Prompt Log

## Production Prompts In The App

### Natural-language expense parser

This is the instruction block used in `services/ai_service.py`:

```text
You extract shared expense drafts for a Splitwise-style app.

Today's date is {today}.
The current user is {current_user_name} (user_id={current_user_id}).
Allowed group members are listed with exact user_id values.

Rules:
- Return a draft that matches the schema exactly.
- Use amount_paise, never floating-point rupees.
- Resolve relative dates like "last night" against today's date.
- Only use payer_user_id or participant user_id values from the allowed members.
- If a member name is ambiguous or missing, keep user_id null and add a warning.
- If the request implies reduced or uneven shares, use split_mode "custom" and fill amount_paise values.
- If the request implies proportional shares, use split_mode "weights" and fill weight values.
- If the request clearly means everyone in the group, use split_mode "equal_all" and leave participants empty.
- Never invent amounts, members, or dates. Lower confidence and add warnings instead.
```

Why this prompt:
- It constrains the model to exact group members.
- It forces integer money handling.
- It encodes fallback behavior instead of trusting hallucinated fields.

### Bill-text parser

This is the instruction block used in `services/ai_service.py`:

```text
You extract structured restaurant or receipt bill data.

Today's date is {today}.

Rules:
- Return the schema exactly.
- All money must be in amount_paise or total_paise.
- Extract every usable line item when present.
- If taxes, tips, or service charges appear, include them as line items too.
- Do not invent missing items. If you cannot confidently recover line items, lower confidence and add warnings.
- Description should be a clean human-readable label such as "Restaurant bill at X".
```

Why this prompt:
- It keeps the parser useful for item assignment.
- It explicitly avoids fake line items.
- It makes taxes/service charges visible instead of losing them outside the split.

## Coding Tool Usage Log

### Prompt 1

Asked:
- Build an assessment-ready Smart Expense Splitter from the provided Unico Connect brief inside the current repo using Python, with seeded data, REST APIs, a responsive UI, AI draft parsing, tests, and submission docs.

Got:
- A full Flask + SQLite rebuild replacing the initial prototype.

### Prompt 2

Asked:
- Tighten the UI so AI-generated custom splits do not accidentally keep unrelated members selected by default.

Got:
- Participant rendering logic was adjusted to treat drafted participants as explicit selections.

### Prompt 3

Asked:
- Add a small verification layer so the settle-up logic and main validation flows are exercised locally before handing off.

Got:
- `unittest` coverage for seeded API flows, invalid custom splits, AI fallback, weighted remainder handling, and greedy settlements.
