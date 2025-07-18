import json
import os

class RevocationRegistry:
    def __init__(self, registry_file_path='revocation_list.json'):
        """
        Simula un registro di revoca pubblico e immutabile (es. DLT/Blockchain).
        Utilizza un file JSON locale per persistere la lista delle revoche.
        """
        self.file_path = registry_file_path
        self._load_revocations()
        print(f"Registro di revoca inizializzato. Caricate {len(self.revoked_ids)} revoche.")

    def _load_revocations(self):
        """Carica la lista degli ID revocati dal file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                self.revoked_ids = set(json.load(f))
        else:
            self.revoked_ids = set()

    def _save_revocations(self):
        """Salva la lista aggiornata degli ID revocati nel file."""
        with open(self.file_path, 'w') as f:
            json.dump(list(self.revoked_ids), f, indent=2)

    def add_revocation(self, credential_id):
        """
        Aggiunge un ID di credenziale al registro delle revoche.
        Questa operazione è append-only.
        """
        if credential_id not in self.revoked_ids:
            self.revoked_ids.add(credential_id)
            self._save_revocations()
            print(f"REVOCA: Aggiunto credential_id '{credential_id}' al registro.")
            return True
        return False

    def is_revoked(self, credential_id):
        """
        Controlla se un ID di credenziale è presente nel registro delle revoche.
        """
        return credential_id in self.revoked_ids
        
    def clear_registry_for_testing(self):
        """Metodo di utilità per pulire il registro tra un test e l'altro."""
        self.revoked_ids = set()
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
        print("Registro di revoca pulito per il test.")
