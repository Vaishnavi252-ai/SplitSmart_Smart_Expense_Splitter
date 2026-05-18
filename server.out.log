import os
import tempfile
import unittest
from unittest import mock

from app import create_app


class ExpenseSplitterApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "test.db")
        self.app = create_app({"TESTING": True, "DATABASE": self.database_path})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_seeded_group_can_be_loaded(self):
        response = self.client.get("/api/groups/1")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["name"], "Goa Escape")
        self.assertEqual(len(payload["members"]), 4)

    def test_invalid_custom_split_is_rejected(self):
        response = self.client.post(
            "/api/groups/1/expenses",
            json={
                "payer_user_id": 1,
                "created_by_user_id": 1,
                "description": "Broken dinner",
                "amount_paise": 10000,
                "currency_code": "INR",
                "expense_date": "2026-05-18",
                "split_mode": "custom",
                "participants": [
                    {"user_id": 1, "selected": True, "amount_paise": 3000},
                    {"user_id": 2, "selected": True, "amount_paise": 3000},
                ],
                "source_type": "manual",
                "line_items": [],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("sum exactly", response.get_json()["error"])

    def test_equal_subset_expense_is_saved(self):
        response = self.client.post(
            "/api/groups/1/expenses",
            json={
                "payer_user_id": 1,
                "created_by_user_id": 1,
                "description": "Test lunch",
                "amount_paise": 9000,
                "currency_code": "INR",
                "expense_date": "2026-05-18",
                "split_mode": "equal_subset",
                "participants": [
                    {"user_id": 1, "selected": True},
                    {"user_id": 2, "selected": True},
                    {"user_id": 3, "selected": True},
                ],
                "source_type": "manual",
                "line_items": [],
            },
        )
        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["description"], "Test lunch")
        self.assertEqual(len(payload["shares"]), 3)

    def test_ai_expense_endpoint_falls_back_without_api_key(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            response = self.client.post(
                "/api/groups/1/ai/parse-expense",
                json={
                    "text": "I paid 2400 for dinner with Aman and Priya",
                    "current_user_id": 1,
                },
            )
        self.assertEqual(response.status_code, 422)
        payload = response.get_json()
        self.assertIn("unavailable", payload["fallback_message"])


if __name__ == "__main__":
    unittest.main()
