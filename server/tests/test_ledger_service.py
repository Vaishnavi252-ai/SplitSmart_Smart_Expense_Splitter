import unittest

from server.services.ledger_service import allocate_weighted_amount, calculate_settlements


class LedgerServiceTests(unittest.TestCase):
    def test_allocate_weighted_amount_distributes_remainder_deterministically(self):
        shares = allocate_weighted_amount(
            100,
            [
                {"user_id": 1, "weight": 1},
                {"user_id": 2, "weight": 1},
                {"user_id": 3, "weight": 1},
            ],
        )
        self.assertEqual(sum(share["amount_paise"] for share in shares), 100)
        self.assertEqual([share["amount_paise"] for share in shares], [34, 33, 33])

    def test_calculate_settlements_returns_minimal_greedy_transfers(self):
        settlements = calculate_settlements(
            {
                1: 5000,
                2: -3000,
                3: -2000,
            },
            {
                1: "Aisha",
                2: "Aman",
                3: "Priya",
            },
        )
        self.assertEqual(len(settlements), 2)
        self.assertEqual(settlements[0]["from_name"], "Aman")
        self.assertEqual(settlements[0]["to_name"], "Aisha")
        self.assertEqual(settlements[0]["amount_paise"], 3000)


if __name__ == "__main__":
    unittest.main()
