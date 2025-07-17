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

