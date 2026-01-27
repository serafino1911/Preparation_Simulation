"""
Finestra per la configurazione delle sorgenti Flare in CALPUFF
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from pathlib import Path


class FlareSourcesWindow:
    """Finestra per gestire i file FLARE_NAMES"""
    
    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = temp_dir
        self.window = tk.Toplevel(parent)
        self.window.title("Configurazione Sorgenti Flare")
        self.window.geometry("600x350")
        
        # File FLARE_NAMES (dalla configurazione temporanea)
        self.flare_names = ['DUMMY.CSV']  # Default
        self.load_current_config()
        
        self.setup_ui()
        self.refresh_files_list()
    
    def load_current_config(self):
        """Carica la configurazione dalla configurazione temporanea"""
        calpuff_config = self.temp_dir / "calpuff_config.json"
        if calpuff_config.exists():
            try:
                with open(calpuff_config, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.flare_names = data.get('flare_names', ['DUMMY.CSV'])
            except Exception as e:
                print(f"Errore caricamento configurazione flare: {e}")
    
    def save_current_config(self):
        """Salva la configurazione nella configurazione temporanea"""
        calpuff_config = self.temp_dir / "calpuff_config.json"
        try:
            # Carica config esistente o crea nuova
            if calpuff_config.exists():
                with open(calpuff_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Aggiorna file flare
            config['flare_names'] = self.flare_names
            
            # Salva
            with open(calpuff_config, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Successo", "Configurazione Flare salvata correttamente!")
            self.window.destroy()
            
        except Exception as e:
            print(f"Errore salvataggio configurazione flare: {e}")
            messagebox.showerror("Errore", f"Errore nel salvataggio: {e}")
    
    def setup_ui(self):
        """Crea l'interfaccia utente"""
        # Frame principale
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # ===== SEZIONE FILE FLARE_NAMES =====
        files_frame = ttk.LabelFrame(main_frame, text="File FLARE_NAMES", padding="10")
        files_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(0, weight=1)
        
        # Descrizione
        desc_label = ttk.Label(files_frame, 
                              text="Specifica i file che contengono le definizioni delle sorgenti Flare.\nDefault: DUMMY.CSV",
                              font=('Arial', 9, 'italic'),
                              foreground='gray')
        desc_label.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Lista file
        files_list_frame = ttk.Frame(files_frame)
        files_list_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        files_list_frame.columnconfigure(0, weight=1)
        files_list_frame.rowconfigure(0, weight=1)
        
        # Scrollbar per file
        files_scrollbar = ttk.Scrollbar(files_list_frame)
        files_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Listbox file
        self.files_listbox = tk.Listbox(files_list_frame, height=8, 
                                        yscrollcommand=files_scrollbar.set)
        self.files_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        files_scrollbar.config(command=self.files_listbox.yview)
        
        # Pulsanti per file
        buttons_frame = ttk.Frame(files_frame)
        buttons_frame.grid(row=2, column=0, columnspan=3, pady=5)
        
        ttk.Button(buttons_frame, text="➕ Aggiungi File", 
                  command=self.add_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🗑️ Rimuovi File", 
                  command=self.remove_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🔄 Reset a DUMMY.CSV", 
                  command=self.reset_files).pack(side=tk.LEFT, padx=5)
        
        # ===== BOTTONI AZIONE =====
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=1, column=0, pady=20)
        
        ttk.Button(action_frame, text="💾 Salva", 
                  command=self.save_current_config, width=20).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="❌ Annulla", 
                  command=self.window.destroy, width=20).pack(side=tk.LEFT, padx=10)
    
    def refresh_files_list(self):
        """Aggiorna la lista dei file nell'interfaccia"""
        self.files_listbox.delete(0, tk.END)
        for file in self.flare_names:
            self.files_listbox.insert(tk.END, file)
    
    def add_file(self):
        """Aggiunge un file alla lista"""
        # Mostra dialog per inserimento manuale o selezione
        dialog = tk.Toplevel(self.window)
        dialog.title("Aggiungi File Flare")
        dialog.geometry("500x150")
        dialog.transient(self.window)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(frame, text="Nome del file:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        filename_var = tk.StringVar(value="DUMMY.CSV")
        filename_entry = ttk.Entry(frame, textvariable=filename_var, width=40)
        filename_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        def browse_file():
            file_path = filedialog.askopenfilename(
                title="Seleziona file Flare",
                filetypes=[("CSV files", "*.csv"), ("DAT files", "*.dat"), ("All files", "*.*")]
            )
            if file_path:
                filename_var.set(Path(file_path).name)
        
        def add_and_close():
            filename = filename_var.get().strip()
            if filename:
                if filename not in self.flare_names:
                    self.flare_names.append(filename)
                    self.refresh_files_list()
                    dialog.destroy()
                else:
                    messagebox.showwarning("Attenzione", "File già presente nella lista")
            else:
                messagebox.showwarning("Attenzione", "Inserire un nome file valido")
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, pady=15)
        
        ttk.Button(button_frame, text="📁 Sfoglia", 
                  command=browse_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="✅ Aggiungi", 
                  command=add_and_close).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Annulla", 
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        frame.columnconfigure(0, weight=1)
        dialog.columnconfigure(0, weight=1)
    
    def remove_file(self):
        """Rimuove il file selezionato dalla lista"""
        selection = self.files_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare un file da rimuovere")
            return
        
        idx = selection[0]
        filename = self.flare_names[idx]
        
        if messagebox.askyesno("Conferma", f"Rimuovere il file '{filename}'?"):
            self.flare_names.pop(idx)
            self.refresh_files_list()
    
    def reset_files(self):
        """Reset alla lista default"""
        if messagebox.askyesno("Conferma", "Ripristinare la lista a DUMMY.CSV?"):
            self.flare_names = ['DUMMY.CSV']
            self.refresh_files_list()
