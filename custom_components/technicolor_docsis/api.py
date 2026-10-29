"""Local, read-only client for the Technicolor CGA4233-EU web API."""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any

import aiohttp
from yarl import URL

MODEM_PATH = "modem/exUSTbl,exDSTbl,USTbl,DSTbl,ErrTbl"
SYSTEM_PATH = (
    "system/CMStatus,ModelName,Manufacturer,SerialNumber,HardwareVersion,"
    "SoftwareVersion,UpTime,BootloaderVersion,CoreVersion,FirmwareName,"
    "FirmwareBuildTime,ProcessorSpeed,CMMACAddress,MemTotal,MemFree,CPUUsage"
)
TABLES = ("USTbl", "DSTbl", "exUSTbl", "exDSTbl", "ErrTbl")


class RouterError(Exception):
    """The router cannot provide a valid response."""


class AuthenticationError(RouterError):
    """The router rejected authentication."""


def normalize_host(host: str) -> str:
    """Accept an address or origin, but never embedded credentials or paths."""
    host = host.strip()
    url = URL(host if "://" in host else f"http://{host}")
    if (
        url.scheme not in ("http", "https")
        or not url.host
        or url.user is not None
        or url.path not in ("", "/")
        or url.query_string
        or url.fragment
    ):
        raise ValueError("Enter only the router address, without a path or credentials")
    return str(url.origin())


def derive_password(password: str, salt: str, web_salt: str) -> str:
    """Match SJCL PBKDF2-HMAC-SHA256 with UTF-8 salts and 128-bit keys."""
    first = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 1000, dklen=16).hex()
    return hashlib.pbkdf2_hmac("sha256", first.encode(), web_salt.encode(), 1000, dklen=16).hex()


class RouterClient:
    """Own an isolated session; IP-address cookies must be explicitly allowed."""

    def __init__(self, host: str, username: str, password: str) -> None:
        self.host = normalize_host(host)
        self._username = username
        self._password = password
        self._session = aiohttp.ClientSession(
            cookie_jar=aiohttp.CookieJar(unsafe=True),
            timeout=aiohttp.ClientTimeout(total=60),
        )
        self._authenticated = False
        self._lock = asyncio.Lock()

    async def close(self) -> None:
        """Release the owned HTTP session without invalidating other logins."""
        await self._session.close()

    async def _request(
        self, method: str, path: str, form: dict[str, str] | None = None
    ) -> dict[str, Any]:
        cookies = self._session.cookie_jar.filter_cookies(URL(self.host))
        auth = cookies.get("auth")
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRF-TOKEN": auth.value if auth else "",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": f"{self.host}/",
        }
        try:
            async with self._session.request(
                method,
                f"{self.host}/api/v1/{path}",
                data=form,
                headers=headers,
                allow_redirects=False,
            ) as response:
                if response.status in (401, 403):
                    raise AuthenticationError("Router authentication required")
                if response.status != 200:
                    raise RouterError(f"Router returned HTTP {response.status}")
                payload = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise RouterError("Unable to read router response") from err
        if not isinstance(payload, dict):
            raise RouterError("Invalid router response")
        if payload.get("error") != "ok":
            if path == "session/login":
                raise AuthenticationError("Router rejected login")
            raise RouterError("Router rejected read request")
        return payload

    async def _login(self) -> None:
        """Authenticate and initialize the router's read permissions via its menu."""
        self._authenticated = False
        challenge = await self._request(
            "POST",
            "session/login",
            {"username": self._username, "password": "seeksalthash"},
        )
        salt = challenge.get("salt")
        if salt == "none":
            password = self._password
        elif isinstance(salt, str) and isinstance(challenge.get("saltwebui"), str):
            password = await asyncio.to_thread(
                derive_password, self._password, salt, challenge["saltwebui"]
            )
        else:
            raise RouterError("Unsupported login challenge")
        await self._request(
            "POST",
            "session/login",
            {"username": self._username, "password": password},
        )
        await self._request("GET", "session/menu")
        self._authenticated = True

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch one consistent snapshot; retry expired authentication once."""
        async with self._lock:
            for attempt in range(2):
                if not self._authenticated:
                    await self._login()
                try:
                    system = (await self._request("GET", SYSTEM_PATH)).get("data")
                    modem = (await self._request("GET", MODEM_PATH)).get("data")
                    if not isinstance(system, dict) or not isinstance(modem, dict):
                        raise RouterError("Missing system or modem data")
                    if system.get("ModelName", "").strip() != "CGA4233-EU":
                        raise RouterError("Only CGA4233-EU is supported")
                    if not (system.get("SerialNumber") or system.get("CMMACAddress")):
                        raise RouterError("Router did not supply a stable device identifier")
                    for table in TABLES:
                        rows = modem.get(table)
                        if not isinstance(rows, list) or not all(
                            isinstance(row, dict) for row in rows
                        ):
                            raise RouterError(f"Invalid or missing {table}")
                    return {"system": system, "modem": modem}
                except AuthenticationError:
                    self._authenticated = False
                    if attempt:
                        raise
            raise AuthenticationError("Router authentication failed")


def device_identifier(data: dict[str, Any]) -> str:
    """Use the serial number, falling back to the cable modem MAC."""
    system = data["system"]
    return str(system.get("SerialNumber") or system["CMMACAddress"]).strip().lower()
