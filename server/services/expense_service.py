import json
import sqlite3
from datetime import date

from db import get_db
from errors import ApiError
from services.ledger_service import (
    build_shares,
    build_split_summary,
    calculate_balances,
    calculate_settlements,
    compute_item_assignment_totals,
    format_paise,
)


SOURCE_LABELS = {
    "manual": "Manual",
    "ai_natural_language": "AI text",
    "ai_bill_text": "Bill parser",
}


def list_users():
    db = get_db()
    rows = db.execute(
        """
        SELECT id, name, email, created_at
        FROM users
        ORDER BY name COLLATE NOCASE
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_user(user_id: int):
    db = get_db()
    row = db.execute(
        """
        SELECT id, name, email, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()
    if row is None:
        raise ApiError("User not found.", 404)
    return dict(row)


def create_user(payload):
    db = get_db()
    try:
        cursor = db.execute(
            """
            INSERT INTO users (name, email)
            VALUES (?, ?)
            """,
            (payload.name, payload.email),
        )
        db.commit()
    except sqlite3.IntegrityError as error:
        if "users.email" in str(error):
            raise ApiError("A user with this email already exists.")
        raise
    return get_user(cursor.lastrowid)


def list_groups(current_user_id: int | None = None):
    db = get_db()
    params = []
    filters = []

    if current_user_id is not None:
        filters.append(
            """
            EXISTS (
                SELECT 1
                FROM group_members viewer
                WHERE viewer.group_id = g.id AND viewer.user_id = ?
            )
            """
        )
        params.append(current_user_id)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    rows = db.execute(
        f"""
        SELECT
            g.id,
            g.name,
            g.description,
            g.currency_code,
            g.created_by_user_id,
            g.created_at,
            g.updated_at,
            creator.name AS created_by_name,
            COUNT(DISTINCT gm.user_id) AS member_count,
            COUNT(DISTINCT e.id) AS expense_count,
            COALESCE(MAX(e.expense_date), substr(g.created_at, 1, 10)) AS last_activity
        FROM groups g
        JOIN users creator ON creator.id = g.created_by_user_id
        JOIN group_members gm ON gm.group_id = g.id
        LEFT JOIN expenses e ON e.group_id = g.id
        {where_clause}
        GROUP BY g.id, creator.name
        ORDER BY last_activity DESC, g.updated_at DESC
        """,
        params,
    ).fetchall()

    groups = [dict(row) for row in rows]
    if not groups:
        return []

    group_ids = [group["id"] for group in groups]
    placeholders = ",".join("?" for _ in group_ids)
    member_rows = get_db().execute(
        f"""
        SELECT gm.group_id, u.id, u.name
        FROM group_members gm
        JOIN users u ON u.id = gm.user_id
        WHERE gm.group_id IN ({placeholders})
        ORDER BY u.name COLLATE NOCASE
        """,
        group_ids,
    ).fetchall()

    members_by_group = {}
    for row in member_rows:
        members_by_group.setdefault(row["group_id"], []).append({"id": row["id"], "name": row["name"]})

    for group in groups:
        group["members_preview"] = members_by_group.get(group["id"], [])
        group["last_activity_label"] = group["last_activity"]
        if current_user_id is not None:
            current_balance = next(
                (item["balance_paise"] for item in get_group_balances(group["id"]) if item["user_id"] == current_user_id),
                0,
            )
            group["current_user_balance_paise"] = current_balance
            group["current_user_balance_display"] = format_paise(abs(current_balance))

    return groups


def get_group(group_id: int):
    db = get_db()
    row = db.execute(
        """
        SELECT
            g.id,
            g.name,
            g.description,
            g.currency_code,
            g.created_by_user_id,
            g.created_at,
            g.updated_at,
            creator.name AS created_by_name
        FROM groups g
        JOIN users creator ON creator.id = g.created_by_user_id
        WHERE g.id = ?
        """,
        (group_id,),
    ).fetchone()

    if row is None:
        raise ApiError("Group not found.", 404)

    group = dict(row)
    group["members"] = get_group_members(group_id)
    group["expense_count"] = db.execute(
        "SELECT COUNT(*) AS count FROM expenses WHERE group_id = ?",
        (group_id,),
    ).fetchone()["count"]
    group["last_expense_date"] = db.execute(
        "SELECT MAX(expense_date) AS last_expense_date FROM expenses WHERE group_id = ?",
        (group_id,),
    ).fetchone()["last_expense_date"]
    return group


def get_group_members(group_id: int):
    _ensure_group_exists(group_id)
    rows = get_db().execute(
        """
        SELECT
            u.id,
            u.name,
            u.email,
            gm.role,
            gm.joined_at
        FROM group_members gm
        JOIN users u ON u.id = gm.user_id
        WHERE gm.group_id = ?
        ORDER BY CASE gm.role WHEN 'owner' THEN 0 ELSE 1 END, u.name COLLATE NOCASE
        """,
        (group_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def create_group(payload):
    db = get_db()
    _ensure_users_exist(payload.member_ids)

    try:
        cursor = db.execute(
            """
            INSERT INTO groups (name, description, currency_code, created_by_user_id)
            VALUES (?, ?, ?, ?)
            """,
            (
                payload.name,
                payload.description,
                payload.currency_code,
                payload.created_by_user_id,
            ),
        )

        group_id = cursor.lastrowid
        for member_id in payload.member_ids:
            db.execute(
                """
                INSERT INTO group_members (group_id, user_id, role)
                VALUES (?, ?, ?)
                """,
                (group_id, member_id, "owner" if member_id == payload.created_by_user_id else "member"),
            )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return get_group(group_id)


def create_expense(group_id: int, payload):
    group = get_group(group_id)
    group_member_ids = [member["id"] for member in group["members"]]
    group_member_id_set = set(group_member_ids)

    if payload.currency_code != group["currency_code"]:
        raise ApiError("This build supports a single currency per group. Use the group's currency code.")

    if payload.payer_user_id not in group_member_id_set:
        raise ApiError("The payer must belong to the group.")
    if payload.created_by_user_id not in group_member_id_set:
        raise ApiError("The creator must belong to the group.")

    participant_records = [participant.model_dump() for participant in payload.participants]
    shares = build_shares(payload.amount_paise, payload.split_mode, participant_records, group_member_ids)

    line_items = [item.model_dump() for item in payload.line_items]
    for line_item in line_items:
        if not set(line_item["assigned_user_ids"]).issubset(group_member_id_set):
            raise ApiError("Line item assignments can only reference group members.")

    if line_items:
        if payload.split_mode != "custom":
            raise ApiError("Line-item assignment is only supported for custom splits.")
        line_item_total = sum(item["amount_paise"] for item in line_items)
        if line_item_total != payload.amount_paise:
            raise ApiError("Parsed line items must sum exactly to the expense total.")

        assignment_totals = compute_item_assignment_totals(line_items)
        share_totals = {}
        for share in shares:
            share_totals[share["user_id"]] = share_totals.get(share["user_id"], 0) + share["amount_paise"]

        if any(assignment_totals.get(user_id, 0) != share_totals.get(user_id, 0) for user_id in group_member_ids):
            raise ApiError("Custom share amounts must match the assigned bill items exactly.")

    db = get_db()
    try:
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                group_id,
                payload.payer_user_id,
                payload.created_by_user_id,
                payload.description,
                payload.amount_paise,
                payload.currency_code,
                payload.expense_date.isoformat(),
                payload.split_mode,
                payload.source_type,
                payload.notes,
                payload.ai_confidence,
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

        db.execute(
            """
            UPDATE groups
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (group_id,),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return get_expense(expense_id)


def list_group_expenses(group_id: int, payer_user_id=None, start_date=None, end_date=None, search=None):
    _ensure_group_exists(group_id)
    expense_rows = _fetch_expense_rows(
        group_id,
        payer_user_id=payer_user_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    return _hydrate_expenses(expense_rows)


def get_expense(expense_id: int):
    rows = get_db().execute(
        """
        SELECT
            e.id,
            e.group_id,
            e.payer_user_id,
            e.created_by_user_id,
            e.description,
            e.amount_paise,
            e.currency_code,
            e.expense_date,
            e.split_mode,
            e.source_type,
            e.notes,
            e.ai_confidence,
            e.created_at,
            payer.name AS payer_name,
            creator.name AS created_by_name
        FROM expenses e
        JOIN users payer ON payer.id = e.payer_user_id
        JOIN users creator ON creator.id = e.created_by_user_id
        WHERE e.id = ?
        """,
        (expense_id,),
    ).fetchall()

    hydrated = _hydrate_expenses(rows)
    if not hydrated:
        raise ApiError("Expense not found.", 404)
    return hydrated[0]


def get_group_balances(group_id: int):
    members = get_group_members(group_id)
    member_lookup = {member["id"]: member["name"] for member in members}
    balance_map = _get_balance_map(group_id, member_lookup)

    balances = []
    for member in members:
        balance_paise = balance_map.get(member["id"], 0)
        balances.append(
            {
                "user_id": member["id"],
                "name": member["name"],
                "email": member["email"],
                "balance_paise": balance_paise,
                "balance_display": format_paise(abs(balance_paise)),
                "status": "gets_back" if balance_paise > 0 else "owes" if balance_paise < 0 else "settled",
            }
        )

    balances.sort(key=lambda item: (abs(item["balance_paise"]), item["name"]), reverse=True)
    return balances


def get_group_settlements(group_id: int):
    members = get_group_members(group_id)
    member_lookup = {member["id"]: member["name"] for member in members}
    balance_map = _get_balance_map(group_id, member_lookup)
    return calculate_settlements(balance_map, member_lookup)


def _get_balance_map(group_id: int, member_lookup):
    expenses = _hydrate_expenses(_fetch_expense_rows(group_id))
    return calculate_balances(expenses, member_lookup)


def _fetch_expense_rows(group_id: int, payer_user_id=None, start_date=None, end_date=None, search=None):
    db = get_db()
    clauses = ["e.group_id = ?"]
    params = [group_id]

    if payer_user_id is not None:
        clauses.append("e.payer_user_id = ?")
        params.append(payer_user_id)

    if start_date is not None:
        clauses.append("e.expense_date >= ?")
        params.append(start_date)

    if end_date is not None:
        clauses.append("e.expense_date <= ?")
        params.append(end_date)

    if search:
        clauses.append("LOWER(e.description) LIKE ?")
        params.append(f"%{search.lower()}%")

    return db.execute(
        f"""
        SELECT
            e.id,
            e.group_id,
            e.payer_user_id,
            e.created_by_user_id,
            e.description,
            e.amount_paise,
            e.currency_code,
            e.expense_date,
            e.split_mode,
            e.source_type,
            e.notes,
            e.ai_confidence,
            e.created_at,
            payer.name AS payer_name,
            creator.name AS created_by_name
        FROM expenses e
        JOIN users payer ON payer.id = e.payer_user_id
        JOIN users creator ON creator.id = e.created_by_user_id
        WHERE {' AND '.join(clauses)}
        ORDER BY e.expense_date DESC, e.created_at DESC, e.id DESC
        """,
        params,
    ).fetchall()


def _hydrate_expenses(expense_rows):
    if not expense_rows:
        return []

    expense_ids = [row["id"] for row in expense_rows]
    placeholders = ",".join("?" for _ in expense_ids)
    db = get_db()

    share_rows = db.execute(
        f"""
        SELECT
            es.expense_id,
            es.user_id,
            es.amount_paise,
            es.weight,
            es.share_order,
            u.name AS user_name
        FROM expense_shares es
        JOIN users u ON u.id = es.user_id
        WHERE es.expense_id IN ({placeholders})
        ORDER BY es.expense_id, es.share_order, es.id
        """,
        expense_ids,
    ).fetchall()

    item_rows = db.execute(
        f"""
        SELECT
            expense_id,
            item_name,
            amount_paise,
            assigned_user_ids_json
        FROM expense_items
        WHERE expense_id IN ({placeholders})
        ORDER BY expense_id, id
        """,
        expense_ids,
    ).fetchall()

    shares_by_expense = {}
    for row in share_rows:
        share = dict(row)
        shares_by_expense.setdefault(share["expense_id"], []).append(
            {
                "user_id": share["user_id"],
                "user_name": share["user_name"],
                "amount_paise": share["amount_paise"],
                "amount_display": format_paise(share["amount_paise"]),
                "weight": share["weight"],
                "share_order": share["share_order"],
            }
        )

    items_by_expense = {}
    for row in item_rows:
        item = dict(row)
        items_by_expense.setdefault(item["expense_id"], []).append(
            {
                "item_name": item["item_name"],
                "amount_paise": item["amount_paise"],
                "amount_display": format_paise(item["amount_paise"]),
                "assigned_user_ids": json.loads(item["assigned_user_ids_json"]),
            }
        )

    expenses = []
    for row in expense_rows:
        expense = dict(row)
        expense["amount_display"] = format_paise(expense["amount_paise"])
        expense["shares"] = shares_by_expense.get(expense["id"], [])
        expense["line_items"] = items_by_expense.get(expense["id"], [])
        expense["split_summary"] = build_split_summary(expense["shares"])
        expense["source_label"] = SOURCE_LABELS.get(expense["source_type"], expense["source_type"])
        expense["line_item_count"] = len(expense["line_items"])
        expenses.append(expense)
    return expenses


def _ensure_group_exists(group_id: int):
    row = get_db().execute("SELECT id FROM groups WHERE id = ?", (group_id,)).fetchone()
    if row is None:
        raise ApiError("Group not found.", 404)


def _ensure_users_exist(user_ids):
    unique_ids = list(dict.fromkeys(user_ids))
    placeholders = ",".join("?" for _ in unique_ids)
    rows = get_db().execute(
        f"SELECT id FROM users WHERE id IN ({placeholders})",
        unique_ids,
    ).fetchall()
    existing_ids = {row["id"] for row in rows}
    missing_ids = [user_id for user_id in unique_ids if user_id not in existing_ids]
    if missing_ids:
        raise ApiError(f"Unknown user ids: {missing_ids}")
