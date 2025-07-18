###################################################################################################################
#  WPK I - Model
##################################################################################################################
# L’Università Verificatrice è l’entità che riceve e valida le credenziali presentate dagli studenti. 
# I suoi obiettivi principali comprendono la verifica affidabile. 
# Ricevere credenziali e verificarne l’autenticità e l’integrità.
###################################################################################################################

from utils.crypto_utils import verify_signature
from utils.credential import AcademicCredential

class VerifyingUniversity:
    def __init__(self, university_id):
        """
        Inizializza l'Università Verificatrice (UV).
        """
        self.id = university_id
        self.trusted_authorities = {} # Dizionario per le chiavi pubbliche degli EA fidati
        print(f"Università Verificatrice '{self.id}' creata.")

    def add_trusted_authority(self, authority):
        """Aggiunge un Ente di Accreditamento all'elenco di quelli fidati."""
        self.trusted_authorities[authority.name] = authority.public_key
        print(f"'{self.id}' ora si fida di '{authority.name}'.")

    def verify_presentation(self, presentation, registry):
        """
        Verifica una presentazione selettiva ricevuta da uno studente.
        Esegue 3 controlli: fiducia nell'emittente, firma della credenziale, e prova di inclusione.
        """
        print(f"\n'{self.id}' sta verificando una presentazione...")

        try:
            # --- CHECK 1: Fiducia nell'Emittente (Concetto dal Lab 3: CA) ---
            issuer_cert = presentation['issuer_certificate']
            authority_name = issuer_cert['authority_name']
            
            if authority_name not in self.trusted_authorities:
                print(f"RISULTATO: FALLITO. L'ente di accreditamento '{authority_name}' non è fidato.")
                return False
            
            authority_public_key = self.trusted_authorities[authority_name]
            
            # Verifichiamo la firma dell'EA sul certificato dell'università emittente
            if not verify_signature(authority_public_key, issuer_cert['signature'], issuer_cert['data']):
                print("RISULTATO: FALLITO. Il certificato dell'università emittente non è valido.")
                return False
            print("CHECK 1/4: Fiducia nell'emittente... OK.")

            # --- CHECK 2: Firma della Credenziale (Concetto dal Lab 2: Firme) ---
            # Dobbiamo ottenere la chiave pubblica dell'emittente dal suo certificato
            from cryptography.hazmat.primitives import serialization
            issuer_public_key_pem = issuer_cert['data']['public_key_pem'].encode('utf-8')
            issuer_public_key = serialization.load_pem_public_key(issuer_public_key_pem)

            if not verify_signature(issuer_public_key, presentation['credential_signature'], presentation['original_credential_public_part']):
                print("RISULTATO: FALLITO. La firma sulla credenziale non è valida.")
                return False
            print("CHECK 2/4: Firma della credenziale... OK.")

            # --- CHECK 3: Prova di Inclusione (Concetto dal Lab 5: Merkle Tree) ---
            merkle_root = presentation['original_credential_public_part']['merkle_root']
            presented_course = presentation['presented_course']
            proof = presentation['merkle_proof'] # La prova è già un dizionario/lista JSON
            
            # Usiamo il nostro metodo statico di verifica
            if not AcademicCredential.verify_proof(presented_course, proof, merkle_root):
                print("RISULTATO: FALLITO. La Merkle proof non è valida.")
                return False
            print("CHECK 3/4: Prova di inclusione del corso... OK.")

            print("\nRISULTATO: SUCCESSO! La presentazione è valida e verificata.")

            # --- CHECK 4: Controllo Stato di Revoca ---
            credential_id = presentation['original_credential_public_part']['credential_id']
            if registry.is_revoked(credential_id):
                print("CHECK 4/4: Stato di revoca...\nRISULTATO: FALLITO. La credenziale è stata revocata.")
                return False
            
            print("CHECK 4/4: Stato di revoca... OK (non revocata).")

            print("\nRISULTATO: SUCCESSO! La presentazione è valida e verificata.")
            return True

        except Exception as e:
            print(f"RISULTATO: FALLITO. Errore durante la verifica: {e}")
            return False
