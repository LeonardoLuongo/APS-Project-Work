###################################################################################################################
#  WPK I - Model
################################################################################################################## 
# Le credenziali dello studente dovrebbero essere conservate in modo sicuro,
# preferibilmente in un wallet digitale personale, 
# la cui implementazione potrebbe variare da soluzioni software a hardware wallet 
# per un livello di sicurezza superiore, seguendo le direttive del W3C VC Data Model.
###################################################################################################################

from utils.crypto_utils import generate_rsa_keys, sign_data, hash_data
from cryptography.hazmat.primitives import serialization

class StudentWallet:
    def __init__(self, student_id):
        """
        Inizializza il wallet digitale dello studente.
        Il wallet gestisce le chiavi e le credenziali.
        """
        self.owner_id = student_id
        self.private_key, self.public_key = generate_rsa_keys()
        
        # L'identificatore pseudonimo dello studente (Subject ID nella credenziale)
        # può essere un hash della sua chiave pubblica.
        self.pseudonym = hash_data(
            self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )
        
        self.credentials = {} # Un dizionario per conservare le credenziali per ID
        print(f"Wallet creato per lo studente '{self.owner_id}' con pseudonym '{self.pseudonym[:10]}...'.")
    
    def receive_credential(self, credential):
        """
        Riceve e salva una nuova credenziale nel wallet.
        In un sistema reale, qui avverrebbe anche una verifica della firma.
        """
        # Per ora, la aggiungiamo semplicemente al nostro "database" di credenziali.
        self.credentials[credential.credential_id] = credential
        print(f"Wallet di '{self.owner_id}': ricevuta e salvata la credenziale {credential.credential_id}.")

    def create_selective_presentation(self, credential_id, course_id_to_present):
        """
        Crea una "Presentazione Verificabile" per un corso specifico.
        """
        
        if credential_id not in self.credentials:
            print("Errore: Credenziale non trovata nel wallet.")
            return None

        credential = self.credentials[credential_id]

        presented_course_data = next((c for c in credential.json_courses if c.get("id") == course_id_to_present), None)
    
        if presented_course_data is None:
            print(f"Errore: Il corso '{course_id_to_present}' non è stato trovato.")
            return None
        
        # Genera la prova di inclusione per il corso richiesto
        proof = credential.generate_proof_for_course(presented_course_data)

        if proof is None:
            print(f"Errore: Il corso {presented_course_data['nome']} non è stato trovato nella credenziale.")
            return None
            
        # La presentazione contiene tutto ciò che serve al verificatore
        presentation = {
            "type": "VerifiablePresentation",
            "presented_course": presented_course_data.copy(),
            "merkle_proof": proof.copy(),  # Copia per evitare modifiche accidentali
            "original_credential_public_part": credential.to_verifiable_dict().copy(),
            "issuer_certificate": credential.issuer_info['certificate'].copy(),
            "credential_signature": credential.signature
        }
        
        print(f"\nWallet di '{self.owner_id}': creata presentazione per il corso '{presented_course_data['nome']}'.")
        return presentation
