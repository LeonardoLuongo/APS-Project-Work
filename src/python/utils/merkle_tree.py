
import hashlib
import json

def _hash_function(data):
    """Funzione di hashing interna, consistente in tutto il progetto."""
    if isinstance(data, dict) or isinstance(data, list):
        # Forma canonica: chiavi ordinate, nessun spazio.
        data_string = json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
    elif not isinstance(data, bytes):
        data_string = str(data).encode('utf-8')
    else:
        data_string = data
    return hashlib.sha256(data_string).hexdigest()

class MerkleTree:
    def __init__(self, data_list):
        """
        Costruisce un Merkle Tree da una lista di dati.
        Args:
            data_list (list): Lista di dati originali (es. i dizionari dei corsi).
        """
        self.data_list = data_list
        self.leaves = [_hash_function(json.dumps(d, sort_keys=True)) for d in self.data_list]
        self.tree = self._build_tree()
        self.root = self.tree[0] if self.tree else None

    def _build_tree(self):
        """Costruisce l'albero livello per livello."""
        if not self.leaves:
            return []
        
        level = self.leaves[:]
        tree = [level]
        
        while len(level) > 1:
            if len(level) % 2 != 0:
                level.append(level[-1]) # Duplica l'ultimo se dispari
            
            next_level = []
            for i in range(0, len(level), 2):
                combined_hash = _hash_function(level[i] + level[i+1])
                next_level.append(combined_hash)
            
            level = next_level
            tree.insert(0, level) # Inserisce i livelli più alti all'inizio della lista
            
        return tree[0] # Restituisce solo il livello della radice

    def get_proof(self, data_to_prove):
        """
        Genera una Merkle Proof per un dato specifico.
        La proof è una lista di tuple (hash, posizione).
        """
        try:
            leaf_hash = _hash_function(json.dumps(data_to_prove, sort_keys=True))
            index = self.leaves.index(leaf_hash)
        except ValueError:
            return None # Il dato non è nell'albero

        proof = []
        current_level_nodes = self.leaves[:]
        
        while len(current_level_nodes) > 1:
            if len(current_level_nodes) % 2 != 0:
                current_level_nodes.append(current_level_nodes[-1])

            is_right_node = index % 2
            sibling_index = index - 1 if is_right_node else index + 1
            
            if sibling_index < len(current_level_nodes):
                proof.append({
                    'hash': current_level_nodes[sibling_index],
                    'position': 'left' if is_right_node else 'right'
                })

            # Passa al livello successivo
            next_level = []
            for i in range(0, len(current_level_nodes), 2):
                 next_level.append(_hash_function(current_level_nodes[i] + current_level_nodes[i+1]))
            
            current_level_nodes = next_level
            index = index // 2
            
        return proof

    @staticmethod
    def verify_proof(data_to_verify, proof, root):
        """
        Verifica una Merkle Proof.
        """
        computed_hash = _hash_function(json.dumps(data_to_verify, sort_keys=True))
        
        for p in proof:
            if p['position'] == 'left':
                computed_hash = _hash_function(p['hash'] + computed_hash)
            elif p['position'] == 'right':
                computed_hash = _hash_function(computed_hash + p['hash'])
            else:
                return False

        return computed_hash == root