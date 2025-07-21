# src/python/models.py
"""
Definisce i modelli di dati centralizzati (dataclasses) per il progetto.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey


@dataclass(frozen=True)
class CertificateData:
    """Dati contenuti all'interno di un certificato, prima della firma."""
    university_id: str
    public_key_pem: str

    def to_dict(self) -> Dict[str, Any]:
        """Converte la dataclass in un dizionario."""
        return asdict(self)

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
    
    def to_dict(self, serializable: bool = False) -> Dict[str, Any]:
        """
        Converte la dataclass in un dizionario.
        Se serializable=True, converte i campi bytes in stringhe esadecimali per il JSON.
        """
        # Converti ricorsivamente le dataclass annidate in dizionari
        data = {
            "data": self.data.to_dict(),
            "signature": self.signature,
            "authority_name": self.authority_name
        }
        
        if serializable:
            data['signature'] = self.signature.hex()
            
        return data

@dataclass(frozen=True)
class VerifiableCredentialPublicPart:
    """La parte pubblica e firmabile di una credenziale."""
    credential_id: str
    issuer_id: str
    student_pseudonym: str
    merkle_root: str
    issue_date: str

    def to_dict(self) -> Dict[str, Any]:
        """Converte la dataclass in un dizionario."""
        return asdict(self)

@dataclass(frozen=True)
class VerifiablePresentation:
    """Rappresenta una presentazione selettiva creata da uno studente per un verificatore."""
    type: str
    presented_course: Dict[str, Any]
    merkle_proof: List[Dict[str, str]]
    original_credential_public_part: VerifiableCredentialPublicPart
    issuer_certificate: Certificate
    credential_signature: bytes

    def to_dict(self, serializable: bool = False) -> Dict[str, Any]:
        """
        Converte la dataclass in un dizionario.
        Se serializable=True, converte ricorsivamente e gestisce i campi bytes.
        """
        if not serializable:
            # Se non dobbiamo serializzare per JSON, asdict è sufficiente
            return asdict(self)

        # Se dobbiamo serializzare, dobbiamo gestire i tipi complessi manualmente
        data = {
            "type": self.type,
            "presented_course": self.presented_course,
            "merkle_proof": self.merkle_proof,
            # Chiama ricorsivamente .to_dict() per gli oggetti annidati
            "original_credential_public_part": self.original_credential_public_part.to_dict(),
            "issuer_certificate": self.issuer_certificate.to_dict(serializable=True),
            # Converte i bytes della firma in esadecimale
            "credential_signature": self.credential_signature.hex()
        }
        return data