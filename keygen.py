from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os
from config import pkpass, URL
from log import log


# Generate public and private keys of they do not exist

try:
    raw_private_key = open('keys/private.pem', 'r').read()
    our_public_key = open('keys/public.pem', 'r').read()
    our_private_key = serialization.load_pem_private_key(raw_private_key.encode(), pkpass.encode())

    log("Loaded keys from file", "KEYGEN")
except:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    our_private_key = key.private_bytes(encoding=serialization.Encoding.PEM,
                                        format=serialization.PrivateFormat.PKCS8,
                                        encryption_algorithm=serialization.BestAvailableEncryption(pkpass.encode()))
    our_public_key = key.public_key().public_bytes(encoding=serialization.Encoding.PEM,
                                                   format=serialization.PublicFormat.SubjectPublicKeyInfo)
    # Make sure the keys folder exists
    if os.path.isdir('keys') is False:
        os.mkdir('keys')
    open('keys/private.pem', 'w').write(our_private_key.decode())
    open('keys/public.pem', 'w').write(our_public_key.decode())
    log("Generated new keys", "KEYGEN")
