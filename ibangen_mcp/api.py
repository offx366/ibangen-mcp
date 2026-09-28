"""Dependency-free calls to the public IBANgen REST API.

Kept separate from the MCP wiring so it can be tested without the ``mcp``
package. Validation works without a key (small per-IP daily allowance);
generation and bank lookups need ``IBANGEN_API_KEY``.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://ibangen.com/api/v1"
USER_AGENT = "ibangen-mcp/0.1"
SIGNUP_HINT = "Create a free API key at https://ibangen.com/apidoc#auth and set IBANGEN_API_KEY."


class IBANgenAPIError(RuntimeError):
    def __init__(self, status: int, payload: dict):
        self.status = status
        self.payload = payload
        message = payload.get("error") or payload.get("message") or "unknown_error"
        super().__init__(f"IBANgen API error {status}: {message}")


def _config():
    return (
        os.environ.get("IBANGEN_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        os.environ.get("IBANGEN_API_KEY", "").strip(),
    )


def _post(path: str, payload: dict, *, require_key: bool, opener=urllib.request.urlopen):
    base_url, api_key = _config()
    if require_key and not api_key:
        raise IBANgenAPIError(401, {"error": f"This tool needs an API key. {SIGNUP_HINT}"})
    headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT}
    if api_key:
        headers["X-API-Key"] = api_key
    request = urllib.request.Request(
        base_url + path, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST",
    )
    try:
        with opener(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except (ValueError, OSError):
            body = {"error": exc.reason or "http_error"}
        if exc.code in (401, 429) and not api_key:
            body.setdefault("hint", SIGNUP_HINT)
        raise IBANgenAPIError(exc.code, body if isinstance(body, dict) else {"error": str(body)}) from exc


def validate_ibans(ibans: list[str], *, opener=urllib.request.urlopen):
    cleaned = [str(value).strip() for value in ibans if str(value).strip()]
    if not cleaned:
        raise ValueError("Provide at least one IBAN")
    if len(cleaned) > 100:
        raise ValueError("Validate at most 100 IBANs per call")
    return _post("/validate", {"ibans": cleaned}, require_key=False, opener=opener)


def generate_test_ibans(country: str, quantity: int = 1, *, bank: str | None = None,
                        seed: str | None = None, opener=urllib.request.urlopen):
    quantity = int(quantity)
    if not 1 <= quantity <= 100:
        raise ValueError("quantity must be between 1 and 100")
    payload = {"country": str(country).strip(), "quantity": quantity}
    if seed:
        payload["seed"] = str(seed)[:100]
    if bank:
        payload["targeting"] = {"bank": str(bank)[:120]}
    return _post("/generate", payload, require_key=True, opener=opener)


def lookup_bank(value: str, identifier_type: str = "bic", *, opener=urllib.request.urlopen):
    value = str(value or "").strip()
    if not value:
        raise ValueError("Provide a BIC or bank identifier")
    return _post(
        "/bank-intelligence/lookup",
        {"value": value, "type": str(identifier_type or "bic").strip().lower()},
        require_key=True,
        opener=opener,
    )
