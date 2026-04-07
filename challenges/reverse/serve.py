#!/usr/bin/env python3
"""
LicenseGuard - Challenge Reverse Engineering
Serveur web Flask : téléchargement du binaire + validation du serial
Port 5008 uniquement - aucun port netcat requis
"""

from flask import Flask, send_file, render_template, request
import hashlib
import os

app = Flask(__name__)

BINARY_PATH = "/app/public/licenseguard"

# ── Même logique de vérification que licenseguard.py ──
_K1      = [0x4C, 0x47, 0x32, 0x34]
_K2      = 420
_K3      = 3
_K4_SALT = b"SecureSoft2024"

_ENCODED_FLAG = [
    15, 61, 37, 30, 30, 10, 84, 41, 6, 21, 70, 8, 94, 3, 64,
    107, 62, 90, 21, 86, 28, 0, 86, 24, 24, 85, 1, 16, 1, 66, 79
]
_FLAG_KEY = b"LicenseGuard2024"


def _decode_flag():
    return ''.join(
        chr(_ENCODED_FLAG[i] ^ _FLAG_KEY[i % len(_FLAG_KEY)])
        for i in range(len(_ENCODED_FLAG))
    )


def _rotate_right(val, r, bits=8):
    r = r % bits
    return ((val >> r) | (val << (bits - r))) & ((1 << bits) - 1)


def _parse_serial(serial):
    parts = serial.strip().upper().split('-')
    if len(parts) != 4:
        return None
    blocs = []
    for p in parts:
        if len(p) != 4:
            return None
        try:
            blocs.append(bytes.fromhex(p))
        except ValueError:
            return None
    return blocs


def _verify_serial(serial):
    blocs = _parse_serial(serial)
    if blocs is None:
        return False
    b1, b2, b3, b4 = blocs

    # Bloc 1 : XOR
    if bytes([b ^ k for b, k in zip(b1, _K1)]) != bytes([0x1a, 0x2b, 0x3c, 0x4d]):
        return False
    # Bloc 2 : somme
    if sum(b2) != _K2:
        return False
    # Bloc 3 : rotation droite
    if bytes([_rotate_right(b, _K3) for b in b3]) != bytes([0x5a, 0xa5, 0x69, 0x96]):
        return False
    # Bloc 4 : SHA256
    digest = hashlib.sha256(b1 + b2 + b3 + _K4_SALT).digest()
    if digest[:2] != b4[:2] or b4[2:] != b'\x00\x00':
        return False

    return True




@app.route('/')
def index():
    return render_template('index.html', result=None, serial='', flag='')


@app.route('/download')
def download():
    if not os.path.exists(BINARY_PATH):
        return "Binary not found — contact admin", 404
    return send_file(
        BINARY_PATH,
        as_attachment=True,
        download_name='licenseguard',
        mimetype='application/octet-stream'
    )


@app.route('/validate', methods=['POST'])
def validate():
    serial = request.form.get('serial', '').strip()

    # Vérification format basique
    if not serial or len(serial) != 19:
        return render_template('index.html', result='format', serial=serial, flag='')

    if _verify_serial(serial):
        flag = _decode_flag()
        return render_template('index.html', result='ok', serial=serial, flag=flag)
    else:
        # Distinguer format invalide de serial incorrect
        if _parse_serial(serial) is None:
            return render_template_string(HTML, result='format', serial=serial, flag='')
        return render_template('index.html', result='fail', serial=serial, flag='')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008)