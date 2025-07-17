###################################################################################################################
#  WPK I - Model
##################################################################################################################
# Sebbene non direttamente coinvolti nel flusso primario di emissione e verifica delle singole credenziali, 
# gli Enti di Accreditamento svolgono un ruolo di supporto cruciale, 
# ossia la verifica dell’accreditamento dell’issuer (UE). 
# Gli Enti di Accreditamento agiscono come entità che pubblica 
# o rende verificabile lo stato di accreditamento di un’Università Emittente. 
# Ciò permette alle UV di stabilire con certezza se un determinato emittente sia riconosciuto 
# e autorizzato a rilasciare specifiche tipologie di credenziali. 
###################################################################################################################

from utils.crypto_utils import generate_rsa_keys, sign_data
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives import hashes, serialization

class AccreditationAuthority:
    def __init__(self, name):
        """
        Inizializza l'Ente di Accreditamento (EA).
        L'EA ha una propria coppia di chiavi per firmare i certificati delle università.
        """
        self.name = name
        self.private_key, self.public_key = generate_rsa_keys()
        print(f"Ente di Accreditamento '{self.name}' creato.")

    def certify_university(self, university_id, university_public_key: RSAPublicKey):
        """
        Firma la chiave pubblica di un'università, creando un "certificato".
        Questo certificato attesta che l'EA riconosce l'università.
        """
        # Per ora, il certificato è un semplice dizionario con i dati essenziali.
        # In un sistema reale, questo sarebbe un certificato X.509.
        certificate_data = {
            "university_id": university_id,
            "public_key_pem": university_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
        }
        
        signature = sign_data(self.private_key, certificate_data)
        
        # Il certificato "rilasciato" è l'insieme dei dati e della firma
        certified_university = {
            "data": certificate_data,
            "signature": signature,
            "authority_name": self.name
        }
        
        print(f"L'EA '{self.name}' ha certificato l'università '{university_id}'.")
        return certified_university
