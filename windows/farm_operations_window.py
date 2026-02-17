"""
Finestra per le operazioni sul Farm remoto
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
from pathlib import Path
import threading

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
        
        self.setup_ui()
    
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
            
            # Upload dei file di output se presenti
            self.log_message("\n" + "-"*50)
            self.log_message("Upload file di output:")
            
            uploaded_files = []
            
            # File da caricare: (percorso_locale, percorso_remoto, descrizione)
            files_to_upload = [
                (Path("Outputs/oro.txt"), f"{working_folder}/TERREL/orografia/oro.txt", "orografia"),
                (Path("Outputs/landuse.xyz"), f"{working_folder}/CTGPROC/landuse.xyz", "landuse")
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
                    self.log_message(f"\n✓ {operation_name} completato con successo!")
                    messagebox.showinfo("Successo", f"{operation_name} completato!\nCartella {folder_name} copiata con successo.")
                else:
                    self.log_message(f"  ✗ ERRORE durante la copia: {error}")
                    messagebox.showerror("Errore", f"Errore durante la copia:\n{error}")
            
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
        """Lancia elaborazione dati geografici - DA IMPLEMENTARE"""
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch Geographic")
        self.log_message("⚠ Funzione da implementare")
        messagebox.showinfo("Info", "Funzione Launch Geographic da implementare")
    
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
        """Carica file INP per CALMET - DA IMPLEMENTARE"""
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Load inp CALMET")
        self.log_message("⚠ Funzione da implementare")
        messagebox.showinfo("Info", "Funzione Load inp CALMET da implementare")
    
    def launch_calmet(self):
        """Lancia l'esecuzione di CALMET - DA IMPLEMENTARE"""
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch CALMET")
        self.log_message("⚠ Funzione da implementare")
        messagebox.showinfo("Info", "Funzione Launch CALMET da implementare")
    
    def load_inp_calpuff(self):
        """Carica file INP per CALPUFF - DA IMPLEMENTARE"""
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Load inp CALPUFF")
        self.log_message("⚠ Funzione da implementare")
        messagebox.showinfo("Info", "Funzione Load inp CALPUFF da implementare")
    
    def launch_calpuff(self):
        """Lancia l'esecuzione di CALPUFF - DA IMPLEMENTARE"""
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch CALPUFF")
        self.log_message("⚠ Funzione da implementare")
        messagebox.showinfo("Info", "Funzione Launch CALPUFF da implementare")
    
    def load_inp_calpost(self):
        """Carica file INP per CALPOST - DA IMPLEMENTARE"""
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Load inp CALPOST")
        self.log_message("⚠ Funzione da implementare")
        messagebox.showinfo("Info", "Funzione Load inp CALPOST da implementare")
    
    def launch_calpost(self):
        """Lancia l'esecuzione di CALPOST - DA IMPLEMENTARE"""
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch CALPOST")
        self.log_message("⚠ Funzione da implementare")
        messagebox.showinfo("Info", "Funzione Launch CALPOST da implementare")
    
    def launch_aggreg(self):
        """Lancia aggregazione dati - DA IMPLEMENTARE"""
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch Aggreg")
        self.log_message("⚠ Funzione da implementare")
        messagebox.showinfo("Info", "Funzione Launch Aggreg da implementare")
    
    def launch_mean(self):
        """Lancia calcolo medie - DA IMPLEMENTARE"""
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch Mean")
        self.log_message("⚠ Funzione da implementare")
        messagebox.showinfo("Info", "Funzione Launch Mean da implementare")
    
    def launch_percentile(self):
        """Lancia calcolo percentili - DA IMPLEMENTARE"""
        self.log_message("\n" + "="*50)
        self.log_message("Operazione: Launch Percentile")
        self.log_message("⚠ Funzione da implementare")
        messagebox.showinfo("Info", "Funzione Launch Percentile da implementare")
