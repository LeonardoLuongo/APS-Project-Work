# src/python/Student/student.py
from .wallet import StudentWallet

class Student:
    def __init__(self, name: str):
        """Inizializza uno Studente con un nome e un wallet personale."""
        self.name = name
        self.wallet = StudentWallet(self.name)
        print(f"Studente '{self.name}' creato con il proprio wallet.")