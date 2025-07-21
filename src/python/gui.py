"""
GUI applicativo per il Project Work 

Tkinter/Ttk con tre ruoli: Studente, Università Emittente, Università Verificatrice

Tutti gli oggetti di dominio sono singleton in SessionManager (rimangono
  vivi mentre si cambia frame/utente nella stessa sessione)

Layout: un unico container nel root gestito con `grid`

"""
from __future__ import annotations

import copy
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any

from AccreditationAuthority.accreditation_authority import AccreditationAuthority
from IssuingUniversity.issuing_university import IssuingUniversity
from VerifyingUniversity.verifying_university import VerifyingUniversity
from Student.student import Student
from Revocation.revocation import RevocationRegistry
from utils.exceptions import ProjectBaseException
from models import VerifiablePresentation

# ---------------------------------------------------------------------------
# Credenziali di accesso dimostrative {"student", "issuer", "verifier"}
# ---------------------------------------------------------------------------
ACCOUNTS: Dict[str, Dict[str, str]] = {
    "student@uni.com": {
        "password": "forzalupi",
        "role": "student",
        "name": "Francesco Monda",
    },
    "student2@uni.com": {
        "password": "forzalupi",
        "role": "student",
        "name": "Leonardo Luongo",
    },
    "issuer@uni.com": {
        "password": "forzalupi",
        "role": "issuer",
        "name": "Université de Rennes",
    },
    "verifier@uni.com": {
        "password": "forzalupi",
        "role": "verifier",
        "name": "Università di Salerno",
    },
}

# ---------------------------------------------------------------------------
# Catalogo corsi di esempio
# ---------------------------------------------------------------------------
COURSE_CATALOGUE: List[Dict[str, Any]] = [
    {"id": 1, "nome": "Algoritmi e Protocolli per la Sicurezza", "voto": 30, "cfu": 9, "data": "2024-06-18"},
    {"id": 2, "nome": "Sistemi Distribuiti", "voto": 28, "cfu": 6, "data": "2024-05-20"},
    {"id": 3, "nome": "Letteratura Francese", "voto": 25, "cfu": 6, "data": "2024-06-10"},
]



# ---------------------------------------------------------------------------
# Session manager – mantiene gli oggetti di dominio per tutta la GUI
# ---------------------------------------------------------------------------
class SessionManager:
    def __init__(self):
        print("[Session] Setup domini…")
        # Autorità di accreditamento
        self.accreditation_authority = AccreditationAuthority("EU-Accreditation-Body")

        # Università emittente accreditata
        self.issuing_uni = IssuingUniversity(
            university_id="Université de Rennes",
            accreditation_authority=self.accreditation_authority,
        )

        # Università verificatrice, che si fida dell'autorità EA
        self.verifying_uni = VerifyingUniversity("Università di Salerno")
        self.verifying_uni.add_trusted_authority(self.accreditation_authority)

        # Studente e wallet
        self.students: Dict[str, Student] = {
            e: Student(info["name"])
            for e, info in ACCOUNTS.items() if info["role"] == "student"
        }

        self.active_student: Student | None = None

        # Registro di revoca
        self.revocation_registry = RevocationRegistry()
        # In contesto di testing svuotiamo il registro
        self.revocation_registry.clear_registry_for_testing()

        # Buffer di presentazioni create (visibile alla UV)
        self.presentations: List[VerifiablePresentation] = []
        
    def get_student(self, email: str) -> Student | None:
        return self.students.get(email)

# ---------------------------------------------------------------------------
# Frame base con pulsante Logout e hook on_show
# ---------------------------------------------------------------------------
class BaseFrame(ttk.Frame):
    def __init__(self, master: "MainApp", **kwargs):
        super().__init__(master.container, padding=15, **kwargs)
        self.master_app: "MainApp" = master
        self.session: SessionManager = master.session
        ttk.Button(self, text="Logout", command=self.logout).pack(side=tk.BOTTOM, pady=8)

    def logout(self):
        self.master_app.show_frame(LoginFrame)

    def on_show(self):
        """Hook chiamato ogni volta che il frame viene portato in primo piano."""
        pass

# ---------------------------------------------------------------------------
# LoginFrame
# ---------------------------------------------------------------------------
class LoginFrame(ttk.Frame):
    def __init__(self, master: "MainApp"):
        super().__init__(master.container, padding=20)
        self.master_app = master

        ttk.Label(
            self, text="Academic Credential Manager",
            font=("Helvetica", 16, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 15))

        ttk.Label(self, text="Email:").grid(row=1, column=0, sticky="e", pady=4)
        ttk.Label(self, text="Password:").grid(row=2, column=0, sticky="e", pady=4)

        self.email_var, self.pass_var = tk.StringVar(), tk.StringVar()

        #tieni i riferimenti agli Entry
        self.email_entry = ttk.Entry(self, textvariable=self.email_var)
        self.email_entry.grid(row=1, column=1, sticky="we", pady=4)

        self.pass_entry = ttk.Entry(self, show="*", textvariable=self.pass_var)
        self.pass_entry.grid(row=2, column=1, sticky="we", pady=4)

        ttk.Button(self, text="Login", command=self._attempt_login)\
            .grid(row=3, column=0, columnspan=2, pady=12)

        self.columnconfigure(1, weight=1)

    # -------------------------------------------------------------- nuovo hook
    def on_show(self):
        """Resetta i campi e assicura lo stato normal ogni volta che si ritorna."""
        self.email_var.set("")
        self.pass_var.set("")
        self.email_entry.configure(state="normal")
        self.pass_entry.configure(state="normal")
        self.email_entry.focus_set()


    # ------------------------------------------------------------------
    def _attempt_login(self):
        email = self.email_var.get().strip().lower()
        pwd = self.pass_var.get()
        acct = ACCOUNTS.get(email)
        if not acct or acct["password"] != pwd:
            messagebox.showerror("Login fallito", "Credenziali non valide.")
            return
        messagebox.showinfo("Benvenuto", f"Login riuscito come {acct['role'].capitalize()}.")
        self.master_app.open_role_gui(acct["role"], email)

# ---------------------------------------------------------------------------
# STUDENTE -------------------------------------------------------------------
class StudentFrame(BaseFrame):
    """Frame dello studente: credenziali e presentazioni."""

    def __init__(self, master: "MainApp", student: Student):
        super().__init__(master)
        self.student = student 
        
        self.content = ttk.Frame(self)
        self.content.pack(anchor="n", pady=10, fill="x")

        # ---------------- titolo
        ttk.Label(
            self.content,
            text=f"Benvenuto {self.student.name} (Studente)",
            font=("Helvetica", 14, "bold"),
        ).pack(pady=6)

        # ---------------- listbox credenziali
        self.cred_listbox = tk.Listbox(self.content, height=4)
        self.cred_listbox.pack(pady=4, fill="x")
        self.cred_listbox.bind("<<ListboxSelect>>", self._on_select_credential)

        # ---------------- tabella corsi
        self.tree = ttk.Treeview(
            self.content,
            columns=("id", "nome", "voto", "cfu", "data"),
            show="headings",
            height=4,
        )
        self._setup_tree_columns()
        self.tree.pack(pady=4, fill="x")

        # ---------------- selezione corso + pulsante
        id_frm = ttk.Frame(self.content); id_frm.pack(pady=4)
        ttk.Label(id_frm, text="ID corso:").pack(side=tk.LEFT)
        self.course_var = tk.StringVar()
        ttk.Entry(id_frm, textvariable=self.course_var, width=6).pack(side=tk.LEFT)
        ttk.Button(
            self.content,
            text="Crea Presentazione",
            command=self.create_presentation,
        ).pack(pady=4)

        # ---------------- messaggi
        self.msg_var = tk.StringVar()
        ttk.Label(self.content, textvariable=self.msg_var, foreground="green").pack(pady=4)

    # ------------------------------------------------------------------ col helper
    def _setup_tree_columns(self):
        self.tree.heading("id",   text="ID")
        self.tree.heading("nome", text="Nome")
        self.tree.heading("voto", text="Voto")
        self.tree.heading("cfu",  text="CFU")
        self.tree.heading("data", text="Data")

        # larghezze di base; stretch per occupare tutta la larghezza
        for col, w in zip(
            ("id", "nome", "voto", "cfu", "data"),
            (50, 260, 60, 60, 90),
        ):
            anchor = "center" if col != "nome" else "w"
            self.tree.column(col, width=w, anchor=anchor, stretch=True)

    # ------------------------------------------------------------------ hook
    def on_show(self):
        self._refresh_cred_list()
        self.msg_var.set("")
        self.tree.delete(*self.tree.get_children())

    # ------------------------------------------------------------------ util
    def _refresh_cred_list(self):
        self.cred_listbox.delete(0, tk.END)
        registry = self.session.revocation_registry
        for n, cid in enumerate(self.student.wallet.credentials):
            self.cred_listbox.insert(tk.END, cid)
            if registry.is_revoked(cid):
                self.cred_listbox.itemconfig(n, fg="red")

    def _on_select_credential(self, _):
        sel = self.cred_listbox.curselection()
        if not sel:
            return
        cid = self.cred_listbox.get(sel[0])

        if self.session.revocation_registry.is_revoked(cid):
            messagebox.showerror(
                "Credenziale revocata",
                "Questa credenziale è stata revocata e non è più utilizzabile.",
            )
            return

        cred = self.student.wallet.credentials[cid]
        self.tree.delete(*self.tree.get_children())
        for course in cred.courses:
            self.tree.insert(
                "", tk.END,
                values=(
                    course["id"],
                    course["nome"],
                    course["voto"],
                    course["cfu"],
                    course["data"],
                ),
            )

    # ------------------------------------------------------------------ azione
    def create_presentation(self):
        sel = self.cred_listbox.curselection()
        if not sel:
            messagebox.showwarning("Attenzione", "Seleziona una credenziale.")
            return
        cid = self.cred_listbox.get(sel[0])

        # blocca se revocata
        if self.session.revocation_registry.is_revoked(cid):
            messagebox.showerror(
                "Credenziale revocata",
                "Impossibile creare presentazioni: la credenziale è revocata.",
            )
            return

        # ID corso valido?
        try:
            course_id = int(self.course_var.get())
        except ValueError:
            messagebox.showerror("Errore", "ID corso non valido.")
            return

        # controllo duplicato: stessa credenziale + stesso corso già presentato
        for p in self.session.presentations:
            same_credential = p.original_credential_public_part.credential_id == cid
            same_course     = p.presented_course["id"] == course_id
            if same_credential and same_course:
                messagebox.showinfo(
                    "Già presente",
                    "Hai già creato una presentazione per questo corso con la stessa credenziale.",
                )
                return

        # creazione vera e propria
        try:
            pres = self.student.wallet.create_selective_presentation(cid, course_id)
            self.session.presentations.append(pres)
            self.msg_var.set(f"Presentazione creata per corso {course_id}")
        except ProjectBaseException as exc:
            messagebox.showerror("Errore", str(exc))


# ---------------------------------------------------------------------------
# UNIVERSITÀ EMITTENTE -------------------------------------------------------
class IssuingFrame(BaseFrame):
    """Frame dell’università emittente: emissione e revoca con scelta studente."""

    def __init__(self, master: "MainApp"):
        super().__init__(master)
        self.issuer = self.session.issuing_uni

        ttk.Label(
            self,
            text=f"{self.issuer.id} - Università Emittente",
            font=("Helvetica", 14, "bold"),
        ).pack(pady=6)

        ttk.Button(
            self,
            text="Emetti credenziale a studente",
            command=self._open_issue_dialog,
        ).pack(pady=4)

        ttk.Label(self, text="Tutte le credenziali emesse:").pack()

        # ---------- nuova tabella
        self.tree = ttk.Treeview(
            self,
            columns=("idx", "pseud", "cred"),
            show="headings",
            height=6,
        )
        self.tree.heading("idx",  text="ID")
        self.tree.heading("pseud", text="Pseudonimo")
        self.tree.heading("cred", text="Credenziale")

        self.tree.column("idx",  width=50,  anchor="center", stretch=True)
        self.tree.column("pseud", width=380, anchor="w",      stretch=True)
        self.tree.column("cred", width=260, anchor="center", stretch=True)

        self.tree.pack(pady=4, fill="x")

        ttk.Button(
            self,
            text="Revoca credenziale",
            command=self._open_revoke_dialog,
        ).pack(pady=4)

    # ------------------------------------------------------------------ hook
    def on_show(self):
        self._refresh_table()

    # ------------------------------------------------------------------ util
    def _refresh_table(self):
        """Riempi la tabella con tutte le credenziali di tutti gli studenti."""
        self.tree.delete(*self.tree.get_children())
        registry = self.session.revocation_registry

        for i, (stud) in enumerate(self.session.students.values(), start=1):
            for cid in stud.wallet.credentials:
                row_id = self.tree.insert("", tk.END, values=(i, stud.pseudonym, cid))
                if registry.is_revoked(cid):
                    self.tree.item(row_id, tags=("rev",))

        # colora di rosso le revocate
        self.tree.tag_configure("rev", foreground="red")


    # ------------------------------------------------------------------ dialog di emissione
    def _open_issue_dialog(self):
        top = tk.Toplevel(self); top.title("Emetti credenziale")

        ttk.Label(top, text="Seleziona lo pseudonimo:").pack(padx=10, pady=6)

        student_lb = tk.Listbox(top, width=60, height=4)
        student_lb.pack(padx=10, pady=4)

        students = list(self.session.students.values())
        for s in students:
            student_lb.insert(tk.END, s.pseudonym)

        def _issue():
            sel = student_lb.curselection()
            if not sel:
                messagebox.showwarning("Attenzione", "Seleziona uno studente."); return
            stud = students[sel[0]]
            self.issuer.issue_credential(stud.wallet, copy.deepcopy(COURSE_CATALOGUE))
            messagebox.showinfo("Successo", f"Credenziale emessa a {stud.pseudonym}.")
            top.destroy()
            self._refresh_table()        

        ttk.Button(top, text="Emetti", command=_issue).pack(pady=6)
        ttk.Button(top, text="Annulla", command=top.destroy).pack()

    # ------------------------------------------------------------------ dialog di revoca
    def _open_revoke_dialog(self):
        top = tk.Toplevel(self); top.title("Revoca credenziale")

        ttk.Label(top, text="Seleziona lo pseudonimo:").grid(row=0, column=0, padx=10, pady=(8, 4), sticky="w")
        ttk.Label(top, text="Seleziona la credenziale:").grid(row=0, column=1, padx=10, pady=(8, 4), sticky="w")

        student_lb = tk.Listbox(top, width=60, height=8, exportselection=False)
        cred_lb    = tk.Listbox(top, width=45, height=8, exportselection=False)
        student_lb.grid(row=1, column=0, padx=10, pady=4)
        cred_lb.grid(row=1, column=1, padx=10, pady=4)

        students = list(self.session.students.values())
        registry = self.session.revocation_registry

        for s in students:
            student_lb.insert(tk.END, s.pseudonym)

        def load_creds(idx):
            cred_lb.delete(0, tk.END)
            for n, cid in enumerate(students[idx].wallet.credentials):
                cred_lb.insert(tk.END, cid)
                if registry.is_revoked(cid):
                    cred_lb.itemconfig(n, fg="red")

        if students:
            student_lb.selection_set(0); load_creds(0)

        student_lb.bind("<<ListboxSelect>>",
                        lambda _: load_creds(student_lb.curselection()[0]))

        def _revoke():
            s_sel, c_sel = student_lb.curselection(), cred_lb.curselection()
            if not s_sel or not c_sel:
                messagebox.showwarning("Attenzione", "Seleziona studente e credenziale."); return

            stud = students[s_sel[0]]; cid = cred_lb.get(c_sel[0])

            if registry.is_revoked(cid):
                messagebox.showinfo("Già revocata", "Questa credenziale è già revocata."); return

            self.issuer.revoke_credential(registry, cid)
            messagebox.showinfo("Revoca", f"Credenziale {cid} revocata per {stud.pseudonym}.")
            top.destroy()
            self._refresh_table()       

        ttk.Button(top, text="Revoca", command=_revoke).grid(row=2, column=0, columnspan=2, pady=8)
        ttk.Button(top, text="Annulla", command=top.destroy).grid(row=3, column=0, columnspan=2, pady=(0, 8))


# ---------------------------------------------------------------------------
# UNIVERSITÀ VERIFICATRICE ---------------------------------------------------
class VerifyingFrame(BaseFrame):
    """Frame dell’università verificatrice con tabella delle presentazioni."""

    def __init__(self, master: "MainApp"):
        super().__init__(master)
        self.verifier = self.session.verifying_uni

        self.content = ttk.Frame(self)
        self.content.pack(anchor="n", pady=10, fill="x")

        # ---------- titolo
        ttk.Label(
            self.content,
            text=f"{self.verifier.id} - Università Verificatrice",
            font=("Helvetica", 14, "bold"),
        ).pack(pady=6)

        # ---------- tabella presentazioni
        self.tree = ttk.Treeview(
            self.content,
            columns=("pid", "cred", "exam"),
            show="headings",
            height=6,
        )
        self.tree.heading("pid",  text="ID")
        self.tree.heading("cred", text="Credenziale")
        self.tree.heading("exam", text="Esame") 
         
        self.tree.column("pid",  width=60,  anchor="center", stretch=True)
        self.tree.column("cred", width=240, anchor="center", stretch=True) 
        self.tree.column("exam", width=260, anchor="w",      stretch=True)

        self.tree.pack(pady=4, fill="x")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # definizione tag colore
        self.tree.tag_configure("ok",   foreground="green")
        self.tree.tag_configure("fail", foreground="red")
        

        # ---------- pulsante verifica
        ttk.Button(
            self.content,
            text="Verifica presentazione",
            command=self.verify_selected,
        ).pack(pady=4)

        # ---------- risultato verifica
        self.result_var = tk.StringVar()
        self.result_lbl = ttk.Label(         
            self.content,
            textvariable=self.result_var,
            foreground="green",
        )
        self.result_lbl.pack(pady=4)

        self._current_index: int | None = None

    # ------------------------------------------------------------------ hook
    def on_show(self):
        self._refresh_table()
        self.result_var.set("")
        self._current_index = None

    # ------------------------------------------------------------------ util
    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for idx, pres in enumerate(self.session.presentations):
            full_cid   = pres.original_credential_public_part.credential_id 
            course_name = pres.presented_course["nome"]
            self.tree.insert(
                "", tk.END,
                values=(idx, full_cid, course_name),
            )

    def _on_select(self, _event):
        sel = self.tree.selection()
        self._current_index = int(self.tree.item(sel[0], "values")[0]) if sel else None

    # ------------------------------------------------------------------ azione
    def verify_selected(self):
        if self._current_index is None:
            messagebox.showwarning("Attenzione", "Seleziona una presentazione.")
            return

        # iid della riga selezionata
        row_id = self.tree.selection()[0]
        pres   = self.session.presentations[self._current_index]

        # rimuovi eventuali tag precedenti
        self.tree.item(row_id, tags="")

        try:
            self.verifier.verify_presentation(pres, self.session.revocation_registry)
            self.result_var.set("Presentazione VERIFICATA.")
            self.result_lbl.configure(foreground="green") 
            self.tree.item(row_id, tags=("ok",))      # verde
        except ProjectBaseException as exc:
            self.result_var.set(f"Fallita: {exc}")
            self.result_lbl.configure(foreground="red") 
            self.tree.item(row_id, tags=("fail",))    # rosso



# ---------------------------------------------------------------------------
# MAIN APPLICATION -----------------------------------------------------------
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Project Work APS - Gruppo 11 - IZ")
        self.minsize(620, 620)

        # Stato condiviso
        self.session = SessionManager()

        # Container principale
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)

        # Cache dei frame
        self.frames: Dict[type, ttk.Frame] = {}

        # Mappa ruolo → frame
        self.role_map = {
            "student": StudentFrame,
            "issuer": IssuingFrame,
            "verifier": VerifyingFrame, 
        }

        # Schermata di login iniziale
        login_frame = LoginFrame(self)
        self.frames[LoginFrame] = login_frame
        login_frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(LoginFrame)

    # ------------------------------------------------------------------
    def show_frame(self, frame_cls: type[ttk.Frame]):
        """Mostra (o crea) il frame richiesto."""
        if frame_cls not in self.frames:
            frame = frame_cls(self)
            self.frames[frame_cls] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        frame = self.frames[frame_cls]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

    # ------------------------------------------------------------------
    def open_role_gui(self, role: str, email: str):
        """Passa al frame specifico dopo il login."""
        if role == "student":
            # ricava l'istanza dallo user appena loggato
            stud = self.session.students.get(email)
            if not stud:
                messagebox.showerror("Errore", "Studente non trovato."); return

            self.session.active_student = stud          # <‑‑ memorizza
            frame = StudentFrame(self, stud)            # passa l’istanza
            self.frames[StudentFrame] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            self.show_frame(StudentFrame)
            return

        # issuer / verifier
        self.show_frame(self.role_map[role])
   

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
