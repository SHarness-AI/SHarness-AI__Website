#!/usr/bin/env node
// sharness.ai pre-release gate. Run from anywhere: node admin/build/validate.js
// The same gate the *.sgit.ai sites run (this one is adapted from nfrs.sgit.ai).
// Checks, in order:
//   1. version agreement — admin/build/version.txt vs every page's version badge,
//      the versions table, llms.txt, llms-full.txt and index.md
//   2. internal links — every relative href/src in every .html file resolves to a
//      file in the tree (fragments stripped; external and mailto links skipped)
//   3. canonical host — every <link rel="canonical"> and og:url points at the host
//      in CNAME, and every page declares one
//   4. key-leak tripwire — nothing in the tree may look like an sgit vault key
//      (a >=20-char passphrase joined by a colon to a uuid-shaped id)
//   5. generate or date every number — every page carrying a figure carries an
//      as-of date in a <span class="asof">, so a stale figure is visible
//   6. articles hold the newsroom's format (front matter, summary length, anchors,
//      lead figure, no em-dash), so each imports into newsroom.sgit.ai unchanged
// Any failure exits 1: no tag, no publish.
'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const errors = [];

function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir)) {
    if (name === '.git' || name === '.github' || name === 'node_modules' || name === '.sg_vault') continue;
    const p = path.join(dir, name);
    const st = fs.statSync(p);
    if (st.isDirectory()) walk(p, out);
    else out.push(p);
  }
  return out;
}

const files = walk(ROOT);
const htmlFiles = files.filter(f => f.endsWith('.html'));

// --- 1. version agreement -------------------------------------------------
const VERSION = fs.readFileSync(path.join(ROOT, 'admin/build/version.txt'), 'utf8').trim();
if (!/^v\d+\.\d+\.\d+$/.test(VERSION)) {
  errors.push(`version.txt does not carry a vX.Y.Z version: "${VERSION}"`);
}
for (const f of htmlFiles) {
  const t = fs.readFileSync(f, 'utf8');
  const badges = [...t.matchAll(/class="ver"[^>]*>(v\d+\.\d+\.\d+)</g)].map(m => m[1]);
  for (const b of badges) if (b !== VERSION) {
    errors.push(`${path.relative(ROOT, f)}: version badge ${b} != ${VERSION}`);
  }
}
for (const extra of ['llms.txt', 'llms-full.txt', 'index.md']) {
  const t = fs.readFileSync(path.join(ROOT, extra), 'utf8');
  if (!t.includes(VERSION)) errors.push(`${extra} does not mention ${VERSION}`);
}
const versTable = fs.readFileSync(path.join(ROOT, 'admin/versions.html'), 'utf8');
if (!versTable.includes(`class="vnum">${VERSION}<`)) {
  errors.push(`admin/versions.html has no row for ${VERSION}`);
}
// each release appears exactly once — a blanket version-bump sed that touches
// the history table produces duplicates (it shipped once on nhi.sgit.ai)
const rows = [...versTable.matchAll(/class="vnum">(v\d+\.\d+\.\d+)</g)].map(m => m[1]);
for (const v of rows) if (rows.filter(x => x === v).length > 1) {
  errors.push(`admin/versions.html lists ${v} more than once`);
  break;
}

// --- 2. internal links ----------------------------------------------------
for (const f of htmlFiles) {
  const t = fs.readFileSync(f, 'utf8');
  const dir = path.dirname(f);
  for (const m of t.matchAll(/(?:href|src)="([^"#]+)(?:#[^"]*)?"/g)) {
    const target = m[1];
    if (/^(https?:|mailto:|data:|\/\/)/.test(target) || target === '') continue;
    // a leading "/" is the site root (the newsroom's article shape uses /articles/images/…)
    const resolved = target.startsWith('/') ? path.join(ROOT, target) : path.resolve(dir, target);
    if (!fs.existsSync(resolved)) {
      errors.push(`${path.relative(ROOT, f)}: broken link -> ${target}`);
    }
  }
}

// --- 3. canonical host ----------------------------------------------------
const HOST = fs.readFileSync(path.join(ROOT, 'CNAME'), 'utf8').trim();
if (!/^[a-z0-9.-]+$/.test(HOST)) errors.push(`CNAME does not carry a hostname: "${HOST}"`);
for (const f of htmlFiles) {
  const t = fs.readFileSync(f, 'utf8');
  const claimed = [
    ...[...t.matchAll(/<link[^>]+rel="canonical"[^>]+href="([^"]+)"/g)].map(m => m[1]),
    ...[...t.matchAll(/<meta[^>]+property="og:url"[^>]+content="([^"]+)"/g)].map(m => m[1]),
  ];
  for (const url of claimed) if (!url.startsWith(`https://${HOST}/`)) {
    errors.push(`${path.relative(ROOT, f)}: canonical/og:url is not on ${HOST} -> ${url}`);
  }
  // every page must declare where it canonically lives
  if (!/rel="canonical"/.test(t)) {
    errors.push(`${path.relative(ROOT, f)}: no canonical link`);
  }
}

// --- 4. key-leak tripwire -------------------------------------------------
const KEY_SHAPE = /[A-Za-z0-9_-]{20,}:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/;
for (const f of files) {
  if (/\.(png|jpg|jpeg|gif|webp|ico|woff2?|zip)$/.test(f)) continue;
  const t = fs.readFileSync(f, 'utf8');
  if (KEY_SHAPE.test(t)) {
    errors.push(`${path.relative(ROOT, f)}: contains a vault-key-shaped string`);
  }
}

// --- 5. generate or date every number --------------------------------------
// The nav and the footer are stripped before looking, so the chrome can neither
// satisfy nor trip a check meant for the page body.
function bodyOnly(text) {
  return text
    .replace(/<nav class="site">[\s\S]*?<\/nav>/, '')
    .replace(/<footer class="site">[\s\S]*?<\/footer>/, '')
    .replace(/<head>[\s\S]*?<\/head>/, '');
}
// Every page that carries a figure must carry an as-of date beside it. The
// marker is <span class="asof">, which the stylesheet renders visibly: a
// number whose date is missing is a number nobody can check.
//
// "A figure" has to be defined carefully or the check is useless in both
// directions. Three things are NOT figures and were flagged as such by the
// first draft of this rule: a four-digit year, a version string, and a
// licence name (CC BY 4.0). None of them is a measurement, and treating them
// as one trains people to add a meaningless date to silence the gate — which
// is exactly the outcome this rule exists to prevent.
const YEAR = /^(?:1[89]|20)\d\d$/;
for (const f of htmlFiles) {
  const rel = path.relative(ROOT, f);
  if (rel.startsWith('admin/')) continue;      // the versions table is dated by row
  const t = fs.readFileSync(f, 'utf8');
  // an article is dated by its byline (<time datetime>), as nfrs.sgit.ai's document
  // pages are dated by their metadata block: the page is as fresh as its publication
  const dated = /class="asof"/.test(t) || /<p class="byline">[^\n]*<time datetime="\d{4}-\d{2}-\d{2}">/.test(t);
  if (dated) continue;
  const prose = bodyOnly(t)
    .replace(/<[^>]+>/g, ' ')                  // attributes hold paths and versions
    .replace(/\bv\d+(?:\.\d+)+/g, ' ')       // version strings
    .replace(/\bCC BY \d+(?:\.\d+)?/g, ' '); // the licence name
  const figures = (prose.match(/\d[\d,]{2,}(?:\.\d+)?|\d+(?:\.\d+)?%/g) || [])
    .filter(x => !YEAR.test(x.replace(/,/g, '')));
  if (figures.length) {
    errors.push(`${rel}: carries figures (${figures.slice(0, 3).join(', ')}) but no `
      + `<span class="asof"> date — generate or date every number`);
  }
}

// --- 6. articles hold the newsroom's format --------------------------------
// The shape send.sgit.ai's "Every site its own articles" sets out, so a source in
// admin/content/articles/ imports into newsroom.sgit.ai unchanged: the front matter,
// a summary of 220 to 360 words, the three anchors the newsroom's build reads, a lead
// figure that exists, and no em-dash (rule 1 of that guidance; the build fails on one).
const ART = path.join(ROOT, 'admin/content/articles');
const FIELDS = ['title', 'date', 'author', 'author_url', 'summary', 'version', 'license', 'tags', 'status'];
if (fs.existsSync(ART)) {
  for (const name of fs.readdirSync(ART).filter(n => n.endsWith('.md'))) {
    const rel = `admin/content/articles/${name}`;
    const t = fs.readFileSync(path.join(ART, name), 'utf8');
    const fm = t.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
    if (!fm) { errors.push(`${rel}: no front matter`); continue; }
    const meta = {};
    for (const line of fm[1].split('\n')) {
      const i = line.indexOf(':');
      if (i > 0) meta[line.slice(0, i).trim()] = line.slice(i + 1).trim();
    }
    for (const f of FIELDS) if (!meta[f]) errors.push(`${rel}: front matter has no ${f}`);
    if (meta.date && !/^\d{4}-\d{2}-\d{2}$/.test(meta.date)) errors.push(`${rel}: date is not YYYY-MM-DD`);
    if (meta.tags && !/\barticle\]$/.test(meta.tags)) errors.push(`${rel}: the last tag must be "article"`);
    const words = (meta.summary || '').split(/\s+/).filter(Boolean).length;
    if (words < 220 || words > 360) errors.push(`${rel}: summary is ${words} words, not 220 to 360`);
    for (const a of ['in-short', 'limits', 'sources']) {
      if (!t.includes(`{#${a}}`)) errors.push(`${rel}: no {#${a}} section`);
    }
    const lead = fm[2].trimStart().match(/^!\[[^\]]+\]\(([^)\s]+)\)/);
    if (!lead) errors.push(`${rel}: does not open with a lead figure`);
    else if (!fs.existsSync(path.join(ROOT, lead[1].replace(/^\//, '')))) {
      errors.push(`${rel}: lead figure ${lead[1]} does not exist`);
    }
    t.split('\n').forEach((line, n) => {
      if (line.includes('\u2014')) errors.push(`${rel}:${n + 1}: em-dash`);
    });
  }
}

// --- report ---------------------------------------------------------------
if (errors.length) {
  console.error(`validate: ${errors.length} error(s)`);
  for (const e of errors) console.error('  ✗ ' + e);
  process.exit(1);
}
console.log(`validate: OK — ${VERSION} on ${HOST}, ${htmlFiles.length} pages, links resolve, every figure dated, no key-shaped strings`);
