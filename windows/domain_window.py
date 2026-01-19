"""
Finestra per la definizione del dominio geografico
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
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
        
        # Origine griglia
        self.origin_lat = tk.DoubleVar(value=45.0)
        self.origin_lon = tk.DoubleVar(value=9.0)
        self.nx = tk.IntVar(value=100)
        self.ny = tk.IntVar(value=100)
        
        # Markers sulla mappa
        self.map_markers = {}
        self.map_polygons = []
        
        # Flag per evitare loop infiniti nei callback
        self.updating_vertices = False
        
        self.setup_ui()
        
        # Aggiungi callback per aggiornare la mappa quando cambia l'origine
        self.origin_lat.trace_add('write', lambda *args: self.window.after(100, self.update_map))
        self.origin_lon.trace_add('write', lambda *args: self.window.after(100, self.update_map))
        
        self.update_map()
    
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
        
        # Vertice Nord-Ovest
        self.create_vertex_inputs(controls_frame, "Nord-Ovest (NW)", "NW", 0)
        
        # Vertice Nord-Est
        self.create_vertex_inputs(controls_frame, "Nord-Est (NE)", "NE", 2)
        
        # Vertice Sud-Est
        self.create_vertex_inputs(controls_frame, "Sud-Est (SE)", "SE", 4)
        
        # Vertice Sud-Ovest
        self.create_vertex_inputs(controls_frame, "Sud-Ovest (SW)", "SW", 6)
        
        # Separatore
        ttk.Separator(controls_frame, orient='horizontal').grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Passo della griglia
        ttk.Label(controls_frame, text="Passo Griglia:", font=('Arial', 10, 'bold')).grid(row=9, column=0, columnspan=3, sticky=tk.W, pady=(5, 2))
        
        step_frame = ttk.Frame(controls_frame)
        step_frame.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Entry(step_frame, textvariable=self.grid_step, width=15).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Combobox(step_frame, textvariable=self.grid_step_unit, values=['km', 'gradi'], state='readonly', width=10).pack(side=tk.LEFT)
        
        # Separatore
        ttk.Separator(controls_frame, orient='horizontal').grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Origine Griglia
        ttk.Label(controls_frame, text="Origine Griglia:", font=('Arial', 10, 'bold')).grid(row=12, column=0, columnspan=3, sticky=tk.W, pady=(5, 2))
        
        # Latitudine origine
        origin_frame1 = ttk.Frame(controls_frame)
        origin_frame1.grid(row=13, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(origin_frame1, text="Lat:").pack(side=tk.LEFT, padx=(10, 5))
        ttk.Entry(origin_frame1, textvariable=self.origin_lat, width=15).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(origin_frame1, text="Lon:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(origin_frame1, textvariable=self.origin_lon, width=15).pack(side=tk.LEFT)
        
        # NX e NY
        origin_frame2 = ttk.Frame(controls_frame)
        origin_frame2.grid(row=14, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(origin_frame2, text="NX:").pack(side=tk.LEFT, padx=(10, 5))
        ttk.Entry(origin_frame2, textvariable=self.nx, width=15).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(origin_frame2, text="NY:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(origin_frame2, textvariable=self.ny, width=15).pack(side=tk.LEFT)
        
        # Bottoni azione
        button_frame = ttk.Frame(controls_frame)
        button_frame.grid(row=15, column=0, columnspan=3, pady=20)
        
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
    
    def create_vertex_inputs(self, parent, label, vertex_key, row):
        """Crea gli input per un vertice"""
        ttk.Label(parent, text=label, font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(5, 2))
        
        # Latitudine
        ttk.Label(parent, text="Lat:").grid(row=row+1, column=0, sticky=tk.W, padx=(10, 5))
        lat_var = tk.DoubleVar(value=self.vertices[vertex_key]['lat'])
        lat_entry = ttk.Entry(parent, textvariable=lat_var, width=15)
        lat_entry.grid(row=row+1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Longitudine
        ttk.Label(parent, text="Lon:").grid(row=row+1, column=2, sticky=tk.W, padx=(10, 5))
        lon_var = tk.DoubleVar(value=self.vertices[vertex_key]['lon'])
        lon_entry = ttk.Entry(parent, textvariable=lon_var, width=15)
        lon_entry.grid(row=row+1, column=2, sticky=(tk.W, tk.E), pady=2, padx=(40, 0))
        
        # Salva i riferimenti alle variabili
        setattr(self, f'{vertex_key}_lat', lat_var)
        setattr(self, f'{vertex_key}_lon', lon_var)
        
        # Aggiungi callback per mantenere il vincolo del rettangolo
        lat_var.trace_add('write', lambda *args: self.on_vertex_change(vertex_key, 'lat'))
        lon_var.trace_add('write', lambda *args: self.on_vertex_change(vertex_key, 'lon'))
    
    def on_vertex_change(self, vertex_key, coord_type):
        """Gestisce le modifiche ai vertici per mantenere il vincolo del rettangolo"""
        if self.updating_vertices:
            return
        
        self.updating_vertices = True
        
        try:
            # Vincoli del rettangolo:
            # NW e NE condividono la stessa latitudine (lato nord)
            # SE e SW condividono la stessa latitudine (lato sud)
            # NE e SE condividono la stessa longitudine (lato est)
            # NW e SW condividono la stessa longitudine (lato ovest)
            
            if vertex_key == 'NW':
                if coord_type == 'lat':
                    # Aggiorna NE lat (lato nord)
                    self.NE_lat.set(self.NW_lat.get())
                else:  # lon
                    # Aggiorna SW lon (lato ovest)
                    self.SW_lon.set(self.NW_lon.get())
            
            elif vertex_key == 'NE':
                if coord_type == 'lat':
                    # Aggiorna NW lat (lato nord)
                    self.NW_lat.set(self.NE_lat.get())
                else:  # lon
                    # Aggiorna SE lon (lato est)
                    self.SE_lon.set(self.NE_lon.get())
            
            elif vertex_key == 'SE':
                if coord_type == 'lat':
                    # Aggiorna SW lat (lato sud)
                    self.SW_lat.set(self.SE_lat.get())
                else:  # lon
                    # Aggiorna NE lon (lato est)
                    self.NE_lon.set(self.SE_lon.get())
            
            elif vertex_key == 'SW':
                if coord_type == 'lat':
                    # Aggiorna SE lat (lato sud)
                    self.SE_lat.set(self.SW_lat.get())
                else:  # lon
                    # Aggiorna NW lon (lato ovest)
                    self.NW_lon.set(self.SW_lon.get())
            
            # Aggiorna automaticamente la mappa
            self.window.after(100, self.update_map)
        
        except tk.TclError:
            # Ignora errori durante la modifica
            pass
        finally:
            self.updating_vertices = False
    
    def update_vertices_from_ui(self):
        """Aggiorna i vertici dalle celle di input"""
        try:
            self.vertices['NW']['lat'] = self.NW_lat.get()
            self.vertices['NW']['lon'] = self.NW_lon.get()
            self.vertices['NE']['lat'] = self.NE_lat.get()
            self.vertices['NE']['lon'] = self.NE_lon.get()
            self.vertices['SE']['lat'] = self.SE_lat.get()
            self.vertices['SE']['lon'] = self.SE_lon.get()
            self.vertices['SW']['lat'] = self.SW_lat.get()
            self.vertices['SW']['lon'] = self.SW_lon.get()
            return True
        except tk.TclError:
            messagebox.showerror("Errore", "Inserire valori numerici validi per latitudine e longitudine")
            return False
    
    def update_map(self):
        """Aggiorna la mappa con i vertici correnti"""
        if not self.update_vertices_from_ui():
            return
        
        if self.map_widget is None:
            messagebox.showinfo("Info", "Mappa non disponibile. Installa tkintermapview.")
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
            
            print("Mappa aggiornata con successo")
            
        except Exception as e:
            print(f"Errore in update_map: {e}")
            messagebox.showerror("Errore", f"Errore nell'aggiornamento della mappa: {str(e)}")
    
    def lat_lon_to_utm(self, lat, lon):
        """Converte coordinate lat/lon in coordinate UTM (km)
        
        Returns:
            tuple: (zona_utm, km_x, km_y) dove zona_utm è stringa tipo '32N'
        """
        if not PYPROJ_AVAILABLE:
            return None, None, None
        
        try:
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
        if not self.update_vertices_from_ui():
            return
        
        try:
            grid_step_value = float(self.grid_step.get())
        except ValueError:
            messagebox.showerror("Errore", "Inserire un valore numerico valido per il passo della griglia")
            return
        
        # Converti le coordinate in UTM per ciascun vertice
        vertices_with_utm = {}
        zona_utm = None
        
        for key, vertex in self.vertices.items():
            lat = vertex['lat']
            lon = vertex['lon']
            
            # Converti in UTM
            zona, km_x, km_y = self.lat_lon_to_utm(lat, lon)
            
            # Salva la zona del primo vertice (dovrebbero essere tutti nella stessa zona)
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
        origin_zona, origin_km_x, origin_km_y = self.lat_lon_to_utm(origin_lat, origin_lon)
        
        domain_data = {
            'zona_utm': zona_utm,
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
