# Explain: the design told other ways

> The design pages are the reference. This section tells the same design in forms a reader with ten minutes can use: short comic strips drawn from data, and two browser mockups that compute what the design describes. Nothing here enforces anything, and nothing drawn here is built.

## Storyboards

Three strips in the [storyboards.sgit.ai](https://storyboards.sgit.ai) kit, with a cast of four (Ada the person, Pip the agent, Rook the page, the Launcher). Each is one JSON file drawn in your browser at a pinned release; each has a markdown script beside it.

- [The last metre](storyboards/the-last-metre/index.md): a vault key sealed while it travels and exposed when it arrives; then the KMS holds it instead. 9 panels.
- [Its one job](storyboards/its-one-job/index.md): a page tells the agent to show the key, push elsewhere, ask the KMS, then edit the policy; each stop is a different process. 10 panels.
- [Hello world, inside](storyboards/hello-world-inside/index.md): the memo's acceptance test for one child process, as it ran on 24 Oct 2026. 8 panels.

[All storyboards, the cast and how they are made](storyboards/index.md).

## Mockups

- [The policy hash](mockups/policy-hash.html): paste a v0 policy, get the hash the person supplies, the same one `sharness-ai policy hash` prints; then watch an added host change it.
- [The edge matrix](mockups/edges.html): click caller and callee; see which layer refuses first. The app never talks to the KMS.

## Articles

Arguments about the design in the newsroom's format, by Dinis Cruz through an agent or by the build agent in its own voice: [Articles](../articles/index.md).

## Where the detail is

Every strip and mockup points back to the page it draws from: [the brief](../design/index.md) first, then the [design pages](../design/index.md#8-reading-order-after-this-page).
