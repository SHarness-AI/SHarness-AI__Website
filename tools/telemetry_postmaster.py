#!/usr/bin/env python3
"""Everything the telemetry vault's postmaster needs, from the vault key alone. Kept by sherpa@sharness.

The sgit.ai network's convention (the newsroom's admin/build/postmaster.py; docs/append-lane-messaging.md §7.1,
"the vault key is the only secret"): the lane's enum key and the key pair's passphrase are derived from the vault's
write key and never stored; the key pair that decrypts what arrives lives inside the vault, its private halves
encrypted under that passphrase. Whoever holds the vault key (Dinis, an agent given it, a vault app) can drain the
lane; no secret lives only in one session.

  derived(wk, label)   HMAC-SHA256(key = bytes of the write key, message = label), hex. The labels, fixed:
                         sharness.ai/postmaster/enum-key/v1          the lane's enum key
                         sharness.ai/postmaster/front-door-pass/v1   the key pair's passphrase
  In the vault:
    .vault/postmaster/lane.json                 vault id, endpoint, recipient fingerprint, senders (published tokens)
    .vault/postmaster/front-door-keypair/       sgit's key files; the private ones encrypted under the passphrase

Commands (run with a clone of the telemetry vault, outside this repository):
  python3 tools/telemetry_postmaster.py init <vault clone> --token <append token hex>
        make the key pair inside the vault, write lane.json, print the public half for data/telemetry.json
  python3 tools/telemetry_postmaster.py configure <vault clone>
        register the lane with the server (needs SG_SEND_ACCESS_TOKEN; safe to repeat)
  python3 tools/telemetry_postmaster.py public <vault clone>
        print data/telemetry.json's content (the public half only)

Standard library and the sgit CLI only.
"""
import argparse, hashlib, hmac, json, os, shutil, subprocess, sys, tempfile

LABEL = 'sharness.ai/postmaster/{}/v1'
PM = os.path.join('.vault', 'postmaster')
ENDPOINT = 'https://dev.send.sgraph.ai'


def write_key(vault):
    """The vault's id and write key, derived by sgit from the vault key in the clone; never printed."""
    vk = open(os.path.join(vault, '.sg_vault', 'local', 'vault_key')).read().strip()
    out = subprocess.run(['sgit', 'vault', 'derive-keys', vk], capture_output=True, text=True, check=True).stdout
    keys = {k.strip(): v.strip() for k, v in (l.split(':', 1) for l in out.splitlines() if ':' in l)}
    return keys['vault_id'], keys['write_key']


def derived(wk, name):
    return hmac.new(bytes.fromhex(wk), LABEL.format(name).encode(), hashlib.sha256).hexdigest()


def lane_path(vault):
    return os.path.join(vault, PM, 'lane.json')


def open_postmaster(vault):
    """(lane, passphrase, home): the lane with its enum key filled in, the key pair's passphrase, and a throwaway HOME
    whose sgit keystore holds the vault's key pair. Set HOME to it while decrypting; delete it after."""
    vault = os.path.abspath(vault)
    vid, wk = write_key(vault)
    lane = json.load(open(lane_path(vault)))
    if lane['vault_id'] != vid:
        raise SystemExit(f'lane.json names {lane["vault_id"]}, this clone is {vid}')
    lane['enum_key'] = derived(wk, 'enum-key')
    home = tempfile.mkdtemp(prefix='postmaster-')
    src = os.path.join(vault, PM, 'front-door-keypair')
    shutil.copytree(src, os.path.join(home, '.sg-send', 'keys', 'sha256_' + lane['recipient'].split(':')[1]))
    return lane, derived(wk, 'front-door-pass'), home


def init(vault, token):
    """Make the front-door key pair inside the vault (private halves encrypted under the derived passphrase), write
    lane.json. Prints nothing secret: the fingerprint and the public key only."""
    vault = os.path.abspath(vault)
    vid, wk = write_key(vault)
    if os.path.exists(lane_path(vault)):
        raise SystemExit(f'{lane_path(vault)} exists; not overwriting')
    home = tempfile.mkdtemp(prefix='postmaster-init-')
    env = dict(os.environ, HOME=home, SG_SEND_PASSPHRASE=derived(wk, 'front-door-pass'))
    out = subprocess.run(['sgit', 'pki', 'keygen', '--label', f'sharness.ai telemetry front door ({vid})'],
                         capture_output=True, text=True, check=True, env=env).stdout
    keys_dir = os.path.join(home, '.sg-send', 'keys')
    dirs = [d for d in os.listdir(keys_dir) if d.startswith('sha256_')]
    if len(dirs) != 1:
        raise SystemExit(f'expected one key pair in {keys_dir}, found {dirs}')
    fp = 'sha256:' + dirs[0][len('sha256_'):]
    pub = subprocess.run(['sgit', 'pki', 'export', fp], capture_output=True, text=True, check=True, env=env).stdout
    pem = pub[pub.index('-----BEGIN PUBLIC KEY-----'):pub.index('-----END PUBLIC KEY-----') + len('-----END PUBLIC KEY-----')]
    pem = pem.replace('\\n', '\n')                       # sgit pki export prints the PEM with escaped newlines
    dst = os.path.join(vault, PM, 'front-door-keypair')
    os.makedirs(os.path.join(vault, PM), exist_ok=True)
    shutil.copytree(os.path.join(keys_dir, dirs[0]), dst)
    shutil.rmtree(home, ignore_errors=True)
    lane = {'vault_id': vid, 'endpoint': ENDPOINT, 'recipient': fp, 'recipient_public_key': pem,
            'senders': {'sharness.ai': token}, 'geo': ['https://ipapi.co/json/', 'https://ipwho.is/'],
            'note': 'enum key and key-pair passphrase are derived from the vault write key (tools/telemetry_postmaster.py); never stored'}
    json.dump(lane, open(lane_path(vault), 'w'), indent=1)
    print(json.dumps(public(vault), indent=1))


def public(vault):
    """What the site publishes: data/telemetry.json. The append token and the public key are publishable by design."""
    lane = json.load(open(lane_path(os.path.abspath(vault))))
    return {'enabled': True, 'endpoint': lane['endpoint'], 'vault_id': lane['vault_id'],
            'append_token': lane['senders']['sharness.ai'],
            'recipient': {'fingerprint': lane['recipient'], 'encrypt': lane['recipient_public_key']},
            'geo': lane['geo'],
            'note': 'One anonymous event per page per session, encrypted in the browser to this key, written to a write-only lane. See /project/telemetry/.'}


def configure(vault):
    """Register the lane's anchors (every sender's token hash) and the enum key's hash with the server. Replaces the
    list. Needs the vault write key (from the clone) and SG_SEND_ACCESS_TOKEN (from the environment)."""
    import urllib.request
    vault = os.path.abspath(vault)
    _, wk = write_key(vault)
    lane, _, home = open_postmaster(vault)
    shutil.rmtree(home, ignore_errors=True)
    body = {'append_anchors': [hashlib.sha256(t.encode()).hexdigest() for t in lane['senders'].values()],
            'enum_key_hash': hashlib.sha256(lane['enum_key'].encode()).hexdigest()}
    req = urllib.request.Request(f"{lane['endpoint']}/api/vault/append/configure/{lane['vault_id']}", data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json', 'x-sgraph-vault-write-key': wk,
                                          'x-sgraph-access-token': os.environ['SG_SEND_ACCESS_TOKEN']}, method='POST')
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('init'); p.add_argument('vault'); p.add_argument('--token', required=True, help='append token, lowercase hex 16..128')
    p = sub.add_parser('configure'); p.add_argument('vault')
    p = sub.add_parser('public'); p.add_argument('vault')
    a = ap.parse_args()
    if a.cmd == 'init':
        import re
        if not re.fullmatch(r'[0-9a-f]{16,128}', a.token):
            raise SystemExit('append token must be lowercase hex, 16 to 128 characters')
        init(a.vault, a.token)
    elif a.cmd == 'configure':
        print(json.dumps(configure(a.vault), indent=1))
    elif a.cmd == 'public':
        print(json.dumps(public(a.vault), indent=1))


if __name__ == '__main__':
    main()
