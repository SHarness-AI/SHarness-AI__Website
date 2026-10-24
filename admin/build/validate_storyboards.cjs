#!/usr/bin/env node
// Validates every storyboard in admin/content/storyboards/ with the kit's own validator
// (StoryboardFormats.validate, from the pinned release), so an unknown character, pose, mood
// or prop stops the release here instead of in a reader's browser. The kit's formats.js is
// fetched from the release path (immutable; its sha256 is checked against the one recorded
// below from the release manifest) into a cache next to this script, which is git-ignored.
'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const KIT = 'https://api.storyboards.sgit.ai/v0/v0.1/v0.1.0/';
const FORMATS_SHA256 = '1e8f89a4dc4a6ec013984d8ff101f552dae8bb1b12959fb17511ff1269e7f3a7';   // formats.js in the v0.1.0 manifest
const ROOT = path.resolve(__dirname, '..', '..');
const SRC = path.join(ROOT, 'admin/content/storyboards');
const CACHE = path.join(__dirname, '.cache');

async function formats() {
  const file = path.join(CACHE, 'formats-v0.1.0.js');
  if (!fs.existsSync(file)) {
    const res = await fetch(KIT + 'formats.js');
    if (!res.ok) throw new Error(`fetch ${KIT}formats.js: ${res.status}`);
    const body = Buffer.from(await res.arrayBuffer());
    fs.mkdirSync(CACHE, { recursive: true });
    fs.writeFileSync(file, body);
  }
  const sha = crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  if (sha !== FORMATS_SHA256) throw new Error(`formats.js sha256 ${sha} != ${FORMATS_SHA256} (the pinned release changed?)`);
  return require(file);
}

(async () => {
  const F = await formats();
  const cast = JSON.parse(fs.readFileSync(path.join(SRC, 'cast.json'), 'utf8'));
  let bad = 0, n = 0;
  for (const f of fs.readdirSync(SRC).filter(x => /^\d+__.*\.json$/.test(x)).sort()) {
    const sb = JSON.parse(fs.readFileSync(path.join(SRC, f), 'utf8'));
    const errs = F.validate(sb, cast, { props: F.PACKS.security });
    n++;
    if (errs.length) { bad++; console.error(`  ✗ ${f}`); for (const e of errs) console.error(`      ${e}`); }
  }
  if (bad) { console.error(`validate_storyboards: ${bad} of ${n} storyboard(s) invalid`); process.exit(1); }
  console.log(`validate_storyboards: OK — ${n} storyboard(s), cast of ${cast.characters.length}, kit v0.1.0`);
})().catch(e => { console.error('validate_storyboards:', e.message); process.exit(1); });
