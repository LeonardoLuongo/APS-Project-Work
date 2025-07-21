# src/python/benchmark.py
import time
import json
import os
import statistics
import sys
from typing import Dict, Any

# Importa le tue classi originali
from AccreditationAuthority.accreditation_authority import AccreditationAuthority
from IssuingUniversity.issuing_university import IssuingUniversity
from Student.student import Student
from VerifyingUniversity.verifying_university import VerifyingUniversity
from Revocation.revocation import RevocationRegistry
from Student.wallet import StudentWallet
from utils.crypto_utils import generate_rsa_keys, sign_data
from utils.credential import AcademicCredential
from typing import List


class BenchmarkIssuingUniversity(IssuingUniversity):
    def issue_credential(self, student_wallet: StudentWallet, courses: List[Dict[str, Any]]):
        """Crea, firma e rilascia una credenziale accademica a uno studente."""
        print(f"\nL'università '{self.id}' sta emettendo una credenziale per lo studente...")
        
        issuer_info = {'id': self.id, 'certificate': self.certificate}
        credential = AcademicCredential(
            issuer_info=issuer_info,
            student_pseudonym=student_wallet.pseudonym,
            courses=courses
        )

        data_to_sign = credential.get_public_part()
        signature = sign_data(self.private_key, data_to_sign)
        credential.signature = signature

        print(f"Credenziale {credential.credential_id} creata e firmata con Merkle Root: {credential.merkle_root[:10]}...")
        
        student_wallet.receive_credential(credential)
        return credential

# --- CONFIGURAZIONE DEL BENCHMARK ---
NUM_RUNS = 100  # Esegui 100 cicli per avere una media affidabile
NUM_COURSES_PER_CREDENTIAL = 10 # Testa credenziali con 10 esami

def generate_mock_courses(num_courses: int) -> list:
    """Genera una lista di corsi fittizi per il test."""
    return [{"id": i, "nome": f"Corso di Prova {i}", "voto": 28, "cfu": 6} for i in range(1, num_courses + 1)]

def run_single_cycle() -> Dict[str, float]:
    """
    Esegue un singolo ciclo completo (setup, emissione, presentazione, verifica)
    e restituisce un dizionario con le metriche di performance misurate.
    """
    # 1. SETUP DEGLI ATTORI (viene rieseguito ogni volta per isolare i test)
    ea = AccreditationAuthority(name="Benchmark-EA")
    uni_rennes = BenchmarkIssuingUniversity(university_id="Benchmark-UE", accreditation_authority=ea)
    uni_salerno = VerifyingUniversity(university_id="Benchmark-UV")
    uni_salerno.add_trusted_authority(ea)
    studente = Student(name="Benchmark-Student")
    registry = RevocationRegistry(registry_file_path='benchmark_revocation_list.json')
    registry.clear_registry_for_testing()
    courses = generate_mock_courses(NUM_COURSES_PER_CREDENTIAL)

    # 2. MISURA EMISSIONE
    start_time = time.perf_counter()
    credential_obj = uni_rennes.issue_credential(studente.wallet, courses)
    issue_latency = (time.perf_counter() - start_time) * 1000

    # 3. MISURA GENERAZIONE PRESENTAZIONE
    cred_id = credential_obj.credential_id
    course_id_to_present = NUM_COURSES_PER_CREDENTIAL // 2 # Scegliamo un corso a metà lista
    
    start_time = time.perf_counter()
    presentation = studente.wallet.create_selective_presentation(cred_id, course_id_to_present)
    presentation_latency = (time.perf_counter() - start_time) * 1000
    
    if not presentation:
        raise RuntimeError("Benchmark fallito: la presentazione non è stata creata.")

    # 4. MISURA VERIFICA COMPLETA
    start_time = time.perf_counter()
    is_valid = uni_salerno.verify_presentation(presentation, registry)
    verification_latency = (time.perf_counter() - start_time) * 1000

    if not is_valid:
        raise RuntimeError("Benchmark fallito: una verifica valida non è passata.")

    # 5. MISURA DIMENSIONI
    credential_size = len(json.dumps(credential_obj.to_dict(serializable=True)).encode('utf-8'))
    presentation_size = len(json.dumps(presentation.to_dict(serializable=True)).encode('utf-8'))

    return {
        "issue_latency": issue_latency,
        "presentation_latency": presentation_latency,
        "verification_latency": verification_latency,
        "credential_size_kb": credential_size / 1024,
        "presentation_size_kb": presentation_size / 1024,
    }

def main():
    """Funzione principale per eseguire il benchmark e stampare i risultati aggregati."""
    print(f"--- Inizio Benchmark ---")
    print(f"Configurazione: {NUM_RUNS} cicli, {NUM_COURSES_PER_CREDENTIAL} esami per credenziale.")
    
    all_metrics = []
    
    # Esegui il ciclo di benchmark
    for i in range(NUM_RUNS):
        # Reindirizza l'output standard per non inquinare la console con i print delle classi
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        try:
            metrics = run_single_cycle()
            all_metrics.append(metrics)
        except Exception as e:
            # Ripristina stdout prima di stampare l'errore
            sys.stdout.close()
            sys.stdout = original_stdout
            print(f"\nERRORE durante il ciclo {i+1}: {e}")
            return # Interrompi il benchmark in caso di errore
        finally:
            # Assicurati di ripristinare sempre stdout
            sys.stdout.close()
            sys.stdout = original_stdout
        
        # Stampa un indicatore di progresso
        print(f"\rCiclo {i+1}/{NUM_RUNS} completato.", end="")

    print("\n\n--- Fine Benchmark ---")

    # Calcolo delle statistiche aggregate
    latencies_issue = [m["issue_latency"] for m in all_metrics]
    latencies_present = [m["presentation_latency"] for m in all_metrics]
    latencies_verify = [m["verification_latency"] for m in all_metrics]
    sizes_cred = [m["credential_size_kb"] for m in all_metrics]
    sizes_pres = [m["presentation_size_kb"] for m in all_metrics]

    # Stampa dei risultati formattati per la relazione
    print("\n--- Risultati Medi delle Prestazioni ---")
    print(f"\n** Latenza Operazioni (media su {NUM_RUNS} esecuzioni) **")
    print(f"  - Emissione Credenziale:  {statistics.mean(latencies_issue):.4f} ms (dev. std: {statistics.stdev(latencies_issue):.4f})")
    print(f"  - Generazione Presentazione: {statistics.mean(latencies_present):.4f} ms (dev. std: {statistics.stdev(latencies_present):.4f})")
    print(f"  - Verifica Completa:        {statistics.mean(latencies_verify):.4f} ms (dev. std: {statistics.stdev(latencies_verify):.4f})")
    
    print(f"\n** Dimensione Dati (media su {NUM_RUNS} esecuzioni) **")
    print(f"  - Dimensione Credenziale:   {statistics.mean(sizes_cred):.4f} KB (dev. std: {statistics.stdev(sizes_cred):.4f})")
    print(f"  - Dimensione Presentazione: {statistics.mean(sizes_pres):.4f} KB (dev. std: {statistics.stdev(sizes_pres):.4f})")

    # Pulizia finale del file di revoca
    if os.path.exists('benchmark_revocation_list.json'):
        os.remove('benchmark_revocation_list.json')

if __name__ == "__main__":
    # Assicurati che il metodo issue_credential in IssuingUniversity RESTITUISCA la credenziale.
    # Se non lo fa, devi fare questa piccola modifica nel file originale.
    # Esempio in IssuingUniversity/issuing_university.py:
    #   ...
    #   student_wallet.receive_credential(credential)
    #   return credential  <-- AGGIUNGI QUESTA RIGA
    main()