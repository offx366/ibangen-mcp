# ibangen-mcp

<!-- mcp-name: io.github.offx366/ibangen-mcp -->

Official MCP server for [IBANgen](https://ibangen.com), the IBAN generator and validator for payment testing.

MCP server that gives AI agents three IBANgen tools:

| Tool | Key needed | What it does |
|---|---|---|
| `validate_ibans` | No (10 IBANs per call, small daily allowance per IP) | Country format, length and MOD-97 checksum. Paid keys add bank, BIC and SEPA Instant / VoP reachability. |
| `generate_test_ibans` | Yes | Synthetic, checksum-valid test IBANs; optional `seed` and bank targeting. |
| `lookup_bank` | Yes (bank-intelligence plan) | BIC or domestic identifier to registry records with sources. |

Generated IBANs are test data only. A valid IBAN does not prove that an account exists.

## Install

```bash
pip install ibangen-mcp
```

## Claude Desktop / Claude Code

```json
{
  "mcpServers": {
    "ibangen": {
      "command": "ibangen-mcp",
      "env": { "IBANGEN_API_KEY": "your_key_optional_for_validation" }
    }
  }
}
```

Cursor uses the same block in `.cursor/mcp.json`. Get a key at https://ibangen.com/apidoc#auth.

`IBANGEN_API_BASE_URL` overrides the default `https://ibangen.com/api/v1`.
