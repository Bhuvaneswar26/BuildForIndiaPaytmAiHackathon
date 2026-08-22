import asyncio
import unittest

from fastapi.testclient import TestClient

from app.graph.workflow import run_alert_workflow
from app.main import app


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
        self.assertIn("merchant_guidance", result["context"])
        self.assertIn("suggestions", result["context"]["merchant_guidance"])
        self.assertIn("guardrails", result["context"])
        self.assertTrue(result["context"]["guardrails"]["allow_send"])
        self.assertEqual(result["context"]["merchant_name"], "Amit")
        self.assertEqual(result["context"]["language_policy"]["selected_language"], "en")
        self.assertEqual(result["context"]["language_policy"]["notify_channel"], "email")

    def test_evaluate_endpoint_accepts_metrics_only_payload_with_telugu_fallback(self):
        client = TestClient(app)
        response = client.post(
            "/v1/evaluate",
            json={
                "metrics": {
                    "merchant_id": "TEST_001",
                    "name": "Steven",
                    "phone": "+919999999999",
                    "email": "stevensonr289@gmail.com",
                    "language": "telugu",
                    "pct": 25,
                    "aggregate_turnover": 1000000,
                    "threshold": 4000000,
                    "fy_label": "FY2025-26",
                    "advisor_url": "http://127.0.0.1:8100",
                    "gst_portal": "https://reg.gst.gov.in/registration/",
                    "data_caveat": "Estimated from platform + declared sales.",
                    "months_to_threshold": 2,
                    "new_checkpoint": 0.25,
                    "checklist": [],
                }
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["risk"], "watch")
        self.assertEqual(body["message"]["language"], "en")
        self.assertTrue(body["validation"]["ok"])
        self.assertEqual(body["payload"]["email"], "stevensonr289@gmail.com")


if __name__ == "__main__":
    unittest.main()
