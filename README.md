# ibangen-mcp

<!-- mcp-name: io.github.offx366/ibangen-mcp -->

Official MCP server for [IBANgen](https://ibangen.com), the IBAN generator and validator for payment testing.

MCP server that gives AI agents IBANgen tools for IBAN and US bank account test data.

| Tool | Key needed | What it does |
|---|---|---|
| `validate_ibans` | No (10 IBANs per call, small daily allowance per IP) | Country format, length and MOD-97 checksum. Paid keys add bank, BIC and SEPA Instant / VoP reachability. |
| `generate_test_ibans` | No for country-level IBANs (10 a day per IP); a key for more and for bank targeting | Synthetic, checksum-valid test IBANs; optional `seed` and bank targeting (paid key). |
| `lookup_bank` | Yes (bank-intelligence plan) | BIC or domestic identifier to registry records with sources. |
| `generate_us_test_accounts` | Yes (free key is sufficient) | 1–10 US routing/account test rows; optional reproducible seed; no paid reveal or targeting. |
| `validate_us_routing_numbers` | Yes (qualifying registry plan) | 1–10 routing numbers through the existing metered registry API; requires explicit approval of up to one API credit per distinct number. |
| `lookup_us_routing_number` | Yes (existing API entitlement gates) | Source-backed routing lookup; requires explicit approval of one API credit. |

For assistants without MCP, the same product map is published as plain text at
https://ibangen.com/llms.txt and https://ibangen.com/llms-full.txt.

Generated IBANs are test data only. A valid IBAN does not prove that an account exists.
US account numbers are synthetic; routing references do not establish live ACH,
Fedwire or account eligibility. The metered US tools do not replace the free web
preview and do not bypass bank metadata gates. They never automatically retry a
transport failure, because a credit may already have been consumed.

## Remote server (nothing to install)

Add `https://ibangen.com/api/mcp` as a custom connector in ChatGPT, Claude, Cursor or VS Code
(Streamable HTTP, no key needed to start; send `Authorization: Bearer <API key>` for paid-plan limits).
It offers `validate_ibans`, `generate_test_ibans`, `bank_test_ibans` (free sample IBANs, BIC and bank
code of one bank), `iban_format` and `calculate_iban`.

```bash
claude mcp add --transport http ibangen https://ibangen.com/api/mcp
```

## Install the local server

```bash
pip install ibangen-mcp
```

## Claude Desktop / Claude Code

```json
{
  "mcpServers": {
    "ibangen": {
      "command": "ibangen-mcp",
      "env": { "IBANGEN_API_KEY": "optional_for_validation_and_10_ibans_a_day" }
    }
  }
}
```

Cursor uses the same block in `.cursor/mcp.json`. Get a free key (100 API calls a month) at https://ibangen.com/account?focus=api.

The same API is also sold on [RapidAPI](https://rapidapi.com/offx366/api/iban-us-bank-account-test-data-api) (IBAN plus US bank account and routing test data).

`IBANGEN_API_BASE_URL` overrides the default `https://ibangen.com/api/v1`.
