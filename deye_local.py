"""Experimental read-only client for the Deye DL1000B-WIFI local web UI.

Protocol derived from observed device JavaScript; not yet validated on hardware.
Only requests require.cgi, send.cgi and status.cgi. No inverter control operations.
"""
import argparse
import base64
import json
import re
import secrets
import sys
import time
from urllib.parse import quote

import requests
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import load_pem_public_key


def unwrap(text):
    start = text.find("json_start")
    end = text.find("json_end")
    if start >= 0 and end > start:
        return text[start + len("json_start"):end]
    return text


def aes_encrypt_url(url, key):
    raw = url.encode("utf-8")
    raw += b"\x00" * (16 - len(raw) % 16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(key)).encryptor()
    return base64.b64encode(cipher.update(raw) + cipher.finalize()).decode("ascii")


def aes_decrypt_response(text, key):
    payload = text.split("result_end", 1)[0].strip()
    raw = base64.b64decode(payload, validate=True)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(key)).decryptor()
    return (decryptor.update(raw) + decryptor.finalize()).rstrip(b"\x00").decode("utf-8")


class DeyeLocal:
    def __init__(self, ip, timeout=8):
        if not re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", ip):
            raise ValueError("Provide a numeric IPv4 address, e.g. 192.168.1.93")
        if any(int(part) > 255 for part in ip.split(".")):
            raise ValueError("Invalid IPv4 address")
        self.base = f"http://{ip}/"
        self.session = requests.Session()
        self.timeout = timeout
        self.key = None

    def get_encoded(self, original):
        # The firmware's encryptMessage() Base64-encodes the entire URL for
        # bootstrap endpoints, and AES-encrypts it after key exchange.
        if self.key is None:
            path = base64.b64encode(original.encode("utf-8")).decode("ascii")
        else:
            path = aes_encrypt_url(original, self.key)
        # Preserve Base64 slash/plus characters in the path, as in XHR.open().
        response = self.session.get(self.base + path, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def exchange_key(self):
        response = self.get_encoded(f"require.cgi?t={time.time():.6f}")
        public_pem = unwrap(response).strip()
        if "BEGIN PUBLIC KEY" not in public_pem:
            raise RuntimeError("require.cgi did not return an RSA public key")
        public_key = load_pem_public_key(public_pem.encode("utf-8"))
        # Match the observed 16-digit ASCII session key format.
        key_text = str(secrets.randbelow(9000000000000000) + 1000000000000000)
        encrypted_key = public_key.encrypt(
            key_text.encode("ascii"), padding.PKCS1v15()
        )
        rsa_b64 = base64.b64encode(encrypted_key).decode("ascii")
        # Important: send.cgi itself is a bootstrap endpoint, not AES encrypted.
        send_url = f"send.cgi?key={quote(rsa_b64, safe='')}&t={time.time():.6f}"
        answer = self.get_encoded(send_url)
        if "success" not in unwrap(answer).lower():
            raise RuntimeError("send.cgi did not confirm key exchange")
        self.key = key_text.encode("ascii")

    def status(self):
        if self.key is None:
            self.exchange_key()
        response = self.get_encoded(f"status.cgi?t={time.time():.6f}")
        clear = aes_decrypt_response(response, self.key)
        payload = json.loads(unwrap(clear))
        if not isinstance(payload, dict):
            raise RuntimeError("Unexpected status payload type")
        return payload


def main():
    parser = argparse.ArgumentParser(description="Read Deye logger status locally")
    parser.add_argument("--ip", default="192.168.1.93", help="Local logger IPv4")
    args = parser.parse_args()
    client = DeyeLocal(args.ip)
    try:
        data = client.status()
        # Print only the limited measurement fields, never full device data.
        subdevices = data.get("subDevices", data.get("subdevices", []))
        print("Connected. Status response received.")
        print("Top-level fields:", ", ".join(sorted(data.keys())))
        print("Subdevice collection type:", type(subdevices).__name__)
        # Report scalar measurement fields found in nested structures.
        wanted = {"ratedPower", "currentPower", "yieldToday", "totalYield"}
        def walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k in wanted and isinstance(v, (str, int, float)):
                        print(f"{k}: {v}")
                    elif isinstance(v, (dict, list)):
                        walk(v)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        walk(data)
    except (requests.RequestException, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Local read failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
