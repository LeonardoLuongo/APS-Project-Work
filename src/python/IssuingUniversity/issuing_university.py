# src/python/IssuingUniversity/issuing_university.py
from typing import List, Dict, Any

from utils.crypto_utils import generate_rsa_keys, sign_data
from utils.credential import AcademicCredential
from AccreditationAuthority.accreditation_authority import AccreditationAuthority
from Student.wallet import StudentWallet
from Revocation.revocation import RevocationRegistry

class IssuingUniversity:
    def __init__(self, university_id: str, accreditation_authority: AccreditationAuthority):
        """
        Inizializza l'Università Emittente (UE).
        L'UE genera la propria coppia di chiavi e viene certificata da un EA.
        """
        self.id = university_id
        self.private_key, self.public_key = generate_rsa_keys()
        
        self.certificate = accreditation_authority.certify_university(
            self.id, self.public_key
        )
        print(f"Università Emittente '{self.id}' creata e certificata da '{accreditation_authority.name}'.")

    def issue_credential(self, student_wallet: StudentWallet, courses: List[Dict[str, Any]]):
        """Crea, firma e rilascia una credenziale accademica a uno studente."""
        print(f"\nL'università '{self.id}' sta emettendo una credenziale per lo studente...")
        
        issuer_info = {'id': self.id, 'certificate': self.certificate}
        credential = AcademicCredential(
            issuer_info=issuer_info,
            student_pseudonym=student_wallet.pseudonym,
            courses=courses
        )

        data_to_sign = credential.get_public_part()
        signature = sign_data(self.private_key, data_to_sign)
        credential.signature = signature

        print(f"Credenziale {credential.credential_id} creata e firmata con Merkle Root: {credential.merkle_root[:10]}...")
        
        student_wallet.receive_credential(credential)
    
    def revoke_credential(self, registry: RevocationRegistry, credential_id: str):
        """Registra la revoca di una credenziale."""
        print(f"\nL'università '{self.id}' sta revocando la credenziale ID: {credential_id}")
        registry.add_revocation(credential_id)