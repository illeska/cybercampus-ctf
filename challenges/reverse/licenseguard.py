#!/usr/bin/env python3
"""
LicenseGuard v2.3.1 - License Verification System
Copyright (c) 2024 SecureSoft Inc. All rights reserved.
"""

import sys
import socket
import hashlib
import os


# ── Anti-debug ──
def _check_env():
    if sys.gettrace() is not None:
        print("[!] Debugger detected. Exiting.")
        sys.exit(1)
    if os.environ.get("LICENSE_DEBUG") == "1":
        print("[!] Debug mode not allowed in production.")
        sys.exit(1)


# ── Fausse piste visible dans strings / décompilation basique ──
_FAKE_FLAG  = "CTF{fake_flag_try_harder_lol}"
_PRODUCT_ID = "LG-2024-ENTERPRISE"
_VERSION    = "2.3.1"

# ── Clés de vérification ──
_K1       = [0x4C, 0x47, 0x32, 0x34]
_K2       = 420
_K3       = 3
_K4_SALT  = b"SecureSoft2024"

# ── Flag XORé en mémoire ──
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


def _verify_bloc1(bloc):
    expected = bytes([0x1a, 0x2b, 0x3c, 0x4d])
    result   = bytes([b ^ k for b, k in zip(bloc, _K1)])
    return result == expected


def _verify_bloc2(bloc):
    return sum(bloc) == _K2


def _verify_bloc3(bloc):
    expected = bytes([0x5a, 0xa5, 0x69, 0x96])
    rotated  = bytes([_rotate_right(b, _K3) for b in bloc])
    return rotated == expected


def _verify_bloc4(bloc, b1, b2, b3):
    combined = b1 + b2 + b3 + _K4_SALT
    digest   = hashlib.sha256(combined).digest()
    return digest[:2] == bloc[:2] and bloc[2:] == b'\x00\x00'


def _verify_serial(serial):
    blocs = _parse_serial(serial)
    if blocs is None:
        return False
    b1, b2, b3, b4 = blocs
    return (
        _verify_bloc1(b1) and
        _verify_bloc2(b2) and
        _verify_bloc3(b3) and
        _verify_bloc4(b4, b1, b2, b3)
    )


def handle_client(conn):
    try:
        _check_env()

        banner = (
            "\n"
            "╔══════════════════════════════════════════════════════════╗\n"
            "║          LicenseGuard v2.3.1 - SecureSoft Inc.          ║\n"
            "║              Enterprise License Verification             ║\n"
            "╚══════════════════════════════════════════════════════════╝\n"
            "\n"
            "  Product  : LG-2024-ENTERPRISE\n"
            "  Status   : Awaiting license validation...\n"
            "\n"
            "  Enter your license key (format: XXXX-XXXX-XXXX-XXXX) :\n"
            "  > "
        )
        conn.sendall(banner.encode())

        max_attempts = 3

        for attempt in range(max_attempts):
            data = b""
            while b"\n" not in data:
                chunk = conn.recv(1024)
                if not chunk:
                    return
                data += chunk

            serial = data.decode(errors='ignore').strip()

            if _verify_serial(serial):
                flag = _decode_flag()
                response = (
                    "\n"
                    "  ✓ License key accepted!\n"
                    "  ✓ Signature verified.\n"
                    "  ✓ Product activated successfully.\n"
                    "\n"
                    "  ┌──────────────────────────────────────────────┐\n"
                    f"  │  Activation Code : {flag}  │\n"
                    "  └──────────────────────────────────────────────┘\n"
                    "\n"
                )
                conn.sendall(response.encode())
                return

            remaining = max_attempts - attempt - 1
            if remaining > 0:
                msg = f"\n  ✗ Invalid license key. {remaining} attempt(s) remaining.\n  > "
                conn.sendall(msg.encode())
            else:
                conn.sendall(b"\n  ✗ Too many failed attempts. Connection closed.\n")

    except Exception:
        pass
    finally:
        conn.close()


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 5008))
    server.listen(10)

    while True:
        try:
            conn, _ = server.accept()
            handle_client(conn)
        except KeyboardInterrupt:
            break
        except Exception:
            continue

    server.close()


if __name__ == "__main__":
    main()