# src/python/utils/crypto_utils.py
"""
Funzioni di utilità per operazioni crittografiche come hashing, generazione di chiavi e firme.
"""
import hashlib
import json
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.exceptions import InvalidSignature

from config import KEY_SIZE, PUBLIC_EXPONENT
from .exceptions import SignatureVerificationError

def hash_data(data: any) -> str:
    """Crea un hash SHA256 dei dati in modo deterministico."""
    if not isinstance(data, bytes):
        data_string = json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
    else:
        data_string = data
    return hashlib.sha256(data_string).hexdigest()

def generate_rsa_keys() -> tuple[RSAPrivateKey, RSAPublicKey]:
    """Genera una coppia di chiavi RSA."""
    private_key = rsa.generate_private_key(
        public_exponent=PUBLIC_EXPONENT,
        key_size=KEY_SIZE,
    )
    public_key = private_key.public_key()
    return private_key, public_key

def sign_data(private_key: RSAPrivateKey, data: any) -> bytes:
    """Firma i dati usando una chiave privata RSA."""
    if not isinstance(data, bytes):
        data_bytes = json.dumps(data, sort_keys=True, default=lambda o: o.__dict__).encode('utf-8')
    else:
        data_bytes = data
        
    return private_key.sign(
        data_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

def verify_signature(public_key: RSAPublicKey, signature: bytes, data: any):
    """
    Verifica una firma usando la chiave pubblica RSA.
    Solleva SignatureVerificationError in caso di fallimento.
    """
    if not isinstance(data, bytes):
        data_bytes = json.dumps(data, sort_keys=True, default=lambda o: o.__dict__).encode('utf-8')
    else:
        data_bytes = data

    try:
        public_key.verify(
            signature,
            data_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    except InvalidSignature as e:
        raise SignatureVerificationError(f"Verifica della firma fallita: {e}")

def key_to_pem(key: RSAPrivateKey | RSAPublicKey) -> str:
    """Serializza una chiave (privata o pubblica) in formato PEM string."""
    if isinstance(key, RSAPrivateKey):
        pem_bytes = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    else:
        pem_bytes = key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    return pem_bytes.decode('utf-8')