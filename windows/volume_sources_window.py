"""
Finestra per la configurazione delle sorgenti volumetriche (Volume Sources) in CALPUFF
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import math
from pathlib import Path

# Import opzionali per la mappa
try:
    import tkintermapview
    from pyproj import CRS, Transformer
    MAPVIEW_AVAILABLE = True
    PYPROJ_AVAILABLE = True
except ImportError:
    MAPVIEW_AVAILABLE = False
    PYPROJ_AVAILABLE = False


class VolumeSourcesWindow:
    """Finestra per gestire le sorgenti volumetriche e i file VOLUME_NAMES"""
    
    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = temp_dir
        self.window = tk.Toplevel(parent)
        self.window.title("Configurazione Sorgenti Volumetriche")
        self.window.geometry("900x700")
        
        # Database delle sorgenti volumetriche (salvato separatamente)
        self.sources_db_file = Path("saved_configurations") / "volume_sources_database.json"
        self.sources_database = self.load_sources_database()
        
        # Sorgenti correnti e file VOLUME_NAMES (dalla configurazione temporanea)
        self.current_sources = {}
        self.volume_names = ['DUMMY.DAT']  # Default
        self.volume_names_location = []  # Percorsi dei file selezionati
        self.load_current_sources()
        
        # Origine del dominio (per conversione km -> lat/lon)
        self.domain_origin = self.load_domain_origin()
        
        self.setup_ui()
        self.refresh_sources_list()
        self.refresh_files_list()
    
    def load_sources_database(self):
        """Carica il database delle sorgenti salvate"""
        if self.sources_db_file.exists():
            try:
                with open(self.sources_db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Errore caricamento database sorgenti volumetriche: {e}")
                return {}
        return {}
    
    def save_sources_database(self):
        """Salva il database delle sorgenti"""
        try:
            self.sources_db_file.parent.mkdir(exist_ok=True)
            with open(self.sources_db_file, 'w', encoding='utf-8') as f:
                json.dump(self.sources_database, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Errore salvataggio database sorgenti volumetriche: {e}")
    
    def load_current_sources(self):
        """Carica le sorgenti dalla configurazione corrente"""
        config_file = self.temp_dir / 'calpuff_config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sources_list = data.get('volume_emission', [])
                    # Converti lista in dizionario usando source_name come chiave
                    self.current_sources = {src['source_name']: src for src in sources_list}
                    # Carica anche VOLUME_NAMES
                    self.volume_names = data.get('volume_names', ['DUMMY.DAT'])
                    self.volume_names_location = data.get('volume_names_location', [])
            except Exception as e:
                print(f"Errore caricamento sorgenti volumetriche: {e}")
    
    def load_domain_origin(self):
        """Carica l'origine del dominio e i vertici dalla configurazione"""
        config_file = self.temp_dir / 'domain_config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Estrai origine dalla griglia
                    grid_origin = data.get('grid_origin', {})
                    grid_step = data.get('grid_step', {})
                    vertices = data.get('vertices', {})
                    zona_utm = data.get('zona_utm', '32N')
                    
                    return {
                        'lat': grid_origin.get('lat'),
                        'lon': grid_origin.get('lon'),
                        'vertices': vertices,
                        'zona_utm': zona_utm,
                        'grid_step': grid_step.get('value'),
                        'grid_step_unit': grid_step.get('unit', 'km'),
                        'nx': grid_origin.get('nx'),
                        'ny': grid_origin.get('ny')
                    }
            except Exception as e:
                print(f"Errore caricamento origine dominio: {e}")
        return None
    
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
        
        # ===== SEZIONE FILE VOLUME_NAMES =====
        files_frame = ttk.LabelFrame(main_frame, text="File VOLUME_NAMES", padding="10")
        files_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        files_frame.columnconfigure(0, weight=1)
        
        # Frame per lista file
        files_list_frame = ttk.Frame(files_frame)
        files_list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        files_list_frame.columnconfigure(0, weight=1)
        
        # Listbox per file
        files_scrollbar = ttk.Scrollbar(files_list_frame)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.files_listbox = tk.Listbox(files_list_frame, height=3, 
                                        yscrollcommand=files_scrollbar.set)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        files_scrollbar.config(command=self.files_listbox.yview)
        
        # Bottoni per gestione file
        files_btn_frame = ttk.Frame(files_frame)
        files_btn_frame.grid(row=1, column=0, pady=5)
        
        ttk.Button(files_btn_frame, text="➕ Aggiungi File", 
                  command=self.add_volume_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(files_btn_frame, text="🗑️ Rimuovi File", 
                  command=self.remove_volume_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(files_btn_frame, text="🔄 Reset a DUMMY.DAT", 
                  command=self.reset_volume_files).pack(side=tk.LEFT, padx=5)
        
        # === COLONNA SINISTRA: Lista Sorgenti ===
        left_frame = ttk.LabelFrame(main_frame, text="Sorgenti Volumetriche Configurate", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        # Listbox con scrollbar
        list_scroll = ttk.Scrollbar(left_frame)
        list_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.sources_listbox = tk.Listbox(left_frame, yscrollcommand=list_scroll.set, font=('Arial', 10))
        self.sources_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_scroll.config(command=self.sources_listbox.yview)
        
        self.sources_listbox.bind('<<ListboxSelect>>', self.on_source_select)
        
        # Bottoni gestione
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Button(btn_frame, text="➕ Nuova", command=self.add_new_source, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📋 Da DB", command=self.add_from_database, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ Elimina", command=self.delete_source, width=12).pack(side=tk.LEFT, padx=2)
        
        # === COLONNA DESTRA: Dettagli Sorgente ===
        right_frame = ttk.LabelFrame(main_frame, text="Dettagli Sorgente", padding="10")
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
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
        """Mostra messaggio quando nessuna sorgente è selezionata"""
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        ttk.Label(
            self.details_frame, 
            text="Seleziona una sorgente dalla lista\no creane una nuova",
            font=('Arial', 10, 'italic'),
            foreground='gray'
        ).pack(pady=50)
    
    def refresh_sources_list(self):
        """Aggiorna la lista delle sorgenti"""
        self.sources_listbox.delete(0, tk.END)
        for name in sorted(self.current_sources.keys()):
            source = self.current_sources[name]
            height = source.get('height', 0)
            sigma_z = source.get('initial_sigma_z', 0)
            self.sources_listbox.insert(tk.END, f"{name} (H:{height}m, σz:{sigma_z}m)")
    
    def on_source_select(self, event):
        """Gestisce la selezione di una sorgente dalla lista"""
        selection = self.sources_listbox.curselection()
        if not selection:
            return
        
        # Estrai il nome della sorgente (prima delle parentesi)
        full_text = self.sources_listbox.get(selection[0])
        source_name = full_text.split(' (')[0]
        
        if source_name in self.current_sources:
            self.show_source_details(source_name)
    
    def show_source_details(self, source_name):
        """Mostra i dettagli di una sorgente selezionata"""
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        source_data = self.current_sources[source_name]
        
        # Nome sorgente
        ttk.Label(self.details_frame, text=f"Sorgente: {source_name}", 
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=tk.W)
        
        row = 1
        
        # Parametri geometrici
        ttk.Label(self.details_frame, text="Parametri Geometrici:", 
                 font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1
        
        position = source_data.get('position', [0, 0])
        ttk.Label(self.details_frame, text="Posizione X (km):").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Label(self.details_frame, text=f"{position[0]}").grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        ttk.Label(self.details_frame, text="Posizione Y (km):").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Label(self.details_frame, text=f"{position[1]}").grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        ttk.Label(self.details_frame, text="Altezza (m):").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Label(self.details_frame, text=f"{source_data.get('height', 0)}").grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        ttk.Label(self.details_frame, text="Elevazione Base (m):").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Label(self.details_frame, text=f"{source_data.get('base_elev', 0)}").grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # Parametri dispersione
        ttk.Separator(self.details_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(self.details_frame, text="Parametri Dispersione:", 
                 font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(self.details_frame, text="Sigma Z Iniziale (m):").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Label(self.details_frame, text=f"{source_data.get('initial_sigma_z', 0)}").grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        ttk.Label(self.details_frame, text="Sigma Y Iniziale (m):").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Label(self.details_frame, text=f"{source_data.get('initial_sigma_y', 0)}").grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # Tassi di emissione
        ttk.Separator(self.details_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(self.details_frame, text="Tassi di Emissione:", 
                 font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        emis_rates = source_data.get('emis_rates', [])
        for idx, rate in enumerate(emis_rates):
            ttk.Label(self.details_frame, text=f"Specie {idx+1}:").grid(row=row, column=0, sticky=tk.W, pady=2, padx=(20, 0))
            ttk.Label(self.details_frame, text=f"{rate:.4E}").grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1
        
        # Bottone modifica
        ttk.Button(
            self.details_frame, 
            text="✏️ Modifica Sorgente", 
            command=lambda: self.edit_source(source_name)
        ).grid(row=row, column=0, columnspan=2, pady=20)
    
    # ===== GESTIONE FILE VOLUME_NAMES =====
    
    def refresh_files_list(self):
        """Aggiorna la lista dei file VOLUME_NAMES"""
        self.files_listbox.delete(0, tk.END)
        for file_name in self.volume_names:
            self.files_listbox.insert(tk.END, file_name)
    
    def add_volume_file(self):
        """Aggiunge un file alla lista VOLUME_NAMES"""
        file_path = filedialog.askopenfilename(
            title="Seleziona file sorgente volumetrica",
            filetypes=[("DAT files", "*.DAT"), ("Tutti i file", "*.*")]
        )
        
        if file_path:
            # Estrai solo il nome del file
            file_name = Path(file_path).name
            
            # Se la lista contiene solo DUMMY.DAT, sostituiscilo
            if self.volume_names == ['DUMMY.DAT']:
                self.volume_names = [file_name]
                self.volume_names_location = [file_path]
            else:
                # Altrimenti aggiungi se non già presente
                if file_name not in self.volume_names:
                    self.volume_names.append(file_name)
                    self.volume_names_location.append(file_path)
                else:
                    messagebox.showinfo("Info", f"Il file '{file_name}' è già nella lista")
                    return
            
            self.refresh_files_list()
    
    def remove_volume_file(self):
        """Rimuove un file dalla lista VOLUME_NAMES"""
        selection = self.files_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un file da rimuovere")
            return
        
        index = selection[0]
        file_name = self.volume_names[index]
        
        if messagebox.askyesno("Conferma", f"Rimuovere '{file_name}' dalla lista?"):
            del self.volume_names[index]
            del self.volume_names_location[index]
            # Se lista vuota, ripristina DUMMY.DAT
            if not self.volume_names:
                self.volume_names = ['DUMMY.DAT']
                self.volume_names_location = []
            
            self.refresh_files_list()
    
    def reset_volume_files(self):
        """Ripristina la lista a DUMMY.DAT"""
        if messagebox.askyesno("Conferma", "Ripristinare la lista a DUMMY.DAT?"):
            self.volume_names = ['DUMMY.DAT']
            self.volume_names_location = []
            self.refresh_files_list()
    
    # ===== GESTIONE SORGENTI =====
    
    def add_new_source(self):
        """Apre finestra per aggiungere una nuova sorgente"""
        VolumeSourceEditorWindow(self.window, self.temp_dir, self.domain_origin, None, self.on_source_added)
    
    def add_from_database(self):
        """Mostra finestra per selezionare una sorgente dal database"""
        if not self.sources_database:
            messagebox.showinfo("Database Vuoto", "Non ci sono sorgenti salvate nel database.\nCrea una nuova sorgente e salvala nel database.")
            return
        
        # Finestra di selezione
        selection_window = tk.Toplevel(self.window)
        selection_window.title("Seleziona Sorgente dal Database")
        selection_window.geometry("400x500")
        selection_window.transient(self.window)
        selection_window.grab_set()
        
        ttk.Label(selection_window, text="Sorgenti Disponibili nel Database:", 
                 font=('Arial', 10, 'bold')).pack(pady=10, padx=10)
        
        # Listbox delle sorgenti
        list_frame = ttk.Frame(selection_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        db_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=('Arial', 10))
        db_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=db_listbox.yview)
        
        for name in sorted(self.sources_database.keys()):
            source = self.sources_database[name]
            height = source.get('height', 0)
            sigma_z = source.get('initial_sigma_z', 0)
            db_listbox.insert(tk.END, f"{name} (H:{height}m, σz:{sigma_z}m)")
        
        def on_select():
            selection = db_listbox.curselection()
            if not selection:
                messagebox.showwarning("Attenzione", "Seleziona una sorgente!")
                return
            
            full_text = db_listbox.get(selection[0])
            source_name = full_text.split(' (')[0]
            
            # Verifica se esiste già
            if source_name in self.current_sources:
                if not messagebox.askyesno("Conferma", f"La sorgente '{source_name}' esiste già.\nSovrascriverla?"):
                    return
            
            # Aggiungi la sorgente
            self.current_sources[source_name] = self.sources_database[source_name].copy()
            self.refresh_sources_list()
            messagebox.showinfo("Successo", f"Sorgente '{source_name}' aggiunta!")
            selection_window.destroy()
        
        ttk.Button(selection_window, text="Aggiungi", command=on_select).pack(pady=10)
        ttk.Button(selection_window, text="Annulla", command=selection_window.destroy).pack(pady=5)
    
    def edit_source(self, source_name):
        """Apre finestra per modificare una sorgente esistente"""
        VolumeSourceEditorWindow(self.window, self.temp_dir, self.domain_origin, (source_name, self.current_sources[source_name]), self.on_source_edited)
    
    def delete_source(self):
        """Elimina la sorgente selezionata"""
        selection = self.sources_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona una sorgente da eliminare!")
            return
        
        full_text = self.sources_listbox.get(selection[0])
        source_name = full_text.split(' (')[0]
        
        if messagebox.askyesno("Conferma", f"Eliminare la sorgente '{source_name}'?"):
            del self.current_sources[source_name]
            self.refresh_sources_list()
            self.show_empty_details()
    
    def on_source_added(self, source_name, source_data, save_to_db):
        """Callback quando una nuova sorgente viene aggiunta"""
        self.current_sources[source_name] = source_data
        
        if save_to_db:
            self.sources_database[source_name] = source_data.copy()
            self.save_sources_database()
            messagebox.showinfo("Successo", f"Sorgente '{source_name}' aggiunta e salvata nel database!")
        
        self.refresh_sources_list()
    
    def on_source_edited(self, old_name, new_name, source_data, save_to_db):
        """Callback quando una sorgente viene modificata"""
        if old_name != new_name:
            del self.current_sources[old_name]
        
        self.current_sources[new_name] = source_data
        
        if save_to_db:
            self.sources_database[new_name] = source_data.copy()
            self.save_sources_database()
        
        self.refresh_sources_list()
        self.show_source_details(new_name)
    
    def save_and_close(self):
        """Salva le sorgenti nella configurazione e chiude"""
        config_file = self.temp_dir / 'calpuff_config.json'
        
        try:
            # Carica configurazione esistente
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                config_data = {}
            
            # Aggiorna le sorgenti volumetriche (converti dizionario in lista)
            config_data['volume_emission'] = list(self.current_sources.values())
            
            # Aggiorna anche VOLUME_NAMES
            config_data['volume_names'] = self.volume_names
            config_data['volume_names_location'] = self.volume_names_location
            
            # Salva
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Successo", f"{len(self.current_sources)} sorgenti volumetriche salvate nella configurazione!")
            self.window.destroy()
        
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il salvataggio:\n{str(e)}")


class VolumeSourceEditorWindow:
    """Finestra per creare/modificare una sorgente volumetrica"""
    
    def __init__(self, parent, temp_dir, domain_origin, source_data, callback):
        """
        domain_origin: origine del dominio per conversione km -> lat/lon
        source_data: None per nuova sorgente, oppure (nome, dati) per modifica
        callback: funzione da chiamare al salvataggio
        """
        self.parent = parent
        self.temp_dir = temp_dir
        self.domain_origin = domain_origin
        self.callback = callback
        self.is_edit = source_data is not None
        
        self.window = tk.Toplevel(parent)
        self.window.title("Modifica Sorgente" if self.is_edit else "Nuova Sorgente Volumetrica")
        self.window.geometry("1000x700")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Widget mappa
        self.map_widget = None
        self.map_marker = None
        self.domain_polygon = None
        self.grid_paths = []
        
        # Dati
        if self.is_edit:
            self.original_name = source_data[0]
            data = source_data[1]
        else:
            self.original_name = None
            data = {}
        
        # Variabili
        self.source_name = tk.StringVar(value=self.original_name if self.is_edit else "")
        position = data.get('position', [0.0, 0.0])
        self.pos_x = tk.DoubleVar(value=position[0])
        self.pos_y = tk.DoubleVar(value=position[1])
        self.height = tk.DoubleVar(value=data.get('height', 9.0))
        self.base_elev = tk.DoubleVar(value=data.get('base_elev', 0.0))
        self.initial_sigma_z = tk.DoubleVar(value=data.get('initial_sigma_z', 7.0))
        self.initial_sigma_y = tk.DoubleVar(value=data.get('initial_sigma_y', 10.0))
        self.save_to_db = tk.BooleanVar(value=False)
        
        # Tassi di emissione (lista di stringhe per la visualizzazione)
        self.emis_rates_str = tk.StringVar(value=self.format_emis_rates(data.get('emis_rates', [])))
        
        self.setup_ui()
        
        # Aggiorna mappa iniziale se in modifica
        if self.is_edit and self.map_widget:
            self.update_map()
    
    def format_emis_rates(self, rates):
        """Formatta i tassi di emissione per la visualizzazione"""
        if not rates:
            return ""
        return ", ".join([f"{r:.4E}" for r in rates])
    
    def parse_emis_rates(self, rates_str):
        """Analizza i tassi di emissione dalla stringa"""
        try:
            if not rates_str.strip():
                return []
            parts = [p.strip() for p in rates_str.split(',')]
            return [float(p) for p in parts if p]
        except ValueError:
            raise ValueError("Formato tassi di emissione non valido. Usa valori separati da virgola (es: 2.00E-002, 3.00E-002)")
    
    def setup_ui(self):
        """Configura l'interfaccia"""
        # Frame principale diviso in due colonne
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # === COLONNA SINISTRA: Form ===
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        canvas = tk.Canvas(left_frame)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # === COLONNA DESTRA: Mappa ===
        right_frame = ttk.LabelFrame(main_frame, text="Posizione sulla Mappa", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=0)
        
        # Widget mappa
        if MAPVIEW_AVAILABLE and self.domain_origin:
            try:
                self.map_widget = tkintermapview.TkinterMapView(right_frame, corner_radius=0)
                self.map_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                
                # Inizializza la mappa mostrando il dominio
                self.initialize_map_with_domain()
                
            except Exception as e:
                print(f"Errore creazione widget mappa: {e}")
                ttk.Label(right_frame, text="Mappa non disponibile", 
                         font=('Arial', 10, 'italic'), foreground='gray').grid(row=0, column=0, pady=20)
        else:
            info_text = "Mappa non disponibile"
            if not MAPVIEW_AVAILABLE:
                info_text += "\n(Installa tkintermapview)"
            elif not self.domain_origin:
                info_text += "\n(Configura prima il dominio)"
            ttk.Label(right_frame, text=info_text, 
                     font=('Arial', 10, 'italic'), foreground='gray').grid(row=0, column=0, pady=20)
        
        # Pulsanti per la mappa
        map_buttons_frame = ttk.Frame(right_frame)
        map_buttons_frame.grid(row=1, column=0, pady=10)
        
        ttk.Button(map_buttons_frame, text="🗺️ Aggiorna Mappa", 
                  command=self.update_map, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(map_buttons_frame, text="📍 Clicca sulla Mappa", 
                  command=self.start_map_click, width=20).pack(side=tk.LEFT, padx=5)
        
        row = 0
        
        # Nome sorgente
        ttk.Label(scrollable_frame, text="Nome Sorgente:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=10)
        row += 1
        ttk.Entry(scrollable_frame, textvariable=self.source_name, width=40).grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=10)
        row += 1
        
        # Frame parametri geometrici
        geo_frame = ttk.LabelFrame(scrollable_frame, text="Parametri Geometrici (posizione in km)", padding="10")
        geo_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10, padx=10)
        geo_frame.columnconfigure(1, weight=1)
        row += 1
        
        ttk.Label(geo_frame, text="Posizione X (km):").grid(row=0, column=0, sticky=tk.W, pady=5)
        pos_x_entry = ttk.Entry(geo_frame, textvariable=self.pos_x, width=20)
        pos_x_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        pos_x_entry.bind('<Return>', lambda e: self.update_map())
        
        ttk.Label(geo_frame, text="Posizione Y (km):").grid(row=1, column=0, sticky=tk.W, pady=5)
        pos_y_entry = ttk.Entry(geo_frame, textvariable=self.pos_y, width=20)
        pos_y_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        pos_y_entry.bind('<Return>', lambda e: self.update_map())
        
        ttk.Label(geo_frame, text="Altezza (m):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(geo_frame, textvariable=self.height, width=20).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(geo_frame, text="Elevazione Base (m):").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(geo_frame, textvariable=self.base_elev, width=20).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # Frame parametri dispersione
        disp_frame = ttk.LabelFrame(scrollable_frame, text="Parametri Dispersione", padding="10")
        disp_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10, padx=10)
        disp_frame.columnconfigure(1, weight=1)
        row += 1
        
        ttk.Label(disp_frame, text="Sigma Z Iniziale (m):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(disp_frame, textvariable=self.initial_sigma_z, width=20).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(disp_frame, text="Sigma Y Iniziale (m):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(disp_frame, textvariable=self.initial_sigma_y, width=20).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # Frame tassi di emissione
        emis_frame = ttk.LabelFrame(scrollable_frame, text="Tassi di Emissione", padding="10")
        emis_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10, padx=10)
        emis_frame.columnconfigure(0, weight=1)
        row += 1
        
        ttk.Label(emis_frame, text="Inserisci i tassi di emissione separati da virgola\n(es: 2.00E-002, 3.00E-002)", 
                 font=('Arial', 8, 'italic')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        emis_entry = ttk.Entry(emis_frame, textvariable=self.emis_rates_str, width=50)
        emis_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # Checkbox per salvare nel database
        ttk.Checkbutton(
            scrollable_frame, 
            text="Salva questa sorgente nel database per riutilizzi futuri", 
            variable=self.save_to_db
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=15, padx=10)
        row += 1
        
        # Bottoni
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="💾 Salva", command=self.save_source, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="❌ Annulla", command=self.window.destroy, width=15).pack(side=tk.LEFT, padx=10)
    
    def save_source(self):
        """Salva la sorgente"""
        name = self.source_name.get().strip()
        
        if not name:
            messagebox.showerror("Errore", "Inserire un nome per la sorgente!")
            return
        
        # Valida e analizza i tassi di emissione
        try:
            emis_rates = self.parse_emis_rates(self.emis_rates_str.get())
            if not emis_rates:
                messagebox.showerror("Errore", "Inserire almeno un tasso di emissione!")
                return
        except ValueError as e:
            messagebox.showerror("Errore", str(e))
            return
        
        # Raccogli dati
        source_data = {
            'source_name': name,
            'position': [self.pos_x.get(), self.pos_y.get()],
            'height': self.height.get(),
            'base_elev': self.base_elev.get(),
            'initial_sigma_z': self.initial_sigma_z.get(),
            'initial_sigma_y': self.initial_sigma_y.get(),
            'emis_rates': emis_rates
        }
        
        # Callback
        if self.is_edit:
            self.callback(self.original_name, name, source_data, self.save_to_db.get())
        else:
            self.callback(name, source_data, self.save_to_db.get())
        
        self.window.destroy()
    
    def km_to_lat_lon(self, x_km, y_km):
        """Converte coordinate UTM (in km) in lat/lon"""
        if not self.domain_origin or not PYPROJ_AVAILABLE:
            return None, None
        
        try:
            zona_utm = self.domain_origin.get('zona_utm', '32N')
            utm_zone = int(zona_utm[:-1])
            hemisphere = 'north' if zona_utm[-1] == 'N' else 'south'
            
            crs_wgs84 = CRS.from_epsg(4326)
            crs_utm = CRS.from_dict({
                'proj': 'utm',
                'zone': utm_zone,
                'hemisphere': hemisphere,
                'ellps': 'WGS84'
            })
            
            source_utm_x = x_km * 1000
            source_utm_y = y_km * 1000
            
            transformer_to_wgs84 = Transformer.from_crs(crs_utm, crs_wgs84, always_xy=True)
            lon, lat = transformer_to_wgs84.transform(source_utm_x, source_utm_y)
            
            return lat, lon
            
        except Exception as e:
            print(f"Errore conversione coordinate: {e}")
            return None, None
    
    def lat_lon_to_km(self, lat, lon):
        """Converte coordinate lat/lon in UTM (km)"""
        if not self.domain_origin or not PYPROJ_AVAILABLE:
            return None, None
        
        try:
            zona_utm = self.domain_origin.get('zona_utm', '32N')
            utm_zone = int(zona_utm[:-1])
            hemisphere = 'north' if zona_utm[-1] == 'N' else 'south'
            
            crs_wgs84 = CRS.from_epsg(4326)
            crs_utm = CRS.from_dict({
                'proj': 'utm',
                'zone': utm_zone,
                'hemisphere': hemisphere,
                'ellps': 'WGS84'
            })
            
            transformer_to_utm = Transformer.from_crs(crs_wgs84, crs_utm, always_xy=True)
            utm_x, utm_y = transformer_to_utm.transform(lon, lat)
            
            x_km = utm_x / 1000
            y_km = utm_y / 1000
            
            return x_km, y_km
            
        except Exception as e:
            print(f"Errore conversione coordinate: {e}")
            return None, None

    def km_to_degree_steps(self, step_km, reference_lat):
        """Converte un passo in km in delta lat/lon approssimati."""
        lat_step = step_km / 110.574
        cos_lat = abs(math.cos(math.radians(reference_lat)))
        if cos_lat < 1e-6:
            cos_lat = 1e-6
        lon_step = step_km / (111.320 * cos_lat)
        return lat_step, lon_step

    def utm_to_lat_lon(self, zona_utm, km_x, km_y):
        """Converte coordinate UTM (km) in lat/lon per il disegno della griglia."""
        if not PYPROJ_AVAILABLE or not zona_utm:
            return None, None

        try:
            utm_zone = int(zona_utm[:-1])
            hemisphere = 'north' if zona_utm[-1].upper() == 'N' else 'south'

            crs_wgs84 = CRS.from_epsg(4326)
            crs_utm = CRS.from_dict({
                'proj': 'utm',
                'zone': utm_zone,
                'hemisphere': hemisphere,
                'ellps': 'WGS84'
            })

            transformer = Transformer.from_crs(crs_utm, crs_wgs84, always_xy=True)
            lon, lat = transformer.transform(km_x * 1000.0, km_y * 1000.0)
            return lat, lon

        except Exception as e:
            print(f"Errore conversione griglia UTM -> lat/lon: {e}")
            return None, None

    def draw_grid_overlay(self):
        """Disegna la griglia del dominio sulla mappa, se disponibile."""
        if not self.map_widget or not self.domain_origin:
            return

        for path in self.grid_paths:
            try:
                path.delete()
            except Exception:
                pass
        self.grid_paths = []

        origin_lat = self.domain_origin.get('lat')
        origin_lon = self.domain_origin.get('lon')
        step_value = self.domain_origin.get('grid_step')
        nx = self.domain_origin.get('nx')
        ny = self.domain_origin.get('ny')

        if None in (origin_lat, origin_lon, step_value, nx, ny):
            return

        try:
            origin_lat = float(origin_lat)
            origin_lon = float(origin_lon)
            step_value = float(step_value)
            nx = int(nx)
            ny = int(ny)
        except (TypeError, ValueError):
            return

        if step_value <= 0 or nx <= 0 or ny <= 0:
            return

        unit = self.domain_origin.get('grid_step_unit', 'km')
        grid_lines = []

        if unit == 'km':
            zona_utm = self.domain_origin.get('zona_utm', '32N')
            origin_x_km, origin_y_km = self.lat_lon_to_km(origin_lat, origin_lon)

            if origin_x_km is not None and origin_y_km is not None:
                max_x_km = origin_x_km + (nx * step_value)
                max_y_km = origin_y_km + (ny * step_value)

                for ix in range(nx + 1):
                    current_x_km = origin_x_km + (ix * step_value)
                    start = self.utm_to_lat_lon(zona_utm, current_x_km, origin_y_km)
                    end = self.utm_to_lat_lon(zona_utm, current_x_km, max_y_km)
                    if None not in start and None not in end:
                        grid_lines.append([start, end])

                for iy in range(ny + 1):
                    current_y_km = origin_y_km + (iy * step_value)
                    start = self.utm_to_lat_lon(zona_utm, origin_x_km, current_y_km)
                    end = self.utm_to_lat_lon(zona_utm, max_x_km, current_y_km)
                    if None not in start and None not in end:
                        grid_lines.append([start, end])

        if not grid_lines:
            if unit == 'km':
                lat_step, lon_step = self.km_to_degree_steps(step_value, origin_lat)
            else:
                lat_step = step_value
                lon_step = step_value

            max_lat = origin_lat + (ny * lat_step)
            max_lon = origin_lon + (nx * lon_step)

            for ix in range(nx + 1):
                current_lon = origin_lon + (ix * lon_step)
                grid_lines.append([(origin_lat, current_lon), (max_lat, current_lon)])

            for iy in range(ny + 1):
                current_lat = origin_lat + (iy * lat_step)
                grid_lines.append([(current_lat, origin_lon), (current_lat, max_lon)])

        for line_coords in grid_lines:
            path = self.map_widget.set_path(
                line_coords,
                color="#1E90FF",
                width=1
            )
            self.grid_paths.append(path)
    
    def initialize_map_with_domain(self):
        """Inizializza la mappa mostrando il dominio completo"""
        if not self.map_widget or not self.domain_origin:
            return
        
        try:
            vertices = self.domain_origin.get('vertices', {})
            if not vertices:
                # Nessun vertice, usa origine
                origin_lat = self.domain_origin.get('lat')
                origin_lon = self.domain_origin.get('lon')
                if origin_lat and origin_lon:
                    self.map_widget.set_position(origin_lat, origin_lon)
                    self.map_widget.set_zoom(10)
                return
            
            # Crea lista coordinate per il poligono (in ordine: NW, NE, SE, SW)
            polygon_coords = []
            for corner in ['NW', 'NE', 'SE', 'SW']:
                if corner in vertices:
                    lat = vertices[corner].get('lat')
                    lon = vertices[corner].get('lon')
                    if lat is not None and lon is not None:
                        polygon_coords.append((lat, lon))
            
            if len(polygon_coords) >= 3:
                # Disegna il poligono del dominio
                self.domain_polygon = self.map_widget.set_polygon(
                    polygon_coords,
                    fill_color=None,
                    outline_color="blue",
                    border_width=3,
                    name="domain"
                )
                
                # Centra la mappa sul dominio
                center_lat = sum(c[0] for c in polygon_coords) / len(polygon_coords)
                center_lon = sum(c[1] for c in polygon_coords) / len(polygon_coords)
                self.map_widget.set_position(center_lat, center_lon)
                self.map_widget.set_zoom(10)

            self.draw_grid_overlay()
                
        except Exception as e:
            print(f"Errore inizializzazione mappa con dominio: {e}")
    
    def update_map(self):
        """Aggiorna la visualizzazione sulla mappa"""
        if not self.map_widget:
            return
        
        try:
            x_km = self.pos_x.get()
            y_km = self.pos_y.get()
        except tk.TclError:
            return
        
        lat, lon = self.km_to_lat_lon(x_km, y_km)
        
        if lat is None or lon is None:
            return
        
        try:
            # Rimuovi marker precedente
            if self.map_marker:
                self.map_marker.delete()
            
            # Aggiungi marker per la sorgente
            name = self.source_name.get() or "Nuova Sorgente"
            try:
                height = self.height.get()
            except tk.TclError:
                height = 0
                
            self.map_marker = self.map_widget.set_marker(
                lat, lon,
                text=f"{name}\nX: {x_km:.2f} km\nY: {y_km:.2f} km\nH: {height}m",
                marker_color_circle="purple",
                marker_color_outside="darkviolet"
            )
            
        except Exception as e:
            print(f"Errore aggiornamento mappa: {e}")
    
    def start_map_click(self):
        """Attiva la modalità click sulla mappa per selezionare la posizione"""
        if not MAPVIEW_AVAILABLE or not self.map_widget:
            messagebox.showinfo("Info", "Mappa non disponibile")
            return
        
        waiting_for_click = {'active': True}
        
        def on_map_click(coords):
            if not waiting_for_click['active']:
                return
            
            lat, lon = coords
            x_km, y_km = self.lat_lon_to_km(lat, lon)
            
            if x_km is not None and y_km is not None:
                self.pos_x.set(round(x_km, 3))
                self.pos_y.set(round(y_km, 3))
                self.update_map()
                waiting_for_click['active'] = False
                self.map_widget.add_left_click_map_command(None)
        
        self.map_widget.add_left_click_map_command(on_map_click)
        messagebox.showinfo("Modalità Click", 
                          "Clicca sulla mappa per selezionare la posizione della sorgente")
