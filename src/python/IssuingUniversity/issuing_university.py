###################################################################################################################
#  WPK I - Model
##################################################################################################################
# L’Università Emittente è l’entità responsabile della creazione e del rilascio delle credenziali accademiche. 
# I suoi obiettivi fondamentali sono l’emissione autentica e non ripudiabile.
# Rilasciare credenziali accademiche digitali che siano autentiche, integre e non ripudiabili, 
# tipicamente attraverso l’apposizione di firme digitali. 
# Questa funzione costituisce il nucleo del modulo di emissione.
###################################################################################################################

from utils.crypto_utils import generate_rsa_keys, sign_data
from utils.credential import AcademicCredential

class IssuingUniversity:
    def __init__(self, university_id, accreditation_authority):
        """
        Inizializza l'Università Emittente (UE).
        L'UE genera la propria coppia di chiavi e viene certificata da un EA.
        """
        self.id = university_id
        self.private_key, self.public_key = generate_rsa_keys()
        
        # L'università ottiene un certificato dall'EA
        self.certificate = accreditation_authority.certify_university(
            self.id, self.public_key
        )
        print(f"Università Emittente '{self.id}' creata e certificata da '{accreditation_authority.name}'.")
        

    def issue_credential(self, student_wallet, courses):
        """
        Crea, firma e rilascia una credenziale accademica a uno studente.
        """
        print(f"\nL'università '{self.id}' sta emettendo una credenziale per lo studente...")
        
        # 1. Crea l'oggetto credenziale. Il Merkle Tree viene costruito al suo interno.
        credential = AcademicCredential(
            issuer_info={'id': self.id, 'certificate': self.certificate},
            student_pseudonym=student_wallet.pseudonym,
            courses=courses
        )

        # 2. Firma la parte verificabile della credenziale (che contiene la Merkle Root).
        # Questo applica i concetti del Lab 2 (Firme Digitali).
        data_to_sign = credential.to_verifiable_dict()
        signature = sign_data(self.private_key, data_to_sign)
        credential.signature = signature

        print(f"Credenziale {credential.credential_id} creata e firmata con Merkle Root: {credential.merkle_root[:10]}...")
        
        # 3. "Consegna" la credenziale allo studente
        student_wallet.receive_credential(credential)
    
    def revoke_credential(self, registry, credential_id):
        """
        Registra la revoca di una credenziale.
        In un sistema reale, solo l'emittente originale avrebbe il diritto di farlo.
        """
        print(f"\nL'università '{self.id}' sta revocando la credenziale ID: {credential_id}")
        registry.add_revocation(credential_id)



