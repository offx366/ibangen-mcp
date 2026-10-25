"""Dependency-free calls to the public IBANgen REST API.

Kept separate from the MCP wiring so it can be tested without the ``mcp``
package. Validation and country-level generation work without a key (small
per-IP daily allowances); bank targeting, bank lookups and US tools need
``IBANGEN_API_KEY`` (a free key includes 100 API calls a month).
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://ibangen.com/api/v1"
USER_AGENT = "ibangen-mcp/0.1.2"
SIGNUP_HINT = ("Create a free API key (100 calls a month) at https://ibangen.com/account?focus=api "
               "and set IBANGEN_API_KEY.")


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


def _request(path: str, payload: dict | None, *, require_key: bool, method="POST", opener=urllib.request.urlopen):
    base_url, api_key = _config()
    if require_key and not api_key:
        raise IBANgenAPIError(401, {"error": f"This tool needs an API key. {SIGNUP_HINT}"})
    headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT}
    if api_key:
        headers["X-API-Key"] = api_key
    request = urllib.request.Request(
        base_url + path, data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers=headers, method=method,
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
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        # No automatic retry: a metered operation may already have completed.
        raise IBANgenAPIError(503, {"error": "transport_failure; do not automatically retry a metered call"}) from exc
    except (ValueError, UnicodeError) as exc:
        raise IBANgenAPIError(502, {"error": "invalid_api_response; do not automatically retry a metered call"}) from exc


def _post(path: str, payload: dict, *, require_key: bool, opener=urllib.request.urlopen):
    return _request(path, payload, require_key=require_key, opener=opener)


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
    # Country-level IBANs work without a key (up to 10 a day per IP); bank targeting needs a paid key.
    return _post("/generate", payload, require_key=bool(bank), opener=opener)


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


def generate_us_test_accounts(quantity: int = 1, seed: str | None = None, *, opener=urllib.request.urlopen):
    if type(quantity) is not int or not 1 <= quantity <= 10:
        raise ValueError("quantity must be an integer between 1 and 10")
    payload = {"mode": "synthetic", "quantity": quantity}
    if seed is not None:
        if not isinstance(seed, str) or len(seed) > 100:
            raise ValueError("seed must be a string of at most 100 characters")
        payload["seed"] = seed
    return _post("/us/routing/generate", payload, require_key=True, opener=opener)


def validate_us_routing_numbers(routing_numbers: list[str], *, confirm_api_credits: bool = False,
                                opener=urllib.request.urlopen):
    if not isinstance(routing_numbers, list) or not 1 <= len(routing_numbers) <= 10:
        raise ValueError("Provide between 1 and 10 routing numbers")
    if any(not isinstance(value, str) or not value.strip() or len(value) > 30 for value in routing_numbers):
        raise ValueError("Routing numbers must be nonempty strings of at most 30 characters")
    if confirm_api_credits is not True:
        raise ValueError("Explicitly confirm spending up to one API credit per distinct routing number")
    return _post("/us/routing/check-list", {"routing_numbers": [value.strip() for value in routing_numbers],
                                           "generate_tests": False}, require_key=True, opener=opener)


def lookup_us_routing_number(routing_number: str, *, confirm_api_credit: bool = False,
                              opener=urllib.request.urlopen):
    if not isinstance(routing_number, str) or not re.fullmatch(r"[0-9]{9}", routing_number):
        raise ValueError("Provide a routing number as a 9-digit string, preserving leading zeros")
    if confirm_api_credit is not True:
        raise ValueError("Explicitly confirm spending one API credit for this lookup")
    return _request("/us/routing/" + routing_number, None, method="GET", require_key=True, opener=opener)
