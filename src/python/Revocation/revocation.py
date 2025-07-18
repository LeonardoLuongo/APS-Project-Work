# src/python/Revocation/revocation.py
import json
import os
from typing import Set

from config import REVOCATION_REGISTRY_FILE_PATH

class RevocationRegistry:
    def __init__(self, registry_file_path: str = REVOCATION_REGISTRY_FILE_PATH):
        """
        Simula un registro di revoca pubblico.
        Utilizza un file JSON locale per persistere la lista delle revoche.
        """
        self.file_path = registry_file_path
        self.revoked_ids: Set[str] = self._load_revocations()
        print(f"Registro di revoca inizializzato. Caricate {len(self.revoked_ids)} revoche da '{self.file_path}'.")

    def _load_revocations(self) -> Set[str]:
        """Carica la lista degli ID revocati dal file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    return set(json.load(f))
            except (json.JSONDecodeError, IOError) as e:
                print(f"Attenzione: impossibile caricare il file di revoca '{self.file_path}'. Errore: {e}. Inizio con un registro vuoto.")
                return set()
        return set()

    def _save_revocations(self):
        """Salva la lista aggiornata degli ID revocati nel file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(list(self.revoked_ids), f, indent=2)
        except IOError as e:
            print(f"Errore: impossibile salvare il file di revoca '{self.file_path}'. Errore: {e}")

    def add_revocation(self, credential_id: str):
        """Aggiunge un ID di credenziale al registro delle revoche."""
        if credential_id not in self.revoked_ids:
            self.revoked_ids.add(credential_id)
            self._save_revocations()
            print(f"REVOCA: Aggiunto credential_id '{credential_id}' al registro.")

    def is_revoked(self, credential_id: str) -> bool:
        """Controlla se un ID di credenziale è presente nel registro delle revoche."""
        return credential_id in self.revoked_ids
        
    def clear_registry_for_testing(self):
        """Metodo di utilità per pulire il registro tra un test e l'altro."""
        self.revoked_ids = set()
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
                print("Registro di revoca pulito per il test.")
            except OSError as e:
                print(f"Errore durante la pulizia del registro: {e}")
        # Ensure the file is gone so _load_revocations doesn't find it
        self._save_revocations()