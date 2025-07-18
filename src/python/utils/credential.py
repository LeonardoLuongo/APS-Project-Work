# src/python/utils/credential.py
import uuid
import datetime
from typing import List, Dict, Any, Optional

from .merkle_tree import MerkleTree
from models import Certificate, VerifiableCredentialPublicPart

class AcademicCredential:
    def __init__(self, issuer_info: Dict[str, Any], student_pseudonym: str, courses: List[Dict[str, Any]]):
        """Rappresenta una credenziale accademica verificabile."""
        self.credential_id = str(uuid.uuid4())
        self.issuer_info: Certificate = issuer_info['certificate']
        self.issuer_id: str = issuer_info['id']
        self.student_pseudonym = student_pseudonym
        
        # Ordina i dizionari per garantire hash consistenti
        self.courses = [dict(sorted(course.items())) for course in courses]
        
        self.issue_date = datetime.datetime.utcnow().isoformat()

        # Costruisci il Merkle Tree
        self.tree = MerkleTree(self.courses)
        self.merkle_root = self.tree.root

        self.signature: Optional[bytes] = None

    def get_public_part(self) -> VerifiableCredentialPublicPart:
        """Restituisce un dataclass con i dati pubblici e firmabili."""
        return VerifiableCredentialPublicPart(
            credential_id=self.credential_id,
            issuer_id=self.issuer_id,
            student_pseudonym=self.student_pseudonym,
            merkle_root=self.merkle_root,
            issue_date=self.issue_date
        )

    def generate_proof_for_course(self, course_data: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
        """Genera una prova di inclusione per un corso specifico."""
        return self.tree.get_proof(course_data)
    
    @staticmethod
    def verify_proof(leaf_data: Dict[str, Any], proof: List[Dict[str, str]], merkle_root: str) -> bool:
        """Delega la verifica della prova di inclusione a MerkleTree."""
        return MerkleTree.verify_proof(leaf_data, proof, merkle_root)