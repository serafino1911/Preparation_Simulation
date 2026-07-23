import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
from pathlib import Path
from datetime import date, datetime
import threading


class FilettiWindow:
    """Finestra per la preparazione dei filetti"""

    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = Path(temp_dir)
        self.config_file = self.temp_dir / "filetti_config.json"

        self.window = tk.Toplevel(parent)
        self.window.title("Filetti")
        self.window.geometry("860x620")
        self.window.transient(parent)
        self.window.grab_set()

        self.input_db_var = tk.StringVar(value="")
        self.def_sources_var = tk.StringVar(value="")
        self.source_type_var = tk.StringVar(value="Puntuali")
        self.output_name_var = tk.StringVar(value="")

        today = date.today()
        self.start_dt_var = tk.StringVar(value=f"{today.strftime('%d/%m/%Y')} 00:00")
        self.end_dt_var = tk.StringVar(value=f"{today.strftime('%d/%m/%Y')} 00:00")

        self.molpesis_rows = []
        self.molpesis_rows_frame = None
        self._loaded_molpesis_rows = []

        self._load_existing_config()
        self._setup_ui()

    def _setup_ui(self):
        main_frame = ttk.Frame(self.window, padding="12")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        ttk.Label(
            main_frame,
            text="Selezione Filetti",
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        ttk.Label(main_frame, text="input_db:").grid(row=1, column=0, sticky=tk.W, pady=6)
        ttk.Entry(main_frame, textvariable=self.input_db_var).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=6, padx=8
        )
        ttk.Button(main_frame, text="Sfoglia...", command=self._browse_input_db, width=12).grid(
            row=1, column=2, sticky=tk.E, pady=6
        )

        ttk.Label(main_frame, text="def Sources:").grid(row=2, column=0, sticky=tk.W, pady=6)
        ttk.Entry(main_frame, textvariable=self.def_sources_var).grid(
            row=2, column=1, sticky=(tk.W, tk.E), pady=6, padx=8
        )
        ttk.Button(main_frame, text="Sfoglia...", command=self._browse_def_sources, width=12).grid(
            row=2, column=2, sticky=tk.E, pady=6
        )

        ttk.Label(main_frame, text="Tipo sorgenti:").grid(row=3, column=0, sticky=tk.W, pady=6)
        ttk.Combobox(
            main_frame,
            textvariable=self.source_type_var,
            values=["Puntuali", "Areali"],
            state="readonly"
        ).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=6, padx=8)

        ttk.Label(main_frame, text="Nome output:").grid(row=4, column=0, sticky=tk.W, pady=6)
        ttk.Entry(main_frame, textvariable=self.output_name_var).grid(
            row=4, column=1, sticky=(tk.W, tk.E), pady=6, padx=8
        )

        ttk.Label(main_frame, text="DATE_START:").grid(row=5, column=0, sticky=tk.W, pady=6)
        start_date_frame = ttk.Frame(main_frame)
        start_date_frame.grid(row=5, column=1, sticky=tk.W, pady=6, padx=8)
        ttk.Entry(start_date_frame, textvariable=self.start_dt_var, width=20).pack(side=tk.LEFT)
        ttk.Label(start_date_frame, text="(gg/mm/aaaa HH:MM)", foreground="gray").pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(
            start_date_frame,
            text="📅",
            command=lambda: self._open_calendar_with_hour("start"),
            width=3,
        ).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Label(main_frame, text="DATE_END:").grid(row=6, column=0, sticky=tk.W, pady=6)
        end_date_frame = ttk.Frame(main_frame)
        end_date_frame.grid(row=6, column=1, sticky=tk.W, pady=6, padx=8)
        ttk.Entry(end_date_frame, textvariable=self.end_dt_var, width=20).pack(side=tk.LEFT)
        ttk.Label(end_date_frame, text="(gg/mm/aaaa HH:MM)", foreground="gray").pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(
            end_date_frame,
            text="📅",
            command=lambda: self._open_calendar_with_hour("end"),
            width=3,
        ).pack(side=tk.LEFT, padx=(6, 0))

        molpesis_frame = ttk.LabelFrame(main_frame, text="MOLPESIS", padding="8")
        molpesis_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        molpesis_frame.columnconfigure(0, weight=1)

        header = ttk.Frame(molpesis_frame)
        header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 4))
        header.columnconfigure(0, weight=2)
        header.columnconfigure(1, weight=1)
        header.columnconfigure(2, weight=1)
        ttk.Label(header, text="Pollutant", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(header, text="mol", font=("Arial", 9, "bold")).grid(row=0, column=1, sticky=tk.W, padx=6)
        ttk.Label(header, text="units", font=("Arial", 9, "bold")).grid(row=0, column=2, sticky=tk.W, padx=6)

        self.molpesis_rows_frame = ttk.Frame(molpesis_frame)
        self.molpesis_rows_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.molpesis_rows_frame.columnconfigure(0, weight=1)

        molpesis_actions = ttk.Frame(molpesis_frame)
        molpesis_actions.grid(row=2, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Button(molpesis_actions, text="Aggiungi pollutant", command=self._add_molpesis_row).pack(side=tk.LEFT)

        if self._loaded_molpesis_rows:
            for pollutant, mol, units in self._loaded_molpesis_rows:
                self._add_molpesis_row(pollutant, mol, units)
        else:
            self._add_molpesis_row("NOX", "40.", "g/s")
            self._add_molpesis_row("PM10", "10.", "g/s")

        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=8, column=0, columnspan=3, sticky=tk.E, pady=(14, 0))

        ttk.Button(buttons_frame, text="Salva", command=self._save_config, width=12).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(buttons_frame, text="Create", command=self._create, width=12).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(buttons_frame, text="Chiudi", command=self.window.destroy, width=12).pack(side=tk.LEFT)

    def _parse_datetime(self, value, field_name):
        text = str(value).strip()
        formats = ["%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
        for fmt in formats:
            try:
                parsed = datetime.strptime(text, fmt)
                if fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                    parsed = parsed.replace(hour=0, minute=0)
                return parsed
            except Exception:
                continue
        raise ValueError(f"{field_name} non valida")

    def _open_calendar_with_hour(self, target):
        current_value = self.start_dt_var.get() if target == "start" else self.end_dt_var.get()
        try:
            current_dt = self._parse_datetime(current_value, "data")
        except Exception:
            current_dt = datetime.now().replace(minute=0, second=0, microsecond=0)

        cal_window = tk.Toplevel(self.window)
        cal_window.title(f"Seleziona Data {'Inizio' if target == 'start' else 'Fine'}")
        cal_window.geometry("460x220")
        cal_window.transient(self.window)
        cal_window.grab_set()

        frame = ttk.Frame(cal_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Inserisci data e ora:", font=("Arial", 10)).pack(pady=10)

        date_frame = ttk.Frame(frame)
        date_frame.pack(pady=10)

        ttk.Label(date_frame, text="Giorno:").grid(row=0, column=0, padx=5)
        day_var = tk.StringVar(value=str(current_dt.day).zfill(2))
        ttk.Spinbox(date_frame, from_=1, to=31, textvariable=day_var, width=5).grid(row=0, column=1, padx=5)

        ttk.Label(date_frame, text="Mese:").grid(row=0, column=2, padx=5)
        month_var = tk.StringVar(value=str(current_dt.month).zfill(2))
        ttk.Spinbox(date_frame, from_=1, to=12, textvariable=month_var, width=5).grid(row=0, column=3, padx=5)

        ttk.Label(date_frame, text="Anno:").grid(row=0, column=4, padx=5)
        year_var = tk.StringVar(value=str(current_dt.year))
        ttk.Spinbox(date_frame, from_=2000, to=2100, textvariable=year_var, width=7).grid(row=0, column=5, padx=5)

        ttk.Label(date_frame, text="Ora:").grid(row=1, column=0, padx=5, pady=(10, 0))
        hour_var = tk.StringVar(value=str(current_dt.hour).zfill(2))
        ttk.Spinbox(date_frame, from_=0, to=23, textvariable=hour_var, width=5, format="%02.0f").grid(
            row=1, column=1, padx=5, pady=(10, 0)
        )
        ttk.Label(date_frame, text=":00").grid(row=1, column=2, sticky=tk.W, pady=(10, 0))

        def _apply_selection():
            try:
                picked = datetime(int(year_var.get()), int(month_var.get()), int(day_var.get()), int(hour_var.get()), 0)
            except Exception:
                messagebox.showwarning("Data non valida", "Seleziona una data e ora valide.", parent=cal_window)
                return

            formatted = picked.strftime("%d/%m/%Y %H:%M")
            if target == "start":
                self.start_dt_var.set(formatted)
            else:
                self.end_dt_var.set(formatted)
            cal_window.destroy()

        action_frame = ttk.Frame(frame)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="OK", command=_apply_selection, width=12).pack(side=tk.LEFT)
        ttk.Button(action_frame, text="Annulla", command=cal_window.destroy, width=12).pack(side=tk.LEFT, padx=(8, 0))

    def _add_molpesis_row(self, pollutant="", mol="", units="g/s"):
        row_data = {
            "pollutant_var": tk.StringVar(value=pollutant),
            "mol_var": tk.StringVar(value=mol),
            "units_var": tk.StringVar(value=units),
            "frame": None,
        }
        self.molpesis_rows.append(row_data)

        if self.molpesis_rows_frame is not None:
            self._create_molpesis_row_widget(row_data)

    def _remove_molpesis_row(self, row_data):
        if row_data not in self.molpesis_rows:
            return

        row_frame = row_data.get("frame")
        if row_frame is not None:
            row_frame.destroy()

        self.molpesis_rows.remove(row_data)

    def _create_molpesis_row_widget(self, row_data):
        row_frame = ttk.Frame(self.molpesis_rows_frame)
        row_frame.pack(fill=tk.X, pady=2)

        pollutant_entry = ttk.Entry(row_frame, textvariable=row_data["pollutant_var"])
        pollutant_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        mol_entry = ttk.Entry(row_frame, textvariable=row_data["mol_var"], width=14)
        mol_entry.pack(side=tk.LEFT, padx=6)

        units_combo = ttk.Combobox(
            row_frame,
            textvariable=row_data["units_var"],
            values=["g/s", "kg/h", "mg/s", "ug/s"],
            width=10,
            state="readonly",
        )
        units_combo.pack(side=tk.LEFT, padx=(0, 6))

        remove_button = ttk.Button(
            row_frame,
            text="Rimuovi",
            width=10,
            command=lambda: self._remove_molpesis_row(row_data),
        )
        remove_button.pack(side=tk.LEFT)

        row_data["frame"] = row_frame

    def _browse_input_db(self):
        selected = filedialog.askopenfilename(parent=self.window, title="Seleziona input_db")
        if selected:
            self.input_db_var.set(selected)

    def _browse_def_sources(self):
        selected = filedialog.askopenfilename(parent=self.window, title="Seleziona def Sources")
        if selected:
            self.def_sources_var.set(selected)

    def _build_payload(self):
        input_db = self.input_db_var.get().strip()
        def_sources = self.def_sources_var.get().strip()

        if not input_db or not def_sources:
            raise ValueError("Seleziona entrambi i file: input_db e def Sources.")

        start_dt = self._parse_datetime(self.start_dt_var.get(), "DATE_START")
        end_dt = self._parse_datetime(self.end_dt_var.get(), "DATE_END")
        if start_dt > end_dt:
            raise ValueError("DATE_START deve essere minore o uguale a DATE_END.")

        molpesis = {}
        for row_data in self.molpesis_rows:
            pollutant = row_data["pollutant_var"].get().strip()
            mol = row_data["mol_var"].get().strip()
            units = row_data["units_var"].get().strip()
            if not pollutant:
                continue
            molpesis[pollutant] = {
                "mol": mol,
                "units": units or "g/s",
            }

        return {
            "input_db": input_db,
            "def_sources": def_sources,
            "source_type": self.source_type_var.get().strip() or "Puntuali",
            "output_name": self.output_name_var.get().strip(),
            "start_dt": start_dt,
            "end_dt": end_dt,
            "molpesis": molpesis,
        }

    def _write_config(self, payload):
        data = {
            "input_db": payload["input_db"],
            "def_sources": payload["def_sources"],
            "source_type": payload["source_type"],
            "output_name": payload["output_name"],
            "DATE_START": payload["start_dt"].strftime("%d/%m/%Y %H:%M"),
            "DATE_END": payload["end_dt"].strftime("%d/%m/%Y %H:%M"),
            "MOLPESIS": payload["molpesis"],
        }

        self.temp_dir.mkdir(parents=True, exist_ok=True)
        with self.config_file.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=4, ensure_ascii=False)

    def _load_existing_config(self):
        if not self.config_file.exists():
            return

        try:
            with self.config_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            return

        self.input_db_var.set(str(data.get("input_db", "")))
        self.def_sources_var.set(str(data.get("def_sources", "")))
        saved_source_type = str(data.get("source_type", "Puntuali")).strip()
        if saved_source_type in ("Puntuali", "Areali"):
            self.source_type_var.set(saved_source_type)

        self.output_name_var.set(str(data.get("output_name", "")))
        loaded_start = str(data.get("DATE_START", "")).strip()
        loaded_end = str(data.get("DATE_END", "")).strip()
        if loaded_start:
            try:
                self.start_dt_var.set(self._parse_datetime(loaded_start, "DATE_START").strftime("%d/%m/%Y %H:%M"))
            except Exception:
                pass
        if loaded_end:
            try:
                self.end_dt_var.set(self._parse_datetime(loaded_end, "DATE_END").strftime("%d/%m/%Y %H:%M"))
            except Exception:
                pass

        loaded_molpesis = data.get("MOLPESIS", {})
        if isinstance(loaded_molpesis, dict):
            for pollutant, values in loaded_molpesis.items():
                if not isinstance(values, dict):
                    continue
                self._loaded_molpesis_rows.append(
                    (
                        str(pollutant),
                        str(values.get("mol", "")),
                        str(values.get("units", "g/s")),
                    )
                )

    def _save_config(self):
        try:
            payload = self._build_payload()
        except ValueError as exc:
            messagebox.showwarning("Dati non validi", str(exc))
            return

        try:
            self._write_config(payload)
        except Exception as exc:
            messagebox.showerror("Errore", f"Impossibile salvare la configurazione:\n{exc}")
            return

        messagebox.showinfo("Successo", "Configurazione Filetti salvata correttamente.")

    def _create(self):
        try:
            payload = self._build_payload()
            self._write_config(payload)
        except ValueError as exc:
            messagebox.showwarning("Dati non validi", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("Errore", f"Impossibile preparare la configurazione:\n{exc}")
            return

        self._run_generation_with_wait(payload)

    def _create_wait_window(self):
        wait_window = tk.Toplevel(self.window)
        wait_window.title("Creazione Filetti")
        wait_window.geometry("360x140")
        wait_window.resizable(False, False)
        wait_window.transient(self.window)
        wait_window.grab_set()
        wait_window.protocol("WM_DELETE_WINDOW", lambda: None)

        frame = ttk.Frame(wait_window, padding="18")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Creazione file in corso...",
            font=("Arial", 10, "bold")
        ).pack(pady=(0, 10))

        progress = ttk.Progressbar(frame, mode="indeterminate", length=300)
        progress.pack(pady=8)
        progress.start(12)

        ttk.Label(
            frame,
            text="Attendere il completamento dell'operazione.",
            font=("Arial", 9)
        ).pack(pady=(8, 0))

        return wait_window, progress

    def _run_generation_with_wait(self, payload):
        wait_window, progress = self._create_wait_window()
        result = {"output_path": None, "error": None}

        def worker():
            try:
                result["output_path"] = self._run_generation(payload)
            except Exception as exc:
                result["error"] = exc

        threading.Thread(target=worker, daemon=True).start()
        self.window.after(100, lambda: self._poll_generation_result(wait_window, progress, result))

    def _poll_generation_result(self, wait_window, progress, result):
        if result["output_path"] is None and result["error"] is None:
            if wait_window.winfo_exists():
                self.window.after(100, lambda: self._poll_generation_result(wait_window, progress, result))
            return

        self._finish_generation(wait_window, progress, result)

    def _finish_generation(self, wait_window, progress, result):
        progress.stop()
        if wait_window.winfo_exists():
            wait_window.grab_release()
            wait_window.destroy()

        if result.get("error") is not None:
            messagebox.showerror("Errore", f"Impossibile creare il file Filetti:\n{result['error']}")
            return

        output_path = result.get("output_path")
        messagebox.showinfo("Successo", f"File creato correttamente:\n{output_path}")

    def _run_generation(self, payload):
        output_dir = self.temp_dir.parent / "Outputs"
        source_type = payload["source_type"]

        if source_type == "Areali":
            from service.filetti_areali_writer import generate_filetti_areali

            return generate_filetti_areali(
                payload["input_db"],
                payload["def_sources"],
                payload["start_dt"],
                payload["end_dt"],
                molpesis=payload["molpesis"],
                output_dir=output_dir,
                output_name=payload["output_name"],
            )

        if source_type == "Puntuali":
            from service.filetti_puntuali_writer import generate_filetti_puntuali

            return generate_filetti_puntuali(
                payload["input_db"],
                payload["def_sources"],
                payload["start_dt"],
                payload["end_dt"],
                molpesis=payload["molpesis"],
                output_dir=output_dir,
                output_name=payload["output_name"],
            )

        raise ValueError(f"Tipo sorgenti non supportato: {source_type}")
