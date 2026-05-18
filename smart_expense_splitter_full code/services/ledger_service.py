from collections import defaultdict

from errors import ApiError


def format_paise(amount_paise: int) -> str:
    return f"₹{amount_paise / 100:.2f}"


def _normalize_participants(participants):
    normalized = []
    for participant in participants:
        if hasattr(participant, "model_dump"):
            normalized.append(participant.model_dump())
        else:
            normalized.append(dict(participant))
    return normalized


def allocate_weighted_amount(total_paise: int, weighted_members):
    if total_paise <= 0:
        raise ApiError("Expense totals must be greater than zero.")

    prepared = []
    total_weight = 0

    for order, member in enumerate(weighted_members):
        if isinstance(member, dict):
            user_id = member["user_id"]
            weight = member["weight"]
        else:
            user_id, weight = member

        if weight <= 0:
            raise ApiError("Weights must be positive integers.")

        total_weight += weight
        prepared.append(
            {
                "user_id": user_id,
                "weight": weight,
                "order": order,
            }
        )

    if not prepared or total_weight <= 0:
        raise ApiError("At least one participant is required.")

    allocated = 0
    for item in prepared:
        numerator = total_paise * item["weight"]
        item["amount_paise"] = numerator // total_weight
        item["remainder_rank"] = numerator % total_weight
        allocated += item["amount_paise"]

    remainder = total_paise - allocated
    for item in sorted(prepared, key=lambda value: (-value["remainder_rank"], value["order"])):
        if remainder == 0:
            break
        item["amount_paise"] += 1
        remainder -= 1

    return [
        {
            "user_id": item["user_id"],
            "amount_paise": item["amount_paise"],
            "weight": item["weight"],
        }
        for item in prepared
    ]


def build_shares(total_paise: int, split_mode: str, participants, group_member_ids):
    group_member_id_set = set(group_member_ids)
    normalized = _normalize_participants(participants)

    for participant in normalized:
        if participant["user_id"] not in group_member_id_set:
            raise ApiError("Every participant must belong to the group.")

    if split_mode == "equal_all":
        shares = allocate_weighted_amount(
            total_paise,
            [{"user_id": member_id, "weight": 1} for member_id in group_member_ids],
        )
    elif split_mode == "equal_subset":
        selected_ids = []
        for participant in normalized:
            if participant.get("selected", True) and participant["user_id"] not in selected_ids:
                selected_ids.append(participant["user_id"])
        if not selected_ids:
            raise ApiError("Select at least one participant for the expense.")
        shares = allocate_weighted_amount(
            total_paise,
            [{"user_id": member_id, "weight": 1} for member_id in selected_ids],
        )
    elif split_mode == "custom":
        shares = []
        running_total = 0
        seen_ids = set()

        for order, participant in enumerate(normalized):
            if participant["user_id"] in seen_ids:
                raise ApiError("Participants must be unique.")
            seen_ids.add(participant["user_id"])

            if not participant.get("selected", True):
                continue

            amount_paise = participant.get("amount_paise")
            if amount_paise is None:
                raise ApiError("Custom splits require an amount for each selected participant.")

            running_total += amount_paise
            shares.append(
                {
                    "user_id": participant["user_id"],
                    "amount_paise": amount_paise,
                    "weight": None,
                    "order": order,
                }
            )

        if not shares:
            raise ApiError("Select at least one participant for the expense.")
        if running_total != total_paise:
            raise ApiError("Custom split amounts must sum exactly to the expense total.")
    elif split_mode == "weights":
        weighted_members = []
        seen_ids = set()
        for participant in normalized:
            if participant["user_id"] in seen_ids:
                raise ApiError("Participants must be unique.")
            seen_ids.add(participant["user_id"])

            if participant.get("selected", True):
                weight = participant.get("weight")
                if weight is None:
                    raise ApiError("Weighted splits require a positive integer weight per participant.")
                weighted_members.append({"user_id": participant["user_id"], "weight": weight})

        shares = allocate_weighted_amount(total_paise, weighted_members)
    else:
        raise ApiError("Unsupported split mode.")

    if sum(item["amount_paise"] for item in shares) != total_paise:
        raise ApiError("Split shares must sum exactly to the expense total.")

    for index, share in enumerate(shares):
        share["order"] = share.get("order", index)

    return shares


def compute_item_assignment_totals(line_items):
    totals = defaultdict(int)

    for line_item in line_items:
        assigned_user_ids = line_item["assigned_user_ids"]
        distributed = allocate_weighted_amount(
            line_item["amount_paise"],
            [{"user_id": user_id, "weight": 1} for user_id in assigned_user_ids],
        )
        for share in distributed:
            totals[share["user_id"]] += share["amount_paise"]

    return dict(totals)


def calculate_balances(expenses, member_lookup):
    balances = {member_id: 0 for member_id in member_lookup}

    for expense in expenses:
        balances[expense["payer_user_id"]] = balances.get(expense["payer_user_id"], 0) + expense["amount_paise"]
        for share in expense["shares"]:
            balances[share["user_id"]] = balances.get(share["user_id"], 0) - share["amount_paise"]

    return balances


def calculate_settlements(balance_map, member_lookup):
    creditors = []
    debtors = []

    for user_id, balance in balance_map.items():
        if balance > 0:
            creditors.append({"user_id": user_id, "amount_paise": balance})
        elif balance < 0:
            debtors.append({"user_id": user_id, "amount_paise": -balance})

    creditors.sort(key=lambda value: value["amount_paise"], reverse=True)
    debtors.sort(key=lambda value: value["amount_paise"], reverse=True)

    creditor_index = 0
    debtor_index = 0
    settlements = []

    while creditor_index < len(creditors) and debtor_index < len(debtors):
        creditor = creditors[creditor_index]
        debtor = debtors[debtor_index]
        settlement_amount = min(creditor["amount_paise"], debtor["amount_paise"])

        settlements.append(
            {
                "from_user_id": debtor["user_id"],
                "from_name": member_lookup[debtor["user_id"]],
                "to_user_id": creditor["user_id"],
                "to_name": member_lookup[creditor["user_id"]],
                "amount_paise": settlement_amount,
                "amount_display": format_paise(settlement_amount),
            }
        )

        creditor["amount_paise"] -= settlement_amount
        debtor["amount_paise"] -= settlement_amount

        if creditor["amount_paise"] == 0:
            creditor_index += 1
        if debtor["amount_paise"] == 0:
            debtor_index += 1

    return settlements


def build_split_summary(shares):
    if not shares:
        return "No participants"
    return ", ".join(f"{share['user_name']} {format_paise(share['amount_paise'])}" for share in shares)
