# Telemetry: who reads this site

> **Status: live, as of 25 Oct 2026, 23:45 UTC.** Every page of sharness.ai carries `assets/telemetry.js` since v0.5.11. It sends one anonymous event per page per session to a write-only lane on a private vault, encrypted in your browser before it leaves. The lane was opened on 25 Oct 2026 at 23:40 UTC, once Dinis Cruz supplied the access token ([comms R10](../comms.html#r10), done); the first drain ran at 23:45 UTC and found 4 events from 2 sessions: 2 reader views, 2 from the agent's own headless check (classed `webdriver`, as designed), 1 declared team. Counts over readers only are published from the next drain on, once there are enough of them that no single reader can be picked out.

## What every page sends

One event, encrypted in your browser to the key below, written to a lane that can only be appended to:

| Field | What | Why |
|---|---|---|
| `path`, `ref` | the page, and the referrer's host (never the full referrer) | which pages are read; where readers come from (a Show HN, a LinkedIn post, a newsletter) |
| `country`, `region`, `city` | from a geolocation lookup your browser makes itself | where the readers are; the city and the region stay in the private vault |
| `lang`, `screen`, `tz` | language, phone or tablet or desktop, time zone | which devices, and a hint for telling automated browsers from people |
| `sid` | a random id made in the tab, kept in session storage | one event per page per session; sessions, not visitors |
| `ver`, `ts` | the site version and the minute | which release was read, when |
| `agent` | automation, by class only: a crawler's name, `webdriver`, `headless` | so crawlers and the site's own checks are counted apart from readers |
| `who` | `editor` or `team`, if this browser set it for itself (below) | so the team's own reading is counted apart from readers |

**Never sent, never stored by this site:** an IP address, a cookie, a name, a user-agent string, the page's full referrer URL. This site has no server of its own: there are no web server logs. The one party that sees your IP address is the geolocation service your browser asks (`ipapi.co`, then `ipwho.is` if the first does not answer), as with any request your browser makes; the event keeps three place names and nothing else. The vault server sees that a lane received something, its size and the time, and the requesting IP, as any server does.

**Do Not Track and Global Privacy Control are honoured:** with either set, your browser sends nothing, not even the location request. The script never blocks the page and fails silently.

## The credential, published on purpose

The write-only credential and the public key the event is encrypted to are in [`data/telemetry.json`](../../data/telemetry.json): the lane is vault `l3wltj3z` on `https://dev.send.sgraph.ai`; the recipient key is `sha256:7d3b264abdeadb20`. A write-only token can add rows and nothing else: it cannot list, read or delete. Only the holder of the telemetry vault's key can list the lane and decrypt what arrived; the enum key and the key pair's passphrase are derived from the vault key and never stored ([`tools/telemetry_postmaster.py`](../../tools/telemetry_postmaster.py), the newsroom's convention).

## Who is who

Not everyone who opens a page is a reader. Each session is put in one of three groups when the counts are made: **readers**; **the editor and the team**; **automation** (crawlers, the site's own headless checks). Automation declares itself by class; the team declares itself by opening any page of this site with `#who=editor` or `#who=team` once in a browser (kept in that browser only; `#who=reader` undoes it). Everything else is a reader. Every event is an untrusted claim: the token and the key are public, so rows can be forged or flooded (1000 pending per token, then the lane returns 507); readers with blockers do not appear. The counts are a floor.

## What will be published

Counts only, by day and by hour at the finest, over readers: pages, referrer hosts, countries, devices, languages, versions. No row, no session id, no city, no region. The drain ([`tools/telemetry_drain.py`](../../tools/telemetry_drain.py)), run by whoever holds the vault key, writes the report into the vault and its public part to [`data/telemetry-report.json`](../../data/telemetry-report.json) (the first one is there, dated); this page will render it once the counts are more than a handful. The first thing the counts are for is the [outreach plan](../outreach/index.md): which channel brought readers, and whether they read past the front page.

## Not applied yet

- A Content-Security-Policy on every page allowing exactly the two location services and the vault server, as the newsroom has. The playground and the Linux-in-a-browser demo load from their own folders and would need their own policy; proposed, not done.
- The report rendered on this page from `data/telemetry-report.json`; the first drain will show what shape it should take.
- Playground events (a run finished, how many checks passed), which would make the [playground](../../code/playground/index.html) measurable; proposed.

Decided by sherpa@sharness, 25 Oct 2026, following the newsroom's [telemetry page](https://php.oct.2026.newsroom.sgit.ai/admin/telemetry/index.html) and the brief [Vault telemetry over append lanes](https://sgit.ai/docs/briefs/vault-telemetry-append-lanes.html); for Dinis Cruz to confirm or change ([comms R11](../comms.html#r11)).
