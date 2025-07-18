# src/python/Student/wallet.py
from typing import Dict, Any

from utils.crypto_utils import generate_rsa_keys, key_to_pem, hash_data
from utils.credential import AcademicCredential
from utils.exceptions import CredentialNotFoundError, CourseNotFoundError
from models import VerifiablePresentation

class StudentWallet:
    def __init__(self, student_id: str):
        """Inizializza il wallet digitale dello studente."""
        self.owner_id = student_id
        self.private_key, self.public_key = generate_rsa_keys()
        
        # Identificatore pseudonimo basato sulla chiave pubblica
        self.pseudonym = hash_data(key_to_pem(self.public_key))
        
        self.credentials: Dict[str, AcademicCredential] = {}
        print(f"Wallet creato per lo studente '{self.owner_id}' con pseudonym '{self.pseudonym[:10]}...'.")
    
    def receive_credential(self, credential: AcademicCredential):
        """Riceve e salva una nuova credenziale nel wallet."""
        self.credentials[credential.credential_id] = credential
        print(f"Wallet di '{self.owner_id}': ricevuta e salvata la credenziale {credential.credential_id}.")

    def create_selective_presentation(self, credential_id: str, course_id_to_present: int) -> VerifiablePresentation:
        """
        Crea una "Presentazione Verificabile" (in formato dataclass) per un corso specifico.
        Solleva CredentialNotFoundError o CourseNotFoundError in caso di problemi.
        """
        if credential_id not in self.credentials:
            raise CredentialNotFoundError(f"Credenziale con ID {credential_id} non trovata nel wallet.")

        credential = self.credentials[credential_id]

        # Cerca il corso per ID
        presented_course_data = next((c for c in credential.courses if c.get("id") == course_id_to_present), None)
    
        if presented_course_data is None:
            raise CourseNotFoundError(f"Corso con ID '{course_id_to_present}' non trovato nella credenziale.")
        
        proof = credential.generate_proof_for_course(presented_course_data)
        if proof is None:
            # Questo non dovrebbe accadere se il corso è stato trovato, ma è una salvaguardia
            raise CourseNotFoundError("Impossibile generare la prova di Merkle per il corso.")
            
        presentation = VerifiablePresentation(
            type="VerifiablePresentation",
            presented_course=presented_course_data,
            merkle_proof=proof,
            original_credential_public_part=credential.get_public_part(),
            issuer_certificate=credential.issuer_info,
            credential_signature=credential.signature
        )
        
        print(f"\nWallet di '{self.owner_id}': creata presentazione per il corso '{presented_course_data['nome']}'.")
        return presentation