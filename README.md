Copyright © 2026 Lewis James Seals Jr. All rights reserved.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT.

# Brute Genius

Exhaustive combinatorial search as an MCP server. Given a discrete search space, Brute Genius enumerates the full Cartesian product, shards it across a fleet of accelerators, scores every combination against a named objective, and returns a ranked list. It does not sample or prune; it tries everything.

**Warning: this plugin spends real money fast.** Always call `brute_genius_plan` first and respect the cost ceiling it returns. `brute_genius_kill` is the emergency stop.

## Connect to Claude Desktop

1. Install dependencies:

```bash
cd brute-genius
pip install -e ".[test]"
```

2. Add the server to Claude Desktop’s MCP configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "brute-genius": {
      "command": "python",
      "args": ["/absolute/path/to/brute-genius/server.py"]
    }
  }
}
```

3. Restart Claude Desktop. The tools `brute_genius_plan`, `brute_genius_launch`, `brute_genius_status`, `brute_genius_results`, `brute_genius_kill`, and `xpu_probe` will appear, along with the resources and prompts.

For other clients (Cursor, Copilot, etc.) point the MCP host at the same `python /absolute/path/to/server.py` stdio command. For remote/HTTP use:

```python
mcp.run(transport="http", host="0.0.0.0", port=8000)
```

## Quick test

```bash
pytest test_server.py -v
npx @modelcontextprotocol/inspector python server.py
```

## Safety guarantees

- `plan()` refuses any estimate above `max_cost_usd`
- Hard caps: 64 nodes, 10⁹ combinations
- Objectives are registry-only; caller code is never executed
- `kill()` always stops every node associated with a plan_id
