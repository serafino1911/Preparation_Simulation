"""
Finestra configurazione estrazione puntuale su griglia dominio.
"""

import json
import math
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

try:
    import tkintermapview
    MAPVIEW_AVAILABLE = True
except ImportError:
    MAPVIEW_AVAILABLE = False

try:
    from pyproj import CRS, Transformer
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False


class ConfigPuntualeWindow:
    """Dialog per selezionare punti griglia e opzioni estrazione puntuale."""

    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = Path(temp_dir)
        self.window = tk.Toplevel(parent)
        self.window.title("Configurazione Puntuale")
        self.window.geometry("1120x760")
        self.window.transient(parent)
        self.window.grab_set()

        self.result = None
        self.map_widget = None
        self.domain_polygon = None
        self.grid_paths = []
        self.point_markers = []
        self._node_cache = {}
        self._origin_xy_km = None
        self._transformer_to_wgs84 = None
        self._transformer_to_utm = None

        self.domain_info = self._load_domain_info()
        self._parsed_domain = self._parse_domain_values()
        self.post_process_path = self.temp_dir / "post_process.json"
        self.post_process_data = self._load_post_process()

        saved_points = self.post_process_data.get("puntuale_points", [])
        self.selected_points = self._normalize_saved_points(saved_points)

        default_source = str(self.post_process_data.get("puntuale_source_folder", self.post_process_data.get("aggreg_folder", "AGGREG"))).strip() or "AGGREG"
        default_output = str(self.post_process_data.get("puntuale_output_folder", "PUNTUALE")).strip() or "PUNTUALE"
        default_gran = self.post_process_data.get("puntuale_granularity", ["daily", "monthly", "annual"])
        if isinstance(default_gran, str):
            default_gran = [default_gran]
        default_gran = [str(item).lower() for item in default_gran if str(item).strip()]

        self.source_folder_var = tk.StringVar(value=default_source)
        self.output_folder_var = tk.StringVar(value=default_output)
        self.background_var = tk.BooleanVar(value=bool(self.post_process_data.get("puntuale_background", False)))
        self.include_raw_var = tk.BooleanVar(value=bool(self.post_process_data.get("puntuale_include_raw", True)))
        self.daily_var = tk.BooleanVar(value="daily" in default_gran)
        self.monthly_var = tk.BooleanVar(value="monthly" in default_gran)
        self.annual_var = tk.BooleanVar(value="annual" in default_gran)

        self._setup_ui()
        self._refresh_points_list()
        self._refresh_point_markers()

    @classmethod
    def show_dialog(cls, parent, temp_dir):
        dialog = cls(parent, temp_dir)
        dialog.window.wait_window()
        return dialog.result

    def _load_post_process(self):
        if not self.post_process_path.exists():
            return {}
        try:
            with self.post_process_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return {}

    def _load_domain_info(self):
        config_file = self.temp_dir / "domain_config.json"
        if not config_file.exists():
            return None

        try:
            with config_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            return None

        grid_origin = data.get("grid_origin", {})
        grid_step = data.get("grid_step", {})

        return {
            "lat": grid_origin.get("lat"),
            "lon": grid_origin.get("lon"),
            "nx": grid_origin.get("nx"),
            "ny": grid_origin.get("ny"),
            "grid_step": grid_step.get("value"),
            "grid_step_unit": grid_step.get("unit", "km"),
            "zona_utm": data.get("zona_utm", "32N"),
            "vertices": data.get("vertices", {}),
        }

    def _parse_domain_values(self):
        if not self.domain_info:
            return None

        required = ("lat", "lon", "nx", "ny", "grid_step")
        if any(self.domain_info.get(key) is None for key in required):
            return None

        try:
            return {
                "origin_lat": float(self.domain_info["lat"]),
                "origin_lon": float(self.domain_info["lon"]),
                "nx": int(self.domain_info["nx"]),
                "ny": int(self.domain_info["ny"]),
                "step": float(self.domain_info["grid_step"]),
                "unit": self.domain_info.get("grid_step_unit", "km"),
                "zona_utm": self.domain_info.get("zona_utm", "32N"),
            }
        except (TypeError, ValueError):
            return None

    def _build_grid_nodes(self):
        parsed = self._parsed_domain
        if not parsed:
            return {}

        nx = parsed["nx"]
        ny = parsed["ny"]
        step = parsed["step"]
        unit = parsed["unit"]
        origin_lat = parsed["origin_lat"]
        origin_lon = parsed["origin_lon"]
        zona_utm = parsed["zona_utm"]

        if nx <= 0 or ny <= 0 or step <= 0:
            return {}

        nodes = {}

        if unit == "km":
            origin_x_km, origin_y_km = self._lat_lon_to_km(origin_lat, origin_lon)
            if origin_x_km is None or origin_y_km is None:
                return {}

            for ix in range(nx + 1):
                for iy in range(ny + 1):
                    x_km = origin_x_km + (ix * step)
                    y_km = origin_y_km + (iy * step)
                    lat, lon = self._utm_to_lat_lon(zona_utm, x_km, y_km)
                    if lat is None or lon is None:
                        continue
                    nodes[(ix, iy)] = {
                        "ix": ix,
                        "iy": iy,
                        "x_km": x_km,
                        "y_km": y_km,
                        "lat": lat,
                        "lon": lon,
                    }
            return nodes

        lat_step = step
        lon_step = step
        for ix in range(nx + 1):
            for iy in range(ny + 1):
                lat = origin_lat + (iy * lat_step)
                lon = origin_lon + (ix * lon_step)
                x_km, y_km = self._lat_lon_to_km(lat, lon)
                if x_km is None or y_km is None:
                    continue
                nodes[(ix, iy)] = {
                    "ix": ix,
                    "iy": iy,
                    "x_km": x_km,
                    "y_km": y_km,
                    "lat": lat,
                    "lon": lon,
                }

        return nodes

    def _is_valid_grid_index(self, ix, iy):
        parsed = self._parsed_domain
        if not parsed:
            return False
        return 0 <= ix <= parsed["nx"] and 0 <= iy <= parsed["ny"]

    def _get_node(self, ix, iy):
        key = (ix, iy)
        if key in self._node_cache:
            return self._node_cache[key]

        parsed = self._parsed_domain
        if not parsed or not self._is_valid_grid_index(ix, iy):
            return None

        step = parsed["step"]
        unit = parsed["unit"]
        origin_lat = parsed["origin_lat"]
        origin_lon = parsed["origin_lon"]
        zona_utm = parsed["zona_utm"]

        if unit == "km":
            if self._origin_xy_km is None:
                origin_x_km, origin_y_km = self._lat_lon_to_km(origin_lat, origin_lon)
                if origin_x_km is None or origin_y_km is None:
                    return None
                self._origin_xy_km = (origin_x_km, origin_y_km)

            origin_x_km, origin_y_km = self._origin_xy_km
            x_km = origin_x_km + (ix * step)
            y_km = origin_y_km + (iy * step)
            lat, lon = self._utm_to_lat_lon(zona_utm, x_km, y_km)
            if lat is None or lon is None:
                return None
        else:
            lat = origin_lat + (iy * step)
            lon = origin_lon + (ix * step)
            x_km, y_km = self._lat_lon_to_km(lat, lon)
            if x_km is None or y_km is None:
                return None

        node = {
            "ix": ix,
            "iy": iy,
            "x_km": x_km,
            "y_km": y_km,
            "lat": lat,
            "lon": lon,
        }
        self._node_cache[key] = node
        return node

    def _normalize_saved_points(self, points):
        if not isinstance(points, list):
            return []

        normalized = []
        used = set()
        for point in points:
            if not isinstance(point, dict):
                continue
            try:
                ix = int(point.get("ix"))
                iy = int(point.get("iy"))
            except Exception:
                continue
            key = (ix, iy)
            if key in used or not self._is_valid_grid_index(ix, iy):
                continue
            used.add(key)
            entry = self._build_point_entry(ix, iy, len(normalized) + 1)
            if entry:
                normalized.append(entry)

        return normalized

    def _build_point_entry(self, ix, iy, index):
        node = self._get_node(ix, iy)
        if not node:
            return None
        return {
            "point_id": f"P{index:02d}",
            "ix": ix,
            "iy": iy,
            "x_km": round(node["x_km"], 6),
            "y_km": round(node["y_km"], 6),
            "lat": round(node["lat"], 8),
            "lon": round(node["lon"], 8),
        }

    def _setup_ui(self):
        main_frame = ttk.Frame(self.window, padding="12")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(1, weight=1)

        top_frame = ttk.LabelFrame(main_frame, text="Opzioni Estrazione", padding="10")
        top_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        top_frame.columnconfigure(1, weight=1)

        ttk.Label(top_frame, text="Cartella sorgente:").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Entry(top_frame, textvariable=self.source_folder_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=4)

        ttk.Label(top_frame, text="Cartella output:").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Entry(top_frame, textvariable=self.output_folder_var, width=40).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=4)

        checks_frame = ttk.Frame(top_frame)
        checks_frame.grid(row=0, column=2, rowspan=2, padx=(16, 0), sticky=tk.W)

        ttk.Checkbutton(checks_frame, text="Output RAW orari", variable=self.include_raw_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(checks_frame, text="Granularità aggregate:").grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
        ttk.Checkbutton(checks_frame, text="Daily", variable=self.daily_var).grid(row=2, column=0, sticky=tk.W)
        ttk.Checkbutton(checks_frame, text="Monthly", variable=self.monthly_var).grid(row=3, column=0, sticky=tk.W)
        ttk.Checkbutton(checks_frame, text="Annual", variable=self.annual_var).grid(row=4, column=0, sticky=tk.W)
        ttk.Checkbutton(
            checks_frame,
            text="Esegui in background con bsub -q pmten",
            variable=self.background_var
        ).grid(row=5, column=0, sticky=tk.W, pady=(8, 0))

        left_frame = ttk.LabelFrame(main_frame, text="Punti Selezionati", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 6))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)

        self.points_listbox = tk.Listbox(left_frame, font=("Consolas", 10), height=18)
        self.points_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 8))

        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))

        ttk.Button(buttons_frame, text="➕ Aggiungi da griglia", command=self._prompt_add_by_index).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(buttons_frame, text="🗺️ Aggiungi da mappa", command=self._start_map_pick).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons_frame, text="🗑️ Rimuovi selezionato", command=self._remove_selected).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons_frame, text="♻️ Pulisci tutti", command=self._clear_points).pack(side=tk.LEFT, padx=6)

        right_frame = ttk.LabelFrame(main_frame, text="Dominio e Griglia", padding="10")
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(6, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        if MAPVIEW_AVAILABLE and self.domain_info:
            try:
                self.map_widget = tkintermapview.TkinterMapView(right_frame, corner_radius=0)
                self.map_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                # Delay heavy map/grid initialization until window is rendered.
                self.window.after_idle(self._initialize_map_with_domain)
            except Exception:
                self.map_widget = None

        if not self.map_widget:
            ttk.Label(
                right_frame,
                text="Mappa non disponibile.\nUsa inserimento indice i,j.",
                foreground="gray"
            ).grid(row=0, column=0)

        map_help = ttk.Label(
            right_frame,
            text="Click mappa: selezione nodo griglia più vicino",
            foreground="#555555"
        )
        map_help.grid(row=1, column=0, sticky=tk.W, pady=(8, 0))

        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(action_frame, text="✅ Conferma", command=self._on_confirm, width=18).pack(side=tk.LEFT, padx=8)
        ttk.Button(action_frame, text="❌ Annulla", command=self._on_cancel, width=18).pack(side=tk.LEFT, padx=8)

        if not self.domain_info:
            messagebox.showwarning(
                "Attenzione",
                "domain_config.json non trovato o non valido.\n"
                "La selezione punti richiede una griglia dominio valida.",
                parent=self.window
            )

    def _refresh_points_list(self):
        self.points_listbox.delete(0, tk.END)
        for point in self.selected_points:
            self.points_listbox.insert(
                tk.END,
                f"{point['point_id']}  i={point['ix']:>3}  j={point['iy']:>3}  "
                f"X={point['x_km']:.3f}  Y={point['y_km']:.3f}"
            )

    def _refresh_point_markers(self):
        if not self.map_widget:
            return

        for marker in self.point_markers:
            try:
                marker.delete()
            except Exception:
                pass
        self.point_markers = []

        for point in self.selected_points:
            marker = self.map_widget.set_marker(
                point["lat"],
                point["lon"],
                text=f"{point['point_id']} (i={point['ix']}, j={point['iy']})",
                marker_color_circle="#C62828",
                marker_color_outside="#8E0000",
            )
            self.point_markers.append(marker)

    def _renumber_points(self):
        for idx, point in enumerate(self.selected_points, start=1):
            point["point_id"] = f"P{idx:02d}"

    def _add_point(self, ix, iy):
        if not self._is_valid_grid_index(ix, iy):
            messagebox.showerror("Errore", "Indice griglia fuori dominio.", parent=self.window)
            return

        if any(point["ix"] == ix and point["iy"] == iy for point in self.selected_points):
            return

        point = self._build_point_entry(ix, iy, len(self.selected_points) + 1)
        if not point:
            messagebox.showerror("Errore", "Impossibile calcolare coordinate per il nodo selezionato.", parent=self.window)
            return
        self.selected_points.append(point)
        self._refresh_points_list()
        self._refresh_point_markers()

    def _prompt_add_by_index(self):
        if not self._parsed_domain:
            messagebox.showerror("Errore", "Griglia dominio non disponibile.", parent=self.window)
            return

        dialog = tk.Toplevel(self.window)
        dialog.title("Aggiungi Punto")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()

        ttk.Label(dialog, text="Indice i:").grid(row=0, column=0, padx=10, pady=(10, 6), sticky=tk.W)
        ttk.Label(dialog, text="Indice j:").grid(row=1, column=0, padx=10, pady=6, sticky=tk.W)

        i_var = tk.StringVar()
        j_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=i_var, width=12).grid(row=0, column=1, padx=10, pady=(10, 6))
        ttk.Entry(dialog, textvariable=j_var, width=12).grid(row=1, column=1, padx=10, pady=6)

        def _confirm():
            try:
                ix = int(i_var.get().strip())
                iy = int(j_var.get().strip())
            except Exception:
                messagebox.showerror("Errore", "Inserire indici interi validi.", parent=dialog)
                return
            self._add_point(ix, iy)
            dialog.destroy()

        ttk.Button(dialog, text="OK", command=_confirm).grid(row=2, column=0, padx=10, pady=10)
        ttk.Button(dialog, text="Annulla", command=dialog.destroy).grid(row=2, column=1, padx=10, pady=10)

    def _start_map_pick(self):
        if not self.map_widget:
            messagebox.showinfo("Info", "Mappa non disponibile in questa installazione.", parent=self.window)
            return

        try:
            self.map_widget.add_left_click_map_command(None)
        except Exception:
            pass

        def on_click(coords):
            lat, lon = coords
            nearest = self._find_nearest_node(lat, lon)
            if nearest is None:
                return
            self._add_point(nearest[0], nearest[1])

        self.map_widget.add_left_click_map_command(on_click)
        messagebox.showinfo(
            "Selezione Punto",
            "Clicca sulla mappa per aggiungere il nodo griglia più vicino.\n"
            "Puoi cliccare più volte per aggiungere più punti.",
            parent=self.window
        )

    def _find_nearest_node(self, lat, lon):
        parsed = self._parsed_domain
        if not parsed:
            return None

        nx = parsed["nx"]
        ny = parsed["ny"]
        step = parsed["step"]
        unit = parsed["unit"]
        origin_lat = parsed["origin_lat"]
        origin_lon = parsed["origin_lon"]

        if step <= 0:
            return None

        if unit == "km":
            if self._origin_xy_km is None:
                origin_x_km, origin_y_km = self._lat_lon_to_km(origin_lat, origin_lon)
                if origin_x_km is None or origin_y_km is None:
                    return None
                self._origin_xy_km = (origin_x_km, origin_y_km)

            x_km, y_km = self._lat_lon_to_km(lat, lon)
            if x_km is None or y_km is None:
                return None

            origin_x_km, origin_y_km = self._origin_xy_km
            ix = int(round((x_km - origin_x_km) / step))
            iy = int(round((y_km - origin_y_km) / step))
        else:
            ix = int(round((lon - origin_lon) / step))
            iy = int(round((lat - origin_lat) / step))

        ix = max(0, min(nx, ix))
        iy = max(0, min(ny, iy))
        return (ix, iy)

    def _remove_selected(self):
        selection = self.points_listbox.curselection()
        if not selection:
            return
        index = int(selection[0])
        if 0 <= index < len(self.selected_points):
            self.selected_points.pop(index)
            self._renumber_points()
            self._refresh_points_list()
            self._refresh_point_markers()

    def _clear_points(self):
        self.selected_points = []
        self._refresh_points_list()
        self._refresh_point_markers()

    def _collect_granularities(self):
        values = []
        if self.daily_var.get():
            values.append("daily")
        if self.monthly_var.get():
            values.append("monthly")
        if self.annual_var.get():
            values.append("annual")
        return values

    def _on_confirm(self):
        source_folder = self.source_folder_var.get().strip()
        output_folder = self.output_folder_var.get().strip()

        if not source_folder:
            messagebox.showerror("Errore", "La cartella sorgente non può essere vuota.", parent=self.window)
            return

        if not output_folder:
            messagebox.showerror("Errore", "La cartella output non può essere vuota.", parent=self.window)
            return

        if not self.selected_points:
            messagebox.showerror("Errore", "Seleziona almeno un punto dalla griglia.", parent=self.window)
            return

        payload = {
            "puntuale_source_folder": source_folder,
            "puntuale_output_folder": output_folder,
            "puntuale_background": bool(self.background_var.get()),
            "puntuale_include_raw": bool(self.include_raw_var.get()),
            "puntuale_granularity": self._collect_granularities(),
            "puntuale_timezone_mode": "keep_filename",
            "puntuale_points": self.selected_points,
        }

        self._save_post_process(payload)
        self.result = payload
        self.window.destroy()

    def _save_post_process(self, payload):
        previous = {}
        if self.post_process_path.exists():
            try:
                with self.post_process_path.open("r", encoding="utf-8") as handle:
                    previous = json.load(handle)
            except Exception:
                previous = {}

        previous.update(payload)

        with self.post_process_path.open("w", encoding="utf-8") as handle:
            json.dump(previous, handle, indent=2, ensure_ascii=False)

    def _on_cancel(self):
        self.result = None
        self.window.destroy()

    def _initialize_map_with_domain(self):
        if not self.map_widget or not self.domain_info:
            return

        vertices = self.domain_info.get("vertices", {})
        if vertices:
            try:
                rectangle_coords = [
                    (vertices["NW"]["lat"], vertices["NW"]["lon"]),
                    (vertices["NE"]["lat"], vertices["NE"]["lon"]),
                    (vertices["SE"]["lat"], vertices["SE"]["lon"]),
                    (vertices["SW"]["lat"], vertices["SW"]["lon"]),
                ]
                self.domain_polygon = self.map_widget.set_polygon(
                    rectangle_coords,
                    fill_color=None,
                    outline_color="#0D47A1",
                    border_width=2,
                    name="domain_boundary",
                )
                center_lat = sum(v["lat"] for v in vertices.values()) / 4
                center_lon = sum(v["lon"] for v in vertices.values()) / 4
                self.map_widget.set_position(center_lat, center_lon)
                self.map_widget.set_zoom(11)
            except Exception:
                pass
        elif self.domain_info.get("lat") is not None and self.domain_info.get("lon") is not None:
            self.map_widget.set_position(self.domain_info["lat"], self.domain_info["lon"])
            self.map_widget.set_zoom(12)

        self._draw_grid_overlay()

    def _iter_with_last(self, limit, stride):
        if limit < 0:
            return []
        if stride <= 1:
            return list(range(limit + 1))
        values = list(range(0, limit + 1, stride))
        if not values or values[-1] != limit:
            values.append(limit)
        return values

    def _draw_grid_overlay(self):
        if not self.map_widget:
            return

        for path in self.grid_paths:
            try:
                path.delete()
            except Exception:
                pass
        self.grid_paths = []

        parsed = self._parse_domain_values()
        if not parsed:
            return

        origin_lat = parsed["origin_lat"]
        origin_lon = parsed["origin_lon"]
        nx = parsed["nx"]
        ny = parsed["ny"]
        step = parsed["step"]
        unit = parsed["unit"]
        zona_utm = parsed["zona_utm"]

        if nx <= 0 or ny <= 0 or step <= 0:
            return

        max_lines = max(nx, ny)
        if max_lines <= 80:
            stride = 1
        elif max_lines <= 200:
            stride = 2
        elif max_lines <= 500:
            stride = 5
        else:
            stride = 10

        lines = []

        if unit == "km":
            origin_x_km, origin_y_km = self._lat_lon_to_km(origin_lat, origin_lon)
            if origin_x_km is not None and origin_y_km is not None:
                max_x = origin_x_km + (nx * step)
                max_y = origin_y_km + (ny * step)

                for ix in self._iter_with_last(nx, stride):
                    current_x = origin_x_km + (ix * step)
                    start = self._utm_to_lat_lon(zona_utm, current_x, origin_y_km)
                    end = self._utm_to_lat_lon(zona_utm, current_x, max_y)
                    if None not in start and None not in end:
                        lines.append([start, end])

                for iy in self._iter_with_last(ny, stride):
                    current_y = origin_y_km + (iy * step)
                    start = self._utm_to_lat_lon(zona_utm, origin_x_km, current_y)
                    end = self._utm_to_lat_lon(zona_utm, max_x, current_y)
                    if None not in start and None not in end:
                        lines.append([start, end])

        if not lines:
            lat_step, lon_step = self._km_to_degree_steps(step, origin_lat)
            max_lat = origin_lat + (ny * lat_step)
            max_lon = origin_lon + (nx * lon_step)

            for ix in self._iter_with_last(nx, stride):
                current_lon = origin_lon + (ix * lon_step)
                lines.append([(origin_lat, current_lon), (max_lat, current_lon)])

            for iy in self._iter_with_last(ny, stride):
                current_lat = origin_lat + (iy * lat_step)
                lines.append([(current_lat, origin_lon), (current_lat, max_lon)])

        for line_coords in lines:
            path = self.map_widget.set_path(line_coords, color="#1976D2", width=1)
            self.grid_paths.append(path)

    def _km_to_degree_steps(self, step_km, reference_lat):
        lat_step = step_km / 110.574
        cos_lat = abs(math.cos(math.radians(reference_lat)))
        if cos_lat < 1e-6:
            cos_lat = 1e-6
        lon_step = step_km / (111.320 * cos_lat)
        return lat_step, lon_step

    def _utm_to_lat_lon(self, zona_utm, km_x, km_y):
        if not PYPROJ_AVAILABLE or not zona_utm:
            return None, None

        try:
            if not self._ensure_transformers(zona_utm):
                return None, None
            lon, lat = self._transformer_to_wgs84.transform(km_x * 1000.0, km_y * 1000.0)
            return lat, lon
        except Exception:
            return None, None

    def _lat_lon_to_km(self, lat, lon):
        if not PYPROJ_AVAILABLE or not self.domain_info:
            return None, None

        zona_utm = self.domain_info.get("zona_utm", "32N")
        try:
            if not self._ensure_transformers(zona_utm):
                return None, None
            utm_x, utm_y = self._transformer_to_utm.transform(lon, lat)
            return utm_x / 1000.0, utm_y / 1000.0
        except Exception:
            return None, None

    def _ensure_transformers(self, zona_utm):
        if not PYPROJ_AVAILABLE or not zona_utm:
            return False

        if self._transformer_to_wgs84 is not None and self._transformer_to_utm is not None:
            return True

        try:
            utm_zone = int(zona_utm[:-1])
            hemisphere = "north" if zona_utm[-1].upper() == "N" else "south"

            crs_wgs84 = CRS.from_epsg(4326)
            crs_utm = CRS.from_dict({
                "proj": "utm",
                "zone": utm_zone,
                "hemisphere": hemisphere,
                "ellps": "WGS84",
            })

            self._transformer_to_wgs84 = Transformer.from_crs(crs_utm, crs_wgs84, always_xy=True)
            self._transformer_to_utm = Transformer.from_crs(crs_wgs84, crs_utm, always_xy=True)
            return True
        except Exception:
            self._transformer_to_wgs84 = None
            self._transformer_to_utm = None
            return False
