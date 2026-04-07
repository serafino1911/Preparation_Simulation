"""
Finestra per la configurazione dei Scaling Factors in CALPUFF
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from pathlib import Path


class ScalingFactorsWindow:
    """Finestra per gestire i fattori di scala temporali"""
    
    FACTOR_TYPES = {
        'CONSTANT1': 'Costante',
        'MONTH12': 'Mensile (12 valori)',
        'DAY7': 'Settimanale (7 giorni)',
        'HOUR24': 'Orario (24 ore)',
        'HOUR24_DAY7': 'Orario x Giorno (24x7)',
        'HOUR24_MONTH12': 'Orario x Mese (24x12)',
        'WSP6': 'Velocità vento (6 classi)',
        'WSP6_PGCLASS6': 'Velocità vento x Stabilità (6x6)',
        'TEMPERATURE12': 'Temperatura (12 classi)'
    }
    
    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = temp_dir
        self.window = tk.Toplevel(parent)
        self.window.title("Configurazione Scaling Factors")
        self.window.geometry("1000x700")
        
        # Dati dei fattori di scala
        self.scaling_factors = []  # Lista di definizioni (TABELLA_FINALE_HD)
        self.scaling_data = {}  # Dizionario con i dati per ogni tipo
        
        # Associazioni sorgenti-inquinanti per tipo di sorgente
        self.scal_fact_punt_sor = []  # Point sources
        self.scal_fact_area_sor = []  # Area sources
        self.scal_fact_vol_sor = []   # Volume sources
        self.scal_fact_road_sor = []  # Road sources
        self.scal_fact_line_sor = []  # Line sources
        
        self.selected_factor_index = None
        
        self.load_scaling_factors()
        self.setup_ui()
        self.refresh_factors_list()
    
    def load_scaling_factors(self):
        """Carica i fattori di scala dalla configurazione"""
        config_file = self.temp_dir / 'calpuff_config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.scaling_factors = data.get('scaling_factors', [])
                    self.scaling_data = data.get('scaling_data', {})
                    # Carica le associazioni sorgenti-inquinanti
                    self.scal_fact_punt_sor = data.get('scal_fact_punt_sor', [])
                    self.scal_fact_area_sor = data.get('scal_fact_area_sor', [])
                    self.scal_fact_vol_sor = data.get('scal_fact_vol_sor', [])
                    self.scal_fact_road_sor = data.get('scal_fact_road_sor', [])
                    self.scal_fact_line_sor = data.get('scal_fact_line_sor', [])
            except Exception as e:
                print(f"Errore caricamento scaling factors: {e}")
    
    def setup_ui(self):
        """Configura l'interfaccia utente"""
        # Frame principale con scrollbar
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(1, weight=1)
        
        # === COLONNA SINISTRA: Lista Fattori ===
        left_frame = ttk.LabelFrame(main_frame, text="Fattori di Scala Definiti", padding="10")
        left_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        # Listbox con scrollbar
        list_scroll = ttk.Scrollbar(left_frame)
        list_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.factors_listbox = tk.Listbox(left_frame, yscrollcommand=list_scroll.set, font=('Arial', 10))
        self.factors_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_scroll.config(command=self.factors_listbox.yview)
        
        self.factors_listbox.bind('<<ListboxSelect>>', self.on_factor_select)
        
        # Bottoni gestione
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Button(btn_frame, text="➕ Nuovo", command=self.add_new_factor, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ Elimina", command=self.delete_factor, width=12).pack(side=tk.LEFT, padx=2)
        
        # === COLONNA DESTRA: Editor Valori ===
        right_frame = ttk.LabelFrame(main_frame, text="Editor Valori Scaling Factor", padding="10")
        right_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(2, weight=1)
        
        # Info factor selezionato
        info_frame = ttk.Frame(right_frame)
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(info_frame, text="Nome:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.factor_name_label = ttk.Label(info_frame, text="-", font=('Arial', 10))
        self.factor_name_label.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        ttk.Label(info_frame, text="Tipo:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.factor_type_label = ttk.Label(info_frame, text="-", font=('Arial', 10))
        self.factor_type_label.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # === SEZIONE ASSOCIAZIONI SORGENTI ===
        assoc_frame = ttk.LabelFrame(right_frame, text="Associazioni Sorgenti-Inquinanti", padding="5")
        assoc_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 10))
        assoc_frame.columnconfigure(0, weight=1)
        
        # Frame con scrollbar per le associazioni
        assoc_canvas_frame = ttk.Frame(assoc_frame)
        assoc_canvas_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        assoc_canvas_frame.columnconfigure(0, weight=1)
        
        assoc_scroll = ttk.Scrollbar(assoc_canvas_frame)
        assoc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.assoc_listbox = tk.Listbox(assoc_canvas_frame, yscrollcommand=assoc_scroll.set, 
                                        height=4, font=('Arial', 9))
        self.assoc_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        assoc_scroll.config(command=self.assoc_listbox.yview)
        
        # Bottoni per gestire le associazioni
        assoc_btn_frame = ttk.Frame(assoc_frame)
        assoc_btn_frame.grid(row=1, column=0, pady=5)
        
        ttk.Button(assoc_btn_frame, text="➕ Aggiungi", 
                  command=self.add_association, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(assoc_btn_frame, text="🗑️ Rimuovi", 
                  command=self.remove_association, width=12).pack(side=tk.LEFT, padx=2)
        
        # Area di editing con scrollbar
        edit_frame = ttk.Frame(right_frame)
        edit_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        edit_frame.columnconfigure(0, weight=1)
        edit_frame.rowconfigure(0, weight=1)
        
        edit_scroll_y = ttk.Scrollbar(edit_frame)
        edit_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        edit_scroll_x = ttk.Scrollbar(edit_frame, orient=tk.HORIZONTAL)
        edit_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.edit_canvas = tk.Canvas(edit_frame, yscrollcommand=edit_scroll_y.set, 
                                     xscrollcommand=edit_scroll_x.set)
        self.edit_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        edit_scroll_y.config(command=self.edit_canvas.yview)
        edit_scroll_x.config(command=self.edit_canvas.xview)
        
        self.edit_inner_frame = ttk.Frame(self.edit_canvas)
        self.canvas_window = self.edit_canvas.create_window((0, 0), window=self.edit_inner_frame, anchor=tk.NW)
        
        self.edit_inner_frame.bind('<Configure>', self.on_frame_configure)
        self.edit_canvas.bind('<Configure>', self.on_canvas_configure)
        
        # === BOTTONI AZIONE ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="💾 Salva", command=self.save_config, width=20).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="❌ Annulla", command=self.window.destroy, width=20).pack(side=tk.LEFT, padx=10)
    
    def on_frame_configure(self, event=None):
        """Aggiorna la scrollregion del canvas"""
        self.edit_canvas.configure(scrollregion=self.edit_canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        """Ridimensiona il frame interno al canvas"""
        self.edit_canvas.itemconfig(self.canvas_window, width=event.width)
    
    def refresh_factors_list(self):
        """Aggiorna la lista dei fattori di scala"""
        self.factors_listbox.delete(0, tk.END)
        for i, factor in enumerate(self.scaling_factors):
            factor_name = factor.get('factor_name', 'UNNAMED')
            factor_type = factor.get('factor_type', 'UNKNOWN')
            display_text = f"{factor.get('index', i+1)}. {factor_name} ({factor_type})"
            self.factors_listbox.insert(tk.END, display_text)
    
    def on_factor_select(self, event):
        """Gestisce la selezione di un fattore dalla lista"""
        selection = self.factors_listbox.curselection()
        if not selection:
            return
        
        self.selected_factor_index = selection[0]
        self.display_factor_editor()
    
    def display_factor_editor(self):
        """Mostra l'editor per il fattore selezionato"""
        if self.selected_factor_index is None or self.selected_factor_index >= len(self.scaling_factors):
            return
        
        factor = self.scaling_factors[self.selected_factor_index]
        factor_name = factor.get('factor_name', '')
        factor_type = factor.get('factor_type', '')
        factor_index = factor.get('index', str(self.selected_factor_index + 1))
        
        # Aggiorna le label
        self.factor_name_label.config(text=factor_name)
        type_desc = self.FACTOR_TYPES.get(factor_type, factor_type)
        self.factor_type_label.config(text=f"{factor_type} - {type_desc}")
        
        # Aggiorna la lista delle associazioni
        self.refresh_associations_list(factor_name)
        
        # Pulisci l'area di editing
        for widget in self.edit_inner_frame.winfo_children():
            widget.destroy()
        
        # Crea l'editor appropriato in base al tipo
        if factor_type == 'CONSTANT1':
            self.create_constant_editor(factor_index)
        elif factor_type == 'MONTH12':
            self.create_month12_editor(factor_index)
        elif factor_type == 'DAY7':
            self.create_day7_editor(factor_index)
        elif factor_type == 'HOUR24':
            self.create_hour24_editor(factor_index)
        elif factor_type == 'HOUR24_DAY7':
            self.create_hour24_day7_editor(factor_index)
        elif factor_type == 'HOUR24_MONTH12':
            self.create_hour24_month12_editor(factor_index)
        else:
            ttk.Label(self.edit_inner_frame, 
                     text=f"Editor per tipo '{factor_type}' non ancora implementato",
                     font=('Arial', 10, 'italic')).pack(pady=20)
    
    def create_constant_editor(self, factor_index):
        """Editor per fattore costante"""
        ttk.Label(self.edit_inner_frame, text="Valore Costante:", 
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        
        value_var = tk.DoubleVar(value=1.0)
        if factor_index in self.scaling_data.get('CONSTANT1', {}):
            value_var.set(self.scaling_data['CONSTANT1'][factor_index])
        
        ttk.Entry(self.edit_inner_frame, textvariable=value_var, width=20).pack(anchor=tk.W, pady=5)
        
        # Salva il riferimento per il salvataggio
        setattr(self, f'constant_{factor_index}', value_var)
    
    def create_month12_editor(self, factor_index):
        """Editor per fattori mensili (12 valori)"""
        months = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 
                 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
        
        # Carica valori esistenti o usa default
        if 'MONTH12' not in self.scaling_data:
            self.scaling_data['MONTH12'] = {}
        if factor_index not in self.scaling_data['MONTH12']:
            self.scaling_data['MONTH12'][factor_index] = [1.0] * 12
        
        values = self.scaling_data['MONTH12'][factor_index]
        
        ttk.Label(self.edit_inner_frame, text="Valori Mensili (Gen-Dic):", 
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        
        grid_frame = ttk.Frame(self.edit_inner_frame)
        grid_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        entries = []
        for i, month in enumerate(months):
            row = i // 4
            col = (i % 4) * 2
            
            ttk.Label(grid_frame, text=f"{month}:").grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            var = tk.DoubleVar(value=values[i] if i < len(values) else 1.0)
            ttk.Entry(grid_frame, textvariable=var, width=10).grid(row=row, column=col+1, padx=5, pady=2)
            entries.append(var)
        
        setattr(self, f'month12_{factor_index}', entries)
    
    def create_day7_editor(self, factor_index):
        """Editor per fattori settimanali (7 giorni)"""
        days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
        
        if 'DAY7' not in self.scaling_data:
            self.scaling_data['DAY7'] = {}
        if factor_index not in self.scaling_data['DAY7']:
            self.scaling_data['DAY7'][factor_index] = [1.0] * 7
        
        values = self.scaling_data['DAY7'][factor_index]
        
        ttk.Label(self.edit_inner_frame, text="Valori Settimanali (Lun-Dom):", 
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        
        grid_frame = ttk.Frame(self.edit_inner_frame)
        grid_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        entries = []
        for i, day in enumerate(days):
            ttk.Label(grid_frame, text=f"{day}:").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            var = tk.DoubleVar(value=values[i] if i < len(values) else 1.0)
            ttk.Entry(grid_frame, textvariable=var, width=15).grid(row=i, column=1, padx=5, pady=2)
            entries.append(var)
        
        setattr(self, f'day7_{factor_index}', entries)
    
    def create_hour24_editor(self, factor_index):
        """Editor per fattori orari (24 ore)"""
        if 'HOUR24' not in self.scaling_data:
            self.scaling_data['HOUR24'] = {}
        if factor_index not in self.scaling_data['HOUR24']:
            self.scaling_data['HOUR24'][factor_index] = [1.0] * 24
        
        values = self.scaling_data['HOUR24'][factor_index]
        
        ttk.Label(self.edit_inner_frame, text="Valori Orari (00:00-23:00):", 
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        
        ttk.Label(self.edit_inner_frame, text="Nota: Ora 1 = 00:00–01:00", 
                 font=('Arial', 8, 'italic'), foreground='gray').pack(anchor=tk.W)
        
        grid_frame = ttk.Frame(self.edit_inner_frame)
        grid_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        entries = []
        for hour in range(24):
            row = hour // 6
            col = (hour % 6) * 2
            
            label_text = f"{hour:02d}:00"
            ttk.Label(grid_frame, text=label_text).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            var = tk.DoubleVar(value=values[hour] if hour < len(values) else 1.0)
            ttk.Entry(grid_frame, textvariable=var, width=8).grid(row=row, column=col+1, padx=5, pady=2)
            entries.append(var)
        
        setattr(self, f'hour24_{factor_index}', entries)
    
    def create_hour24_day7_editor(self, factor_index):
        """Editor per fattori orari x giornalieri (24x7 matrice)"""
        days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
        
        # Inizializza i dati se necessario
        # Per HOUR24_DAY7, abbiamo bisogno sia dei dati HOUR24 che DAY7
        if 'HOUR24' not in self.scaling_data:
            self.scaling_data['HOUR24'] = {}
        if 'DAY7' not in self.scaling_data:
            self.scaling_data['DAY7'] = {}
        
        if factor_index not in self.scaling_data['HOUR24']:
            self.scaling_data['HOUR24'][factor_index] = [1.0] * 24
        if factor_index not in self.scaling_data['DAY7']:
            self.scaling_data['DAY7'][factor_index] = [1.0] * 7
        
        hour_values = self.scaling_data['HOUR24'][factor_index]
        day_values = self.scaling_data['DAY7'][factor_index]
        
        ttk.Label(self.edit_inner_frame, text="Fattori Orari x Giornalieri (Matrice 24x7):", 
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        
        ttk.Label(self.edit_inner_frame, 
                 text="Configurare separatamente i pattern orari e giornalieri. Il prodotto darà la matrice completa.",
                 font=('Arial', 8, 'italic'), foreground='gray').pack(anchor=tk.W, pady=(0, 10))
        
        # Notebook per separare ore e giorni
        notebook = ttk.Notebook(self.edit_inner_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab per pattern orario
        hour_frame = ttk.Frame(notebook, padding="10")
        notebook.add(hour_frame, text="Pattern Orario (24h)")
        
        hour_grid = ttk.Frame(hour_frame)
        hour_grid.pack(fill=tk.BOTH, expand=True)
        
        hour_entries = []
        for hour in range(24):
            row = hour // 6
            col = (hour % 6) * 2
            
            label_text = f"{hour:02d}:00"
            ttk.Label(hour_grid, text=label_text).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            var = tk.DoubleVar(value=hour_values[hour] if hour < len(hour_values) else 1.0)
            ttk.Entry(hour_grid, textvariable=var, width=8).grid(row=row, column=col+1, padx=5, pady=2)
            hour_entries.append(var)
        
        # Tab per pattern giornaliero
        day_frame = ttk.Frame(notebook, padding="10")
        notebook.add(day_frame, text="Pattern Giornaliero (7d)")
        
        day_grid = ttk.Frame(day_frame)
        day_grid.pack(fill=tk.BOTH, expand=True)
        
        day_entries = []
        for i, day in enumerate(days):
            ttk.Label(day_grid, text=f"{day}:").grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            var = tk.DoubleVar(value=day_values[i] if i < len(day_values) else 1.0)
            ttk.Entry(day_grid, textvariable=var, width=15).grid(row=i, column=1, padx=5, pady=5)
            day_entries.append(var)
        
        setattr(self, f'hour24_{factor_index}', hour_entries)
        setattr(self, f'day7_{factor_index}', day_entries)
    
    def create_hour24_month12_editor(self, factor_index):
        """Editor per fattori orari x mensili (24x12 matrice)"""
        months = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 
                 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
        
        # Inizializza i dati se necessario
        if 'HOUR24' not in self.scaling_data:
            self.scaling_data['HOUR24'] = {}
        if 'MONTH12' not in self.scaling_data:
            self.scaling_data['MONTH12'] = {}
        
        if factor_index not in self.scaling_data['HOUR24']:
            self.scaling_data['HOUR24'][factor_index] = [1.0] * 24
        if factor_index not in self.scaling_data['MONTH12']:
            self.scaling_data['MONTH12'][factor_index] = [1.0] * 12
        
        hour_values = self.scaling_data['HOUR24'][factor_index]
        month_values = self.scaling_data['MONTH12'][factor_index]
        
        ttk.Label(self.edit_inner_frame, text="Fattori Orari x Mensili (Matrice 24x12):", 
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        
        ttk.Label(self.edit_inner_frame, 
                 text="Configurare separatamente i pattern orari e mensili. Il prodotto darà la matrice completa.",
                 font=('Arial', 8, 'italic'), foreground='gray').pack(anchor=tk.W, pady=(0, 10))
        
        # Notebook per separare ore e mesi
        notebook = ttk.Notebook(self.edit_inner_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab per pattern orario
        hour_frame = ttk.Frame(notebook, padding="10")
        notebook.add(hour_frame, text="Pattern Orario (24h)")
        
        hour_grid = ttk.Frame(hour_frame)
        hour_grid.pack(fill=tk.BOTH, expand=True)
        
        hour_entries = []
        for hour in range(24):
            row = hour // 6
            col = (hour % 6) * 2
            
            label_text = f"{hour:02d}:00"
            ttk.Label(hour_grid, text=label_text).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            var = tk.DoubleVar(value=hour_values[hour] if hour < len(hour_values) else 1.0)
            ttk.Entry(hour_grid, textvariable=var, width=8).grid(row=row, column=col+1, padx=5, pady=2)
            hour_entries.append(var)
        
        # Tab per pattern mensile
        month_frame = ttk.Frame(notebook, padding="10")
        notebook.add(month_frame, text="Pattern Mensile (12m)")
        
        month_grid = ttk.Frame(month_frame)
        month_grid.pack(fill=tk.BOTH, expand=True)
        
        month_entries = []
        for i, month in enumerate(months):
            row = i // 4
            col = (i % 4) * 2
            
            ttk.Label(month_grid, text=f"{month}:").grid(row=row, column=col, sticky=tk.W, padx=5, pady=5)
            var = tk.DoubleVar(value=month_values[i] if i < len(month_values) else 1.0)
            ttk.Entry(month_grid, textvariable=var, width=10).grid(row=row, column=col+1, padx=5, pady=5)
            month_entries.append(var)
        
        setattr(self, f'hour24_{factor_index}', hour_entries)
        setattr(self, f'month12_{factor_index}', month_entries)
    
    def add_new_factor(self):
        """Aggiunge un nuovo fattore di scala"""
        # Dialog per nome
        factor_name = simpledialog.askstring("Nuovo Fattore", "Nome del fattore di scala:", parent=self.window)
        if not factor_name:
            return
        
        # Dialog per tipo
        type_dialog = tk.Toplevel(self.window)
        type_dialog.title("Seleziona Tipo")
        type_dialog.geometry("400x400")
        type_dialog.transient(self.window)
        type_dialog.grab_set()
        
        selected_type = tk.StringVar()
        
        ttk.Label(type_dialog, text="Seleziona il tipo di fattore:", 
                 font=('Arial', 10, 'bold')).pack(pady=10)
        
        # Listbox con i tipi
        list_frame = ttk.Frame(type_dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        types_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=('Arial', 10))
        types_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=types_listbox.yview)
        
        for type_key, type_desc in self.FACTOR_TYPES.items():
            types_listbox.insert(tk.END, f"{type_key} - {type_desc}")
        
        def on_select():
            selection = types_listbox.curselection()
            if selection:
                selected_text = types_listbox.get(selection[0])
                selected_type.set(selected_text.split(' - ')[0])
                type_dialog.destroy()
        
        ttk.Button(type_dialog, text="Seleziona", command=on_select).pack(pady=10)
        
        type_dialog.wait_window()
        
        if not selected_type.get():
            return
        
        # Calcola il prossimo indice
        next_index = str(len(self.scaling_factors) + 1)
        
        # Crea il nuovo fattore
        new_factor = {
            'index': next_index,
            'factor_name': factor_name,
            'factor_type': selected_type.get()
        }
        
        self.scaling_factors.append(new_factor)
        self.refresh_factors_list()
        
        messagebox.showinfo("Successo", f"Fattore '{factor_name}' aggiunto.\n"
                                        f"Configurare i valori e salvare.")
    
    def delete_factor(self):
        """Elimina il fattore selezionato"""
        if self.selected_factor_index is None:
            messagebox.showwarning("Attenzione", "Selezionare un fattore da eliminare")
            return
        
        factor = self.scaling_factors[self.selected_factor_index]
        factor_name = factor.get('factor_name', 'UNNAMED')
        
        if not messagebox.askyesno("Conferma", f"Eliminare il fattore '{factor_name}'?"):
            return
        
        # Rimuovi il fattore
        factor_index = factor.get('index')
        self.scaling_factors.pop(self.selected_factor_index)

        # Rimuovi tutte le associazioni sorgente-inquinante collegate al fattore
        self.scal_fact_punt_sor = [
            assoc for assoc in self.scal_fact_punt_sor
            if assoc.get('scaling_factor') != factor_name
        ]
        self.scal_fact_area_sor = [
            assoc for assoc in self.scal_fact_area_sor
            if assoc.get('scaling_factor') != factor_name
        ]
        self.scal_fact_vol_sor = [
            assoc for assoc in self.scal_fact_vol_sor
            if assoc.get('scaling_factor') != factor_name
        ]
        self.scal_fact_road_sor = [
            assoc for assoc in self.scal_fact_road_sor
            if assoc.get('scaling_factor') != factor_name
        ]
        self.scal_fact_line_sor = [
            assoc for assoc in self.scal_fact_line_sor
            if assoc.get('scaling_factor') != factor_name
        ]
        
        # Rimuovi i dati associati
        for data_type in self.scaling_data:
            if factor_index in self.scaling_data[data_type]:
                del self.scaling_data[data_type][factor_index]
        
        # Re-indicizza i fattori rimanenti
        for i, f in enumerate(self.scaling_factors):
            f['index'] = str(i + 1)
        
        self.selected_factor_index = None
        self.refresh_factors_list()
        self.assoc_listbox.delete(0, tk.END)
        
        # Pulisci l'editor
        for widget in self.edit_inner_frame.winfo_children():
            widget.destroy()
        
        self.factor_name_label.config(text="-")
        self.factor_type_label.config(text="-")
    
    def refresh_associations_list(self, factor_name):
        """Aggiorna la lista delle associazioni per il fattore corrente"""
        self.assoc_listbox.delete(0, tk.END)
        
        # Cerca in tutte le liste di associazioni
        all_associations = [
            ('Point', self.scal_fact_punt_sor),
            ('Area', self.scal_fact_area_sor),
            ('Volume', self.scal_fact_vol_sor),
            ('Road', self.scal_fact_road_sor),
            ('Line', self.scal_fact_line_sor)
        ]
        
        for source_type, assoc_list in all_associations:
            for assoc in assoc_list:
                if assoc.get('scaling_factor') == factor_name:
                    display_text = f"[{source_type}] {assoc['source_name']} - {assoc['pollutant']}"
                    self.assoc_listbox.insert(tk.END, display_text)
    
    def add_association(self):
        """Aggiunge un'associazione sorgente-inquinante al fattore corrente"""
        if self.selected_factor_index is None:
            messagebox.showwarning("Attenzione", "Selezionare un fattore di scala")
            return
        
        factor = self.scaling_factors[self.selected_factor_index]
        factor_name = factor.get('factor_name', '')
        
        # Carica le sorgenti e gli inquinanti disponibili
        available_sources = self._get_available_sources()
        available_pollutants = self._get_available_pollutants()
        
        if not available_pollutants:
            messagebox.showwarning("Attenzione", "Nessun inquinante configurato.\nConfigurare prima le specie.")
            return
        
        # Crea dialog per l'associazione
        dialog = tk.Toplevel(self.window)
        dialog.title("Nuova Associazione")
        dialog.geometry("400x250")
        dialog.transient(self.window)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tipo di sorgente
        ttk.Label(frame, text="Tipo Sorgente:").grid(row=0, column=0, sticky=tk.W, pady=5)
        source_type_var = tk.StringVar(value="Point")
        source_type_combo = ttk.Combobox(frame, textvariable=source_type_var, 
                                         values=['Point', 'Area', 'Volume', 'Road', 'Line'],
                                         state='readonly', width=25)
        source_type_combo.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Nome sorgente (combobox dinamico)
        ttk.Label(frame, text="Nome Sorgente:").grid(row=1, column=0, sticky=tk.W, pady=5)
        source_name_var = tk.StringVar()
        source_name_combo = ttk.Combobox(frame, textvariable=source_name_var, 
                                         values=available_sources.get('Point', []),
                                         state='readonly', width=25)
        source_name_combo.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Funzione per aggiornare le sorgenti disponibili quando cambia il tipo
        def update_sources(event=None):
            source_type = source_type_var.get()
            sources = available_sources.get(source_type, [])
            source_name_combo['values'] = sources
            if sources:
                source_name_var.set(sources[0])
            else:
                source_name_var.set('')
        
        source_type_combo.bind('<<ComboboxSelected>>', update_sources)
        update_sources()  # Inizializza
        
        # Inquinante (combobox)
        ttk.Label(frame, text="Inquinante:").grid(row=2, column=0, sticky=tk.W, pady=5)
        pollutant_var = tk.StringVar(value=available_pollutants[0] if available_pollutants else '')
        pollutant_combo = ttk.Combobox(frame, textvariable=pollutant_var, 
                                       values=available_pollutants,
                                       state='readonly', width=25)
        pollutant_combo.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Info
        info_label = ttk.Label(frame, 
                               text=f"Verrà associato a: {factor_name}",
                               font=('Arial', 9, 'italic'),
                               foreground='gray')
        info_label.grid(row=3, column=0, columnspan=2, pady=10)
        
        def save_association():
            source_name = source_name_var.get().strip()
            pollutant = pollutant_var.get().strip()
            source_type = source_type_var.get()
            
            if not source_name or not pollutant:
                messagebox.showwarning("Attenzione", "Selezionare sorgente e inquinante")
                return
            
            new_assoc = {
                'source_name': source_name,
                'pollutant': pollutant,
                'scaling_factor': factor_name
            }
            
            # Aggiungi alla lista appropriata
            if source_type == 'Point':
                self.scal_fact_punt_sor.append(new_assoc)
            elif source_type == 'Area':
                self.scal_fact_area_sor.append(new_assoc)
            elif source_type == 'Volume':
                self.scal_fact_vol_sor.append(new_assoc)
            elif source_type == 'Road':
                self.scal_fact_road_sor.append(new_assoc)
            elif source_type == 'Line':
                self.scal_fact_line_sor.append(new_assoc)
            
            self.refresh_associations_list(factor_name)
            dialog.destroy()
        
        # Bottoni
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Salva", command=save_association).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def remove_association(self):
        """Rimuove un'associazione selezionata"""
        selection = self.assoc_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare un'associazione da rimuovere")
            return
        
        selected_text = self.assoc_listbox.get(selection[0])
        
        if not messagebox.askyesno("Conferma", f"Rimuovere l'associazione:\n{selected_text}?"):
            return
        
        # Estrai informazioni dal testo
        # Formato: "[Type] source_name - pollutant"
        import re
        match = re.match(r'\[(\w+)\] (.+) - (.+)', selected_text)
        if not match:
            return
        
        source_type, source_name, pollutant = match.groups()
        
        # Trova e rimuovi l'associazione dalla lista appropriata
        factor = self.scaling_factors[self.selected_factor_index]
        factor_name = factor.get('factor_name', '')
        
        def remove_from_list(assoc_list):
            for i, assoc in enumerate(assoc_list):
                if (assoc.get('source_name') == source_name and 
                    assoc.get('pollutant') == pollutant and
                    assoc.get('scaling_factor') == factor_name):
                    assoc_list.pop(i)
                    return True
            return False
        
        # Rimuovi dalla lista appropriata
        removed = False
        if source_type == 'Point':
            removed = remove_from_list(self.scal_fact_punt_sor)
        elif source_type == 'Area':
            removed = remove_from_list(self.scal_fact_area_sor)
        elif source_type == 'Volume':
            removed = remove_from_list(self.scal_fact_vol_sor)
        elif source_type == 'Road':
            removed = remove_from_list(self.scal_fact_road_sor)
        elif source_type == 'Line':
            removed = remove_from_list(self.scal_fact_line_sor)
        
        if removed:
            self.refresh_associations_list(factor_name)
        else:
            messagebox.showerror("Errore", "Impossibile rimuovere l'associazione")
    
    def _get_available_sources(self):
        """Recupera le sorgenti configurate per tipo"""
        config_file = self.temp_dir / 'calpuff_config.json'
        sources_by_type = {
            'Point': [],
            'Area': [],
            'Volume': [],
            'Road': [],
            'Line': []
        }
        
        if not config_file.exists():
            return sources_by_type
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Point sources - salvate come 'point_sources'
            point_sources = data.get('point_sources', [])
            sources_by_type['Point'] = [src.get('source_name', '') for src in point_sources if src.get('source_name')]
            
            # Area sources - salvate come 'area_emission'
            area_sources = data.get('area_emission', [])
            sources_by_type['Area'] = [src.get('source_name', '') for src in area_sources if src.get('source_name')]
            
            # Volume sources - salvate come 'volume_emission'
            volume_sources = data.get('volume_emission', [])
            sources_by_type['Volume'] = [src.get('source_name', '') for src in volume_sources if src.get('source_name')]
            
            # Road sources - salvate come 'road_emission'
            road_sources = data.get('road_emission', [])
            sources_by_type['Road'] = [src.get('source_name', '') for src in road_sources if src.get('source_name')]
            
            # Line sources - salvate come 'line_emission'
            line_sources = data.get('line_emission', [])
            sources_by_type['Line'] = [src.get('source_name', '') for src in line_sources if src.get('source_name')]
            
        except Exception as e:
            print(f"Errore caricamento sorgenti: {e}")
        
        return sources_by_type
    
    def _get_available_pollutants(self):
        """Recupera gli inquinanti (species) configurati"""
        config_file = self.temp_dir / 'calpuff_config.json'
        pollutants = []
        
        if not config_file.exists():
            return pollutants
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Le species sono salvate come dizionario {nome: {parametri}}
            species = data.get('species', {})
            pollutants = list(species.keys())
            
        except Exception as e:
            print(f"Errore caricamento inquinanti: {e}")
        
        return pollutants
    
    def save_config(self):
        """Salva la configurazione dei fattori di scala"""
        try:
            # Raccogli i dati da tutti gli editor attivi
            self.collect_editor_data()
            
            config_file = self.temp_dir / 'calpuff_config.json'
            
            # Carica la configurazione esistente
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                config_data = {}
            
            # Aggiorna i dati degli scaling factors
            config_data['scaling_factors'] = self.scaling_factors
            config_data['scaling_data'] = self.scaling_data
            
            # Aggiorna le associazioni sorgenti-inquinanti
            config_data['scal_fact_punt_sor'] = self.scal_fact_punt_sor
            config_data['scal_fact_area_sor'] = self.scal_fact_area_sor
            config_data['scal_fact_vol_sor'] = self.scal_fact_vol_sor
            config_data['scal_fact_road_sor'] = self.scal_fact_road_sor
            config_data['scal_fact_line_sor'] = self.scal_fact_line_sor
            
            # Salva
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Successo", 
                              f"Scaling factors salvati:\n"
                              f"- {len(self.scaling_factors)} fattori definiti\n"
                              f"File: {config_file}")
            self.window.destroy()
        
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il salvataggio:\n{str(e)}")
    
    def collect_editor_data(self):
        """Raccoglie i dati da tutti gli editor attivi"""
        if self.selected_factor_index is None or self.selected_factor_index >= len(self.scaling_factors):
            return
        
        factor = self.scaling_factors[self.selected_factor_index]
        factor_index = factor.get('index')
        factor_type = factor.get('factor_type')
        
        # Raccogli i dati in base al tipo
        if factor_type == 'CONSTANT1':
            if hasattr(self, f'constant_{factor_index}'):
                if 'CONSTANT1' not in self.scaling_data:
                    self.scaling_data['CONSTANT1'] = {}
                var = getattr(self, f'constant_{factor_index}')
                self.scaling_data['CONSTANT1'][factor_index] = var.get()
        
        elif factor_type == 'MONTH12':
            if hasattr(self, f'month12_{factor_index}'):
                if 'MONTH12' not in self.scaling_data:
                    self.scaling_data['MONTH12'] = {}
                entries = getattr(self, f'month12_{factor_index}')
                self.scaling_data['MONTH12'][factor_index] = [var.get() for var in entries]
        
        elif factor_type == 'DAY7':
            if hasattr(self, f'day7_{factor_index}'):
                if 'DAY7' not in self.scaling_data:
                    self.scaling_data['DAY7'] = {}
                entries = getattr(self, f'day7_{factor_index}')
                self.scaling_data['DAY7'][factor_index] = [var.get() for var in entries]
        
        elif factor_type == 'HOUR24':
            if hasattr(self, f'hour24_{factor_index}'):
                if 'HOUR24' not in self.scaling_data:
                    self.scaling_data['HOUR24'] = {}
                entries = getattr(self, f'hour24_{factor_index}')
                self.scaling_data['HOUR24'][factor_index] = [var.get() for var in entries]
        
        elif factor_type in ['HOUR24_DAY7', 'HOUR24_MONTH12']:
            # Questi tipi hanno sia hour24 che day7/month12
            if hasattr(self, f'hour24_{factor_index}'):
                if 'HOUR24' not in self.scaling_data:
                    self.scaling_data['HOUR24'] = {}
                entries = getattr(self, f'hour24_{factor_index}')
                self.scaling_data['HOUR24'][factor_index] = [var.get() for var in entries]
            
            if factor_type == 'HOUR24_DAY7' and hasattr(self, f'day7_{factor_index}'):
                if 'DAY7' not in self.scaling_data:
                    self.scaling_data['DAY7'] = {}
                entries = getattr(self, f'day7_{factor_index}')
                self.scaling_data['DAY7'][factor_index] = [var.get() for var in entries]
            
            elif factor_type == 'HOUR24_MONTH12' and hasattr(self, f'month12_{factor_index}'):
                if 'MONTH12' not in self.scaling_data:
                    self.scaling_data['MONTH12'] = {}
                entries = getattr(self, f'month12_{factor_index}')
                self.scaling_data['MONTH12'][factor_index] = [var.get() for var in entries]
