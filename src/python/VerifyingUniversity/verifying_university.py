# src/python/VerifyingUniversity/verifying_university.py
from typing import Dict
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from utils.crypto_utils import verify_signature
from utils.credential import AcademicCredential
from utils.exceptions import (
    SignatureVerificationError, MerkleProofError, UntrustedAuthorityError, CredentialRevokedError
)
from AccreditationAuthority.accreditation_authority import AccreditationAuthority
from Revocation.revocation import RevocationRegistry
from models import VerifiablePresentation

class VerifyingUniversity:
    def __init__(self, university_id: str):
        """Inizializza l'Università Verificatrice (UV)."""
        self.id = university_id
        self.trusted_authorities: Dict[str, RSAPublicKey] = {}
        print(f"Università Verificatrice '{self.id}' creata.")

    def add_trusted_authority(self, authority: AccreditationAuthority):
        """Aggiunge un Ente di Accreditamento all'elenco di quelli fidati."""
        self.trusted_authorities[authority.name] = authority.public_key
        print(f"'{self.id}' ora si fida di '{authority.name}'.")

    def verify_presentation(self, presentation: VerifiablePresentation, registry: RevocationRegistry) -> bool:
        """
        Verifica una presentazione selettiva ricevuta da uno studente.
        Esegue 4 controlli sequenziali. Ritorna True se tutti passano.
        Solleva un'eccezione specifica al primo fallimento.
        """
        # print(f"\n'{self.id}' sta verificando una presentazione per lo studente con pseudonym: {presentation['original_credential_public_part']['student_pseudonym']}")

        # --- CHECK 1: Fiducia nell'Emittente (Trust in CA) ---
        issuer_cert = presentation.issuer_certificate
        authority_name = issuer_cert.authority_name
        
        if authority_name not in self.trusted_authorities:
            raise UntrustedAuthorityError(f"L'ente '{authority_name}' non è nella lista di quelli fidati.")
        
        authority_public_key = self.trusted_authorities[authority_name]
        verify_signature(authority_public_key, issuer_cert.signature, issuer_cert.data)
        print("CHECK 1/4: Fiducia nell'emittente... OK.")

        # --- CHECK 2: Firma della Credenziale (Issuer Signature) ---
        issuer_public_key = issuer_cert.get_public_key()
        try:
            verify_signature(
                issuer_public_key, 
                presentation.credential_signature, 
                presentation.original_credential_public_part
            )
        except SignatureVerificationError as e:
            raise e
        
        print("CHECK 2/4: Firma della credenziale... OK.")

        # --- CHECK 3: Prova di Inclusione (Merkle Proof) ---
        public_part = presentation.original_credential_public_part
        if not AcademicCredential.verify_proof(presentation.presented_course, presentation.merkle_proof, public_part.merkle_root):
            raise MerkleProofError("La prova di inclusione del corso non è valida.")
        print("CHECK 3/4: Prova di inclusione del corso... OK.")
        
        # --- CHECK 4: Controllo Stato di Revoca ---
        credential_id = public_part.credential_id
        if registry.is_revoked(credential_id):
            raise CredentialRevokedError(f"La credenziale ID {credential_id} è stata revocata.")
        print("CHECK 4/4: Stato di revoca... OK (non revocata).")

        print("\nRISULTATO: SUCCESSO! La presentazione è valida e verificata.")
        return True