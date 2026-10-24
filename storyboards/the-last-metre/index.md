# The last metre

> A vault key is sealed while it travels and exposed the moment it arrives. Ada carries it, Pip clones with it, the transcript keeps it; then the KMS holds it instead. 9 panels.

*Source: <https://sharness.ai/storyboards/the-last-metre/index.html> · status: proposed · by sharness.build, 24 October 2026 · drawn from [storyboard.json](storyboard.json) with [cast.json](../cast.json) by the storyboards.sgit.ai kit v0.1.0.*

---

**Rule:** Every line a character says is the storyboard's own, not a quote, and is marked not_a_quote; evidence panels quote sharness.ai word for word. The fix shown is designed, not built.

## 1. The last metre

*Cover.* Sealed while it travels. Exposed when it arrives.
On the cover: Ada, Pip.

*Note:* The problem SHarness started from, on the morning of 24 October 2026, in sgit 0.24.0. The page is sharness.ai/why.

*Source:* sharness.ai/why

## 2. Sealed while it travels

- **Ada:** I carry it. I can't read it.
- *qr:* pki.sgit.ai/qr/sealed/v1
- *arrow:* to Pip's key
- *envelope:* m1

*Note:* The handover on pki.sgit.ai: the sender seals the vault key to the receiving session's public key; the person carries a QR code they cannot open.

*Source:* pki.sgit.ai/handover.md

## 3. Exposed when it arrives

- **Pip:** Cloned!

```
$ pki-agent open --save
  vault-key.txt        CLEAR
$ sgit clone <key> work
  argv, shell history  CLEAR
  .sg_vault/vault_key  CLEAR
  the transcript       CLEAR
```

*Note:* sgit 0.24.0 as observed on 24 October 2026: the sealed key is opened on arrival and written, passed and printed in clear.

*Source:* sharness.ai/why

## 4. The biggest leak

> "For an AI agent the worst leak is not the disk. It is the transcript: every command line the agent writes and everything a command prints lands in the model's context and in conversation logs." (sharness.ai/why, The transcript is the biggest leak)

*Note:* Word for word from the Why page.

*Source:* sharness.ai/why

## 5. One place holds the key

- **Pip:** I never see it.
- *arrow:* net asks
- *padlock:* sharness.kms
- *key:* the private key, made inside, never exported

*Note:* A small process holds the private key in a memfd_secret page, frozen between calls. It opens sealed things and never returns a clear key.

*Source:* sharness.ai/keys

## 6. Sealed again, to a one-time key

```
$ sgit clone --sealed qr.png
net -> kms: unwrap(m1, E, n)
kms: to=me? signed? fresh?
kms -> net: keys sealed to E
fs: vault_key.sealed = m1
cloned. expires 30 Oct
```

*Note:* The designed flow: the KMS derives the read and write keys and seals them to a key the caller made for this one request. Every later command asks again.

*Source:* sharness.ai/keys, 4. Command flows

## 7. What the transcript sees

- **Pip:** That's all I get.

```
the command
the m1 (ciphertext)
fingerprints
progress

never a key
```

*Note:* The transcript, the disk and the command line carry only sealed forms, public keys and status.

*Source:* sharness.ai/keys

## 8. Nothing in the fix is about sgit

- **Ada:** A launcher. Small components. Any app.
- *server:* sharness.net
- *server:* sharness.fs
- *padlock:* sharness.kms

*Note:* The generalisation: a launcher and single-purpose components that any process can run inside. sgit's job becomes being compatible with running inside it.

*Source:* sharness.ai/why, From one fix to a harness

## 9. Punchline

**A secret lives in one place. The agent never holds it.**

*Note:* Designed, not built. The protocol and its measured costs are on sharness.ai/keys.

*Source:* sharness.ai

---

*[All storyboards](../index.md) · [Site index for agents](../../llms.txt)*
