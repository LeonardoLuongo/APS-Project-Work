import uuid
import datetime
from pymerkle import InmemoryTree as MerkleTree
import json 

class AcademicCredential:
    def __init__(self, issuer_info, student_pseudonym, courses):
        """
        Rappresenta una credenziale accademica verificabile.
        """
        self.credential_id = str(uuid.uuid4())
        self.issuer_info = issuer_info
        self.student_pseudonym = student_pseudonym
        # È fondamentale che i corsi siano una lista di stringhe per la libreria
        self.courses = [json.dumps(c, sort_keys=True) for c in courses]
        self.issue_date = datetime.datetime.utcnow().isoformat()

        # --- Integrazione del Merkle Tree (con la libreria 'pymerkle') ---
        # 1. pymerkle gestisce internamente la conversione, non dobbiamo fare nulla
        self.tree = MerkleTree()
        for course_str in self.courses:
            # Aggiungiamo i dati all'albero. pymerkle li hasherà per noi.
            # Convertiamo il dizionario in una stringa JSON ordinata per consistenza.
            self.tree.append_entry(course_str.encode('utf-8'))
        
        # 2. Otteniamo la Merkle Root (pymerkle la fornisce come stringa esadecimale)
        self.merkle_root = self.tree.get_state().hex()

        # La firma non è ancora presente, verrà aggiunta dall'emittente
        self.signature = None 

    def to_verifiable_dict(self):
        """Restituisce un dizionario con i dati che verranno firmati."""
        return {
            "credential_id": self.credential_id,
            "issuer_id": self.issuer_info['id'],
            "student_pseudonym": self.student_pseudonym,
            "merkle_root": self.merkle_root,
            "issue_date": self.issue_date
        }

    def generate_proof_for_course(self, course_data):
        """Genera una prova di inclusione per un corso specifico."""
        course_str = json.dumps(course_data, sort_keys=True)
        try:
            # La libreria ha bisogno dell'indice della foglia per generare la prova
            leaf_index = self.courses.index(course_str)
            proof = self.tree.get_proof(leaf_index)
            return proof
        except ValueError:
            # Il corso non è stato trovato nella credenziale
            return None
