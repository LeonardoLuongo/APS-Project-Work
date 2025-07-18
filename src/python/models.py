# src/python/models.py
"""
Definisce i modelli di dati centralizzati (dataclasses) per il progetto.
"""
from dataclasses import dataclass
from typing import Dict, Any, List
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

@dataclass(frozen=True)
class CertificateData:
    """Dati contenuti all'interno di un certificato, prima della firma."""
    university_id: str
    public_key_pem: str

@dataclass(frozen=True)
class Certificate:
    """Rappresenta un certificato completo, con dati e firma dell'autorità."""
    data: CertificateData
    signature: bytes
    authority_name: str

    def get_public_key(self) -> RSAPublicKey:
        """Deserializza e restituisce l'oggetto chiave pubblica dall'PEM."""
        from cryptography.hazmat.primitives import serialization
        return serialization.load_pem_public_key(self.data.public_key_pem.encode('utf-8'))

@dataclass(frozen=True)
class VerifiableCredentialPublicPart:
    """La parte pubblica e firmabile di una credenziale."""
    credential_id: str
    issuer_id: str
    student_pseudonym: str
    merkle_root: str
    issue_date: str

@dataclass(frozen=True)
class VerifiablePresentation:
    """Rappresenta una presentazione selettiva creata da uno studente per un verificatore."""
    type: str
    presented_course: Dict[str, Any]
    merkle_proof: List[Dict[str, str]]
    original_credential_public_part: VerifiableCredentialPublicPart
    issuer_certificate: Certificate
    credential_signature: bytes