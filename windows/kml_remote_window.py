"""
Finestra per configurare la generazione remota dei KML.
"""

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


class KMLRemoteWindow:
    """Finestra per configurare e avviare la generazione KML sul farm."""

    def __init__(self, parent, temp_dir, start_callback=None):
        self.parent = parent
        self.temp_dir = temp_dir
        self.start_callback = start_callback
        self.window = tk.Toplevel(parent)
        self.window.title("Configurazione KML Remoto")
        self.window.geometry("820x760")

        self.job_name = tk.StringVar(value="kml_job")
        self.remote_payload_root = tk.StringVar(value="KML_REMOTE")
        self.remote_output_dir = tk.StringVar(value="")
        self.levels = tk.IntVar(value=400)
        self.variable = tk.StringVar(value="")
        self.zone = tk.StringVar(value="32")
        self.projin = tk.StringVar(value="utm")
        self.projout = tk.StringVar(value="WGS84")
        self.static = tk.BooleanVar(value=False)
        self.max_scale = tk.DoubleVar(value=130.0)
        self.min_scale = tk.DoubleVar(value=0.0)
        self.x_col = tk.StringVar(value="x_km")
        self.y_col = tk.StringVar(value="y_km")
        self.val_col = tk.StringVar(value="value")
        self.scale = tk.DoubleVar(value=1.0)
        self.x_shift = tk.DoubleVar(value=0.0)
        self.y_shift = tk.DoubleVar(value=0.0)
        self.x_scale_factor = tk.DoubleVar(value=1.0)
        self.y_scale_factor = tk.DoubleVar(value=1.0)

        self.available_source_folders = self._load_post_process_source_folders()
        self.selected_source_folders = []
        self.manual_source_folder = tk.StringVar(value="")
        self.source_folder_listbox = None

        self.load_existing_config()
        self.setup_ui()

    def _load_post_process_source_folders(self):
        """Estrae le cartelle sorgenti salvate in post_process.json."""
        post_process_file = self.temp_dir / "post_process.json"
        if not post_process_file.exists():
            return []

        try:
            with open(post_process_file, 'r', encoding='utf-8') as handle:
                data = json.load(handle)
        except Exception:
            return []

        candidates = []
        tracked_keys = {
            'aggreg_folder',
            'mean_source_folder',
            'mean_output_folder',
            'percentile_source_folder',
            'percentile_output_folder',
            'puntuale_source_folder',
        }
        for key, value in data.items():
            if key in tracked_keys:
                folder_value = str(value).strip()
                if folder_value:
                    candidates.append(folder_value)

        return self._unique_folder_values(candidates)

    def _unique_folder_values(self, folders):
        """Deduplica i percorsi preservando il primo valore originale."""
        unique = []
        seen = set()
        for item in folders:
            normalized = str(item).replace('\\', '/').strip()
            if not normalized:
                continue
            lowered = normalized.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            unique.append(str(item).strip())
        return unique

    def load_existing_config(self):
        """Carica la configurazione salvata, se presente."""
        config_file = self.temp_dir / "kml_config.json"
        if not config_file.exists():
            return

        try:
            with open(config_file, 'r', encoding='utf-8') as handle:
                data = json.load(handle)
        except Exception as exc:
            messagebox.showwarning(
                "Attenzione",
                f"Impossibile caricare la configurazione KML remota:\n{exc}",
                parent=self.parent,
            )
            return

        self.job_name.set(data.get('job_name', self.job_name.get()))
        self.remote_payload_root.set(data.get('remote_payload_root', self.remote_payload_root.get()))
        self.remote_output_dir.set(data.get('remote_output_dir', self.remote_output_dir.get()))
        self.levels.set(int(data.get('levels', self.levels.get())))
        self.variable.set(data.get('variable', self.variable.get()))
        self.zone.set(str(data.get('zone', self.zone.get())))
        self.projin.set(data.get('projin', self.projin.get()))
        self.projout.set(data.get('projout', self.projout.get()))
        self.static.set(bool(data.get('static', self.static.get())))
        self.max_scale.set(float(data.get('max_scale', self.max_scale.get())))
        self.min_scale.set(float(data.get('min_scale', self.min_scale.get())))
        self.x_col.set(data.get('x_col', self.x_col.get()))
        self.y_col.set(data.get('y_col', self.y_col.get()))
        self.val_col.set(data.get('val_col', self.val_col.get()))
        self.scale.set(float(data.get('scale', self.scale.get())))
        self.x_shift.set(float(data.get('x_shift', self.x_shift.get())))
        self.y_shift.set(float(data.get('y_shift', self.y_shift.get())))
        self.x_scale_factor.set(float(data.get('x_scale_factor', self.x_scale_factor.get())))
        self.y_scale_factor.set(float(data.get('y_scale_factor', self.y_scale_factor.get())))
        loaded_sources = data.get('source_folders', [])
        if isinstance(loaded_sources, list):
            self.selected_source_folders = [str(item).strip() for item in loaded_sources if str(item).strip()]
            self.available_source_folders = self._unique_folder_values(
                list(self.available_source_folders) + self.selected_source_folders
            )
        elif data.get('file_list'):
            self.selected_source_folders = []

    def setup_ui(self):
        """Costruisce l'interfaccia della finestra."""
        main_frame = ttk.Frame(self.window, padding="12")
        main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        ttk.Label(
            main_frame,
            text="Configurazione KML Remoto",
            font=('Arial', 13, 'bold')
        ).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        info_label = ttk.Label(
            main_frame,
            text=(
                "Seleziona una o piu cartelle sorgenti salvate in post_process.json. "
                "Il job cerchera tutti i CSV nelle sottocartelle ricorsivamente. "
                "Lo Start Processing salva la configurazione, carica uno script Python "
                "sul farm e sottomette la generazione KML."
            ),
            justify=tk.LEFT,
            wraplength=760,
        )
        info_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        form_frame = ttk.LabelFrame(main_frame, text="Parametri", padding="10")
        form_frame.grid(row=2, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)
        form_frame.rowconfigure(11, weight=1)

        self._add_entry(form_frame, 0, "Nome job:", self.job_name)
        self._add_entry(form_frame, 0, "Cartella payload remota:", self.remote_payload_root, column_offset=2)
        self._add_entry(form_frame, 1, "Cartella output remota:", self.remote_output_dir)
        self._add_entry(form_frame, 2, "Livelli:", self.levels)
        self._add_entry(form_frame, 2, "Variabile:", self.variable, column_offset=2)
        self._add_entry(form_frame, 3, "Zona:", self.zone)
        self._add_entry(form_frame, 3, "Proj in:", self.projin, column_offset=2)
        self._add_entry(form_frame, 4, "Proj out:", self.projout)

        ttk.Checkbutton(
            form_frame,
            text="Scala statica",
            variable=self.static,
        ).grid(row=4, column=2, columnspan=2, sticky=tk.W, padx=6, pady=4)

        ttk.Label(
            form_frame,
            text=(
                "Lascia vuota la cartella output per salvare i KML accanto ai CSV. "
                "Se la imposti, verra ricreata all'interno la stessa struttura delle cartelle sorgenti. "
                "Se Variabile e vuota, verra inferita dalla prima sottocartella sotto ogni cartella sorgente selezionata."
            ),
            foreground="gray40",
            wraplength=720,
        ).grid(row=5, column=0, columnspan=4, sticky=tk.W, pady=(2, 8))

        self._add_entry(form_frame, 6, "Max scale:", self.max_scale)
        self._add_entry(form_frame, 6, "Min scale:", self.min_scale, column_offset=2)
        self._add_entry(form_frame, 7, "Colonna X:", self.x_col)
        self._add_entry(form_frame, 7, "Colonna Y:", self.y_col, column_offset=2)
        self._add_entry(form_frame, 8, "Colonna valori:", self.val_col)
        self._add_entry(form_frame, 8, "Moltiplicatore:", self.scale, column_offset=2)
        self._add_entry(form_frame, 9, "Shift X:", self.x_shift)
        self._add_entry(form_frame, 9, "Shift Y:", self.y_shift, column_offset=2)
        self._add_entry(form_frame, 10, "Scale factor X:", self.x_scale_factor)
        self._add_entry(form_frame, 10, "Scale factor Y:", self.y_scale_factor, column_offset=2)

        sources_frame = ttk.LabelFrame(form_frame, text="Cartelle sorgenti", padding="8")
        sources_frame.grid(row=11, column=0, columnspan=4, sticky=(tk.N, tk.S, tk.W, tk.E), pady=(10, 4))
        sources_frame.columnconfigure(0, weight=1)
        sources_frame.rowconfigure(2, weight=1)

        ttk.Label(
            sources_frame,
            text="Valori caricati da post_process.json, con possibilita di aggiungere o rimuovere cartelle manualmente.",
            foreground="gray40",
            wraplength=700,
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 8))

        manual_frame = ttk.Frame(sources_frame)
        manual_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
        manual_frame.columnconfigure(0, weight=1)

        ttk.Entry(manual_frame, textvariable=self.manual_source_folder).grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 8)
        )
        ttk.Button(manual_frame, text="Add", command=self.add_source_folder, width=10).grid(
            row=0, column=1, padx=(0, 6)
        )
        ttk.Button(manual_frame, text="Remove Selected", command=self.remove_selected_folders, width=16).grid(
            row=0, column=2
        )

        source_frame = ttk.Frame(sources_frame)
        source_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.N, tk.S, tk.W, tk.E))
        source_frame.columnconfigure(0, weight=1)
        source_frame.rowconfigure(0, weight=1)

        self.source_folder_listbox = tk.Listbox(
            source_frame,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            height=10,
        )
        self.source_folder_listbox.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        self.source_folder_listbox.bind('<<ListboxSelect>>', self._on_source_folder_selection)

        scrollbar = ttk.Scrollbar(source_frame, orient=tk.VERTICAL, command=self.source_folder_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.source_folder_listbox.configure(yscrollcommand=scrollbar.set)

        self._refresh_source_folder_listbox()

        ttk.Label(
            form_frame,
            text="Le cartelle possono essere assolute o relative alla working folder del farm. Tutti i CSV nelle sottocartelle verranno processati.",
            foreground="gray40",
            wraplength=720,
        ).grid(row=12, column=0, columnspan=4, sticky=tk.W, pady=(4, 0))

        if not self.available_source_folders:
            ttk.Label(
                form_frame,
                text="Nessuna cartella disponibile in post_process.json. Configura prima le operazioni di post-processing.",
                foreground="darkred",
                wraplength=720,
            ).grid(row=13, column=0, columnspan=4, sticky=tk.W, pady=(8, 0))

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky=tk.E, pady=(12, 0))

        ttk.Button(button_frame, text="💾 Save", command=self.save_config, width=18).pack(side=tk.LEFT, padx=6)
        ttk.Button(button_frame, text="🚀 Start Processing", command=self.start_processing, width=22).pack(side=tk.LEFT, padx=6)
        ttk.Button(button_frame, text="❌ Close", command=self.window.destroy, width=18).pack(side=tk.LEFT, padx=6)

    def _add_entry(self, parent, row, label, variable, column_offset=0):
        ttk.Label(parent, text=label).grid(
            row=row,
            column=column_offset,
            sticky=tk.W,
            padx=(0, 6),
            pady=4,
        )
        ttk.Entry(parent, textvariable=variable).grid(
            row=row,
            column=column_offset + 1,
            sticky=(tk.W, tk.E),
            padx=(0, 12),
            pady=4,
        )

    def _collect_selected_source_folders(self):
        if self.source_folder_listbox is None:
            return []
        return [
            self.available_source_folders[index]
            for index in self.source_folder_listbox.curselection()
        ]

    def _on_source_folder_selection(self, _event=None):
        """Mantiene allineata la selezione logica con la listbox."""
        self.selected_source_folders = self._collect_selected_source_folders()

    def _refresh_source_folder_listbox(self, selected_folders=None):
        """Sincronizza la listbox con l'elenco corrente di cartelle."""
        if self.source_folder_listbox is None:
            return

        if selected_folders is None:
            selected_now = set(self.selected_source_folders)
        else:
            selected_now = set(selected_folders)
        self.available_source_folders = self._unique_folder_values(self.available_source_folders)

        self.source_folder_listbox.delete(0, tk.END)
        for index, folder in enumerate(self.available_source_folders):
            self.source_folder_listbox.insert(tk.END, folder)
            if folder in selected_now:
                self.source_folder_listbox.selection_set(index)
        self.selected_source_folders = [
            folder for folder in self.available_source_folders
            if folder in selected_now
        ]

    def add_source_folder(self):
        """Aggiunge manualmente una cartella all'elenco sorgenti."""
        folder_value = self.manual_source_folder.get().strip()
        if not folder_value:
            messagebox.showwarning("Attenzione", "Inserisci una cartella da aggiungere.", parent=self.window)
            return

        normalized_existing = {item.replace('\\', '/').strip().lower() for item in self.available_source_folders}
        normalized_value = folder_value.replace('\\', '/').strip().lower()
        if normalized_value not in normalized_existing:
            self.available_source_folders.append(folder_value)

        self.selected_source_folders = self._unique_folder_values(
            list(self.selected_source_folders) + [folder_value]
        )
        self.manual_source_folder.set("")
        self._refresh_source_folder_listbox(selected_folders=self.selected_source_folders)

    def remove_selected_folders(self):
        """Rimuove dall'elenco le cartelle selezionate manualmente dall'utente."""
        selected_indexes = list(self.source_folder_listbox.curselection()) if self.source_folder_listbox else []
        if not selected_indexes:
            messagebox.showwarning("Attenzione", "Seleziona almeno una cartella da rimuovere.", parent=self.window)
            return

        selected_values = {self.available_source_folders[index] for index in selected_indexes}
        self.available_source_folders = [
            folder for folder in self.available_source_folders
            if folder not in selected_values
        ]
        self.selected_source_folders = [
            folder for folder in self.selected_source_folders
            if folder not in selected_values
        ]
        self._refresh_source_folder_listbox(selected_folders=self.selected_source_folders)

    def _build_config_data(self):
        source_folders = self._collect_selected_source_folders()
        config_data = {
            'job_name': self.job_name.get().strip(),
            'remote_payload_root': self.remote_payload_root.get().strip(),
            'remote_output_dir': self.remote_output_dir.get().strip(),
            'levels': int(self.levels.get()),
            'variable': self.variable.get().strip(),
            'zone': self.zone.get().strip(),
            'projin': self.projin.get().strip(),
            'projout': self.projout.get().strip(),
            'static': bool(self.static.get()),
            'max_scale': float(self.max_scale.get()),
            'min_scale': float(self.min_scale.get()),
            'x_col': self.x_col.get().strip(),
            'y_col': self.y_col.get().strip(),
            'val_col': self.val_col.get().strip(),
            'scale': float(self.scale.get()),
            'x_shift': float(self.x_shift.get()),
            'y_shift': float(self.y_shift.get()),
            'x_scale_factor': float(self.x_scale_factor.get()),
            'y_scale_factor': float(self.y_scale_factor.get()),
            'base': self.remote_output_dir.get().strip(),
            'source_folders': source_folders,
        }
        self._validate_config_data(config_data)
        return config_data

    def _validate_config_data(self, config_data):
        if not config_data['job_name']:
            raise ValueError("Inserisci un nome job.")
        if not config_data['remote_payload_root']:
            raise ValueError("Inserisci la cartella payload remota.")
        if not config_data['zone']:
            raise ValueError("Inserisci la zona di proiezione.")
        if not config_data['x_col'] or not config_data['y_col'] or not config_data['val_col']:
            raise ValueError("Inserisci i nomi delle colonne X, Y e valori.")
        if not config_data['source_folders']:
            raise ValueError("Seleziona o aggiungi almeno una cartella sorgente.")
        if config_data['levels'] <= 0:
            raise ValueError("Il numero di livelli deve essere positivo.")
        if config_data['max_scale'] < config_data['min_scale']:
            raise ValueError("Max scale deve essere maggiore o uguale a Min scale.")

    def save_config(self, show_message=True):
        """Salva la configurazione locale in temp_config."""
        try:
            config_data = self._build_config_data()
            config_file = self.temp_dir / 'kml_config.json'
            with open(config_file, 'w', encoding='utf-8') as handle:
                json.dump(config_data, handle, indent=4, ensure_ascii=False)
        except Exception as exc:
            messagebox.showerror("Errore", f"Errore durante il salvataggio della configurazione KML:\n{exc}", parent=self.window)
            return False

        if show_message:
            messagebox.showinfo("Successo", "Configurazione KML remota salvata correttamente.", parent=self.window)
        return True

    def start_processing(self):
        """Salva la configurazione e avvia il callback di processing remoto."""
        if not self.save_config(show_message=False):
            return

        if self.start_callback is None:
            messagebox.showinfo(
                "Configurazione salvata",
                "La configurazione KML è stata salvata, ma non è stato configurato alcun avvio remoto.",
                parent=self.window,
            )
            return

        try:
            self.start_callback()
        except Exception as exc:
            messagebox.showerror("Errore", f"Errore durante l'avvio remoto del KML:\n{exc}", parent=self.window)
            return

        self.window.lift()
        self.window.focus_force()
