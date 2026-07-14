"""
Finestra per la configurazione delle sorgenti areali (Area Sources) in CALPUFF
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import math
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


class AreaSourcesWindow:
    """Finestra per gestire le sorgenti areali e i file AREA_NAMES"""
    
    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = temp_dir
        self.window = tk.Toplevel(parent)
        self.window.title("Configurazione Sorgenti Areali")
        self.window.geometry("900x700")
        
        # Database delle sorgenti areali (salvato separatamente)
        self.sources_db_file = Path("saved_configurations") / "area_sources_database.json"
        self.sources_database = self.load_sources_database()
        
        # Sorgenti correnti e file AREA_NAMES (dalla configurazione temporanea)
        self.current_sources = []
        self.area_names = ['DUMMY.DAT']  # Default
        self.area_names_location = []  # Default
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
                print(f"Errore caricamento database sorgenti areali: {e}")
                return {}
        return {}
    
    def save_sources_database(self):
        """Salva il database delle sorgenti"""
        try:
            self.sources_db_file.parent.mkdir(exist_ok=True)
            with open(self.sources_db_file, 'w', encoding='utf-8') as f:
                json.dump(self.sources_database, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Errore salvataggio database sorgenti areali: {e}")
    
    def load_current_sources(self):
        """Carica le sorgenti dalla configurazione temporanea"""
        calpuff_config = self.temp_dir / "calpuff_config.json"
        if calpuff_config.exists():
            try:
                with open(calpuff_config, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_sources = data.get('area_emission', [])
                    self.area_names = data.get('area_names', ['DUMMY.DAT'])
                    self.area_names_location = data.get('area_names_location', [])
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
            config['area_emission'] = self.current_sources
            config['area_names'] = self.area_names
            config['area_names_location'] = self.area_names_location
            
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
        
        # ===== SEZIONE FILE AREA_NAMES =====
        files_frame = ttk.LabelFrame(main_frame, text="File AREA_NAMES", padding="10")
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
        sources_frame = ttk.LabelFrame(main_frame, text="Sorgenti Areali", padding="10")
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
        
        # Treeview per sorgenti
        columns = ('name', 'vertices', 'height', 'sigma_z')
        self.sources_tree = ttk.Treeview(list_frame, columns=columns, show='headings',
                                         yscrollcommand=scrollbar.set)
        self.sources_tree.heading('name', text='Nome')
        self.sources_tree.heading('vertices', text='Vertici')
        self.sources_tree.heading('height', text='Altezza (m)')
        self.sources_tree.heading('sigma_z', text='Sigma Z (m)')
        
        self.sources_tree.column('name', width=150)
        self.sources_tree.column('vertices', width=100)
        self.sources_tree.column('height', width=100)
        self.sources_tree.column('sigma_z', width=100)
        
        self.sources_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.sources_tree.yview)
        
        # Pulsanti per sorgenti
        btn_frame = ttk.Frame(sources_frame)
        btn_frame.grid(row=1, column=0, pady=5)
        
        ttk.Button(btn_frame, text="➕ Nuova Sorgente", 
                  command=self.add_source).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="✏️ Modifica", 
                  command=self.edit_source).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="🗑️ Elimina", 
                  command=self.delete_source).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="💾 Salva nel DB", 
                  command=self.save_to_database).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="📂 Carica dal DB", 
                  command=self.load_from_database).grid(row=0, column=4, padx=5)
        
        # Pulsante Salva e Chiudi
        ttk.Button(main_frame, text="💾 Salva e Chiudi", 
                  command=self.save_and_close).grid(row=2, column=0, pady=10)
    
    # ===== GESTIONE FILE AREA_NAMES =====
    
    def refresh_files_list(self):
        """Aggiorna la lista dei file"""
        self.files_listbox.delete(0, tk.END)
        for file_name in self.area_names:
            self.files_listbox.insert(tk.END, file_name)
    
    def add_file(self):
        """Aggiunge un file alla lista AREA_NAMES"""
        file_path = filedialog.askopenfilename(
            title="Seleziona file sorgente areale",
            filetypes=[("DAT files", "*.DAT"), ("Tutti i file", "*.*")]
        )
        
        if file_path:
            # Estrai solo il nome del file
            file_name = Path(file_path).name
            
            # Se la lista contiene solo DUMMY.DAT, sostituiscilo
            if self.area_names == ['DUMMY.DAT']:
                self.area_names = [file_name]
                self.area_names_location = [file_path]
            else:
                # Altrimenti aggiungi se non già presente
                if file_name not in self.area_names:
                    self.area_names.append(file_name)
                    self.area_names_location.append(file_path)
            
            self.refresh_files_list()
    
    def remove_file(self):
        """Rimuove un file dalla lista"""
        selection = self.files_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un file da rimuovere")
            return
        
        index = selection[0]
        del self.area_names_location[index]  # Rimuovi anche la posizione
        del self.area_names[index]
        
        # Se lista vuota, ripristina DUMMY.DAT
        if not self.area_names:
            self.area_names = ['DUMMY.DAT']
            self.area_names_location = []
        
        self.refresh_files_list()
    
    def reset_files(self):
        """Ripristina la lista a DUMMY.DAT"""
        if messagebox.askyesno("Conferma", "Ripristinare la lista a DUMMY.DAT?"):
            self.area_names = ['DUMMY.DAT']
            self.area_names_location = []
            self.refresh_files_list()
    
    # ===== GESTIONE SORGENTI =====
    
    def refresh_sources_list(self):
        """Aggiorna la lista delle sorgenti"""
        for item in self.sources_tree.get_children():
            self.sources_tree.delete(item)
        
        for source in self.current_sources:
            polygon = source.get('poligon', [])
            num_vertices = len(polygon)
            self.sources_tree.insert('', tk.END, values=(
                source.get('source_name', ''),
                f"{num_vertices} vertici",
                source.get('height', ''),
                source.get('initial_sigma_z', '')
            ))
    
    def add_source(self):
        """Apre la finestra per aggiungere una nuova sorgente"""
        editor = AreaSourceEditorWindow(self.window, self.temp_dir)
        self.window.wait_window(editor.window)
        
        if editor.result:
            self.current_sources.append(editor.result)
            self.refresh_sources_list()
    
    def edit_source(self):
        """Modifica la sorgente selezionata"""
        selection = self.sources_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona una sorgente da modificare")
            return
        
        index = self.sources_tree.index(selection[0])
        source_data = self.current_sources[index]
        
        editor = AreaSourceEditorWindow(self.window, self.temp_dir, source_data)
        self.window.wait_window(editor.window)
        
        if editor.result:
            self.current_sources[index] = editor.result
            self.refresh_sources_list()
    
    def delete_source(self):
        """Elimina la sorgente selezionata"""
        selection = self.sources_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona una sorgente da eliminare")
            return
        
        if messagebox.askyesno("Conferma", "Eliminare la sorgente selezionata?"):
            index = self.sources_tree.index(selection[0])
            del self.current_sources[index]
            self.refresh_sources_list()
    
    def save_to_database(self):
        """Salva una sorgente nel database"""
        selection = self.sources_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona una sorgente da salvare")
            return
        
        index = self.sources_tree.index(selection[0])
        source_data = self.current_sources[index]
        
        name = source_data.get('source_name', '')
        if not name:
            messagebox.showerror("Errore", "La sorgente deve avere un nome")
            return
        
        # Salva nel database
        self.sources_database[name] = source_data
        self.save_sources_database()
        
        messagebox.showinfo("Successo", f"Sorgente '{name}' salvata nel database")
    
    def load_from_database(self):
        """Carica una sorgente dal database"""
        if not self.sources_database:
            messagebox.showinfo("Info", "Nessuna sorgente salvata nel database")
            return
        
        # Finestra di selezione
        dialog = tk.Toplevel(self.window)
        dialog.title("Carica Sorgente dal Database")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Seleziona sorgente da caricare:").pack(pady=10)
        
        listbox = tk.Listbox(dialog)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for name in sorted(self.sources_database.keys()):
            listbox.insert(tk.END, name)
        
        def load_selected():
            selection = listbox.curselection()
            if selection:
                name = listbox.get(selection[0])
                source_data = self.sources_database[name].copy()
                self.current_sources.append(source_data)
                self.refresh_sources_list()
                dialog.destroy()
        
        ttk.Button(dialog, text="Carica", command=load_selected).pack(pady=10)
    
    def save_and_close(self):
        """Salva le sorgenti e chiude la finestra"""
        self.save_current_sources()
        self.window.destroy()


class AreaSourceEditorWindow:
    """Finestra per creare/modificare una singola sorgente areale"""
    
    def __init__(self, parent, temp_dir, source_data=None):
        self.parent = parent
        self.temp_dir = temp_dir
        self.source_data = source_data or {}
        self.result = None
        
        self.window = tk.Toplevel(parent)
        self.window.title("Nuova Sorgente Areale" if not source_data else "Modifica Sorgente Areale")
        self.window.geometry("1000x700")
        
        # Carica dominio per la mappa
        self.domain_origin = self.load_domain_origin()
        
        # Lista vertici del poligono
        self.vertices = []
        
        self.setup_ui()
        self.load_data()
        
        # Inizializza mappa con dominio se disponibile
        if MAPVIEW_AVAILABLE and self.domain_origin:
            self.window.after(500, self.initialize_map_with_domain)
    
    def load_domain_origin(self):
        """Carica l'origine del dominio se disponibile"""
        domain_config = self.temp_dir / "domain_config.json"
        if domain_config.exists():
            try:
                with open(domain_config, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    origin = data.get('grid_origin', {})
                    grid_step = data.get('grid_step', {})
                    zona_utm = data.get('zona_utm', '32N')
                    vertices = data.get('vertices', {})
                    
                    if origin and 'lat' in origin and 'lon' in origin:
                        return {
                            'lat': origin['lat'],
                            'lon': origin['lon'],
                            'zona_utm': zona_utm,
                            'vertices': vertices,
                            'grid_step': grid_step.get('value'),
                            'grid_step_unit': grid_step.get('unit', 'km'),
                            'nx': origin.get('nx'),
                            'ny': origin.get('ny')
                        }
            except Exception as e:
                print(f"Errore caricamento origine dominio: {e}")
        return None
    
    def setup_ui(self):
        """Crea l'interfaccia con form e mappa affiancati"""
        # Frame principale con due colonne
        main_container = ttk.Frame(self.window)
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
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
        
        # Campi del form
        self.fields = {}
        row = 0
        
        # Nome sorgente
        ttk.Label(scrollable_frame, text="Nome Sorgente:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.fields['source_name'] = ttk.Entry(scrollable_frame, width=30)
        self.fields['source_name'].grid(row=row, column=1, pady=5, padx=5)
        row += 1
        
        # Altezza (m)
        ttk.Label(scrollable_frame, text="Altezza (m):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.fields['height'] = ttk.Entry(scrollable_frame, width=30)
        self.fields['height'].grid(row=row, column=1, pady=5, padx=5)
        row += 1
        
        # Elevazione base (m)
        ttk.Label(scrollable_frame, text="Elevazione Base (m):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.fields['base_elev'] = ttk.Entry(scrollable_frame, width=30)
        self.fields['base_elev'].grid(row=row, column=1, pady=5, padx=5)
        row += 1
        
        # Sigma Z iniziale (m)
        ttk.Label(scrollable_frame, text="Sigma Z Iniziale (m):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.fields['initial_sigma_z'] = ttk.Entry(scrollable_frame, width=30)
        self.fields['initial_sigma_z'].grid(row=row, column=1, pady=5, padx=5)
        row += 1
        
        # Tassi di emissione
        ttk.Label(scrollable_frame, text="Tassi di Emissione:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Label(scrollable_frame, text="(separati da virgola)").grid(row=row+1, column=0, sticky=tk.W)
        self.fields['emis_rates'] = ttk.Entry(scrollable_frame, width=30)
        self.fields['emis_rates'].grid(row=row, column=1, rowspan=2, pady=5, padx=5)
        row += 2
        
        # Sezione Poligono
        ttk.Separator(scrollable_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(scrollable_frame, text="Vertici Poligono (UTM km):", 
                 font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Lista vertici
        vertices_frame = ttk.Frame(scrollable_frame)
        vertices_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        vertices_frame.columnconfigure(0, weight=1)
        
        vertices_scroll = ttk.Scrollbar(vertices_frame)
        vertices_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.vertices_listbox = tk.Listbox(vertices_frame, height=6, 
                                           yscrollcommand=vertices_scroll.set)
        self.vertices_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vertices_scroll.config(command=self.vertices_listbox.yview)
        row += 1
        
        # Pulsanti gestione vertici
        vertices_btn_frame = ttk.Frame(scrollable_frame)
        vertices_btn_frame.grid(row=row, column=0, columnspan=2, pady=5)
        
        ttk.Button(vertices_btn_frame, text="➕ Aggiungi Vertice", 
                  command=self.add_vertex).pack(side=tk.LEFT, padx=5)
        ttk.Button(vertices_btn_frame, text="🗑️ Rimuovi Vertice", 
                  command=self.remove_vertex).pack(side=tk.LEFT, padx=5)
        ttk.Button(vertices_btn_frame, text="🗺️ Aggiorna Mappa", 
                  command=self.update_map).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Pulsanti
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="💾 Salva", command=self.save).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="❌ Annulla", command=self.cancel).grid(row=0, column=1, padx=5)
        
        # ===== COLONNA DESTRA: MAPPA =====
        right_frame = ttk.Frame(main_container, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Titolo mappa
        ttk.Label(right_frame, text="Area Sorgente", 
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, pady=(0, 10))
        
        # Mappa o messaggio
        if MAPVIEW_AVAILABLE:
            self.map_widget = tkmv.TkinterMapView(right_frame, width=450, height=600)
            self.map_widget.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Imposta posizione di default
            if self.domain_origin:
                self.map_widget.set_position(self.domain_origin['lat'], self.domain_origin['lon'])
                self.map_widget.set_zoom(10)
            else:
                self.map_widget.set_position(45.0, 9.0)
                self.map_widget.set_zoom(8)
            
            # Poligono e markers
            self.area_polygon = None
            self.domain_polygon = None
            self.vertex_markers = []
            self.grid_paths = []
        else:
            ttk.Label(right_frame, 
                     text="Mappa non disponibile\n(installa tkintermapview e pyproj)",
                     font=('Arial', 10)).grid(row=1, column=0)
    
    def load_data(self):
        """Carica i dati della sorgente nei campi"""
        if self.source_data:
            self.fields['source_name'].insert(0, self.source_data.get('source_name', ''))
            self.fields['height'].insert(0, str(self.source_data.get('height', '')))
            self.fields['base_elev'].insert(0, str(self.source_data.get('base_elev', '')))
            self.fields['initial_sigma_z'].insert(0, str(self.source_data.get('initial_sigma_z', '')))
            
            emis_rates = self.source_data.get('emis_rates', [])
            if emis_rates:
                self.fields['emis_rates'].insert(0, ', '.join(map(str, emis_rates)))
            
            # Carica vertici del poligono
            polygon = self.source_data.get('poligon', [])
            self.vertices = polygon.copy()
            self.refresh_vertices_list()
    
    def refresh_vertices_list(self):
        """Aggiorna la lista dei vertici"""
        self.vertices_listbox.delete(0, tk.END)
        for i, vertex in enumerate(self.vertices):
            self.vertices_listbox.insert(tk.END, f"V{i+1}: X={vertex[0]}, Y={vertex[1]}")
    
    def add_vertex(self):
        """Aggiunge un vertice al poligono"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Aggiungi Vertice")
        dialog.geometry("350x200")
        dialog.transient(self.window)
        # Non usare grab_set() per permettere i click sulla mappa
        
        ttk.Label(dialog, text="Coordinata X (km UTM):").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        x_entry = ttk.Entry(dialog, width=20)
        x_entry.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Coordinata Y (km UTM):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        y_entry = ttk.Entry(dialog, width=20)
        y_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # Variabile per tenere traccia se stiamo aspettando un click sulla mappa
        waiting_for_click = {'active': False}
        preview_marker = {'marker': None}  # Marker temporaneo per il preview
        
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
                
                # Aggiungi marker preview immediato
                preview_marker['marker'] = self.map_widget.set_marker(
                    lat, lon,
                    text=f"V{len(self.vertices) + 1}",
                    marker_color_circle="orange",
                    marker_color_outside="darkorange"
                )
                
                # Disattiva la modalità click
                waiting_for_click['active'] = False
                map_click_btn.config(text="🗺️ Clicca sulla Mappa")
        
        def toggle_map_click():
            """Attiva/disattiva la modalità click sulla mappa"""
            if not MAPVIEW_AVAILABLE:
                messagebox.showinfo("Info", "Mappa non disponibile")
                return
            
            waiting_for_click['active'] = not waiting_for_click['active']
            
            if waiting_for_click['active']:
                map_click_btn.config(text="⏸️ Annulla Click")
                # Imposta il callback per i click sulla mappa
                self.map_widget.add_left_click_map_command(on_map_click)
            else:
                map_click_btn.config(text="🗺️ Clicca sulla Mappa")
                # Rimuovi il callback settandolo a None
                self.map_widget.add_left_click_map_command(None)
        
        def add():
            try:
                x = float(x_entry.get())
                y = float(y_entry.get())
                self.vertices.append([x, y])
                self.refresh_vertices_list()
                
                # Rimuovi handler se attivo
                waiting_for_click['active'] = False
                self.map_widget.add_left_click_map_command(None)
                
                # NON rimuovere il marker preview - verrà gestito da update_map()
                # che rimuove tutti i marker e li ricrea
                
                # Aggiorna la mappa con tutti i vertici
                self.update_map()
                
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Errore", "Inserisci valori numerici validi")
        
        def on_close():
            # Rimuovi handler se attivo
            waiting_for_click['active'] = False
            if MAPVIEW_AVAILABLE:
                self.map_widget.add_left_click_map_command(None)
            
            # Rimuovi marker preview se esiste
            if preview_marker['marker']:
                preview_marker['marker'].delete()
            
            dialog.destroy()
        
        # Pulsante per click sulla mappa
        map_click_btn = ttk.Button(dialog, text="🗺️ Clicca sulla Mappa", command=toggle_map_click)
        map_click_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Pulsanti conferma/annulla
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Aggiungi", command=add).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=on_close).pack(side=tk.LEFT, padx=5)
        
        dialog.protocol("WM_DELETE_WINDOW", on_close)
    
    def remove_vertex(self):
        """Rimuove il vertice selezionato"""
        selection = self.vertices_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un vertice da rimuovere")
            return
        
        index = selection[0]
        del self.vertices[index]
        self.refresh_vertices_list()
        # Aggiorna la mappa per rimuovere il marker e ridisegnare il poligono
        self.update_map()
    
    def initialize_map_with_domain(self):
        """Inizializza la mappa mostrando il dominio"""
        if not MAPVIEW_AVAILABLE or not self.domain_origin:
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
    
    def km_to_lat_lon(self, x_km, y_km):
        """Converte coordinate UTM (in km) in lat/lon"""
        if not self.domain_origin or not PYPROJ_AVAILABLE:
            return None, None
        
        try:
            # Ottieni la zona UTM dal dominio
            zona_utm = self.domain_origin.get('zona_utm', '32N')
            
            # Estrai numero zona ed emisfero
            utm_zone = int(zona_utm[:-1])  # Es: "32N" -> 32
            hemisphere = 'north' if zona_utm[-1] == 'N' else 'south'
            
            # CRS per WGS84 (lat/lon) e UTM
            crs_wgs84 = CRS.from_epsg(4326)  # WGS84
            crs_utm = CRS.from_dict({
                'proj': 'utm',
                'zone': utm_zone,
                'hemisphere': hemisphere,
                'ellps': 'WGS84'
            })
            
            # Converti km in metri (le coordinate sono già UTM assolute)
            source_utm_x = x_km * 1000  # da km a metri
            source_utm_y = y_km * 1000  # da km a metri
            
            # Trasforma da UTM a lat/lon
            transformer_to_wgs84 = Transformer.from_crs(crs_utm, crs_wgs84, always_xy=True)
            lon, lat = transformer_to_wgs84.transform(source_utm_x, source_utm_y)
            
            return lat, lon
            
        except Exception as e:
            print(f"Errore conversione coordinate: {e}")
            return None, None
    
    def lat_lon_to_km(self, lat, lon):
        """Converte coordinate lat/lon in UTM (km)
        
        Args:
            lat: Latitudine
            lon: Longitudine
            
        Returns:
            tuple: (x_km, y_km) o (None, None) se conversione non possibile
        """
        if not self.domain_origin or not PYPROJ_AVAILABLE:
            return None, None
        
        try:
            # Ottieni la zona UTM dal dominio
            zona_utm = self.domain_origin.get('zona_utm', '32N')
            
            # Estrai numero zona ed emisfero
            utm_zone = int(zona_utm[:-1])  # Es: "32N" -> 32
            hemisphere = 'north' if zona_utm[-1] == 'N' else 'south'
            
            # CRS per WGS84 (lat/lon) e UTM
            crs_wgs84 = CRS.from_epsg(4326)  # WGS84
            crs_utm = CRS.from_dict({
                'proj': 'utm',
                'zone': utm_zone,
                'hemisphere': hemisphere,
                'ellps': 'WGS84'
            })
            
            # Trasforma da lat/lon a UTM
            transformer_to_utm = Transformer.from_crs(crs_wgs84, crs_utm, always_xy=True)
            utm_x, utm_y = transformer_to_utm.transform(lon, lat)
            
            # Converti metri in km
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
        if not MAPVIEW_AVAILABLE or not self.domain_origin or not hasattr(self, 'map_widget'):
            return

        for path in getattr(self, 'grid_paths', []):
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
        zona_utm = self.domain_origin.get('zona_utm', '32N')
        grid_lines = []

        if unit == 'km':
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
    
    def update_map(self):
        """Aggiorna la visualizzazione del poligono sulla mappa"""
        if not MAPVIEW_AVAILABLE:
            return
        
        try:
            # Rimuovi TUTTI i marker dalla mappa (inclusi quelli temporanei)
            self.map_widget.delete_all_marker()
            self.vertex_markers = []
            
            # Rimuovi poligono precedente
            if self.area_polygon:
                self.area_polygon.delete()
                self.area_polygon = None
            
            # Converti vertici in lat/lon e aggiungi marker
            for i, vertex in enumerate(self.vertices):
                lat, lon = self.km_to_lat_lon(vertex[0], vertex[1])
                if lat is not None and lon is not None:
                    # Aggiungi marker per ogni vertice con numero
                    marker = self.map_widget.set_marker(
                        lat, lon, 
                        text=f"V{i+1}", 
                        marker_color_circle="orange",
                        marker_color_outside="darkorange"
                    )
                    self.vertex_markers.append(marker)
            
            # Disegno del poligono disabilitato per ora
            # TODO: Risolvere problema overlay poligono
            
        except Exception as e:
            print(f"Errore aggiornamento mappa: {e}")
    
    def save(self):
        """Salva i dati della sorgente"""
        try:
            # Validazione
            if not self.fields['source_name'].get():
                messagebox.showerror("Errore", "Il nome della sorgente è obbligatorio")
                return
            
            if len(self.vertices) < 3:
                messagebox.showerror("Errore", "Il poligono deve avere almeno 3 vertici")
                return
            
            # Raccogli dati
            emis_rates_str = self.fields['emis_rates'].get()
            emis_rates = []
            if emis_rates_str:
                emis_rates = [float(x.strip()) for x in emis_rates_str.split(',')]
            
            self.result = {
                'source_name': self.fields['source_name'].get(),
                'height': float(self.fields['height'].get()),
                'base_elev': float(self.fields['base_elev'].get()),
                'initial_sigma_z': float(self.fields['initial_sigma_z'].get()),
                'emis_rates': emis_rates,
                'poligon': self.vertices
            }
            
            self.window.destroy()
            
        except ValueError as e:
            messagebox.showerror("Errore", f"Valori non validi: {e}")
    
    def cancel(self):
        """Annulla le modifiche"""
        self.result = None
        self.window.destroy()
