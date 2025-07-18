# src/python/utils/exceptions.py
"""
Definisce le eccezioni personalizzate per il progetto per una gestione degli errori più chiara.
"""

class ProjectBaseException(Exception):
    """Classe base per le eccezioni di questo progetto."""
    pass

class SignatureVerificationError(ProjectBaseException):
    """Sollevata quando la verifica di una firma digitale fallisce."""
    pass

class CredentialNotFoundError(ProjectBaseException):
    """Sollevata quando una credenziale non viene trovata (es. nel wallet)."""
    pass

class CourseNotFoundError(ProjectBaseException):
    """Sollevata quando un corso specifico non è presente in una credenziale."""
    pass

class MerkleProofError(ProjectBaseException):
    """Sollevata quando una prova di Merkle non è valida."""
    pass

class UntrustedAuthorityError(ProjectBaseException):
    """Sollevata quando un certificato proviene da un'autorità non fidata."""
    pass

class CredentialRevokedError(ProjectBaseException):
    """Sollevata quando si tenta di verificare una credenziale revocata."""
    pass