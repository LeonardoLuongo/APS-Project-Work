# src/python/config.py
"""
Modulo per le costanti di configurazione del progetto.
"""

# Configurazione per RSA
KEY_SIZE = 2048
PUBLIC_EXPONENT = 65537

# Configurazione per il registro di revoca
REVOCATION_REGISTRY_FILE_PATH = 'revocation_list.json'