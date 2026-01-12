"""
Finestra per la selezione e creazione di file orografia e uso terreno
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json
import numpy as np
import threading

try:
    import rasterio
    import pyproj
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False


class ProgressWindow:
    """Finestra di progresso con barra di caricamento"""
    
    def __init__(self, parent, title="Elaborazione in corso..."):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x150")
        self.window.resizable(False, False)
        
        # Rendi la finestra modale
        self.window.transient(parent)
        self.window.grab_set()
        
        # Centra la finestra
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.window.winfo_screenheight() // 2) - (150 // 2)
        self.window.geometry(f"400x150+{x}+{y}")
        
        # Frame principale
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label status
        self.status_label = ttk.Label(
            main_frame,
            text="Inizializzazione...",
            font=('Arial', 10)
        )
        self.status_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame,
            mode='determinate',
            length=360
        )
        self.progress.pack(pady=10)
        
        # Label percentuale
        self.percent_label = ttk.Label(
            main_frame,
            text="0%",
            font=('Arial', 9)
        )
        self.percent_label.pack(pady=(0, 10))
        
        self.window.protocol("WM_DELETE_WINDOW", lambda: None)  # Disabilita chiusura
    
    def update_progress(self, value, status_text=""):
        """Aggiorna la barra di progresso
        
        Args:
            value: valore da 0 a 100
            status_text: testo di stato opzionale
        """
        self.progress['value'] = value
        self.percent_label.config(text=f"{int(value)}%")
        if status_text:
            self.status_label.config(text=status_text)
        self.window.update()
    
    def close(self):
        """Chiude la finestra"""
        self.window.grab_release()
        self.window.destroy()


class OrographyWindow:
    """Finestra per gestire orografia e uso terreno"""
    
    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = temp_dir
        self.window = tk.Toplevel(parent)
        self.window.title("Orografia e Uso Terreno")
        self.window.geometry("700x600")
        
        # Directory default per i file
        self.default_dir = Path("Working_Files")
        
        # Variabili per i percorsi dei file
        self.orography_file = tk.StringVar(value="")
        self.landuse_file = tk.StringVar(value="")
        
        # Variabili per i file di output
        self.output_grid = tk.StringVar(value="Outputs\\grd_xyz.txt")
        self.output_oro = tk.StringVar(value="Outputs\\oro.txt")
        self.output_landuse = tk.StringVar(value="Outputs\\landuse.xyz")
        
        # Cerca file di default nella cartella Working_Files
        self.find_default_files()
        
        self.setup_ui()
    
    def find_default_files(self):
        """Cerca file di default nella cartella Working_Files"""
        if not self.default_dir.exists():
            return
        
        # Cerca file orografia (file .xyz)
        xyz_files = list(self.default_dir.glob("*.xyz"))
        if xyz_files:
            # Prendi il primo file .xyz come default per orografia
            self.orography_file.set(str(xyz_files[0]))
        
        # Cerca file uso terreno (file .tif)
        tif_files = list(self.default_dir.glob("*.tif"))
        if tif_files:
            # Prendi il primo file .tif come default per uso terreno
            self.landuse_file.set(str(tif_files[0]))
    
    def setup_ui(self):
        """Configura l'interfaccia della finestra"""
        # Frame principale
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configura il grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Titolo
        title_label = ttk.Label(
            main_frame, 
            text="Selezione File Orografia e Uso Terreno",
            font=('Arial', 12, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # === SEZIONE OROGRAFIA ===
        ttk.Label(
            main_frame, 
            text="File Orografia:",
            font=('Arial', 10, 'bold')
        ).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        # Entry per file orografia
        orography_entry = ttk.Entry(
            main_frame, 
            textvariable=self.orography_file,
            width=50
        )
        orography_entry.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Bottone sfoglia orografia
        ttk.Button(
            main_frame,
            text="Sfoglia...",
            command=self.browse_orography_file,
            width=12
        ).grid(row=2, column=2, padx=(5, 0), pady=(0, 5))
        
        # Output Grid
        ttk.Label(
            main_frame,
            text="Output Grid:"
        ).grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        
        ttk.Entry(
            main_frame,
            textvariable=self.output_grid,
            width=50
        ).grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Output Oro
        ttk.Label(
            main_frame,
            text="Output Oro:"
        ).grid(row=5, column=0, sticky=tk.W, pady=(5, 5))
        
        ttk.Entry(
            main_frame,
            textvariable=self.output_oro,
            width=50
        ).grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Bottone crea orografia
        ttk.Button(
            main_frame,
            text="Crea Orografia",
            command=self.create_orography,
            width=20
        ).grid(row=7, column=0, columnspan=3, pady=(5, 20))
        
        # Separatore
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )
        
        # === SEZIONE USO TERRENO ===
        ttk.Label(
            main_frame, 
            text="File Uso Terreno:",
            font=('Arial', 10, 'bold')
        ).grid(row=9, column=0, sticky=tk.W, pady=(0, 5))
        
        # Entry per file uso terreno
        landuse_entry = ttk.Entry(
            main_frame, 
            textvariable=self.landuse_file,
            width=50
        )
        landuse_entry.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Bottone sfoglia uso terreno
        ttk.Button(
            main_frame,
            text="Sfoglia...",
            command=self.browse_landuse_file,
            width=12
        ).grid(row=10, column=2, padx=(5, 0), pady=(0, 5))
        
        # Output Landuse
        ttk.Label(
            main_frame,
            text="Output Landuse:"
        ).grid(row=11, column=0, sticky=tk.W, pady=(10, 5))
        
        ttk.Entry(
            main_frame,
            textvariable=self.output_landuse,
            width=50
        ).grid(row=12, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Bottone crea uso terreno
        ttk.Button(
            main_frame,
            text="Crea Uso Terreno",
            command=self.create_landuse,
            width=20
        ).grid(row=13, column=0, columnspan=3, pady=(5, 20))
        
        # Separatore
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=14, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )
        
        # Bottone chiudi
        ttk.Button(
            main_frame,
            text="Chiudi",
            command=self.window.destroy,
            width=20
        ).grid(row=15, column=0, columnspan=3, pady=(10, 0))
    
    def browse_orography_file(self):
        """Apre dialog per selezionare il file orografia"""
        initial_dir = self.default_dir if self.default_dir.exists() else Path.home()
        
        filename = filedialog.askopenfilename(
            parent=self.window,
            title="Seleziona File Orografia",
            initialdir=initial_dir,
            filetypes=[
                ("File XYZ", "*.xyz"),
                ("Tutti i file", "*.*")
            ]
        )
        
        if filename:
            self.orography_file.set(filename)
    
    def browse_landuse_file(self):
        """Apre dialog per selezionare il file uso terreno"""
        initial_dir = self.default_dir if self.default_dir.exists() else Path.home()
        
        filename = filedialog.askopenfilename(
            parent=self.window,
            title="Seleziona File Uso Terreno",
            initialdir=initial_dir,
            filetypes=[
                ("File TIFF", "*.tif"),
                ("File TIFF", "*.tiff"),
                ("Tutti i file", "*.*")
            ]
        )
        
        if filename:
            self.landuse_file.set(filename)
    
    def create_orography(self):
        """Crea il file orografia (implementazione da definire)"""
        orography_path = self.orography_file.get()
        
        if not orography_path:
            messagebox.showerror(
                "Errore",
                "Selezionare un file orografia prima di procedere"
            )
            return
        
        if not Path(orography_path).exists():
            messagebox.showerror(
                "Errore",
                f"Il file selezionato non esiste:\n{orography_path}"
            )
            return
        
        # Legge la configurazione del dominio
        domain_config_file = self.temp_dir / 'domain_config.json'
        if not domain_config_file.exists():
            messagebox.showerror(
                "Errore",
                "Configurazione del dominio non trovata.\nDefinire prima il dominio."
            )
            return
        
        try:
            with open(domain_config_file, 'r') as f:
                domain_config = json.load(f)
        except Exception as e:
            messagebox.showerror(
                "Errore",
                f"Errore nella lettura della configurazione del dominio:\n{str(e)}"
            )
            return
        
        # Estrae i bordi dal dominio (usando le coordinate km_x, km_y)
        vertices = domain_config.get('vertices', {})
        
        # Calcola i bordi X e Y dalle coordinate dei vertici
        x_coords = [v['km_x'] for v in vertices.values() if v.get('km_x') is not None]
        y_coords = [v['km_y'] for v in vertices.values() if v.get('km_y') is not None]
        
        if not x_coords or not y_coords:
            messagebox.showerror(
                "Errore",
                "Coordinate UTM non trovate nella configurazione del dominio.\nRicreare la configurazione del dominio."
            )
            return
        
        # Converti km in metri (i file di orografia usano metri)
        x_border = (min(x_coords) * 1000, max(x_coords) * 1000)
        y_border = (min(y_coords) * 1000, max(y_coords) * 1000)
        
        output_grid = self.output_grid.get()
        output_oro = self.output_oro.get()
        
        config_file = self.temp_dir / 'orography_config.json'
        
        # Esegue l'elaborazione (con possibilità di retry con lat-lon)
        self._execute_orography_processing(
            orography_path,
            output_grid,
            output_oro,
            x_border,
            y_border,
            config_file,
            domain_config,
            use_latlon=False
        )
    
    def _execute_orography_processing(self, orography_path, output_grid, output_oro, 
                                       x_border, y_border, config_file, domain_config, use_latlon=False):
        """Esegue il processing dell'orografia, con supporto per retry in lat-lon"""
        
        # Crea la finestra di progresso
        title = "Creazione Orografia (Lat-Lon)" if use_latlon else "Creazione Orografia"
        progress_window = ProgressWindow(self.window, title)
        
        # Variabile per memorizzare il risultato
        result = {'success': False, 'error': None, 'no_points': False}
        
        # Esegue l'elaborazione in un thread separato
        def process_thread():
            try:
                progress_window.update_progress(10, "Lettura file di input...")
                
                self.process_orography(
                    orography_path,
                    output_grid,
                    output_oro,
                    x_border,
                    y_border,
                    progress_window,
                    use_latlon=use_latlon
                )
                
                # Se successo, salva la configurazione
                orography_config = {
                    'input_file': orography_path,
                    'output_grid': output_grid,
                    'output_oro': output_oro,
                    'x_border': list(x_border),
                    'y_border': list(y_border),
                    'zona_utm': domain_config.get('zona_utm', 'N/A'),
                    'use_latlon': use_latlon,  # Salva se sono state usate coordinate lat-lon
                    'coordinate_type': 'lat-lon' if use_latlon else 'UTM'
                }
                
                with open(config_file, 'w') as f:
                    json.dump(orography_config, f, indent=4)
                
                result['success'] = True
                progress_window.update_progress(100, "Completato!")
            except ValueError as e:
                # Errore di validazione (nessun punto trovato)
                result['error'] = str(e)
                result['no_points'] = 'Nessun punto trovato' in str(e)
            except Exception as e:
                result['error'] = str(e)
            finally:
                # Chiude la finestra dopo un breve ritardo
                self.window.after(500, progress_window.close)
        
        # Avvia il thread
        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()
        
        # Attende la chiusura della finestra di progresso
        self.window.wait_window(progress_window.window)
        
        # Mostra il risultato
        if result['success']:
            messagebox.showinfo(
                "Successo",
                f"Orografia creata con successo!\n\n"
                f"Configurazione salvata: {config_file}\n"
                f"Output Grid: {output_grid}\n"
                f"Output Oro: {output_oro}"
            )
        elif result['no_points'] and not use_latlon:
            # Offre l'opzione di riprovare con lat-lon
            retry = messagebox.askyesno(
                "Nessun Punto Trovato",
                f"{result['error']}\n\n"
                f"Vuoi riprovare usando le coordinate Lat-Lon\n"
                f"invece delle coordinate UTM?",
                icon='warning'
            )
            
            if retry:
                # Calcola i bordi in lat-lon
                vertices = domain_config.get('vertices', {})
                lat_coords = [v['lat'] for v in vertices.values() if v.get('lat') is not None]
                lon_coords = [v['lon'] for v in vertices.values() if v.get('lon') is not None]
                
                lat_border = (min(lat_coords), max(lat_coords))
                lon_border = (min(lon_coords), max(lon_coords))
                
                # Riprova con lat-lon (x_border=lon, y_border=lat)
                self._execute_orography_processing(
                    orography_path,
                    output_grid,
                    output_oro,
                    lon_border,  # x_border = longitudine
                    lat_border,  # y_border = latitudine
                    config_file,
                    domain_config,
                    use_latlon=True
                )
        else:
            messagebox.showerror(
                "Errore",
                f"Errore durante la creazione dell'orografia:\n{result['error']}"
            )
    
    def process_orography(self, input_file, output_grid, output_oro, x_border, y_border, progress_window=None, use_latlon=False):
        """Processa il file di orografia (equivalente a red_oro.py)
        
        Args:
            use_latlon: Se True, interpreta x_border come longitudine e y_border come latitudine
        """
        ndata = 100000000
        null = -999
        
        maxx, maxy = float('-inf'), float('-inf')
        minx, miny = float('inf'), float('inf')
        
        # Prima passata: conta le righe totali per la progress bar
        if progress_window:
            progress_window.update_progress(15, "Conteggio righe...")
        
        total_lines = 0
        with open(input_file, 'r') as f:
            for _ in f:
                total_lines += 1
                if total_lines >= ndata:
                    break
        
        if progress_window:
            progress_window.update_progress(20, "Elaborazione dati...")
        
        processed_lines = 0
        points_found = 0  # Contatore per i punti trovati all'interno del dominio
        last_progress = 20
        
        with open(input_file, 'r') as f_in, \
             open(output_grid, 'w') as f_out1, \
             open(output_oro, 'w') as f_out2:
            
            # Scrive intestazioni fisse nei file di output
            f_out2.write("1\n1\n32\n")
            
            # Cicla su ogni riga del file di input
            for i, line in enumerate(f_in):
                if i >= ndata:
                    break
                
                # Estrae le coordinate x, y e il valore z dalla riga
                x, y, z = map(float, line.split())
                
                # Considera solo i punti all'interno dei bordi specificati
                if y_border[0] <= y <= y_border[1] and x_border[0] <= x <= x_border[1]:
                    points_found += 1  # Incrementa il contatore
                    if z != -32768:  # Valore valido
                        f_out1.write(f'{x:14.2f}{y:15.2f}\n')
                        f_out2.write(f'{x:14.2f}{y:15.2f}{int(z):10d}\n')
                    else:  # Valore nullo
                        f_out1.write(f'{x:14.2f}{y:15.2f}\n')
                        f_out2.write(f'{x:14.2f}{y:15.2f}{null:10d}\n')
                
                # Aggiorna i valori estremi delle coordinate
                maxx = max(maxx, x)
                maxy = max(maxy, y)
                minx = min(minx, x)
                miny = min(miny, y)
                
                # Aggiorna la progress bar ogni 1000 righe
                processed_lines += 1
                if progress_window and processed_lines % 1000 == 0:
                    # Calcola il progresso (da 20% a 95%)
                    current_progress = 20 + int((processed_lines / total_lines) * 75)
                    if current_progress > last_progress:
                        last_progress = current_progress
                        progress_window.update_progress(
                            current_progress,
                            f"Elaborate {processed_lines:,} / {total_lines:,} righe..."
                        )
        
        if progress_window:
            progress_window.update_progress(95, "Finalizzazione...")
        
        # Verifica se sono stati trovati punti all'interno del dominio
        if points_found == 0:
            raise ValueError(
                f"Nessun punto trovato all'interno del dominio specificato.\n\n"
                f"Bordi dominio:\n"
                f"X: {x_border[0]:,.2f} - {x_border[1]:,.2f}\n"
                f"Y: {y_border[0]:,.2f} - {y_border[1]:,.2f}\n\n"
                f"Range dati orografia:\n"
                f"X: {minx:,.2f} - {maxx:,.2f}\n"
                f"Y: {miny:,.2f} - {maxy:,.2f}\n\n"
                f"Suggerimento: Cambiare il file Orografia o verificare\n"
                f"che il dominio sia stato definito correttamente."
            )
        
        print(f"Coordinate elaborate - Max: ({maxx}, {maxy}), Min: ({minx}, {miny})")
        print(f"Punti trovati all'interno del dominio: {points_found}")
    
    def create_landuse(self):
        """Crea il file uso terreno"""
        if not RASTERIO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Librerie mancanti per l'elaborazione uso terreno.\n\n"
                "Installare: pip install rasterio pyproj"
            )
            return
        
        landuse_path = self.landuse_file.get()
        
        if not landuse_path:
            messagebox.showerror(
                "Errore",
                "Selezionare un file uso terreno prima di procedere"
            )
            return
        
        if not Path(landuse_path).exists():
            messagebox.showerror(
                "Errore",
                f"Il file selezionato non esiste:\n{landuse_path}"
            )
            return
        
        # Verifica che esista il file grid (creato da orografia)
        grid_file = self.output_grid.get()
        if not Path(grid_file).exists():
            messagebox.showerror(
                "Errore",
                f"File grid non trovato: {grid_file}\n\n"
                f"Creare prima l'orografia per generare il file grid."
            )
            return
        
        # Legge la configurazione dell'orografia per sapere il tipo di coordinate usate
        orography_config_file = self.temp_dir / 'orography_config.json'
        use_latlon = False
        zona_utm = '32N'  # Default
        
        if orography_config_file.exists():
            try:
                with open(orography_config_file, 'r') as f:
                    orography_config = json.load(f)
                    use_latlon = orography_config.get('use_latlon', False)
                    zona_utm = orography_config.get('zona_utm', '32N')
                    coord_type = orography_config.get('coordinate_type', 'UTM')
                    
                    print(f"Grid creato con coordinate: {coord_type}")
            except Exception as e:
                messagebox.showwarning(
                    "Avviso",
                    f"Impossibile leggere la configurazione orografia.\n"
                    f"Si assume coordinate UTM.\n\nErrore: {e}"
                )
        
        output_landuse = self.output_landuse.get()
        
        # Salva configurazione uso terreno in JSON
        landuse_config = {
            'input_file': landuse_path,
            'grid_file': grid_file,
            'output_file': output_landuse,
            'use_latlon': use_latlon,
            'zona_utm': zona_utm
        }
        
        config_file = self.temp_dir / 'landuse_config.json'
        with open(config_file, 'w') as f:
            json.dump(landuse_config, f, indent=4)
        
        # Crea la finestra di progresso
        progress_window = ProgressWindow(self.window, "Creazione Uso Terreno")
        
        # Variabile per memorizzare il risultato
        result = {'success': False, 'error': None}
        
        # Esegue l'elaborazione in un thread separato
        def process_thread():
            try:
                progress_window.update_progress(10, "Lettura file di input...")
                
                self.process_landuse(
                    landuse_path,
                    grid_file,
                    output_landuse,
                    progress_window,
                    use_latlon=use_latlon,
                    zona_utm=zona_utm
                )
                
                result['success'] = True
                progress_window.update_progress(100, "Completato!")
            except Exception as e:
                result['error'] = str(e)
            finally:
                # Chiude la finestra dopo un breve ritardo
                self.window.after(500, progress_window.close)
        
        # Avvia il thread
        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()
        
        # Attende la chiusura della finestra di progresso
        self.window.wait_window(progress_window.window)
        
        # Mostra il risultato
        if result['success']:
            messagebox.showinfo(
                "Successo",
                f"Uso terreno creato con successo!\n\n"
                f"Configurazione salvata: {config_file}\n"
                f"Output: {output_landuse}"
            )
        else:
            messagebox.showerror(
                "Errore",
                f"Errore durante la creazione dell'uso terreno:\n{result['error']}"
            )
    
    def process_landuse(self, tif_file, grid_file, output_file, progress_window=None, use_latlon=False, zona_utm='32N'):
        """Processa il file GeoTIFF per creare il file uso terreno
        
        Args:
            use_latlon: Se True, il grid contiene coordinate lat-lon invece di UTM
            zona_utm: Zona UTM (es. '32N') da usare se use_latlon=False
        """
        # Mapping CORINE (invertito per lookup veloce)
        MAP_CORINE_A = {
            1: 111, 2: 112, 3: 121, 4: 122, 5: 123, 6: 124, 7: 131, 8: 132, 9: 133,
            10: 141, 11: 142, 12: 211, 13: 212, 14: 213, 15: 221, 16: 222, 17: 223,
            18: 231, 19: 241, 20: 242, 21: 243, 22: 244, 23: 311, 24: 312, 25: 313,
            26: 321, 27: 322, 28: 323, 29: 324, 30: 331, 31: 332, 32: 333, 33: 334,
            34: 335, 35: 411, 36: 412, 37: 421, 38: 422, 39: 423, 40: 511, 41: 512,
            42: 521, 43: 522, 44: 523, 48: 999, 49: 990, 50: 995, 255: 990,
        }
        mapping_lookup = {v: k for k, v in MAP_CORINE_A.items()}
        
        if progress_window:
            progress_window.update_progress(15, "Lettura file grid...")
        
        # Legge le coordinate dalla griglia
        points = np.loadtxt(grid_file, ndmin=2)
        points = points[:, -2:]  # Ultime 2 colonne
        
        if progress_window:
            progress_window.update_progress(25, "Apertura GeoTIFF...")
        
        # Crea directory di output se non esiste
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        with rasterio.open(tif_file) as src:
            if progress_window:
                progress_window.update_progress(35, "Lettura raster...")
            
            # Legge il primo band
            raster_data = src.read(1)
            transform_raster = src.transform
            
            # Costruisce i CRS
            crs_raster = pyproj.CRS(src.crs)
            
            # Estrae il numero di zona da zona_utm (es. '32N' -> 32)
            zone_number = int(''.join(filter(str.isdigit, zona_utm)))
            
            if use_latlon:
                # Le coordinate nel grid sono già lat-lon (WGS84)
                crs_grid = pyproj.CRS({
                    'proj': 'longlat', 'ellps': 'WGS84',
                    'datum': 'WGS84', 'no_defs': True
                })
                # Nel grid: colonna 0 = lon, colonna 1 = lat
                grid_x, grid_y = points[:, 0], points[:, 1]  # lon, lat
            else:
                # Le coordinate nel grid sono UTM (in metri)
                crs_grid = pyproj.CRS({
                    'proj': 'utm', 'zone': zone_number, 'ellps': 'WGS84',
                    'datum': 'WGS84', 'units': 'm', 'no_defs': True
                })
                # Nel grid: colonna 0 = x_utm, colonna 1 = y_utm
                grid_x, grid_y = points[:, 0], points[:, 1]
            
            crs_wgs84 = pyproj.CRS({
                'proj': 'longlat', 'ellps': 'WGS84',
                'datum': 'WGS84', 'no_defs': True
            })
            
            if progress_window:
                progress_window.update_progress(45, "Trasformazione coordinate...")
            
            # Crea i transformers
            transformer_to_raster = pyproj.Transformer.from_crs(crs_grid, crs_raster, always_xy=True)
            transformer_to_wgs84 = pyproj.Transformer.from_crs(crs_raster, crs_wgs84, always_xy=True)
            
            # Trasforma i punti dal CRS del grid al CRS del raster
            rast_x, rast_y = transformer_to_raster.transform(grid_x, grid_y)
            
            if progress_window:
                progress_window.update_progress(60, "Calcolo indici pixel...")
            
            # Calcola gli indici dei pixel
            if transform_raster.b == 0 and transform_raster.d == 0:
                # Raster north-up standard
                a, c = transform_raster.a, transform_raster.c
                e, f = transform_raster.e, transform_raster.f
                
                cols = np.floor((rast_x - c) / a).astype(int)
                rows = np.floor((f - rast_y) / abs(e)).astype(int)
                x_center = c + (cols + 0.5) * a
                y_center = f + (rows + 0.5) * e
            else:
                # Fallback per raster ruotati
                rows, cols, x_center, y_center = [], [], [], []
                for x, y in zip(rast_x, rast_y):
                    row, col = src.index(x, y)
                    rows.append(row)
                    cols.append(col)
                    xc, yc = src.xy(row, col)
                    x_center.append(xc)
                    y_center.append(yc)
                rows = np.array(rows)
                cols = np.array(cols)
                x_center = np.array(x_center)
                y_center = np.array(y_center)
            
            if progress_window:
                progress_window.update_progress(70, "Estrazione valori raster...")
            
            # Estrae i valori dei pixel e converti a int32 per evitare overflow
            values = raster_data[rows, cols].astype(np.int32)
            
            # Crea lookup table veloce per il mapping
            min_val = int(raster_data.min())
            max_val = int(raster_data.max())
            offset = -min_val
            lookup_array = np.full(max_val - min_val + 1, 999, dtype=np.int32)
            for orig, new in mapping_lookup.items():
                if min_val <= orig <= max_val:
                    lookup_array[orig + offset] = new
            
            # Assicurati che values + offset non causi overflow
            indices = (values + offset).astype(np.int32)
            # Limita gli indici per evitare out of bounds
            indices = np.clip(indices, 0, len(lookup_array) - 1)
            mapped_values = lookup_array[indices]
            
            if progress_window:
                progress_window.update_progress(85, "Trasformazione a WGS84...")
            
            # Trasforma i centri dei pixel a WGS84
            longs, lats = transformer_to_wgs84.transform(x_center, y_center)
            longs = np.round(longs, 8)
            lats = np.round(lats, 9)
            
            if progress_window:
                progress_window.update_progress(95, "Salvataggio output...")
            
            # Prepara e salva l'output
            out_arr = np.column_stack((longs, lats, mapped_values))
            np.savetxt(output_file, out_arr, fmt='%.8f\t%.9f\t%d', delimiter='\t')
        
        print(f"Uso terreno creato: {len(points)} punti processati")
