###################################################################################################################
#  WPK I - Model
##################################################################################################################
# Lo Studente rappresenta l’utente primario del sistema, 
# il cui interesse principale risiede nella gestione autonoma e sicura delle proprie attestazioni accademiche. 
# Gli obiettivi per lo Studente includono l’acquisizione e la custodia sicura, 
# ossia ottenere credenziali accademiche digitali rilasciate dalla propria università di origine. 
# Tali credenziali dovrebbero essere conservate in modo sicuro,
# preferibilmente in un wallet digitale personale, 
# la cui implementazione potrebbe variare da soluzioni software a hardware wallet 
# per un livello di sicurezza superiore, seguendo le direttive del W3C VC Data Model.
###################################################################################################################

from .wallet import StudentWallet

class Student:
    def __init__(self, name):
        """Inizializza uno Studente con un nome e un wallet personale."""
        self.name = name
        self.wallet = StudentWallet(self.name)
        print(f"Studente '{self.name}' creato con il proprio wallet.")
