# In src/python/main.py

# Importa tutte le classi
from AccreditationAuthority.accreditation_authority import AccreditationAuthority
from IssuingUniversity.issuing_university import IssuingUniversity
from Student.student import Student
from VerifyingUniversity.verifying_university import VerifyingUniversity

def main():
    print("--- Inizio Simulazione: Fase di Setup ---")

    # 1. Creare l'Ente di Accreditamento (l'autorità suprema)
    ea = AccreditationAuthority(name="EU-Accreditation-Body")

    # 2. Creare le Università
    # L'Università di Rennes viene creata e automaticamente certificata dall'EA
    uni_rennes = IssuingUniversity(university_id="Université de Rennes", accreditation_authority=ea)
    
    # L'Università di Salerno si prepara a verificare
    uni_salerno = VerifyingUniversity(university_id="Università di Salerno")
    
    # Salerno deve sapere di chi fidarsi! Aggiunge l'EA alla sua lista.
    uni_salerno.add_trusted_authority(ea)

    # 3. Creare lo Studente
    studente_francesco = Student(name="Francesco Monda")
    
    print("\n--- Fine Fase di Setup ---")
    print("Attori creati e pronti per interagire.")

    print("\n--- Inizio Simulazione: Fase di Emissione Credenziale ---")

    # Dati degli esami superati da Francesco a Rennes
    corsi_superati = [
        {"nome": "Algoritmi e Protocolli per la Sicurezza", "voto": 30, "cfu": 9, "data": "2024-06-18"},
        {"nome": "Sistemi Distribuiti", "voto": 28, "cfu": 6, "data": "2024-05-20"},
        {"nome": "Letteratura Francese", "voto": 25, "cfu": 6, "data": "2024-06-10"}
    ]

    # L'Università di Rennes emette la credenziale e la invia al wallet di Francesco
    uni_rennes.issue_credential(studente_francesco.wallet, corsi_superati)

    # Verifichiamo che il wallet dello studente contenga la credenziale
    print(f"Il wallet di Francesco ora contiene {len(studente_francesco.wallet.credentials)} credenziali.")
    # Prendiamo l'ID della prima (e unica) credenziale per ispezionarla
    cred_id = list(studente_francesco.wallet.credentials.keys())[0]
    received_credential = studente_francesco.wallet.credentials[cred_id]
    print(f"Dettagli credenziale ricevuta (ID: {received_credential.credential_id}):")
    print(f"  - Emessa da: {received_credential.issuer_info['id']}")
    print(f"  - Merkle Root: {received_credential.merkle_root}")
    print(f"  - Firma valida? {'Sì' if received_credential.signature else 'No'}")


if __name__ == "__main__":
    main()
