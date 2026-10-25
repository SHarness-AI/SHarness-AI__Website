---
title: A secure harness for agents: behaviour policies enforced from outside the agent, one small component at a time, starting with my own Claude sessions
date: 2026-10-24
author: Dinis Cruz
author_url: https://sgit.ai/about/
summary: SHarness is the natural next step from the work we have done on agent behaviour policies. An Agent Behaviour Policy describes what an agent should do; a Process Behaviour Policy is that same policy executed, put underneath the agent as a stronger harness, and run from outside the agent's environment, so the agent cannot simply decide to ignore it. That is where the name comes from: a secure harness, the layer that lets agents run securely. It is an open source project, and the way I would like to build it is to start with very simple examples and with each component done in isolation: a network component, a KMS component, a file component and an LLM component, each a very small service, together deciding where the private keys live, where the model's calls go, and where the execution flow and the business logic are controlled. It started this morning, as a way to stop sgit from holding vault keys in clear text, and that evolution is part of the story. The first users will be my own Claude sessions, and then sgit and the agents that use it all day, including the newsroom's agents, which run around the clock and read a lot of dangerous data. It should be as generic as possible, maybe even a skill, and its key principle is to lock down the capabilities and the permissions Claude has, with file behaviour policies and network behaviour policies as extensions of the same idea. Someone running a hello world with Claude should be able to start it and know that the agent cannot reach the internet or write where it should not. The real power comes when a cloud provider runs some of these components as a service. And on a laptop, disposable users per session already change how safe it is to let an agent run a process.
version: v0.3.0
license: https://creativecommons.org/licenses/by/4.0/
tags: [sharness, secure-harness, agent-security, process-behaviour-policy, agent-behaviour-policy, file-behaviour-policy, network-behaviour-policy, claude, sgit, open-source, article]
status: published
---

![From a policy the agent reads to a policy the agent runs inside. On the left, an Agent Behaviour Policy: the rules are text in the agent's context, and the agent itself decides whether to follow them, so a prompt injection can talk it out of them. On the right, SHarness: the same rules, written as a policy whose hash the person supplies, enforced from outside the agent by a launcher that starts four small components, network, KMS, file and LLM, each under its own disposable user and its own policy. The agent sits inside, with no keys, no direct network and no write access of its own; every request it makes goes through one of the components.](/articles/images/secure-harness-for-agents.svg)

*From a policy the agent reads to a policy the agent runs inside. On the left, an Agent Behaviour Policy: the rules are text in the agent's context, and the agent itself decides whether to follow them, so a prompt injection can talk it out of them. On the right, SHarness: the same rules, written as a policy whose hash the person supplies, enforced from outside the agent by a launcher that starts four small components, network, KMS, file and LLM, each under its own disposable user and its own policy. The agent sits inside, with no keys, no direct network and no write access of its own; every request it makes goes through one of the components.*

## In short {#in-short}

- **SHarness is behaviour policies executed, not just written.** An Agent Behaviour Policy describes what an agent may do; a Process Behaviour Policy is enforced underneath the agent, from outside its environment. Status: designed, not built.
- **The name is the idea: a secure harness.** The layer agents run inside so that they run securely.
- **Start small and separate.** Very simple examples first, and each component (network, KMS, file, LLM) built and tested in isolation, in one CLI project for now.
- **Each component is a very small service** that decides one thing: where the private keys live, where the model's calls go, where files are written, where the business logic is checked.
- **It started this morning with sgit,** as a way to stop vault keys being held in clear text, and grew from there.
- **The first users are my own Claude sessions,** then sgit and the agents that use it all day, including the newsroom's, which read a lot of dangerous data.
- **Generic on purpose.** Useful to anyone running an agent, maybe even as a skill, with its key principle being to lock down what Claude can do.
- **File and network behaviour policies** are the next extensions of the same idea. Proposed.
- **A hello world should show it working:** the agent cannot reach the internet or write where it should not, because SHarness is inline.
- **On a laptop, disposable users per session** are the part I find most powerful today: measured at about 49 ms each, in one environment.

## From agent behaviour policies to a harness {#progression}

I see SHarness as the natural progression from the work we have done on [agent behaviour policies](https://riskmandate.ai/abp.html). An Agent Behaviour Policy is a description: what the agent is mandated to do, what it can technically do, the gap between the two, and what stands in the way of each capability. Most of what stands in the way today is the agent itself, reading its instructions and choosing to follow them.

What we are doing now is executing those policies. We call them [Process Behaviour Policies](../design/policies/index.md): the same model, applied to the processes an agent runs, and enforced by something above the agent instead of by the agent. That gives us a stronger harness around what the agent is doing. More importantly, it allows the policy to be executed from outside the agent's environment, which is what makes it binding. A lock the agent applies to itself is a setting it can undo; a lock applied from outside is a boundary.

That is the name of the product: a secure harness. It is the layer that agents run inside so that they can run securely.

## Small, simple, and one component at a time {#small}

This is an open source project, and I think it is very important to start with very simple examples, and with each of the components done in isolation. We might end up with separate CLI projects for some of them; for now, they can all live in [one](https://github.com/SHarness-AI/SHarness-AI__CLI).

The components are:

- **a network component**, the only thing that talks to the outside;
- **a KMS component**, the only place private keys exist;
- **a file component**, the only thing that writes to the folders that matter;
- **an LLM component**, the only thing that talks to the model.

Each of them is a very simple service. Together they give the model a layer of isolation, and give us a layer of security in the places that matter: where the private keys are, where the LLM calls go, where the execution flow runs, and where the business logic is actually controlled. The design for each is on [Components](../design/components/index.md); none of them is built yet.

## Where it started, this morning {#origin}

Historically, and by that I mean this morning, it started with sgit, our encrypted version of git. The question was how to stop sgit from ever holding a vault key in clear text. A key handed to an agent was sealed while it travelled and exposed the moment it arrived: written to a file, passed on the command line, kept in the clone's folder. I wrote that up in [A vault key that never lands](https://cli.sgit.ai/articles/a-vault-key-that-never-lands.html), and the design that followed split sgit into small components, each under its own policy.

Nothing in that design turned out to be specific to sgit. That evolution is part of this project, and it is all published: the article, the requirements and the side-by-side review on cli.sgit.ai, its [design pack for sgit](https://cli.sgit.ai/dev/sealed-vault-keys/index.html), and the [SHarness design pack](../project/sources/index.md) that generalised it.

## The first users {#first-users}

The first real use case is my own normal Claude sessions. The second is sgit, and the agents that now use sgit all the time.

We already have a whole bunch of agents running around the clock, the newsroom's agents in particular, and those agents now need to be controlled. They are an interesting case, because they are exposed to a lot of dangerous data: pages, feeds and documents written by people we do not know, any of which can carry instructions. That is exactly the situation where a policy the agent merely reads is not enough.

## Generic, and as locked down as possible {#generic}

I think this will be useful to a lot of people, so the plan is to make it as generic as possible. It could even be a skill, or something that simple, that you add and that really locks things down.

One of the key principles is to lock down the capabilities and the permissions that Claude has. The way we design this can make a big difference here, especially with Process Behaviour Policies, and I think we should expand them: **file behaviour policies** and **network behaviour policies**, as extensions of the same idea. A behaviour policy defines what we want to happen; a file behaviour policy defines what we want to happen to the file system, and a network behaviour policy what we want to happen on the network. Today those are names for a direction, not a specification.

## Slim first, then harden {#slim}

What I have in mind is to make it as simple as possible, as fast as possible and as slim as possible, then figure out how we harden it, then test it, and see how the flow works in practice.

The test I would like it to pass is the simplest one. Somebody doing a hello world with Claude should be able to run it, and then know that, at that moment, the agent cannot connect to the internet, cannot write to the file system, and cannot make all sorts of other requests, because SHarness is now inline, in the middle of every one of them.

## The power of running it as a service {#service}

The real power comes when some of this runs as a service: on Cloudflare, on AWS, or with another cloud provider, where some of these actions can be offloaded. That makes it even more secure, because a lot of our controls and limitations can be applied there, outside the machine the agent is running on. It will be an interesting workflow to see in practice. Today this is a proposal; no such service exists.

## Protecting Claude on your laptop {#laptop}

The fundamental point is to let people protect Claude, and I would say especially Claude running locally on a laptop. What I think is super powerful in what we are doing is that we are creating disposable users per session: every component, and every sandbox, gets its own user that exists for that session and is gone after it. That really ramps up the security of running a process that an agent controls.

## What this does not claim {#limits}

- **Nothing here is built.** The components, the policies and the launcher are designed; the [evidence](../evidence/index.md) is a set of probes and timings from one environment on one day.
- **It does not protect against root or the kernel.** The design trusts the kernel; anything with root on the machine can read a process's ordinary memory.
- **File and network behaviour policies are not specified.** They are the direction this memo sets; the Process Behaviour Policy schema is the only one written down.
- **The cloud service is a proposal.** No provider offers it, and nothing here describes any provider's plans.
- **"Disposable users in about 49 ms" is one measurement,** averaged over ten runs in one cloud agent workspace on 24 October 2026; a laptop will differ.
- **"Maybe even a skill" is an idea, not a design.** How a skill could apply locks that bind the agent that loads it is an open question, because locks the agent applies to itself are only settings.
- **The newsroom's agents are not yet running inside it.** They are the use case, not a user.

If you run agents that read untrusted data and would like to try a small piece of this first, write to [agent@riskmandate.ai](mailto:agent@riskmandate.ai).

## Where this comes from {#sources}

A voice memo of mine on 24 October 2026, [published in full](../project/sources/memos/2026-10-24-memo-01-secure-harness.md) as Otter transcribed it, written up in my voice by sharness.build, this site's build agent, in the same session that built the site; the editorial responsibility is mine. Sources: [Agent Behaviour Policies](https://riskmandate.ai/abp.html) on riskmandate.ai; [A vault key that never lands](https://cli.sgit.ai/articles/a-vault-key-that-never-lands.html) and the [sealed vault keys design pack](https://cli.sgit.ai/dev/sealed-vault-keys/index.html) on cli.sgit.ai; the SHarness design pack on this site, under [the source documents](../project/sources/index.md); [Every site its own articles](https://send.sgit.ai/articles/every-site-its-own-articles.html) on send.sgit.ai for the format. The one number, 49 ms for an ephemeral user, a firewall rule, a locked launch and a teardown, averaged over 10 runs, is from [Evidence](../evidence/index.md#4-process-isolation), section 4. Two phrases in the transcript were not clear enough to use and are left out: a qualifier on "the newsroom" and a sentence beginning "VCS will become an inline process".
