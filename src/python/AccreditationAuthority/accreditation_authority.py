# src/python/AccreditationAuthority/accreditation_authority.py
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from utils.crypto_utils import generate_rsa_keys, sign_data, key_to_pem
from models import Certificate, CertificateData

class AccreditationAuthority:
    def __init__(self, name: str):
        """Inizializza l'Ente di Accreditamento (EA)."""
        self.name = name
        self.private_key, self.public_key = generate_rsa_keys()
        print(f"Ente di Accreditamento '{self.name}' creato.")

    def certify_university(self, university_id: str, university_public_key: RSAPublicKey) -> Certificate:
        """
        Firma la chiave pubblica di un'università, creando un certificato.
        Questo certificato attesta che l'EA riconosce l'università.
        """
        certificate_data = CertificateData(
            university_id=university_id,
            public_key_pem=key_to_pem(university_public_key)
        )
        
        signature = sign_data(self.private_key, certificate_data)
        
        certified_university = Certificate(
            data=certificate_data,
            signature=signature,
            authority_name=self.name
        )
        
        print(f"L'EA '{self.name}' ha certificato l'università '{university_id}'.")
        return certified_university