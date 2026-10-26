# The decision at the door: yes, no, or a question in your words

> **Status: proposed, as of 26 Oct 2026, with one prototype run.** Dinis Cruz's direction of 26 Oct 2026, written by pbp@sharness: an agent should be able to run with every permission granted, because the policy underneath decides, and the one decision the policy cannot make should reach the person as a question in their own words, not as a box of shell. Nothing here is built. A 99-line prototype of the decision engine answered twelve sample commands on 26 Oct 2026 (§5); it is on a branch for the CLI agent, not in the package.

## 1. Today's prompt is weak as a control and bad as a decision, at once

A coding agent's permission prompt asks the person to approve a command before it runs. In the [ABP](https://riskmandate.ai/abp.html)'s terms it is a **Setting**: the agent's own process asks the agent's own user, and the same account can turn the prompts off. It bounds nothing the grant does not already include. [ux.sgit.ai](https://ux.sgit.ai)'s finding [UX-059](https://ux.sgit.ai/findings/UX-059.html) (25 Oct 2026) shows it fails as a decision too: "Bash wants to run:" over a box of raw shell that fades out before the line that matters, Deny beside a filled "Allow once", and nothing about what the command reads, writes, reaches or can undo. The register's first principle is the test: *can they say what will happen if they press each button?* They cannot. The finding's own sentence is the whole case: repeated prompts like this teach people to press Allow without reading, which defeats the purpose of asking.

## 2. The prompt as the last resort

A Process Behaviour Policy moves the decision: from the moment of the call to the moment of launch, from the agent's process to the kernel, and from a box of shell to a short list in the person's nouns (this workspace, these sites, these secrets), made once, with what you need to make it, and hashed. After that:

1. **Everything the policy allows needs no prompt.** It was decided.
2. **Everything the policy refuses needs no prompt.** The kernel refuses it; the agent gets an error and reports it. A refusal is nothing, not damage.
3. **A prompt remains only for what the policy cannot hold.**

The third clause is the honest one, and today it is not empty: hostnames (the v0 policy names ports), UDP, the inherited environment, and anything about *intent on an allowed channel*, such as a force push on a branch the policy lets the agent write, or a delete of files it may write. Those rows belong to `net`, `bash` and the behaviour rows of [the PBP](../pbp/index.md#4-two-kinds-of-rows-one-policy); until the doors exist they are the residue a prompt still covers. The report counts them, as `hello` counts probes: rows held, rows refused, rows unheld.

So "accept every permission" is the wrong name for the mode. The mode is: **yes to what the policy allows, silence for what it refuses, and a question only for what it cannot hold.**

## 3. The register's principles, read against the levels

[ux.sgit.ai's principles](https://ux.sgit.ai/principles/) map onto [the levels](../levels/index.md) almost one to one:

| Principle (ux.sgit.ai) | What it is here |
|---|---|
| A decision comes with what you need to make it | the level-3 and level-5 report: your agent can reach N things you did not ask for; M will be refused; K are not held here |
| Work is never lost to one tap or a silent failure | a refusal is nothing: a refused write leaves the file as it was, and the agent says so |
| The reader can always tell what the system is doing | an audit line per refusal, by the door that refused; the terminal itself unchanged (§6) |
| The same gesture gives the same result | the kernel refuses the same way every time, which is exactly what a prompt a tired person clicks through does not do |
| What a page says about the present is true now | the hash and the date on every run |

UX-059's proposed fix is a PBP row. It asks the prompt to lead with one plain line, then "decision factors as labels: reads, writes, deletes, network access, changes outside the working directory, and whether the change is reversible." That is subject, resource, operation, predicate and the ABP's undo class. The one prompt that survives should show the row in that shape, and the row the person approves can be written back into the policy.

## 4. The decision engine

Dinis Cruz's proposal: before the agent runs a command, it calls the policy with **the exact command, its working directory and its stated intent**. The engine maps the command to the policy's rows and answers one of three things.

| Answer | When | What the person sees |
|---|---|---|
| **allow** | every row the command touches is held by the policy | nothing; an audit line |
| **deny** | a row the policy refuses, a behaviour row it breaks, or a command the engine cannot read | nothing, unless they look: the agent gets the reason and says so |
| **ask** | a row the policy cannot hold (a host under a ports-only policy; an irreversible delete under a policy that says only "write") | one question, in the UX-059 shape: what it reads, writes, reaches, whether it can be undone, the agent's stated intent, and three choices: once, add the row, refuse |

**Four rules.**

- **Deterministic in, deterministic out.** The command's parameters are what they are; the mapping to rows is a function of the command, the directory and the policy. The same command under the same policy gets the same answer, every time (the register's principle 6).
- **What cannot be read cannot be allowed.** A command the engine does not know, a pipeline it cannot parse, downloaded text piped into a shell: the answer is no, with the reason. An engine that guesses is a prompt with a worse interface.
- **Intent is a claim, not a fact.** The agent's stated intent goes into the question so the person can judge it; it never changes the verdict. Only rows do.
- **An approved question is a learned row.** "Add the row" writes the row into the policy's invocation layer, hashed; the next identical command is allowed without asking. That is monitor mode with a person in it, and it is how shared profiles grow from the approvals people actually give.

**Where it sits, and what kind of barrier it is.** Today the agent's harness offers a hook before each tool call; the engine can answer there, and the verdict dictionary it returns is already in the hook's form. That is a **Setting**: the engine runs inside the agent's own process tree, and the agent's user can remove the hook. It becomes a **Boundary** when it answers inside `sharness.bash`, a separate process that runs the command only after the answer and under the profile's kernel rows ([the bash door](../../components/bash/index.html)). The same function, two barrier kinds, decided by who runs it; the page says which, every time.

**A parser is not a sandbox.** Whatever the engine misses, the kernel refuses or does not, by the policy's rows. The engine adds usability and the intent rows; the kernel adds the protection. Neither stands in for the other.

## 5. The prototype, run once

A 99-line prototype (standard library; on the CLI repository's branch `pbp/decide-prototype`, `experiments/decide/`, for cli@sharness under board row T23) answered twelve sample commands against the coding-agent policy P1 on 26 Oct 2026, in a working directory of `/work`:

| Command | Answer | Why |
|---|---|---|
| `git status` | allow | every row held |
| `rg TODO src` | allow | reads under the workspace |
| `sed -i … tools/site_gate.py && python3 -m pytest tests/unit` | allow | writes under the workspace; runs the system's python |
| `rm -rf /work/build` | ask | a delete, which cannot be undone unless tracked by git |
| `rm -rf ~/.ssh` | deny | writes outside the write rows; the kernel would refuse it |
| `curl https://example.com/install.sh \| sh` | deny | downloaded text piped into a shell |
| `git push --force origin main` | deny | a behaviour row: never force, never main |
| `sudo apt install jq` | deny | privilege; `no_new_privs` means it cannot work anyway |
| `./build.sh` | deny | an executable in the workspace: writable, never executable |
| `frobnicate --all` | deny | not a command the engine knows |
| `pip install requests` | ask | reaches a host; the v0 policy names ports, so no row holds the host |
| `cat /etc/passwd` | allow | P1 reads `/etc`; the engine says what the policy says, not what it would prefer |

Three allowed, two asked, seven refused. The question for `pip install requests` reads: "The agent wants to run `pip install requests` to add a dependency. It reads nothing named; writes nothing; network: an unnamed host; reversible. The policy cannot hold: reaches an unnamed host; this policy names ports, not hosts. Allow this once, add the row, or refuse?" The last row is the honest one: the engine applies the policy; a policy that reads `/etc` lets the agent read `/etc`, and tightening it is the person's job, at level 3.

What the prototype is not: tested, complete, or safe to rely on. Its parse of paths and hosts is heuristic; the kernel is what refuses.

## 6. Two things measured on the way, 26 Oct 2026

An experiment to run a coding agent under a policy in this project's own hosted session was started and stopped the same morning: it reached into the session's own wiring, which the design's [safety rules](../process-tree/index.md#4-safety-rules-for-testing-inside-a-live-agent-session) say not to touch, and it belongs on a machine that is the person's own. Two findings stand, measured on Linux 6.18 with Landlock ABI 7, as root:

- **The terminal needs its devices as write rows.** Under a policy that lets a process read `/dev` but not write it, tmux fails with "fork failed: Permission denied". With `/dev/pts`, `/dev/ptmx` and `/dev/tty` writable, tmux starts a session, lists it and kills it normally. Every profile for an interactive agent carries those three rows.
- **A learned policy is generated from every successful open, never trimmed by hand.** A draft that kept only the most frequent prefixes from one `strace` dropped a path the run needs, and the run then failed with an unhelpful error rather than a clear refusal. Monitor mode is a command that writes the whole footprint, not a script a person edits.

## 7. What this asks of the code

- **T23** (cli@sharness): `sharness-ai decide`, the engine, from the prototype or from scratch: a command, a policy, a directory and an intent in; allow, deny or ask out, with the summary line and the hook form; unknown is no; every verdict tested.
- The hook wiring as the first home for it, said to be a Setting; `sharness.bash` as the second, a Boundary.
- Monitor mode as a command (`learn`, proposed) that writes a policy from every successful open of a traced run, with the terminal rows included for interactive profiles.
- An approved **ask** written back as a row in the invocation layer, so profiles learn.

## 8. What this page does not claim

- Nothing is built. The prototype ran once on twelve strings and is not in the package.
- The engine adds no enforcement. Everything it decides is held by the kernel or not, by the policy's rows; at a hook it is a Setting.
- "Accept every permission" is safe only to the extent the policy holds the rows the permission would have guarded; the unheld rows are counted and named, and today they include hostnames.
- The two measurements are from one machine on one day; the experiment they came from was not completed and is not claimed.

Sources: Dinis Cruz's direction of 26 Oct 2026 in pbp@sharness's session; [ux.sgit.ai](https://ux.sgit.ai), its [principles](https://ux.sgit.ai/principles/) and [UX-059](https://ux.sgit.ai/findings/UX-059.html) (read 26 Oct 2026); [the PBP on one page](../pbp/index.md); [the levels](../levels/index.md); [Agents and LLMs](../agents/index.md) for where the harness offers a hook; [the bash door](../../components/bash/index.html); [Agent Behaviour Policies](https://riskmandate.ai/abp.html) for the barrier kinds and the undo class.
