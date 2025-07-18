# In src/python/main.py

# Importa tutte le classi
from AccreditationAuthority.accreditation_authority import AccreditationAuthority
from IssuingUniversity.issuing_university import IssuingUniversity
from Student.student import Student
from VerifyingUniversity.verifying_university import VerifyingUniversity
from Revocation.revocation import RevocationRegistry

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

    # 4. Inizializza il registro di revoca
    revocation_registry = RevocationRegistry()

    # Pulisci il registro all'inizio di ogni esecuzione per avere test puliti
    revocation_registry.clear_registry_for_testing()
    
    print("\n--- Fine Fase di Setup ---")
    print("Attori creati e pronti per interagire.")

    print("\n--- Inizio Simulazione: Fase di Emissione Credenziale ---")

    # Dati degli esami superati da Francesco a Rennes
    corsi_superati = [
        {"id": 1, "nome": "Algoritmi e Protocolli per la Sicurezza", "voto": 30, "cfu": 9, "data": "2024-06-18"},
        {"id": 2, "nome": "Sistemi Distribuiti", "voto": 28, "cfu": 6, "data": "2024-05-20"},
        {"id": 3, "nome": "Letteratura Francese", "voto": 25, "cfu": 6, "data": "2024-06-10"}
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

    print("\n--- Inizio Simulazione: Fase di Presentazione e Verifica ---")

    # Lo studente Francesco deve presentare solo l'esame di Sistemi Distribuiti a Salerno
    id_esame_da_presentare = 1 # Prendiamo il secondo esame dalla lista
    
    # 1. Il wallet di Francesco crea la presentazione selettiva
    presentation = studente_francesco.wallet.create_selective_presentation(cred_id, id_esame_da_presentare)
    
    if presentation:
        # 2. Francesco "invia" la presentazione all'Università di Salerno
        # 3. Salerno esegue la verifica completa
        is_valid = uni_salerno.verify_presentation(presentation, revocation_registry)

        if is_valid:
            print(f"\nL'università di Salerno ha accettato la prova per il corso '{presentation['presented_course']['nome']}'.")
        else:
            print(f"\nL'università di Salerno ha rifiutato la prova per il corso '{presentation['presented_course']['nome']}'.")
            
    # --- Scenario di Fallimento: Prova a presentare un dato non valido ---
    print("\n--- Simulazione di un tentativo di frode (manomissione post-creazione) ---")

    # 1. Lo studente genera una presentazione VALIDA per il corso con id=2.
    id_esame_da_manipolare = 2
    presentazione_valida = studente_francesco.wallet.create_selective_presentation(cred_id, id_esame_da_manipolare)

    if presentazione_valida:
        print("Lo studente ha generato una presentazione valida. Ora prova a manometterla...")
        
        # 2. Lo studente MALEVOLO modifica il voto nel dato presentato.
        #    La prova (merkle_proof) rimane quella originale, ma il dato è alterato.
        presentazione_manomessa = presentazione_valida.copy() # Lavoriamo su una copia
        presentazione_manomessa['presented_course']['voto'] = 30 # Altera il voto da 28 a 30
        
        print(f"Dato del corso manomesso: {presentazione_manomessa['presented_course']}")

        # 3. Lo studente invia la presentazione MANOMESSA a Salerno.
        print("\nSalerno riceve e verifica la presentazione manomessa...")
        is_valid_manomessa = uni_salerno.verify_presentation(presentazione_manomessa, revocation_registry)

        if not is_valid_manomessa:
            print("\nRISULTATO SCENARIO FRODE: SUCCESSO. La frode è stata rilevata come previsto!")
        else:
            print("\nRISULTATO SCENARIO FRODE: FALLITO. La frode non è stata rilevata!")
    
    # --- Scenario di Revoca ---
    print("\n--- Simulazione di Revoca di una Credenziale ---")

    # 1. Lo studente presenta la sua credenziale VALIDA (ID 2) e la verifica ha successo.
    print("\nStep 1: Presentazione valida prima della revoca...")
    id_esame = 2
    presentazione_pre_revoca = studente_francesco.wallet.create_selective_presentation(cred_id, id_esame)
    if presentazione_pre_revoca:
        # Passiamo il registro al metodo di verifica
        is_valid = uni_salerno.verify_presentation(presentazione_pre_revoca, revocation_registry)
        print(f"Stato verifica pre-revoca: {'Successo' if is_valid else 'Fallita'}")

    # 2. L'Università di Rennes decide di REVOCARE la credenziale di Francesco.
    print("\nStep 2: L'università emittente revoca la credenziale...")
    uni_rennes.revoke_credential(revocation_registry, cred_id)

    # 3. Lo studente (magari ignaro) prova a ripresentare la stessa credenziale.
    print("\nStep 3: Tentativo di ripresentare la credenziale dopo la revoca...")
    presentazione_post_revoca = studente_francesco.wallet.create_selective_presentation(cred_id, id_esame)
    if presentazione_post_revoca:
        # La verifica ora dovrebbe fallire al CHECK 4.
        is_valid_post = uni_salerno.verify_presentation(presentazione_post_revoca, revocation_registry)
        
        if not is_valid_post:
            print("\nRISULTATO SCENARIO REVOCA: SUCCESSO. La revoca è stata rilevata correttamente!")
        else:
            print("\nRISULTATO SCENARIO REVOCA: FALLITO. La revoca non è stata rilevata.")


if __name__ == "__main__":
    main()
