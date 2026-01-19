"""
Finestra per la definizione del dominio temporale
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime
from pathlib import Path


class TemporalWindow:
    """Finestra per definire il dominio temporale della simulazione"""
    
    # Percorsi predefiniti per i file meteo
    PREDEFINED_PATHS = {
        'Italia': '/project/pmten/WRF_Italia/wrf_out/',  # Da configurare
        'Genova': '/project/pmten/WRF_Italia/wrf_out_ge/'   # Da configurare
    }
    
    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = temp_dir
        self.window = tk.Toplevel(parent)
        self.window.title("Definisci Dominio Temporale")
        self.window.geometry("600x650")
        
        # Variabili
        self.start_date = tk.StringVar()
        self.end_date = tk.StringVar()
        self.meteo_source = tk.StringVar(value="Italia")
        self.custom_path = tk.StringVar()
        
        # Carica configurazione esistente se presente
        self.load_existing_config()
        
        self.setup_ui()
    
    def load_existing_config(self):
        """Carica la configurazione temporale esistente se presente"""
        config_file = self.temp_dir / "temporal_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.start_date.set(config.get('start_date', ''))
                self.end_date.set(config.get('end_date', ''))
                self.meteo_source.set(config.get('meteo_source', 'Italia'))
                self.custom_path.set(config.get('custom_path', ''))
            except Exception as e:
                print(f"Errore durante il caricamento della configurazione temporale: {e}")
    
    def setup_ui(self):
        """Configura l'interfaccia della finestra"""
        # Frame principale
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configura il grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # === TITOLO ===
        title_label = ttk.Label(
            main_frame,
            text="Configurazione Dominio Temporale",
            font=('Arial', 12, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # === SEZIONE DATE ===
        date_frame = ttk.LabelFrame(main_frame, text="Periodo di Simulazione", padding="15")
        date_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        date_frame.columnconfigure(1, weight=1)
        
        # Data inizio
        ttk.Label(date_frame, text="Data Inizio:", font=('Arial', 9, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        
        start_date_frame = ttk.Frame(date_frame)
        start_date_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        self.start_entry = ttk.Entry(start_date_frame, textvariable=self.start_date, width=20)
        self.start_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(start_date_frame, text="(gg/mm/aaaa)", foreground='gray').pack(side=tk.LEFT)
        
        ttk.Button(
            start_date_frame,
            text="📅",
            command=lambda: self.open_calendar('start'),
            width=3
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Data fine
        ttk.Label(date_frame, text="Data Fine:", font=('Arial', 9, 'bold')).grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        
        end_date_frame = ttk.Frame(date_frame)
        end_date_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        self.end_entry = ttk.Entry(end_date_frame, textvariable=self.end_date, width=20)
        self.end_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(end_date_frame, text="(gg/mm/aaaa)", foreground='gray').pack(side=tk.LEFT)
        
        ttk.Button(
            end_date_frame,
            text="📅",
            command=lambda: self.open_calendar('end'),
            width=3
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # === SEZIONE FILE METEO ===
        meteo_frame = ttk.LabelFrame(main_frame, text="Sorgente File Meteorologici", padding="15")
        meteo_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        meteo_frame.columnconfigure(0, weight=1)
        
        # Radio buttons per la selezione
        ttk.Radiobutton(
            meteo_frame,
            text="Italia",
            variable=self.meteo_source,
            value="Italia",
            command=self.on_source_change
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.italia_path_label = ttk.Label(
            meteo_frame,
            text=f"  → {self.PREDEFINED_PATHS['Italia']}",
            foreground='gray',
            font=('Arial', 8)
        )
        self.italia_path_label.grid(row=1, column=0, sticky=tk.W, padx=(20, 0))
        
        ttk.Radiobutton(
            meteo_frame,
            text="Genova",
            variable=self.meteo_source,
            value="Genova",
            command=self.on_source_change
        ).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.genova_path_label = ttk.Label(
            meteo_frame,
            text=f"  → {self.PREDEFINED_PATHS['Genova']}",
            foreground='gray',
            font=('Arial', 8)
        )
        self.genova_path_label.grid(row=3, column=0, sticky=tk.W, padx=(20, 0))
        
        ttk.Radiobutton(
            meteo_frame,
            text="Custom",
            variable=self.meteo_source,
            value="Custom",
            command=self.on_source_change
        ).grid(row=4, column=0, sticky=tk.W, pady=5)
        
        # Frame per percorso custom
        custom_frame = ttk.Frame(meteo_frame)
        custom_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), padx=(20, 0), pady=5)
        custom_frame.columnconfigure(0, weight=1)
        
        self.custom_entry = ttk.Entry(custom_frame, textvariable=self.custom_path)
        self.custom_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.browse_btn = ttk.Button(
            custom_frame,
            text="Sfoglia...",
            command=self.browse_custom_path
        )
        self.browse_btn.grid(row=0, column=1)
        
        # Inizializza lo stato dei controlli
        self.on_source_change()
        
        # === INFO BOX ===
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        info_text = (
            "ℹ️ Nota: I percorsi 'Italia' e 'Genova' utilizzano directory predefinite.\n"
            "Seleziona 'Custom' per specificare un percorso personalizzato."
        )
        
        info_label = ttk.Label(
            info_frame,
            text=info_text,
            foreground='#0066cc',
            font=('Arial', 8),
            wraplength=550,
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W)
        
        # === BOTTONI AZIONE ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame,
            text="Salva",
            command=self.save_temporal_config,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Annulla",
            command=self.window.destroy,
            width=15
        ).pack(side=tk.LEFT, padx=5)
    
    def on_source_change(self):
        """Gestisce il cambio di sorgente meteo"""
        if self.meteo_source.get() == "Custom":
            self.custom_entry.config(state='normal')
            self.browse_btn.config(state='normal')
        else:
            self.custom_entry.config(state='disabled')
            self.browse_btn.config(state='disabled')
    
    def browse_custom_path(self):
        """Apre un dialogo per selezionare un percorso custom"""
        path = filedialog.askdirectory(
            parent=self.window,
            title="Seleziona la directory dei file meteorologici"
        )
        if path:
            self.custom_path.set(path)
    
    def open_calendar(self, date_type):
        """Apre un calendario per selezionare una data"""
        # Finestra calendario semplice
        cal_window = tk.Toplevel(self.window)
        cal_window.title(f"Seleziona Data {'Inizio' if date_type == 'start' else 'Fine'}")
        cal_window.geometry("400x200")
        cal_window.transient(self.window)
        cal_window.grab_set()
        
        frame = ttk.Frame(cal_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Inserisci la data:", font=('Arial', 10)).pack(pady=10)
        
        # Frame per giorno, mese, anno
        date_frame = ttk.Frame(frame)
        date_frame.pack(pady=10)
        
        # Giorno
        ttk.Label(date_frame, text="Giorno:").grid(row=0, column=0, padx=5)
        day_var = tk.StringVar(value="01")
        day_spin = ttk.Spinbox(date_frame, from_=1, to=31, textvariable=day_var, width=5)
        day_spin.grid(row=0, column=1, padx=5)
        
        # Mese
        ttk.Label(date_frame, text="Mese:").grid(row=0, column=2, padx=5)
        month_var = tk.StringVar(value="01")
        month_spin = ttk.Spinbox(date_frame, from_=1, to=12, textvariable=month_var, width=5)
        month_spin.grid(row=0, column=3, padx=5)
        
        # Anno
        ttk.Label(date_frame, text="Anno:").grid(row=0, column=4, padx=5)
        year_var = tk.StringVar(value="2026")
        year_spin = ttk.Spinbox(date_frame, from_=2000, to=2100, textvariable=year_var, width=7)
        year_spin.grid(row=0, column=5, padx=5)
        
        def apply_date():
            day = day_var.get().zfill(2)
            month = month_var.get().zfill(2)
            year = year_var.get()
            date_str = f"{day}/{month}/{year}"
            
            if date_type == 'start':
                self.start_date.set(date_str)
            else:
                self.end_date.set(date_str)
            
            cal_window.destroy()
        
        ttk.Button(frame, text="OK", command=apply_date).pack(pady=10)
    
    def validate_dates(self):
        """Valida le date inserite"""
        start = self.start_date.get().strip()
        end = self.end_date.get().strip()
        
        if not start or not end:
            messagebox.showerror(
                "Errore",
                "Inserisci sia la data di inizio che quella di fine!",
                parent=self.window
            )
            return False
        
        # Verifica formato date
        try:
            start_dt = datetime.strptime(start, "%d/%m/%Y")
            end_dt = datetime.strptime(end, "%d/%m/%Y")
            
            if start_dt >= end_dt:
                messagebox.showerror(
                    "Errore",
                    "La data di inizio deve essere precedente alla data di fine!",
                    parent=self.window
                )
                return False
            
        except ValueError:
            messagebox.showerror(
                "Errore",
                "Formato data non valido! Usa il formato gg/mm/aaaa",
                parent=self.window
            )
            return False
        
        return True
    
    def validate_meteo_path(self):
        """Valida il percorso dei file meteo"""
        source = self.meteo_source.get()
        
        if source == "Custom":
            path = self.custom_path.get().strip()
            if not path:
                messagebox.showerror(
                    "Errore",
                    "Specifica un percorso per i file meteorologici!",
                    parent=self.window
                )
                return False
        
        return True
    
    def save_temporal_config(self):
        """Salva la configurazione temporale"""
        # Valida i dati
        if not self.validate_dates():
            return
        
        if not self.validate_meteo_path():
            return
        
        # Determina il percorso da salvare
        source = self.meteo_source.get()
        if source in self.PREDEFINED_PATHS:
            meteo_path = self.PREDEFINED_PATHS[source]
        else:
            meteo_path = self.custom_path.get().strip()
        
        # Crea la configurazione
        config = {
            'start_date': self.start_date.get().strip(),
            'end_date': self.end_date.get().strip(),
            'meteo_source': source,
            'meteo_path': meteo_path,
            'custom_path': self.custom_path.get().strip() if source == "Custom" else ""
        }
        
        # Salva nel file
        config_file = self.temp_dir / "temporal_config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo(
                "Successo",
                "Configurazione temporale salvata con successo!",
                parent=self.window
            )
            self.window.destroy()
        
        except Exception as e:
            messagebox.showerror(
                "Errore",
                f"Errore durante il salvataggio:\n{str(e)}",
                parent=self.window
            )
    
    @classmethod
    def update_predefined_paths(cls, italia_path=None, genova_path=None):
        """Metodo per aggiornare i percorsi predefiniti
        
        Args:
            italia_path: Nuovo percorso per Italia
            genova_path: Nuovo percorso per Genova
        """
        if italia_path:
            cls.PREDEFINED_PATHS['Italia'] = italia_path
        if genova_path:
            cls.PREDEFINED_PATHS['Genova'] = genova_path
