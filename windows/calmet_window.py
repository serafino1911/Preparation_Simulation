"""
Finestra per la configurazione di CALMET
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path


class CalmetWindow:
    """Finestra per configurare i parametri di CALMET"""
    
    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = temp_dir
        self.window = tk.Toplevel(parent)
        self.window.title("Configurazione CALMET")
        self.window.geometry("800x700")
        
        # Variabili di configurazione
        self.start_date = tk.StringVar(value="2024-01-01")
        self.end_date = tk.StringVar(value="2024-01-02")
        self.month_calmet = tk.BooleanVar(value=False)
        self.month_calpuff = tk.BooleanVar(value=False)
        self.number_of_day = tk.IntVar(value=1)
        self.wrf_path = tk.StringVar(value="")
        self.calmet_output = tk.StringVar(value="Auto")
        self.calmet_data = tk.StringVar(value="CALMETDATA")
        self.calpuff_data = tk.StringVar(value="CALPUFFDATA")
        self.calpost_data = tk.StringVar(value="CALPOSTDATA")
        self.link_wrf = tk.BooleanVar(value=False)
        self.link_calmet = tk.BooleanVar(value=False)
        self.link_calpuff = tk.BooleanVar(value=False)
        
        # Projection Config
        self.proj = tk.StringVar(value="UTM")
        self.zone = tk.StringVar(value="32 N")
        self.origin_lat = tk.StringVar(value="44.404709N")
        self.origin_lon = tk.StringVar(value="8.868261E")
        self.mach_lat1 = tk.StringVar(value="40.00N")
        self.mach_lat2 = tk.StringVar(value="40.01N")
        self.feast = tk.StringVar(value="0.0")
        self.fnorth = tk.StringVar(value="0.0")
        
        # Grid Config
        self.nx = tk.IntVar(value=250)
        self.ny = tk.IntVar(value=185)
        self.dim = tk.DoubleVar(value=0.081)
        self.xori = tk.DoubleVar(value=479.385)
        self.yori = tk.DoubleVar(value=4909.341)
        self.nz = tk.IntVar(value=10)
        self.zface = tk.StringVar(value="0.,20.,40.,80.,160.,300.,600.,1000.,1500.,2200.,3000.")
        
        self.load_existing_config()
        self.setup_ui()
    
    def load_existing_config(self):
        """Carica la configurazione esistente se presente"""
        # Prima carica dai file di configurazione esistenti (domain, temporal)
        self.load_from_domain_config()
        self.load_from_temporal_config()
        
        # Poi sovrascrivi con i dati specifici di CALMET se esistono
        config_file = self.temp_dir / 'calmet_config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Carica i dati nelle variabili
                self.start_date.set(data.get('start_date', self.start_date.get()))
                self.end_date.set(data.get('end_date', self.end_date.get()))
                self.month_calmet.set(data.get('month_calmet', False))
                self.month_calpuff.set(data.get('month_calpuff', False))
                self.number_of_day.set(data.get('number_of_day', 1))
                self.wrf_path.set(data.get('wrf_path', ''))
                self.calmet_output.set(data.get('calmet_output', 'Auto'))
                self.calmet_data.set(data.get('calmet_data', 'CALMETDATA'))
                self.calpuff_data.set(data.get('calpuff_data', 'CALPUFFDATA'))
                self.calpost_data.set(data.get('calpost_data', 'CALPOSTDATA'))
                self.link_wrf.set(data.get('link_wrf', False))
                self.link_calmet.set(data.get('link_calmet', False))
                self.link_calpuff.set(data.get('link_calpuff', False))
                
                # Projection
                self.proj.set(data.get('proj', self.proj.get()))
                self.zone.set(data.get('zone', self.zone.get()))
                self.origin_lat.set(data.get('origin_lat', self.origin_lat.get()))
                self.origin_lon.set(data.get('origin_lon', self.origin_lon.get()))
                self.mach_lat1.set(data.get('mach_lat1', '40.00N'))
                self.mach_lat2.set(data.get('mach_lat2', '40.01N'))
                self.feast.set(data.get('feast', '0.0'))
                self.fnorth.set(data.get('fnorth', '0.0'))
                
                # Grid
                self.nx.set(data.get('nx', self.nx.get()))
                self.ny.set(data.get('ny', self.ny.get()))
                self.dim.set(data.get('dim', self.dim.get()))
                self.xori.set(data.get('xori', self.xori.get()))
                self.yori.set(data.get('yori', self.yori.get()))
                self.nz.set(data.get('nz', 10))
                self.zface.set(data.get('zface', '0.,20.,40.,80.,160.,300.,600.,1000.,1500.,2200.,3000.'))
                
            except Exception as e:
                print(f"Errore nel caricamento della configurazione CALMET: {e}")
    
    def load_from_domain_config(self):
        """Carica i dati dal domain_config.json se esiste"""
        domain_file = self.temp_dir / 'domain_config.json'
        if domain_file.exists():
            try:
                with open(domain_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Carica zona UTM
                if 'zona_utm' in data and data['zona_utm']:
                    self.zone.set(data['zona_utm'])
                
                # Carica grid step
                if 'grid_step' in data:
                    grid_step = data['grid_step']
                    if grid_step.get('unit') == 'km':
                        self.dim.set(grid_step.get('value', 0.081))
                
                # Carica origine griglia
                if 'grid_origin' in data:
                    origin = data['grid_origin']
                    
                    # NX e NY
                    if 'nx' in origin:
                        self.nx.set(origin['nx'])
                    if 'ny' in origin:
                        self.ny.set(origin['ny'])
                    
                    # XORI e YORI (da km_x e km_y)
                    if 'km_x' in origin and origin['km_x'] is not None:
                        self.xori.set(origin['km_x'])
                    if 'km_y' in origin and origin['km_y'] is not None:
                        self.yori.set(origin['km_y'])
                    
                    # Origin Lat/Lon - converti in formato stringa con N/S E/W
                    if 'lat' in origin and 'lon' in origin:
                        lat = origin['lat']
                        lon = origin['lon']
                        
                        # Formatta latitudine
                        lat_dir = 'N' if lat >= 0 else 'S'
                        lat_str = f"{abs(lat):.6f}{lat_dir}"
                        self.origin_lat.set(lat_str)
                        
                        # Formatta longitudine
                        lon_dir = 'E' if lon >= 0 else 'W'
                        lon_str = f"{abs(lon):.6f}{lon_dir}"
                        self.origin_lon.set(lon_str)
                
            except Exception as e:
                print(f"Errore nel caricamento da domain_config: {e}")
    
    def load_from_temporal_config(self):
        """Carica i dati dal temporal_config.json se esiste"""
        temporal_file = self.temp_dir / 'temporal_config.json'
        if temporal_file.exists():
            try:
                with open(temporal_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Carica le date
                if 'start_date' in data:
                    self.start_date.set(data['start_date'])
                if 'end_date' in data:
                    self.end_date.set(data['end_date'])
                
                # Carica meteo_path come wrf_path
                if 'meteo_path' in data:
                    self.wrf_path.set(data['meteo_path'])
                
            except Exception as e:
                print(f"Errore nel caricamento da temporal_config: {e}")
    
    def setup_ui(self):
        """Configura l'interfaccia utente"""
        # Frame principale con scrollbar
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configura il grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Canvas e scrollbar per contenuto scrollabile
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        main_frame.rowconfigure(0, weight=1)
        
        row = 0
        
        # === SEZIONE DATE E PARAMETRI GENERALI ===
        date_frame = ttk.LabelFrame(scrollable_frame, text="Date e Parametri Generali", padding="10")
        date_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        date_frame.columnconfigure(1, weight=1)
        date_frame.columnconfigure(3, weight=1)
        row += 1
        
        ttk.Label(date_frame, text="Data Inizio:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(date_frame, textvariable=self.start_date, width=20).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        
        ttk.Label(date_frame, text="Data Fine:").grid(row=0, column=2, sticky=tk.W, pady=5)
        ttk.Entry(date_frame, textvariable=self.end_date, width=20).grid(row=0, column=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(date_frame, text="Numero Giorni:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(date_frame, textvariable=self.number_of_day, width=20).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        
        check_frame = ttk.Frame(date_frame)
        check_frame.grid(row=1, column=2, columnspan=2, sticky=tk.W, pady=5)
        ttk.Checkbutton(check_frame, text="Month CALMET", variable=self.month_calmet).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Checkbutton(check_frame, text="Month CALPUFF", variable=self.month_calpuff).pack(side=tk.LEFT)
        
        # === SEZIONE PERCORSI ===
        path_frame = ttk.LabelFrame(scrollable_frame, text="Percorsi e Output", padding="10")
        path_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        path_frame.columnconfigure(1, weight=1)
        path_frame.columnconfigure(3, weight=1)
        row += 1
        
        ttk.Label(path_frame, text="WRF Path:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(path_frame, textvariable=self.wrf_path, width=30).grid(row=0, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(path_frame, text="CALMET Output:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(path_frame, textvariable=self.calmet_output, width=20).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        
        ttk.Label(path_frame, text="CALMET Data:").grid(row=1, column=2, sticky=tk.W, pady=5)
        ttk.Entry(path_frame, textvariable=self.calmet_data, width=20).grid(row=1, column=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(path_frame, text="CALPUFF Data:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(path_frame, textvariable=self.calpuff_data, width=20).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        
        ttk.Label(path_frame, text="CALPOST Data:").grid(row=2, column=2, sticky=tk.W, pady=5)
        ttk.Entry(path_frame, textvariable=self.calpost_data, width=20).grid(row=2, column=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        link_frame = ttk.Frame(path_frame)
        link_frame.grid(row=3, column=0, columnspan=4, sticky=tk.W, pady=(10, 5))
        ttk.Checkbutton(link_frame, text="Link WRF", variable=self.link_wrf).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Checkbutton(link_frame, text="Link CALMET", variable=self.link_calmet).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Checkbutton(link_frame, text="Link CALPUFF", variable=self.link_calpuff).pack(side=tk.LEFT)
        
        # === SEZIONE PROIEZIONE ===
        proj_frame = ttk.LabelFrame(scrollable_frame, text="Configurazione Proiezione", padding="10")
        proj_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        proj_frame.columnconfigure(1, weight=1)
        proj_frame.columnconfigure(3, weight=1)
        row += 1
        
        ttk.Label(proj_frame, text="Proiezione:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(proj_frame, textvariable=self.proj, values=['UTM', 'LCC'], state='readonly', width=18).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        
        ttk.Label(proj_frame, text="Zona:").grid(row=0, column=2, sticky=tk.W, pady=5)
        ttk.Entry(proj_frame, textvariable=self.zone, width=18).grid(row=0, column=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(proj_frame, text="Origin Lat:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(proj_frame, textvariable=self.origin_lat, width=18).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        
        ttk.Label(proj_frame, text="Origin Lon:").grid(row=1, column=2, sticky=tk.W, pady=5)
        ttk.Entry(proj_frame, textvariable=self.origin_lon, width=18).grid(row=1, column=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(proj_frame, text="Match Lat1:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(proj_frame, textvariable=self.mach_lat1, width=18).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        
        ttk.Label(proj_frame, text="Match Lat2:").grid(row=2, column=2, sticky=tk.W, pady=5)
        ttk.Entry(proj_frame, textvariable=self.mach_lat2, width=18).grid(row=2, column=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(proj_frame, text="False Easting:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(proj_frame, textvariable=self.feast, width=18).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        
        ttk.Label(proj_frame, text="False Northing:").grid(row=3, column=2, sticky=tk.W, pady=5)
        ttk.Entry(proj_frame, textvariable=self.fnorth, width=18).grid(row=3, column=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # === SEZIONE GRIGLIA ===
        grid_frame = ttk.LabelFrame(scrollable_frame, text="Configurazione Griglia", padding="10")
        grid_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        grid_frame.columnconfigure(1, weight=1)
        grid_frame.columnconfigure(3, weight=1)
        grid_frame.columnconfigure(5, weight=1)
        row += 1
        
        ttk.Label(grid_frame, text="NX:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(grid_frame, textvariable=self.nx, width=12).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(grid_frame, text="NY:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(grid_frame, textvariable=self.ny, width=12).grid(row=0, column=3, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(grid_frame, text="DIM (km):").grid(row=0, column=4, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(grid_frame, textvariable=self.dim, width=12).grid(row=0, column=5, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(grid_frame, text="XORI:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(grid_frame, textvariable=self.xori, width=12).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(grid_frame, text="YORI:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(grid_frame, textvariable=self.yori, width=12).grid(row=1, column=3, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(grid_frame, text="NZ:").grid(row=1, column=4, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(grid_frame, textvariable=self.nz, width=12).grid(row=1, column=5, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(grid_frame, text="ZFACE:").grid(row=2, column=0, sticky=tk.W, pady=5)
        zface_entry = ttk.Entry(grid_frame, textvariable=self.zface)
        zface_entry.grid(row=2, column=1, columnspan=5, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # === BOTTONI AZIONE ===
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=row, column=0, pady=20)
        row += 1
        
        ttk.Button(button_frame, text="💾 Salva", command=self.save_config, width=20).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="❌ Annulla", command=self.window.destroy, width=20).pack(side=tk.LEFT, padx=10)
    
    def save_config(self):
        """Salva la configurazione CALMET"""
        config_data = {
            'start_date': self.start_date.get(),
            'end_date': self.end_date.get(),
            'month_calmet': self.month_calmet.get(),
            'month_calpuff': self.month_calpuff.get(),
            'number_of_day': self.number_of_day.get(),
            'wrf_path': self.wrf_path.get(),
            'calmet_output': self.calmet_output.get(),
            'calmet_data': self.calmet_data.get(),
            'calpuff_data': self.calpuff_data.get(),
            'calpost_data': self.calpost_data.get(),
            'link_wrf': self.link_wrf.get(),
            'link_calmet': self.link_calmet.get(),
            'link_calpuff': self.link_calpuff.get(),
            'proj': self.proj.get(),
            'zone': self.zone.get(),
            'origin_lat': self.origin_lat.get(),
            'origin_lon': self.origin_lon.get(),
            'mach_lat1': self.mach_lat1.get(),
            'mach_lat2': self.mach_lat2.get(),
            'feast': self.feast.get(),
            'fnorth': self.fnorth.get(),
            'nx': self.nx.get(),
            'ny': self.ny.get(),
            'dim': self.dim.get(),
            'xori': self.xori.get(),
            'yori': self.yori.get(),
            'nz': self.nz.get(),
            'zface': self.zface.get()
        }
        
        try:
            config_file = self.temp_dir / 'calmet_config.json'
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Successo", f"Configurazione CALMET salvata in:\n{config_file}")
            self.window.destroy()
        
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il salvataggio:\n{str(e)}")
