"""
Finestra per la definizione del dominio geografico
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import math
import os
import re
try:
    import tkintermapview
    MAPVIEW_AVAILABLE = True
except ImportError:
    MAPVIEW_AVAILABLE = False

try:
    from pyproj import Transformer, CRS
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False


class DomainWindow:
    """Finestra per definire il dominio geografico della simulazione"""
    
    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = temp_dir
        self.window = tk.Toplevel(parent)
        self.window.title("Definisci Dominio Geografico")
        self.window.geometry("1200x700")
        
        # Coordinate dei 4 vertici (Nord-Ovest, Nord-Est, Sud-Est, Sud-Ovest)
        self.vertices = {
            'NW': {'lat': 45.5, 'lon': 9.0},  # Nord-Ovest
            'NE': {'lat': 45.5, 'lon': 9.5},  # Nord-Est
            'SE': {'lat': 45.0, 'lon': 9.5},  # Sud-Est
            'SW': {'lat': 45.0, 'lon': 9.0}   # Sud-Ovest
        }
        
        # Passo della griglia (in km o gradi)
        self.grid_step = tk.StringVar(value="1.0")
        self.grid_step_unit = tk.StringVar(value="km")

        # Modalita' di input delle coordinate del dominio
        self.coordinate_system = tk.StringVar(value="latlon")
        self.utm_zone = tk.StringVar(value="")
        
        # Origine griglia
        self.origin_lat = tk.DoubleVar(value=45.0)
        self.origin_lon = tk.DoubleVar(value=9.0)
        self.origin_km_x = None
        self.origin_km_y = None
        self.nx = tk.IntVar(value=100)
        self.ny = tk.IntVar(value=100)

        # Controlli dinamici dei vertici
        self.vertex_controls = {}
        self.origin_controls = {}
        self.utm_zone_frame = None
        self.utm_zone_entry = None
        self.display_coordinate_system = self.coordinate_system.get()
        self.syncing_ui = False
        self.is_updating_map = False
        self.map_update_after_id = None

        # Se presente, carica una configurazione dominio già salvata
        self.load_existing_domain_config()
        
        # Elementi grafici sulla mappa
        self.map_markers = {}
        self.map_polygons = []
        self.map_paths = []
        
        # Flag per evitare loop infiniti nei callback
        self.updating_vertices = False
        
        self.setup_ui()
        
        # Aggiorna la mappa quando cambiano origine o parametri della griglia
        for var in (self.origin_lat, self.origin_lon, self.grid_step, self.grid_step_unit, self.nx, self.ny):
            var.trace_add('write', self.schedule_map_update)
        self.utm_zone.trace_add('write', self.schedule_map_update)
        
        self.update_map()

    def load_existing_domain_config(self):
        """Carica i parametri del dominio da `domain_config.json` se presente."""
        config_file = self.temp_dir / 'domain_config.json'
        if not config_file.exists():
            return

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                domain_data = json.load(f)

            coordinate_system = self.normalize_coordinate_system(
                domain_data.get('coordinate_system') or domain_data.get('coordinate_type')
            )
            self.coordinate_system.set(coordinate_system)

            zone_value = domain_data.get('zona_utm') or domain_data.get('utm_zone')
            if zone_value:
                normalized_zone = self.normalize_utm_zone(zone_value)
                if normalized_zone:
                    self.utm_zone.set(normalized_zone)

            vertices = domain_data.get('vertices', {})
            for key in ('NW', 'NE', 'SE', 'SW'):
                vertex_data = vertices.get(key)
                if not vertex_data:
                    continue
                self.vertices[key]['lat'] = float(vertex_data.get('lat', self.vertices[key]['lat']))
                self.vertices[key]['lon'] = float(vertex_data.get('lon', self.vertices[key]['lon']))
                if vertex_data.get('km_x') is not None:
                    self.vertices[key]['km_x'] = float(vertex_data.get('km_x'))
                if vertex_data.get('km_y') is not None:
                    self.vertices[key]['km_y'] = float(vertex_data.get('km_y'))

            grid_step = domain_data.get('grid_step', {})
            if 'value' in grid_step:
                self.grid_step.set(str(grid_step['value']))
            if 'unit' in grid_step:
                self.grid_step_unit.set(grid_step['unit'])

            grid_origin = domain_data.get('grid_origin', {})
            if 'lat' in grid_origin:
                self.origin_lat.set(float(grid_origin['lat']))
            if 'lon' in grid_origin:
                self.origin_lon.set(float(grid_origin['lon']))
            if 'km_x' in grid_origin and grid_origin['km_x'] is not None:
                self.origin_km_x = float(grid_origin['km_x'])
            if 'km_y' in grid_origin and grid_origin['km_y'] is not None:
                self.origin_km_y = float(grid_origin['km_y'])
            if 'nx' in grid_origin:
                self.nx.set(int(grid_origin['nx']))
            if 'ny' in grid_origin:
                self.ny.set(int(grid_origin['ny']))

        except Exception as e:
            messagebox.showwarning(
                "Avviso",
                f"Impossibile caricare il dominio salvato da {config_file}:\n{str(e)}"
            )
    
    def setup_ui(self):
        """Configura l'interfaccia della finestra"""
        # Frame principale diviso in due colonne
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configura il grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(1, weight=1)
        
        # === COLONNA SINISTRA: Controlli ===
        controls_frame = ttk.LabelFrame(main_frame, text="Parametri Dominio", padding="10")
        controls_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        # Modalita' coordinate
        mode_frame = ttk.LabelFrame(controls_frame, text="Sistema di Coordinate", padding="8")
        mode_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
        ttk.Radiobutton(
            mode_frame,
            text="Lat / Lon",
            variable=self.coordinate_system,
            value="latlon",
            command=self.refresh_coordinate_mode_ui
        ).pack(side=tk.LEFT, padx=(0, 12))
        utm_button = ttk.Radiobutton(
            mode_frame,
            text="UTM",
            variable=self.coordinate_system,
            value="utm",
            command=self.refresh_coordinate_mode_ui
        )
        utm_button.pack(side=tk.LEFT)
        if not PYPROJ_AVAILABLE:
            utm_button.configure(state=tk.DISABLED)
            ttk.Label(
                mode_frame,
                text="pyproj non disponibile: UTM disabilitato",
                foreground="darkred"
            ).pack(side=tk.LEFT, padx=(12, 0))

        self.utm_zone_frame = ttk.Frame(controls_frame)
        self.utm_zone_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
        ttk.Label(self.utm_zone_frame, text="Zona UTM:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 6))
        self.utm_zone_entry = ttk.Entry(self.utm_zone_frame, textvariable=self.utm_zone, width=15)
        self.utm_zone_entry.pack(side=tk.LEFT)
        ttk.Label(
            self.utm_zone_frame,
            text="Formato: 32N, 33S, ...",
            foreground="gray40"
        ).pack(side=tk.LEFT, padx=(8, 0))

        # Vertice Nord-Ovest
        self.create_vertex_inputs(controls_frame, "Nord-Ovest (NW)", "NW", 2)
        
        # Vertice Nord-Est
        self.create_vertex_inputs(controls_frame, "Nord-Est (NE)", "NE", 4)
        
        # Vertice Sud-Est
        self.create_vertex_inputs(controls_frame, "Sud-Est (SE)", "SE", 6)
        
        # Vertice Sud-Ovest
        self.create_vertex_inputs(controls_frame, "Sud-Ovest (SW)", "SW", 8)
        
        # Separatore
        ttk.Separator(controls_frame, orient='horizontal').grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Passo della griglia
        ttk.Label(controls_frame, text="Passo Griglia:", font=('Arial', 10, 'bold')).grid(row=11, column=0, columnspan=3, sticky=tk.W, pady=(5, 2))
        
        step_frame = ttk.Frame(controls_frame)
        step_frame.grid(row=12, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Entry(step_frame, textvariable=self.grid_step, width=15).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Combobox(step_frame, textvariable=self.grid_step_unit, values=['km', 'gradi'], state='readonly', width=10).pack(side=tk.LEFT)
        
        # Separatore
        ttk.Separator(controls_frame, orient='horizontal').grid(row=13, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Origine Griglia
        ttk.Label(controls_frame, text="Origine Griglia:", font=('Arial', 10, 'bold')).grid(row=14, column=0, columnspan=3, sticky=tk.W, pady=(5, 2))
        
        origin_frame1 = ttk.Frame(controls_frame)
        origin_frame1.grid(row=15, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)
        origin_first_label = ttk.Label(origin_frame1, text="Lat:")
        origin_first_label.pack(side=tk.LEFT, padx=(10, 5))
        self.origin_first_var = tk.StringVar(value=self._format_coord_value(self.origin_lat.get()))
        origin_first_entry = ttk.Entry(origin_frame1, textvariable=self.origin_first_var, width=15)
        origin_first_entry.pack(side=tk.LEFT, padx=(0, 20))
        origin_second_label = ttk.Label(origin_frame1, text="Lon:")
        origin_second_label.pack(side=tk.LEFT, padx=(0, 5))
        self.origin_second_var = tk.StringVar(value=self._format_coord_value(self.origin_lon.get()))
        origin_second_entry = ttk.Entry(origin_frame1, textvariable=self.origin_second_var, width=15)
        origin_second_entry.pack(side=tk.LEFT)

        self.origin_controls = {
            'first_label': origin_first_label,
            'first_entry': origin_first_entry,
            'first_var': self.origin_first_var,
            'second_label': origin_second_label,
            'second_entry': origin_second_entry,
            'second_var': self.origin_second_var,
        }
        
        # NX e NY
        origin_frame2 = ttk.Frame(controls_frame)
        origin_frame2.grid(row=16, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(origin_frame2, text="NX:").pack(side=tk.LEFT, padx=(10, 5))
        ttk.Entry(origin_frame2, textvariable=self.nx, width=15).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(origin_frame2, text="NY:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(origin_frame2, textvariable=self.ny, width=15).pack(side=tk.LEFT)
        
        # Bottoni azione
        button_frame = ttk.Frame(controls_frame)
        button_frame.grid(row=17, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Salva", command=self.save_domain).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annulla", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
        # === COLONNA DESTRA: Mappa ===
        map_frame = ttk.LabelFrame(main_frame, text="Mappa Interattiva", padding="10")
        map_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        map_frame.columnconfigure(0, weight=1)
        map_frame.rowconfigure(0, weight=1)
        
        # Widget mappa
        if MAPVIEW_AVAILABLE:
            try:
                self.map_widget = tkintermapview.TkinterMapView(map_frame, corner_radius=0)
                self.map_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                # Imposta il tile server (OpenStreetMap)
                self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
                print("MapView creato con successo")
            except Exception as e:
                print(f"Errore creazione MapView: {e}")
                self.map_widget = None
                fallback_label = ttk.Label(
                    map_frame, 
                    text=f"Errore nel caricamento della mappa:\n{str(e)}\n\nProva a reinstallare tkintermapview.",
                    justify=tk.CENTER,
                    foreground='red'
                )
                fallback_label.grid(row=0, column=0, pady=50)
        else:
            # Fallback: mostra un messaggio
            fallback_label = ttk.Label(
                map_frame, 
                text="Per visualizzare la mappa,\ninstalla tkintermapview:\npip install tkintermapview\n\nLa configurazione verrà salvata comunque.",
                justify=tk.CENTER,
                foreground='red'
            )
            fallback_label.grid(row=0, column=0, pady=50)
            self.map_widget = None

        self.refresh_coordinate_mode_ui()
        self.display_coordinate_system = self.normalize_coordinate_system(self.coordinate_system.get())

        self.origin_first_var.trace_add('write', self.schedule_map_update)
        self.origin_second_var.trace_add('write', self.schedule_map_update)
    
    def create_vertex_inputs(self, parent, label, vertex_key, row):
        """Crea gli input per un vertice"""
        vertex_frame = ttk.Frame(parent)
        vertex_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(vertex_frame, text=label, font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(5, 2))

        coord_row = ttk.Frame(vertex_frame)
        coord_row.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2)
        coord_row.columnconfigure(1, weight=1)
        coord_row.columnconfigure(3, weight=1)

        first_label = ttk.Label(coord_row, text="")
        first_label.grid(row=0, column=0, sticky=tk.W, padx=(10, 5))
        first_var = tk.StringVar(value=self._format_coord_value(self.vertices[vertex_key].get('lat')))
        first_entry = ttk.Entry(coord_row, textvariable=first_var, width=15)
        first_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

        second_label = ttk.Label(coord_row, text="")
        second_label.grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        second_var = tk.StringVar(value=self._format_coord_value(self.vertices[vertex_key].get('lon')))
        second_entry = ttk.Entry(coord_row, textvariable=second_var, width=15)
        second_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), pady=2)

        self.vertex_controls[vertex_key] = {
            'first_label': first_label,
            'first_var': first_var,
            'first_entry': first_entry,
            'second_label': second_label,
            'second_var': second_var,
            'second_entry': second_entry,
        }

        first_var.trace_add('write', lambda *args, key=vertex_key: self.on_vertex_change(key, 'first'))
        second_var.trace_add('write', lambda *args, key=vertex_key: self.on_vertex_change(key, 'second'))

    def normalize_coordinate_system(self, value):
        """Normalizza il sistema di coordinate scelto."""
        if not value:
            return 'latlon'

        normalized = str(value).strip().lower().replace('_', '-')
        if normalized in {'utm'}:
            return 'utm'
        return 'latlon'

    def normalize_utm_zone(self, zone_value):
        """Valida e normalizza una zona UTM nel formato `32N`."""
        if zone_value is None:
            return None

        match = re.fullmatch(r'\s*(\d{1,2})\s*([NSns])\s*', str(zone_value))
        if not match:
            return None

        zone_number = int(match.group(1))
        if not 1 <= zone_number <= 60:
            return None

        hemisphere = match.group(2).upper()
        return f"{zone_number}{hemisphere}"

    def _format_coord_value(self, value):
        """Formatta i valori numerici per la UI."""
        if value is None:
            return ""
        try:
            return f"{float(value):.6f}".rstrip('0').rstrip('.')
        except (TypeError, ValueError):
            return str(value)

    def schedule_map_update(self, *args, force=False):
        """Pianifica un aggiornamento mappa debounced, evitando rientri durante sync programmatici."""
        if not force and (self.syncing_ui or self.updating_vertices or self.is_updating_map):
            return

        if self.map_update_after_id is not None:
            try:
                self.window.after_cancel(self.map_update_after_id)
            except tk.TclError:
                pass

        self.map_update_after_id = self.window.after(100, self.update_map)

    def get_effective_utm_zone(self, lat=None, lon=None):
        """Restituisce la zona UTM da usare per le conversioni."""
        zone = self.normalize_utm_zone(self.utm_zone.get())
        if zone:
            return zone

        if lat is not None and lon is not None:
            zone_from_latlon, _, _ = self.lat_lon_to_utm(lat, lon)
            if zone_from_latlon:
                return zone_from_latlon

        for vertex in self.vertices.values():
            vertex_lat = vertex.get('lat')
            vertex_lon = vertex.get('lon')
            if vertex_lat is None or vertex_lon is None:
                continue
            zone_from_latlon, _, _ = self.lat_lon_to_utm(vertex_lat, vertex_lon)
            if zone_from_latlon:
                return zone_from_latlon

        return None

    def refresh_coordinate_mode_ui(self):
        """Aggiorna etichette e valori in base al sistema di coordinate attivo."""
        if not self.vertex_controls:
            return

        current_mode = self.normalize_coordinate_system(self.coordinate_system.get())
        previous_mode = self.normalize_coordinate_system(getattr(self, 'display_coordinate_system', current_mode))

        if current_mode == 'utm' and not PYPROJ_AVAILABLE:
            self.coordinate_system.set('latlon')
            self.display_coordinate_system = 'latlon'
            messagebox.showwarning(
                "Avviso",
                "Il sistema UTM richiede pyproj. La finestra restera' in modalita' Lat/Lon."
            )
            return

        if current_mode == 'utm':
            self.utm_zone_frame.grid()
            first_label = 'X UTM (km):'
            second_label = 'Y UTM (km):'
        else:
            self.utm_zone_frame.grid_remove()
            first_label = 'Lat:'
            second_label = 'Lon:'

        zone_hint = self.normalize_utm_zone(self.utm_zone.get())

        self.syncing_ui = True
        self.updating_vertices = True
        try:
            for key, controls in self.vertex_controls.items():
                controls['first_label'].configure(text=first_label)
                controls['second_label'].configure(text=second_label)

                vertex = self.vertices[key]
                if previous_mode != current_mode:
                    first_raw = controls['first_var'].get().strip()
                    second_raw = controls['second_var'].get().strip()

                    try:
                        if previous_mode == 'latlon' and current_mode == 'utm':
                            lat = float(first_raw)
                            lon = float(second_raw)
                            conversion_zone = zone_hint
                            zone_from_conversion, km_x, km_y = self.lat_lon_to_utm(lat, lon, conversion_zone)
                            if conversion_zone is None and zone_from_conversion:
                                conversion_zone = zone_from_conversion
                            if km_x is None or km_y is None:
                                raise ValueError("Impossibile convertire le coordinate in UTM")
                            vertex['lat'] = lat
                            vertex['lon'] = lon
                            vertex['km_x'] = km_x
                            vertex['km_y'] = km_y
                            controls['first_var'].set(self._format_coord_value(km_x))
                            controls['second_var'].set(self._format_coord_value(km_y))
                            if conversion_zone:
                                self.utm_zone.set(conversion_zone)
                        elif previous_mode == 'utm' and current_mode == 'latlon':
                            if not zone_hint:
                                raise ValueError("Inserire una zona UTM valida nel formato 32N, 33S, ...")
                            km_x = float(first_raw)
                            km_y = float(second_raw)
                            lat, lon = self.utm_to_lat_lon(zone_hint, km_x, km_y)
                            if lat is None or lon is None:
                                raise ValueError("Impossibile convertire le coordinate UTM in lat/lon")
                            vertex['lat'] = lat
                            vertex['lon'] = lon
                            vertex['km_x'] = km_x
                            vertex['km_y'] = km_y
                            controls['first_var'].set(self._format_coord_value(lat))
                            controls['second_var'].set(self._format_coord_value(lon))
                    except ValueError:
                        self.coordinate_system.set(previous_mode)
                        self.display_coordinate_system = previous_mode
                        messagebox.showerror(
                            "Errore",
                            "Completa i valori dei vertici prima di cambiare sistema di coordinate."
                        )
                        return
                else:
                    if current_mode == 'utm':
                        if vertex.get('km_x') is None or vertex.get('km_y') is None:
                            current_zone = self.normalize_utm_zone(self.utm_zone.get()) or self.get_effective_utm_zone(vertex.get('lat'), vertex.get('lon'))
                            if current_zone:
                                _, km_x, km_y = self.lat_lon_to_utm(vertex.get('lat'), vertex.get('lon'), current_zone)
                                if km_x is not None and km_y is not None:
                                    vertex['km_x'] = km_x
                                    vertex['km_y'] = km_y
                        controls['first_var'].set(self._format_coord_value(vertex.get('km_x')))
                        controls['second_var'].set(self._format_coord_value(vertex.get('km_y')))
                    else:
                        controls['first_var'].set(self._format_coord_value(vertex.get('lat')))
                        controls['second_var'].set(self._format_coord_value(vertex.get('lon')))

            self._refresh_origin_controls(current_mode, previous_mode, zone_hint)
        finally:
            self.updating_vertices = False
            self.syncing_ui = False

        self.utm_zone_entry.configure(state='normal')
        self.display_coordinate_system = current_mode
        self.schedule_map_update()

    def _refresh_origin_controls(self, current_mode, previous_mode, zone_hint):
        """Allinea i controlli dell'origine griglia alla modalita' attiva."""
        if not self.origin_controls:
            return

        first_label = self.origin_controls['first_label']
        second_label = self.origin_controls['second_label']
        first_var = self.origin_first_var
        second_var = self.origin_second_var

        if current_mode == 'utm':
            first_label.configure(text='X UTM:')
            second_label.configure(text='Y UTM:')
        else:
            first_label.configure(text='Lat:')
            second_label.configure(text='Lon:')

        if previous_mode != current_mode:
            try:
                if previous_mode == 'latlon' and current_mode == 'utm':
                    origin_lat = float(first_var.get())
                    origin_lon = float(second_var.get())
                    conversion_zone = zone_hint
                    zone_from_conversion, origin_km_x, origin_km_y = self.lat_lon_to_utm(origin_lat, origin_lon, conversion_zone)
                    if conversion_zone is None and zone_from_conversion:
                        conversion_zone = zone_from_conversion
                    if origin_km_x is None or origin_km_y is None:
                        raise ValueError("Impossibile convertire l'origine griglia in UTM")
                    self.origin_lat.set(origin_lat)
                    self.origin_lon.set(origin_lon)
                    self.origin_km_x = origin_km_x
                    self.origin_km_y = origin_km_y
                    first_var.set(self._format_coord_value(origin_km_x))
                    second_var.set(self._format_coord_value(origin_km_y))
                    if conversion_zone:
                        self.utm_zone.set(conversion_zone)
                elif previous_mode == 'utm' and current_mode == 'latlon':
                    if not zone_hint:
                        raise ValueError("Inserire una zona UTM valida nel formato 32N, 33S, ...")
                    origin_km_x = float(first_var.get())
                    origin_km_y = float(second_var.get())
                    origin_lat, origin_lon = self.utm_to_lat_lon(zone_hint, origin_km_x, origin_km_y)
                    if origin_lat is None or origin_lon is None:
                        raise ValueError("Impossibile convertire l'origine griglia in lat/lon")
                    self.origin_lat.set(origin_lat)
                    self.origin_lon.set(origin_lon)
                    self.origin_km_x = origin_km_x
                    self.origin_km_y = origin_km_y
                    first_var.set(self._format_coord_value(origin_lat))
                    second_var.set(self._format_coord_value(origin_lon))
            except ValueError:
                self.coordinate_system.set(previous_mode)
                self.display_coordinate_system = previous_mode
                messagebox.showerror(
                    "Errore",
                    "Completa i valori dell'origine griglia prima di cambiare sistema di coordinate."
                )
                return
        else:
            if current_mode == 'utm':
                if self.origin_km_x is None or self.origin_km_y is None:
                    zone_for_origin = self.normalize_utm_zone(self.utm_zone.get()) or self.get_effective_utm_zone(self.origin_lat.get(), self.origin_lon.get())
                    if zone_for_origin:
                        _, origin_km_x, origin_km_y = self.lat_lon_to_utm(self.origin_lat.get(), self.origin_lon.get(), zone_for_origin)
                        if origin_km_x is not None and origin_km_y is not None:
                            self.origin_km_x = origin_km_x
                            self.origin_km_y = origin_km_y
                first_var.set(self._format_coord_value(self.origin_km_x))
                second_var.set(self._format_coord_value(self.origin_km_y))
            else:
                first_var.set(self._format_coord_value(self.origin_lat.get()))
                second_var.set(self._format_coord_value(self.origin_lon.get()))

    def update_origin_from_ui(self, show_error=False):
        """Aggiorna l'origine griglia dai campi visibili."""
        try:
            system = self.normalize_coordinate_system(self.coordinate_system.get())
            zone = self.normalize_utm_zone(self.utm_zone.get())

            if system == 'utm' and not zone:
                raise ValueError("Inserire una zona UTM valida nel formato 32N, 33S, ...")

            first_value = float(self.origin_first_var.get())
            second_value = float(self.origin_second_var.get())

            if system == 'utm':
                self.origin_km_x = first_value
                self.origin_km_y = second_value
                origin_lat, origin_lon = self.utm_to_lat_lon(zone, self.origin_km_x, self.origin_km_y)
                if origin_lat is None or origin_lon is None:
                    raise ValueError("Impossibile convertire l'origine griglia in lat/lon")
            else:
                origin_lat = first_value
                origin_lon = second_value
                zone_from_latlon, origin_km_x, origin_km_y = self.lat_lon_to_utm(origin_lat, origin_lon, zone)
                if zone is None and zone_from_latlon:
                    self.utm_zone.set(zone_from_latlon)
                self.origin_km_x = origin_km_x
                self.origin_km_y = origin_km_y

            self.origin_lat.set(origin_lat)
            self.origin_lon.set(origin_lon)
            return True
        except (tk.TclError, ValueError):
            if show_error:
                if self.normalize_coordinate_system(self.coordinate_system.get()) == 'utm' and not self.normalize_utm_zone(self.utm_zone.get()):
                    messagebox.showerror("Errore", "Inserire una zona UTM valida nel formato 32N, 33S, ...")
                else:
                    messagebox.showerror("Errore", "Inserire valori numerici validi per l'origine griglia")
            return False
    
    def on_vertex_change(self, vertex_key, coord_type):
        """Gestisce le modifiche ai vertici per mantenere il vincolo del rettangolo"""
        if self.updating_vertices:
            return
        
        self.updating_vertices = True
        should_update_map = False
        
        try:
            # In Lat/Lon: first=lat (N/S), second=lon (E/W)
            # In UTM: first=X (E/W), second=Y (N/S)
            system = self.normalize_coordinate_system(self.coordinate_system.get())
            is_utm = (system == 'utm')

            # Coordina quale asse rappresenta N/S o E/W in base alla modalita'.
            north_south_coord = 'second' if is_utm else 'first'
            east_west_coord = 'first' if is_utm else 'second'
            
            if vertex_key == 'NW':
                if coord_type == north_south_coord:
                    # Lato nord: NW <-> NE
                    self.vertex_controls['NE'][f'{coord_type}_var'].set(self.vertex_controls['NW'][f'{coord_type}_var'].get())
                elif coord_type == east_west_coord:
                    # Lato ovest: NW <-> SW
                    self.vertex_controls['SW'][f'{coord_type}_var'].set(self.vertex_controls['NW'][f'{coord_type}_var'].get())
            
            elif vertex_key == 'NE':
                if coord_type == north_south_coord:
                    # Lato nord: NE <-> NW
                    self.vertex_controls['NW'][f'{coord_type}_var'].set(self.vertex_controls['NE'][f'{coord_type}_var'].get())
                elif coord_type == east_west_coord:
                    # Lato est: NE <-> SE
                    self.vertex_controls['SE'][f'{coord_type}_var'].set(self.vertex_controls['NE'][f'{coord_type}_var'].get())
            
            elif vertex_key == 'SE':
                if coord_type == north_south_coord:
                    # Lato sud: SE <-> SW
                    self.vertex_controls['SW'][f'{coord_type}_var'].set(self.vertex_controls['SE'][f'{coord_type}_var'].get())
                elif coord_type == east_west_coord:
                    # Lato est: SE <-> NE
                    self.vertex_controls['NE'][f'{coord_type}_var'].set(self.vertex_controls['SE'][f'{coord_type}_var'].get())
            
            elif vertex_key == 'SW':
                if coord_type == north_south_coord:
                    # Lato sud: SW <-> SE
                    self.vertex_controls['SE'][f'{coord_type}_var'].set(self.vertex_controls['SW'][f'{coord_type}_var'].get())
                elif coord_type == east_west_coord:
                    # Lato ovest: SW <-> NW
                    self.vertex_controls['NW'][f'{coord_type}_var'].set(self.vertex_controls['SW'][f'{coord_type}_var'].get())
            
            # Richiede un aggiornamento mappa dopo avere rilasciato il lock di sync.
            should_update_map = True
        
        except tk.TclError:
            # Ignora errori durante la modifica
            pass
        finally:
            self.updating_vertices = False
            if should_update_map:
                self.schedule_map_update(force=True)
    
    def update_vertices_from_ui(self, show_error=False):
        """Aggiorna i vertici dalle celle di input attive."""
        try:
            system = self.normalize_coordinate_system(self.coordinate_system.get())
            zone = self.normalize_utm_zone(self.utm_zone.get())

            if system == 'utm' and not zone:
                raise ValueError("Inserire una zona UTM valida nel formato 32N, 33S, ...")

            for key in ('NW', 'NE', 'SE', 'SW'):
                controls = self.vertex_controls[key]
                first_value = float(controls['first_var'].get())
                second_value = float(controls['second_var'].get())

                if system == 'utm':
                    km_x = first_value
                    km_y = second_value
                    lat, lon = self.utm_to_lat_lon(zone, km_x, km_y)
                    if lat is None or lon is None:
                        raise ValueError("Impossibile convertire le coordinate UTM in lat/lon")
                else:
                    lat = first_value
                    lon = second_value
                    zone_from_latlon, km_x, km_y = self.lat_lon_to_utm(lat, lon, zone)
                    if zone is None and zone_from_latlon:
                        zone = zone_from_latlon

                self.vertices[key]['lat'] = lat
                self.vertices[key]['lon'] = lon
                self.vertices[key]['km_x'] = km_x
                self.vertices[key]['km_y'] = km_y

            if zone:
                self.utm_zone.set(zone)

            return True
        except (tk.TclError, ValueError):
            if show_error:
                if self.normalize_coordinate_system(self.coordinate_system.get()) == 'utm' and not self.normalize_utm_zone(self.utm_zone.get()):
                    messagebox.showerror("Errore", "Inserire una zona UTM valida nel formato 32N, 33S, ...")
                else:
                    messagebox.showerror("Errore", "Inserire valori numerici validi per le coordinate del dominio")
            return False
    
    def km_to_degree_steps(self, step_km, reference_lat):
        """Converte un passo in km in delta lat/lon approssimati."""
        lat_step = step_km / 110.574
        cos_lat = abs(math.cos(math.radians(reference_lat)))
        if cos_lat < 1e-6:
            cos_lat = 1e-6
        lon_step = step_km / (111.320 * cos_lat)
        return lat_step, lon_step

    def utm_to_lat_lon(self, zona_utm, km_x, km_y):
        """Converte coordinate UTM (km) in lat/lon."""
        if not PYPROJ_AVAILABLE or not zona_utm:
            return None, None

        try:
            zone_number = int(zona_utm[:-1])
            hemisphere = zona_utm[-1].upper()

            if hemisphere == 'N':
                epsg_code = 32600 + zone_number
            else:
                epsg_code = 32700 + zone_number

            transformer = Transformer.from_crs(
                f"EPSG:{epsg_code}",
                "EPSG:4326",
                always_xy=True
            )
            lon, lat = transformer.transform(km_x * 1000.0, km_y * 1000.0)
            return lat, lon

        except Exception as e:
            print(f"Errore nella conversione da UTM a lat/lon: {e}")
            return None, None

    def draw_grid_overlay(self):
        """Disegna la griglia sulla mappa quando i parametri sono completi."""
        try:
            origin_lat = float(self.origin_lat.get())
            origin_lon = float(self.origin_lon.get())
            step_value = float(self.grid_step.get())
            nx = int(self.nx.get())
            ny = int(self.ny.get())
        except (tk.TclError, ValueError):
            return

        if step_value <= 0 or nx <= 0 or ny <= 0:
            return

        unit = self.grid_step_unit.get()
        grid_lines = []

        if unit == 'km':
            zona_utm = self.get_effective_utm_zone(origin_lat, origin_lon)
            zona_utm, origin_km_x, origin_km_y = self.lat_lon_to_utm(origin_lat, origin_lon, zona_utm)

            if zona_utm and origin_km_x is not None and origin_km_y is not None:
                max_km_x = origin_km_x + (nx * step_value)
                max_km_y = origin_km_y + (ny * step_value)

                for ix in range(nx + 1):
                    current_km_x = origin_km_x + (ix * step_value)
                    start = self.utm_to_lat_lon(zona_utm, current_km_x, origin_km_y)
                    end = self.utm_to_lat_lon(zona_utm, current_km_x, max_km_y)
                    if None not in start and None not in end:
                        grid_lines.append([start, end])

                for iy in range(ny + 1):
                    current_km_y = origin_km_y + (iy * step_value)
                    start = self.utm_to_lat_lon(zona_utm, origin_km_x, current_km_y)
                    end = self.utm_to_lat_lon(zona_utm, max_km_x, current_km_y)
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
                width=1,
                name="grid_overlay"
            )
            self.map_paths.append(path)

    def update_map(self):
        """Aggiorna la mappa con i vertici correnti"""
        if self.is_updating_map:
            return

        self.is_updating_map = True
        self.map_update_after_id = None

        try:
            if not self.update_vertices_from_ui(show_error=False):
                return
            if not self.update_origin_from_ui(show_error=False):
                return
        finally:
            self.is_updating_map = False

        if self.map_widget is None:
            return
        
        try:
            # Calcola il centro del dominio
            center_lat = sum(v['lat'] for v in self.vertices.values()) / 4
            center_lon = sum(v['lon'] for v in self.vertices.values()) / 4
            
            print(f"Centro mappa: {center_lat}, {center_lon}")
            
            # Posiziona la mappa al centro
            self.map_widget.set_position(center_lat, center_lon)
            self.map_widget.set_zoom(10)
            
            # Rimuovi i marker precedenti
            for marker in self.map_markers.values():
                marker.delete()
            self.map_markers.clear()
            
            # Rimuovi i poligoni precedenti
            for polygon in self.map_polygons:
                polygon.delete()
            self.map_polygons.clear()

            # Rimuovi le linee della griglia precedenti
            for path in self.map_paths:
                path.delete()
            self.map_paths.clear()
            
            # Aggiungi i vertici come marker
            for key, vertex in self.vertices.items():
                marker = self.map_widget.set_marker(
                    vertex['lat'], 
                    vertex['lon'],
                    text=f"{key}\n{vertex['lat']:.4f}, {vertex['lon']:.4f}"
                )
                self.map_markers[key] = marker
            
            # Aggiungi il marker per l'origine griglia
            try:
                origin_marker = self.map_widget.set_marker(
                    self.origin_lat.get(),
                    self.origin_lon.get(),
                    text=f"Origine Griglia\n{self.origin_lat.get():.4f}, {self.origin_lon.get():.4f}",
                    marker_color_circle="green",
                    marker_color_outside="darkgreen"
                )
                self.map_markers['origin'] = origin_marker
            except tk.TclError:
                pass  # Ignora errori se i valori non sono validi
            
            # Disegna il rettangolo del dominio
            rectangle_coords = [
                (self.vertices['NW']['lat'], self.vertices['NW']['lon']),
                (self.vertices['NE']['lat'], self.vertices['NE']['lon']),
                (self.vertices['SE']['lat'], self.vertices['SE']['lon']),
                (self.vertices['SW']['lat'], self.vertices['SW']['lon'])
            ]
            
            polygon = self.map_widget.set_polygon(
                rectangle_coords,
                fill_color=None,
                outline_color="red",
                border_width=3,
                name="domain_boundary"
            )
            self.map_polygons.append(polygon)

            # Disegna la griglia se i parametri sono disponibili
            self.draw_grid_overlay()
            
            print("Mappa aggiornata con successo")
            
        except Exception as e:
            print(f"Errore in update_map: {e}")
            messagebox.showerror("Errore", f"Errore nell'aggiornamento della mappa: {str(e)}")
    
    def lat_lon_to_utm(self, lat, lon, zona_utm=None):
        """Converte coordinate lat/lon in coordinate UTM (km)
        
        Returns:
            tuple: (zona_utm, km_x, km_y) dove zona_utm è stringa tipo '32N'
        """
        if not PYPROJ_AVAILABLE:
            return None, None, None
        
        try:
            zone_override = self.normalize_utm_zone(zona_utm)
            if zone_override:
                zone_number = int(zone_override[:-1])
                hemisphere = zone_override[-1].upper()
            else:
                # Determina la zona UTM dalla longitudine
                zone_number = int((lon + 180) / 6) + 1
                
                # Determina l'emisfero
                hemisphere = 'N' if lat >= 0 else 'S'
            
            # Crea il codice EPSG per la zona UTM
            # Zone UTM Nord: 32601-32660, Zone UTM Sud: 32701-32760
            if hemisphere == 'N':
                epsg_code = 32600 + zone_number
            else:
                epsg_code = 32700 + zone_number
            
            # Crea il transformer da WGS84 (EPSG:4326) a UTM
            transformer = Transformer.from_crs(
                "EPSG:4326",  # WGS84 (lat/lon)
                f"EPSG:{epsg_code}",  # UTM
                always_xy=True
            )
            
            # Converti coordinate (attenzione: transformer usa (lon, lat)!)
            utm_x, utm_y = transformer.transform(lon, lat)
            
            # Converti da metri a chilometri
            km_x = utm_x / 1000.0
            km_y = utm_y / 1000.0
            
            # Costruisci la stringa della zona (es. "32N", "33S")
            zona_utm = f"{zone_number}{hemisphere}"
            
            return zona_utm, km_x, km_y
            
        except Exception as e:
            print(f"Errore nella conversione UTM: {e}")
            return None, None, None
    
    def save_domain(self):
        """Salva il dominio in un file JSON"""
        if not self.update_vertices_from_ui(show_error=True):
            return
        if not self.update_origin_from_ui(show_error=True):
            return
        
        try:
            grid_step_value = float(self.grid_step.get())
        except ValueError:
            messagebox.showerror("Errore", "Inserire un valore numerico valido per il passo della griglia")
            return

        coordinate_system = self.normalize_coordinate_system(self.coordinate_system.get())
        zona_utm = self.normalize_utm_zone(self.utm_zone.get()) or self.get_effective_utm_zone()

        if coordinate_system == 'utm':
            if not PYPROJ_AVAILABLE:
                messagebox.showerror(
                    "Errore",
                    "Per salvare un dominio in UTM e' necessario installare pyproj."
                )
                return
            if not zona_utm:
                messagebox.showerror("Errore", "Inserire una zona UTM valida nel formato 32N, 33S, ...")
                return
        
        # Converti le coordinate in UTM per ciascun vertice
        vertices_with_utm = {}
        
        for key, vertex in self.vertices.items():
            lat = vertex['lat']
            lon = vertex['lon']
            
            # Converti in UTM
            zona, km_x, km_y = self.lat_lon_to_utm(lat, lon, zona_utm)
            if zona_utm is None:
                zona_utm = zona
            
            # Crea il dizionario del vertice con tutte le coordinate
            vertices_with_utm[key] = {
                'lat': lat,
                'lon': lon,
                'km_x': round(km_x, 3) if km_x is not None else None,
                'km_y': round(km_y, 3) if km_y is not None else None
            }
        
        # Converti anche l'origine griglia in UTM
        origin_lat = self.origin_lat.get()
        origin_lon = self.origin_lon.get()
        origin_zona, origin_km_x, origin_km_y = self.lat_lon_to_utm(origin_lat, origin_lon, zona_utm)
        if origin_km_x is None:
            origin_km_x = self.origin_km_x
        if origin_km_y is None:
            origin_km_y = self.origin_km_y
        
        domain_data = {
            'coordinate_system': coordinate_system,
            'coordinate_type': 'UTM' if coordinate_system == 'utm' else 'lat-lon',
            'zona_utm': zona_utm,
            'utm_zone': zona_utm,
            'vertices': vertices_with_utm,
            'grid_step': {
                'value': grid_step_value,
                'unit': self.grid_step_unit.get()
            },
            'grid_origin': {
                'lat': origin_lat,
                'lon': origin_lon,
                'km_x': round(origin_km_x, 3) if origin_km_x is not None else None,
                'km_y': round(origin_km_y, 3) if origin_km_y is not None else None,
                'nx': self.nx.get(),
                'ny': self.ny.get()
            }
        }
        
        # Salva in un file JSON
        config_file = self.temp_dir / 'domain_config.json'
        with open(config_file, 'w') as f:
            json.dump(domain_data, f, indent=4)
        
        if not PYPROJ_AVAILABLE:
            messagebox.showwarning(
                "Avviso", 
                f"Dominio salvato in:\n{config_file}\n\nATTENZIONE: pyproj non disponibile.\nLe coordinate UTM non sono state calcolate.\nInstalla pyproj: pip install pyproj"
            )
        else:
            messagebox.showinfo("Successo", f"Dominio salvato in:\n{config_file}\n\nZona UTM: {zona_utm}")
        
        self.window.destroy()
