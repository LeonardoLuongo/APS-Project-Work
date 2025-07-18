# src/python/utils/merkle_tree.py
"""
Implementazione di un Merkle Tree per generare e verificare prove di inclusione.
"""
from typing import List, Dict, Any, Optional
from .crypto_utils import hash_data

class MerkleTree:
    def __init__(self, data_list: List[Dict[str, Any]]):
        """Costruisce un Merkle Tree da una lista di dati (es. dizionari dei corsi)."""
        self.data_list = data_list
        self.leaves = [hash_data(d) for d in self.data_list]
        self.tree = self._build_tree()
        self.root = self.tree[0][0] if self.tree and self.tree[0] else None

    def _build_tree(self) -> List[List[str]]:
        """Costruisce l'albero livello per livello, dal basso verso l'alto."""
        if not self.leaves:
            return []
        
        levels = [self.leaves[:]]
        current_level = self.leaves[:]
        
        while len(current_level) > 1:
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])
            
            next_level = []
            for i in range(0, len(current_level), 2):
                combined_hash = hash_data(current_level[i] + current_level[i+1])
                next_level.append(combined_hash)
            
            levels.append(next_level)
            current_level = next_level
            
        return list(reversed(levels))

    def get_proof(self, data_to_prove: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
        """Genera una Merkle Proof per un dato specifico."""
        try:
            leaf_hash = hash_data(data_to_prove)
            index = self.leaves.index(leaf_hash)
        except ValueError:
            return None

        proof = []
        for i in range(len(self.tree) - 1, 0, -1):
            level = self.tree[i]
            is_right_node = index % 2
            sibling_index = index - 1 if is_right_node else index + 1
            
            if sibling_index < len(level):
                proof.append({
                    'hash': level[sibling_index],
                    'position': 'left' if is_right_node else 'right'
                })
            index //= 2
            
        return proof

    @staticmethod
    def verify_proof(data_to_verify: Dict[str, Any], proof: List[Dict[str, str]], root: str) -> bool:
        """Verifica una Merkle Proof."""
        computed_hash = hash_data(data_to_verify)
        
        for p in proof:
            sibling_hash = p['hash']
            if p['position'] == 'left':
                computed_hash = hash_data(sibling_hash + computed_hash)
            elif p['position'] == 'right':
                computed_hash = hash_data(computed_hash + sibling_hash)
            else:
                return False

        return computed_hash == root