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
        self.window.geometry("900x750")
        
        # Variabili di configurazione base
        self.num_periods = tk.IntVar(value=24)
        self.ioutu = tk.IntVar(value=1)
        self.iprtu = tk.IntVar(value=3)
        
        # Emissioni puntuali
        self.npt1 = tk.IntVar(value=0)
        self.iptu = tk.IntVar(value=1)
        self.npt2 = tk.IntVar(value=0)
        
        # Emissioni areali
        self.nar1 = tk.IntVar(value=0)
        self.iaru = tk.IntVar(value=1)
        self.nar2 = tk.IntVar(value=0)
        
        # Emissioni volumetriche
        self.nvl1 = tk.IntVar(value=0)
        self.ivlu = tk.IntVar(value=1)
        self.nvl2 = tk.IntVar(value=0)
        
        # Emissioni flare
        self.nfl2 = tk.IntVar(value=0)
        
        # Emissioni stradali
        self.nrd1 = tk.IntVar(value=0)
        self.irdu = tk.IntVar(value=1)
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
        
        self.load_existing_config()
        self.setup_ui()
    
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
                self.iprtu.set(data.get('iprtu', 3))
                
                # Point emissions
                self.npt1.set(data.get('npt1', 0))
                self.iptu.set(data.get('iptu', 1))
                self.npt2.set(data.get('npt2', 0))
                
                # Area emissions
                self.nar1.set(data.get('nar1', 0))
                self.iaru.set(data.get('iaru', 1))
                self.nar2.set(data.get('nar2', 0))
                
                # Volume emissions
                self.nvl1.set(data.get('nvl1', 0))
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
        ttk.Combobox(base_frame, textvariable=self.ioutu, 
                    values=[1, 2, 3], state='readonly', width=13).grid(row=0, column=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(base_frame, text="IPRTU (Precisione):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(base_frame, textvariable=self.iprtu, 
                    values=[1, 2, 3, 4, 5, 6, 7, 8], state='readonly', width=13).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        
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
        
        ttk.Label(point_frame, text="NPT1:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(point_frame, textvariable=self.npt1, width=10).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(point_frame, text="IPTU:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Combobox(point_frame, textvariable=self.iptu, values=[1,2,3,4,5,6,7,8,9], 
                    state='readonly', width=8).grid(row=0, column=3, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
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
        
        ttk.Label(area_frame, text="NAR1:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(area_frame, textvariable=self.nar1, width=10).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(area_frame, text="IARU:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Combobox(area_frame, textvariable=self.iaru, values=[1,2,3,4,5,6,7,8,9], 
                    state='readonly', width=8).grid(row=0, column=3, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
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
        
        ttk.Label(volume_frame, text="NVL1:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(volume_frame, textvariable=self.nvl1, width=10).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(volume_frame, text="IVLU:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Combobox(volume_frame, textvariable=self.ivlu, values=[1,2,3,4,5,6,7,8,9], 
                    state='readonly', width=8).grid(row=0, column=3, sticky=(tk.W, tk.E), pady=5, padx=(5, 10))
        
        ttk.Label(volume_frame, text="NVL2 (File Ext):").grid(row=0, column=4, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Entry(volume_frame, textvariable=self.nvl2, width=10).grid(row=0, column=5, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Button(volume_frame, text="⚙️ Configura Sorgenti Volumetriche", 
                  command=self.configure_volume_emissions).grid(row=1, column=0, columnspan=6, pady=10)
        
        # === SEZIONE EMISSIONI FLARE/STRADALI ===
        other_frame = ttk.LabelFrame(scrollable_frame, text="Altre Emissioni", padding="10")
        other_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        other_frame.columnconfigure(1, weight=1)
        other_frame.columnconfigure(3, weight=1)
        row += 1
        
        # Flare
        ttk.Label(other_frame, text="Flare (NFL2):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(other_frame, textvariable=self.nfl2, width=15).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        ttk.Button(other_frame, text="⚙️ Configura Flare", 
                  command=self.configure_flare_emissions, width=20).grid(row=0, column=2, columnspan=2, pady=5, padx=10)
        
        # Road
        ttk.Label(other_frame, text="Strade (NRD1):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(other_frame, textvariable=self.nrd1, width=10).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))
        ttk.Label(other_frame, text="IRDU:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Combobox(other_frame, textvariable=self.irdu, values=[1,2,3,4,5,6,7,8,9], 
                    state='readonly', width=8).grid(row=1, column=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(other_frame, text="NRD2 (File Ext):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(other_frame, textvariable=self.nrd2, width=15).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 15))
        ttk.Button(other_frame, text="⚙️ Configura Sorgenti Stradali", 
                  command=self.configure_road_emissions, width=20).grid(row=2, column=2, columnspan=2, pady=5, padx=10)
        
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
        ttk.Combobox(line_frame, textvariable=self.ilnu, values=[1,2,3,4,5,6,7,8,9], 
                    state='readonly', width=8).grid(row=0, column=5, sticky=(tk.W, tk.E), pady=5, padx=5)
        
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
        ttk.Button(button_frame, text="❌ Annulla", command=self.window.destroy, width=20).pack(side=tk.LEFT, padx=10)
    
    def configure_species(self):
        """Apre finestra per configurare le species"""
        messagebox.showinfo("In Sviluppo", "Funzionalità in fase di sviluppo")
    
    def configure_point_emissions(self):
        """Apre finestra per configurare emissioni puntuali"""
        messagebox.showinfo("In Sviluppo", "Funzionalità in fase di sviluppo")
    
    def configure_area_emissions(self):
        """Apre finestra per configurare emissioni areali"""
        messagebox.showinfo("In Sviluppo", "Funzionalità in fase di sviluppo")
    
    def configure_volume_emissions(self):
        """Apre finestra per configurare emissioni volumetriche"""
        messagebox.showinfo("In Sviluppo", "Funzionalità in fase di sviluppo")
    
    def configure_flare_emissions(self):
        """Apre finestra per configurare emissioni flare"""
        messagebox.showinfo("In Sviluppo", "Funzionalità in fase di sviluppo")
    
    def configure_road_emissions(self):
        """Apre finestra per configurare emissioni stradali"""
        messagebox.showinfo("In Sviluppo", "Funzionalità in fase di sviluppo")
    
    def configure_line_emissions(self):
        """Apre finestra per configurare linee galleggianti"""
        messagebox.showinfo("In Sviluppo", "Funzionalità in fase di sviluppo")
    
    def configure_scaling_factors(self):
        """Apre finestra per configurare scaling factors"""
        messagebox.showinfo("In Sviluppo", "Funzionalità in fase di sviluppo")
    
    def save_config(self):
        """Salva la configurazione CALPUFF"""
        config_data = {
            # Base config
            'num_periods': self.num_periods.get(),
            'ioutu': self.ioutu.get(),
            'iprtu': self.iprtu.get(),
            
            # Point emissions
            'npt1': self.npt1.get(),
            'iptu': self.iptu.get(),
            'npt2': self.npt2.get(),
            
            # Area emissions
            'nar1': self.nar1.get(),
            'iaru': self.iaru.get(),
            'nar2': self.nar2.get(),
            
            # Volume emissions
            'nvl1': self.nvl1.get(),
            'ivlu': self.ivlu.get(),
            'nvl2': self.nvl2.get(),
            
            # Flare emissions
            'nfl2': self.nfl2.get(),
            
            # Road emissions
            'nrd1': self.nrd1.get(),
            'irdu': self.irdu.get(),
            'nrd2': self.nrd2.get(),
            
            # Line emissions
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
            
            # Scaling factors
            'tabella': self.tabella.get()
        }
        
        try:
            config_file = self.temp_dir / 'calpuff_config.json'
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Successo", f"Configurazione CALPUFF salvata in:\n{config_file}")
            self.window.destroy()
        
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il salvataggio:\n{str(e)}")
