"""
Finestra per la configurazione delle linee galleggianti (Buoyant Line Sources) in CALPUFF
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from pathlib import Path

# Import opzionali per la mappa
try:
    import tkintermapview as tkmv
    from pyproj import CRS, Transformer
    MAPVIEW_AVAILABLE = True
    PYPROJ_AVAILABLE = True
except ImportError:
    MAPVIEW_AVAILABLE = False
    PYPROJ_AVAILABLE = False


class LineSourcesWindow:
    """Finestra per gestire le sorgenti linee galleggianti e i file LINE_NAMES"""
    
    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = temp_dir
        self.window = tk.Toplevel(parent)
        self.window.title("Configurazione Linee Galleggianti (Buoyant Line)")
        self.window.geometry("900x700")
        
        # Database delle sorgenti (salvato separatamente)
        self.sources_db_file = Path("saved_configurations") / "line_sources_database.json"
        self.sources_database = self.load_sources_database()
        
        # Sorgenti correnti e file LINE_NAMES (dalla configurazione temporanea)
        self.current_sources = []
        self.line_names = ['DUMMY.DAT']  # Default
        self.load_current_sources()
        
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
                print(f"Errore caricamento database linee galleggianti: {e}")
                return {}
        return {}
    
    def save_sources_database(self):
        """Salva il database delle sorgenti"""
        try:
            self.sources_db_file.parent.mkdir(exist_ok=True)
            with open(self.sources_db_file, 'w', encoding='utf-8') as f:
                json.dump(self.sources_database, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Errore salvataggio database linee galleggianti: {e}")
    
    def load_current_sources(self):
        """Carica le sorgenti dalla configurazione temporanea"""
        calpuff_config = self.temp_dir / "calpuff_config.json"
        if calpuff_config.exists():
            try:
                with open(calpuff_config, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_sources = data.get('line_emission', [])
                    self.line_names = data.get('line_names', ['DUMMY.DAT'])
            except Exception as e:
                print(f"Errore caricamento sorgenti correnti: {e}")
    
    def save_current_sources(self):
        """Salva le sorgenti nella configurazione temporanea"""
        calpuff_config = self.temp_dir / "calpuff_config.json"
        try:
            # Carica config esistente o crea nuova
            if calpuff_config.exists():
                with open(calpuff_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Aggiorna sorgenti e file
            config['line_emission'] = self.current_sources
            config['line_names'] = self.line_names
            
            # Salva
            with open(calpuff_config, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Errore salvataggio sorgenti: {e}")
            messagebox.showerror("Errore", f"Errore nel salvataggio: {e}")
    
    def setup_ui(self):
        """Crea l'interfaccia utente"""
        # Frame principale con due sezioni
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        # ===== SEZIONE FILE LINE_NAMES =====
        files_frame = ttk.LabelFrame(main_frame, text="File LINE_NAMES", padding="10")
        files_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        main_frame.columnconfigure(0, weight=1)
        
        # Lista file
        files_list_frame = ttk.Frame(files_frame)
        files_list_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        files_list_frame.columnconfigure(0, weight=1)
        files_list_frame.rowconfigure(0, weight=1)
        
        # Scrollbar per file
        files_scrollbar = ttk.Scrollbar(files_list_frame)
        files_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Listbox file
        self.files_listbox = tk.Listbox(files_list_frame, height=4, 
                                        yscrollcommand=files_scrollbar.set)
        self.files_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        files_scrollbar.config(command=self.files_listbox.yview)
        
        # Pulsanti per file
        ttk.Button(files_frame, text="➕ Aggiungi File", 
                  command=self.add_file).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(files_frame, text="🗑️ Rimuovi File", 
                  command=self.remove_file).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(files_frame, text="🔄 Reset a DUMMY.DAT", 
                  command=self.reset_files).grid(row=1, column=2, padx=5, pady=5)
        
        # ===== SEZIONE SORGENTI =====
        sources_frame = ttk.LabelFrame(main_frame, text="Sorgenti Linee Galleggianti", padding="10")
        sources_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.rowconfigure(1, weight=1)
        sources_frame.columnconfigure(0, weight=1)
        sources_frame.rowconfigure(0, weight=1)
        
        # Lista sorgenti con scrollbar
        list_frame = ttk.Frame(sources_frame)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.sources_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.sources_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.sources_listbox.yview)
        
        # Pulsanti sorgenti
        buttons_frame = ttk.Frame(sources_frame)
        buttons_frame.grid(row=1, column=0, pady=10)
        
        ttk.Button(buttons_frame, text="➕ Nuova Sorgente", 
                  command=self.add_source).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="✏️ Modifica", 
                  command=self.edit_source).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🗑️ Elimina", 
                  command=self.delete_source).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="💾 Salva nel Database", 
                  command=self.save_to_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="📂 Carica dal Database", 
                  command=self.load_from_database).pack(side=tk.LEFT, padx=5)
        
        # Bottoni finali
        final_buttons = ttk.Frame(main_frame)
        final_buttons.grid(row=2, column=0, pady=10)
        
        ttk.Button(final_buttons, text="💾 Salva Configurazione", 
                  command=self.save_and_close, width=25).pack(side=tk.LEFT, padx=5)
        ttk.Button(final_buttons, text="❌ Annulla", 
                  command=self.window.destroy, width=25).pack(side=tk.LEFT, padx=5)
    
    def refresh_files_list(self):
        """Aggiorna la lista dei file nell'interfaccia"""
        self.files_listbox.delete(0, tk.END)
        for file in self.line_names:
            self.files_listbox.insert(tk.END, file)
    
    def refresh_sources_list(self):
        """Aggiorna la lista delle sorgenti nell'interfaccia"""
        self.sources_listbox.delete(0, tk.END)
        for source in self.current_sources:
            name = source.get('source_name', 'N/A')
            height = source.get('relase_height', 0)
            num_points = len(source.get('position_xy', []))
            self.sources_listbox.insert(tk.END, 
                f"{name} - H:{height}m - Punti:{num_points}")
    
    def add_file(self):
        """Aggiunge un file alla lista"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Aggiungi File Line")
        dialog.geometry("500x150")
        dialog.transient(self.window)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(frame, text="Nome del file:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        filename_var = tk.StringVar(value="DUMMY.DAT")
        filename_entry = ttk.Entry(frame, textvariable=filename_var, width=40)
        filename_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        def browse_file():
            file_path = filedialog.askopenfilename(
                title="Seleziona file Line",
                filetypes=[("DAT files", "*.dat"), ("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if file_path:
                filename_var.set(Path(file_path).name)
        
        def add_and_close():
            filename = filename_var.get().strip()
            if filename:
                if filename not in self.line_names:
                    self.line_names.append(filename)
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
        filename = self.line_names[idx]
        
        if messagebox.askyesno("Conferma", f"Rimuovere il file '{filename}'?"):
            self.line_names.pop(idx)
            self.refresh_files_list()
    
    def reset_files(self):
        """Reset alla lista default"""
        if messagebox.askyesno("Conferma", "Ripristinare la lista a DUMMY.DAT?"):
            self.line_names = ['DUMMY.DAT']
            self.refresh_files_list()
    
    def add_source(self):
        """Aggiunge una nuova sorgente"""
        LineSourceEditor(self.window, self, None)
    
    def edit_source(self):
        """Modifica la sorgente selezionata"""
        selection = self.sources_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare una sorgente da modificare")
            return
        
        idx = selection[0]
        source = self.current_sources[idx]
        LineSourceEditor(self.window, self, source, idx)
    
    def delete_source(self):
        """Elimina la sorgente selezionata"""
        selection = self.sources_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare una sorgente da eliminare")
            return
        
        idx = selection[0]
        source_name = self.current_sources[idx].get('source_name', 'N/A')
        
        if messagebox.askyesno("Conferma", f"Eliminare la sorgente '{source_name}'?"):
            self.current_sources.pop(idx)
            self.refresh_sources_list()
    
    def save_to_database(self):
        """Salva una sorgente nel database"""
        selection = self.sources_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare una sorgente da salvare")
            return
        
        idx = selection[0]
        source = self.current_sources[idx]
        source_name = source.get('source_name', 'unnamed')
        
        self.sources_database[source_name] = source.copy()
        self.save_sources_database()
        messagebox.showinfo("Successo", f"Sorgente '{source_name}' salvata nel database")
    
    def load_from_database(self):
        """Carica una sorgente dal database"""
        if not self.sources_database:
            messagebox.showinfo("Info", "Database vuoto")
            return
        
        # Finestra di selezione
        dialog = tk.Toplevel(self.window)
        dialog.title("Carica dal Database")
        dialog.geometry("400x300")
        dialog.transient(self.window)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        
        ttk.Label(frame, text="Seleziona sorgente:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        listbox = tk.Listbox(frame)
        listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        
        for name in self.sources_database.keys():
            listbox.insert(tk.END, name)
        
        def load_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Attenzione", "Selezionare una sorgente")
                return
            
            source_name = listbox.get(selection[0])
            source = self.sources_database[source_name].copy()
            self.current_sources.append(source)
            self.refresh_sources_list()
            dialog.destroy()
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, pady=10)
        
        ttk.Button(button_frame, text="✅ Carica", command=load_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def save_and_close(self):
        """Salva e chiude la finestra"""
        self.save_current_sources()
        messagebox.showinfo("Successo", "Configurazione linee galleggianti salvata!")
        self.window.destroy()


class LineSourceEditor:
    """Editor per singola linea galleggiante"""
    
    def __init__(self, parent, main_window, source_data=None, source_idx=None):
        self.parent = parent
        self.main_window = main_window
        self.source_idx = source_idx
        self.is_edit = source_data is not None
        
        # Carica dominio per la mappa
        self.domain_origin = self.load_domain_origin()
        
        # Dati sorgente
        if source_data:
            self.source_name = tk.StringVar(value=source_data.get('source_name', ''))
            self.relase_height = tk.DoubleVar(value=source_data.get('relase_height', 9.0))
            self.base_elev = tk.DoubleVar(value=source_data.get('base_elev', 0.0))
            self.points = source_data.get('position_xy', [])
            self.emis_rates = source_data.get('emis_rates', [])
        else:
            self.source_name = tk.StringVar(value='Line1')
            self.relase_height = tk.DoubleVar(value=9.0)
            self.base_elev = tk.DoubleVar(value=0.0)
            self.points = []
            self.emis_rates = []
        
        self.setup_ui()
    
    def load_domain_origin(self):
        """Carica l'origine del dominio se disponibile"""
        temp_dir = self.main_window.temp_dir
        domain_config = temp_dir / "domain_config.json"
        if domain_config.exists():
            try:
                with open(domain_config, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    origin = data.get('grid_origin', {})
                    zona_utm = data.get('zona_utm', '32N')
                    vertices = data.get('vertices', {})
                    
                    if origin and 'lat' in origin and 'lon' in origin:
                        return {
                            'lat': origin['lat'],
                            'lon': origin['lon'],
                            'zona_utm': zona_utm,
                            'vertices': vertices
                        }
            except Exception as e:
                print(f"Errore caricamento origine dominio: {e}")
        return None
    
    def setup_ui(self):
        """Crea l'interfaccia dell'editor"""
        self.dialog = tk.Toplevel(self.parent)
        title = "Modifica Linea Galleggiante" if self.is_edit else "Nuova Linea Galleggiante"
        self.dialog.title(title)
        self.dialog.geometry("1100x700")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Frame principale con due colonne
        main_container = ttk.Frame(self.dialog)
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)  # Colonna mappa espandibile
        main_container.rowconfigure(0, weight=1)
        
        # ===== COLONNA SINISTRA: FORM =====
        left_frame = ttk.Frame(main_container, padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Canvas e scrollbar per form
        canvas = tk.Canvas(left_frame, width=450)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        row = 0
        
        # === PARAMETRI BASE ===
        params_frame = ttk.LabelFrame(scrollable_frame, text="Parametri Base", padding="10")
        params_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        params_frame.columnconfigure(1, weight=1)
        row += 1
        
        ttk.Label(params_frame, text="Nome Sorgente:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(params_frame, textvariable=self.source_name, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(params_frame, text="Release Height (m):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(params_frame, textvariable=self.relase_height, width=15).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(params_frame, text="Base Elevation (m):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(params_frame, textvariable=self.base_elev, width=15).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # === PUNTI LINEA ===
        points_frame = ttk.LabelFrame(scrollable_frame, text="Punti Linea (X, Y)", padding="10")
        points_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        points_frame.columnconfigure(0, weight=1)
        row += 1
        
        # Lista punti
        list_frame = ttk.Frame(points_frame)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        points_scrollbar = ttk.Scrollbar(list_frame)
        points_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.points_listbox = tk.Listbox(list_frame, yscrollcommand=points_scrollbar.set, height=8)
        self.points_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        points_scrollbar.config(command=self.points_listbox.yview)
        
        self.refresh_points_list()
        
        # Pulsanti punti
        points_buttons = ttk.Frame(points_frame)
        points_buttons.grid(row=1, column=0, pady=5)
        
        ttk.Button(points_buttons, text="➕ Aggiungi Punto", 
                  command=self.add_point).pack(side=tk.LEFT, padx=5)
        ttk.Button(points_buttons, text="✏️ Modifica Punto", 
                  command=self.edit_point).pack(side=tk.LEFT, padx=5)
        ttk.Button(points_buttons, text="🗑️ Rimuovi Punto", 
                  command=self.remove_point).pack(side=tk.LEFT, padx=5)
        
        # === TASSI DI EMISSIONE ===
        emis_frame = ttk.LabelFrame(scrollable_frame, text="Tassi di Emissione", padding="10")
        emis_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        emis_frame.columnconfigure(0, weight=1)
        row += 1
        
        ttk.Label(emis_frame, text="Inserire i tassi separati da virgola (es: 2.0E-2, 3.0E-2):").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.emis_rates_var = tk.StringVar(value=', '.join(str(x) for x in self.emis_rates))
        ttk.Entry(emis_frame, textvariable=self.emis_rates_var, width=50).grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # === AGGIORNA MAPPA ===
        map_button_frame = ttk.Frame(scrollable_frame)
        map_button_frame.grid(row=row, column=0, pady=10, padx=5)
        row += 1
        
        ttk.Button(map_button_frame, text="🗺️ Aggiorna Mappa", 
                  command=self.update_map, width=30).pack()
        
        # === BOTTONI FINALI ===
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.grid(row=row, column=0, pady=20, padx=5)
        row += 1
        
        ttk.Button(buttons_frame, text="💾 Salva", 
                  command=self.save_source, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="❌ Annulla", 
                  command=self.dialog.destroy, width=20).pack(side=tk.LEFT, padx=5)
        
        # ===== COLONNA DESTRA: MAPPA =====
        right_frame = ttk.Frame(main_container, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Titolo mappa
        ttk.Label(right_frame, text="Linea Galleggiante", 
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, pady=(0, 10))
        
        # Mappa o messaggio
        if MAPVIEW_AVAILABLE:
            self.map_widget = tkmv.TkinterMapView(right_frame, width=550, height=650)
            self.map_widget.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Imposta posizione di default
            if self.domain_origin:
                self.map_widget.set_position(self.domain_origin['lat'], self.domain_origin['lon'])
                self.map_widget.set_zoom(12)
            else:
                self.map_widget.set_position(45.0, 9.0)
                self.map_widget.set_zoom(8)
            
            # Percorso e markers
            self.line_path = None
            self.domain_polygon = None
            self.point_markers = []
            
            # Inizializza mappa dopo un breve ritardo
            self.dialog.after(500, self.initialize_map_with_domain)
        else:
            ttk.Label(right_frame, 
                     text="Mappa non disponibile\n(installa tkintermapview e pyproj)",
                     font=('Arial', 10)).grid(row=1, column=0)
    
    def refresh_points_list(self):
        """Aggiorna la lista dei punti"""
        self.points_listbox.delete(0, tk.END)
        for i, point in enumerate(self.points):
            x, y = point
            self.points_listbox.insert(tk.END, f"Punto {i+1}: X={x}, Y={y}")
    
    def add_point(self):
        """Aggiunge un punto"""
        # Controlla se ci sono già 2 punti (massimo per linee galleggianti)
        if len(self.points) >= 2:
            messagebox.showwarning("Limite Raggiunto", 
                                  "Una linea galleggiante può avere massimo 2 punti.")
            return
        
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Aggiungi Punto")
        dialog.geometry("450x280")
        dialog.transient(self.dialog)
        # Non usare grab_set() per permettere i click sulla mappa
        
        frame = ttk.Frame(dialog, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        
        x_var = tk.DoubleVar(value=0.0)
        y_var = tk.DoubleVar(value=0.0)
        
        ttk.Label(frame, text="X (km UTM):").grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        x_entry = ttk.Entry(frame, textvariable=x_var, width=20)
        x_entry.grid(row=0, column=1, pady=5, padx=5, sticky=(tk.W, tk.E))
        
        ttk.Label(frame, text="Y (km UTM):").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        y_entry = ttk.Entry(frame, textvariable=y_var, width=20)
        y_entry.grid(row=1, column=1, pady=5, padx=5, sticky=(tk.W, tk.E))
        
        ttk.Separator(frame, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Variabile per tenere traccia se stiamo aspettando un click sulla mappa
        waiting_for_click = {'active': False}
        preview_marker = {'marker': None}
        
        def on_map_click(coords):
            """Callback quando si clicca sulla mappa"""
            if not waiting_for_click['active']:
                return
            
            lat, lon = coords
            x_km, y_km = self.lat_lon_to_km(lat, lon)
            
            if x_km is not None and y_km is not None:
                x_entry.delete(0, tk.END)
                x_entry.insert(0, f"{x_km:.3f}")
                y_entry.delete(0, tk.END)
                y_entry.insert(0, f"{y_km:.3f}")
                
                # Rimuovi marker precedente se esiste
                if preview_marker['marker']:
                    preview_marker['marker'].delete()
                
                # Aggiungi marker preview
                preview_marker['marker'] = self.map_widget.set_marker(
                    lat, lon,
                    text=f"P{len(self.points) + 1}",
                    marker_color_circle="orange",
                    marker_color_outside="darkorange"
                )
        
        def toggle_map_selection():
            """Attiva/disattiva la selezione sulla mappa"""
            waiting_for_click['active'] = not waiting_for_click['active']
            if waiting_for_click['active']:
                map_btn.config(text="🗺️ Disattiva Mappa")
                messagebox.showinfo("Info", "Clicca sulla mappa per selezionare un punto")
            else:
                map_btn.config(text="🗺️ Seleziona su Mappa")
        
        def save_point():
            # Rimuovi marker preview
            if preview_marker['marker']:
                preview_marker['marker'].delete()
            
            self.points.append([x_var.get(), y_var.get()])
            self.refresh_points_list()
            self.update_map()
            dialog.destroy()
        
        def cancel():
            # Rimuovi marker preview
            if preview_marker['marker']:
                preview_marker['marker'].delete()
            dialog.destroy()
        
        # Aggiungi callback per click sulla mappa
        if MAPVIEW_AVAILABLE and hasattr(self, 'map_widget'):
            self.map_widget.add_left_click_map_command(on_map_click)
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        if MAPVIEW_AVAILABLE and hasattr(self, 'map_widget'):
            map_btn = ttk.Button(button_frame, text="🗺️ Seleziona su Mappa", 
                                command=toggle_map_selection)
            map_btn.grid(row=0, column=0, columnspan=2, padx=5, pady=(0, 10))
        
        ttk.Button(button_frame, text="✅ Aggiungi", command=save_point).grid(row=1, column=0, padx=5)
        ttk.Button(button_frame, text="❌ Annulla", command=cancel).grid(row=1, column=1, padx=5)
    
    def edit_point(self):
        """Modifica un punto"""
        selection = self.points_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare un punto da modificare")
            return
        
        idx = selection[0]
        point = self.points[idx]
        
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Modifica Punto")
        dialog.geometry("400x200")
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        x_var = tk.DoubleVar(value=point[0])
        y_var = tk.DoubleVar(value=point[1])
        
        ttk.Label(frame, text="X (km UTM):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=x_var, width=20).grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(frame, text="Y (km UTM):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=y_var, width=20).grid(row=1, column=1, pady=5, padx=5)
        
        def save_point():
            self.points[idx] = [x_var.get(), y_var.get()]
            self.refresh_points_list()
            self.update_map()
            dialog.destroy()
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="💾 Salva", command=save_point).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def remove_point(self):
        """Rimuove un punto"""
        selection = self.points_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare un punto da rimuovere")
            return
        
        idx = selection[0]
        if messagebox.askyesno("Conferma", f"Rimuovere il punto {idx+1}?"):
            self.points.pop(idx)
            self.refresh_points_list()
            self.update_map()
    
    def save_source(self):
        """Salva la sorgente"""
        # Validazione
        if not self.source_name.get().strip():
            messagebox.showerror("Errore", "Inserire un nome per la sorgente")
            return
        
        if len(self.points) != 2:
            messagebox.showerror("Errore", "Una linea galleggiante deve avere esattamente 2 punti")
            return
        
        # Parse emission rates
        try:
            emis_text = self.emis_rates_var.get().strip()
            if emis_text:
                emis_rates = [float(x.strip()) for x in emis_text.split(',')]
            else:
                emis_rates = []
        except ValueError:
            messagebox.showerror("Errore", "Formato tassi di emissione non valido")
            return
        
        # Crea dizionario sorgente
        source = {
            'source_name': self.source_name.get().strip(),
            'relase_height': self.relase_height.get(),
            'base_elev': self.base_elev.get(),
            'position_xy': self.points,
            'emis_rates': emis_rates
        }
        
        # Aggiungi o modifica
        if self.is_edit and self.source_idx is not None:
            self.main_window.current_sources[self.source_idx] = source
        else:
            self.main_window.current_sources.append(source)
        
        self.main_window.refresh_sources_list()
        self.dialog.destroy()
    
    # ===== METODI MAPPA =====
    
    def initialize_map_with_domain(self):
        """Inizializza la mappa con il dominio e i punti esistenti"""
        if not MAPVIEW_AVAILABLE or not hasattr(self, 'map_widget'):
            return
        
        # Disegna il dominio se disponibile
        if self.domain_origin and self.domain_origin.get('vertices'):
            self.draw_domain_polygon()
        
        # Disegna i punti esistenti
        if self.points:
            self.update_map()
    
    def draw_domain_polygon(self):
        """Disegna il poligono del dominio sulla mappa"""
        if not MAPVIEW_AVAILABLE or not PYPROJ_AVAILABLE:
            return
        
        try:
            vertices = self.domain_origin.get('vertices', {})
            if not vertices:
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
                # Rimuovi poligono precedente se esiste
                if self.domain_polygon:
                    self.domain_polygon.delete()
                
                # Disegna il poligono del dominio
                self.domain_polygon = self.map_widget.set_polygon(
                    polygon_coords,
                    fill_color=None,
                    outline_color="blue",
                    border_width=3,
                    name="Dominio"
                )
                
                # Centra la mappa sul dominio
                center_lat = sum(c[0] for c in polygon_coords) / len(polygon_coords)
                center_lon = sum(c[1] for c in polygon_coords) / len(polygon_coords)
                self.map_widget.set_position(center_lat, center_lon)
                self.map_widget.set_zoom(10)
                
        except Exception as e:
            print(f"Errore nel disegno del dominio: {e}")
    
    def update_map(self):
        """Aggiorna la visualizzazione della linea sulla mappa"""
        if not MAPVIEW_AVAILABLE or not hasattr(self, 'map_widget'):
            return
        
        # Rimuovi markers precedenti
        for marker in self.point_markers:
            marker.delete()
        self.point_markers = []
        
        # Rimuovi percorso precedente
        if self.line_path:
            self.line_path.delete()
            self.line_path = None
        
        if not self.points:
            return
        
        zona_utm = self.domain_origin.get('zona_utm', '32N') if self.domain_origin else '32N'
        
        # Converti punti e aggiungi markers
        lat_lon_points = []
        for i, point in enumerate(self.points):
            x_km, y_km = point
            lat, lon = self.km_to_lat_lon(x_km, y_km, zona_utm)
            
            if lat and lon:
                lat_lon_points.append((lat, lon))
                marker = self.map_widget.set_marker(
                    lat, lon,
                    text=f"P{i+1}",
                    marker_color_circle="green",
                    marker_color_outside="darkgreen"
                )
                self.point_markers.append(marker)
        
        # Disegna la linea
        if len(lat_lon_points) >= 2:
            self.line_path = self.map_widget.set_path(
                lat_lon_points,
                color="green",
                width=4
            )
    
    def lat_lon_to_km(self, lat, lon):
        """Converte coordinate lat/lon in km UTM"""
        if not PYPROJ_AVAILABLE or not self.domain_origin:
            return None, None
        
        try:
            zona_utm = self.domain_origin.get('zona_utm', '32N')
            hemisphere = 'north' if zona_utm[-1] == 'N' else 'south'
            zone_number = int(zona_utm[:-1])
            
            crs_wgs84 = CRS.from_epsg(4326)
            crs_utm = CRS.from_dict({
                'proj': 'utm',
                'zone': zone_number,
                'datum': 'WGS84',
                'units': 'm',
                'south': hemisphere == 'south'
            })
            
            transformer = Transformer.from_crs(crs_wgs84, crs_utm, always_xy=True)
            x_m, y_m = transformer.transform(lon, lat)
            
            return x_m / 1000.0, y_m / 1000.0
        except Exception as e:
            print(f"Errore conversione lat/lon -> km: {e}")
            return None, None
    
    def km_to_lat_lon(self, x_km, y_km, zona_utm='32N'):
        """Converte coordinate km UTM in lat/lon"""
        if not PYPROJ_AVAILABLE:
            return None, None
        
        try:
            hemisphere = 'north' if zona_utm[-1] == 'N' else 'south'
            zone_number = int(zona_utm[:-1])
            
            crs_utm = CRS.from_dict({
                'proj': 'utm',
                'zone': zone_number,
                'datum': 'WGS84',
                'units': 'm',
                'south': hemisphere == 'south'
            })
            crs_wgs84 = CRS.from_epsg(4326)
            
            transformer = Transformer.from_crs(crs_utm, crs_wgs84, always_xy=True)
            lon, lat = transformer.transform(x_km * 1000.0, y_km * 1000.0)
            
            return lat, lon
        except Exception as e:
            print(f"Errore conversione km -> lat/lon: {e}")
            return None, None
