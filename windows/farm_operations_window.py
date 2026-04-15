"""
Finestra per le operazioni sul Farm remoto
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
from pathlib import Path
import threading
import os
import re
from service.ctgproc_inp_writer import generate_ctgproc_inp
from service.makegeo_inp_writer import generate_makegeo_inp
from service.terrel_inp_writer import generate_terrel_inp

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False


class FarmOperationsWindow:
    """Finestra per eseguire operazioni sul Farm remoto"""
    
    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = temp_dir
        self.window = tk.Toplevel(parent)
        self.window.title("Operazioni sul Farm")
        self.window.geometry("1000x800")
        
        # Variabili per la connessione
        self.ssh_client = None
        
        # Variabili per le password
        self.jump_password = tk.StringVar()
        self.target_password = tk.StringVar()
        self.same_credentials = tk.BooleanVar(value=True)
        
        # Carica configurazione farm
        self.farm_config = self.load_farm_config()
        self._script_template_cache = {}
        
        self.setup_ui()

    def _get_scripts_root(self):
        """Restituisce la cartella locale con i template script."""
        return Path(__file__).resolve().parent.parent / "Working_Files" / "scripts"

    def _load_script_template(self, relative_path):
        """Carica un template script da Working_Files/scripts con cache in memoria."""
        cache_key = str(relative_path).replace('\\', '/')
        if cache_key in self._script_template_cache:
            return self._script_template_cache[cache_key]

        template_path = self._get_scripts_root() / relative_path
        try:
            template_content = template_path.read_text(encoding='utf-8')
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"Template script non trovato: {template_path}. "
                "Verifica i file in Working_Files/scripts."
            ) from exc

        self._script_template_cache[cache_key] = template_content
        return template_content

    def _render_script_template(self, relative_path, placeholders):
        """Renderizza un template sostituendo solo placeholder ${TPL_*}."""
        template_content = self._load_script_template(relative_path)
        token_pattern = re.compile(r"\$\{([A-Z0-9_]+)\}")

        def _replace(match):
            key = match.group(1)
            if key in placeholders:
                return str(placeholders[key])
            return match.group(0)

        rendered = token_pattern.sub(_replace, template_content)
        unresolved = sorted({
            match.group(1)
            for match in token_pattern.finditer(rendered)
            if match.group(1).startswith('TPL_')
        })
        if unresolved:
            unresolved_str = ', '.join(unresolved)
            raise RuntimeError(
                f"Placeholder non risolti nel template {relative_path}: {unresolved_str}"
            )

        return rendered
    
    def load_farm_config(self):
        """Carica la configurazione farm esistente"""
        config_file = self.temp_dir / "farm_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                messagebox.showwarning(
                    "Attenzione",
                    f"Impossibile caricare la configurazione farm: {e}\n\n"
                    "Configura prima il Farm dalla finestra 'Configurazione Farm'."
                )
                return {}
        else:
            messagebox.showwarning(
                "Configurazione Mancante",
                "Nessuna configurazione Farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return {}
    
    def setup_ui(self):
        """Configura l'interfaccia della finestra"""
        # Frame principale
        main_frame = ttk.Frame(self.window, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configura il grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # === TITOLO ===
        title_label = ttk.Label(
            main_frame,
            text="🚀 Operazioni sul Farm",
            font=('Arial', 13, 'bold')
        )
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # === CREDENZIALI ===
        cred_frame = ttk.LabelFrame(main_frame, text="🔐 Credenziali SSH", padding="10")
        cred_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        cred_frame.columnconfigure(1, weight=1)
        
        # Password Jump Server
        ttk.Label(cred_frame, text="Password Jump Server:").grid(
            row=0, column=0, sticky=tk.W, pady=3, padx=(0, 5)
        )
        ttk.Entry(cred_frame, textvariable=self.jump_password, show="*", width=30).grid(
            row=0, column=1, sticky=(tk.W, tk.E), pady=3
        )
        
        # Checkbox per usare le stesse credenziali
        ttk.Checkbutton(
            cred_frame,
            text="Usa stesse credenziali per target server",
            variable=self.same_credentials,
            command=self.toggle_target_password
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(8, 3))
        
        # Password Target Server
        self.target_password_label = ttk.Label(cred_frame, text="Password Target Server:")
        self.target_password_label.grid(
            row=2, column=0, sticky=tk.W, pady=3, padx=(0, 5)
        )
        self.target_password_entry = ttk.Entry(cred_frame, textvariable=self.target_password, show="*", width=30)
        self.target_password_entry.grid(
            row=2, column=1, sticky=(tk.W, tk.E), pady=3
        )
        
        # Inizialmente nascondi il campo password target se stesse credenziali
        self.toggle_target_password()
        
        # === STATO CONNESSIONE ===
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        status_frame.columnconfigure(1, weight=1)
        
        
        # === PULSANTI OPERAZIONI ===
        operations_frame = ttk.LabelFrame(main_frame, text="📋 Operazioni Disponibili", padding="15")
        operations_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        operations_frame.columnconfigure(0, weight=1)
        operations_frame.columnconfigure(1, weight=1)
        operations_frame.columnconfigure(2, weight=1)
        
        button_width = 25
        button_padx = 5
        button_pady = 5
        
        # RIGA 0
        ttk.Button(
            operations_frame,
            text="🐍 Create Virtual Environment",
            command=self.create_virtual_environment,
            width=button_width
        ).grid(row=0, column=0, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        ttk.Button(
            operations_frame,
            text="🗺️ Prepare Geographic",
            command=self.prepare_geographic,
            width=button_width
        ).grid(row=0, column=1, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        ttk.Button(
            operations_frame,
            text="🚀 Launch Geographic",
            command=self.launch_geographic,
            width=button_width
        ).grid(row=0, column=2, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        # RIGA 1
        ttk.Button(
            operations_frame,
            text="🌤️ Prepare CALMET",
            command=self.prepare_calmet,
            width=button_width
        ).grid(row=1, column=0, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        ttk.Button(
            operations_frame,
            text="📄 Load inp CALMET",
            command=self.load_inp_calmet,
            width=button_width
        ).grid(row=1, column=1, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        ttk.Button(
            operations_frame,
            text="🚀 Launch CALMET",
            command=self.launch_calmet,
            width=button_width
        ).grid(row=1, column=2, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        # RIGA 2
        ttk.Button(
            operations_frame,
            text="💨 Prepare CALPUFF",
            command=self.prepare_calpuff,
            width=button_width
        ).grid(row=2, column=0, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        ttk.Button(
            operations_frame,
            text="📄 Load inp CALPUFF",
            command=self.load_inp_calpuff,
            width=button_width
        ).grid(row=2, column=1, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        ttk.Button(
            operations_frame,
            text="🚀 Launch CALPUFF",
            command=self.launch_calpuff,
            width=button_width
        ).grid(row=2, column=2, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        # RIGA 3
        ttk.Button(
            operations_frame,
            text="📊 Prepare CALPOST",
            command=self.prepare_calpost,
            width=button_width
        ).grid(row=3, column=0, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        ttk.Button(
            operations_frame,
            text="📄 Load inp CALPOST",
            command=self.load_inp_calpost,
            width=button_width
        ).grid(row=3, column=1, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        ttk.Button(
            operations_frame,
            text="🚀 Launch CALPOST",
            command=self.launch_calpost,
            width=button_width
        ).grid(row=3, column=2, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        # RIGA 4
        ttk.Button(
            operations_frame,
            text="📈 Launch Aggreg",
            command=self.launch_aggreg,
            width=button_width
        ).grid(row=4, column=0, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        ttk.Button(
            operations_frame,
            text="📊 Launch Mean",
            command=self.launch_mean,
            width=button_width
        ).grid(row=4, column=1, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        ttk.Button(
            operations_frame,
            text="📉 Launch Percentile",
            command=self.launch_percentile,
            width=button_width
        ).grid(row=4, column=2, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        # RIGA 5
        ttk.Button(
            operations_frame,
            text="☁️ Prepare Meteo",
            command=self.prepare_meteo,
            width=button_width
        ).grid(row=5, column=0, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        ttk.Button(
            operations_frame,
            text="🌩️ Launch Meteo",
            command=self.launch_meteo,
            width=button_width
        ).grid(row=5, column=1, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        ttk.Button(
            operations_frame,
            text="📍 Launch Puntuale",
            command=self.launch_puntuale,
            width=button_width
        ).grid(row=5, column=2, padx=button_padx, pady=button_pady, sticky=(tk.W, tk.E))
        
        # === AREA OUTPUT/LOG ===
        log_frame = ttk.LabelFrame(main_frame, text="📄 Output Operation Log", padding="10")
        log_frame.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            width=70,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # === PULSANTI AZIONE ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, sticky=(tk.W, tk.E))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # Pulsante Test Connessione
        test_conn_btn = ttk.Button(
            button_frame,
            text="🔌 Test Connessione",
            command=self.test_connection
        )
        test_conn_btn.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))
        
        # Pulsante Clear Log
        clear_log_btn = ttk.Button(
            button_frame,
            text="🗑️ Pulisci Log",
            command=self.clear_log
        )
        clear_log_btn.grid(row=0, column=1, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Log iniziale
        self.log_message("Finestra operazioni farm inizializzata.")
        if self.farm_config:
            self.log_message(f"Configurazione caricata: {self.farm_config.get('target_host', 'N/A')}")
        else:
            self.log_message("⚠ Nessuna configurazione farm trovata. Configura prima il Farm.")
    
    def log_message(self, message):
        """Aggiunge un messaggio al log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Pulisce il log"""
        self.log_text.delete(1.0, tk.END)
    
    def toggle_target_password(self):
        """Mostra/nascondi il campo password target server"""
        if self.same_credentials.get():
            self.target_password_label.grid_remove()
            self.target_password_entry.grid_remove()
        else:
            self.target_password_label.grid()
            self.target_password_entry.grid()
    
    def test_connection(self):
        """Testa la connessione al farm"""
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non è installato.\n\n"
                "Installa con: pip install paramiko"
            )
            return
        
        if not self.farm_config:
            messagebox.showerror(
                "Errore",
                "Nessuna configurazione farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return
        
        # Verifica che le password siano state inserite
        if not self.jump_password.get():
            messagebox.showerror(
                "Errore",
                "Inserisci la password per il Jump Server!"
            )
            return
        
        if not self.same_credentials.get() and not self.target_password.get():
            messagebox.showerror(
                "Errore",
                "Inserisci la password per il Target Server!"
            )
            return
        
        self.log_message("\n" + "="*50)
        self.log_message("Test connessione in corso...")
        
        # Esegui test in un thread separato per non bloccare l'UI
        thread = threading.Thread(target=self._test_connection_thread)
        thread.daemon = True
        thread.start()
    
    def _test_connection_thread(self):
        """Thread per testare la connessione"""
        try:
            # Connessione al Jump Server
            jump_host = self.farm_config.get('ssh_host', '')
            jump_port = int(self.farm_config.get('ssh_port', 22))
            jump_username = self.farm_config.get('ssh_username', '')
            jump_password = self.jump_password.get()
            
            self.log_message(f"Connessione al Jump Server: {jump_username}@{jump_host}:{jump_port}")
            
            jump_client = paramiko.SSHClient()
            jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_client.connect(
                hostname=jump_host,
                port=jump_port,
                username=jump_username,
                password=jump_password
            )
            
            self.log_message("✓ Jump Server connesso con successo!")
            
            # Connessione al Target Server
            target_host = self.farm_config.get('target_host', '')
            target_username = self.farm_config.get('target_username', jump_username)
            target_password = self.target_password.get() if not self.same_credentials.get() else jump_password
            
            self.log_message(f"Connessione al Target Server: {target_username}@{target_host}")
            
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
                sock=jump_channel
            )
            
            self.log_message("✓ Target Server connesso con successo!")
            
            # Test comando
            stdin, stdout, stderr = target_client.exec_command('pwd')
            output = stdout.read().decode().strip()
            self.log_message(f"Directory corrente: {output}")
            
            self.connection_status.set("✓ Connesso")
            self.log_message("\n✓ TEST CONNESSIONE RIUSCITO!")
            
            target_client.close()
            jump_client.close()
            
        except Exception as e:
            self.log_message(f"\n✗ ERRORE CONNESSIONE: {str(e)}")
            self.connection_status.set("✗ Errore connessione")
            messagebox.showerror("Errore Connessione", f"Impossibile connettersi al farm:\n\n{str(e)}")
    
    def execute_remote_command(self, command, operation_name):
        """Esegue un comando remoto sul farm"""
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non è installato.\n\n"
                "Installa con: pip install paramiko"
            )
            return
        
        if not self.farm_config:
            messagebox.showerror(
                "Errore",
                "Nessuna configurazione farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return
        
        # Verifica che le password siano state inserite
        if not self.jump_password.get():
            messagebox.showerror(
                "Errore",
                "Inserisci la password per il Jump Server!"
            )
            return
        
        if not self.same_credentials.get() and not self.target_password.get():
            messagebox.showerror(
                "Errore",
                "Inserisci la password per il Target Server!"
            )
            return
        
        self.log_message("\n" + "="*50)
        self.log_message(f"Operazione: {operation_name}")
        self.log_message(f"Comando: {command}")
        
        # Esegui in un thread separato
        thread = threading.Thread(
            target=self._execute_command_thread,
            args=(command, operation_name)
        )
        thread.daemon = True
        thread.start()
    
    def _execute_command_thread(self, command, operation_name):
        """Thread per eseguire comando remoto"""
        try:
            # Connessione al Jump Server
            jump_host = self.farm_config.get('ssh_host', '')
            jump_port = int(self.farm_config.get('ssh_port', 22))
            jump_username = self.farm_config.get('ssh_username', '')
            jump_password = self.jump_password.get()
            
            self.log_message(f"Connessione in corso...")
            
            jump_client = paramiko.SSHClient()
            jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_client.connect(
                hostname=jump_host,
                port=jump_port,
                username=jump_username,
                password=jump_password
            )
            
            # Connessione al Target Server
            target_host = self.farm_config.get('target_host', '')
            target_username = self.farm_config.get('target_username', jump_username)
            target_password = self.target_password.get() if not self.same_credentials.get() else jump_password
            working_folder = self.farm_config.get('working_folder', '/project/pmten/simulations/')
            
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
                sock=jump_channel
            )
            
            self.log_message("✓ Connesso al farm")
            
            # Esegui comando
            full_command = f"cd {working_folder} && {command}"
            self.log_message(f"Esecuzione comando in: {working_folder}")
            
            stdin, stdout, stderr = target_client.exec_command(full_command)
            
            # Leggi output
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if output:
                self.log_message(f"\nOutput:\n{output}")
            
            if error:
                self.log_message(f"\nErrori/Warning:\n{error}")
            
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.log_message(f"\n✓ {operation_name} completato con successo!")
                messagebox.showinfo("Successo", f"{operation_name} completato con successo!")
            else:
                self.log_message(f"\n✗ {operation_name} fallito con exit code {exit_status}")
                messagebox.showwarning("Attenzione", f"{operation_name} completato con errori (exit code {exit_status})")
            
            target_client.close()
            jump_client.close()
            
        except Exception as e:
            self.log_message(f"\n✗ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante l'esecuzione:\n\n{str(e)}")
    
    def create_virtual_environment(self):
        """Crea un ambiente virtuale Python sul farm, carica requirements.txt e installa le dipendenze"""
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non è installato.\n\n"
                "Installa con: pip install paramiko"
            )
            return
        
        if not self.farm_config:
            messagebox.showerror(
                "Errore",
                "Nessuna configurazione farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return
        
        # Verifica che le password siano state inserite
        if not self.jump_password.get():
            messagebox.showerror(
                "Errore",
                "Inserisci la password per il Jump Server!"
            )
            return
        
        if not self.same_credentials.get() and not self.target_password.get():
            messagebox.showerror(
                "Errore",
                "Inserisci la password per il Target Server!"
            )
            return
        
        # Verifica che requirements.txt esista
        requirements_file = Path("Working_Files/requirements.txt")
        if not requirements_file.exists():
            messagebox.showerror(
                "Errore",
                f"File requirements.txt non trovato in:\n{requirements_file.absolute()}"
            )
            return
        
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Create Virtual Environment")
        
        # Esegui in un thread separato
        thread = threading.Thread(target=self._create_venv_thread)
        thread.daemon = True
        thread.start()
    
    def _create_venv_thread(self):
        """Thread per creare virtual environment e installare dipendenze"""
        try:
            # Connessione al Jump Server
            jump_host = self.farm_config.get('ssh_host', '')
            jump_port = int(self.farm_config.get('ssh_port', 22))
            jump_username = self.farm_config.get('ssh_username', '')
            jump_password = self.jump_password.get()
            
            self.log_message(f"Connessione in corso...")
            
            jump_client = paramiko.SSHClient()
            jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_client.connect(
                hostname=jump_host,
                port=jump_port,
                username=jump_username,
                password=jump_password
            )
            
            # Connessione al Target Server
            target_host = self.farm_config.get('target_host', '')
            target_username = self.farm_config.get('target_username', jump_username)
            target_password = self.target_password.get() if not self.same_credentials.get() else jump_password
            working_folder = self.farm_config.get('working_folder', '/project/pmten/simulations/')
            
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
                sock=jump_channel
            )
            
            self.log_message("✓ Connesso al farm")
            
            # 1. Upload requirements.txt
            self.log_message("Caricamento requirements.txt...")
            sftp = target_client.open_sftp()
            
            local_file = Path("Working_Files/requirements.txt")
            remote_file = f"{working_folder}/requirements.txt"
            
            sftp.put(str(local_file), remote_file)
            sftp.close()
            self.log_message(f"✓ File caricato: {remote_file}")
            
            # 2. Crea virtual environment
            self.log_message("Creazione virtual environment...")
            stdin, stdout, stderr = target_client.exec_command(
                f"cd {working_folder} && python3 -m venv .venv"
            )
            stdout.channel.recv_exit_status()  # Attendi completamento
            error = stderr.read().decode()
            if error:
                self.log_message(f"Warning: {error}")
            self.log_message("✓ Virtual environment creato")
            
            # 3. Upgrade pip
            self.log_message("Aggiornamento pip...")
            stdin, stdout, stderr = target_client.exec_command(
                f"cd {working_folder} && source .venv/bin/activate && pip install --upgrade pip"
            )
            output = stdout.read().decode()
            stdout.channel.recv_exit_status()  # Attendi completamento
            self.log_message("✓ Pip aggiornato")
            
            # 4. Installa dipendenze
            self.log_message("Installazione dipendenze da requirements.txt...")
            stdin, stdout, stderr = target_client.exec_command(
                f"cd {working_folder} && source .venv/bin/activate && pip install -r requirements.txt"
            )
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if output:
                self.log_message(f"\nOutput pip install:\n{output}")
            if error:
                self.log_message(f"\nPip stderr:\n{error}")
            
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.log_message("\n✓ Virtual Environment creato e dipendenze installate con successo!")
                messagebox.showinfo("Successo", "Virtual Environment creato e dipendenze installate con successo!")
            else:
                self.log_message(f"\n✗ Installazione dipendenze fallita con exit code {exit_status}")
                messagebox.showwarning("Attenzione", f"Installazione completata con errori (exit code {exit_status})")
            
            target_client.close()
            jump_client.close()
            
        except Exception as e:
            self.log_message(f"\n✗ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante l'esecuzione:\n\n{str(e)}")
    
    def prepare_geographic(self):
        """Prepara i dati geografici copiando le cartelle necessarie"""
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non è installato.\n\n"
                "Installa con: pip install paramiko"
            )
            return
        
        if not self.farm_config:
            messagebox.showerror(
                "Errore",
                "Nessuna configurazione farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return
        
        # Verifica che le password siano state inserite
        if not self.jump_password.get():
            messagebox.showerror(
                "Errore",
                "Inserisci la password per il Jump Server!"
            )
            return
        
        if not self.same_credentials.get() and not self.target_password.get():
            messagebox.showerror(
                "Errore",
                "Inserisci la password per il Target Server!"
            )
            return
        
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Prepare Geographic")
        
        # Esegui in un thread separato
        thread = threading.Thread(target=self._prepare_geographic_thread)
        thread.daemon = True
        thread.start()
    
    def _prepare_geographic_thread(self):
        """Thread per preparare i dati geografici"""
        try:
            # Connessione al Jump Server
            jump_host = self.farm_config.get('ssh_host', '')
            jump_port = int(self.farm_config.get('ssh_port', 22))
            jump_username = self.farm_config.get('ssh_username', '')
            jump_password = self.jump_password.get()
            
            self.log_message(f"Connessione in corso...")
            
            jump_client = paramiko.SSHClient()
            jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_client.connect(
                hostname=jump_host,
                port=jump_port,
                username=jump_username,
                password=jump_password
            )
            
            # Connessione al Target Server
            target_host = self.farm_config.get('target_host', '')
            target_username = self.farm_config.get('target_username', jump_username)
            target_password = self.target_password.get() if not self.same_credentials.get() else jump_password
            working_folder = self.farm_config.get('working_folder', '/project/pmten/simulations/')
            
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
                sock=jump_channel
            )
            
            self.log_message("✓ Connesso al farm")
            
            # Cartelle da copiare
            base_procedure_path = "/project/pmten/Base_Procedure"
            folders_to_copy = [
                "TERREL",
                "CTGPROC",
                "MAKEGEO_V3.2_L110401"
            ]
            
            copied_folders = []
            skipped_folders = []
            errors = []
            
            for folder in folders_to_copy:
                source_path = f"{base_procedure_path}/{folder}"
                dest_path = f"{working_folder}/{folder}"
                
                self.log_message(f"\nVerifica cartella: {folder}")
                
                # Verifica se la cartella esiste già nella destinazione
                stdin, stdout, stderr = target_client.exec_command(f'test -d "{dest_path}" && echo "EXISTS" || echo "NOT_EXISTS"')
                exists = stdout.read().decode().strip() == "EXISTS"
                
                if exists:
                    self.log_message(f"  ⊙ Cartella già presente: {dest_path}")
                    skipped_folders.append(folder)
                else:
                    # Verifica che la cartella sorgente esista
                    stdin, stdout, stderr = target_client.exec_command(f'test -d "{source_path}" && echo "EXISTS" || echo "NOT_EXISTS"')
                    source_exists = stdout.read().decode().strip() == "EXISTS"
                    
                    if not source_exists:
                        self.log_message(f"  ✗ ERRORE: Cartella sorgente non trovata: {source_path}")
                        errors.append(f"{folder} (sorgente non trovata)")
                        continue
                    
                    # Copia la cartella
                    self.log_message(f"  → Copia in corso...")
                    stdin, stdout, stderr = target_client.exec_command(f'cp -r "{source_path}" "{dest_path}"')
                    exit_status = stdout.channel.recv_exit_status()
                    error = stderr.read().decode()
                    
                    if exit_status == 0:
                        self.log_message(f"  ✓ Cartella copiata: {dest_path}")
                        copied_folders.append(folder)
                    else:
                        self.log_message(f"  ✗ ERRORE durante la copia: {error}")
                        errors.append(f"{folder} (errore copia)")

            # Generazione file .inp locali per CTGPROC, MAKEGEO, TERREL
            self.log_message("\n" + "-"*50)
            self.log_message("Generazione file .inp geografici in Outputs:")
            try:
                workspace_root = self.temp_dir.parent
                output_dir = workspace_root / "Outputs"

                domain_config_path = self.temp_dir / "domain_config.json"
                landuse_config_path = self.temp_dir / "landuse_config.json"
                orography_config_path = self.temp_dir / "orography_config.json"

                required_configs = [domain_config_path, landuse_config_path, orography_config_path]
                missing_configs = [path.name for path in required_configs if not path.exists()]
                if missing_configs:
                    missing_text = ", ".join(missing_configs)
                    raise FileNotFoundError(f"Configurazioni mancanti: {missing_text}")

                terrel_inp = generate_terrel_inp(
                    domain_config_path=domain_config_path,
                    orography_config_path=orography_config_path,
                    output_dir=output_dir,
                )
                ctgproc_inp = generate_ctgproc_inp(
                    domain_config_path=domain_config_path,
                    landuse_config_path=landuse_config_path,
                    output_dir=output_dir,
                )
                makegeo_inp = generate_makegeo_inp(
                    domain_config_path=domain_config_path,
                    output_dir=output_dir,
                )

                self.log_message(f"  ✓ Creato: {terrel_inp}")
                self.log_message(f"  ✓ Creato: {ctgproc_inp}")
                self.log_message(f"  ✓ Creato: {makegeo_inp}")
            except Exception as inp_error:
                self.log_message(f"  ✗ ERRORE generazione INP: {inp_error}")
                errors.append(f"INP geografici ({inp_error})")
            
            # Upload dei file di output se presenti
            self.log_message("\n" + "-"*50)
            self.log_message("Upload file di output:")
            
            uploaded_files = []
            
            # File da caricare: (percorso_locale, percorso_remoto, descrizione)
            files_to_upload = [
                (Path("Outputs/oro.txt"), f"{working_folder}/TERREL/oro.txt", "orografia"),
                (Path("Outputs/landuse.xyz"), f"{working_folder}/CTGPROC/landuse.xyz", "landuse"),
                (Path("Outputs/terrel.inp"), f"{working_folder}/TERREL/terrel.inp", "terrel.inp"),
                (Path("Outputs/ctgproc.inp"), f"{working_folder}/CTGPROC/ctgproc.inp", "ctgproc.inp"),
                (Path("Outputs/makegeo.inp"), f"{working_folder}/MAKEGEO_V3.2_L110401/makegeo.inp", "makegeo.inp")
            ]
            
            sftp = target_client.open_sftp()
            
            for local_path, remote_path, description in files_to_upload:
                if local_path.exists():
                    try:
                        self.log_message(f"\n  → Upload {description}: {local_path.name}")
                        
                        # Verifica che la directory remota esista
                        remote_dir = remote_path.rsplit('/', 1)[0]
                        try:
                            sftp.stat(remote_dir)
                        except FileNotFoundError:
                            self.log_message(f"    ⚠ Directory remota non trovata: {remote_dir}")
                            errors.append(f"{local_path.name} (directory remota non trovata)")
                            continue
                        
                        # Upload file
                        sftp.put(str(local_path), remote_path)
                        self.log_message(f"    ✓ File caricato: {remote_path}")
                        uploaded_files.append(local_path.name)
                    except Exception as e:
                        self.log_message(f"    ✗ ERRORE upload {local_path.name}: {str(e)}")
                        errors.append(f"{local_path.name} (errore upload)")
                else:
                    self.log_message(f"  ⊙ File non presente: {local_path}")
            
            sftp.close()
            
            # Riepilogo
            self.log_message("\n" + "="*50)
            self.log_message("RIEPILOGO:")
            if copied_folders:
                self.log_message(f"  Cartelle copiate ({len(copied_folders)}): {', '.join(copied_folders)}")
            if skipped_folders:
                self.log_message(f"  Cartelle già presenti ({len(skipped_folders)}): {', '.join(skipped_folders)}")
            if uploaded_files:
                self.log_message(f"  File caricati ({len(uploaded_files)}): {', '.join(uploaded_files)}")
            if errors:
                self.log_message(f"  Errori ({len(errors)}): {', '.join(errors)}")
            
            target_client.close()
            jump_client.close()
            
            # Messaggio finale
            if errors:
                self.log_message("\n⚠ Prepare Geographic completato con errori")
                messagebox.showwarning("Attenzione", f"Operazione completata con {len(errors)} errori.\nControlla il log per dettagli.")
            elif copied_folders or uploaded_files:
                self.log_message("\n✓ Prepare Geographic completato con successo!")
                msg = f"Operazione completata!\n"
                if copied_folders:
                    msg += f"Cartelle copiate: {len(copied_folders)}\n"
                if skipped_folders:
                    msg += f"Cartelle già presenti: {len(skipped_folders)}\n"
                if uploaded_files:
                    msg += f"File caricati: {len(uploaded_files)}"
                messagebox.showinfo("Successo", msg)
            else:
                self.log_message("\n✓ Tutte le cartelle erano già presenti")
                messagebox.showinfo("Info", "Tutte le cartelle geografiche erano già presenti.")
            
        except Exception as e:
            self.log_message(f"\n✗ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante l'esecuzione:\n\n{str(e)}")
    
    def prepare_calmet(self):
        """Prepara CALMET copiando la cartella necessaria"""
        self._prepare_folder("CALMET", "Prepare CALMET")
    
    def prepare_calpuff(self):
        """Prepara CALPUFF copiando la cartella necessaria"""
        self._prepare_folder("CALPUFF", "Prepare CALPUFF")
    
    def prepare_calpost(self):
        """Prepara CALPOST copiando la cartella necessaria"""
        self._prepare_folder("CALPOST", "Prepare CALPOST")
    
    def _prepare_folder(self, folder_name, operation_name):
        """Metodo generico per preparare una cartella copiandola da Base_Procedure"""
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non è installato.\n\n"
                "Installa con: pip install paramiko"
            )
            return
        
        if not self.farm_config:
            messagebox.showerror(
                "Errore",
                "Nessuna configurazione farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return
        
        # Verifica che le password siano state inserite
        if not self.jump_password.get():
            messagebox.showerror(
                "Errore",
                "Inserisci la password per il Jump Server!"
            )
            return
        
        if not self.same_credentials.get() and not self.target_password.get():
            messagebox.showerror(
                "Errore",
                "Inserisci la password per il Target Server!"
            )
            return
        
        self.log_message("\n" + "="*50)
        self.log_message(f"Operazione: {operation_name}")
        
        # Esegui in un thread separato
        thread = threading.Thread(
            target=self._prepare_folder_thread,
            args=(folder_name, operation_name)
        )
        thread.daemon = True
        thread.start()
    
    def _prepare_folder_thread(self, folder_name, operation_name):
        """Thread per preparare una cartella"""
        try:
            # Connessione al Jump Server
            jump_host = self.farm_config.get('ssh_host', '')
            jump_port = int(self.farm_config.get('ssh_port', 22))
            jump_username = self.farm_config.get('ssh_username', '')
            jump_password = self.jump_password.get()
            
            self.log_message(f"Connessione in corso...")
            
            jump_client = paramiko.SSHClient()
            jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_client.connect(
                hostname=jump_host,
                port=jump_port,
                username=jump_username,
                password=jump_password
            )
            
            # Connessione al Target Server
            target_host = self.farm_config.get('target_host', '')
            target_username = self.farm_config.get('target_username', jump_username)
            target_password = self.target_password.get() if not self.same_credentials.get() else jump_password
            working_folder = self.farm_config.get('working_folder', '/project/pmten/simulations/')
            
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
                sock=jump_channel
            )
            
            self.log_message("✓ Connesso al farm")
            
            # Percorsi
            base_procedure_path = "/project/pmten/Base_Procedure"
            source_path = f"{base_procedure_path}/{folder_name}"
            dest_path = f"{working_folder}/{folder_name}"
            
            self.log_message(f"\nVerifica cartella: {folder_name}")
            
            # Verifica se la cartella esiste già nella destinazione
            stdin, stdout, stderr = target_client.exec_command(f'test -d "{dest_path}" && echo "EXISTS" || echo "NOT_EXISTS"')
            exists = stdout.read().decode().strip() == "EXISTS"
            
            if exists:
                self.log_message(f"  ⊙ Cartella già presente: {dest_path}")
                self.log_message(f"\n✓ {operation_name}: Cartella già presente, nessuna azione necessaria")
                messagebox.showinfo("Info", f"La cartella {folder_name} è già presente nel working folder.")
            else:
                # Verifica che la cartella sorgente esista
                stdin, stdout, stderr = target_client.exec_command(f'test -d "{source_path}" && echo "EXISTS" || echo "NOT_EXISTS"')
                source_exists = stdout.read().decode().strip() == "EXISTS"
                
                if not source_exists:
                    self.log_message(f"  ✗ ERRORE: Cartella sorgente non trovata: {source_path}")
                    messagebox.showerror("Errore", f"Cartella sorgente non trovata:\n{source_path}")
                    target_client.close()
                    jump_client.close()
                    return
                
                # Copia la cartella
                self.log_message(f"  → Copia in corso da: {source_path}")
                self.log_message(f"                    a: {dest_path}")
                stdin, stdout, stderr = target_client.exec_command(f'cp -r "{source_path}" "{dest_path}"')
                exit_status = stdout.channel.recv_exit_status()
                error = stderr.read().decode()
                
                if exit_status == 0:
                    self.log_message(f"  ✓ Cartella copiata con successo!")
                    
                    # Se è CALMET, copia anche makegeo.dat da MAKEGEO_V3.2_L110401

                else:
                    self.log_message(f"  ✗ ERRORE durante la copia: {error}")
                    messagebox.showerror("Errore", f"Errore durante la copia:\n{error}")
                
                
                self.log_message(f"\n✓ {operation_name} completato con successo!")
                messagebox.showinfo("Successo", f"{operation_name} completato!\nCartella {folder_name} copiata con successo.")
            
            
            if folder_name == "CALMET":
                makegeo_src = f"{working_folder}/MAKEGEO_V3.2_L110401/makegeo.dat"
                makegeo_dst = f"{dest_path}/makegeo.dat"
                self.log_message(f"  → Copia makegeo.dat da MAKEGEO_V3.2_L110401...")
                stdin, stdout, stderr = target_client.exec_command(f'cp "{makegeo_src}" "{makegeo_dst}" 2>/dev/null && echo "OK" || echo "SKIP"')
                result = stdout.read().decode().strip()
                if result == "OK":
                    self.log_message(f"  ✓ makegeo.dat copiato in CALMET")
                else:
                    self.log_message(f"  ⊙ makegeo.dat non trovato (operazione facoltativa)")

            target_client.close()
            jump_client.close()
            
        except Exception as e:
            self.log_message(f"\n✗ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante l'esecuzione:\n\n{str(e)}")
    
    # === METODI PLACEHOLDER PER NUOVI BOTTONI ===
    
    def prepare_meteo(self):
        """Prepara i dati meteo - DA IMPLEMENTARE"""
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Prepare Meteo")
        self.log_message("⚠ Funzione da implementare")
        messagebox.showinfo("Info", "Funzione Prepare Meteo da implementare")
    
    def launch_geographic(self):
        """Lancia elaborazione dati geografici: TERREL → CTGPROC → MAKEGEO"""
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non è installato.\n\n"
                "Installa con: pip install paramiko"
            )
            return
        
        if not self.farm_config:
            messagebox.showerror(
                "Errore",
                "Nessuna configurazione farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return
        
        if not self.jump_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Jump Server!")
            return
        
        if not self.same_credentials.get() and not self.target_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Target Server!")
            return
        
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch Geographic")
        
        thread = threading.Thread(target=self._launch_geographic_thread)
        thread.daemon = True
        thread.start()
    
    def _launch_geographic_thread(self):
        """Thread per lanciare la sequenza geografica TERREL → CTGPROC → MAKEGEO"""
        jump_client = None
        target_client = None
        try:
            jump_host = self.farm_config.get('ssh_host', '')
            jump_port = int(self.farm_config.get('ssh_port', 22))
            jump_username = self.farm_config.get('ssh_username', '')
            jump_password = self.jump_password.get()
            
            self.log_message("Connessione in corso...")
            
            jump_client = paramiko.SSHClient()
            jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_client.connect(
                hostname=jump_host,
                port=jump_port,
                username=jump_username,
                password=jump_password
            )
            
            target_host = self.farm_config.get('target_host', '')
            target_username = self.farm_config.get('target_username', jump_username)
            target_password = self.target_password.get() if not self.same_credentials.get() else jump_password
            working_folder = self.farm_config.get('working_folder', '/project/pmten/simulations/')
            
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
                sock=jump_channel
            )
            
            self.log_message("✓ Connesso al farm")
            #remuve rendondant "/" a fine percorso
            worki_folder = working_folder.rstrip('/')
            # Definizione percorsi e comandi
            terrel_exe = f"{worki_folder}/TERREL/terrel_v7.0.0.exe"
            ctgproc_exe = f"{worki_folder}/CTGPROC/ctgproc_nostro.exe"
            makegeo_exe = f"{worki_folder}/MAKEGEO_V3.2_L110401/makegeo_v3.2.exe"

            bash_script = self._render_script_template(
                "run_geographic.sh.template",
                {
                    "TPL_WORKING_FOLDER": working_folder,
                    "TPL_WORKI_FOLDER": worki_folder,
                    "TPL_TERREL_EXE": terrel_exe,
                    "TPL_CTGPROC_EXE": ctgproc_exe,
                    "TPL_MAKEGEO_EXE": makegeo_exe,
                },
            )
            
            # Salva lo script sul server
            script_path = f"{working_folder}/run_geographic.sh"
            self.log_message("Creazione script di esecuzione...")
            
            sftp = target_client.open_sftp()
            with sftp.open(script_path, 'w') as script_file:
                script_file.write(bash_script)
            sftp.close()
            
            # Rendi eseguibile lo script
            stdin, stdout, stderr = target_client.exec_command(f'chmod +x {script_path}')
            stdout.channel.recv_exit_status()
            
            self.log_message("✓ Script creato")
            
            # Esegui con bsub
            self.log_message("\n" + "-"*50)
            self.log_message("Sottomissione job con bsub -q pmten...")
            target_client.exec_command(f'cd {working_folder} && rm -f geo_output.log geo_error.log')  # Pulisci log precedenti
            bsub_command = f'cd {working_folder}; bsub -q pmten -o geo_output.log -e geo_error.log ./run_geographic.sh'
            
            stdin, stdout, stderr = target_client.exec_command(bsub_command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            exit_status = stdout.channel.recv_exit_status()
            
            if output:
                self.log_message(f"Output bsub:\n{output}")
            if error:
                self.log_message(f"Stderr bsub:\n{error}")
            
            if exit_status == 0:
                self.log_message("\n✓ Job sottomesso con successo!")
                self.log_message("\nSequenza esecuzione:")
                self.log_message("  1. TERREL → terrel.dat")
                self.log_message("  2. CTGPROC → luse.dat")
                self.log_message("  3. MAKEGEO (terrel.dat + luse.dat) → makegeo.dat")
                self.log_message("\nLog disponibili:")
                self.log_message(f"  - Output: {working_folder}/geo_output.log")
                self.log_message(f"  - Errori: {working_folder}/geo_error.log")
                
                messagebox.showinfo(
                    "Successo",
                    "Job geografico sottomesso con successo!\n\n"
                    "Sequenza: TERREL → CTGPROC → MAKEGEO\n"
                    "Controlla i log per monitorare l'esecuzione."
                )
            else:
                self.log_message(f"\n✗ Errore sottomissione job (exit code {exit_status})")
                messagebox.showerror(
                    "Errore",
                    f"Errore durante la sottomissione del job.\nExit code: {exit_status}"
                )
            
            target_client.close()
            jump_client.close()
            
        except Exception as e:
            self.log_message(f"\n✗ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante Launch Geographic:\n\n{str(e)}")
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
    
    def launch_meteo(self):
        """Lancia elaborazione dati meteo - DA IMPLEMENTARE"""
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch Meteo")
        self.log_message("⚠ Funzione da implementare")
        messagebox.showinfo("Info", "Funzione Launch Meteo da implementare")
    
    def launch_puntuale(self):
        """Lancia elaborazione dati puntuali - DA IMPLEMENTARE"""
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch Puntuale")
        self.log_message("⚠ Funzione da implementare")
        messagebox.showinfo("Info", "Funzione Launch Puntuale da implementare")
    
    def load_inp_calmet(self):
        """Carica tutte le cartelle CALMET_INP* nel working folder del target server"""
        self._load_inp_by_pattern("Load inp CALMET", "CALMET_INP*")

    def _load_inp_by_pattern(self, operation_name, folder_pattern):
        """Carica tutte le cartelle locali che matchano il pattern nel working folder remoto"""
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non è installato.\n\n"
                "Installa con: pip install paramiko"
            )
            return

        if not self.farm_config:
            messagebox.showerror(
                "Errore",
                "Nessuna configurazione farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return

        if not self.jump_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Jump Server!")
            return

        if not self.same_credentials.get() and not self.target_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Target Server!")
            return

        local_base_dir = self.temp_dir.parent
        inp_folders = sorted([path for path in local_base_dir.glob(folder_pattern) if path.is_dir()])

        self.log_message("\n" + "="*50)
        self.log_message(f"Operazione: {operation_name}")

        if not inp_folders:
            self.log_message(f"✗ Nessuna cartella {folder_pattern} trovata in: {local_base_dir}")
            messagebox.showwarning(
                "Attenzione",
                f"Nessuna cartella {folder_pattern} trovata in:\n{local_base_dir}"
            )
            return

        self.log_message(f"Cartelle trovate ({len(inp_folders)}):")
        for folder in inp_folders:
            self.log_message(f"  - {folder.name}")

        thread = threading.Thread(
            target=self._load_inp_folders_thread,
            args=(inp_folders, operation_name)
        )
        thread.daemon = True
        thread.start()

    def _upload_folder_recursive(self, sftp, local_folder, remote_folder):
        """Upload ricorsivo di una cartella locale su percorso remoto"""
        try:
            sftp.stat(remote_folder)
        except FileNotFoundError:
            sftp.mkdir(remote_folder)

        for root, dirs, files in os.walk(local_folder):
            root_path = Path(root)
            relative_root = root_path.relative_to(local_folder)

            remote_root = remote_folder
            if str(relative_root) != '.':
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

    def _load_inp_folders_thread(self, inp_folders, operation_name):
        """Thread per upload cartelle INP al target server"""
        jump_client = None
        target_client = None
        sftp = None
        try:
            jump_host = self.farm_config.get('ssh_host', '')
            jump_port = int(self.farm_config.get('ssh_port', 22))
            jump_username = self.farm_config.get('ssh_username', '')
            jump_password = self.jump_password.get()

            self.log_message("Connessione in corso...")

            jump_client = paramiko.SSHClient()
            jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_client.connect(
                hostname=jump_host,
                port=jump_port,
                username=jump_username,
                password=jump_password
            )

            target_host = self.farm_config.get('target_host', '')
            target_username = self.farm_config.get('target_username', jump_username)
            target_password = self.target_password.get() if not self.same_credentials.get() else jump_password
            working_folder = self.farm_config.get('working_folder', '/project/pmten/simulations/')

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
                sock=jump_channel
            )

            self.log_message("✓ Connesso al farm")

            stdin, stdout, stderr = target_client.exec_command(f'mkdir -p "{working_folder}"')
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_text = stderr.read().decode().strip()
                raise RuntimeError(f"Impossibile creare/verificare working folder remoto: {error_text}")

            sftp = target_client.open_sftp()
            uploaded = []
            errors = []

            for local_folder in inp_folders:
                remote_folder = f"{working_folder.rstrip('/')}/{local_folder.name}"
                self.log_message(f"\nUpload cartella: {local_folder.name}")
                self.log_message(f"  Locale: {local_folder}")
                self.log_message(f"  Remoto: {remote_folder}")

                try:
                    self._upload_folder_recursive(sftp, local_folder, remote_folder)
                    uploaded.append(local_folder.name)
                    self.log_message("  ✓ Upload completato")
                except Exception as upload_error:
                    errors.append(f"{local_folder.name}: {upload_error}")
                    self.log_message(f"  ✗ Errore upload: {upload_error}")

            self.log_message("\n" + "="*50)
            self.log_message(f"RIEPILOGO {operation_name.upper()}:")
            self.log_message(f"  Cartelle richieste: {len(inp_folders)}")
            self.log_message(f"  Upload riusciti: {len(uploaded)}")
            if uploaded:
                self.log_message(f"  Elenco upload: {', '.join(uploaded)}")
            if errors:
                self.log_message(f"  Errori: {len(errors)}")
                for error in errors:
                    self.log_message(f"    - {error}")

            if errors:
                messagebox.showwarning(
                    "Attenzione",
                    f"{operation_name} completato con errori.\nUpload riusciti: {len(uploaded)}\nErrori: {len(errors)}"
                )
            else:
                messagebox.showinfo(
                    "Successo",
                    f"{operation_name} completato con successo!\nCartelle caricate: {len(uploaded)}"
                )

        except Exception as e:
            self.log_message(f"\n✗ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante {operation_name}:\n\n{str(e)}")
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
    
    def launch_calmet(self):
        """Lancia CALMET su tutti i file .inp in ordine data con job bsub sequenziale"""
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non è installato.\n\n"
                "Installa con: pip install paramiko"
            )
            return

        if not self.farm_config:
            messagebox.showerror(
                "Errore",
                "Nessuna configurazione farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return

        if not self.jump_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Jump Server!")
            return

        if not self.same_credentials.get() and not self.target_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Target Server!")
            return

        calmet_config_path = self.temp_dir / "calmet_config.json"
        if not calmet_config_path.exists():
            messagebox.showerror(
                "Errore",
                "Configurazione CALMET non trovata.\n\n"
                "Apri la finestra CALMET e salva la configurazione prima di lanciare."
            )
            return

        try:
            with open(calmet_config_path, 'r', encoding='utf-8') as config_file:
                calmet_config = json.load(config_file)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile leggere calmet_config.json:\n\n{e}")
            return

        wrf_path = str(calmet_config.get('wrf_path', '')).strip()
        calmet_data = str(calmet_config.get('calmet_data', 'CALMETDATA')).strip() or 'CALMETDATA'
        link_calmet = bool(calmet_config.get('link_calmet', calmet_config.get('link_CALMET', False)))

        if not wrf_path:
            messagebox.showerror(
                "Errore",
                "Il campo 'wrf_path' è vuoto nella configurazione CALMET.\n\n"
                "Configura il percorso WRF nella finestra CALMET."
            )
            return

        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch CALMET")
        self.log_message(f"wrf_path: {wrf_path}")
        self.log_message(f"cartella output CALMET: {calmet_data}")
        self.log_message(f"Modalità WRF: {'Link simbolici' if link_calmet else 'Copia file'}")

        thread = threading.Thread(
            target=self._launch_calmet_thread,
            args=(wrf_path, calmet_data, link_calmet)
        )
        thread.daemon = True
        thread.start()

    def _launch_calmet_thread(self, wrf_path, calmet_data, link_calmet=False):
        """Thread per preparare script remoto CALMET e sottometterlo via bsub"""
        jump_client = None
        target_client = None
        try:
            jump_host = self.farm_config.get('ssh_host', '')
            jump_port = int(self.farm_config.get('ssh_port', 22))
            jump_username = self.farm_config.get('ssh_username', '')
            jump_password = self.jump_password.get()

            self.log_message("Connessione in corso...")

            jump_client = paramiko.SSHClient()
            jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_client.connect(
                hostname=jump_host,
                port=jump_port,
                username=jump_username,
                password=jump_password
            )

            target_host = self.farm_config.get('target_host', '')
            target_username = self.farm_config.get('target_username', jump_username)
            target_password = self.target_password.get() if not self.same_credentials.get() else jump_password
            working_folder = self.farm_config.get('working_folder', '/project/pmten/simulations/')
            work_folder = working_folder.rstrip('/')

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
                sock=jump_channel
            )

            self.log_message("✓ Connesso al farm")

            inp_root_glob = f"{work_folder}/CALMET_INP*"
            calmet_dir = f"{work_folder}/CALMET"
            calmet_data_dir = f"{work_folder}/{calmet_data}"
            script_path = f"{work_folder}/run_calmet_batch.sh"

            self.log_message("Verifica cartelle remote CALMET/CALMET_INP*/WRF...")
            checks = [
                (f'test -d "{calmet_dir}"', f"Cartella CALMET non trovata: {calmet_dir}"),
                (f'ls -d {inp_root_glob} >/dev/null 2>&1', f"Nessuna cartella CALMET_INP* trovata in {work_folder}"),
                (f'test -d "{wrf_path}"', f"wrf_path non trovato sul server: {wrf_path}")
            ]
            for check_cmd, error_msg in checks:
                stdin, stdout, stderr = target_client.exec_command(f'{check_cmd} && echo "OK" || echo "FAIL"')
                if stdout.read().decode().strip() != "OK":
                    raise RuntimeError(error_msg)

            stdin, stdout, stderr = target_client.exec_command(
                f'mkdir -p "{calmet_data_dir}" && echo "OK" || echo "FAIL"'
            )
            if stdout.read().decode().strip() != "OK":
                error_text = stderr.read().decode().strip()
                raise RuntimeError(f"Impossibile creare cartella output CALMET: {error_text}")

            bash_script = self._render_script_template(
                "run_calmet_batch.sh.template",
                {
                    "TPL_WORK_FOLDER": work_folder,
                    "TPL_CALMET_DIR": calmet_dir,
                    "TPL_WRF_PATH": wrf_path.rstrip('/'),
                    "TPL_CALMET_DATA_DIR": calmet_data_dir,
                    "TPL_CALMET_DATA": calmet_data,
                    "TPL_WRF_LINK_MODE": 'ln -sf' if link_calmet else 'cp',
                },
            )

            self.log_message("Creazione script remoto CALMET...")
            sftp = target_client.open_sftp()
            with sftp.open(script_path, 'w') as script_file:
                script_file.write(bash_script)
            sftp.close()

            stdin, stdout, stderr = target_client.exec_command(f'chmod +x "{script_path}"')
            stdout.channel.recv_exit_status()
            self.log_message(f"✓ Script creato: {script_path}")

            bsub_out = f"{calmet_data_dir}/calmet_batch_output.log"
            bsub_err = f"{calmet_data_dir}/calmet_batch_error.log"
            target_client.exec_command(f'rm -f "{bsub_out}" "{bsub_err}"')

            self.log_message("Sottomissione job CALMET con bsub -q pmten...")
            bsub_command = (
                f'cd "{work_folder}"; '
                f'bsub -q pmten -o "{bsub_out}" -e "{bsub_err}" "{script_path}"'
            )
            stdin, stdout, stderr = target_client.exec_command(bsub_command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            exit_status = stdout.channel.recv_exit_status()

            if output:
                self.log_message(f"Output bsub:\n{output}")
            if error:
                self.log_message(f"Stderr bsub:\n{error}")

            job_id = None
            match = re.search(r"<([0-9]+)>", output or "")
            if match:
                job_id = match.group(1)

            if exit_status == 0:
                self.log_message("\n✓ Job CALMET sottomesso con successo!")
                if job_id:
                    self.log_message(f"Job ID: {job_id}")
                self.log_message("Esecuzione sequenziale prevista per tutti i .inp in ordine data.")
                self.log_message(f"Log batch: {bsub_out}")
                self.log_message(f"Error batch: {bsub_err}")
                self.log_message(f"Output run-by-run in: {calmet_data_dir}")

                messagebox.showinfo(
                    "Successo",
                    "Job CALMET sottomesso con successo!\n\n"
                    "Esecuzione sequenziale avviata per tutti i file .inp in CALMET_INP*.\n"
                    f"Output e log disponibili in: {calmet_data_dir}"
                )
            else:
                raise RuntimeError(f"Errore durante la sottomissione bsub (exit code {exit_status})")

        except Exception as e:
            self.log_message(f"\n✗ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante Launch CALMET:\n\n{str(e)}")
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
    
    def load_inp_calpuff(self):
        """Carica tutte le cartelle CALPUFF_INP* nel working folder del target server"""
        self._load_inp_by_pattern("Load inp CALPUFF", "CALPUFF_INP*")
    
    def launch_calpuff(self):
        """Lancia CALPUFF su tutti i file .inp in ordine data con job bsub sequenziale"""
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non è installato.\n\n"
                "Installa con: pip install paramiko"
            )
            return

        if not self.farm_config:
            messagebox.showerror(
                "Errore",
                "Nessuna configurazione farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return

        if not self.jump_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Jump Server!")
            return

        if not self.same_credentials.get() and not self.target_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Target Server!")
            return

        calmet_config_path = self.temp_dir / "calmet_config.json"
        if not calmet_config_path.exists():
            messagebox.showerror(
                "Errore",
                "Configurazione CALMET non trovata.\n\n"
                "Apri la finestra CALMET e salva la configurazione prima di lanciare CALPUFF."
            )
            return

        try:
            with open(calmet_config_path, 'r', encoding='utf-8') as config_file:
                calmet_config = json.load(config_file)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile leggere calmet_config.json:\n\n{e}")
            return

        calpuff_data = str(calmet_config.get('calpuff_data', 'CALPUFFDATA')).strip() or 'CALPUFFDATA'
        calmet_data = str(calmet_config.get('calmet_data', 'CALMETDATA')).strip() or 'CALMETDATA'
        link_calmet = bool(calmet_config.get('link_calmet', calmet_config.get('link_CALMET', False)))
        
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch CALPUFF")
        self.log_message(f"cartella output CALPUFF: {calpuff_data}")
        self.log_message(f"Sorgente CALMET: {calmet_data}")
        self.log_message(f"Modalità file meteo CALMET→CALPUFF: {'Link simbolici' if link_calmet else 'Copia file'}")

        thread = threading.Thread(
            target=self._launch_calpuff_thread,
            args=(calpuff_data, calmet_data, link_calmet)
        )
        thread.daemon = True
        thread.start()

    def _launch_calpuff_thread(self, calpuff_data, calmet_data='CALMETDATA', link_calmet=False):
        """Thread per preparare script remoto CALPUFF e sottometterlo via bsub"""
        jump_client = None
        target_client = None
        try:
            jump_host = self.farm_config.get('ssh_host', '')
            jump_port = int(self.farm_config.get('ssh_port', 22))
            jump_username = self.farm_config.get('ssh_username', '')
            jump_password = self.jump_password.get()

            self.log_message("Connessione in corso...")

            jump_client = paramiko.SSHClient()
            jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_client.connect(
                hostname=jump_host,
                port=jump_port,
                username=jump_username,
                password=jump_password
            )

            target_host = self.farm_config.get('target_host', '')
            target_username = self.farm_config.get('target_username', jump_username)
            target_password = self.target_password.get() if not self.same_credentials.get() else jump_password
            working_folder = self.farm_config.get('working_folder', '/project/pmten/simulations/')
            work_folder = working_folder.rstrip('/')

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
                sock=jump_channel
            )

            self.log_message("✓ Connesso al farm")

            inp_root_glob = f"{work_folder}/CALPUFF_INP*"
            calpuff_dir = f"{work_folder}/CALPUFF"
            calpuff_data_dir = f"{work_folder}/{calpuff_data}"
            calmet_data_dir = f"{work_folder}/{calmet_data}"
            script_path = f"{work_folder}/run_calpuff_batch.sh"

            self.log_message("Verifica cartelle remote CALPUFF/CALPUFF_INP*...")
            checks = [
                (f'test -d "{calpuff_dir}"', f"Cartella CALPUFF non trovata: {calpuff_dir}"),
                (f'ls -d {inp_root_glob} >/dev/null 2>&1', f"Nessuna cartella CALPUFF_INP* trovata in {work_folder}"),
            ]
            for check_cmd, error_msg in checks:
                stdin, stdout, stderr = target_client.exec_command(f'{check_cmd} && echo "OK" || echo "FAIL"')
                if stdout.read().decode().strip() != "OK":
                    raise RuntimeError(error_msg)

            stdin, stdout, stderr = target_client.exec_command(
                f'mkdir -p "{calpuff_data_dir}" && echo "OK" || echo "FAIL"'
            )
            if stdout.read().decode().strip() != "OK":
                error_text = stderr.read().decode().strip()
                raise RuntimeError(f"Impossibile creare cartella output CALPUFF: {error_text}")

            bash_script = self._render_script_template(
                "run_calpuff_batch.sh.template",
                {
                    "TPL_WORK_FOLDER": work_folder,
                    "TPL_CALPUFF_DIR": calpuff_dir,
                    "TPL_CALPUFF_DATA_DIR": calpuff_data_dir,
                    "TPL_CALMET_DATA_DIR": calmet_data_dir,
                    "TPL_CALMET_LINK_MODE": 'ln -sf' if link_calmet else 'cp -f',
                },
            )

            self.log_message("Creazione script remoto CALPUFF...")
            sftp = target_client.open_sftp()
            with sftp.open(script_path, 'w') as script_file:
                script_file.write(bash_script)
            sftp.close()

            stdin, stdout, stderr = target_client.exec_command(f'chmod +x "{script_path}"')
            stdout.channel.recv_exit_status()
            self.log_message(f"✓ Script creato: {script_path}")

            bsub_out = f"{calpuff_data_dir}/calpuff_batch_output.log"
            bsub_err = f"{calpuff_data_dir}/calpuff_batch_error.log"
            target_client.exec_command(f'rm -f "{bsub_out}" "{bsub_err}"')

            self.log_message("Sottomissione job CALPUFF con bsub -q pmten...")
            bsub_command = (
                f'cd "{work_folder}"; '
                f'bsub -q pmten -o "{bsub_out}" -e "{bsub_err}" "{script_path}"'
            )
            stdin, stdout, stderr = target_client.exec_command(bsub_command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            exit_status = stdout.channel.recv_exit_status()

            if output:
                self.log_message(f"Output bsub:\n{output}")
            if error:
                self.log_message(f"Stderr bsub:\n{error}")

            job_id = None
            match = re.search(r"<([0-9]+)>", output or "")
            if match:
                job_id = match.group(1)

            if exit_status == 0:
                self.log_message("\n✓ Job CALPUFF sottomesso con successo!")
                if job_id:
                    self.log_message(f"Job ID: {job_id}")
                self.log_message("Esecuzione sequenziale prevista per tutti i .inp in ordine data.")
                self.log_message(f"Log batch: {bsub_out}")
                self.log_message(f"Error batch: {bsub_err}")
                self.log_message(f"Output run-by-run in: {calpuff_data_dir}")

                messagebox.showinfo(
                    "Successo",
                    "Job CALPUFF sottomesso con successo!\n\n"
                    "Esecuzione sequenziale avviata per tutti i file .inp in CALPUFF_INP*.\n"
                    f"Output e log disponibili in: {calpuff_data_dir}"
                )
            else:
                raise RuntimeError(f"Errore durante la sottomissione bsub (exit code {exit_status})")

        except Exception as e:
            self.log_message(f"\n✗ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante Launch CALPUFF:\n\n{str(e)}")
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
    
    def load_inp_calpost(self):
        """Carica tutte le cartelle CALPOST_INP* nel working folder del target server"""
        self._load_inp_by_pattern("Load inp CALPOST", "CALPOST_INP*")
    
    def launch_calpost(self):
        """Lancia CALPOST su tutti i file .inp in ordine data/ora con job bsub sequenziale"""
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non è installato.\n\n"
                "Installa con: pip install paramiko"
            )
            return

        if not self.farm_config:
            messagebox.showerror(
                "Errore",
                "Nessuna configurazione farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return

        if not self.jump_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Jump Server!")
            return

        if not self.same_credentials.get() and not self.target_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Target Server!")
            return

        calmet_config_path = self.temp_dir / "calmet_config.json"
        if not calmet_config_path.exists():
            messagebox.showerror(
                "Errore",
                "Configurazione CALMET non trovata.\n\n"
                "Apri la finestra CALMET e salva la configurazione prima di lanciare CALPOST."
            )
            return

        try:
            with open(calmet_config_path, 'r', encoding='utf-8') as config_file:
                calmet_config = json.load(config_file)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile leggere calmet_config.json:\n\n{e}")
            return

        calpost_data = str(calmet_config.get('calpost_data', 'CALPOSTDATA')).strip() or 'CALPOSTDATA'
        calpuff_data = str(calmet_config.get('calpuff_data', 'CALPUFFDATA')).strip() or 'CALPUFFDATA'

        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch CALPOST")
        self.log_message(f"cartella output CALPOST: {calpost_data}")

        thread = threading.Thread(
            target=self._launch_calpost_thread,
            args=(calpost_data, calpuff_data)
        )
        thread.daemon = True
        thread.start()

    def _launch_calpost_thread(self, calpost_data, calpuff_data):
        """Thread per preparare script remoto CALPOST e sottometterlo via bsub"""
        jump_client = None
        target_client = None
        try:
            jump_host = self.farm_config.get('ssh_host', '')
            jump_port = int(self.farm_config.get('ssh_port', 22))
            jump_username = self.farm_config.get('ssh_username', '')
            jump_password = self.jump_password.get()

            self.log_message("Connessione in corso...")

            jump_client = paramiko.SSHClient()
            jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_client.connect(
                hostname=jump_host,
                port=jump_port,
                username=jump_username,
                password=jump_password
            )

            target_host = self.farm_config.get('target_host', '')
            target_username = self.farm_config.get('target_username', jump_username)
            target_password = self.target_password.get() if not self.same_credentials.get() else jump_password
            working_folder = self.farm_config.get('working_folder', '/project/pmten/simulations/')
            work_folder = working_folder.rstrip('/')

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
                sock=jump_channel
            )

            self.log_message("✓ Connesso al farm")

            inp_root_glob = f"{work_folder}/CALPOST_INP*"
            calpost_dir = f"{work_folder}/CALPOST"
            calpuff_dir = f"{work_folder}/CALPUFF"
            calpuff_data_dir = f"{work_folder}/{calpuff_data}"
            calpost_data_dir = f"{work_folder}/{calpost_data}"
            script_path = f"{work_folder}/run_calpost_batch.sh"

            self.log_message("Verifica cartelle remote CALPOST/CALPOST_INP*...")
            checks = [
                (f'test -d "{calpost_dir}"', f"Cartella CALPOST non trovata: {calpost_dir}"),
                (f'ls -d {inp_root_glob} >/dev/null 2>&1', f"Nessuna cartella CALPOST_INP* trovata in {work_folder}"),
            ]
            for check_cmd, error_msg in checks:
                stdin, stdout, stderr = target_client.exec_command(f'{check_cmd} && echo "OK" || echo "FAIL"')
                if stdout.read().decode().strip() != "OK":
                    raise RuntimeError(error_msg)

            stdin, stdout, stderr = target_client.exec_command(
                f'mkdir -p "{calpost_data_dir}" && echo "OK" || echo "FAIL"'
            )
            if stdout.read().decode().strip() != "OK":
                error_text = stderr.read().decode().strip()
                raise RuntimeError(f"Impossibile creare cartella output CALPOST: {error_text}")

            bash_script = self._render_script_template(
                "run_calpost_batch.sh.template",
                {
                    "TPL_WORK_FOLDER": work_folder,
                    "TPL_CALPOST_DIR": calpost_dir,
                    "TPL_CALPUFF_DIR": calpuff_dir,
                    "TPL_CALPUFF_DATA_DIR": calpuff_data_dir,
                    "TPL_CALPOST_DATA_DIR": calpost_data_dir,
                },
            )

            self.log_message("Creazione script remoto CALPOST...")
            sftp = target_client.open_sftp()
            with sftp.open(script_path, 'w') as script_file:
                script_file.write(bash_script)
            sftp.close()

            stdin, stdout, stderr = target_client.exec_command(f'chmod +x "{script_path}"')
            stdout.channel.recv_exit_status()
            self.log_message(f"✓ Script creato: {script_path}")

            bsub_out = f"{calpost_data_dir}/calpost_batch_output.log"
            bsub_err = f"{calpost_data_dir}/calpost_batch_error.log"
            target_client.exec_command(f'rm -f "{bsub_out}" "{bsub_err}"')

            self.log_message("Sottomissione job CALPOST con bsub -q pmten...")
            bsub_command = (
                f'cd "{work_folder}"; '
                f'bsub -q pmten -o "{bsub_out}" -e "{bsub_err}" "{script_path}"'
            )
            stdin, stdout, stderr = target_client.exec_command(bsub_command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            exit_status = stdout.channel.recv_exit_status()

            if output:
                self.log_message(f"Output bsub:\n{output}")
            if error:
                self.log_message(f"Stderr bsub:\n{error}")

            job_id = None
            match = re.search(r"<([0-9]+)>", output or "")
            if match:
                job_id = match.group(1)

            if exit_status == 0:
                self.log_message("\n✓ Job CALPOST sottomesso con successo!")
                if job_id:
                    self.log_message(f"Job ID: {job_id}")
                self.log_message("Esecuzione sequenziale prevista per tutti i .inp in ordine data/ora.")
                self.log_message(f"Log batch: {bsub_out}")
                self.log_message(f"Error batch: {bsub_err}")
                self.log_message(f"Output run-by-run in: {calpost_data_dir}")

                messagebox.showinfo(
                    "Successo",
                    "Job CALPOST sottomesso con successo!\n\n"
                    "Esecuzione sequenziale avviata per tutti i file .inp in CALPOST_INP*.\n"
                    f"Output e log disponibili in: {calpost_data_dir}"
                )
            else:
                raise RuntimeError(f"Errore durante la sottomissione bsub (exit code {exit_status})")

        except Exception as e:
            self.log_message(f"\n✗ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante Launch CALPOST:\n\n{str(e)}")
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
    
    def launch_aggreg(self):
        """Organizza i CSV di CALPOST in sottocartelle per parametro"""
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non è installato.\n\n"
                "Installa con: pip install paramiko"
            )
            return

        if not self.farm_config:
            messagebox.showerror(
                "Errore",
                "Nessuna configurazione farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return

        if not self.jump_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Jump Server!")
            return

        if not self.same_credentials.get() and not self.target_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Target Server!")
            return

        calmet_config_path = self.temp_dir / "calmet_config.json"
        if not calmet_config_path.exists():
            messagebox.showerror(
                "Errore",
                "Configurazione CALMET non trovata.\n\n"
                "Apri la finestra CALMET e salva la configurazione prima di lanciare l'aggregazione."
            )
            return

        try:
            with open(calmet_config_path, 'r', encoding='utf-8') as config_file:
                calmet_config = json.load(config_file)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile leggere calmet_config.json:\n\n{e}")
            return

        calpost_data = str(calmet_config.get('calpost_data', 'CALPOSTDATA')).strip() or 'CALPOSTDATA'

        # Load saved post-process config
        post_process_path = self.temp_dir / "post_process.json"
        saved_aggreg_folder = "AGGREG"
        saved_use_links = False
        saved_background = False
        if post_process_path.exists():
            try:
                with open(post_process_path, 'r', encoding='utf-8') as _f:
                    _pp = json.load(_f)
                saved_aggreg_folder = str(_pp.get('aggreg_folder', 'AGGREG')).strip() or 'AGGREG'
                saved_use_links = bool(_pp.get('use_links', False))
                saved_background = bool(_pp.get('aggreg_background', False))
            except Exception:
                pass

        # Build custom aggregation dialog
        dialog = tk.Toplevel(self.window)
        dialog.title("Modalità Aggregazione")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self.window)

        dialog_result = {}

        tk.Label(
            dialog, text="Modalità aggregazione:",
            font=('TkDefaultFont', 10, 'bold')
        ).grid(row=0, column=0, columnspan=2, sticky='w', padx=12, pady=(12, 2))

        mode_var = tk.StringVar(value="link" if saved_use_links else "copy")
        tk.Radiobutton(
            dialog, text="Copia i file nella nuova cartella",
            variable=mode_var, value="copy"
        ).grid(row=1, column=0, columnspan=2, sticky='w', padx=24)
        tk.Radiobutton(
            dialog, text="Crea link simbolici nella nuova cartella",
            variable=mode_var, value="link"
        ).grid(row=2, column=0, columnspan=2, sticky='w', padx=24)

        tk.Label(
            dialog, text="Cartella di destinazione:",
            font=('TkDefaultFont', 10, 'bold')
        ).grid(row=3, column=0, columnspan=2, sticky='w', padx=12, pady=(12, 2))
        folder_var = tk.StringVar(value=saved_aggreg_folder)
        tk.Entry(dialog, textvariable=folder_var, width=30).grid(
            row=4, column=0, columnspan=2, sticky='w', padx=24, pady=(0, 12)
        )

        background_var = tk.BooleanVar(value=saved_background)
        tk.Checkbutton(
            dialog,
            text="Esegui in background con bsub -q pmten (job non monitorato)",
            variable=background_var
        ).grid(row=5, column=0, columnspan=2, sticky='w', padx=24, pady=(0, 12))

        def _on_ok():
            folder = folder_var.get().strip()
            if not folder:
                messagebox.showerror("Errore", "Il nome della cartella non può essere vuoto.", parent=dialog)
                return
            dialog_result['use_links'] = (mode_var.get() == "link")
            dialog_result['aggreg_folder'] = folder
            dialog_result['run_in_background'] = background_var.get()
            dialog.destroy()

        def _on_cancel():
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(0, 12))
        tk.Button(btn_frame, text="OK", width=10, command=_on_ok).pack(side='left', padx=6)
        tk.Button(btn_frame, text="Annulla", width=10, command=_on_cancel).pack(side='left', padx=6)

        self.window.wait_window(dialog)

        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch Aggreg")

        if not dialog_result:
            self.log_message("Operazione annullata dall'utente.")
            return

        use_links = dialog_result['use_links']
        aggreg_folder = dialog_result['aggreg_folder']
        run_in_background = bool(dialog_result.get('run_in_background', False))
        aggregation_mode = "link simbolici" if use_links else "copia file"

        # Persist to post_process.json
        try:
            previous = {}
            if post_process_path.exists():
                with open(post_process_path, 'r', encoding='utf-8') as _f:
                    previous = json.load(_f)
            previous['aggreg_folder'] = aggreg_folder
            previous['use_links'] = use_links
            previous['aggreg_background'] = run_in_background
            with open(post_process_path, 'w', encoding='utf-8') as _f:
                json.dump(previous, _f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        self.log_message(f"cartella sorgente CALPOST: {calpost_data}")
        self.log_message(f"Modalità aggregazione: {aggregation_mode}")
        self.log_message(f"Cartella destinazione: {aggreg_folder}/<PARAMETRO>")
        self.log_message(
            "Modalità esecuzione: background (bsub -q pmten, job non monitorato)"
            if run_in_background else
            "Modalità esecuzione: foreground (monitorata dalla UI)"
        )

        if run_in_background:
            messagebox.showwarning(
                "Attenzione",
                "L'aggregazione verrà sottomessa in background con bsub -q pmten.\n"
                "Il lavoro non sarà monitorato dalla UI."
            )

        thread = threading.Thread(
            target=self._launch_aggreg_thread,
            args=(calpost_data, use_links, aggreg_folder, run_in_background)
        )
        thread.daemon = True
        thread.start()

    def _launch_aggreg_thread(self, calpost_data, use_links=False, aggreg_folder='AGGREG', run_in_background=False):
        """Thread per aggregare i CSV CALPOST in sottocartelle per parametro"""
        jump_client = None
        target_client = None
        try:
            jump_host = self.farm_config.get('ssh_host', '')
            jump_port = int(self.farm_config.get('ssh_port', 22))
            jump_username = self.farm_config.get('ssh_username', '')
            jump_password = self.jump_password.get()

            self.log_message("Connessione in corso...")

            jump_client = paramiko.SSHClient()
            jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_client.connect(
                hostname=jump_host,
                port=jump_port,
                username=jump_username,
                password=jump_password
            )

            target_host = self.farm_config.get('target_host', '')
            target_username = self.farm_config.get('target_username', jump_username)
            target_password = self.target_password.get() if not self.same_credentials.get() else jump_password
            working_folder = self.farm_config.get('working_folder', '/project/pmten/simulations/')
            work_folder = working_folder.rstrip('/')

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
                sock=jump_channel
            )

            self.log_message("✓ Connesso al farm")

            calpost_data_dir = f"{work_folder}/{calpost_data}"
            aggregate_root_dir = f"{work_folder}/{aggreg_folder}"
            mode_value = "link" if use_links else "copy"
            source_dir_literal = json.dumps(calpost_data_dir)
            dest_root_literal = json.dumps(aggregate_root_dir)
            mode_literal = json.dumps(mode_value)

            self.log_message("Verifica cartella output CALPOST...")
            stdin, stdout, stderr = target_client.exec_command(
                f'test -d "{calpost_data_dir}" && echo "OK" || echo "FAIL"'
            )
            if stdout.read().decode().strip() != "OK":
                raise RuntimeError(f"Cartella output CALPOST non trovata: {calpost_data_dir}")

            self.log_message("Ricerca parametri nei file CSV CALPOST...")
            remote_script = self._render_script_template(
                "python/aggregate_csv.py.template",
                {
                    "TPL_SOURCE_DIR_LITERAL": source_dir_literal,
                    "TPL_DEST_ROOT_LITERAL": dest_root_literal,
                    "TPL_MODE_LITERAL": mode_literal,
                },
            )

            if run_in_background:
                target_client.exec_command(f'mkdir -p "{aggregate_root_dir}"')
                script_path = f"{work_folder}/run_aggreg_background.sh"
                bsub_out = f"{aggregate_root_dir}/aggreg_output.log"
                bsub_err = f"{aggregate_root_dir}/aggreg_error.log"
                wrapper_script = "#!/bin/bash\nset -e\npython3 - <<'PY'\n" + remote_script + "\nPY\n"

                self.log_message("Creazione script remoto aggregazione (background)...")
                sftp = target_client.open_sftp()
                with sftp.open(script_path, 'w') as script_file:
                    script_file.write(wrapper_script)
                sftp.close()

                target_client.exec_command(f'chmod +x "{script_path}"')
                target_client.exec_command(f'rm -f "{bsub_out}" "{bsub_err}"')

                bsub_command = (
                    f'cd "{work_folder}"; '
                    f'bsub -q pmten -o "{bsub_out}" -e "{bsub_err}" "{script_path}"'
                )
                stdin, stdout, stderr = target_client.exec_command(bsub_command)
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                exit_status = stdout.channel.recv_exit_status()

                if output:
                    self.log_message(f"Output bsub aggregazione:\n{output}")
                if error:
                    self.log_message(f"Stderr bsub aggregazione:\n{error}")

                if exit_status != 0:
                    raise RuntimeError(error or f"Sottomissione aggregazione fallita con exit code {exit_status}")

                self.log_message("\n✓ Job aggregazione sottomesso in background!")
                self.log_message(f"Log output: {bsub_out}")
                self.log_message(f"Log errori: {bsub_err}")
                messagebox.showwarning(
                    "Job Aggregazione Sottomesso",
                    "Job aggregazione sottomesso con bsub -q pmten.\n\n"
                    "Il lavoro non è monitorato dalla UI.\n"
                    f"Controlla i log:\n{bsub_out}\n{bsub_err}"
                )
                return

            remote_command = "python3 - <<'PY'\n" + remote_script + "\nPY"

            stdin, stdout, stderr = target_client.exec_command(remote_command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            exit_status = stdout.channel.recv_exit_status()

            if output:
                self.log_message(f"Output aggregazione:\n{output}")
            if error:
                self.log_message(f"Stderr aggregazione:\n{error}")

            if exit_status != 0:
                raise RuntimeError(error or f"Aggregazione fallita con exit code {exit_status}")

            output_lines = [line.strip() for line in output.splitlines() if line.strip()]
            if not output_lines:
                raise RuntimeError("Nessun riepilogo restituito dal processo di aggregazione")

            try:
                summary = json.loads(output_lines[-1])
            except json.JSONDecodeError as decode_error:
                raise RuntimeError(f"Riepilogo aggregazione non valido: {decode_error}") from decode_error

            parameter_counts = summary.get('counts', {})
            skipped_files = summary.get('skipped', [])
            destination_root = summary.get('dest_root', aggregate_root_dir)

            self.log_message("\n✓ Aggregazione completata con successo!")
            self.log_message(f"Modalità: {'link simbolici' if use_links else 'copia file'}")
            self.log_message(f"Cartella aggregata: {destination_root}")
            self.log_message(f"CSV trovati: {summary.get('total_csv', 0)}")
            self.log_message(f"CSV aggregati: {summary.get('matched_csv', 0)}")

            for parameter_name in sorted(parameter_counts):
                self.log_message(f"  - {parameter_name}: {parameter_counts[parameter_name]} file")

            if skipped_files:
                self.log_message(f"File saltati ({len(skipped_files)}): {', '.join(skipped_files)}")

            messagebox.showinfo(
                "Successo",
                "Aggregazione completata con successo!\n\n"
                f"Modalità: {'link simbolici' if use_links else 'copia file'}\n"
                f"Parametri trovati: {len(parameter_counts)}\n"
                f"Cartella creata: {destination_root}"
            )

        except Exception as e:
            self.log_message(f"\n✗ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante Launch Aggreg:\n\n{str(e)}")
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
    
    def launch_mean(self):
        """Calcola medie giornaliere/mensili/annuali dai CSV aggregati"""
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non è installato.\n\n"
                "Installa con: pip install paramiko"
            )
            return

        if not self.farm_config:
            messagebox.showerror(
                "Errore",
                "Nessuna configurazione farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return

        if not self.jump_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Jump Server!")
            return

        if not self.same_credentials.get() and not self.target_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Target Server!")
            return

        post_process_path = self.temp_dir / "post_process.json"
        saved_source_folder = "AGGREG"
        saved_output_folder = "MEAN"
        saved_granularity = ["daily"]
        saved_background = False
        if post_process_path.exists():
            try:
                with open(post_process_path, 'r', encoding='utf-8') as _f:
                    _pp = json.load(_f)
                saved_source_folder = str(_pp.get('mean_source_folder', _pp.get('aggreg_folder', 'AGGREG'))).strip() or 'AGGREG'
                saved_output_folder = str(_pp.get('mean_output_folder', 'MEAN')).strip() or 'MEAN'
                saved_background = bool(_pp.get('mean_background', False))
                configured = _pp.get('mean_granularity', ['daily'])
                if isinstance(configured, list):
                    saved_granularity = [str(item).lower() for item in configured if str(item).strip()]
                elif isinstance(configured, str) and configured.strip():
                    saved_granularity = [configured.strip().lower()]
            except Exception:
                pass

        dialog = tk.Toplevel(self.window)
        dialog.title("Calcolo Medie")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self.window)

        dialog_result = {}

        tk.Label(
            dialog,
            text="Cartella sorgente (aggregata):",
            font=('TkDefaultFont', 10, 'bold')
        ).grid(row=0, column=0, columnspan=2, sticky='w', padx=12, pady=(12, 2))

        source_var = tk.StringVar(value=saved_source_folder)
        tk.Entry(dialog, textvariable=source_var, width=32).grid(
            row=1, column=0, columnspan=2, sticky='w', padx=24, pady=(0, 8)
        )

        tk.Label(
            dialog,
            text="Cartella destinazione medie:",
            font=('TkDefaultFont', 10, 'bold')
        ).grid(row=2, column=0, columnspan=2, sticky='w', padx=12, pady=(2, 2))

        destination_var = tk.StringVar(value=saved_output_folder)
        tk.Entry(dialog, textvariable=destination_var, width=32).grid(
            row=3, column=0, columnspan=2, sticky='w', padx=24, pady=(0, 8)
        )

        tk.Label(
            dialog,
            text="Granularità media (seleziona una o più):",
            font=('TkDefaultFont', 10, 'bold')
        ).grid(row=4, column=0, columnspan=2, sticky='w', padx=12, pady=(2, 2))

        daily_var = tk.BooleanVar(value='daily' in saved_granularity)
        monthly_var = tk.BooleanVar(value='monthly' in saved_granularity)
        annual_var = tk.BooleanVar(value='annual' in saved_granularity)

        tk.Checkbutton(dialog, text="Daily", variable=daily_var).grid(
            row=5, column=0, sticky='w', padx=24
        )
        tk.Checkbutton(dialog, text="Monthly", variable=monthly_var).grid(
            row=6, column=0, sticky='w', padx=24
        )
        tk.Checkbutton(dialog, text="Annual", variable=annual_var).grid(
            row=7, column=0, sticky='w', padx=24
        )

        background_var = tk.BooleanVar(value=saved_background)
        tk.Checkbutton(
            dialog,
            text="Esegui in background con bsub -q pmten (job non monitorato)",
            variable=background_var
        ).grid(row=8, column=0, columnspan=2, sticky='w', padx=24, pady=(8, 0))

        def _on_ok():
            source_folder = source_var.get().strip()
            destination_folder = destination_var.get().strip()
            granularities = []
            if daily_var.get():
                granularities.append('daily')
            if monthly_var.get():
                granularities.append('monthly')
            if annual_var.get():
                granularities.append('annual')

            if not source_folder:
                messagebox.showerror("Errore", "La cartella sorgente non può essere vuota.", parent=dialog)
                return
            if not destination_folder:
                messagebox.showerror("Errore", "La cartella destinazione non può essere vuota.", parent=dialog)
                return
            if not granularities:
                messagebox.showerror("Errore", "Seleziona almeno una granularità.", parent=dialog)
                return

            dialog_result['source_folder'] = source_folder
            dialog_result['destination_folder'] = destination_folder
            dialog_result['granularities'] = granularities
            dialog_result['run_in_background'] = background_var.get()
            dialog.destroy()

        def _on_cancel():
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=(8, 12))
        tk.Button(btn_frame, text="OK", width=10, command=_on_ok).pack(side='left', padx=6)
        tk.Button(btn_frame, text="Annulla", width=10, command=_on_cancel).pack(side='left', padx=6)

        self.window.wait_window(dialog)

        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch Mean")

        if not dialog_result:
            self.log_message("Operazione annullata dall'utente.")
            return

        source_folder = dialog_result['source_folder']
        destination_folder = dialog_result['destination_folder']
        granularities = dialog_result['granularities']
        run_in_background = bool(dialog_result.get('run_in_background', False))

        try:
            previous = {}
            if post_process_path.exists():
                with open(post_process_path, 'r', encoding='utf-8') as _f:
                    previous = json.load(_f)
            previous['mean_source_folder'] = source_folder
            previous['mean_output_folder'] = destination_folder
            previous['mean_granularity'] = granularities
            previous['mean_background'] = run_in_background
            with open(post_process_path, 'w', encoding='utf-8') as _f:
                json.dump(previous, _f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        self.log_message(f"Sorgente: {source_folder}")
        self.log_message(f"Destinazione: {destination_folder}")
        self.log_message(f"Granularità selezionate: {', '.join(granularities)}")
        self.log_message(
            "Modalità esecuzione: background (bsub -q pmten, job non monitorato)"
            if run_in_background else
            "Modalità esecuzione: foreground (monitorata dalla UI)"
        )

        if run_in_background:
            messagebox.showwarning(
                "Attenzione",
                "Il calcolo medie verrà sottomesso in background con bsub -q pmten.\n"
                "Il lavoro non sarà monitorato dalla UI."
            )

        thread = threading.Thread(
            target=self._launch_mean_thread,
            args=(source_folder, destination_folder, granularities, run_in_background)
        )
        thread.daemon = True
        thread.start()

    def _launch_mean_thread(self, source_folder, destination_folder, granularities, run_in_background=False):
        """Thread per calcolare medie dai CSV aggregati"""
        jump_client = None
        target_client = None
        try:
            jump_host = self.farm_config.get('ssh_host', '')
            jump_port = int(self.farm_config.get('ssh_port', 22))
            jump_username = self.farm_config.get('ssh_username', '')
            jump_password = self.jump_password.get()

            self.log_message("Connessione in corso...")

            jump_client = paramiko.SSHClient()
            jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_client.connect(
                hostname=jump_host,
                port=jump_port,
                username=jump_username,
                password=jump_password
            )

            target_host = self.farm_config.get('target_host', '')
            target_username = self.farm_config.get('target_username', jump_username)
            target_password = self.target_password.get() if not self.same_credentials.get() else jump_password
            working_folder = self.farm_config.get('working_folder', '/project/pmten/simulations/')
            work_folder = working_folder.rstrip('/')

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
                sock=jump_channel
            )

            self.log_message("✓ Connesso al farm")

            source_root = source_folder if source_folder.startswith('/') else f"{work_folder}/{source_folder}"
            destination_root = destination_folder if destination_folder.startswith('/') else f"{work_folder}/{destination_folder}"

            self.log_message("Verifica cartelle remote per il calcolo medie...")
            stdin, stdout, stderr = target_client.exec_command(
                f'test -d "{source_root}" && echo "OK" || echo "FAIL"'
            )
            if stdout.read().decode().strip() != "OK":
                raise RuntimeError(f"Cartella sorgente non trovata: {source_root}")

            source_root_literal = json.dumps(source_root)
            destination_root_literal = json.dumps(destination_root)
            granularities_literal = json.dumps(granularities)

            remote_script = self._render_script_template(
                "python/calc_mean.py.template",
                {
                    "TPL_SOURCE_ROOT_LITERAL": source_root_literal,
                    "TPL_DESTINATION_ROOT_LITERAL": destination_root_literal,
                    "TPL_GRANULARITIES_LITERAL": granularities_literal,
                },
            )

            if run_in_background:
                target_client.exec_command(f'mkdir -p "{destination_root}"')
                script_path = f"{work_folder}/run_mean_background.sh"
                bsub_out = f"{destination_root}/mean_output.log"
                bsub_err = f"{destination_root}/mean_error.log"
                wrapper_script = "#!/bin/bash\nset -e\npython3 - <<'PY'\n" + remote_script + "\nPY\n"

                self.log_message("Creazione script remoto medie (background)...")
                sftp = target_client.open_sftp()
                with sftp.open(script_path, 'w') as script_file:
                    script_file.write(wrapper_script)
                sftp.close()

                target_client.exec_command(f'chmod +x "{script_path}"')
                target_client.exec_command(f'rm -f "{bsub_out}" "{bsub_err}"')

                bsub_command = (
                    f'cd "{work_folder}"; '
                    f'bsub -q pmten -o "{bsub_out}" -e "{bsub_err}" "{script_path}"'
                )
                stdin, stdout, stderr = target_client.exec_command(bsub_command)
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                exit_status = stdout.channel.recv_exit_status()

                if output:
                    self.log_message(f"Output bsub medie:\n{output}")
                if error:
                    self.log_message(f"Stderr bsub medie:\n{error}")

                if exit_status != 0:
                    raise RuntimeError(error or f"Sottomissione medie fallita con exit code {exit_status}")

                self.log_message("\n✓ Job medie sottomesso in background!")
                self.log_message(f"Log output: {bsub_out}")
                self.log_message(f"Log errori: {bsub_err}")
                messagebox.showwarning(
                    "Job Medie Sottomesso",
                    "Job medie sottomesso con bsub -q pmten.\n\n"
                    "Il lavoro non è monitorato dalla UI.\n"
                    f"Controlla i log:\n{bsub_out}\n{bsub_err}"
                )
                return

            remote_command = "python3 - <<'PY'\n" + remote_script + "\nPY"

            self.log_message("Esecuzione calcolo medie sul server...")
            stdin, stdout, stderr = target_client.exec_command(remote_command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            exit_status = stdout.channel.recv_exit_status()

            if output:
                self.log_message(f"Output medie:\n{output}")
            if error:
                self.log_message(f"Stderr medie:\n{error}")

            if exit_status != 0:
                raise RuntimeError(error or f"Calcolo medie fallito con exit code {exit_status}")

            lines = [line.strip() for line in output.splitlines() if line.strip()]
            if not lines:
                raise RuntimeError("Nessun riepilogo restituito dal calcolo medie")

            try:
                summary = json.loads(lines[-1])
            except json.JSONDecodeError as decode_error:
                raise RuntimeError(f"Riepilogo medie non valido: {decode_error}") from decode_error

            details = summary.get('details', {})
            warnings = summary.get('warnings', [])
            skipped = summary.get('skipped_files', [])

            self.log_message("\n✓ Calcolo medie completato con successo!")
            self.log_message(f"Sorgente: {summary.get('source_root', source_root)}")
            self.log_message(f"Destinazione: {summary.get('destination_root', destination_root)}")
            self.log_message(f"Parametri processati: {summary.get('parameters_processed', 0)}")
            self.log_message(f"File output creati: {summary.get('outputs_created', 0)}")

            for parameter_name in sorted(details.keys()):
                for granularity, gran_summary in details[parameter_name].items():
                    self.log_message(
                        f"  - {parameter_name}/{granularity.upper()}: "
                        f"periodi={gran_summary.get('periods_found', 0)}, "
                        f"output={gran_summary.get('outputs_created', 0)}"
                    )

            if warnings:
                self.log_message(f"Warning ({len(warnings)}):")
                for warning in warnings[:20]:
                    self.log_message(f"  * {warning}")
                if len(warnings) > 20:
                    self.log_message(f"  * ... altri {len(warnings) - 20} warning")

            if skipped:
                self.log_message(f"File saltati: {len(skipped)}")

            messagebox.showinfo(
                "Successo",
                "Calcolo medie completato!\n\n"
                f"Parametri processati: {summary.get('parameters_processed', 0)}\n"
                f"Output creati: {summary.get('outputs_created', 0)}\n"
                f"Warning: {len(warnings)}"
            )

        except Exception as e:
            self.log_message(f"\n✗ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante Launch Mean:\n\n{str(e)}")
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
    
    def launch_percentile(self):
        """Calcola percentili giornalieri/mensili/annuali dai CSV aggregati"""
        if not PARAMIKO_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Il modulo 'paramiko' non è installato.\n\n"
                "Installa con: pip install paramiko"
            )
            return

        if not self.farm_config:
            messagebox.showerror(
                "Errore",
                "Nessuna configurazione farm trovata.\n\n"
                "Configura prima il Farm dalla finestra 'Configurazione Farm'."
            )
            return

        if not self.jump_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Jump Server!")
            return

        if not self.same_credentials.get() and not self.target_password.get():
            messagebox.showerror("Errore", "Inserisci la password per il Target Server!")
            return

        post_process_path = self.temp_dir / "post_process.json"
        saved_source_folder = "AGGREG"
        saved_output_folder = "PERCENTILE"
        saved_granularity = ["daily"]
        saved_percentiles = [98.0]
        saved_background = False
        if post_process_path.exists():
            try:
                with open(post_process_path, 'r', encoding='utf-8') as _f:
                    _pp = json.load(_f)
                saved_source_folder = str(_pp.get('percentile_source_folder', _pp.get('aggreg_folder', 'AGGREG'))).strip() or 'AGGREG'
                saved_output_folder = str(_pp.get('percentile_output_folder', 'PERCENTILE')).strip() or 'PERCENTILE'
                saved_background = bool(_pp.get('percentile_background', False))
                configured = _pp.get('percentile_granularity', ['daily'])
                if isinstance(configured, list):
                    saved_granularity = [str(item).lower() for item in configured if str(item).strip()]
                elif isinstance(configured, str) and configured.strip():
                    saved_granularity = [configured.strip().lower()]

                configured_percentiles = _pp.get('percentile_values', [98])
                parsed = []
                if isinstance(configured_percentiles, list):
                    for value in configured_percentiles:
                        try:
                            parsed.append(float(value))
                        except Exception:
                            continue
                elif isinstance(configured_percentiles, (str, int, float)):
                    text_value = str(configured_percentiles)
                    for chunk in text_value.split(','):
                        chunk = chunk.strip()
                        if not chunk:
                            continue
                        try:
                            parsed.append(float(chunk))
                        except Exception:
                            continue
                cleaned = [value for value in parsed if 0 < value <= 100]
                if cleaned:
                    saved_percentiles = cleaned
            except Exception:
                pass

        dialog = tk.Toplevel(self.window)
        dialog.title("Calcolo Percentili")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self.window)

        dialog_result = {}

        tk.Label(
            dialog,
            text="Cartella sorgente (aggregata):",
            font=('TkDefaultFont', 10, 'bold')
        ).grid(row=0, column=0, columnspan=2, sticky='w', padx=12, pady=(12, 2))

        source_var = tk.StringVar(value=saved_source_folder)
        tk.Entry(dialog, textvariable=source_var, width=32).grid(
            row=1, column=0, columnspan=2, sticky='w', padx=24, pady=(0, 8)
        )

        tk.Label(
            dialog,
            text="Cartella destinazione percentili:",
            font=('TkDefaultFont', 10, 'bold')
        ).grid(row=2, column=0, columnspan=2, sticky='w', padx=12, pady=(2, 2))

        destination_var = tk.StringVar(value=saved_output_folder)
        tk.Entry(dialog, textvariable=destination_var, width=32).grid(
            row=3, column=0, columnspan=2, sticky='w', padx=24, pady=(0, 8)
        )

        tk.Label(
            dialog,
            text="Granularità percentile (seleziona una o più):",
            font=('TkDefaultFont', 10, 'bold')
        ).grid(row=4, column=0, columnspan=2, sticky='w', padx=12, pady=(2, 2))

        daily_var = tk.BooleanVar(value='daily' in saved_granularity)
        monthly_var = tk.BooleanVar(value='monthly' in saved_granularity)
        annual_var = tk.BooleanVar(value='annual' in saved_granularity)

        tk.Checkbutton(dialog, text="Daily", variable=daily_var).grid(
            row=5, column=0, sticky='w', padx=24
        )
        tk.Checkbutton(dialog, text="Monthly", variable=monthly_var).grid(
            row=6, column=0, sticky='w', padx=24
        )
        tk.Checkbutton(dialog, text="Annual", variable=annual_var).grid(
            row=7, column=0, sticky='w', padx=24
        )

        tk.Label(
            dialog,
            text="Percentili (preset + custom):",
            font=('TkDefaultFont', 10, 'bold')
        ).grid(row=8, column=0, columnspan=2, sticky='w', padx=12, pady=(8, 2))

        preset_values = [90.0, 95.0, 98.0, 99.0, 100.0]
        preset_vars = {}
        for idx, preset in enumerate(preset_values):
            checked = any(abs(value - preset) < 1e-6 for value in saved_percentiles)
            var = tk.BooleanVar(value=checked)
            preset_vars[preset] = var
            label = f"P{int(preset) if abs(preset - int(preset)) < 1e-6 else preset:g}"
            tk.Checkbutton(dialog, text=label, variable=var).grid(
                row=9 + idx, column=0, sticky='w', padx=24
            )

        custom_percentiles = [
            value for value in saved_percentiles
            if all(abs(value - preset) >= 1e-6 for preset in preset_values)
        ]
        custom_var = tk.StringVar(
            value=','.join(
                f"{int(value)}" if abs(value - int(value)) < 1e-6 else f"{value:g}"
                for value in custom_percentiles
            )
        )

        tk.Label(dialog, text="Custom (es. 92,97.5,100):").grid(
            row=13, column=0, sticky='w', padx=24, pady=(2, 0)
        )
        tk.Entry(dialog, textvariable=custom_var, width=24).grid(
            row=14, column=0, columnspan=2, sticky='w', padx=24, pady=(0, 8)
        )

        background_var = tk.BooleanVar(value=saved_background)
        tk.Checkbutton(
            dialog,
            text="Esegui in background con bsub -q pmten (job non monitorato)",
            variable=background_var
        ).grid(row=15, column=0, columnspan=2, sticky='w', padx=24, pady=(0, 8))

        def _normalize_percentiles(raw_values):
            unique_values = {}
            for value in raw_values:
                key = f"{value:.6f}"
                unique_values[key] = value
            sorted_values = [unique_values[key] for key in sorted(unique_values.keys(), key=lambda item: float(item))]
            normalized = []
            for value in sorted_values:
                if abs(value - int(value)) < 1e-6:
                    normalized.append(float(int(value)))
                else:
                    normalized.append(round(value, 6))
            return normalized

        def _on_ok():
            source_folder = source_var.get().strip()
            destination_folder = destination_var.get().strip()
            granularities = []
            if daily_var.get():
                granularities.append('daily')
            if monthly_var.get():
                granularities.append('monthly')
            if annual_var.get():
                granularities.append('annual')

            percentile_values = []
            for preset, preset_var in preset_vars.items():
                if preset_var.get():
                    percentile_values.append(float(preset))

            invalid_values = []
            custom_text = custom_var.get().strip()
            if custom_text:
                for chunk in custom_text.split(','):
                    chunk = chunk.strip()
                    if not chunk:
                        continue
                    try:
                        parsed = float(chunk)
                    except Exception:
                        invalid_values.append(chunk)
                        continue
                    if not (0 < parsed <= 100):
                        invalid_values.append(chunk)
                        continue
                    percentile_values.append(parsed)

            if not source_folder:
                messagebox.showerror("Errore", "La cartella sorgente non può essere vuota.", parent=dialog)
                return
            if not destination_folder:
                messagebox.showerror("Errore", "La cartella destinazione non può essere vuota.", parent=dialog)
                return
            if not granularities:
                messagebox.showerror("Errore", "Seleziona almeno una granularità.", parent=dialog)
                return
            if invalid_values:
                messagebox.showerror(
                    "Errore",
                    "Valori percentile non validi: " + ", ".join(invalid_values),
                    parent=dialog
                )
                return

            percentile_values = [value for value in percentile_values if 0 < value <= 100]
            percentile_values = _normalize_percentiles(percentile_values)
            if not percentile_values:
                messagebox.showerror("Errore", "Seleziona almeno un percentile valido.", parent=dialog)
                return

            dialog_result['source_folder'] = source_folder
            dialog_result['destination_folder'] = destination_folder
            dialog_result['granularities'] = granularities
            dialog_result['percentiles'] = percentile_values
            dialog_result['run_in_background'] = background_var.get()
            dialog.destroy()

        def _on_cancel():
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=16, column=0, columnspan=2, pady=(8, 12))
        tk.Button(btn_frame, text="OK", width=10, command=_on_ok).pack(side='left', padx=6)
        tk.Button(btn_frame, text="Annulla", width=10, command=_on_cancel).pack(side='left', padx=6)

        self.window.wait_window(dialog)

        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch Percentile")

        if not dialog_result:
            self.log_message("Operazione annullata dall'utente.")
            return

        source_folder = dialog_result['source_folder']
        destination_folder = dialog_result['destination_folder']
        granularities = dialog_result['granularities']
        percentiles = dialog_result['percentiles']
        run_in_background = bool(dialog_result.get('run_in_background', False))

        try:
            previous = {}
            if post_process_path.exists():
                with open(post_process_path, 'r', encoding='utf-8') as _f:
                    previous = json.load(_f)
            previous['percentile_source_folder'] = source_folder
            previous['percentile_output_folder'] = destination_folder
            previous['percentile_granularity'] = granularities
            previous['percentile_values'] = percentiles
            previous['percentile_background'] = run_in_background
            with open(post_process_path, 'w', encoding='utf-8') as _f:
                json.dump(previous, _f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        def _fmt_percentile(value):
            if abs(value - int(value)) < 1e-6:
                return str(int(value))
            return f"{value:g}"

        self.log_message(f"Sorgente: {source_folder}")
        self.log_message(f"Destinazione: {destination_folder}")
        self.log_message(f"Granularità selezionate: {', '.join(granularities)}")
        self.log_message("Percentili selezionati: " + ", ".join(f"P{_fmt_percentile(value)}" for value in percentiles))
        self.log_message(
            "Modalità esecuzione: background (bsub -q pmten, job non monitorato)"
            if run_in_background else
            "Modalità esecuzione: foreground (monitorata dalla UI)"
        )

        if run_in_background:
            messagebox.showwarning(
                "Attenzione",
                "Il calcolo percentili verrà sottomesso in background con bsub -q pmten.\n"
                "Il lavoro non sarà monitorato dalla UI."
            )

        thread = threading.Thread(
            target=self._launch_percentile_thread,
            args=(source_folder, destination_folder, granularities, percentiles, run_in_background)
        )
        thread.daemon = True
        thread.start()

    def _launch_percentile_thread(self, source_folder, destination_folder, granularities, percentiles, run_in_background=False):
        """Thread per calcolare percentili dai CSV aggregati"""
        jump_client = None
        target_client = None
        try:
            jump_host = self.farm_config.get('ssh_host', '')
            jump_port = int(self.farm_config.get('ssh_port', 22))
            jump_username = self.farm_config.get('ssh_username', '')
            jump_password = self.jump_password.get()

            self.log_message("Connessione in corso...")

            jump_client = paramiko.SSHClient()
            jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_client.connect(
                hostname=jump_host,
                port=jump_port,
                username=jump_username,
                password=jump_password
            )

            target_host = self.farm_config.get('target_host', '')
            target_username = self.farm_config.get('target_username', jump_username)
            target_password = self.target_password.get() if not self.same_credentials.get() else jump_password
            working_folder = self.farm_config.get('working_folder', '/project/pmten/simulations/')
            work_folder = working_folder.rstrip('/')

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
                sock=jump_channel
            )

            self.log_message("✓ Connesso al farm")

            source_root = source_folder if source_folder.startswith('/') else f"{work_folder}/{source_folder}"
            destination_root = destination_folder if destination_folder.startswith('/') else f"{work_folder}/{destination_folder}"

            self.log_message("Verifica cartelle remote per il calcolo percentili...")
            stdin, stdout, stderr = target_client.exec_command(
                f'test -d "{source_root}" && echo "OK" || echo "FAIL"'
            )
            if stdout.read().decode().strip() != "OK":
                raise RuntimeError(f"Cartella sorgente non trovata: {source_root}")

            source_root_literal = json.dumps(source_root)
            destination_root_literal = json.dumps(destination_root)
            granularities_literal = json.dumps(granularities)
            percentiles_literal = json.dumps(percentiles)

            remote_script = self._render_script_template(
                "python/calc_percentile.py.template",
                {
                    "TPL_SOURCE_ROOT_LITERAL": source_root_literal,
                    "TPL_DESTINATION_ROOT_LITERAL": destination_root_literal,
                    "TPL_GRANULARITIES_LITERAL": granularities_literal,
                    "TPL_PERCENTILES_LITERAL": percentiles_literal,
                },
            )

            if run_in_background:
                target_client.exec_command(f'mkdir -p "{destination_root}"')
                script_path = f"{work_folder}/run_percentile_background.sh"
                bsub_out = f"{destination_root}/percentile_output.log"
                bsub_err = f"{destination_root}/percentile_error.log"
                wrapper_script = "#!/bin/bash\nset -e\npython3 - <<'PY'\n" + remote_script + "\nPY\n"

                self.log_message("Creazione script remoto percentili (background)...")
                sftp = target_client.open_sftp()
                with sftp.open(script_path, 'w') as script_file:
                    script_file.write(wrapper_script)
                sftp.close()

                target_client.exec_command(f'chmod +x "{script_path}"')
                target_client.exec_command(f'rm -f "{bsub_out}" "{bsub_err}"')

                bsub_command = (
                    f'cd "{work_folder}"; '
                    f'bsub -q pmten -o "{bsub_out}" -e "{bsub_err}" "{script_path}"'
                )
                stdin, stdout, stderr = target_client.exec_command(bsub_command)
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                exit_status = stdout.channel.recv_exit_status()

                if output:
                    self.log_message(f"Output bsub percentili:\n{output}")
                if error:
                    self.log_message(f"Stderr bsub percentili:\n{error}")

                if exit_status != 0:
                    raise RuntimeError(error or f"Sottomissione percentili fallita con exit code {exit_status}")

                self.log_message("\n✓ Job percentili sottomesso in background!")
                self.log_message(f"Log output: {bsub_out}")
                self.log_message(f"Log errori: {bsub_err}")
                messagebox.showwarning(
                    "Job Percentili Sottomesso",
                    "Job percentili sottomesso con bsub -q pmten.\n\n"
                    "Il lavoro non è monitorato dalla UI.\n"
                    f"Controlla i log:\n{bsub_out}\n{bsub_err}"
                )
                return

            remote_command = "python3 - <<'PY'\n" + remote_script + "\nPY"

            self.log_message("Esecuzione calcolo percentili sul server...")
            stdin, stdout, stderr = target_client.exec_command(remote_command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            exit_status = stdout.channel.recv_exit_status()

            if output:
                self.log_message(f"Output percentili:\n{output}")
            if error:
                self.log_message(f"Stderr percentili:\n{error}")

            if exit_status != 0:
                raise RuntimeError(error or f"Calcolo percentili fallito con exit code {exit_status}")

            lines = [line.strip() for line in output.splitlines() if line.strip()]
            if not lines:
                raise RuntimeError("Nessun riepilogo restituito dal calcolo percentili")

            try:
                summary = json.loads(lines[-1])
            except json.JSONDecodeError as decode_error:
                raise RuntimeError(f"Riepilogo percentili non valido: {decode_error}") from decode_error

            details = summary.get('details', {})
            warnings = summary.get('warnings', [])
            skipped = summary.get('skipped_files', [])
            requested_percentiles = summary.get('requested_percentiles', percentiles)

            def _fmt_percentile(value):
                try:
                    numeric_value = float(value)
                except Exception:
                    return str(value)
                if abs(numeric_value - int(numeric_value)) < 1e-6:
                    return str(int(numeric_value))
                return f"{numeric_value:g}"

            self.log_message("\n✓ Calcolo percentili completato con successo!")
            self.log_message(f"Sorgente: {summary.get('source_root', source_root)}")
            self.log_message(f"Destinazione: {summary.get('destination_root', destination_root)}")
            self.log_message(
                "Percentili calcolati: " +
                ", ".join(f"P{_fmt_percentile(value)}" for value in requested_percentiles)
            )
            self.log_message(f"Parametri processati: {summary.get('parameters_processed', 0)}")
            self.log_message(f"File output creati: {summary.get('outputs_created', 0)}")

            for parameter_name in sorted(details.keys()):
                for granularity, gran_summary in details[parameter_name].items():
                    self.log_message(
                        f"  - {parameter_name}/{granularity.upper()}: "
                        f"periodi={gran_summary.get('periods_found', 0)}, "
                        f"output={gran_summary.get('outputs_created', 0)}"
                    )

            if warnings:
                self.log_message(f"Warning ({len(warnings)}):")
                for warning in warnings[:20]:
                    self.log_message(f"  * {warning}")
                if len(warnings) > 20:
                    self.log_message(f"  * ... altri {len(warnings) - 20} warning")

            if skipped:
                self.log_message(f"File saltati: {len(skipped)}")

            messagebox.showinfo(
                "Successo",
                "Calcolo percentili completato!\n\n"
                f"Parametri processati: {summary.get('parameters_processed', 0)}\n"
                f"Output creati: {summary.get('outputs_created', 0)}\n"
                f"Warning: {len(warnings)}"
            )

        except Exception as e:
            self.log_message(f"\n✗ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante Launch Percentile:\n\n{str(e)}")
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
