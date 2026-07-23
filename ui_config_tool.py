"""
UI Tool per la configurazione delle procedure di simulazione
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import shutil
from pathlib import Path
from datetime import datetime

Required_FOLDERS = ["Outputs", "temp_config", "saved_configurations"]

class ConfiguratorApp:
    """Applicazione principale per la configurazione delle simulazioni"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Configuratore Simulazioni - PM_TEN")
        self.root.geometry("400x660")
        
        # Directory per i file temporanei
        self.temp_dir = Path("temp_config")
        self.temp_dir.mkdir(exist_ok=True)
        
        # Directory per le configurazioni salvate
        self.saved_configs_dir = Path("saved_configurations")
        self.saved_configs_dir.mkdir(exist_ok=True)
        
        for folder in Required_FOLDERS:
            Path(folder).mkdir(exist_ok=True)
        self.setup_ui()
    
    def setup_ui(self):
        """Configura l'interfaccia utente principale"""
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titolo
        title_label = ttk.Label(
            main_frame, 
            text="Configuratore Procedure di Simulazione",
            font=('Arial', 14, 'bold')
        )
        title_label.grid(row=0, column=0, pady=20)
        
        # Bottoni Definisci Dominio / Filetti
        domain_buttons_frame = ttk.Frame(main_frame)
        domain_buttons_frame.grid(row=1, column=0, pady=10)

        define_domain_btn = ttk.Button(
            domain_buttons_frame,
            text="Definisci Dominio",
            command=self.open_domain_window,
            width=18
        )
        define_domain_btn.pack(side=tk.LEFT, padx=(0, 5))

        filetti_btn = ttk.Button(
            domain_buttons_frame,
            text="Filetti",
            command=self.open_filetti_window,
            width=10
        )
        filetti_btn.pack(side=tk.LEFT)
        
        # Bottone Orografia e Uso Terreno
        orography_btn = ttk.Button(
            main_frame,
            text="Orografia e Uso Terreno",
            command=self.open_orography_window,
            width=30
        )
        orography_btn.grid(row=2, column=0, pady=10)
        
        # Bottone Dominio Temporale
        temporal_btn = ttk.Button(
            main_frame,
            text="Dominio Temporale",
            command=self.open_temporal_window,
            width=30
        )
        temporal_btn.grid(row=3, column=0, pady=10)
        
        # Bottone Configura CALMET
        calmet_btn = ttk.Button(
            main_frame,
            text="Configura CALMET",
            command=self.open_calmet_window,
            width=30
        )
        calmet_btn.grid(row=4, column=0, pady=10)
        
        # Bottone Configura CALPUFF
        calpuff_btn = ttk.Button(
            main_frame,
            text="Configura CALPUFF",
            command=self.open_calpuff_window,
            width=30
        )
        calpuff_btn.grid(row=5, column=0, pady=10)
        
        # Bottone Configurazione Farm
        farm_btn = ttk.Button(
            main_frame,
            text="Configurazione Farm",
            command=self.open_farm_window,
            width=30
        )
        farm_btn.grid(row=6, column=0, pady=10)
        
        # Bottone Operazioni sul Farm
        farm_ops_btn = ttk.Button(
            main_frame,
            text="Operazioni sul Farm",
            command=self.open_farm_operations_window,
            width=30
        )
        farm_ops_btn.grid(row=7, column=0, pady=10)

        farm_ops_simple_btn = ttk.Button(
            main_frame,
            text="Operazioni sul Farm (Semplice)",
            command=self.open_farm_operations_window_simple,
            width=30
        )
        farm_ops_simple_btn.grid(row=8, column=0, pady=10)
        
        # Separatore
        ttk.Separator(main_frame, orient='horizontal').grid(row=9, column=0, sticky=(tk.W, tk.E), pady=15)
        
        # Bottone Salva Configurazione
        save_config_btn = ttk.Button(
            main_frame,
            text="💾 Salva Configurazione",
            command=self.save_configuration,
            width=30
        )
        save_config_btn.grid(row=10, column=0, pady=10)
        
        # Bottone Carica Configurazione
        load_config_btn = ttk.Button(
            main_frame,
            text="📂 Carica Configurazione",
            command=self.load_configuration,
            width=30
        )
        load_config_btn.grid(row=11, column=0, pady=10)

        # Bottone pulizia simulazione
        clear_sim_btn = ttk.Button(
            main_frame,
            text="🗑️ Clear Simulazion",
            command=self.clear_simulation,
            width=30
        )
        clear_sim_btn.grid(row=12, column=0, pady=10)

        # Bottone Esci
        exit_btn = ttk.Button(
            main_frame,
            text="Esci",
            command=self.root.quit,
            width=30
        )
        exit_btn.grid(row=13, column=0, pady=10)
        
        # Configura il grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
    
    def open_domain_window(self):
        """Apre la finestra per definire il dominio geografico"""
        from windows.domain_window import DomainWindow
        DomainWindow(self.root, self.temp_dir)

    def open_filetti_window(self):
        """Apre la finestra placeholder per Filetti."""
        from windows.filetti_window import FilettiWindow
        FilettiWindow(self.root, self.temp_dir)
    
    def open_orography_window(self):
        """Apre la finestra per orografia e uso terreno"""
        from windows.orography_window import OrographyWindow
        OrographyWindow(self.root, self.temp_dir)
    
    def open_temporal_window(self):
        """Apre la finestra per il dominio temporale"""
        from windows.temporal_window import TemporalWindow
        TemporalWindow(self.root, self.temp_dir)
    
    def open_calmet_window(self):
        """Apre la finestra per la configurazione CALMET"""
        from windows.calmet_window import CalmetWindow
        CalmetWindow(self.root, self.temp_dir)
    
    def open_calpuff_window(self):
        """Apre la finestra per la configurazione CALPUFF"""
        from windows.calpuff_window import CalpuffWindow
        CalpuffWindow(self.root, self.temp_dir)
    
    def open_farm_window(self):
        """Apre la finestra per la configurazione Farm"""
        from windows.farm_window import FarmWindow
        FarmWindow(self.root, self.temp_dir)
    
    def open_farm_operations_window(self):
        """Apre la finestra per le operazioni sul Farm"""
        from windows.farm_operations_window import FarmOperationsWindow
        FarmOperationsWindow(self.root, self.temp_dir)

    def open_farm_operations_window_simple(self):
        """Apre la finestra per le operazioni sul Farm in modalità semplice"""
        from windows.farm_operations_window_simple import FarmOperationsWindow_simple
        FarmOperationsWindow_simple(self.root, self.temp_dir)

    def clear_simulation(self):
        """Elimina i file temporanei e svuota le cartelle *_INP senza rimuovere le cartelle base."""
        target_folders = [self.temp_dir, Path("Outputs")]
        target_folders.extend(
            sorted(
                (folder for folder in Path(".").glob("*_INP") if folder.is_dir()),
                key=lambda folder: folder.name.lower()
            )
        )

        folder_names = "\n".join(f"• {folder}" for folder in target_folders)
        should_clear = messagebox.askyesno(
            "Conferma Pulizia",
            "Vuoi cancellare tutti i file temporanei e svuotare le cartelle *_INP?\n\n"
            f"Cartelle coinvolte:\n{folder_names}\n\n"
            "Le cartelle principali verranno mantenute, ma il loro contenuto sarà rimosso."
        )
        if not should_clear:
            return

        deleted_files = 0
        deleted_dirs = 0
        errors = []

        for folder in target_folders:
            folder = Path(folder)
            folder.mkdir(exist_ok=True)

            for item in folder.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                        deleted_dirs += 1
                    else:
                        item.unlink()
                        deleted_files += 1
                except Exception as exc:
                    errors.append(f"{item}: {exc}")

        if errors:
            error_details = "\n".join(errors[:10])
            if len(errors) > 10:
                error_details += f"\n... altri {len(errors) - 10} errori"
            messagebox.showwarning(
                "Pulizia completata con avvisi",
                f"Elementi rimossi: {deleted_files} file e {deleted_dirs} cartelle.\n\n"
                f"Alcuni elementi non sono stati eliminati:\n{error_details}"
            )
            return

        messagebox.showinfo(
            "Pulizia completata",
            f"Eliminati {deleted_files} file e {deleted_dirs} cartelle dalle aree temporanee della simulazione."
        )
    
    def save_configuration(self):
        """Salva la configurazione corrente con un nome unico"""
        # Chiedi il nome della configurazione
        config_name = simpledialog.askstring(
            "Salva Configurazione",
            "Inserisci un nome per questa configurazione:",
            parent=self.root
        )
        
        if not config_name:
            return
        
        # Rimuovi caratteri non validi dal nome
        config_name = "".join(c for c in config_name if c.isalnum() or c in (' ', '_', '-')).strip()
        
        if not config_name:
            messagebox.showerror("Errore", "Nome configurazione non valido!")
            return
        
        # Crea timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{config_name}_{timestamp}"
        config_folder = self.saved_configs_dir / folder_name
        
        try:
            config_folder.mkdir(exist_ok=True)
            
            # Copia tutti i file dalla directory temp_config
            files_copied = 0
            for file in self.temp_dir.glob("*.json"):
                destination = config_folder / file.name
                with open(file, 'r', encoding='utf-8') as src:
                    content = src.read()
                with open(destination, 'w', encoding='utf-8') as dst:
                    dst.write(content)
                files_copied += 1
            
            # Salva anche i metadati della configurazione
            metadata = {
                'name': config_name,
                'timestamp': timestamp,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'files_saved': files_copied
            }
            
            metadata_file = config_folder / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo(
                "Successo",
                f"Configurazione '{config_name}' salvata con successo!\n"
                f"File salvati: {files_copied}\n"
                f"Percorso: {config_folder}"
            )
        
        except Exception as e:
            messagebox.showerror(
                "Errore",
                f"Errore durante il salvataggio della configurazione:\n{str(e)}"
            )
    
    def load_configuration(self):
        """Carica una configurazione precedentemente salvata"""
        # Ottieni lista delle configurazioni salvate
        configs = []
        for folder in self.saved_configs_dir.iterdir():
            if folder.is_dir():
                metadata_file = folder / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        configs.append({
                            'folder': folder,
                            'name': metadata.get('name', folder.name),
                            'date': metadata.get('date', 'N/A'),
                            'display': f"{metadata.get('name', folder.name)} - {metadata.get('date', 'N/A')}"
                        })
                    except:
                        # Se non c'è metadata, usa il nome della cartella
                        configs.append({
                            'folder': folder,
                            'name': folder.name,
                            'date': 'N/A',
                            'display': folder.name
                        })
        
        if not configs:
            messagebox.showinfo(
                "Info",
                "Nessuna configurazione salvata trovata."
            )
            return
        
        # Crea finestra di selezione
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Carica Configurazione")
        selection_window.geometry("500x400")
        selection_window.transient(self.root)
        selection_window.grab_set()
        
        # Frame principale
        main_frame = ttk.Frame(selection_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label
        ttk.Label(
            main_frame,
            text="Seleziona la configurazione da caricare:",
            font=('Arial', 10, 'bold')
        ).pack(pady=(0, 10))
        
        # Listbox con scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Arial', 9)
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Popola la listbox usando lo stesso ordine mostrato all'utente
        sorted_configs = sorted(configs, key=lambda x: x['date'], reverse=True)
        for config in sorted_configs:
            listbox.insert(tk.END, config['display'])
        
        selected_config = [None]
        
        def on_load():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Attenzione", "Seleziona una configurazione!")
                return
            
            selected_config[0] = sorted_configs[selection[0]]
            selection_window.destroy()
        
        def on_delete():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Attenzione", "Seleziona una configurazione!")
                return
            
            config_to_delete = sorted_configs[selection[0]]
            
            if messagebox.askyesno(
                "Conferma",
                f"Vuoi eliminare la configurazione '{config_to_delete['name']}'?\n"
                "Questa operazione non può essere annullata."
            ):
                try:
                    import shutil
                    shutil.rmtree(config_to_delete['folder'])
                    messagebox.showinfo("Successo", "Configurazione eliminata!")
                    selection_window.destroy()
                    self.load_configuration()  # Riapri la finestra
                except Exception as e:
                    messagebox.showerror("Errore", f"Errore durante l'eliminazione:\n{str(e)}")
        
        # Bottoni
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Carica", command=on_load).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Elimina", command=on_delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annulla", command=selection_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Aspetta che la finestra venga chiusa
        self.root.wait_window(selection_window)
        
        # Se è stata selezionata una configurazione, caricala
        if selected_config[0]:
            try:
                config_folder = selected_config[0]['folder']
                
                # Copia i file dalla configurazione salvata a temp_config
                files_loaded = 0
                for file in config_folder.glob("*.json"):
                    if file.name != "metadata.json":
                        os.path.exists(self.temp_dir) or self.temp_dir.mkdir()
                        destination = self.temp_dir / file.name
                        with open(file, 'r', encoding='utf-8') as src:
                            content = src.read()
                        with open(destination, 'w', encoding='utf-8') as dst:
                            dst.write(content)
                        files_loaded += 1
                
                messagebox.showinfo(
                    "Successo",
                    f"Configurazione '{selected_config[0]['name']}' caricata con successo!\n"
                    f"File caricati: {files_loaded}"
                )
            
            except Exception as e:
                messagebox.showerror(
                    "Errore",
                    f"Errore durante il caricamento della configurazione:\n{str(e)}"
                )


def main():
    """Funzione principale"""
    root = tk.Tk()
    app = ConfiguratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
