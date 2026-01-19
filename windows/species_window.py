"""
Finestra per la configurazione delle specie (Species) in CALPUFF
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from pathlib import Path


class SpeciesWindow:
    """Finestra per gestire le specie e i loro parametri"""
    
    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = temp_dir
        self.window = tk.Toplevel(parent)
        self.window.title("Configurazione Specie")
        self.window.geometry("900x650")
        
        # Database delle specie (salvato separatamente)
        self.species_db_file = Path("saved_configurations") / "species_database.json"
        self.species_database = self.load_species_database()
        
        # Specie correnti (dalla configurazione temporanea)
        self.current_species = {}
        self.load_current_species()
        
        self.setup_ui()
        self.refresh_species_list()
    
    def load_species_database(self):
        """Carica il database delle specie salvate"""
        if self.species_db_file.exists():
            try:
                with open(self.species_db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Errore caricamento database specie: {e}")
                return {}
        return {}
    
    def save_species_database(self):
        """Salva il database delle specie"""
        try:
            self.species_db_file.parent.mkdir(exist_ok=True)
            with open(self.species_db_file, 'w', encoding='utf-8') as f:
                json.dump(self.species_database, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Errore salvataggio database specie: {e}")
    
    def load_current_species(self):
        """Carica le specie dalla configurazione corrente"""
        config_file = self.temp_dir / 'calpuff_config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_species = data.get('species', {})
            except Exception as e:
                print(f"Errore caricamento specie: {e}")
    
    def setup_ui(self):
        """Configura l'interfaccia utente"""
        # Frame principale
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(1, weight=1)
        
        # === COLONNA SINISTRA: Lista Specie ===
        left_frame = ttk.LabelFrame(main_frame, text="Specie Configurate", padding="10")
        left_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        # Listbox con scrollbar
        list_scroll = ttk.Scrollbar(left_frame)
        list_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.species_listbox = tk.Listbox(left_frame, yscrollcommand=list_scroll.set, font=('Arial', 10))
        self.species_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_scroll.config(command=self.species_listbox.yview)
        
        self.species_listbox.bind('<<ListboxSelect>>', self.on_species_select)
        
        # Bottoni gestione
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Button(btn_frame, text="➕ Nuova", command=self.add_new_species, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📋 Da DB", command=self.add_from_database, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ Elimina", command=self.delete_species, width=12).pack(side=tk.LEFT, padx=2)
        
        # === COLONNA DESTRA: Dettagli Specie ===
        right_frame = ttk.LabelFrame(main_frame, text="Dettagli Specie", padding="10")
        right_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(1, weight=1)
        
        # Canvas scrollabile per i dettagli
        canvas = tk.Canvas(right_frame)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        self.details_frame = ttk.Frame(canvas)
        
        self.details_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.details_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        right_frame.rowconfigure(0, weight=1)
        
        self.show_empty_details()
        
        # === BOTTONI AZIONE ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="💾 Salva e Chiudi", command=self.save_and_close, width=20).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="❌ Annulla", command=self.window.destroy, width=20).pack(side=tk.LEFT, padx=10)
    
    def show_empty_details(self):
        """Mostra messaggio quando nessuna specie è selezionata"""
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        ttk.Label(
            self.details_frame, 
            text="Seleziona una specie dalla lista\no creane una nuova",
            font=('Arial', 10, 'italic'),
            foreground='gray'
        ).pack(pady=50)
    
    def refresh_species_list(self):
        """Aggiorna la lista delle specie"""
        self.species_listbox.delete(0, tk.END)
        for name in sorted(self.current_species.keys()):
            dep_type = self.current_species[name].get('dry_deposition', 1)
            dep_label = "Gas" if dep_type == 1 else "Particle"
            self.species_listbox.insert(tk.END, f"{name} ({dep_label})")
    
    def on_species_select(self, event):
        """Gestisce la selezione di una specie dalla lista"""
        selection = self.species_listbox.curselection()
        if not selection:
            return
        
        # Estrai il nome della specie (prima delle parentesi)
        full_text = self.species_listbox.get(selection[0])
        species_name = full_text.split(' (')[0]
        
        if species_name in self.current_species:
            self.show_species_details(species_name)
    
    def show_species_details(self, species_name):
        """Mostra i dettagli di una specie selezionata"""
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        species_data = self.current_species[species_name]
        
        # Nome specie
        ttk.Label(self.details_frame, text=f"Specie: {species_name}", 
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=tk.W)
        
        # Tipo deposizione
        ttk.Label(self.details_frame, text="Tipo Deposizione:").grid(row=1, column=0, sticky=tk.W, pady=5)
        dep_type = species_data.get('dry_deposition', 1)
        dep_text = "Gas (1)" if dep_type == 1 else "Particelle (2)"
        ttk.Label(self.details_frame, text=dep_text, font=('Arial', 10, 'bold')).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        row = 2
        
        # Parametri Gas (se applicabile)
        if species_data.get('gas_inq') is not None:
            ttk.Separator(self.details_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
            row += 1
            
            ttk.Label(self.details_frame, text="Parametri Gas:", 
                     font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
            row += 1
            
            gas_params = species_data['gas_inq']
            for key, value in gas_params.items():
                ttk.Label(self.details_frame, text=f"{key}:").grid(row=row, column=0, sticky=tk.W, pady=2, padx=(20, 0))
                ttk.Label(self.details_frame, text=str(value)).grid(row=row, column=1, sticky=tk.W, pady=2)
                row += 1
        
        # Parametri Dry (se applicabile)
        if species_data.get('dry_inq') is not None:
            ttk.Separator(self.details_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
            row += 1
            
            ttk.Label(self.details_frame, text="Parametri Deposizione Secca:", 
                     font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
            row += 1
            
            dry_params = species_data['dry_inq']
            for key, value in dry_params.items():
                ttk.Label(self.details_frame, text=f"{key}:").grid(row=row, column=0, sticky=tk.W, pady=2, padx=(20, 0))
                ttk.Label(self.details_frame, text=str(value)).grid(row=row, column=1, sticky=tk.W, pady=2)
                row += 1
        
        # Parametri Wet (sempre presente)
        if species_data.get('wet_inq') is not None:
            ttk.Separator(self.details_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
            row += 1
            
            ttk.Label(self.details_frame, text="Parametri Deposizione Umida:", 
                     font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
            row += 1
            
            wet_params = species_data['wet_inq']
            for key, value in wet_params.items():
                ttk.Label(self.details_frame, text=f"{key}:").grid(row=row, column=0, sticky=tk.W, pady=2, padx=(20, 0))
                ttk.Label(self.details_frame, text=str(value)).grid(row=row, column=1, sticky=tk.W, pady=2)
                row += 1
        
        # Bottone modifica
        ttk.Button(
            self.details_frame, 
            text="✏️ Modifica Specie", 
            command=lambda: self.edit_species(species_name)
        ).grid(row=row, column=0, columnspan=2, pady=20)
    
    def add_new_species(self):
        """Apre finestra per aggiungere una nuova specie"""
        SpeciesEditorWindow(self.window, self.temp_dir, None, self.on_species_added)
    
    def add_from_database(self):
        """Mostra finestra per selezionare una specie dal database"""
        if not self.species_database:
            messagebox.showinfo("Database Vuoto", "Non ci sono specie salvate nel database.\nCrea una nuova specie e salvala nel database.")
            return
        
        # Finestra di selezione
        selection_window = tk.Toplevel(self.window)
        selection_window.title("Seleziona Specie dal Database")
        selection_window.geometry("400x500")
        selection_window.transient(self.window)
        selection_window.grab_set()
        
        ttk.Label(selection_window, text="Specie Disponibili nel Database:", 
                 font=('Arial', 10, 'bold')).pack(pady=10)
        
        # Listbox
        list_frame = ttk.Frame(selection_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        db_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=('Arial', 10))
        db_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=db_listbox.yview)
        
        for name in sorted(self.species_database.keys()):
            dep_type = self.species_database[name].get('dry_deposition', 1)
            dep_label = "Gas" if dep_type == 1 else "Particle"
            db_listbox.insert(tk.END, f"{name} ({dep_label})")
        
        def on_select():
            selection = db_listbox.curselection()
            if not selection:
                messagebox.showwarning("Attenzione", "Seleziona una specie!")
                return
            
            full_text = db_listbox.get(selection[0])
            species_name = full_text.split(' (')[0]
            
            # Verifica se esiste già
            if species_name in self.current_species:
                if not messagebox.askyesno("Conferma", f"La specie '{species_name}' esiste già.\nSovrascriverla?"):
                    return
            
            # Aggiungi la specie
            self.current_species[species_name] = self.species_database[species_name].copy()
            self.refresh_species_list()
            messagebox.showinfo("Successo", f"Specie '{species_name}' aggiunta!")
            selection_window.destroy()
        
        ttk.Button(selection_window, text="Aggiungi", command=on_select).pack(pady=10)
        ttk.Button(selection_window, text="Annulla", command=selection_window.destroy).pack(pady=5)
    
    def edit_species(self, species_name):
        """Apre finestra per modificare una specie esistente"""
        SpeciesEditorWindow(self.window, self.temp_dir, (species_name, self.current_species[species_name]), self.on_species_edited)
    
    def delete_species(self):
        """Elimina la specie selezionata"""
        selection = self.species_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona una specie da eliminare!")
            return
        
        full_text = self.species_listbox.get(selection[0])
        species_name = full_text.split(' (')[0]
        
        if messagebox.askyesno("Conferma", f"Eliminare la specie '{species_name}'?"):
            del self.current_species[species_name]
            self.refresh_species_list()
            self.show_empty_details()
    
    def on_species_added(self, species_name, species_data, save_to_db):
        """Callback quando una nuova specie viene aggiunta"""
        self.current_species[species_name] = species_data
        
        if save_to_db:
            self.species_database[species_name] = species_data.copy()
            self.save_species_database()
            messagebox.showinfo("Successo", f"Specie '{species_name}' aggiunta e salvata nel database!")
        
        self.refresh_species_list()
    
    def on_species_edited(self, old_name, new_name, species_data, save_to_db):
        """Callback quando una specie viene modificata"""
        if old_name != new_name:
            del self.current_species[old_name]
        
        self.current_species[new_name] = species_data
        
        if save_to_db:
            self.species_database[new_name] = species_data.copy()
            self.save_species_database()
        
        self.refresh_species_list()
        self.show_species_details(new_name)
    
    def save_and_close(self):
        """Salva le specie nella configurazione e chiude"""
        config_file = self.temp_dir / 'calpuff_config.json'
        
        try:
            # Carica configurazione esistente
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                config_data = {}
            
            # Aggiorna le specie
            config_data['species'] = self.current_species
            
            # Salva
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Successo", f"{len(self.current_species)} specie salvate nella configurazione!")
            self.window.destroy()
        
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il salvataggio:\n{str(e)}")


class SpeciesEditorWindow:
    """Finestra per creare/modificare una specie"""
    
    def __init__(self, parent, temp_dir, species_data, callback):
        """
        species_data: None per nuova specie, oppure (nome, dati) per modifica
        callback: funzione da chiamare al salvataggio
        """
        self.parent = parent
        self.temp_dir = temp_dir
        self.callback = callback
        self.is_edit = species_data is not None
        
        self.window = tk.Toplevel(parent)
        self.window.title("Modifica Specie" if self.is_edit else "Nuova Specie")
        self.window.geometry("600x700")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Dati
        if self.is_edit:
            self.original_name = species_data[0]
            data = species_data[1]
        else:
            self.original_name = None
            data = {}
        
        # Variabili
        self.species_name = tk.StringVar(value=self.original_name if self.is_edit else "")
        self.dry_deposition = tk.IntVar(value=data.get('dry_deposition', 1))
        self.save_to_db = tk.BooleanVar(value=False)
        
        # Gas parameters
        gas_data = data.get('gas_inq', {}) if data.get('gas_inq') is not None else {}
        self.gas_diffus = tk.StringVar(value=gas_data.get('diffus', '.1656'))
        self.gas_alfa = tk.StringVar(value=gas_data.get('alfa', '1.0'))
        self.gas_react = tk.StringVar(value=gas_data.get('react', '8.0'))
        self.gas_mesophyll = tk.StringVar(value=gas_data.get('Mesophyll', '5.0'))
        self.gas_henry = tk.StringVar(value=gas_data.get('Henry_coef', '3.5'))
        
        # Dry parameters
        dry_data = data.get('dry_inq', {}) if data.get('dry_inq') is not None else {}
        self.dry_geo_mass = tk.StringVar(value=dry_data.get('Geo_mass_mean_diam', '4.8'))
        self.dry_geo_std = tk.StringVar(value=dry_data.get('Geo_std_dev', '2'))
        
        # Wet parameters
        wet_data = data.get('wet_inq', {}) if data.get('wet_inq') is not None else {}
        self.wet_liq = tk.StringVar(value=wet_data.get('Liq_Prec', '3.0E-05'))
        self.wet_froz = tk.StringVar(value=wet_data.get('Froz_Prec', '3.0E-05'))
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura l'interfaccia"""
        # Frame principale scrollabile
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        row = 0
        
        # Nome specie
        ttk.Label(scrollable_frame, text="Nome Specie:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=10)
        row += 1
        ttk.Entry(scrollable_frame, textvariable=self.species_name, width=40).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=10)
        row += 1
        
        # Tipo deposizione
        ttk.Label(scrollable_frame, text="Tipo Deposizione:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=10)
        row += 1
        
        dep_frame = ttk.Frame(scrollable_frame)
        dep_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5, padx=10)
        ttk.Radiobutton(dep_frame, text="Gas (1)", variable=self.dry_deposition, value=1, 
                       command=self.on_deposition_change).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(dep_frame, text="Particelle (2)", variable=self.dry_deposition, value=2,
                       command=self.on_deposition_change).pack(side=tk.LEFT)
        row += 1
        
        # Frame per parametri gas
        self.gas_frame = ttk.LabelFrame(scrollable_frame, text="Parametri Gas", padding="10")
        self.gas_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10, padx=10)
        row += 1
        
        ttk.Label(self.gas_frame, text="Diffusivity:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.gas_frame, textvariable=self.gas_diffus, width=20).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(self.gas_frame, text="Alfa:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.gas_frame, textvariable=self.gas_alfa, width=20).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(self.gas_frame, text="Reactivity:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.gas_frame, textvariable=self.gas_react, width=20).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(self.gas_frame, text="Mesophyll:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.gas_frame, textvariable=self.gas_mesophyll, width=20).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(self.gas_frame, text="Henry Coef:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.gas_frame, textvariable=self.gas_henry, width=20).grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.gas_frame.columnconfigure(1, weight=1)
        
        # Frame per parametri dry (particelle)
        self.dry_frame = ttk.LabelFrame(scrollable_frame, text="Parametri Deposizione Secca (Particelle)", padding="10")
        self.dry_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10, padx=10)
        row += 1
        
        ttk.Label(self.dry_frame, text="Geo Mass Mean Diam:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.dry_frame, textvariable=self.dry_geo_mass, width=20).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(self.dry_frame, text="Geo Std Dev:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.dry_frame, textvariable=self.dry_geo_std, width=20).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.dry_frame.columnconfigure(1, weight=1)
        
        # Frame per parametri wet
        wet_frame = ttk.LabelFrame(scrollable_frame, text="Parametri Deposizione Umida", padding="10")
        wet_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10, padx=10)
        row += 1
        
        ttk.Label(wet_frame, text="Liquid Precipitation:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(wet_frame, textvariable=self.wet_liq, width=20).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(wet_frame, text="Frozen Precipitation:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(wet_frame, textvariable=self.wet_froz, width=20).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        wet_frame.columnconfigure(1, weight=1)
        
        # Checkbox per salvare nel database
        ttk.Checkbutton(
            scrollable_frame, 
            text="Salva questa specie nel database per riutilizzi futuri", 
            variable=self.save_to_db
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=15, padx=10)
        row += 1
        
        # Bottoni
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="💾 Salva", command=self.save_species, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="❌ Annulla", command=self.window.destroy, width=15).pack(side=tk.LEFT, padx=10)
        
        # Configura visibilità iniziale
        self.on_deposition_change()
    
    def on_deposition_change(self):
        """Mostra/nasconde parametri in base al tipo di deposizione"""
        if self.dry_deposition.get() == 1:  # Gas
            # Mostra gas, nascondi dry
            for child in self.gas_frame.winfo_children():
                child.configure(state='normal')
            for child in self.dry_frame.winfo_children():
                child.configure(state='disabled')
        else:  # Particelle
            # Nascondi gas, mostra dry
            for child in self.gas_frame.winfo_children():
                child.configure(state='disabled')
            for child in self.dry_frame.winfo_children():
                child.configure(state='normal')
    
    def save_species(self):
        """Salva la specie"""
        name = self.species_name.get().strip()
        
        if not name:
            messagebox.showerror("Errore", "Inserire un nome per la specie!")
            return
        
        # Costruisci dati specie
        species_data = {
            'dry_deposition': self.dry_deposition.get()
        }
        
        if self.dry_deposition.get() == 1:  # Gas
            species_data['gas_inq'] = {
                'diffus': self.gas_diffus.get(),
                'alfa': self.gas_alfa.get(),
                'react': self.gas_react.get(),
                'Mesophyll': self.gas_mesophyll.get(),
                'Henry_coef': self.gas_henry.get()
            }
            species_data['dry_inq'] = None
        else:  # Particelle
            species_data['gas_inq'] = None
            species_data['dry_inq'] = {
                'Geo_mass_mean_diam': self.dry_geo_mass.get(),
                'Geo_std_dev': self.dry_geo_std.get()
            }
        
        species_data['wet_inq'] = {
            'Liq_Prec': self.wet_liq.get(),
            'Froz_Prec': self.wet_froz.get()
        }
        
        # Chiama callback
        if self.is_edit:
            self.callback(self.original_name, name, species_data, self.save_to_db.get())
        else:
            self.callback(name, species_data, self.save_to_db.get())
        
        self.window.destroy()
