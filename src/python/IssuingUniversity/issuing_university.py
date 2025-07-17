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

