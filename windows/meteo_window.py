"""
Finestra per configurazione ed esecuzione Meteo.
"""

import json
import math
import os
import threading
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import ttk, messagebox

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

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False


class MeteoWindow:
    """Finestra dedicata a configurazione Meteo e azioni operative."""

    def __init__(self, parent, temp_dir, farm_controller=None):
        self.parent = parent
        self.temp_dir = Path(temp_dir)
        self.farm_controller = farm_controller
        self.window = tk.Toplevel(parent)
        self.window.title("Configurazione Meteo")
        self.window.geometry("860x740")
        self.window.transient(parent)

        self.config_dir = Path("temp_config")
        self.config_path = self.config_dir / "meteo_config.json"
        self.local_inp_dir = self.temp_dir.parent / "METEO_INP"
        self.points = []
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

        self.output_folder = tk.StringVar(value="METEODATA")
        self.convert_var = tk.BooleanVar(value=True)
        self.src_crs = tk.StringVar(value="EPSG:32632")
        self.dst_crs = tk.StringVar(value="EPSG:4326")
        self.calmet_data = tk.StringVar(value="CALMETDATA")
        self.prtmet = tk.StringVar(value="PRTMET_v4.34/PRTMET")
        self.date_start = tk.StringVar(value="2023-01-01")
        self.date_end = tk.StringVar(value="2024-02-01")
        self.link_file = tk.BooleanVar(value=False)
        self.run_background = tk.BooleanVar(value=True)

        self._load_defaults_and_existing()
        self._setup_ui()
        self._refresh_points_view()
        self._refresh_point_markers()

    def _setup_ui(self):
        main = ttk.Frame(self.window, padding="12")
        main.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=3)

        title = ttk.Label(main, text="Configurazione Meteo", font=("Arial", 12, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))

        config_frame = ttk.LabelFrame(main, text="Parametri Meteo", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        config_frame.columnconfigure(1, weight=1)
        config_frame.columnconfigure(3, weight=1)

        ttk.Label(config_frame, text="OUTPUT_FOLDER:").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(config_frame, textvariable=self.output_folder).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=4, padx=(6, 14))

        ttk.Label(config_frame, text="SRC_CRS:").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Entry(config_frame, textvariable=self.src_crs).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=4, padx=(6, 14))

        ttk.Label(config_frame, text="DST_CRS:").grid(row=1, column=2, sticky=tk.W, pady=4)
        ttk.Entry(config_frame, textvariable=self.dst_crs).grid(row=1, column=3, sticky=(tk.W, tk.E), pady=4, padx=(6, 0))

        ttk.Label(config_frame, text="CALMET_DATA:").grid(row=2, column=0, sticky=tk.W, pady=4)
        ttk.Entry(config_frame, textvariable=self.calmet_data).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=4, padx=(6, 14))

        ttk.Label(config_frame, text="PRTMET:").grid(row=2, column=2, sticky=tk.W, pady=4)
        ttk.Entry(config_frame, textvariable=self.prtmet).grid(row=2, column=3, sticky=(tk.W, tk.E), pady=4, padx=(6, 0))

        ttk.Label(config_frame, text="DATE_START:").grid(row=3, column=0, sticky=tk.W, pady=4)
        ttk.Entry(config_frame, textvariable=self.date_start).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=4, padx=(6, 14))

        ttk.Label(config_frame, text="DATE_END:").grid(row=3, column=2, sticky=tk.W, pady=4)
        ttk.Entry(config_frame, textvariable=self.date_end).grid(row=3, column=3, sticky=(tk.W, tk.E), pady=4, padx=(6, 0))

        ttk.Checkbutton(config_frame, text="CONVERT", variable=self.convert_var).grid(row=4, column=0, sticky=tk.W, pady=4)
        ttk.Checkbutton(config_frame, text="LINK_FILE", variable=self.link_file).grid(row=4, column=1, sticky=tk.W, pady=4)

        ttk.Checkbutton(config_frame, text="Run in background (bsub -q pmten)", variable=self.run_background).grid(
            row=5, column=0, columnspan=4, sticky=tk.W, pady=(8, 2)
        )

        points_frame = ttk.LabelFrame(main, text="POINTS (selezione come Launch Puntuale)", padding="10")
        points_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 8), padx=(0, 6))
        points_frame.columnconfigure(0, weight=1)
        points_frame.rowconfigure(1, weight=1)
        main.rowconfigure(2, weight=1)

        points_btn_row = ttk.Frame(points_frame)
        points_btn_row.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 6))
        ttk.Button(points_btn_row, text="Importa da Puntuale", command=self._select_points_from_puntuale).pack(side=tk.LEFT)
        ttk.Button(points_btn_row, text="Aggiungi da mappa", command=self._start_map_pick).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(points_btn_row, text="Pulisci punto", command=self._clear_single_point).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(points_btn_row, text="Pulisci punti", command=self._clear_points).pack(side=tk.LEFT, padx=(8, 0))

        self.points_list = tk.Listbox(points_frame, height=12, exportselection=False)
        self.points_list.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        map_frame = ttk.LabelFrame(main, text="Mappa Dominio", padding="10")
        map_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 8), padx=(6, 0))
        map_frame.columnconfigure(0, weight=1)
        map_frame.rowconfigure(0, weight=1)

        if MAPVIEW_AVAILABLE and self.domain_info:
            try:
                self.map_widget = tkintermapview.TkinterMapView(map_frame, corner_radius=0)
                self.map_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                self.window.after_idle(self._initialize_map_with_domain)
            except Exception:
                self.map_widget = None

        if not self.map_widget:
            ttk.Label(
                map_frame,
                text="Mappa non disponibile.\nUsa Importa da Puntuale oppure installa tkintermapview.",
                foreground="gray"
            ).grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        actions = ttk.LabelFrame(main, text="Azioni Meteo", padding="10")
        actions.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        for idx in range(5):
            actions.columnconfigure(idx, weight=1)

        ttk.Button(actions, text="Salva Config", command=self.save_config).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=4)
        ttk.Button(actions, text="Create INP", command=self.create_inp).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=4)
        ttk.Button(actions, text="Load INP", command=self.load_inp).grid(row=0, column=2, sticky=(tk.W, tk.E), padx=4)
        ttk.Button(actions, text="Launch Meteo", command=self.launch_meteo).grid(row=0, column=3, sticky=(tk.W, tk.E), padx=4)
        ttk.Button(actions, text="Chiudi", command=self.window.destroy).grid(row=0, column=4, sticky=(tk.W, tk.E), padx=4)

    def _log(self, message):
        if self.farm_controller and hasattr(self.farm_controller, "log_message"):
            self.farm_controller.log_message(message)

    def _load_json_file(self, file_path):
        if not file_path.exists():
            return {}
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return {}

    def _parse_date_tuple(self, value, fallback):
        if isinstance(value, (list, tuple)) and len(value) == 3:
            try:
                return int(value[0]), int(value[1]), int(value[2])
            except Exception:
                return fallback
        if isinstance(value, str):
            chunks = value.strip().split("-")
            if len(chunks) == 3:
                try:
                    return int(chunks[0]), int(chunks[1]), int(chunks[2])
                except Exception:
                    return fallback
        return fallback

    def _tuple_to_date_str(self, date_tuple):
        year, month, day = date_tuple
        return f"{year:04d}-{month:02d}-{day:02d}"

    def _date_str_to_tuple(self, value):
        parsed = self._parse_date_tuple(value, None)
        if not parsed:
            raise ValueError("Formato data non valido. Usa YYYY-MM-DD")
        return parsed

    def _load_defaults_and_existing(self):
        temporal_cfg = self._load_json_file(self.temp_dir / "temporal_config.json")
        calmet_cfg = self._load_json_file(self.temp_dir / "calmet_config.json")

        default_start = self._parse_date_tuple(temporal_cfg.get("start_date", "2023-01-01"), (2023, 1, 1))
        default_end = self._parse_date_tuple(temporal_cfg.get("end_date", "2024-02-01"), (2024, 2, 1))
        self.date_start.set(self._tuple_to_date_str(default_start))
        self.date_end.set(self._tuple_to_date_str(default_end))

        calmet_data_default = str(calmet_cfg.get("calmet_data", "CALMETDATA")).strip() or "CALMETDATA"
        self.calmet_data.set(calmet_data_default)

        existing = self._load_json_file(self.config_path)
        if not existing:
            return

        self.output_folder.set(str(existing.get("OUTPUT_FOLDER", existing.get("METEODATA", self.output_folder.get()))))
        self.convert_var.set(bool(existing.get("CONVERT", self.convert_var.get())))
        self.src_crs.set(str(existing.get("SRC_CRS", self.src_crs.get())))
        self.dst_crs.set(str(existing.get("DST_CRS", self.dst_crs.get())))
        self.calmet_data.set(str(existing.get("CALMET_DATA", self.calmet_data.get())))
        self.prtmet.set(str(existing.get("PRTMET", existing.get("INPUT_FOLDER", self.prtmet.get()))))
        self.link_file.set(bool(existing.get("LINK_FILE", self.link_file.get())))
        self.run_background.set(bool(existing.get("RUN_BACKGROUND", self.run_background.get())))

        start_tuple = self._parse_date_tuple(existing.get("DATE_START"), default_start)
        end_tuple = self._parse_date_tuple(existing.get("DATE_END"), default_end)
        self.date_start.set(self._tuple_to_date_str(start_tuple))
        self.date_end.set(self._tuple_to_date_str(end_tuple))

        points = existing.get("POINTS", [])
        if isinstance(points, list):
            self.points = self._normalize_loaded_points(points)

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

    def _normalize_loaded_points(self, points):
        normalized = []
        for point in points:
            if not isinstance(point, dict):
                continue

            try:
                ix = int(point.get("ix"))
                iy = int(point.get("iy"))
            except Exception:
                continue

            if not self._is_valid_grid_index(ix, iy):
                continue

            built = self._build_point_entry(ix, iy, len(normalized) + 1)
            if built:
                normalized.append(built)

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

    def _collect_config(self):
        start_tuple = self._date_str_to_tuple(self.date_start.get())
        end_tuple = self._date_str_to_tuple(self.date_end.get())
        effective_points = self.points if self.points else [self._get_full_field_point()]

        config = {
            "OUTPUT_FOLDER": self.output_folder.get().strip() or "METEODATA",
            "CONVERT": bool(self.convert_var.get()),
            "SRC_CRS": self.src_crs.get().strip() or "EPSG:32632",
            "DST_CRS": self.dst_crs.get().strip() or "EPSG:4326",
            "CALMET_DATA": self.calmet_data.get().strip() or "CALMETDATA",
            "PRTMET": self.prtmet.get().strip() or "PRTMET_v4.34/PRTMET",
            "DATE_START": list(start_tuple),
            "DATE_END": list(end_tuple),
            "LINK_FILE": bool(self.link_file.get()),
            "POINTS": effective_points,
            "RUN_BACKGROUND": bool(self.run_background.get()),
        }
        return config

    def _get_full_field_point(self):
        point = self._build_point_entry(0, 0, 1)
        if point:
            return point
        return {
            "point_id": "P01",
            "ix": 0,
            "iy": 0,
            "x_km": 0.0,
            "y_km": 0.0,
            "lat": None,
            "lon": None,
        }

    def save_config(self):
        try:
            config = self._collect_config()
        except Exception as exc:
            messagebox.showerror("Errore", f"Configurazione non valida: {exc}")
            return False

        self.config_dir.mkdir(exist_ok=True)
        try:
            with self.config_path.open("w", encoding="utf-8") as handle:
                json.dump(config, handle, indent=2, ensure_ascii=False)
        except Exception as exc:
            messagebox.showerror("Errore", f"Impossibile salvare meteo_config.json: {exc}")
            return False

        self._log("Configurazione Meteo salvata in temp_config/meteo_config.json")
        messagebox.showinfo("Successo", "Configurazione Meteo salvata.")
        return True

    def _refresh_points_view(self):
        self.points_list.delete(0, tk.END)
        if not self.points:
            self.points_list.insert(tk.END, "Nessun punto selezionato: uso 0,0 (tutto campo)")
            return

        for idx, point in enumerate(self.points, start=1):
            point_id = point.get("point_id", f"P{idx:02d}")
            ix = point.get("ix", "?")
            iy = point.get("iy", "?")
            lat = point.get("lat", "?")
            lon = point.get("lon", "?")
            self.points_list.insert(tk.END, f"{point_id}: ix={ix}, iy={iy}, lat={lat}, lon={lon}")

    def _refresh_point_markers(self):
        if not self.map_widget:
            return

        for marker in self.point_markers:
            try:
                marker.delete()
            except Exception:
                pass
        self.point_markers = []

        for point in self.points:
            lat = point.get("lat")
            lon = point.get("lon")
            if lat is None or lon is None:
                continue
            marker = self.map_widget.set_marker(
                lat,
                lon,
                text=f"{point['point_id']} (i={point['ix']}, j={point['iy']})",
                marker_color_circle="#C62828",
                marker_color_outside="#8E0000",
            )
            self.point_markers.append(marker)

    def _renumber_points(self):
        for idx, point in enumerate(self.points, start=1):
            point["point_id"] = f"P{idx:02d}"

    def _add_point(self, ix, iy):
        if not self._is_valid_grid_index(ix, iy):
            messagebox.showerror("Errore", "Indice griglia fuori dominio.", parent=self.window)
            return

        if any(point["ix"] == ix and point["iy"] == iy for point in self.points):
            return

        point = self._build_point_entry(ix, iy, len(self.points) + 1)
        if not point:
            messagebox.showerror("Errore", "Impossibile calcolare coordinate per il nodo selezionato.", parent=self.window)
            return

        self.points.append(point)
        self._refresh_points_view()
        self._refresh_point_markers()

    def _clear_single_point(self):
        if not self.points:
            return

        selection = self.points_list.curselection()
        if not selection:
            messagebox.showinfo("Info", "Seleziona un punto dalla lista da rimuovere.", parent=self.window)
            return

        index = int(selection[0])
        if 0 <= index < len(self.points):
            self.points.pop(index)
            self._renumber_points()
            self._refresh_points_view()
            self._refresh_point_markers()

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

    def _select_points_from_puntuale(self):
        try:
            from windows.config_puntuale_window import ConfigPuntualeWindow
        except Exception as exc:
            messagebox.showerror("Errore", f"Impossibile aprire la selezione punti: {exc}")
            return

        dialog_result = ConfigPuntualeWindow.show_dialog(self.window, self.temp_dir)
        if not dialog_result:
            return

        selected = dialog_result.get("puntuale_points", [])
        if not isinstance(selected, list):
            messagebox.showwarning("Attenzione", "Formato punti non valido.")
            return

        self.points = selected
        self._renumber_points()
        self._refresh_points_view()
        self._refresh_point_markers()
        self._log(f"Punti Meteo aggiornati: {len(self.points)}")

    def _clear_points(self):
        self.points = []
        self._refresh_points_view()
        self._refresh_point_markers()

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

    def _build_points_dict(self):
        if not self.points:
            return {"E1": [0, 0]}

        points_dict = {}
        for idx, point in enumerate(self.points, start=1):
            label = f"E{idx}"
            try:
                ix = int(point.get("ix"))
                iy = int(point.get("iy"))
            except Exception:
                continue
            points_dict[label] = [ix, iy]
        return points_dict

    def _get_prtmet_template_path(self):
        return (
            Path(__file__).resolve().parent.parent
            / "Working_Files"
            / "prtmet_bp.txt"
        )

    def _iter_daily_dates(self, start_tuple, end_tuple):
        start_dt = datetime(start_tuple[0], start_tuple[1], start_tuple[2], 0, 0, 0)
        end_dt = datetime(end_tuple[0], end_tuple[1], end_tuple[2], 0, 0, 0)
        current = start_dt
        while current <= end_dt:
            yield current
            current += timedelta(days=1)

    def _render_prtmet_inp(self, template_text, current_date, point_key, point_ij):
        date_s = current_date.strftime("%Y%m%d")
        year_s = current_date.strftime("%Y")
        month_s = current_date.strftime("%m")
        day_s = current_date.strftime("%d")
        calmet_file = f"calmet_{date_s}.dat"
        run_lst = f"prtmet_{date_s}_{point_key}.lst"
        output = f"meteo_{date_s}_{point_key}.dat"

        content = template_text
        content = content.replace("[calmet.dat]", calmet_file)
        content = content.replace("[prtmet.lst]", run_lst)
        content = content.replace("[output.dat]", output)
        content = content.replace("[year_in]", year_s)
        content = content.replace("[month_in]", month_s)
        content = content.replace("[day_in]", day_s)
        content = content.replace("[hour_in]", "00")
        content = content.replace("[year_out]", year_s)
        content = content.replace("[month_out]", month_s)
        content = content.replace("[day_out]", day_s)
        content = content.replace("[hour_out]", "23")
        content = content.replace("[point_x]", str(point_ij[0]))
        content = content.replace("[point_y]", str(point_ij[1]))
        return content

    def create_inp(self, show_message=True):
        try:
            config = self._collect_config()
        except Exception as exc:
            messagebox.showerror("Errore", f"Configurazione non valida: {exc}")
            return None

        points_dict = self._build_points_dict()

        template_path = self._get_prtmet_template_path()
        if not template_path.exists():
            messagebox.showerror(
                "Errore",
                f"Template PRTMET non trovato:\n{template_path}"
            )
            return None

        try:
            template_text = template_path.read_text(encoding="utf-8")
        except Exception as exc:
            messagebox.showerror("Errore", f"Impossibile leggere il template PRTMET: {exc}")
            return None

        self.local_inp_dir.mkdir(parents=True, exist_ok=True)
        config["POINTS_DICT"] = points_dict

        points_file = self.local_inp_dir / "points.json"
        manifest_file = self.local_inp_dir / "manifest.json"
        daily_inp_dir = self.local_inp_dir / "daily_inp"
        daily_inp_dir.mkdir(parents=True, exist_ok=True)

        for old_file in daily_inp_dir.glob("*.inp"):
            try:
                old_file.unlink()
            except Exception:
                pass

        try:
            with points_file.open("w", encoding="utf-8") as handle:
                json.dump(points_dict, handle, indent=2, ensure_ascii=False)

            generated_files = []
            start_tuple = tuple(config["DATE_START"])
            end_tuple = tuple(config["DATE_END"])

            for current_date in self._iter_daily_dates(start_tuple, end_tuple):
                for point_key, point_ij in points_dict.items():
                    inp_content = self._render_prtmet_inp(template_text, current_date, point_key, point_ij)
                    inp_name = f"prtmet_{current_date.strftime('%Y%m%d')}_{point_key}.inp"
                    inp_path = daily_inp_dir / inp_name
                    inp_path.write_text(inp_content, encoding="utf-8")
                    generated_files.append(inp_name)

            manifest = {
                "count": len(generated_files),
                "date_start": config["DATE_START"],
                "date_end": config["DATE_END"],
                "points": points_dict,
                "files": generated_files,
            }
            with manifest_file.open("w", encoding="utf-8") as handle:
                json.dump(manifest, handle, indent=2, ensure_ascii=False)
        except Exception as exc:
            messagebox.showerror("Errore", f"Impossibile creare file INP Meteo: {exc}")
            return None

        self._log(f"Create INP Meteo completato: {len(generated_files)} file in METEO_INP/daily_inp")
        if show_message:
            messagebox.showinfo(
                "Successo",
                "File Meteo creati con logica giornaliera per punto (00-23).\n\n"
                f"Totale file .inp: {len(generated_files)}\n"
                f"Cartella: {daily_inp_dir}"
            )
        return self.local_inp_dir

    def _validate_remote_prerequisites(self):
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non e installato.\n\nInstalla con: pip install paramiko"
            )
            return False

        if not self.farm_controller:
            messagebox.showerror("Errore", "Meteo window non collegata alle operazioni Farm.")
            return False

        if not getattr(self.farm_controller, "farm_config", None):
            messagebox.showerror("Errore", "Configurazione Farm mancante.")
            return False

        if not self.farm_controller.jump_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Jump Server nella finestra Farm.")
            return False

        if (not self.farm_controller.same_credentials.get()) and (not self.farm_controller.target_password.get()):
            messagebox.showerror("Errore", "Inserisci la password Target Server nella finestra Farm.")
            return False

        return True

    def _connect_target(self):
        farm_config = self.farm_controller.farm_config

        jump_host = farm_config.get("ssh_host", "")
        jump_port = int(farm_config.get("ssh_port", 22))
        jump_username = farm_config.get("ssh_username", "")
        jump_password = self.farm_controller.jump_password.get()

        target_host = farm_config.get("target_host", "")
        target_username = farm_config.get("target_username", jump_username)
        target_password = (
            self.farm_controller.target_password.get()
            if not self.farm_controller.same_credentials.get()
            else jump_password
        )

        jump_client = paramiko.SSHClient()
        jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jump_client.connect(
            hostname=jump_host,
            port=jump_port,
            username=jump_username,
            password=jump_password,
        )

        jump_transport = jump_client.get_transport()
        dest_addr = (target_host, 22)
        local_addr = (jump_host, jump_port)
        jump_channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr)

        target_client = paramiko.SSHClient()
        target_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        target_client.connect(
            hostname=target_host,
            username=target_username,
            password=target_password,
            sock=jump_channel,
        )

        return jump_client, target_client

    def _upload_folder_recursive(self, sftp, local_folder, remote_folder):
        try:
            sftp.stat(remote_folder)
        except FileNotFoundError:
            sftp.mkdir(remote_folder)

        for root, dirs, files in os.walk(local_folder):
            root_path = Path(root)
            relative_root = root_path.relative_to(local_folder)

            remote_root = remote_folder
            if str(relative_root) != ".":
                remote_root = f"{remote_folder}/{str(relative_root).replace('\\\\', '/')}"

            try:
                sftp.stat(remote_root)
            except FileNotFoundError:
                sftp.mkdir(remote_root)

            for directory_name in dirs:
                remote_dir = f"{remote_root}/{directory_name}"
                try:
                    sftp.stat(remote_dir)
                except FileNotFoundError:
                    sftp.mkdir(remote_dir)

            for file_name in files:
                local_file = root_path / file_name
                remote_file = f"{remote_root}/{file_name}"
                sftp.put(str(local_file), remote_file)

    def load_inp(self):
        local_dir = self.create_inp(show_message=False)
        if not local_dir:
            return

        if not self._validate_remote_prerequisites():
            return

        thread = threading.Thread(target=self._load_inp_thread, args=(local_dir,))
        thread.daemon = True
        thread.start()

    def _load_inp_thread(self, local_dir):
        jump_client = None
        target_client = None
        sftp = None
        try:
            self._log("Load INP Meteo: connessione in corso...")
            jump_client, target_client = self._connect_target()

            working_folder = str(self.farm_controller.farm_config.get("working_folder", "/project/pmten/simulations/")).rstrip("/")
            remote_dir = f"{working_folder}/METEO_INP"

            stdin, stdout, stderr = target_client.exec_command(f'mkdir -p "{working_folder}"')
            stdout.channel.recv_exit_status()

            sftp = target_client.open_sftp()
            self._upload_folder_recursive(sftp, local_dir, remote_dir)

            self._log(f"Load INP Meteo completato: {remote_dir}")
            messagebox.showinfo("Successo", f"Upload METEO_INP completato su:\n{remote_dir}")
        except Exception as exc:
            self._log(f"Load INP Meteo errore: {exc}")
            messagebox.showerror("Errore", f"Errore durante Load INP Meteo:\n\n{exc}")
        finally:
            try:
                if sftp:
                    sftp.close()
            except Exception:
                pass
            try:
                if target_client:
                    target_client.close()
            except Exception:
                pass
            try:
                if jump_client:
                    jump_client.close()
            except Exception:
                pass

    def launch_meteo(self):
        local_dir = self.create_inp(show_message=False)
        if not local_dir:
            return

        if not self._validate_remote_prerequisites():
            return

        thread = threading.Thread(target=self._launch_meteo_thread)
        thread.daemon = True
        thread.start()

    def _resolve_remote_path(self, base_folder, value):
        raw = str(value).strip()
        if not raw:
            return base_folder
        if raw.startswith("/"):
            return raw.rstrip("/")
        return f"{base_folder}/{raw.strip('/')}"

    def _launch_meteo_thread(self):
        jump_client = None
        target_client = None
        try:
            config = self._collect_config()
            self._log("Launch Meteo: connessione in corso...")
            jump_client, target_client = self._connect_target()

            work_folder = str(self.farm_controller.farm_config.get("working_folder", "/project/pmten/simulations/")).rstrip("/")
            meteo_inp_dir = f"{work_folder}/METEO_INP"
            output_dir = self._resolve_remote_path(work_folder, config.get("OUTPUT_FOLDER", "METEODATA"))
            prtmet_dir = self._resolve_remote_path(work_folder, config.get("PRTMET", "PRTMET_v4.34/PRTMET"))
            calmet_data_dir = self._resolve_remote_path(work_folder, config.get("CALMET_DATA", "CALMETDATA"))

            stdin, stdout, stderr = target_client.exec_command(f'mkdir -p "{output_dir}"')
            stdout.channel.recv_exit_status()

            if hasattr(self.farm_controller, "_render_script_template"):
                bash_script = self.farm_controller._render_script_template(
                    "run_meteo_batch.sh.template",
                    {
                        "TPL_WORK_FOLDER": work_folder,
                        "TPL_METEO_INP_DIR": meteo_inp_dir,
                        "TPL_OUTPUT_DIR": output_dir,
                        "TPL_PRTMET_DIR": prtmet_dir,
                        "TPL_CALMET_DATA_DIR": calmet_data_dir,
                        "TPL_LINK_FILE": "1" if config.get("LINK_FILE", False) else "0",
                    },
                )
            else:
                raise RuntimeError("Renderer template non disponibile.")

            script_path = f"{work_folder}/run_meteo_batch.sh"
            sftp = target_client.open_sftp()
            with sftp.open(script_path, "w") as script_file:
                script_file.write(bash_script)
            sftp.close()

            target_client.exec_command(f'chmod +x "{script_path}"')

            log_out = f"{output_dir}/meteo_output.log"
            log_err = f"{output_dir}/meteo_error.log"
            target_client.exec_command(f'rm -f "{log_out}" "{log_err}"')

            if bool(config.get("RUN_BACKGROUND", True)):
                bsub_command = (
                    f'cd "{work_folder}"; '
                    f'bsub -q pmten -o "{log_out}" -e "{log_err}" "{script_path}"'
                )
                stdin, stdout, stderr = target_client.exec_command(bsub_command)
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                exit_status = stdout.channel.recv_exit_status()

                if output:
                    self._log(f"Launch Meteo bsub output:\n{output}")
                if error:
                    self._log(f"Launch Meteo bsub stderr:\n{error}")

                if exit_status != 0:
                    raise RuntimeError(f"Sottomissione Meteo fallita con exit code {exit_status}")

                self._log("Launch Meteo sottomesso in background")
                self._log(f"Log output: {log_out}")
                self._log(f"Log errori: {log_err}")
                messagebox.showwarning(
                    "Job Meteo Sottomesso",
                    "Job Meteo sottomesso con bsub -q pmten.\n\n"
                    f"Log output: {log_out}\n"
                    f"Log errori: {log_err}"
                )
                return

            stdin, stdout, stderr = target_client.exec_command(f'cd "{work_folder}"; "{script_path}"')
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            exit_status = stdout.channel.recv_exit_status()

            if output:
                self._log(f"Launch Meteo output:\n{output}")
            if error:
                self._log(f"Launch Meteo stderr:\n{error}")

            if exit_status != 0:
                raise RuntimeError(f"Launch Meteo fallito con exit code {exit_status}")

            messagebox.showinfo("Successo", "Launch Meteo completato con successo.")

        except Exception as exc:
            self._log(f"Launch Meteo errore: {exc}")
            messagebox.showerror("Errore", f"Errore durante Launch Meteo:\n\n{exc}")
        finally:
            try:
                if target_client:
                    target_client.close()
            except Exception:
                pass
            try:
                if jump_client:
                    jump_client.close()
            except Exception:
                pass
