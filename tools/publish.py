#!/usr/bin/env python3
"""Chiffre les données du tableau de bord Allure dans data.enc.json.

Usage :
    ALLURE_KEY='ta-cle' python3 tools/publish.py DOSSIER_DES_CSV [--out data.enc.json]

Le dossier doit contenir les 15 fichiers CSV du tableau de bord.
La clé n'est jamais écrite dans le dépôt : elle vient de la variable ALLURE_KEY.
Chiffrement : PBKDF2-SHA256 (600 000 itérations) puis AES-256-GCM.
"""
import base64
import datetime
import hashlib
import json
import os
import re
import secrets
import sys
import unicodedata
from zoneinfo import ZoneInfo

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

IDS = [
    'activites', 'sommeil', 'vfc', 'charge', 'body_battery', 'pas', 'vo2max',
    'etat_du_jour', 'equilibre_charge', 'predictions', 'records', 'allures',
    'regles', 'plan', 'semaines', 'coach',
]
ITER = 600_000


def norm(s: str) -> str:
    """Même normalisation que l'appli : minuscules, sans accents, espaces et tirets fusionnés."""
    s = unicodedata.normalize('NFD', s.strip().lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[\s_-]+', '-', s)


def b64(b: bytes) -> str:
    return base64.b64encode(b).decode('ascii')


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        sys.exit(1)
    src = args[0]
    out = 'data.enc.json'
    if '--out' in args:
        out = args[args.index('--out') + 1]

    key = os.environ.get('ALLURE_KEY', '')
    if not key.strip():
        sys.exit('ALLURE_KEY est vide : impossible de chiffrer.')

    files, missing = {}, []
    for i in IDS:
        p = os.path.join(src, i + '.csv')
        if not os.path.exists(p):
            missing.append(i + '.csv')
            continue
        with open(p, encoding='utf-8-sig') as f:
            txt = f.read().replace('\r\n', '\n').replace('\r', '\n')
        if txt.count('\n') < 1:
            sys.exit(f'{i}.csv est vide : publication annulée.')
        files[i] = txt
    if missing:
        sys.exit('Fichiers manquants : ' + ', '.join(missing))

    now = datetime.datetime.now(ZoneInfo('Europe/Paris')).replace(microsecond=0)
    payload = json.dumps({'v': 1, 'updated': now.isoformat(), 'files': files},
                         ensure_ascii=False, separators=(',', ':')).encode('utf-8')

    # Le sel reste stable d'une publication à l'autre : l'appli garde la clé dérivée
    # sur le téléphone et n'a pas besoin de la redemander chaque matin.
    salt = None
    if os.path.exists(out):
        try:
            with open(out, encoding='utf-8') as f:
                old = json.load(f)
            if old.get('iter') == ITER:
                salt = base64.b64decode(old['salt'])
        except (ValueError, KeyError):
            salt = None
    if salt is None:
        salt = secrets.token_bytes(16)

    dk = hashlib.pbkdf2_hmac('sha256', norm(key).encode('utf-8'), salt, ITER, 32)
    iv = secrets.token_bytes(12)
    ct = AESGCM(dk).encrypt(iv, payload, None)

    # Vérification immédiate : on relit ce qu'on vient de chiffrer.
    assert AESGCM(dk).decrypt(iv, ct, None) == payload

    pkg = {'v': 1, 'alg': 'AES-256-GCM', 'kdf': 'PBKDF2-SHA256', 'iter': ITER,
           'salt': b64(salt), 'iv': b64(iv), 'ct': b64(ct)}
    tmp = out + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(pkg, f, separators=(',', ':'))
    os.replace(tmp, out)
    print(f'OK : {len(files)} fichiers chiffrés dans {out} ({len(ct) // 1024} Ko), données du {now:%d/%m/%Y %H:%M}.')


if __name__ == '__main__':
    main()
