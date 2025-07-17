###################################################################################################################
#  WPK I - Model
##################################################################################################################
# L’Università Verificatrice è l’entità che riceve e valida le credenziali presentate dagli studenti. 
# I suoi obiettivi principali comprendono la verifica affidabile. 
# Ricevere credenziali e verificarne l’autenticità e l’integrità.
###################################################################################################################


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
