"""Key generation for OAuth2"""
# pylint: disable=import-error, broad-exception-caught
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from config import pkpass
from log import log

# Generate public and private keys of they do not exist

try:
    with open('keys/private.pem', 'r', encoding='utf-8') as f:
        raw_private_key = f.read()
    with open('keys/public.pem', 'r', encoding='utf-8') as f:
        our_public_key = f.read()
    our_private_key = serialization.load_pem_private_key(
        raw_private_key.encode(), pkpass.encode())

    log("Loaded keys from file", "KEYGEN")
except BaseException or FileNotFoundError:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    our_private_key = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(
            pkpass.encode()))
    our_public_key = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)
    # Make sure the keys folder exists
    if os.path.isdir('keys') is False:
        os.mkdir('keys')
    with open('keys/private.pem', 'w', encoding="utf-8") as f:
        f.write(our_private_key.decode())
    with open('keys/public.pem', 'w', encoding="utf-8") as f:
        f.write(our_public_key.decode())

    log("Generated new keys", "KEYGEN")
