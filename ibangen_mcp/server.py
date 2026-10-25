"""stdio MCP server: `ibangen-mcp` (or `python -m ibangen_mcp.server`)."""
from __future__ import annotations

try:  # mcp >= 2
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

from . import api

mcp = _Server("ibangen")


def _call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except (api.IBANgenAPIError, ValueError) as exc:
        payload = getattr(exc, "payload", {}) or {}
        return {"error": str(exc), **{key: value for key, value in payload.items() if key != "error"}}


@mcp.tool()
def validate_ibans(ibans: list[str]) -> list | dict:
    """Validate IBANs: country format, length and MOD-97 checksum.

    Works without an API key for up to 10 IBANs per call (small daily allowance
    per IP). With IBANGEN_API_KEY set, paid plans also return the bank, BIC and
    SEPA Instant / Verification of Payee reachability. A valid result does not
    prove that an account exists.
    """
    return _call(api.validate_ibans, ibans)


@mcp.tool()
def generate_test_ibans(country: str, quantity: int = 1, bank: str | None = None, seed: str | None = None) -> list | dict:
    """Generate synthetic, checksum-valid test IBANs for QA and development.

    `country` is a country name such as "Germany" or "UK". `seed` makes the output
    repeatable. Without IBANGEN_API_KEY up to 10 country-level IBANs a day per IP
    (bank fields hidden); a free key gives 100 API calls a month. `bank` targets one
    bank and needs a paid key. Output is test data only and must never be used for payments.
    """
    return _call(api.generate_test_ibans, country, quantity, bank=bank, seed=seed)


@mcp.tool()
def lookup_bank(value: str, identifier_type: str = "bic") -> dict:
    """Resolve a BIC or domestic bank identifier to registry records with sources.

    Requires IBANGEN_API_KEY on a plan that includes bank intelligence.
    """
    return _call(api.lookup_bank, value, identifier_type)


@mcp.tool()
def generate_us_test_accounts(quantity: int = 1, seed: str | None = None) -> dict:
    """Generate 1–10 free US routing/account test rows using an API key.

    Accounts are synthetic; routing references do not establish live payment
    eligibility. No bank reveal, paid targeting or profile generation is requested.
    A seed makes results reproducible. Never use these values for payments.
    """
    return _call(api.generate_us_test_accounts, quantity, seed)


@mcp.tool()
def validate_us_routing_numbers(routing_numbers: list[str], confirm_api_credits: bool = False) -> dict:
    """Check 1–10 US routing numbers against the existing metered registry API.

    Requires a qualifying API key/plan. Ask the user to approve spending up to one
    API credit per distinct number before setting confirm_api_credits=True.
    Returns source observations, not account existence or proof of ACH eligibility.
    This is not the free web preview. Do not automatically retry a failed call.
    """
    return _call(api.validate_us_routing_numbers, routing_numbers, confirm_api_credits=confirm_api_credits)


@mcp.tool()
def lookup_us_routing_number(routing_number: str, confirm_api_credit: bool = False) -> dict:
    """Look up a 9-digit US routing number with the existing API entitlement gates.

    Ask the user to approve one API credit before confirm_api_credit=True. Preserve
    leading zeros. Registry evidence does not prove account existence or current
    ACH/Fedwire eligibility. Do not automatically retry a failed metered call.
    """
    return _call(api.lookup_us_routing_number, routing_number, confirm_api_credit=confirm_api_credit)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
