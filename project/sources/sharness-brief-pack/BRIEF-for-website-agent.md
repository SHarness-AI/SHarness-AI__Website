# Brief: the SHarness website (sharness.ai)

**From:** Dinis Cruz, with the design session that produced the documents in `docs/` (24 Oct 2026, written up by Claude).
**For:** the agent managing `SHarness-AI__Website`.
**Status of the project:** design. **Nothing is built yet.** Some numbers were measured in a live agent sandbox; everything else is a proposal. The site must keep that distinction visible.

---

## 1. Identity

| Item | Value |
|---|---|
| Brand | **SHarness** (capital S, capital H) |
| Domain | https://sharness.ai |
| GitHub org | https://github.com/SHarness-AI |
| Code repo | https://github.com/SHarness-AI/SHarness-AI__CLI |
| Website repo | https://github.com/SHarness-AI/SHarness-AI__Website |
| PyPI | https://pypi.org/project/sharness-ai/ (distribution `sharness-ai`) |
| Component names | `sharness.<role>` — `.launcher`, `.kms`, `.net`, `.fs`, `.bash`, `.llm`, `.policy` |
| Command name | open — do not use plain `sharness` on the site as a command (see §6) |
| Disambiguation | SHarness is unrelated to *Sharness*, the shell testing library derived from Git's test suite (felipec/sharness). Say so once, plainly, on the home or about page |

## 2. What SHarness is (use this as the seed text)

**One line:** SHarness runs agents and their tools as small, single-purpose processes, each locked down by the kernel and talking only over allowed, mutually authenticated connections, so a secret lives in one place and a tricked process can only do its one job.

**One paragraph:** It started as a fix for one gap: a vault key handed to an AI agent was sealed while it travelled and exposed the moment it arrived, on disk, on the command line and in the agent's transcript. The fix turned out to be general. A launcher starts a few components — a key holder (`.kms`), the only network client (`.net`), the only writer of protected folders (`.fs`), a sandboxed shell (`.bash`) and the only client of the model API (`.llm`) — each under its own Process Behaviour Policy, enforced by Linux (separate users, Landlock, seccomp, namespaces, cgroups) and by mutual TLS between components. The person supplies the hash of the policy, so a prompt-injected agent cannot widen it. sgit (sgit.ai's encrypted vault CLI) is the first app to run inside it.

## 3. Source documents (in `docs/`)

| Doc | Gives the site |
|---|---|
| `00-README.md` | problem, goals, threat model, glossary, decisions, end state |
| `01-architecture.md` | the original four components, edges, mutual TLS with a session CA, command flows, deployment topologies, refactor path in sgit |
| `02-sealed-key-flow-and-kms.md` | the sealed handover end to end, the KMS protocol, where keys live and for how long |
| `03-process-behaviour-policy.md` | Process Behaviour Policies: ABP mapping, schema, layering, hashing/signing, enforcement map, learning a policy from traces, prompt-injection walkthrough |
| `04-environment-evidence.md` | every measurement, with method and caveats |
| `05-sharness.md` | the generalisation: naming, components, transparent vs harness-aware apps, minimal code |
| `06-llm-and-the-agent-loop.md` | how an agent message actually flows (observed), `.llm`, `.bash`, dual-LLM split, Claude API compatibility |
| `07-enforcing-the-process-tree.md` | making every process go through `.bash`; safety rules for testing; proof of concept **not yet run** |

Docs 01–04 use the earlier sgit-specific names (sgit-cli, sgit-fs, sgit-net, sgit-kms). On the site, use the SHarness names and note the mapping once: sgit-kms → `sharness.kms`, sgit-net → `sharness.net`, sgit-fs → `sharness.fs`, sgit-cli → the harnessed app.

## 4. Suggested site structure

| Page | Built from | Notes |
|---|---|---|
| Home | §2 above; 00 §1–2 | the one line, the problem picture, the component picture, status badge "design" |
| Why: the last metre | 00 §1, 02 §1 | the vault-key story; the transcript as the biggest leak |
| Architecture | 05 §2, 01 §1–3 | components, edge matrix, mutual TLS, session CA |
| Components | 05 §1, 01 §2, 06 §3–4 | one section per `sharness.<role>` |
| Keys and the KMS | 02 | sealed flow, protocol, key lifetime options |
| Process Behaviour Policies | 03 | links to riskmandate.ai's Agent Behaviour Policy |
| Agents and LLMs | 06 | how a message flows; where SHarness plugs in; Claude API compatibility |
| Enforcing the process tree | 07 | mark the PoC as not yet run |
| Evidence | 04 | all numbers, each with method and date |
| Roadmap and open decisions | 00 §5, §7 below | |
| About / naming | §1, §6 | includes the disambiguation line |
| `llms.txt` and `.md` twins | all | follow the cli.sgit.ai pattern: every page also as `.md`, generated from the same source; an `llms.txt` index for agents |

Diagrams: the docs use ASCII. Keep them as ASCII in the `.md` twins; redraw as SVG for the HTML pages only if the redraw shows the same mechanism.

## 5. Claims: what the site may say

**Measured (24 Oct 2026, one Claude agent workspace — say so):**
- mutual TLS handshake between components ≈ 3.2 ms; three per command ≈ 10 ms, against 146 ms of sgit imports and ~108 ms of key derivation already paid
- session CA + four role certificates: 24 ms
- edge enforcement by certificate role: allowed and denied exactly per the matrix
- ephemeral user + firewall rule + locked launch + teardown: ~49 ms; new namespaces: ~4 ms
- `memfd_secret` page unreadable even by root via `/proc/<pid>/mem` (EIO); freezing the KMS 0.28 ms, thawing 0.13 ms
- Landlock file and port rules, no-fork limit, dropped capabilities: all enforced as expected
- sgit 0.24.0 facts: private keys at PBKDF2 2,048 iterations; `sgit --version` opens 1,104 files and loads 529 modules

**Proposal (say "designed", "proposed", "will"):** everything about components' behaviour, the KMS protocol, policies, `.llm`, `.bash`, deployment topologies.

**Not yet measured (say so):** seccomp filters, read-only bind mounts, all the side doors in 07 §2.2, AWS KMS compatibility.

**Never claim:**
- that anything is built or released;
- protection against root or kernel compromise (the threat model trusts the kernel; root can read process memory);
- anything about Anthropic's, OpenAI's or any platform's plans. The "platform provides the KMS" section is a proposal for what platforms should offer;
- that a schema bounds intent (it bounds shape).

## 6. Naming rules for the site
- Brand is **SHarness**. Lower-case `sharness` only in code identifiers (`sharness.kms`, `sharness_ai`).
- Don't present `sharness` as a shell command: on Debian, pkgsrc and OpenBSD that name is the unrelated shell test library's package. The command name is an open decision (candidate: `sharness-ai`).
- Proposed environment variable prefix `SHARNESS_AI_`, not `SHARNESS_` (used by the other project).
- Include the disambiguation line once.

## 7. Open decisions (show on the roadmap page)
1. Command name.
2. Full split (`.net` holds derived keys and does all vault crypto) vs. step 1 (`.net` filters; the app gets derived keys sealed to its own one-time key).
3. Remote KMS backend; verify AWS KMS RSA-4096 OAEP-SHA-256 matches sgit's envelope.
4. `.fs` as a process owning the folder vs. a FUSE mount.
5. Who runs the launcher: the agent (locks are only "Settings" for the agent), a local script, or the platform (end state).
6. Run the process-tree proof of concept (07) and publish its results.

## 8. Handling the observations of Claude's environment
Doc 04 §7 and doc 06 §1 describe what was observed inside a Claude agent workspace (process names, versions, the model endpoint, environment variable *names*). They are fine to publish as **dated, read-only observations**, framed as "observed on 24 Oct 2026; may differ elsewhere". No credentials, session identifiers or traffic contents were captured; keep it that way, and don't add speculation about how Anthropic's platform works beyond what the docs state.

## 9. Related sites to link
- The origin article: https://cli.sgit.ai/articles/a-vault-key-that-never-lands.md
- The handover the design builds on: https://pki.sgit.ai/handover.md
- Agent Behaviour Policies: https://riskmandate.ai/abp.html
- sgit: https://cli.sgit.ai

## 10. First tasks
1. Set up the site skeleton with the pages in §4, `.md` twins and `llms.txt`.
2. Write the home page from §2 with the status badge.
3. Port docs 05, 06 and 01 first (they carry the architecture), applying the naming rules in §6.
4. Build the Evidence page from doc 04 with the labels in §5.
5. Add the roadmap page from §7.
6. Credit: "By Dinis Cruz. Design session written up with Claude, 24 October 2026."
