import unittest

from finance_assistant.core import (
    categorize_transaction,
    dashboard_data,
    generate_budget_suggestions,
    load_transactions_from_csv,
    load_transactions_from_plaid,
)


class FinanceAssistantTests(unittest.TestCase):
    def test_transaction_categorization(self):
        self.assertEqual(categorize_transaction("Spotify premium"), "Entertainment")
        self.assertEqual(categorize_transaction("Apartment lease payment"), "Rent")

    def test_csv_upload_integration(self):
        csv_content = "date,description,amount\n2026-05-01,Supermarket,120.50\n"
        rows = load_transactions_from_csv(csv_content)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].category, "Food")

    def test_csv_upload_skips_blank_lines(self):
        csv_content = "date,description,amount\n2026-05-01,Supermarket,120.50\n,,\n"
        rows = load_transactions_from_csv(csv_content)
        self.assertEqual(len(rows), 1)

    def test_csv_upload_requires_amount_for_non_blank_rows(self):
        csv_content = "date,description,amount\n2026-05-01,Supermarket,\n"
        with self.assertRaises(ValueError):
            load_transactions_from_csv(csv_content)

    def test_plaid_integration(self):
        payload = {
            "transactions": [
                {"date": "2026-05-02", "name": "City Metro", "amount": 35.0, "category": ["Travel", "Transport"]}
            ]
        }
        rows = load_transactions_from_plaid(payload)
        self.assertEqual(rows[0].category, "Transport")

    def test_dashboard_visualization_payload(self):
        rows = load_transactions_from_csv(
            "date,description,amount\n2026-05-01,Supermarket,120.50\n2026-05-10,Netflix,30\n"
        )
        dashboard = dashboard_data(rows)
        self.assertEqual(dashboard["charts"]["category_breakdown"]["type"], "pie")
        self.assertIn("Food", dashboard["charts"]["category_breakdown"]["labels"])

    def test_budget_suggestions_are_personalized(self):
        rows = load_transactions_from_csv(
            "date,description,amount\n2026-05-01,Supermarket,120.50\n2026-05-10,Netflix,200\n"
        )
        suggestions = generate_budget_suggestions(rows, monthly_income=500)
        self.assertTrue(any("highest spending category" in text for text in suggestions))
        self.assertTrue(any("savings rate" in text for text in suggestions))


if __name__ == "__main__":
    unittest.main()
