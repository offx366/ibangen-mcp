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
    repeatable. `bank` targets one bank (paid plans). Requires IBANGEN_API_KEY.
    Output is test data only and must never be used for payments.
    """
    return _call(api.generate_test_ibans, country, quantity, bank=bank, seed=seed)


@mcp.tool()
def lookup_bank(value: str, identifier_type: str = "bic") -> dict:
    """Resolve a BIC or domestic bank identifier to registry records with sources.

    Requires IBANGEN_API_KEY on a plan that includes bank intelligence.
    """
    return _call(api.lookup_bank, value, identifier_type)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
