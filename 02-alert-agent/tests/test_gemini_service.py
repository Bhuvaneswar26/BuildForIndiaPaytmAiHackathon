import unittest
from unittest.mock import patch

from app.config import settings
from app.services.gemini_service import _safe_json_parse, generate_alert_copy


class SarvamParserTests(unittest.TestCase):
    def test_safe_json_parse_handles_truncated_json(self):
        raw = '{"title":"GST నమోదు","body":"మీరు GST పరిమితి'
        parsed = _safe_json_parse(raw)
        self.assertEqual(parsed["title"], "GST నమోదు")
        self.assertIn("GST", parsed.get("body", ""))

    @patch("app.services.gemini_service.httpx.post")
    def test_generate_alert_copy_uses_template_when_json_is_truncated(self, mock_post):
        class MockResponse:
            status_code = 200
            text = '{"title":"GST నమోదు ప్రాథ"'

            def json(self):
                return {"choices": [{"message": {"content": self.text}}]}

            def raise_for_status(self):
                return None

        mock_post.return_value = MockResponse()
        metrics = {
            "name": "Sharma Kirana",
            "language": "te",
            "pct": 68,
            "aggregate_turnover": 2720000,
            "threshold": 4000000,
            "fy_label": "FY2025-26",
            "advisor_url": "https://paytm.example/advisor",
            "gst_portal": "https://gst.example/portal",
            "months_to_threshold": 2,
        }
        with patch.object(settings, "sarvam_api_key", "sk_test_alert_agent"):
            result = generate_alert_copy("prepare", metrics)
        self.assertEqual(result["language"], "te")
        self.assertEqual(result["source"], "template_fallback")
        self.assertIn("GST", result["channel_title"])
        self.assertIn("Sharma", result["body"])
        self.assertIn("GST", result["body"])
        request = mock_post.call_args.kwargs
        self.assertEqual(request["headers"]["api-subscription-key"], "sk_test_alert_agent")
        self.assertEqual(request["json"]["model"], "sarvam-105b")
        self.assertEqual(request["json"]["messages"][0]["role"], "system")
        self.assertEqual(request["json"]["messages"][1]["role"], "user")


if __name__ == "__main__":
    unittest.main()
