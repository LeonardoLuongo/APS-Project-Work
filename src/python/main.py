# src/python/main.py
import copy

# Importa tutte le classi necessarie
from AccreditationAuthority.accreditation_authority import AccreditationAuthority
from IssuingUniversity.issuing_university import IssuingUniversity
from Student.student import Student
from VerifyingUniversity.verifying_university import VerifyingUniversity
from Revocation.revocation import RevocationRegistry
from utils.exceptions import ProjectBaseException
from utils.crypto_utils import generate_rsa_keys, sign_data
from models import VerifiablePresentation
from utils.exceptions import SignatureVerificationError
from models import Certificate

def run_simulation():
    """Esegue la simulazione completa del ciclo di vita di una credenziale."""

    ##########################################################################################################################
    print("--- Inizio Simulazione: Fase di Setup ---")

    # 1. Creare l'Ente di Accreditamento (CA)
    ea = AccreditationAuthority(name="EU-Accreditation-Body")

    # 2. Creare le Università
    uni_rennes = IssuingUniversity(university_id="Université de Rennes", accreditation_authority=ea)
    uni_salerno = VerifyingUniversity(university_id="Università di Salerno")
    uni_salerno.add_trusted_authority(ea) # Salerno deve fidarsi dell'EA

    # 3. Creare lo Studente e il suo Wallet
    studente_francesco = Student(name="Francesco Monda")

    # 4. Inizializza il registro di revoca
    revocation_registry = RevocationRegistry()
    revocation_registry.clear_registry_for_testing()
    
    print("\n--- Fine Fase di Setup ---")

    # --- Fase di Emissione Credenziale ---
    print("\n--- Inizio Simulazione: Fase di Emissione Credenziale ---")

    corsi_superati = [
        {"id": 1, "nome": "Algoritmi e Protocolli per la Sicurezza", "voto": 30, "cfu": 9, "data": "2024-06-18"},
        {"id": 2, "nome": "Sistemi Distribuiti", "voto": 28, "cfu": 6, "data": "2024-05-20"}, 
        {"id": 3, "nome": "Letteratura Francese", "voto": 25, "cfu": 6, "data": "2024-06-10"} 
    ]
    uni_rennes.issue_credential(studente_francesco.wallet, corsi_superati)
    cred_id = list(studente_francesco.wallet.credentials.keys())[0]


    ##########################################################################################################################
    # --- Scenario di Successo: Presentazione e Verifica ---
    print("\n--- Inizio Simulazione: Fase di Presentazione e Verifica (Scenario di Successo) ---")
    try:
        id_esame_da_presentare = 3
        presentation = studente_francesco.wallet.create_selective_presentation(cred_id, id_esame_da_presentare)
        is_valid = uni_salerno.verify_presentation(presentation, revocation_registry)
        if is_valid:
            print(f"\nL'università di Salerno ha ACCETTATO la prova per '{presentation.presented_course['nome']}'.")
    except ProjectBaseException as e:
        print(f"\nVERIFICA FALLITA: {e}")

    ##########################################################################################################################
    # --- Scenario di Fallimento: Tentativo di Frode ---
    print("\n--- Simulazione di un tentativo di frode (manomissione) ---")
    try:
        presentazione_valida = studente_francesco.wallet.create_selective_presentation(cred_id, course_id_to_present=2)
        print("Lo studente ha generato una presentazione valida. Ora prova a manometterla...")

        # Lo studente MALEVOLO modifica il voto nel dato presentato.
        presentazione_manomessa = copy.deepcopy(presentazione_valida)
        # Sostituiamo un campo del dataclass. È un po' più verboso ma più sicuro.
        object.__setattr__(presentazione_manomessa, 'presented_course', {'id': 2, 'nome': 'Sistemi Distribuiti', 'voto': 30, 'cfu': 6, 'data': '2024-05-20'})

        print(f"Dato del corso manomesso: {presentazione_manomessa.presented_course}")
        print("\nSalerno riceve e verifica la presentazione manomessa...")
        uni_salerno.verify_presentation(presentazione_manomessa, revocation_registry)
        
        print("\nRISULTATO SCENARIO FRODE: FALLITO. La frode non è stata rilevata!")

    except ProjectBaseException as e:
        print(f"\nVERIFICA FALLITA (correttamente): {e}")
        print("\nRISULTATO SCENARIO FRODE: SUCCESSO. La frode è stata rilevata come previsto!")

    ##########################################################################################################################
    # --- Scenario di Revoca ---
    print("\n--- Simulazione di Revoca di una Credenziale ---")
    
    # Step 1: Verifica pre-revoca (dovrebbe avere successo)
    print("\nStep 1: Presentazione valida prima della revoca...")
    try:
        presentazione_pre_revoca = studente_francesco.wallet.create_selective_presentation(cred_id, course_id_to_present=2)
        is_valid = uni_salerno.verify_presentation(presentazione_pre_revoca, revocation_registry)
        print(f"Stato verifica pre-revoca: {'Successo' if is_valid else 'Fallita'}")
    except ProjectBaseException as e:
        print(f"Stato verifica pre-revoca: Fallita ({e})")

    # Step 2: L'università emittente revoca la credenziale
    print("\nStep 2: L'università emittente revoca la credenziale...")
    uni_rennes.revoke_credential(revocation_registry, cred_id)

    # Step 3: Tentativo di ripresentare la stessa credenziale (dovrebbe fallire)
    print("\nStep 3: Tentativo di ripresentare la credenziale dopo la revoca...")
    try:
        presentazione_post_revoca = studente_francesco.wallet.create_selective_presentation(cred_id, course_id_to_present=2)
        uni_salerno.verify_presentation(presentazione_post_revoca, revocation_registry)
        print("\nRISULTATO SCENARIO REVOCA: FALLITO. La revoca non è stata rilevata.")
    except ProjectBaseException as e:
        print(f"VERIFICA FALLITA (correttamente): {e}")
        print("\nRISULTATO SCENARIO REVOCA: SUCCESSO. La revoca è stata rilevata correttamente!")

    ##########################################################################################################################
    print("\n--- Simulazione di un Avversario Esterno (Forgery) ---")

    # Un hacker prova a creare una presentazione da zero senza una credenziale valida.
    # Inventa i dati e firma con la propria chiave.
    hacker_private_key, hacker_public_key = generate_rsa_keys()
    dati_inventati = {
        "credential_id": "fake-id",
        "issuer_id": "Université de Rennes", # Finge di essere Rennes
        "student_pseudonym": "fake-student",
        "merkle_root": "fake-root",
        "issue_date": "2024-01-01"
    }
    firma_falsa = sign_data(hacker_private_key, dati_inventati)

    presentazione_forgiata = VerifiablePresentation(
        type="VerifiablePresentation",
        presented_course={"id": 99, "nome": "Hacking 101", "voto": 30},
        merkle_proof=[], # Prova inventata
        original_credential_public_part=dati_inventati,
        issuer_certificate=copy.deepcopy(uni_rennes.certificate), # Usa il vero certificato di Rennes per sembrare legittimo
        credential_signature=copy.deepcopy(firma_falsa)
    )

    print("\nUn hacker presenta una credenziale completamente forgiata...")
    try:
        uni_salerno.verify_presentation(presentazione_forgiata, revocation_registry)
        print("\nRISULTATO SCENARIO FORGERY: SUCCESSO. La firma falsa è stata rilevata al CHECK 2!")
    except SignatureVerificationError as e:
        print(f"\nVERIFICA FALLITA (correttamente): {e}")
        print("\nRISULTATO SCENARIO FORGERY: FALLITO. La frode non è stata rilevata!")

    ##########################################################################################################################
    print("\n--- Simulazione di una Università Emittente Malevola (Fiducia Revocata) ---")

    # Supponiamo che l'EA scopra che Rennes si comporta male e la "banna".
    # Nella nostra simulazione, basta che Salerno la rimuova dalle sue fonti fidate.
    # Per semplicità, modifichiamo temporaneamente il certificato per renderlo invalido.
    
    certificato_invalido = Certificate(
        data=copy.deepcopy(uni_rennes.certificate.data),
        authority_name=uni_rennes.certificate.authority_name,
        signature=b'invalid_signature_bytes'  # Invalida la firma dell'EA
    )

    # Lo studente prova a presentare una credenziale (crittograficamente valida) emessa da Rennes.
    presentazione_da_ue_non_fidata = studente_francesco.wallet.create_selective_presentation(cred_id, 2)

    # Inseriamo il certificato "revocato" nella presentazione
    object.__setattr__(presentazione_da_ue_non_fidata, 'issuer_certificate', certificato_invalido)

    print("\nLo studente presenta una credenziale da un'università la cui fiducia è stata revocata...")
    try:
        uni_salerno.verify_presentation(presentazione_da_ue_non_fidata, revocation_registry)
        print("\nRISULTATO SCENARIO UE MALEVOLA: FALLITO. La frode non è stata rilevata!")
    except SignatureVerificationError as e:
        print("\nRISULTATO SCENARIO UE MALEVOLA: SUCCESSO. La mancanza di fiducia è stata rilevata al CHECK 1!")
        


if __name__ == "__main__":
    run_simulation()