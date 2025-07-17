# In src/python/utils/crypto_utils.py

import hashlib
import json
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

# --- Funzioni per Chiavi Asimmetriche (RSA) ---

def generate_rsa_keys():
    """Genera una coppia di chiavi RSA a 2048 bit."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key

def sign_data(private_key, data):
    """Firma i dati usando una chiave privata RSA."""
    # Assicuriamoci che i dati siano in bytes
    if not isinstance(data, bytes):
        data = json.dumps(data, sort_keys=True).encode('utf-8')
        
    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

def verify_signature(public_key, signature, data):
    """Verifica una firma usando la chiave pubblica RSA. Ritorna True/False."""
    # Assicuriamoci che i dati siano in bytes
    if not isinstance(data, bytes):
        data = json.dumps(data, sort_keys=True).encode('utf-8')

    try:
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        # L'eccezione InvalidSignature indica una firma non valida
        print(f"Verifica fallita: {e}")
        return False

# --- Funzioni di Hashing ---

def hash_data(data):
    """Crea un hash SHA256 dei dati."""
    # Assicuriamoci che i dati siano in bytes
    if not isinstance(data, bytes):
        # Convertiamo dizionari/liste in una stringa JSON ordinata per avere hash consistenti
        data_string = json.dumps(data, sort_keys=True).encode('utf-8')
    else:
        data_string = data
        
    return hashlib.sha256(data_string).hexdigest()

# --- Funzioni di serializzazione (opzionali ma utili) ---
# Per salvare e caricare chiavi da/per file

def key_to_pem(key):
    """Serializza una chiave (privata o pubblica) in formato PEM."""
    if isinstance(key, rsa.RSAPrivateKey):
        return key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption() # Per semplicità, non cifriamo il file della chiave
        )
    else:
        return key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )