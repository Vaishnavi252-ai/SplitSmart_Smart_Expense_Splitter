import json

from services.ledger_service import build_shares, compute_item_assignment_totals


USERS = [
    {"name": "Aisha Mehta", "email": "aisha@example.com"},
    {"name": "Aman Shah", "email": "aman@example.com"},
    {"name": "Priya Nair", "email": "priya@example.com"},
    {"name": "Rohan Kulkarni", "email": "rohan@example.com"},
    {"name": "Neha Batra", "email": "neha@example.com"},
    {"name": "Kabir Arora", "email": "kabir@example.com"},
    {"name": "Sara Khan", "email": "sara@example.com"},
    {"name": "Vikram Joshi", "email": "vikram@example.com"},
]


GROUPS = [
    {
        "name": "Goa Escape",
        "description": "Beach trip planning, villas, rides, and too much seafood.",
        "creator": "Aisha Mehta",
        "members": ["Aisha Mehta", "Aman Shah", "Priya Nair", "Rohan Kulkarni"],
        "expenses": [
            {
                "description": "Flight block booking",
                "payer": "Aisha Mehta",
                "amount_paise": 180000,
                "expense_date": "2026-04-10",
                "split_mode": "equal_all",
                "source_type": "manual",
            },
            {
                "description": "Villa advance",
                "payer": "Rohan Kulkarni",
                "amount_paise": 320000,
                "expense_date": "2026-04-11",
                "split_mode": "weights",
                "weights": {
                    "Aisha Mehta": 2,
                    "Aman Shah": 1,
                    "Priya Nair": 1,
                    "Rohan Kulkarni": 2,
                },
                "source_type": "manual",
            },
            {
                "description": "Scooty rental",
                "payer": "Aman Shah",
                "amount_paise": 54000,
                "expense_date": "2026-04-12",
                "split_mode": "equal_subset",
                "participants": ["Aman Shah", "Priya Nair", "Rohan Kulkarni"],
                "source_type": "manual",
            },
            {
                "description": "Beach shack dinner",
                "payer": "Priya Nair",
                "amount_paise": 68500,
                "expense_date": "2026-04-12",
                "split_mode": "custom",
                "source_type": "ai_bill_text",
                "line_items": [
                    {"item_name": "Seafood platter", "amount_paise": 24000, "assigned_user_ids": ["Aisha Mehta", "Priya Nair", "Rohan Kulkarni"]},
                    {"item_name": "Mocktails", "amount_paise": 12600, "assigned_user_ids": ["Aisha Mehta", "Priya Nair", "Rohan Kulkarni"]},
                    {"item_name": "Aman's noodles", "amount_paise": 9800, "assigned_user_ids": ["Aman Shah"]},
                    {"item_name": "Garlic naan basket", "amount_paise": 6100, "assigned_user_ids": ["Aisha Mehta", "Aman Shah", "Priya Nair", "Rohan Kulkarni"]},
                    {"item_name": "Taxes and service charge", "amount_paise": 16000, "assigned_user_ids": ["Aisha Mehta", "Aman Shah", "Priya Nair", "Rohan Kulkarni"]},
                ],
            },
            {
                "description": "Breakfast groceries",
                "payer": "Priya Nair",
                "amount_paise": 18900,
                "expense_date": "2026-04-13",
                "split_mode": "equal_all",
                "source_type": "manual",
            },
            {
                "description": "Ferry tickets",
                "payer": "Rohan Kulkarni",
                "amount_paise": 9600,
                "expense_date": "2026-04-13",
                "split_mode": "equal_subset",
                "participants": ["Aisha Mehta", "Priya Nair"],
                "source_type": "manual",
            },
            {
                "description": "Water sports combo",
                "payer": "Rohan Kulkarni",
                "amount_paise": 42000,
                "expense_date": "2026-04-14",
                "split_mode": "custom",
                "amounts": {
                    "Aisha Mehta": 11000,
                    "Aman Shah": 9000,
                    "Priya Nair": 9000,
                    "Rohan Kulkarni": 13000,
                },
                "source_type": "manual",
            },
            {
                "description": "Late night chai",
                "payer": "Aman Shah",
                "amount_paise": 1200,
                "expense_date": "2026-04-14",
                "split_mode": "equal_subset",
                "participants": ["Aman Shah", "Rohan Kulkarni"],
                "source_type": "manual",
            },
        ],
    },
    {
        "name": "Maple Flat",
        "description": "Monthly flat expenses for rent, utilities, and house essentials.",
        "creator": "Neha Batra",
        "members": ["Aisha Mehta", "Neha Batra", "Kabir Arora", "Vikram Joshi"],
        "expenses": [
            {
                "description": "May rent",
                "payer": "Vikram Joshi",
                "amount_paise": 720000,
                "expense_date": "2026-05-01",
                "split_mode": "weights",
                "weights": {
                    "Aisha Mehta": 2,
                    "Neha Batra": 1,
                    "Kabir Arora": 1,
                    "Vikram Joshi": 2,
                },
                "source_type": "manual",
            },
            {
                "description": "Broadband bill",
                "payer": "Kabir Arora",
                "amount_paise": 299900,
                "expense_date": "2026-05-02",
                "split_mode": "equal_all",
                "source_type": "manual",
            },
            {
                "description": "Electricity bill",
                "payer": "Neha Batra",
                "amount_paise": 64500,
                "expense_date": "2026-05-03",
                "split_mode": "equal_all",
                "source_type": "manual",
            },
            {
                "description": "Weekly groceries",
                "payer": "Aisha Mehta",
                "amount_paise": 23800,
                "expense_date": "2026-05-05",
                "split_mode": "custom",
                "amounts": {
                    "Aisha Mehta": 8200,
                    "Neha Batra": 6200,
                    "Kabir Arora": 4400,
                    "Vikram Joshi": 5000,
                },
                "source_type": "manual",
            },
            {
                "description": "Cleaning help",
                "payer": "Vikram Joshi",
                "amount_paise": 40000,
                "expense_date": "2026-05-06",
                "split_mode": "equal_all",
                "source_type": "manual",
            },
            {
                "description": "Water canisters",
                "payer": "Kabir Arora",
                "amount_paise": 1600,
                "expense_date": "2026-05-08",
                "split_mode": "equal_subset",
                "participants": ["Aisha Mehta", "Kabir Arora", "Vikram Joshi"],
                "source_type": "manual",
            },
            {
                "description": "Gas cylinder refill",
                "payer": "Neha Batra",
                "amount_paise": 1850,
                "expense_date": "2026-05-10",
                "split_mode": "equal_all",
                "source_type": "manual",
            },
            {
                "description": "Streaming bundle",
                "payer": "Aisha Mehta",
                "amount_paise": 89900,
                "expense_date": "2026-05-11",
                "split_mode": "equal_subset",
                "participants": ["Aisha Mehta", "Neha Batra", "Vikram Joshi"],
                "source_type": "manual",
            },
        ],
    },
    {
        "name": "Friday Food Club",
        "description": "Rotating weekend dinners, movies, and impulse dessert runs.",
        "creator": "Sara Khan",
        "members": ["Aman Shah", "Priya Nair", "Neha Batra", "Sara Khan", "Vikram Joshi"],
        "expenses": [
            {
                "description": "Sushi dinner",
                "payer": "Sara Khan",
                "amount_paise": 41200,
                "expense_date": "2026-05-02",
                "split_mode": "custom",
                "source_type": "ai_bill_text",
                "line_items": [
                    {"item_name": "Dragon rolls", "amount_paise": 16200, "assigned_user_ids": ["Aman Shah", "Priya Nair", "Sara Khan", "Vikram Joshi"]},
                    {"item_name": "Miso ramen", "amount_paise": 9800, "assigned_user_ids": ["Aman Shah", "Neha Batra"]},
                    {"item_name": "Sparkling water", "amount_paise": 3200, "assigned_user_ids": ["Aman Shah", "Priya Nair", "Neha Batra", "Sara Khan", "Vikram Joshi"]},
                    {"item_name": "Taxes and service charge", "amount_paise": 12000, "assigned_user_ids": ["Aman Shah", "Priya Nair", "Neha Batra", "Sara Khan", "Vikram Joshi"]},
                ],
            },
            {
                "description": "Bowling night",
                "payer": "Vikram Joshi",
                "amount_paise": 36000,
                "expense_date": "2026-05-03",
                "split_mode": "equal_subset",
                "participants": ["Aman Shah", "Priya Nair", "Sara Khan", "Vikram Joshi"],
                "source_type": "manual",
            },
            {
                "description": "Pizza order",
                "payer": "Aman Shah",
                "amount_paise": 22500,
                "expense_date": "2026-05-04",
                "split_mode": "custom",
                "amounts": {
                    "Aman Shah": 7000,
                    "Priya Nair": 5500,
                    "Neha Batra": 4000,
                    "Sara Khan": 3000,
                    "Vikram Joshi": 3000,
                },
                "source_type": "manual",
            },
            {
                "description": "Coffee round",
                "payer": "Priya Nair",
                "amount_paise": 11800,
                "expense_date": "2026-05-05",
                "split_mode": "equal_subset",
                "participants": ["Priya Nair", "Neha Batra", "Sara Khan"],
                "source_type": "manual",
            },
            {
                "description": "Movie tickets",
                "payer": "Neha Batra",
                "amount_paise": 45000,
                "expense_date": "2026-05-09",
                "split_mode": "equal_subset",
                "participants": ["Aman Shah", "Priya Nair", "Neha Batra", "Vikram Joshi"],
                "source_type": "manual",
            },
            {
                "description": "Dessert crawl",
                "payer": "Sara Khan",
                "amount_paise": 9800,
                "expense_date": "2026-05-10",
                "split_mode": "equal_subset",
                "participants": ["Aman Shah", "Sara Khan"],
                "source_type": "manual",
            },
            {
                "description": "Brunch buffet",
                "payer": "Aman Shah",
                "amount_paise": 50600,
                "expense_date": "2026-05-11",
                "split_mode": "equal_all",
                "source_type": "manual",
            },
            {
                "description": "Cab home",
                "payer": "Vikram Joshi",
                "amount_paise": 17400,
                "expense_date": "2026-05-11",
                "split_mode": "equal_subset",
                "participants": ["Priya Nair", "Sara Khan", "Vikram Joshi"],
                "source_type": "manual",
            },
        ],
    },
]


def seed_database(db):
    user_ids = {}

    for user in USERS:
        cursor = db.execute(
            """
            INSERT INTO users (name, email)
            VALUES (?, ?)
            """,
            (user["name"], user["email"]),
        )
        user_ids[user["name"]] = cursor.lastrowid

    for group in GROUPS:
        creator_id = user_ids[group["creator"]]
        cursor = db.execute(
            """
            INSERT INTO groups (name, description, currency_code, created_by_user_id)
            VALUES (?, ?, 'INR', ?)
            """,
            (group["name"], group["description"], creator_id),
        )
        group_id = cursor.lastrowid
        group_member_ids = [user_ids[name] for name in group["members"]]

        for member_name in group["members"]:
            member_id = user_ids[member_name]
            db.execute(
                """
                INSERT INTO group_members (group_id, user_id, role)
                VALUES (?, ?, ?)
                """,
                (group_id, member_id, "owner" if member_id == creator_id else "member"),
            )

        for expense in group["expenses"]:
            line_items = []
            amounts = expense.get("amounts", {})
            if "line_items" in expense:
                line_items = [
                    {
                        "item_name": line_item["item_name"],
                        "amount_paise": line_item["amount_paise"],
                        "assigned_user_ids": [user_ids[name] for name in line_item["assigned_user_ids"]],
                    }
                    for line_item in expense["line_items"]
                ]
                if expense["split_mode"] == "custom":
                    item_totals = compute_item_assignment_totals(line_items)
                    amounts = {
                        member_name: item_totals.get(user_ids[member_name], 0)
                        for member_name in group["members"]
                        if item_totals.get(user_ids[member_name], 0) > 0
                    }

            participant_records = _build_participants(expense, user_ids, amounts)
            shares = build_shares(expense["amount_paise"], expense["split_mode"], participant_records, group_member_ids)

            cursor = db.execute(
                """
                INSERT INTO expenses (
                    group_id,
                    payer_user_id,
                    created_by_user_id,
                    description,
                    amount_paise,
                    currency_code,
                    expense_date,
                    split_mode,
                    source_type,
                    notes,
                    ai_confidence
                )
                VALUES (?, ?, ?, ?, ?, 'INR', ?, ?, ?, ?, ?)
                """,
                (
                    group_id,
                    user_ids[expense["payer"]],
                    creator_id,
                    expense["description"],
                    expense["amount_paise"],
                    expense["expense_date"],
                    expense["split_mode"],
                    expense.get("source_type", "manual"),
                    expense.get("notes"),
                    expense.get("ai_confidence"),
                ),
            )
            expense_id = cursor.lastrowid

            for share in shares:
                db.execute(
                    """
                    INSERT INTO expense_shares (expense_id, user_id, amount_paise, weight, share_order)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        expense_id,
                        share["user_id"],
                        share["amount_paise"],
                        share.get("weight"),
                        share.get("order", 0),
                    ),
                )

            for line_item in line_items:
                db.execute(
                    """
                    INSERT INTO expense_items (expense_id, item_name, amount_paise, assigned_user_ids_json)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        expense_id,
                        line_item["item_name"],
                        line_item["amount_paise"],
                        json.dumps(line_item["assigned_user_ids"]),
                    ),
                )

    db.commit()


def _build_participants(expense, user_ids, amounts):
    split_mode = expense["split_mode"]

    if split_mode == "equal_all":
        return []
    if split_mode == "equal_subset":
        return [{"user_id": user_ids[name], "selected": True} for name in expense["participants"]]
    if split_mode == "custom":
        return [
            {"user_id": user_ids[name], "selected": True, "amount_paise": amount}
            for name, amount in amounts.items()
        ]
    if split_mode == "weights":
        return [
            {"user_id": user_ids[name], "selected": True, "weight": weight}
            for name, weight in expense["weights"].items()
        ]
    raise ValueError(f"Unsupported split mode: {split_mode}")
