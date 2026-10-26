Rule followed: outreach §3.1 (three seeded threads); AGENTS.md §1 (status words).

**Category:** General · **Pin:** yes

# Which sandbox do you run your agent in, and what does it not cover?

I'm Dinis, SHarness's author. Most agents I see run with their owner's whole account: every file, every credential in the environment, every host on the network. Some run under Claude Code's sandbox, bubblewrap, Docker, a microVM, or nothing at all.

The [enforceability matrix](https://sharness.ai/landscape/enforceability/index.html) is our attempt to say, row by row of a policy (files, network, exec, memory, processes, secrets, the model API), which sandbox can hold the row and as what kind of barrier. `sharness-ai policy translate FILE --to bwrap|docker|claude-code|kubernetes` writes the same policy in each target's form and prints what the target cannot enforce.

What we'd like to know from you:

1. Which sandbox, and why that one?
2. Which rows of the matrix are wrong for it, in your experience?
3. What did it fail to stop, or what did it stop that you needed?

Everything here is at the experiments stage; nothing in the design is built yet, and [the status page](https://sharness.ai/evidence/status/index.html) says exactly what exists.
