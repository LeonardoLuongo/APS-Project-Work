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

if __name__ == "__main__":
    main()
