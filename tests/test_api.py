"""Exercise the real HTTP client without Home Assistant or router credentials."""

import importlib.util
import unittest
from pathlib import Path

from aiohttp import web

SPEC = importlib.util.spec_from_file_location(
    "router_api",
    Path(__file__).parents[1] / "custom_components/technicolor_docsis/api.py",
)
api = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(api)


class RouterClientTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.logins = 0
        self.menu_calls = 0
        self.initialized = False
        self.expire = False
        self.invalid_password = False
        self.malformed = False
        self.seen_passwords = []
        app = web.Application()
        app.router.add_route("*", "/api/v1/{path:.*}", self.handle)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        server = web.TCPSite(self.runner, "127.0.0.1", 0)
        await server.start()
        port = server._server.sockets[0].getsockname()[1]
        self.client = api.RouterClient(f"http://127.0.0.1:{port}", "test", "secret")

    async def asyncTearDown(self):
        await self.client.close()
        await self.runner.cleanup()

    async def handle(self, request):
        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            return web.json_response({"error": "error"}, status=401)
        path = request.match_info["path"]
        if path == "session/login":
            self.assertEqual(request.method, "POST")
            form = await request.post()
            if form["password"] == "seeksalthash":
                return web.json_response({"error": "ok", "salt": "salt", "saltwebui": "websalt"})
            self.seen_passwords.append(form["password"])
            if self.invalid_password:
                return web.json_response({"error": "error"})
            self.assertEqual(form["password"], api.derive_password("secret", "salt", "websalt"))
            self.logins += 1
            self.initialized = False
            response = web.json_response({"error": "ok"})
            response.set_cookie("PHPSESSID", "session")
            response.set_cookie("auth", "csrf")
            return response
        self.assertEqual(request.method, "GET")
        if self.expire:
            self.expire = False
            return web.json_response({"error": "error"}, status=401)
        if (
            request.cookies.get("PHPSESSID") != "session"
            or request.headers.get("X-CSRF-TOKEN") != "csrf"
        ):
            return web.json_response({"error": "error"}, status=401)
        if path == "session/menu":
            self.menu_calls += 1
            self.initialized = True
            return web.json_response({"error": "ok", "data": {"menu": {}}})
        if not self.initialized:
            return web.Response(status=500, text="Session menu has not initialized read access")
        if path.startswith("system/"):
            data = {"ModelName": "CGA4233-EU", "SerialNumber": "TEST123"}
        else:
            data = {name: [] for name in api.TABLES}
            if self.malformed:
                del data["ErrTbl"]
        return web.json_response({"error": "ok", "data": data})

    async def test_login_cookies_headers_and_session_reuse(self):
        data = await self.client.async_get_data()
        self.assertEqual(api.device_identifier(data), "test123")
        await self.client.async_get_data()
        self.assertEqual(self.logins, 1)
        self.assertEqual(self.menu_calls, 1)
        self.assertNotIn("secret", self.seen_passwords)

    async def test_expired_session_reauthenticates_once(self):
        await self.client.async_get_data()
        self.expire = True
        await self.client.async_get_data()
        self.assertEqual(self.logins, 2)
        self.assertEqual(self.menu_calls, 2)

    async def test_login_initializes_read_permissions_before_system_requests(self):
        await self.client.async_get_data()
        self.assertTrue(self.initialized)
        self.assertEqual(self.menu_calls, 1)

    async def test_rejected_credentials(self):
        self.invalid_password = True
        with self.assertRaises(api.AuthenticationError):
            await self.client.async_get_data()
        self.assertEqual(len(self.seen_passwords), 1)

    async def test_missing_table_is_not_silently_zero(self):
        self.malformed = True
        with self.assertRaises(api.RouterError):
            await self.client.async_get_data()


class HostTests(unittest.TestCase):
    def test_address_normalization(self):
        self.assertEqual(api.normalize_host("192.168.100.1"), "http://192.168.100.1")

    def test_reject_credentials_paths_and_unsupported_schemes(self):
        for value in (
            "http://user:secret@router",
            "http://router/#/login",
            "ftp://router",
            "http://router/api",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                api.normalize_host(value)
