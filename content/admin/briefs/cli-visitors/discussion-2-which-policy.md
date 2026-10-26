Rule followed: outreach §3.1; the design's Policies page (the v0 shape).

**Category:** Ideas · **Pin:** yes

# What policy would you want to express for a tool, an MCP server, or an agent?

A v0 Process Behaviour Policy is a small JSON file ([the examples](https://github.com/SHarness-AI/SHarness-AI__CLI/tree/dev/experiments/policies): a hello world, an agent session, a tool server, a newsroom agent, sgit): which paths may be read and written, which TCP ports reached, how much memory, how many processes, and the hash a person supplies so the agent cannot widen it. `sharness-ai run --policy p.json -- cmd` enforces it with Landlock, seccomp, namespaces and cgroups on Linux.

The shape is deliberately small and it is missing things. Tell us what a real tool of yours needs that it cannot say:

- hosts by name rather than ports (the design puts that in `sharness.net`, not the kernel)
- UDP, unix sockets, signals (Landlock's newer ABIs have some of these)
- a secret the tool needs but must never print
- a budget: tokens, time, calls
- anything else

The best answer is a policy file for something you actually run, with the rows it cannot express marked. Those become the next version of the schema, credited.
