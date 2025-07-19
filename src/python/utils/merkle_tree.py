import hashlib
import json
from typing import List, Dict, Any, Optional
from utils.crypto_utils import hash_data


class MerkleTree:
    def __init__(self, data_list: List[Dict[str, Any]]):
        self.data_list = data_list
        self.leaves = [hash_data(d) for d in self.data_list]
        self.root = self._calculate_root(self.leaves)

    def _calculate_root(self, hashes: List[str]) -> Optional[str]:
        """Metodo ricorsivo per calcolare la Merkle Root."""
        if not hashes:
            return None
        if len(hashes) == 1:
            return hashes[0]

        next_level = []
        # Applica il padding se la lista è dispari
        if len(hashes) % 2 == 1:
            hashes.append(hashes[-1])

        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i+1]
            next_level.append(hash_data(combined))
        
        return self._calculate_root(next_level)

    def get_proof(self, data_to_prove: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
        """Genera una Merkle Proof per un dato specifico."""
        try:
            current_hash = hash_data(data_to_prove)
            idx = self.leaves.index(current_hash)
        except ValueError:
            return None # Il dato non è nell'albero

        proof = []
        current_level_hashes = self.leaves[:]

        while len(current_level_hashes) > 1:
            # Applica il padding se il livello attuale è dispari
            if len(current_level_hashes) % 2 == 1:
                current_level_hashes.append(current_level_hashes[-1])

            if idx % 2 == 0: # Nodo a sinistra
                sibling_hash = current_level_hashes[idx + 1]
                proof.append({'hash': sibling_hash, 'position': 'right'})
            else: # Nodo a destra
                sibling_hash = current_level_hashes[idx - 1]
                proof.append({'hash': sibling_hash, 'position': 'left'})
            
            # Passa al livello successivo
            next_level = []
            for i in range(0, len(current_level_hashes), 2):
                combined = current_level_hashes[i] + current_level_hashes[i+1]
                next_level.append(hash_data(combined))
            
            current_level_hashes = next_level
            idx = idx // 2
            
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


