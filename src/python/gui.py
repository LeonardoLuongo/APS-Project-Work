"""
Academic Credential Manager GUI (gui.py)
---------------------------------------
GUI completa con:
    • Login e Logout (email + password)
    • Tre ruoli indipendenti (Studente, Università Emittente, Università Verificatrice)
    • Demo integrata di emissione, presentazione selettiva, verifica e revoca

Dipendenze:
    • Python ≥ 3.10 con modulo Tk (`python-tk@X.Y` su Homebrew)
    • cryptography

Esegui con:
    python src/python/gui.py
"""
from __future__ import annotations
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext

# --- Dominio ----------------------------------------------------------------
from AccreditationAuthority.accreditation_authority import AccreditationAuthority
from IssuingUniversity.issuing_university import IssuingUniversity
from VerifyingUniversity.verifying_university import VerifyingUniversity
from Revocation.revocation import RevocationRegistry
from Student.student import Student

# =============================================================================
# Login Frame
# =============================================================================
class LoginFrame(ttk.Frame):
    """Schermata di autenticazione."""

    def __init__(self, master: "App", accounts: dict[str, dict]):
        super().__init__(master, padding=20)
        self.master = master
        self.accounts = accounts

        ttk.Label(self, text="Academic Credential Manager", font=("Helvetica", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))

        ttk.Label(self, text="Email:").grid(row=1, column=0, sticky="e", pady=4)
        ttk.Label(self, text="Password:").grid(row=2, column=0, sticky="e", pady=4)

        self.email_var = tk.StringVar()
        self.pass_var = tk.StringVar()

        ttk.Entry(self, textvariable=self.email_var).grid(row=1, column=1, sticky="we", pady=4)
        ttk.Entry(self, show="*", textvariable=self.pass_var).grid(row=2, column=1, sticky="we", pady=4)

        login_btn = ttk.Button(self, text="Login", command=self._attempt_login)
        login_btn.grid(row=3, column=0, columnspan=2, pady=12)

        self.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------
    def _attempt_login(self):
        email = self.email_var.get().strip().lower()
        pwd = self.pass_var.get()
        user = self.accounts.get(email)
        if not user or user["password"] != pwd:
            messagebox.showerror("Login fallito", "Credenziali non valide.")
            return
        messagebox.showinfo("Benvenuto", f"Login riuscito come {user['role'].capitalize()}.")
        self.master.open_role_gui(user["role"], user["name"])  # delega all'App

# =============================================================================
# Student GUI
# =============================================================================
class StudentGUI(Student):
    """Interfaccia wallet studente."""

    def __init__(self, name: str, app: "App"):
        super().__init__(name)
        self.app = app
        self.issuing_uni = app.issuing_uni
        self.verifying_uni = app.verifying_uni
        self.registry = app.registry
        self._build_ui()

    # ------------------------- UI -------------------------------------------
    def _build_ui(self):
        self._container = ttk.Frame(self.app, padding=10)
        c = self._container
        c.pack(fill="both", expand=True)

        ttk.Label(c, text=f"Wallet di {self.name}", font=("Helvetica", 14, "bold")).pack(pady=6)

        self.tree = ttk.Treeview(c, columns=("id", "issuer", "date"), show="headings", height=6)
        for col, txt, w in [("id", "Credential ID", 180), ("issuer", "Issuer", 160), ("date", "Issue Date", 100)]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w)
        self.tree.pack(fill="x", pady=5)

        btn_f = ttk.Frame(c)
        btn_f.pack(fill="x", pady=8)
        ttk.Button(btn_f, text="Emetti credenziale", command=self.ui_issue).pack(side="left", padx=4)
        ttk.Button(btn_f, text="Crea presentazione", command=self.ui_presentation).pack(side="left", padx=4)
        ttk.Button(btn_f, text="Revoca credenziale", command=self.ui_revoke).pack(side="left", padx=4)
        ttk.Button(btn_f, text="Aggiorna", command=self._refresh).pack(side="right", padx=4)
        ttk.Button(btn_f, text="Logout", command=self.logout).pack(side="right", padx=4)

        self._refresh()

    # ------------------------- lifecycle ------------------------------------
    def destroy(self):
        self._container.destroy()

    def logout(self):
        self.app.show_login()

    # ------------------------- helpers --------------------------------------
    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for cid, cred in self.wallet.credentials.items():
            self.tree.insert("", "end", values=(cid[:8] + "…", cred.issuer_info['id'], cred.issue_date.split("T")[0]))

    # ------------------------- callbacks ------------------------------------
    def ui_issue(self):
        demo_courses = [
            {"id": 1, "nome": "Algoritmi e Protocolli per la Sicurezza", "voto": 30, "cfu": 9, "data": "2024-06-18"},
            {"id": 2, "nome": "Sistemi Distribuiti", "voto": 28, "cfu": 6, "data": "2024-05-20"},
            {"id": 3, "nome": "Letteratura Francese", "voto": 25, "cfu": 6, "data": "2024-06-10"},
        ]
        self.issuing_uni.issue_credential(self.wallet, demo_courses)
        self._refresh()
        messagebox.showinfo("Credenziale emessa", "Nuova credenziale salvata nel wallet.")

    def ui_presentation(self):
        if not self.wallet.credentials:
            messagebox.showwarning("Vuoto", "Nessuna credenziale nel wallet.")
            return
        cid = simpledialog.askstring("Credential ID", "Inserisci l'ID COMPLETO della credenziale:")
        if not cid:
            return
        try:
            course_id = int(simpledialog.askinteger("Course ID", "ID del corso da presentare:"))
        except (TypeError, ValueError):
            return
        pres = self.wallet.create_selective_presentation(cid, course_id)
        if not pres:
            messagebox.showerror("Errore", "Presentazione non generata.")
            return
        ok = self.verifying_uni.verify_presentation(pres, self.registry)
        messagebox.showinfo("Risultato", "Verifica riuscita." if ok else "Verifica fallita.")

    def ui_revoke(self):
        if not self.wallet.credentials:
            messagebox.showwarning("Vuoto", "Nessuna credenziale nel wallet.")
            return
        cid = simpledialog.askstring("Revoca", "ID COMPLETO della credenziale da revocare:")
        if not cid:
            return
        if self.issuing_uni.revoke_credential(self.registry, cid):
            messagebox.showinfo("Revocata", "Credenziale revocata correttamente.")
        else:
            messagebox.showwarning("Errore", "Credenziale non trovata o già revocata.")

# =============================================================================
# Issuing‑University GUI
# =============================================================================
class IssuerGUI(IssuingUniversity):
    """Interfaccia per Università Emittente."""

    def __init__(self, university_id: str, ea: AccreditationAuthority, app: "App"):
        super().__init__(university_id, ea)
        self.app = app
        self.student = app.student  # assume demo con singolo studente
        self.registry = app.registry
        self.issued: list[str] = []
        self._build_ui()

    # ------------------------- UI -------------------------------------------
    def _build_ui(self):
        self._container = ttk.Frame(self.app, padding=10)
        c = self._container
        c.pack(fill="both", expand=True)

        ttk.Label(c, text=f"Emittente: {self.id}", font=("Helvetica", 14, "bold")).pack(pady=6)
        self.listbox = tk.Listbox(c, height=6)
        self.listbox.pack(fill="x", pady=5)

        btn_f = ttk.Frame(c)
        btn_f.pack(fill="x", pady=8)
        ttk.Button(btn_f, text="Emetti credenziale", command=self.ui_issue).pack(side="left", padx=4)
        ttk.Button(btn_f, text="Revoca credenziale", command=self.ui_revoke).pack(side="left", padx=4)
        ttk.Button(btn_f, text="Aggiorna", command=self._refresh).pack(side="right", padx=4)
        ttk.Button(btn_f, text="Logout", command=self.logout).pack(side="right", padx=4)

    def destroy(self):
        self._container.destroy()

    def logout(self):
        self.app.show_login()

    # ------------------------- helpers --------------------------------------
    def _refresh(self):
        self.listbox.delete(0, tk.END)
        for cid in self.issued:
            self.listbox.insert(tk.END, cid[:8] + "…")

    # ------------------------- callbacks ------------------------------------
    def ui_issue(self):
        courses = [
            {"id": 1, "nome": "Algoritmi e Protocolli per la Sicurezza", "voto": 30, "cfu": 9, "data": "2024-06-18"},
            {"id": 2, "nome": "Sistemi Distribuiti", "voto": 28, "cfu": 6, "data": "2024-05-20"},
        ]
        self.issue_credential(self.student.wallet, courses)
        cid = list(self.student.wallet.credentials.keys())[-1]
        self.issued.append(cid)
        self._refresh()
        messagebox.showinfo("Emessa", f"Credenziale {cid[:8]}… emessa e inviata allo studente.")

    def ui_revoke(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Seleziona", "Seleziona una credenziale da revocare.")
            return
        idx = selection[0]
        cid = self.issued[idx]
        if self.revoke_credential(self.registry, cid):
            messagebox.showinfo("Revocata", f"Credenziale {cid[:8]}… revocata.")
        else:
            messagebox.showwarning("Errore", "Impossibile revocare.")

# =============================================================================
# Verifying‑University GUI
# =============================================================================
class VerifierGUI(VerifyingUniversity):
    """Interfaccia per Università Verificatrice."""

    def __init__(self, university_id: str, ea: AccreditationAuthority, app: "App"):
        super().__init__(university_id)
        self.add_trusted_authority(ea)
        self.app = app
        self.registry = app.registry
        self._build_ui()

    # ------------------------- UI -------------------------------------------
    def _build_ui(self):
        self._container = ttk.Frame(self.app, padding=10)
        c = self._container
        c.pack(fill="both", expand=True)

        ttk.Label(c, text=f"Verificatore: {self.id}", font=("Helvetica", 14, "bold")).pack(pady=6)
        ttk.Label(c, text="Incolla la JSON Verifiable Presentation e premi 'Verifica'.").pack()

        self.txt = scrolledtext.ScrolledText(c, height=10)
        self.txt.pack(fill="both", expand=True, pady=5)

        btn_f = ttk.Frame(c)
        btn_f.pack(fill="x", pady=6)
        ttk.Button(btn_f, text="Verifica", command=self.ui_verify).pack(side="left", padx=4)
        ttk.Button(btn_f, text="Pulisci", command=lambda: self.txt.delete("1.0", tk.END)).pack(side="left", padx=4)
        ttk.Button(btn_f, text="Logout", command=self.logout).pack(side="right", padx=4)

    def destroy(self):
        self._container.destroy()

    def logout(self):
        self.app.show_login()

    # ------------------------- callbacks ------------------------------------
    def ui_verify(self):
        raw = self.txt.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("Vuoto", "Incolla prima la presentazione JSON.")
            return
        try:
            pres = json.loads(raw)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON", f"Errore di parsing JSON: {e}")
            return
        ok = self.verify_presentation(pres, self.registry)
        messagebox.showinfo("Risultato", "Verifica riuscita." if ok else "Verifica fallita.")

# =============================================================================
# Main Application
# =============================================================================
class App(tk.Tk):
    """Applicazione principale Tk."""

    def __init__(self):
        super().__init__()
        self.title("Academic Credential Manager")
        self.geometry("640x480")

        # --- attori dominio -------------------------------------------------
        self.ea = AccreditationAuthority(name="EU-Accreditation-Body")
        self.issuing_uni = None  # creati dopo studente per dipendenza ciclica minima
        self.verifying_uni = None
        self.registry = RevocationRegistry()

        # Demo: creiamo subito lo studente
        self.student = Student(name="Student")

        # ora instanziamo università
        self.issuing_uni = IssuerGUI("Université de Rennes", self.ea, self)  # ma GUI non ancora mostrata
        self.verifying_uni = VerifierGUI("Università di Salerno", self.ea, self)

        # distruggiamo GUI create per mantenerle solo come oggetti logici (non grafici)
        self.issuing_uni.destroy()
        self.verifying_uni.destroy()

        # account demo (email → pwd, role, name)
        self.accounts = {
            "f.monda@uni.com": {"password": "forzalupi", "role": "studente", "name": self.student.name},
            "issuer@univ-rennes.fr": {"password": "forzalupi", "role": "emittente", "name": "Operatore UE"},
            "verifier@unisa.it": {"password": "forzalupi", "role": "verificatore", "name": "Operatore UV"},
        }

        self.current_frame: ttk.Frame | None = None
        self.show_login()

    # ------------------------------------------------------------------
    def show_login(self):
        if self.current_frame:
            try:
                self.current_frame.destroy()
            except Exception:
                pass
        self.current_frame = LoginFrame(self, self.accounts)
        self.current_frame.pack(fill="both", expand=True)

    def open_role_gui(self, role: str, name: str):
        # distruggi frame corrente
        self.current_frame.destroy()

        if role == "studente":
            self.current_frame = StudentGUI(name, self)
        elif role == "emittente":
            # riutilizziamo oggetto IssuerGUI, ma lo ricreiamo per UI
            self.issuing_uni = IssuerGUI("Université de Rennes", self.ea, self)
            self.current_frame = self.issuing_uni
        elif role == "verificatore":
            self.verifying_uni = VerifierGUI("Università di Salerno", self.ea, self)
            self.current_frame = self.verifying_uni
        else:
            raise ValueError("Ruolo non gestito")

    # ------------------------------------------------------------------
    def run(self):
        self.mainloop()

# =============================================================================
# main entry
# =============================================================================

def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
