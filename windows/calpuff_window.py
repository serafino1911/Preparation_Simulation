"""
Finestra per la configurazione di CALPUFF
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path


class CalpuffWindow:
    """Finestra per configurare i parametri di CALPUFF"""
    
    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = temp_dir
        self.window = tk.Toplevel(parent)
        self.window.title("Configurazione CALPUFF")
        self.window.geometry("800x750")
        
        # Variabili di configurazione base
        self.num_periods = tk.IntVar(value=24)
        self.ioutu = tk.IntVar(value=1)
        self.iprtu = tk.IntVar(value=3)
        
        # Emissioni puntuali
        self.iptu = tk.IntVar(value=1)
        self.npt2 = tk.IntVar(value=0)
        
        # Emissioni areali
        self.iaru = tk.IntVar(value=1)
        self.nar2 = tk.IntVar(value=0)
        
        # Emissioni volumetriche
        self.ivlu = tk.IntVar(value=1)
        self.nvl2 = tk.IntVar(value=0)
        
        # Emissioni flare
        self.nfl2 = tk.IntVar(value=0)
        
        # Emissioni stradali
        self.nrd1 = tk.IntVar(value=0)
        self.nrd2 = tk.IntVar(value=0)
        
        # Emissioni linee galleggianti
        self.nln2 = tk.IntVar(value=0)
        self.nlines = tk.IntVar(value=0)
        self.ilnu = tk.IntVar(value=1)
        self.mxnseg = tk.IntVar(value=2)
        self.nlrise = tk.IntVar(value=1)
        self.xl = tk.DoubleVar(value=20.0)
        self.hbl = tk.DoubleVar(value=30.0)
        self.wbl = tk.DoubleVar(value=20.0)
        self.dxl = tk.DoubleVar(value=10.0)
        self.fprimel = tk.DoubleVar(value=10000.0)
        self.wml = tk.DoubleVar(value=10.0)
        
        # Scaling factors
        self.tabella = tk.BooleanVar(value=True)

        # Unita di misura (solo visualizzazione UI)
        self.units_map = self._load_units_map()
        self.ioutu_display = tk.StringVar()
        self.iprtu_display = tk.StringVar()
        self.iptu_display = tk.StringVar()
        self.iaru_display = tk.StringVar()
        self.ivlu_display = tk.StringVar()
        self.ilnu_display = tk.StringVar()
        
        self.load_existing_config()
        self._sync_unit_displays_from_codes()
        self.setup_ui()

    def _load_units_map(self):
        """Carica le definizioni delle unità di misura da un dizionario"""
        units = {
            'IOUTU': {'1': 'g/m3 (conc) or g/m2/s (dep)', '2': 'odour (conc)', '3': 'Bq/m3 (conc) or Bq/m2/s (dep)'},
            'IPRTU': {'1': 'g/m3 (conc) or g/m2/s (dep)', '2': 'mg/m3 (conc) or mg/m2/s (dep)', '3': 'ug/m3 (conc) or ug/m2/s (dep)', '4': 'ng/m3 (conc) or ng/m2/s (dep)', '5': 'odour (conc)', '6': 'TBq/m3 (conc) or TBq/m2/s (dep)', '7': 'GBq/m3 (conc) or GBq/m2/s (dep)', '8': 'Bq/m3 (conc) or Bq/m2/s (dep)'},
            'IPTU': {'1': 'g/s', '2': 'kg/hr', '3': 'lb/hr', '4': 'tons/yr', '5': 'Odour Unit * m3/s', '6': 'Odour Unit * m3/min', '7': 'metric tons/yr', '8': 'Bq/s', '9': 'GBq/yr'},
            'IARU': {'1': 'g/m2/s', '2': 'kg/m2/hr', '3': 'lb/m2/hr', '4': 'tons/m2/yr', '5': 'Odour Unit * m/s', '6': 'Odour Unit * m/min', '7': 'metric tons/m2/yr', '8': 'Bq/m2/s', '9': 'GBq/m2/yr'},
            'IVLU': {'1': 'g/s', '2': 'kg/hr', '3': 'lb/hr', '4': 'tons/yr', '5': 'Odour Unit * m3/s', '6': 'Odour Unit * m3/min', '7': 'metric tons/yr', '8': 'Bq/s', '9': 'GBq/yr'},
            'ILNU': {'1': 'g/s', '2': 'kg/hr', '3': 'lb/hr', '4': 'tons/yr', '5': 'Odour Unit * m3/s', '6': 'Odour Unit * m3/min', '7': 'metric tons/yr', '8': 'Bq/s', '9': 'GBq/yr'},
        }

        return units

    def _unit_values(self, key, fallback_codes):
        """Ritorna i valori testuali del combobox nel formato 'codice - descrizione'."""
        section = self.units_map.get(key, {})
        values = []

        for code in fallback_codes:
            label = section.get(str(code))
            if label:
                values.append(f"{code} - {label}")
            else:
                values.append(str(code))

        # Aggiunge eventuali codici extra presenti nel JSON ma non nel fallback
        for code_text, label in sorted(section.items(), key=lambda item: int(item[0])):
            try:
                code = int(code_text)
            except Exception:
                continue
            if code not in fallback_codes:
                values.append(f"{code} - {label}")

        return values

    def _format_unit_display(self, key, code):
        section = self.units_map.get(key, {})
        label = section.get(str(code))
        if label:
            return f"{code} - {label}"
        return str(code)

    def _sync_unit_displays_from_codes(self):
        """Allinea il testo dei combobox ai valori numerici correnti."""
        self.ioutu_display.set(self._format_unit_display('IOUTU', self.ioutu.get()))
        self.iprtu_display.set(self._format_unit_display('IPRTU', self.iprtu.get()))
        self.iptu_display.set(self._format_unit_display('IPTU', self.iptu.get()))
        self.iaru_display.set(self._format_unit_display('IARU', self.iaru.get()))
        self.ivlu_display.set(self._format_unit_display('IVLU', self.ivlu.get()))
        self.ilnu_display.set(self._format_unit_display('ILNU', self.ilnu.get()))

    def _on_unit_selected(self, key, code_var, display_var):
        """Converte la scelta testuale del combobox nel codice numerico persistente."""
        selected = display_var.get().strip()
        code_text = selected.split(' - ', 1)[0].strip()
        try:
            code_var.set(int(code_text))
        except Exception:
            # Ripristina una visualizzazione coerente se il parsing fallisce
            display_var.set(self._format_unit_display(key, code_var.get()))
    
    def load_existing_config(self):
        """Carica la configurazione esistente se presente"""
        config_file = self.temp_dir / 'calpuff_config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Base config
                self.num_periods.set(data.get('num_periods', 24))
                self.ioutu.set(data.get('ioutu', 1))
                self.iprtu.set(data.get('iprtu', 1))
                
                # Point emissions
                self.iptu.set(data.get('iptu', 1))
                self.npt2.set(data.get('npt2', 0))
                
                # Area emissions
                self.iaru.set(data.get('iaru', 1))
                self.nar2.set(data.get('nar2', 0))
                
                # Volume emissions
                self.ivlu.set(data.get('ivlu', 1))
                self.nvl2.set(data.get('nvl2', 0))
                
                # Flare emissions
                self.nfl2.set(data.get('nfl2', 0))
                
                # Road emissions
                self.nrd1.set(data.get('nrd1', 0))
                self.irdu.set(data.get('irdu', 1))
                self.nrd2.set(data.get('nrd2', 0))
                
                # Line emissions
                self.nln2.set(data.get('nln2', 0))
                self.nlines.set(data.get('nlines', 0))
                self.ilnu.set(data.get('ilnu', 1))
                self.mxnseg.set(data.get('mxnseg', 2))
                self.nlrise.set(data.get('nlrise', 1))
                self.xl.set(data.get('xl', 20.0))
                self.hbl.set(data.get('hbl', 30.0))
                self.wbl.set(data.get('wbl', 20.0))
                self.dxl.set(data.get('dxl', 10.0))
                self.fprimel.set(data.get('fprimel', 10000.0))
                self.wml.set(data.get('wml', 10.0))
                
                # Scaling factors
                self.tabella.set(data.get('tabella', True))
                
            except Exception as e:
                print(f"Errore nel caricamento della configurazione CALPUFF: {e}")
    
    def setup_ui(self):
        """Configura l'interfaccia utente"""
        # Frame principale con scrollbar
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Canvas e scrollbar
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
        
        # === SEZIONE CONFIGURAZIONE BASE ===
        base_frame = ttk.LabelFrame(scrollable_frame, text="Configurazione Base", padding="10")
        base_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        base_frame.columnconfigure(1, weight=1)
        base_frame.columnconfigure(3, weight=1)
        row += 1
        
        ttk.Label(base_frame, text="Periodi Output (NRESPD):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(base_frame, textvariable=self.num_periods, width=15).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        
        ttk.Label(base_frame, text="IOUTU (Unità Output):").grid(row=0, column=2, sticky=tk.W, pady=5)
        ioutu_combo = ttk.Combobox(
            base_frame,
            textvariable=self.ioutu_display,
            values=self._unit_values('IOUTU', [1, 2, 3]),
            state='readonly',
            width=30
        )
        ioutu_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        ioutu_combo.bind('<<ComboboxSelected>>', lambda _e: self._on_unit_selected('IOUTU', self.ioutu, self.ioutu_display))
        
        ttk.Label(base_frame, text="IPRTU (Altre unità Output):").grid(row=1, column=0, sticky=tk.W, pady=5)
        iprtu_combo = ttk.Combobox(
            base_frame,
            textvariable=self.iprtu_display,
            values=self._unit_values('IPRTU', [1, 2, 3, 4, 5, 6, 7, 8]),
            state='readonly',
            width=30
        )
        iprtu_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        iprtu_combo.bind('<<ComboboxSelected>>', lambda _e: self._on_unit_selected('IPRTU', self.iprtu, self.iprtu_display))
        
        # === SEZIONE SPECIES ===
        species_frame = ttk.LabelFrame(scrollable_frame, text="Configurazione Species", padding="10")
        species_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        species_frame.columnconfigure(0, weight=1)
        row += 1
        
        ttk.Button(species_frame, text="🧪 Configura Species", 
                  command=self.configure_species, width=30).grid(row=0, column=0, pady=10)
        ttk.Label(species_frame, text="(NOX, PM10, deposizioni, ecc.)", 
                 font=('Arial', 8, 'italic')).grid(row=1, column=0, pady=(0, 5))
        
        # === SEZIONE EMISSIONI PUNTUALI ===
        point_frame = ttk.LabelFrame(scrollable_frame, text="Emissioni Puntuali", padding="10")
        point_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        point_frame.columnconfigure(1, weight=1)
        point_frame.columnconfigure(3, weight=1)
        point_frame.columnconfigure(5, weight=1)
        row += 1
        
        ttk.Label(point_frame, text="IPTU:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        iptu_combo = ttk.Combobox(
            point_frame,
            textvariable=self.iptu_display,
            values=self._unit_values('IPTU', [1, 2, 3, 4, 5, 6, 7, 8, 9]),
            state='readonly',
            width=25
        )
        iptu_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        iptu_combo.bind('<<ComboboxSelected>>', lambda _e: self._on_unit_selected('IPTU', self.iptu, self.iptu_display))
        
        ttk.Label(point_frame, text="NPT2 (File Ext):").grid(row=0, column=4, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(point_frame, textvariable=self.npt2, width=10).grid(row=0, column=5, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Button(point_frame, text="⚙️ Configura Sorgenti Puntuali", 
                  command=self.configure_point_emissions).grid(row=1, column=0, columnspan=6, pady=10)
        
        # === SEZIONE EMISSIONI AREALI ===
        area_frame = ttk.LabelFrame(scrollable_frame, text="Emissioni Areali", padding="10")
        area_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        area_frame.columnconfigure(1, weight=1)
        area_frame.columnconfigure(3, weight=1)
        area_frame.columnconfigure(5, weight=1)
        row += 1
        
        ttk.Label(area_frame, text="IARU:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        iaru_combo = ttk.Combobox(
            area_frame,
            textvariable=self.iaru_display,
            values=self._unit_values('IARU', [1, 2, 3, 4, 5, 6, 7, 8, 9]),
            state='readonly',
            width=25
        )
        iaru_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        iaru_combo.bind('<<ComboboxSelected>>', lambda _e: self._on_unit_selected('IARU', self.iaru, self.iaru_display))
        
        ttk.Label(area_frame, text="NAR2 (File Ext):").grid(row=0, column=4, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(area_frame, textvariable=self.nar2, width=10).grid(row=0, column=5, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Button(area_frame, text="⚙️ Configura Sorgenti Areali", 
                  command=self.configure_area_emissions).grid(row=1, column=0, columnspan=6, pady=10)
        
        # === SEZIONE EMISSIONI VOLUMETRICHE ===
        volume_frame = ttk.LabelFrame(scrollable_frame, text="Emissioni Volumetriche", padding="10")
        volume_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        volume_frame.columnconfigure(1, weight=1)
        volume_frame.columnconfigure(3, weight=1)
        volume_frame.columnconfigure(5, weight=1)
        row += 1
        
        ttk.Label(volume_frame, text="IVLU:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        ivlu_combo = ttk.Combobox(
            volume_frame,
            textvariable=self.ivlu_display,
            values=self._unit_values('IVLU', [1, 2, 3, 4, 5, 6, 7, 8, 9]),
            state='readonly',
            width=25
        )
        ivlu_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        ivlu_combo.bind('<<ComboboxSelected>>', lambda _e: self._on_unit_selected('IVLU', self.ivlu, self.ivlu_display))
        
        ttk.Label(volume_frame, text="NVL2 (File Ext):").grid(row=0, column=4, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(volume_frame, textvariable=self.nvl2, width=10).grid(row=0, column=5, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Button(volume_frame, text="⚙️ Configura Sorgenti Volumetriche", 
                  command=self.configure_volume_emissions).grid(row=1, column=0, columnspan=6, pady=10)
        
        # === SEZIONE EMISSIONI FLARE ===
        flare_frame = ttk.LabelFrame(scrollable_frame, text="Emissioni Flare", padding="10")
        flare_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        flare_frame.columnconfigure(1, weight=1)
        row += 1
        
        ttk.Label(flare_frame, text="NFL2 (File Ext):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(flare_frame, textvariable=self.nfl2, width=15).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        
        ttk.Button(flare_frame, text="⚙️ Configura Sorgenti Flare", 
                  command=self.configure_flare_emissions).grid(row=1, column=0, columnspan=2, pady=10)
        
        # === SEZIONE EMISSIONI STRADALI ===
        road_frame = ttk.LabelFrame(scrollable_frame, text="Emissioni Stradali", padding="10")
        road_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        road_frame.columnconfigure(1, weight=1)
        road_frame.columnconfigure(3, weight=1)
        road_frame.columnconfigure(5, weight=1)
        row += 1
        
        ttk.Label(road_frame, text="NRD1:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(road_frame, textvariable=self.nrd1, width=10).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        
        ttk.Label(road_frame, text="NRD2 (File Ext):").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(road_frame, textvariable=self.nrd2, width=10).grid(row=0, column=5, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Button(road_frame, text="⚙️ Configura Sorgenti Stradali", 
                  command=self.configure_road_emissions).grid(row=1, column=0, columnspan=6, pady=10)
        
        # === SEZIONE LINEE GALLEGGIANTI ===
        line_frame = ttk.LabelFrame(scrollable_frame, text="Emissioni Linee Galleggianti (Buoyant Line)", padding="10")
        line_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        line_frame.columnconfigure(1, weight=1)
        line_frame.columnconfigure(3, weight=1)
        line_frame.columnconfigure(5, weight=1)
        row += 1
        
        ttk.Label(line_frame, text="NLN2 (File Ext):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(line_frame, textvariable=self.nln2, width=10).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(line_frame, text="NLINES:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(line_frame, textvariable=self.nlines, width=10).grid(row=0, column=3, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(line_frame, text="ILNU:").grid(row=0, column=4, sticky=tk.W, pady=5, padx=(10, 0))
        ilnu_combo = ttk.Combobox(
            line_frame,
            textvariable=self.ilnu_display,
            values=self._unit_values('ILNU', [1, 2, 3, 4, 5, 6, 7, 8, 9]),
            state='readonly',
            width=25
        )
        ilnu_combo.grid(row=0, column=5, sticky=(tk.W, tk.E), pady=5, padx=5)
        ilnu_combo.bind('<<ComboboxSelected>>', lambda _e: self._on_unit_selected('ILNU', self.ilnu, self.ilnu_display))
        
        ttk.Label(line_frame, text="MXNSEG:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(line_frame, textvariable=self.mxnseg, width=10).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(line_frame, text="NLRISE:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(line_frame, textvariable=self.nlrise, width=10).grid(row=1, column=3, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(line_frame, text="XL:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(line_frame, textvariable=self.xl, width=10).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(line_frame, text="HBL:").grid(row=2, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(line_frame, textvariable=self.hbl, width=10).grid(row=2, column=3, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(line_frame, text="WBL:").grid(row=2, column=4, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(line_frame, textvariable=self.wbl, width=10).grid(row=2, column=5, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(line_frame, text="DXL:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(line_frame, textvariable=self.dxl, width=10).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(line_frame, text="FPRIMEL:").grid(row=3, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(line_frame, textvariable=self.fprimel, width=10).grid(row=3, column=3, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(line_frame, text="WML:").grid(row=3, column=4, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(line_frame, textvariable=self.wml, width=10).grid(row=3, column=5, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Button(line_frame, text="⚙️ Configura Linee Galleggianti", 
                  command=self.configure_line_emissions).grid(row=4, column=0, columnspan=6, pady=10)
        
        # === SEZIONE SCALING FACTORS ===
        scaling_frame = ttk.LabelFrame(scrollable_frame, text="Fattori di Scala", padding="10")
        scaling_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        scaling_frame.columnconfigure(0, weight=1)
        row += 1
        
        ttk.Checkbutton(scaling_frame, text="Usa Tabelle di Scaling", 
                       variable=self.tabella).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Button(scaling_frame, text="📊 Configura Scaling Factors", 
                  command=self.configure_scaling_factors, width=30).grid(row=1, column=0, pady=10)
        ttk.Label(scaling_frame, text="(HOUR24, DAY7, MONTH12, ecc.)", 
                 font=('Arial', 8, 'italic')).grid(row=2, column=0, pady=(0, 5))
        
        # === BOTTONI AZIONE ===
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=row, column=0, pady=20)
        row += 1
        
        ttk.Button(button_frame, text="💾 Salva", command=self.save_config, width=20).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="🛠️ Create INP", command=self.create_inp, width=20).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="❌ Annulla", command=self.window.destroy, width=20).pack(side=tk.LEFT, padx=10)
    
    def configure_species(self):
        """Apre finestra per configurare le species"""
        from windows.species_window import SpeciesWindow
        SpeciesWindow(self.window, self.temp_dir)
    
    def configure_point_emissions(self):
        """Apre finestra per configurare emissioni puntuali"""
        from windows.point_sources_window import PointSourcesWindow
        PointSourcesWindow(self.window, self.temp_dir)
    
    def configure_area_emissions(self):
        """Apre finestra per configurare emissioni areali"""
        from windows.area_sources_window import AreaSourcesWindow
        AreaSourcesWindow(self.window, self.temp_dir)
    
    def configure_volume_emissions(self):
        """Apre finestra per configurare emissioni volumetriche"""
        from windows.volume_sources_window import VolumeSourcesWindow
        VolumeSourcesWindow(self.window, self.temp_dir)
    
    def configure_flare_emissions(self):
        """Apre finestra per configurare emissioni flare"""
        from windows.flare_sources_window import FlareSourcesWindow
        FlareSourcesWindow(self.window, self.temp_dir)
    
    def configure_road_emissions(self):
        """Apre finestra per configurare emissioni stradali"""
        from windows.road_sources_window import RoadSourcesWindow
        RoadSourcesWindow(self.window, self.temp_dir)
    
    def configure_line_emissions(self):
        """Apre finestra per configurare linee galleggianti"""
        from windows.line_sources_window import LineSourcesWindow
        LineSourcesWindow(self.window, self.temp_dir)
    
    def configure_scaling_factors(self):
        """Apre finestra per configurare scaling factors"""
        from windows.scaling_factors_window import ScalingFactorsWindow
        ScalingFactorsWindow(self.window, self.temp_dir)

    def create_inp(self):
        """Crea i file .inp CALPUFF e CALPOST giornalieri in CALPUFF_INP e CALPOST_INP"""
        try:
            self._save_current_config(show_message=False, close_window=False)

            from service.calpuff_inp_writer import generate_daily_inp_files
            from service.calpost_inp_writer import generate_daily_calpost_files

            workspace_root = self.temp_dir.parent
            calpuff_output_dir = workspace_root / 'CALPUFF_INP'
            calpost_output_dir = workspace_root / 'CALPOST_INP'

            calpuff_config_path = self.temp_dir / 'calpuff_config.json'
            temporal_config_path = self.temp_dir / 'temporal_config.json'
            calmet_config_path = self.temp_dir / 'calmet_config.json'
            domain_config_path = self.temp_dir / 'domain_config.json'
            landuse_config_path = self.temp_dir / 'landuse_config.json'

            required_configs = [
                calpuff_config_path,
                temporal_config_path,
                calmet_config_path,
                domain_config_path,
                landuse_config_path,
            ]
            missing_configs = [path.name for path in required_configs if not path.exists()]
            if missing_configs:
                missing_text = ', '.join(missing_configs)
                raise FileNotFoundError(f'Configurazioni mancanti: {missing_text}')

            # Genera file CALPUFF
            calpuff_files = generate_daily_inp_files(
                calpuff_config_path=calpuff_config_path,
                temporal_config_path=temporal_config_path,
                calmet_config_path=calmet_config_path,
                domain_config_path=domain_config_path,
                landuse_config_path=landuse_config_path,
                output_dir=calpuff_output_dir,
            )

            # Genera file CALPOST
            calpost_files = generate_daily_calpost_files(
                calpuff_config_path=calpuff_config_path,
                temporal_config_path=temporal_config_path,
                calmet_config_path=calmet_config_path,
                output_dir=calpost_output_dir,
            )

            messagebox.showinfo(
                "Successo",
                f"Creati {len(calpuff_files)} file CALPUFF .inp in:\n{calpuff_output_dir}\n\n"
                f"Creati {len(calpost_files)} file CALPOST .inp in:\n{calpost_output_dir}"
            )
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la creazione degli INP:\n{str(e)}")

    def _save_current_config(self, show_message=True, close_window=True):
        """Salva la configurazione CALPUFF corrente"""
        config_file = self.temp_dir / 'calpuff_config.json'

        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        else:
            config_data = {}

        config_data.update({
            'num_periods': self.num_periods.get(),
            'ioutu': self.ioutu.get(),
            'iprtu': self.iprtu.get(),
            'iptu': self.iptu.get(),
            'npt2': self.npt2.get(),
            'iaru': self.iaru.get(),
            'nar2': self.nar2.get(),
            'ivlu': self.ivlu.get(),
            'nvl2': self.nvl2.get(),
            'nfl2': self.nfl2.get(),
            'nrd1': self.nrd1.get(),
            'nrd2': self.nrd2.get(),
            'nln2': self.nln2.get(),
            'nlines': self.nlines.get(),
            'ilnu': self.ilnu.get(),
            'mxnseg': self.mxnseg.get(),
            'nlrise': self.nlrise.get(),
            'xl': self.xl.get(),
            'hbl': self.hbl.get(),
            'wbl': self.wbl.get(),
            'dxl': self.dxl.get(),
            'fprimel': self.fprimel.get(),
            'wml': self.wml.get(),
            'tabella': self.tabella.get()
        })

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)

        if show_message:
            messagebox.showinfo("Successo", f"Configurazione CALPUFF salvata in:\n{config_file}")
        if close_window:
            self.window.destroy()
    
    def save_config(self):
        """Salva la configurazione CALPUFF"""
        try:
            self._save_current_config(show_message=True, close_window=True)
        
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il salvataggio:\n{str(e)}")
