import uuid
import datetime
import json 
from .merkle_tree import MerkleTree

class AcademicCredential:
    def __init__(self, issuer_info, student_pseudonym, courses):
        """
        Rappresenta una credenziale accademica verificabile.
        """
        self.credential_id = str(uuid.uuid4())
        self.issuer_info = issuer_info
        self.student_pseudonym = student_pseudonym
        # È fondamentale che i corsi siano una lista di stringhe per la libreria
        self.json_courses = [dict(sorted(course.items())) for course in courses]
        self.str_courses = [json.dumps(c, sort_keys=True) for c in courses]
        self.issue_date = datetime.datetime.utcnow().isoformat()

        self.tree = MerkleTree(self.json_courses)
        self.merkle_root = self.tree.root

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
        return self.tree.get_proof(course_data)
    
    @staticmethod
    def verify_proof(leaf_data, proof, merkle_root):
        """Verifica una prova di inclusione usando la nostra classe statica."""
        return MerkleTree.verify_proof(leaf_data, proof, merkle_root)
