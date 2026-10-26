Rule followed: outreach §3.1; the brief's criterion 2; the spectrum page (P2, a tool server, is the nearest profile).

**Title:** P5: an example policy for an MCP server over stdio · **Labels:** good first issue, policy

The example policies go from P0 (a hello world) to P4 (sgit). The thing most people would put under a harness first is an MCP server: a process started by the agent, talking over stdio, reading one directory, reaching nothing on the network (or one host).

**Where to look:** `experiments/policies/p2-tool-server.json` (the shape); `sharness_ai/policy.py` (what `policy check` validates); the examples page on the site for how each policy is described.

**What done looks like:**

- `experiments/policies/p5-mcp-server.json`: reads its own directory and the one it serves, writes nothing (or one scratch folder), no TCP, a memory cap and a process cap that fit a Python or Node server, in the v0 shape.
- `sharness-ai policy check` accepts it and `sharness-ai policy hash` prints its hash; both in a unit test.
- `sharness-ai run --policy experiments/policies/p5-mcp-server.json -- <a real MCP server you have>` either runs it, or refuses with a message that says which row refused: write one paragraph on which, with the kernel and the date, in the pull request. That paragraph is a measurement and goes on the site's Evidence page.
