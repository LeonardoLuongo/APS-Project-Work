"""
Academic Credential Manager GUI (gui.py)
---------------------------------------
* Login / Logout con persistenza file‑system
* Tre ruoli: Studente, Università Emittente, Università Verificatrice
* Demo integrata: emissione, presentazione selettiva, verifica, revoca

Dipendenze:
    • Python ≥ 3.10 (+ Tk → `python-tk@X.Y` per Homebrew)
    • cryptography

Persistenza:
    • `accounts.json`  – credenziali (email, password SHA‑256, ruolo, nome)
    • (facolt.) puoi estendere con `state.pkl` per salvare wallet/registro revoca

Esecuzione:
    python src/python/gui.py
"""
from __future__ import annotations
import json, hashlib, os, pickle, tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext

# --- Dominio ---------------------------------------------------------------
from AccreditationAuthority.accreditation_authority import AccreditationAuthority
from IssuingUniversity.issuing_university import IssuingUniversity
from VerifyingUniversity.verifying_university import VerifyingUniversity
from Revocation.revocation import RevocationRegistry
from Student.student import Student

# =============================================================================
# Helper per persistenza credenziali utente
# =============================================================================
ACCOUNTS_FILE = "accounts.json"

def _pwd_hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

def load_accounts() -> dict[str, dict]:
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE) as f:
            return json.load(f)
    # Primo avvio → crea account demo
    demo = {
        "student@example.com":  {"password": _pwd_hash("student123"),  "role": "studente",    "name": "Demo Student"},
        "issuer@example.com":   {"password": _pwd_hash("issuer123"),   "role": "emittente",   "name": "Operatore UE"},
        "verifier@example.com": {"password": _pwd_hash("verifier123"), "role": "verificatore", "name": "Operatore UV"},
    }
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(demo, f, indent=2)
    return demo

# =============================================================================
# Login Frame
# =============================================================================
class LoginFrame(ttk.Frame):
    def __init__(self, master: "App", accounts: dict[str, dict]):
        super().__init__(master, padding=20)
        self.master = master
        self.accounts = accounts

        ttk.Label(self, text="Academic Credential Manager", font=("Helvetica", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))
        ttk.Label(self, text="Email:").grid(row=1, column=0, sticky="e", pady=4)
        ttk.Label(self, text="Password:").grid(row=2, column=0, sticky="e", pady=4)

        self.email_var = tk.StringVar(); self.pass_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.email_var).grid(row=1, column=1, sticky="we", pady=4)
        ttk.Entry(self, show="*", textvariable=self.pass_var).grid(row=2, column=1, sticky="we", pady=4)
        ttk.Button(self, text="Login", command=self._attempt_login).grid(row=3, column=0, columnspan=2, pady=12)
        self.columnconfigure(1, weight=1)

    def _attempt_login(self):
        email = self.email_var.get().strip().lower(); pwd = self.pass_var.get()
        user = self.accounts.get(email)
        if not user or user["password"] != _pwd_hash(pwd):
            messagebox.showerror("Login fallito", "Credenziali non valide.")
            return
        messagebox.showinfo("Benvenuto", f"Login riuscito come {user['role'].capitalize()}.")
        self.master.open_role_gui(user["role"], user["name"], email)

# =============================================================================
# Student GUI (eredita Student)
# =============================================================================
class StudentGUI(Student):
    def __init__(self, name: str, app: "App"):
        super().__init__(name)
        self.app = app
        self._container: ttk.Frame | None = None  # creato lazy

    # ------------------------- UI -------------------------------------------
    def _build_ui(self):
        if self._container:  # già costruita → ripack
            self._container.pack(fill="both", expand=True)
            self._refresh(); return
        c = self._container = ttk.Frame(self.app, padding=10)
        c.pack(fill="both", expand=True)
        ttk.Label(c, text=f"Wallet di {self.name}", font=("Helvetica", 14, "bold")).pack(pady=6)

        self.tree = ttk.Treeview(c, columns=("id","issuer","date"), show="headings", height=6)
        for col, txt, w in [("id","Credential ID",180),("issuer","Issuer",160),("date","Issue Date",100)]:
            self.tree.heading(col, text=txt); self.tree.column(col, width=w)
        self.tree.pack(fill="x", pady=5)

        btn_f = ttk.Frame(c); btn_f.pack(fill="x", pady=8)
        ttk.Button(btn_f, text="Emetti credenziale demo", command=self.ui_issue).pack(side="left", padx=4)
        ttk.Button(btn_f, text="Crea presentazione", command=self.ui_presentation).pack(side="left", padx=4)
        ttk.Button(btn_f, text="Revoca credenziale", command=self.ui_revoke).pack(side="left", padx=4)
        ttk.Button(btn_f, text="Aggiorna", command=self._refresh).pack(side="right", padx=4)
        ttk.Button(btn_f, text="Logout", command=self.logout).pack(side="right", padx=4)
        self._refresh()

    def logout(self):
        self._container.pack_forget(); self.app.save_state(); self.app.show_login()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for cid, cred in self.wallet.credentials.items():
            self.tree.insert("", "end", values=(cid[:8]+"…", cred.issuer_info['id'], cred.issue_date.split("T")[0]))

    # ------------------------- callbacks ------------------------------------
    def ui_issue(self):
        demo_courses=[{"id":1,"nome":"Algoritmi e Protocolli per la Sicurezza","voto":30,"cfu":9,"data":"2024-06-18"},{"id":2,"nome":"Sistemi Distribuiti","voto":28,"cfu":6,"data":"2024-05-20"}]
        self.app.issuing_uni.issue_credential(self.wallet, demo_courses)
        self._refresh(); messagebox.showinfo("Credenziale emessa","Nuova credenziale nel wallet.")

    def ui_presentation(self):
        if not self.wallet.credentials:
            messagebox.showwarning("Vuoto","Nessuna credenziale."); return
        cid=simpledialog.askstring("Credential ID","ID completo credenziale:");
        if not cid: return
        try: course_id=int(simpledialog.askinteger("Course ID","ID corso da presentare:"))
        except (TypeError,ValueError): return
        pres=self.wallet.create_selective_presentation(cid, course_id)
        if not pres: messagebox.showerror("Errore","Presentazione non generata."); return
        ok=self.app.verifying_uni.verify_presentation(pres,self.app.registry)
        messagebox.showinfo("Risultato","Verifica riuscita." if ok else "Verifica fallita.")

    def ui_revoke(self):
        if not self.wallet.credentials:
            messagebox.showwarning("Vuoto","Nessuna credenziale."); return
        cid=simpledialog.askstring("Revoca","ID completo da revocare:");
        if not cid: return
        if self.app.issuing_uni.revoke_credential(self.app.registry,cid):
            messagebox.showinfo("Revocata","Credenziale revocata.")
        else: messagebox.showwarning("Errore","Credenziale non trovata o già revocata.")

# =============================================================================
# Issuer GUI (aggregazione IssuingUniversity)
# =============================================================================
class IssuerGUI:
    def __init__(self, issuer: IssuingUniversity, app: "App"):
        self.issuer=issuer; self.app=app; self.issued: list[str]=[]; self._container=None

    def _build_ui(self):
        if self._container:
            self._container.pack(fill="both", expand=True); self._refresh(); return
        c=self._container=ttk.Frame(self.app,padding=10); c.pack(fill="both", expand=True)
        ttk.Label(c,text=f"Emittente: {self.issuer.id}",font=("Helvetica",14,"bold")).pack(pady=6)
        self.listbox=tk.Listbox(c,height=6); self.listbox.pack(fill="x", pady=5)
        btn_f=ttk.Frame(c); btn_f.pack(fill="x", pady=8)
        ttk.Button(btn_f,text="Emetti credenziale demo",command=self.ui_issue).pack(side="left", padx=4)
        ttk.Button(btn_f,text="Revoca credenziale",command=self.ui_revoke).pack(side="left", padx=4)
        ttk.Button(btn_f,text="Aggiorna",command=self._refresh).pack(side="right", padx=4)
        ttk.Button(btn_f,text="Logout",command=self.logout).pack(side="right", padx=4)

    def logout(self):
        self._container.pack_forget(); self.app.save_state(); self.app.show_login()

    def _refresh(self):
        self.listbox.delete(0,tk.END);
        for cid in self.issued: self.listbox.insert(tk.END,cid[:8]+"…")

    def ui_issue(self):
        courses=[{"id":1,"nome":"Algoritmi e Protocolli per la Sicurezza","voto":30,"cfu":9,"data":"2024-06-18"}]
        target_wallet=self.app.student_gui.wallet if self.app.student_gui else None
        if not target_wallet:
            messagebox.showwarning("Studente","Lo studente non ha ancora eseguito l'accesso."); return
        self.issuer.issue_credential(target_wallet,courses); cid=list(target_wallet.credentials.keys())[-1]
        self.issued.append(cid); self._refresh(); messagebox.showinfo("Emessa",f"Credenziale {cid[:8]}… emessa.")

    def ui_revoke(self):
        sel=self.listbox.curselection();
        if not sel: messagebox.showwarning("Seleziona","Seleziona una credenziale."); return
        cid=self.issued[sel[0]];
        if self.issuer.revoke_credential(self.app.registry,cid): messagebox.showinfo("Revocata",f"{cid[:8]}… revocata.")
        else: messagebox.showwarning("Errore","Impossibile revocare.")

# =============================================================================
# Verifier GUI (aggregazione VerifyingUniversity)
# =============================================================================
class VerifierGUI:
    def __init__(self, verifier: VerifyingUniversity, app: "App"):
        self.verifier=verifier; self.app=app; self._container=None

    def _build_ui(self):
        if self._container: self._container.pack(fill="both", expand=True); return
        c=self._container=ttk.Frame(self.app,padding=10); c.pack(fill="both", expand=True)
        ttk.Label(c,text=f"Verificatore: {self.verifier.id}",font=("Helvetica",14,"bold")).pack(pady=6)
        ttk.Label(c,text="Incolla la JSON Verifiable Presentation e premi 'Verifica'.").pack()
        self.txt=scrolledtext.ScrolledText(c,height=10); self.txt.pack(fill="both", expand=True,pady=5)
        btn_f=ttk.Frame(c); btn_f.pack(fill="x", pady=6)
        ttk.Button(btn_f,text="Verifica",command=self.ui_verify).pack(side="left", padx=4)
        ttk.Button(btn_f,text="Pulisci",command=lambda:self.txt.delete("1.0",tk.END)).pack(side="left", padx=4)
        ttk.Button(btn_f,text="Logout",command=self.logout).pack(side="right", padx=4)

    def logout(self):
        self._container.pack_forget(); self.app.save_state(); self.app.show_login()

    def ui_verify(self):
        raw=self.txt.get("1.0",tk.END).strip()
        if not raw: messagebox.showwarning("Vuoto","Incolla JSON."); return
        try: pres=json.loads(raw)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON",f"Errore parsing: {e}"); return
        ok=self.verifier.verify_presentation(pres,self.app.registry)
        messagebox.showinfo("Risultato","Verifica riuscita." if ok else "Verifica fallita.")

# =============================================================================
# Main Application
# =============================================================================
class App(tk.Tk):
    STATE_FILE="state.pkl"  # opzionale per salvare wallet, revoche…

    def __init__(self):
        super().__init__(); self.title("Academic Credential Manager"); self.geometry("640x480")
        # Dominio
        self.ea=AccreditationAuthority("EU-Accreditation-Body")
        self.issuing_uni=IssuingUniversity("Université de Rennes", self.ea)
        self.verifying_uni=VerifyingUniversity("Università di Salerno"); self.verifying_uni.add_trusted_authority(self.ea)
        self.registry=RevocationRegistry()
        # GUI placeholders
        self.student_gui: StudentGUI|None=None; self.issuer_gui: IssuerGUI|None=None; self.verifier_gui: VerifierGUI|None=None
        # accounts
        self.accounts=load_accounts()
        # espone frame corrente
        self.current_frame: ttk.Frame|None=None
        self.show_login()

    # ====================== session helpers ================================
    def save_state(self):
        # placeholder: serializza solo lista revoche
        data={"revoked": list(self.registry.revoked_ids)}
        with open(self.STATE_FILE,"wb") as f: pickle.dump(data,f)

    # ====================== navigation ====================================
    def show_login(self):
        if self.current_frame: self.current_frame.pack_forget()
        self.current_frame=LoginFrame(self,self.accounts); self.current_frame.pack(fill="both", expand=True)

    def open_role_gui(self, role: str, name: str, email:str):
        if self.current_frame: self.current_frame.pack_forget()
        if role=="studente":
            if not self.student_gui: self.student_gui=StudentGUI(name,self)
            self.student_gui._build_ui(); self.current_frame=self.student_gui._container
        elif role=="emittente":
            if not self.issuer_gui: self.issuer_gui=IssuerGUI(self.issuing_uni,self)
            self.issuer_gui._build_ui(); self.current_frame=self.issuer_gui._container
        elif role=="verificatore":
            if not self.verifier_gui: self.verifier_gui=VerifierGUI(self.verifying_uni,self)
            self.verifier_gui._build_ui(); self.current_frame=self.verifier_gui._container
        else: raise ValueError("Ruolo non supportato")

    def run(self): self.mainloop()

# =============================================================================
# entry‑point
# =============================================================================

def main():
    App().run()

if __name__=="__main__":
    main()
