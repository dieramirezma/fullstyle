"""Real TCP failures: two read attempts, one mutation, and no retry on auth rejection."""

import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
from app.core.reliability import request


class RetryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.calls = []
        calls = self.calls

        class Handler(BaseHTTPRequestHandler):
            def handle_request(self):
                calls.append((self.command, self.path))
                status = 200
                if self.path == "/recover" and len(calls) == 1:
                    status = 503
                if self.path == "/down":
                    status = 503
                if self.path == "/auth":
                    status = 401
                if self.path == "/slow":
                    time.sleep(5.4)
                try:
                    self.send_response(status)
                    self.end_headers()
                    self.wfile.write(b"{}")
                except BrokenPipeError:
                    pass

            do_GET = handle_request
            do_POST = handle_request
            do_DELETE = handle_request

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)

    async def test_01_read_recovers_after_one_transient_failure(self):
        self.assertEqual((await request("GET", self.url + "/recover")).status_code, 200)
        self.assertEqual(len(self.calls), 2)

    async def test_02_persistent_failure_is_bounded(self):
        self.assertEqual((await request("GET", self.url + "/down")).status_code, 503)
        self.assertEqual(len(self.calls), 2)

    async def test_03_mutations_and_auth_rejections_are_never_retried(self):
        for method, path, expected in (
            ("POST", "/down", 503),
            ("DELETE", "/down", 503),
            ("GET", "/auth", 401),
        ):
            self.calls.clear()
            self.assertEqual(
                (await request(method, self.url + path)).status_code, expected
            )
            self.assertEqual(len(self.calls), 1)

    async def test_04_slow_write_times_out_after_one_effect(self):
        started = time.monotonic()
        with self.assertRaises(httpx.TimeoutException):
            await request("POST", self.url + "/slow")
        self.assertLess(time.monotonic() - started, 6.5)
        self.assertEqual(self.calls, [("POST", "/slow")])


if __name__ == "__main__":
    unittest.main()
