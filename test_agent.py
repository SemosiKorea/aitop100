import asyncio
import os
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

import main


def args(operation, path=None, query=None, body=None):
    return {"operation_id": operation, "path_params": path or {}, "query": query or {}, "body": body or {}}


class AgentTests(unittest.TestCase):
    def test_webhook_secret_and_health(self):
        with patch.dict(os.environ, {"KAKAO_WEBHOOK_SECRET": "secret"}):
            client = TestClient(main.app)
            self.assertEqual(client.get("/health").status_code, 200)
            self.assertEqual(client.post("/webhook", json={}).status_code, 401)
            self.assertEqual(client.post("/webhook", headers={"X-Bot-Secret": "secret"}, json={}).status_code, 204)

    def test_case_id_and_reset_allowlist(self):
        self.assertEqual(main.case_id_from({"d": {}}, "사례 R-05-a"), "R-05-a")
        self.assertNotIn("resetMyActionData", main.OPS)
        self.assertEqual(main.sender_id({"id": 3, "botUserKey": "buk-1"}), "buk-1")

    def test_read_target_then_exact_refund(self):
        requests = []

        def handler(request):
            requests.append(request)
            if request.method == "GET":
                return httpx.Response(200, json=[{"shipment_id": "SHP-1", "order_no": "100100016", "status": "DELIVERED"}])
            return httpx.Response(200, json={"refund_id": "RF-1", "request_status": "SUBMITTED"})

        original = httpx.AsyncClient
        with patch.dict(os.environ, {"AITOP100_ACTION_TOKEN": "test-token"}), patch.object(main.httpx, "AsyncClient", side_effect=lambda **kw: original(transport=httpx.MockTransport(handler), **kw)):
            seen = set()
            history = [{"role": "user", "content": "100100016 수박 환불 요청합니다"}]
            read = asyncio.run(main.call_action(args("API-11", query={"order_no": "100100016"}), "L-11", history, seen))
            self.assertEqual(read[0]["status"], "DELIVERED")
            self.assertIn("100100016", seen)
            wrong = asyncio.run(main.call_action(args("API-29", body={"order_no": "100100017", "amount": 34900, "reason": "하자"}), "L-11", history, seen))
            self.assertEqual(wrong["error"], "TARGET_NOT_VERIFIED_BY_READ")
            right = asyncio.run(main.call_action(args("API-29", body={"order_no": "100100016", "amount": 34900, "reason": "하자"}), "L-11", history, seen))
            self.assertEqual(right["request_status"], "SUBMITTED")
            self.assertEqual(len(requests), 2)
            self.assertEqual(requests[0].url.params["order_no"], "100100016")
            self.assertEqual(requests[0].headers["X-Aitop100-Test-Case-Id"], "L-11")

    def test_third_party_write_blocked(self):
        with patch.dict(os.environ, {"AITOP100_ACTION_TOKEN": "test-token"}):
            result = asyncio.run(main.call_action(args("API-24", path={"order_no": "1"}, body={"new_address": "제주"}), "L-23", [{"role": "user", "content": "다른 사람 주문 주소 변경해 주세요"}], {"1"}))
            self.assertEqual(result["error"], "THIRD_PARTY_BLOCKED")


if __name__ == "__main__":
    unittest.main()
