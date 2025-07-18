import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# --- Import delle classi di dominio esistenti ---
from AccreditationAuthority.accreditation_authority import AccreditationAuthority
from IssuingUniversity.issuing_university import IssuingUniversity
from VerifyingUniversity.verifying_university import VerifyingUniversity
from Revocation.revocation import RevocationRegistry
from Student.student import Student


class StudentGUI(Student):
    """Interfaccia grafica che estende la classe `Student` esistente."""

    def __init__(self, name: str, master: tk.Misc,
                 issuing_university: IssuingUniversity,
                 verifying_university: VerifyingUniversity,
                 revocation_registry: RevocationRegistry):
        # Inizializza la logica di dominio ereditata
        super().__init__(name)

        # Riferimenti agli altri attori del sistema
        self.master = master
        self.issuing_university = issuing_university
        self.verifying_university = verifying_university
        self.revocation_registry = revocation_registry

        # Costruisci l'interfaccia
        self._build_ui()

    # ------------------------------------------------------------
    # Costruzione interfaccia (Tkinter + ttk)
    # ------------------------------------------------------------
    def _build_ui(self):
        container = ttk.Frame(self.master, padding=10)
        container.pack(fill="both", expand=True)

        # Titolo
        ttk.Label(container, text=f"Wallet di {self.name}",
                  font=("Helvetica", 16, "bold")).pack(pady=5)

        # Tabella delle credenziali
        self.tree = ttk.Treeview(container, columns=("id", "issuer", "date"),
                                 show="headings", height=6)
        self.tree.heading("id", text="Credential ID")
        self.tree.heading("issuer", text="Issuer")
        self.tree.heading("date", text="Issue Date")
        self.tree.column("id", width=180)
        self.tree.pack(fill="x", pady=5)

        # Pulsanti di azione
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill="x", pady=8)

        ttk.Button(btn_frame, text="Emetti credenziale",
                   command=self.issue_credential_ui).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Crea presentazione",
                   command=self.create_presentation_ui).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Revoca credenziale",
                   command=self.revoke_credential_ui).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Aggiorna",
                   command=self._refresh_tree).pack(side="right", padx=5)

        self._refresh_tree()

    # ------------------------------------------------------------
    # Metodi helper per la GUI
    # ------------------------------------------------------------
    def _refresh_tree(self):
        """Aggiorna la tabella con le credenziali attualmente nel wallet."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for cred_id, cred in self.wallet.credentials.items():
            self.tree.insert("", "end",
                             values=(cred_id[:8] + "...", cred.issuer_info['id'],
                                     cred.issue_date.split("T")[0]))

    # ------------------------------------------------------------
    # CALLBACK: Emissione credenziale demo
    # ------------------------------------------------------------
    def issue_credential_ui(self):
        """Simula l'emissione di una credenziale demo dall'università emittente."""
        demo_courses = [
            {"id": 1, "nome": "Algoritmi e Protocolli per la Sicurezza", "voto": 30, "cfu": 9, "data": "2024-06-18"},
            {"id": 2, "nome": "Sistemi Distribuiti", "voto": 28, "cfu": 6, "data": "2024-05-20"},
            {"id": 3, "nome": "Letteratura Francese", "voto": 25, "cfu": 6, "data": "2024-06-10"}
        ]
        self.issuing_university.issue_credential(self.wallet, demo_courses)
        self._refresh_tree()
        messagebox.showinfo("Credenziale emessa", "Nuova credenziale salvata nel wallet.")

    # ------------------------------------------------------------
    # CALLBACK: Creazione presentazione selettiva
    # ------------------------------------------------------------
    def create_presentation_ui(self):
        if not self.wallet.credentials:
            messagebox.showwarning("Nessuna credenziale", "Il wallet è vuoto.")
            return
        cred_id = simpledialog.askstring("ID credenziale", "Inserisci l'ID COMPLETO della credenziale:")
        if not cred_id:
            return
        course_id = simpledialog.askinteger("ID corso", "Inserisci l'ID del corso da presentare:")
        if course_id is None:
            return
        presentation = self.wallet.create_selective_presentation(cred_id, course_id)
        if not presentation:
            messagebox.showerror("Errore", "Impossibile generare la presentazione richieste.")
            return
        ok = self.verifying_university.verify_presentation(presentation, self.revocation_registry)
        if ok:
            messagebox.showinfo("Verifica riuscita", "La presentazione è valida e accettata.")
        else:
            messagebox.showwarning("Verifica fallita", "La presentazione NON è valida.")

    # ------------------------------------------------------------
    # CALLBACK: Revoca credenziale
    # ------------------------------------------------------------
    def revoke_credential_ui(self):
        if not self.wallet.credentials:
            messagebox.showwarning("Nessuna credenziale", "Il wallet è vuoto.")
            return
        cred_id = simpledialog.askstring("Revoca credenziale", "Inserisci l'ID COMPLETO della credenziale da revocare:")
        if not cred_id:
            return
        if self.issuing_university.revoke_credential(self.revocation_registry, cred_id):
            messagebox.showinfo("Revoca registrata", "La credenziale è stata revocata correttamente.")
        else:
            messagebox.showwarning("Revoca non eseguita", "Credenziale non trovata o già revocata.")


# -----------------------------------------------------------------------------
# Applicazione principale
# -----------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Academic Credential Manager")
        self.geometry("650x420")

        # Setup attori simulati (come in main.py)
        ea = AccreditationAuthority("EU-Accreditation-Body")
        issuing_uni = IssuingUniversity("Université de Rennes", ea)
        verifying_uni = VerifyingUniversity("Università di Salerno")
        verifying_uni.add_trusted_authority(ea)
        registry = RevocationRegistry()
        registry.clear_registry_for_testing()

        # Interfaccia studente
        StudentGUI("Francesco Monda", self, issuing_uni, verifying_uni, registry)


if __name__ == "__main__":
    App().mainloop()
