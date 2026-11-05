"""No real LLM/provider calls: assert identity at the HTTP boundary."""

import asyncio
import unittest
from unittest.mock import patch

import httpx
from app.core.identity import Identity, current_identity
from app.infrastructure.clients.business_logic_client import BusinessLogicClient


class DelegationTests(unittest.IsolatedAsyncioTestCase):
    async def test_no_identity_cannot_send_any_backend_request(self):
        client = BusinessLogicClient()
        with patch("httpx.AsyncClient") as transport:
            with self.assertRaises(PermissionError):
                await client.request_with_retry(
                    "post", client.base_url + "/appointment", json={}
                )
            transport.assert_not_called()

    async def test_forbidden_write_is_not_retried_or_sent_as_service_account(self):
        calls = []

        async def respond(request):
            calls.append(request)
            return httpx.Response(403, json={"message": "Forbidden"})

        original = httpx.AsyncClient

        def factory(**kwargs):
            return original(transport=httpx.MockTransport(respond), **kwargs)

        marker = current_identity.set(Identity(1, "Bearer synthetic-user-1"))
        try:
            client = BusinessLogicClient()
            with patch("httpx.AsyncClient", side_effect=factory):
                with self.assertRaises(httpx.HTTPStatusError):
                    await client.request_with_retry(
                        "post",
                        client.base_url + "/appointment",
                        json={},
                        headers={"authorization": "Bearer injected"},
                    )
            self.assertEqual(len(calls), 1)
            self.assertEqual(
                calls[0].headers["Authorization"], "Bearer synthetic-user-1"
            )
            self.assertFalse(await client.renew_token())
        finally:
            current_identity.reset(marker)

    async def test_parallel_users_do_not_share_token_state(self):
        observed = []

        async def respond(request):
            await asyncio.sleep(0)
            observed.append(request.headers["Authorization"])
            return httpx.Response(200, json=[])

        original = httpx.AsyncClient
        shared = BusinessLogicClient()

        def factory(**kwargs):
            return original(transport=httpx.MockTransport(respond), **kwargs)

        async def invoke(user):
            marker = current_identity.set(Identity(user, f"Bearer user-{user}"))
            try:
                await shared.request_with_retry("get", shared.base_url + "/appointment")
            finally:
                current_identity.reset(marker)

        with patch("httpx.AsyncClient", side_effect=factory):
            await asyncio.gather(invoke(1), invoke(2))
        self.assertCountEqual(observed, ["Bearer user-1", "Bearer user-2"])
        self.assertIsNone(current_identity.get())

    async def test_token_cannot_be_forwarded_to_another_origin(self):
        marker = current_identity.set(Identity(1, "Bearer user-1"))
        try:
            with self.assertRaises(PermissionError):
                await BusinessLogicClient().request_with_retry(
                    "get", "https://external.invalid/api/user"
                )
        finally:
            current_identity.reset(marker)
