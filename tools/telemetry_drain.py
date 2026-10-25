#!/usr/bin/env python3
"""Drain sharness.ai's telemetry lane into the telemetry vault and compute the report (counts only).

Run by whoever holds the telemetry vault key, with a clone of it at --vault (outside this repository):

    python3 tools/telemetry_drain.py --vault <clone of the telemetry vault> [--site <this repository>]

Everything the drain needs comes from the vault key (tools/telemetry_postmaster.py): the lane's enum key and the
key pair's passphrase are derived from it, the key pair lives in the vault. Lists the lane, fetches pending files,
decrypts each with `sgit pki decrypt`, appends the events as JSON lines to drain/<date>.jsonl, marks them processed,
and writes reports/<date>.json and reports/latest.json with counts only. With --site, copies the public part of the
report to <site>/data/telemetry-report.json: never a row, never a city or a region (a small town with a handful of
visitors can name a person). Then commit and push the vault, and release the site.
"""
import argparse, base64, collections, datetime, json, os, shutil, subprocess, sys, tempfile, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import telemetry_postmaster as pm                                                   # noqa: E402

PRIVATE_ONLY = ('by_region', 'by_city')     # kept in the private vault's reports, never copied to the public site


def post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', **headers}, method='POST')
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def decrypt(enc_b64_twice, fingerprint, passphrase, home):
    enc_text = base64.b64decode(enc_b64_twice)            # the .enc file bytes (themselves base64 text of the envelope)
    with tempfile.NamedTemporaryFile('wb', suffix='.enc', delete=False, dir=home) as f:
        f.write(enc_text); path = f.name
    env = dict(os.environ, HOME=home, SG_SEND_PASSPHRASE=passphrase)
    try:
        out = path[:-4]
        p = subprocess.run(['sgit', 'pki', 'decrypt', path, '--fingerprint', fingerprint, '--output', out],
                           input=(passphrase + '\n').encode(), capture_output=True, timeout=60, env=env)
        if p.returncode != 0 or not os.path.exists(out):
            p = subprocess.run(['sgit', 'pki', 'decrypt', path, '--fingerprint', fingerprint],
                               input=(passphrase + '\n').encode(), capture_output=True, timeout=60, env=env)
        if os.path.exists(out):
            return open(out, 'rb').read().decode('utf-8', 'replace')
        raise RuntimeError(p.stderr.decode()[-300:])
    finally:
        for q in (path, path[:-4]):
            try: os.remove(q)
            except OSError: pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--vault', required=True); ap.add_argument('--site')
    ap.add_argument('--keep-pending', action='store_true', help='do not mark files processed (re-drain later)')
    a = ap.parse_args()
    V = os.path.abspath(a.vault)
    lane, passphrase, home = pm.open_postmaster(V)
    try:
        token = lane['senders']['sharness.ai']
        H = {'x-sgraph-vault-enum-key': lane['enum_key']}
        base = f"{lane['endpoint']}/api/vault/append"
        today = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
        os.makedirs(os.path.join(V, 'drain'), exist_ok=True); os.makedirs(os.path.join(V, 'reports'), exist_ok=True)
        got, after, rows = [], None, []
        while True:
            body = {'include_content': False}
            if after: body['after_file_id'] = after
            r = post(f"{base}/list/{lane['vault_id']}", body, H)
            entries = r.get('entries', [])
            got += entries
            if not r.get('truncated') or not entries: break
            after = entries[-1]['file_id']
        print(f'pending: {len(got)}')
        for i in range(0, len(got), 50):
            batch = got[i:i + 50]
            f = post(f"{base}/fetch/{lane['vault_id']}", {'inbox': token, 'file_ids': [e['file_id'] for e in batch]}, H)
            files = f.get('files') or f.get('entries') or []
            for item in files:
                fid = item.get('file_id') or item.get('id'); content = item.get('content') or item.get('payload')
                if not content: continue
                try:
                    ev = json.loads(decrypt(content, lane['recipient'], passphrase, home))
                except Exception as e:
                    ev = {'v': 0, 'undecryptable': True, 'error': str(e)[:120]}
                ev['_file'] = fid; ev['_received'] = item.get('received') or next((x.get('received') for x in batch if x['file_id'] == fid), None)
                rows.append(ev)
            if not a.keep_pending and files:
                post(f"{base}/mark-processed/{lane['vault_id']}", {'inbox': token, 'file_ids': [x.get('file_id') or x.get('id') for x in files]}, H)
    finally:
        shutil.rmtree(home, ignore_errors=True)
    with open(os.path.join(V, 'drain', f'{today}.jsonl'), 'a', encoding='utf-8') as f:
        for ev in rows: f.write(json.dumps(ev, ensure_ascii=False, sort_keys=True) + '\n')
    # the report: counts over every drained row (all files), never the rows
    allrows = []
    for fn in sorted(os.listdir(os.path.join(V, 'drain'))):
        if fn.endswith('.jsonl'):
            for line in open(os.path.join(V, 'drain', fn), encoding='utf-8'):
                try: allrows.append(json.loads(line))
                except Exception: pass
    real = [r for r in allrows if r.get('v') == 1 and not r.get('test')]
    readers = [r for r in real if not r.get('agent') and not r.get('who')]
    def top(rows_, key, n=25):
        c = collections.Counter((r.get(key) or '(none)') for r in rows_)
        return [[k, v] for k, v in c.most_common(n)]
    days = collections.Counter((r.get('ts') or '')[:10] for r in real)
    rep = {'as_of': today, 'drained_now': len(rows), 'events': len(real), 'test_or_undecryptable': len(allrows) - len(real),
           'sessions': len({r.get('sid') for r in real}),
           'groups': {'readers': len(readers), 'editor_and_team': sum(1 for r in real if r.get('who')),
                      'automation': sum(1 for r in real if r.get('agent'))},
           'by_day': sorted(days.items()), 'by_path': top(readers, 'path', 40), 'by_country': top(readers, 'country'),
           'by_region': top(readers, 'region'), 'by_city': top(readers, 'city'), 'by_referrer': top(readers, 'ref'),
           'by_screen': top(readers, 'screen'), 'by_version': top(readers, 'ver'), 'by_agent': top(real, 'agent'),
           'note': 'Counts over events received in the lane; by_* over readers (no automation, no declared role). Every event is an untrusted claim: the token and the public key are published, so rows can be forged or flooded. Visitors with blockers do not appear. No row leaves the vault.'}
    json.dump(rep, open(os.path.join(V, 'reports', f'{today}.json'), 'w'), indent=1); json.dump(rep, open(os.path.join(V, 'reports', 'latest.json'), 'w'), indent=1)
    if a.site:
        public = {k: v for k, v in rep.items() if k not in PRIVATE_ONLY}
        os.makedirs(os.path.join(a.site, 'data'), exist_ok=True)
        with open(os.path.join(a.site, 'data', 'telemetry-report.json'), 'w') as f:
            json.dump(public, f, indent=1); f.write('\n')
    print(f'events total: {len(real)}; report written for {today}')


if __name__ == '__main__':
    main()
