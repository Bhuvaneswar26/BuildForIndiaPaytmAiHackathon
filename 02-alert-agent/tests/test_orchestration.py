import asyncio
import unittest

from app.graph.workflow import run_alert_workflow


async def _run_workflow():
    return await run_alert_workflow(
        {
            "merchant_id": "M1001",
            "name": "Amit",
            "phone": "+919999999999",
            "email": "merchant@example.com",
            "language": "en",
            "pct": 88,
            "aggregate_turnover": 880000,
            "threshold": 1000000,
            "fy_label": "FY2025-26",
            "advisor_url": "https://advisor.example.com",
            "gst_portal": "https://gst.example.com",
            "data_caveat": "Estimated from Paytm + declared sales.",
            "months_to_threshold": 2,
        }
    )


class AlertWorkflowOrchestrationTest(unittest.TestCase):
    def test_run_alert_workflow_builds_valid_rich_response(self):
        result = asyncio.run(_run_workflow())

        self.assertEqual(result["risk"], "act_soon")
        self.assertEqual(result["message"]["language"], "en")
        self.assertTrue(result["message"]["channel_title"])
        self.assertTrue(result["message"]["body"])
        self.assertEqual(result["payload"]["email"], "merchant@example.com")
        self.assertTrue(result["validation"]["ok"])
        self.assertIn("risk_reason", result["context"])
        self.assertEqual(result["context"]["merchant_name"], "Amit")


if __name__ == "__main__":
    unittest.main()
