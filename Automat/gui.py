import json
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from tickets import main as load_tickets, list_folders, DEFAULT_FOLDER
from dotenv import load_dotenv
import os

try:
    import pythoncom   # kommt mit pywin32, nötig für Outlook in einem Thread
except ImportError:
    pythoncom = None

# Switch-Modelle, die links angezeigt werden – hier anpassen
SWITCH_MODELS = [
    "C9200CX-12P-2X2G-A",
    "C9300L-24P-4X-A",
    "C9300L-48P-4X-A",
    "C9500-16X-A",
    "C9410R-96U-BNDL-A",
    "Cisco Linecard C9400-LC-48U",
]


class ToggleSwitch(tk.Canvas):
    """Schiebeschalter mit zwei Optionen: links / rechts."""

    def __init__(self, master, left="include", right="exact", bg="#dcdad5"):
        super().__init__(master, width=50, height=24, highlightthickness=0, bg=bg, cursor="hand2")
        self.options = (left, right)
        self.var = tk.StringVar(value=left)
        self.track = self.create_rectangle(2, 2, 48, 22, outline="", fill="#4a90d9")
        self.knob = self.create_oval(4, 4, 20, 20, outline="", fill="white")
        self.bind("<Button-1>", self.toggle)

    def toggle(self, _=None):
        is_left = self.var.get() == self.options[0]
        self.var.set(self.options[1] if is_left else self.options[0])
        self.coords(self.knob, (30, 4, 46, 20) if is_left else (4, 4, 20, 20))

    def get(self):
        return self.var.get()


class LoadingBox(tk.Toplevel):
    """Kleines Lade-Fenster in der Mitte über dem Hauptfenster."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Bitte warten")
        self.resizable(False, False)
        self.transient(master)          # bleibt über dem Hauptfenster
        self.protocol("WM_DELETE_WINDOW", lambda: None)   # nicht wegklickbar

        frame = ttk.Frame(self, padding=25)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Tickets werden durchsucht...", style="Header.TLabel").pack(pady=(0, 10))
        self.count_var = tk.StringVar(value="Mails werden gelesen...")
        ttk.Label(frame, textvariable=self.count_var).pack(pady=(0, 10))
        self.bar = ttk.Progressbar(frame, mode="indeterminate", length=280)
        self.bar.pack()
        self.bar.start(10)

        # mittig über dem Hauptfenster platzieren
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = master.winfo_rootx() + (master.winfo_width() - w) // 2
        y = master.winfo_rooty() + (master.winfo_height() - h) // 2
        self.geometry(f"+{x}+{y}")
        self.grab_set()                 # Hauptfenster solange sperren

    def update_progress(self, done, total):
        if total == 0:
            return                      # Anzahl noch unbekannt -> Balken läuft weiter
        if str(self.bar.cget("mode")) == "indeterminate":
            self.bar.stop()
            self.bar.config(mode="determinate", maximum=total)
        self.bar["value"] = done
        self.count_var.set(f"{done} / {total} Tickets")

    def close(self):
        self.bar.stop()
        self.grab_release()
        self.destroy()


def send():
    counts = {}
    for model, var in entries.items():
        text = var.get().strip() or "0"   # leeres Feld = 0
        if not text.isdigit():
            messagebox.showerror("Fehler", f"Ungültige Zahl bei {model}: '{text}'")
            return
        counts[model] = int(text)

    if not any(counts.values()):
        messagebox.showwarning("Hinweis", "Keine Mengen eingegeben.")
        return

    mode = mode_switch.get()   # "include" oder "exact"
    foldername = folder_var.get()
    if not foldername:
        messagebox.showwarning("Hinweis", "Bitte einen Ordner auswählen.")
        return
    print("Modus:", mode, "| Ordner:", foldername)

    # Lade-Box öffnen, Button sperren
    send_button.config(state="disabled")
    status_var.set("")
    box = LoadingBox(root)

    state = {"tickets": None, "error": None, "total": 0, "done": 0}

    def on_total(n):       # wird aus tickets.py aufgerufen: Anzahl Tickets
        state["total"] = n

    def on_progress(n):    # wird aus tickets.py aufgerufen: wie viele fertig
        state["done"] = n

    def worker():
        # Läuft im Hintergrund, damit das Fenster nicht einfriert
        if pythoncom:
            pythoncom.CoInitialize()   # Outlook/COM in neuem Thread initialisieren
        try:
            state["tickets"] = load_tickets(foldername, on_total=on_total, on_progress=on_progress)
        except Exception as e:
            state["error"] = e
        finally:
            if pythoncom:
                pythoncom.CoUninitialize()

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    def check_done():
        # Alle 100 ms: Lade-Box aktualisieren (GUI-Updates nur im Hauptthread!)
        box.update_progress(state["done"], state["total"])
        if t.is_alive():
            root.after(100, check_done)
            return

        box.close()
        send_button.config(state="normal")

        if state["error"]:
            status_var.set("Fehler beim Laden.")
            messagebox.showerror("Fehler", str(state["error"]))
            return

        show_matches(state["tickets"], counts, mode)

    check_done()


def show_matches(tickets, counts, mode):
    result_list.config(state="normal")
    result_list.delete("1.0", tk.END)

    matches = 0
    for id, ticket in tickets.items():
        sw = ticket["infos"]["switches"]
        if mode == "exact":
            passt = counts == sw
        else:
            passt = True
            for model in counts:
                if counts[model] > sw.get(model, 0):
                    passt = False
                    break

        if passt:
            matches += 1
            print("match", id)
            sup_id = ticket["infos"]["sup-id"]
            link = ticket["infos"]["link"]
            tag = f"link_{sup_id}"

            result_list.insert(tk.END, sup_id, "bold")
            result_list.insert(tk.END, "  ")
            result_list.insert(tk.END, link, ("link", tag))
            result_list.insert(tk.END, "\n")
            result_list.tag_bind(tag, "<Button-1>", lambda e, url=link: webbrowser.open(url))

    result_list.config(state="disabled")   # Textfeld nicht editierbar
    status_var.set(f"{len(tickets)} Tickets durchsucht – {matches} Treffer")


def center_window(win, width_ratio=0.5, height_ratio=0.5):
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    w, h = int(sw * width_ratio), int(sh * height_ratio)
    x, y = (sw - w) // 2, (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


root = tk.Tk()
root.title("Switch-Bestellung")
center_window(root)

style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", font=("Segoe UI", 10))
style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8)
frame_bg = style.lookup("TFrame", "background")

main = ttk.Frame(root, padding=20)
main.pack(fill=tk.BOTH, expand=True)

# oben: Schalter include/exact
top = ttk.Frame(main)
top.pack(side=tk.TOP, anchor="w", pady=(0, 15))

ttk.Label(top, text="include").pack(side=tk.LEFT)
mode_switch = ToggleSwitch(top, bg=frame_bg)
mode_switch.pack(side=tk.LEFT, padx=6)
ttk.Label(top, text="exact").pack(side=tk.LEFT)

# Ordner-Auswahl (Unterordner von "Wichtig")
ttk.Label(top, text="Ordner:").pack(side=tk.LEFT, padx=(40, 6))
folder_var = tk.StringVar()
folder_box = ttk.Combobox(top, textvariable=folder_var, state="readonly", width=30)
folder_box.pack(side=tk.LEFT)


def reload_folders():
    try:
        names = list_folders()
    except Exception as e:
        messagebox.showerror("Fehler", f"Ordner konnten nicht geladen werden:\n{e}")
        return
    folder_box["values"] = names
    if folder_var.get() not in names:
        folder_var.set(DEFAULT_FOLDER if DEFAULT_FOLDER in names else (names[0] if names else ""))


ttk.Button(top, text="⟳", width=3, command=reload_folders).pack(side=tk.LEFT, padx=(6, 0))
reload_folders()

# linke Seite: Modelle + Mengenfelder
left = ttk.Frame(main)
left.pack(side=tk.LEFT, anchor="n")

ttk.Label(left, text="Modell", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
ttk.Label(left, text="Menge", style="Header.TLabel").grid(row=0, column=1, sticky="w", pady=(0, 10), padx=(20, 0))

entries = {}
for i, model in enumerate(SWITCH_MODELS, start=1):
    ttk.Label(left, text=model).grid(row=i, column=0, sticky="w", pady=4)
    var = tk.StringVar()
    ttk.Entry(left, textvariable=var, width=8, justify="center").grid(row=i, column=1, sticky="w", pady=4, padx=(20, 0))
    entries[model] = var

# rechte Seite: Treffer
right = ttk.Frame(main)
right.pack(side=tk.LEFT, anchor="n", padx=(30, 0))

ttk.Label(right, text="Ticket Nr", style="Header.TLabel").pack(anchor="w", pady=(0, 11))
result_list = tk.Text(right, width=100, height=10, wrap="none", cursor="arrow", font=("Segoe UI", 10), state="disabled")
result_list.pack(anchor="w")
result_list.tag_config("bold", font=("Segoe UI", 10, "bold"))
result_list.tag_config("link", foreground="#1a73e8", underline=True)
result_list.tag_bind("link", "<Enter>", lambda e: result_list.config(cursor="hand2"))
result_list.tag_bind("link", "<Leave>", lambda e: result_list.config(cursor="arrow"))

# unten: Senden-Button
bottom = ttk.Frame(root, padding=(20, 0, 20, 20))
bottom.pack(side=tk.BOTTOM, fill=tk.X, before=main)

status_var = tk.StringVar()
ttk.Label(bottom, textvariable=status_var).pack(side=tk.LEFT)

send_button = ttk.Button(bottom, text="Senden", command=send)
send_button.pack(side=tk.RIGHT)

root.mainloop()