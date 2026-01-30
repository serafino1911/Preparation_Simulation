"""
Finestra per la configurazione del Farm (connessione SSH e cartella di lavoro)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from pathlib import Path

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False


class FarmWindow:
    """Finestra per configurare la connessione al Farm"""
    
    def __init__(self, parent, temp_dir):
        self.parent = parent
        self.temp_dir = temp_dir
        self.window = tk.Toplevel(parent)
        self.window.title("Configurazione Farm")
        self.window.geometry("650x650")
        
        # Variabili Jump Server (primo server)
        self.ssh_host = tk.StringVar(value="linuxge.ge.infn.it")
        self.ssh_port = tk.StringVar(value="22")
        self.ssh_username = tk.StringVar()
        self.ssh_password = tk.StringVar()
        self.use_key = tk.BooleanVar(value=False)
        self.ssh_key_path = tk.StringVar()
        
        # Variabili Target Server (server finale)
        self.target_host = tk.StringVar(value="hpcpmten1")
        self.target_username = tk.StringVar()
        self.target_password = tk.StringVar()
        
        # Checkbox per usare le stesse credenziali
        self.same_credentials = tk.BooleanVar(value=True)
        
        self.working_folder = tk.StringVar(value="/project/pmten/simulations/")
        
        # Carica configurazione esistente se presente
        self.load_existing_config()
        
        # Aggiungi callback per sincronizzare le credenziali
        self.ssh_username.trace_add('write', lambda *args: self.sync_credentials())
        self.ssh_password.trace_add('write', lambda *args: self.sync_credentials())
        
        self.setup_ui()
    
    def load_existing_config(self):
        """Carica la configurazione farm esistente se presente"""
        config_file = self.temp_dir / "farm_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.ssh_host.set(config.get('ssh_host', ''))
                self.ssh_port.set(config.get('ssh_port', '22'))
                self.ssh_username.set(config.get('ssh_username', ''))
                # Non caricare la password per sicurezza
                self.use_key.set(config.get('use_key', False))
                self.ssh_key_path.set(config.get('ssh_key_path', ''))
                self.target_host.set(config.get('target_host', 'hpcpmten1'))
                self.target_username.set(config.get('target_username', ''))
                self.same_credentials.set(config.get('same_credentials', True))
                # Non caricare la password target per sicurezza
                self.working_folder.set(config.get('working_folder', ''))
            except Exception as e:
                print(f"Errore durante il caricamento della configurazione farm: {e}")
    
    def setup_ui(self):
        """Configura l'interfaccia della finestra"""
        # Frame principale
        main_frame = ttk.Frame(self.window, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configura il grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # === TITOLO ===
        title_label = ttk.Label(
            main_frame,
            text="⚙ Configurazione Connessione Farm",
            font=('Arial', 13, 'bold')
        )
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # === SEZIONE JUMP SERVER (GATEWAY) ===
        ssh_frame = ttk.LabelFrame(main_frame, text="🔒 Jump Server (Gateway)", padding="10")
        ssh_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        ssh_frame.columnconfigure(1, weight=1)
        ssh_frame.columnconfigure(3, weight=1)
        
        ttk.Label(
            ssh_frame,
            text="Server gateway per accedere alla farm",
            foreground='gray',
            font=('Arial', 8)
        ).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 8))
        
        # Host e Porta sulla stessa riga
        ttk.Label(ssh_frame, text="Host:").grid(
            row=1, column=0, sticky=tk.W, pady=3, padx=(0, 5)
        )
        ttk.Entry(ssh_frame, textvariable=self.ssh_host).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=3, padx=(0, 10)
        )
        
        ttk.Label(ssh_frame, text="Porta:").grid(
            row=1, column=2, sticky=tk.W, pady=3, padx=(0, 5)
        )
        ttk.Entry(ssh_frame, textvariable=self.ssh_port, width=8).grid(
            row=1, column=3, sticky=tk.W, pady=3
        )
        
        # Username
        ttk.Label(ssh_frame, text="Username:").grid(
            row=2, column=0, sticky=tk.W, pady=3, padx=(0, 5)
        )
        ttk.Entry(ssh_frame, textvariable=self.ssh_username).grid(
            row=2, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=3
        )
        
        # Password
        self.password_label = ttk.Label(ssh_frame, text="Password:")
        self.password_label.grid(row=3, column=0, sticky=tk.W, pady=3, padx=(0, 5))
        
        self.password_entry = ttk.Entry(ssh_frame, textvariable=self.ssh_password, show="*")
        self.password_entry.grid(row=3, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=3)
        
        # Checkbox per usare chiave SSH
        ttk.Checkbutton(
            ssh_frame,
            text="Usa chiave SSH invece",
            variable=self.use_key,
            command=self.toggle_auth_method
        ).grid(row=4, column=0, columnspan=4, sticky=tk.W, pady=(8, 3))
        
        # Chiave SSH
        self.key_label = ttk.Label(ssh_frame, text="Chiave SSH:")
        self.key_label.grid(row=5, column=0, sticky=tk.W, pady=3, padx=(0, 5))
        
        key_frame = ttk.Frame(ssh_frame)
        key_frame.grid(row=5, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=3)
        
        self.key_entry = ttk.Entry(key_frame, textvariable=self.ssh_key_path)
        self.key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.key_browse_btn = ttk.Button(
            key_frame,
            text="📁",
            command=self.browse_key_file,
            width=3
        )
        self.key_browse_btn.pack(side=tk.LEFT)
        
        # === SEZIONE TARGET SERVER ===
        target_frame = ttk.LabelFrame(main_frame, text="🎯 Target Server (Farm Finale)", padding="10")
        target_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        target_frame.columnconfigure(1, weight=1)
        
        ttk.Label(
            target_frame,
            text="Server di destinazione finale (es: hpcpmten1)",
            foreground='gray',
            font=('Arial', 8)
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))
        
        # Target Host
        ttk.Label(target_frame, text="Host:").grid(
            row=1, column=0, sticky=tk.W, pady=3, padx=(0, 5)
        )
        ttk.Entry(target_frame, textvariable=self.target_host).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=3
        )
        
        # Checkbox stesse credenziali
        ttk.Checkbutton(
            target_frame,
            text="✓ Usa le stesse credenziali del Jump Server",
            variable=self.same_credentials,
            command=self.toggle_target_credentials
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(8, 3))
        
        # Target Username
        ttk.Label(target_frame, text="Username:").grid(
            row=3, column=0, sticky=tk.W, pady=3, padx=(0, 5)
        )
        self.target_username_entry = ttk.Entry(target_frame, textvariable=self.target_username)
        self.target_username_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=3)
        
        # Target Password
        self.target_password_label = ttk.Label(target_frame, text="Password:")
        self.target_password_label.grid(row=4, column=0, sticky=tk.W, pady=3, padx=(0, 5))
        
        self.target_password_entry = ttk.Entry(target_frame, textvariable=self.target_password, show="*")
        self.target_password_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=3)
        
        # === SEZIONE CARTELLA DI LAVORO ===
        folder_frame = ttk.LabelFrame(main_frame, text="📂 Cartella di Lavoro", padding="10")
        folder_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        folder_frame.columnconfigure(1, weight=1)
        
        ttk.Label(folder_frame, text="Percorso:").grid(
            row=0, column=0, sticky=tk.W, pady=3, padx=(0, 5)
        )
        
        ttk.Entry(folder_frame, textvariable=self.working_folder).grid(
            row=0, column=1, sticky=(tk.W, tk.E), pady=3
        )
        
        ttk.Label(
            folder_frame,
            text="Es: /project/pmten/simulations/",
            foreground='gray',
            font=('Arial', 8)
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))
        
        # === SEPARATORE ===
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=4, column=0, sticky=(tk.W, tk.E), pady=15
        )
        
        # === PULSANTI ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, pady=(0, 5))
        
        ttk.Button(
            button_frame,
            text="🔌 Test Connessione",
            command=self.test_connection,
            width=22
        ).pack(side=tk.LEFT, padx=3)
        
        ttk.Button(
            button_frame,
            text="💾 Salva",
            command=self.save_config,
            width=12
        ).pack(side=tk.LEFT, padx=3)
        
        ttk.Button(
            button_frame,
            text="✖ Chiudi",
            command=self.window.destroy,
            width=12
        ).pack(side=tk.LEFT, padx=3)
        
        # Imposta lo stato iniziale dei campi
        self.toggle_auth_method()
        self.toggle_target_credentials()
    
    def toggle_auth_method(self):
        """Attiva/disattiva i campi in base al metodo di autenticazione"""
        if self.use_key.get():
            # Disabilita password, abilita chiave
            self.password_entry.config(state='disabled')
            self.key_entry.config(state='normal')
            self.key_browse_btn.config(state='normal')
        else:
            # Abilita password, disabilita chiave
            self.password_entry.config(state='normal')
            self.key_entry.config(state='disabled')
            self.key_browse_btn.config(state='disabled')
    
    def toggle_target_credentials(self):
        """Attiva/disattiva i campi del target server in base al checkbox"""
        if self.same_credentials.get():
            # Usa le stesse credenziali - disabilita i campi target e sincronizza
            self.target_username_entry.config(state='disabled')
            self.target_password_entry.config(state='disabled')
            # Sincronizza i valori
            self.sync_credentials()
        else:
            # Usa credenziali diverse - abilita i campi target
            self.target_username_entry.config(state='normal')
            self.target_password_entry.config(state='normal')
    
    def sync_credentials(self):
        """Sincronizza le credenziali dal jump server al target server"""
        if self.same_credentials.get():
            self.target_username.set(self.ssh_username.get())
            self.target_password.set(self.ssh_password.get())
    
    def browse_key_file(self):
        """Apre il dialog per selezionare il file della chiave SSH"""
        filename = filedialog.askopenfilename(
            title="Seleziona il file della chiave SSH",
            filetypes=[
                ("Tutti i file", "*.*"),
                ("File PEM", "*.pem"),
                ("File chiave privata", "id_rsa"),
            ]
        )
        
        if filename:
            self.ssh_key_path.set(filename)
    
    def check_folder_path(self, ssh_client):
        """Verifica l'esistenza e l'accessibilità della cartella di lavoro"""
        working_folder = self.working_folder.get()
        
        if not working_folder:
            return {
                'status': 'not_specified',
                'message': "⚠ Cartella di lavoro:\n  └─ Non specificata",
                'can_create': False
            }
        
        try:
            # Verifica se il percorso esiste
            stdin, stdout, stderr = ssh_client.exec_command(f'test -e "{working_folder}" && echo "EXISTS" || echo "NOT_EXISTS"')
            exists_result = stdout.read().decode().strip()
            
            if exists_result == "NOT_EXISTS":
                # Il percorso non esiste, trova dove si interrompe
                broken_info = self.find_broken_path(ssh_client, working_folder)
                
                message = (
                    f"✗ Cartella di lavoro: NON ESISTE\n"
                    f"  └─ Percorso: {working_folder}\n"
                    f"  └─ Il percorso si interrompe a: {broken_info['last_valid']}\n"
                    f"  └─ Manca: {broken_info['missing_part']}"
                )
                
                return {
                    'status': 'not_exists',
                    'message': message,
                    'can_create': broken_info['can_create'],
                    'missing_folder': broken_info['missing_part']
                }
            
            # Verifica se è una directory
            stdin, stdout, stderr = ssh_client.exec_command(f'test -d "{working_folder}" && echo "DIR" || echo "NOT_DIR"')
            is_dir_result = stdout.read().decode().strip()
            
            if is_dir_result == "NOT_DIR":
                return {
                    'status': 'not_directory',
                    'message': (
                        f"✗ Cartella di lavoro: NON È UNA DIRECTORY\n"
                        f"  └─ Percorso: {working_folder}\n"
                        f"  └─ Il percorso esiste ma è un file, non una cartella"
                    ),
                    'can_create': False
                }
            
            # Verifica i permessi di lettura e scrittura
            stdin, stdout, stderr = ssh_client.exec_command(f'test -r "{working_folder}" && echo "READABLE" || echo "NOT_READABLE"')
            readable = stdout.read().decode().strip() == "READABLE"
            
            stdin, stdout, stderr = ssh_client.exec_command(f'test -w "{working_folder}" && echo "WRITABLE" || echo "NOT_WRITABLE"')
            writable = stdout.read().decode().strip() == "WRITABLE"
            
            # Ottieni informazioni aggiuntive
            stdin, stdout, stderr = ssh_client.exec_command(f'ls -ld "{working_folder}"')
            folder_info = stdout.read().decode().strip()
            
            if readable and writable:
                return {
                    'status': 'accessible',
                    'message': (
                        f"✓ Cartella di lavoro: ACCESSIBILE\n"
                        f"  └─ Percorso: {working_folder}\n"
                        f"  └─ Permessi: Lettura ✓ | Scrittura ✓\n"
                        f"  └─ Info: {folder_info}"
                    ),
                    'can_create': False
                }
            else:
                permissions_msg = []
                if not readable:
                    permissions_msg.append("Lettura ✗")
                if not writable:
                    permissions_msg.append("Scrittura ✗")
                
                return {
                    'status': 'limited_permissions',
                    'message': (
                        f"⚠ Cartella di lavoro: PERMESSI LIMITATI\n"
                        f"  └─ Percorso: {working_folder}\n"
                        f"  └─ Problemi: {' | '.join(permissions_msg)}\n"
                        f"  └─ Info: {folder_info}"
                    ),
                    'can_create': False
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': (
                    f"✗ Cartella di lavoro: ERRORE\n"
                    f"  └─ Percorso: {working_folder}\n"
                    f"  └─ Errore: {str(e)}"
                ),
                'can_create': False
            }
    
    def find_broken_path(self, ssh_client, full_path):
        """Trova il punto in cui il percorso si interrompe"""
        # Rimuovi lo slash finale se presente
        full_path = full_path.rstrip('/')
        
        # Dividi il percorso in parti
        parts = full_path.split('/')
        current_path = ""
        last_valid_path = "/"
        missing_parts = []
        
        for i, part in enumerate(parts):
            if not part:  # Salta parti vuote (come il primo elemento dopo lo split di un path assoluto)
                continue
            
            current_path += "/" + part
            
            try:
                # Verifica se questo percorso esiste
                stdin, stdout, stderr = ssh_client.exec_command(f'test -e "{current_path}" && echo "EXISTS" || echo "NOT_EXISTS"')
                exists = stdout.read().decode().strip() == "EXISTS"
                
                if exists:
                    last_valid_path = current_path
                else:
                    # Raccogli tutte le parti mancanti
                    missing_parts.append(part)
            except:
                missing_parts.append(part)
        
        # Può creare solo se manca solo l'ultima cartella
        can_create = len(missing_parts) == 1
        missing_str = '/'.join(missing_parts) if missing_parts else "nessuna"
        
        return {
            'last_valid': last_valid_path,
            'missing_part': missing_str,
            'can_create': can_create,
            'missing_count': len(missing_parts)
        }
    
    def create_folder(self, ssh_client, folder_path):
        """Crea la cartella di lavoro sul server remoto"""
        try:
            # Crea la cartella con mkdir -p (crea anche le directory parent se necessario)
            stdin, stdout, stderr = ssh_client.exec_command(f'mkdir -p "{folder_path}"')
            stderr_output = stderr.read().decode().strip()
            
            if stderr_output:
                return False, f"Errore durante la creazione: {stderr_output}"
            
            # Verifica che la cartella sia stata creata
            stdin, stdout, stderr = ssh_client.exec_command(f'test -d "{folder_path}" && echo "SUCCESS" || echo "FAILED"')
            result = stdout.read().decode().strip()
            
            if result == "SUCCESS":
                return True, "Cartella creata con successo!"
            else:
                return False, "La cartella non è stata creata correttamente"
                
        except Exception as e:
            return False, f"Errore: {str(e)}"
    
    def test_connection(self):
        """Testa la connessione SSH al server tramite jump host"""
        # Validazione base jump server
        if not self.ssh_host.get():
            messagebox.showerror("Errore", "Inserisci l'host del jump server!")
            return
        
        if not self.ssh_username.get():
            messagebox.showerror("Errore", "Inserisci il nome utente per il jump server!")
            return
        
        if not self.use_key.get() and not self.ssh_password.get():
            messagebox.showerror("Errore", "Inserisci la password o seleziona una chiave SSH per il jump server!")
            return
        
        if self.use_key.get() and not self.ssh_key_path.get():
            messagebox.showerror("Errore", "Seleziona il file della chiave SSH!")
            return
        
        # Validazione target server
        if not self.target_host.get():
            messagebox.showerror("Errore", "Inserisci l'host del target server!")
            return
        
        if not self.same_credentials.get():
            # Solo se usa credenziali diverse
            if not self.target_username.get():
                messagebox.showerror("Errore", "Inserisci il nome utente per il target server!")
                return
            
            if not self.target_password.get():
                messagebox.showerror("Errore", "Inserisci la password per il target server!")
                return
        else:
            # Se usa le stesse credenziali, sincronizza prima del test
            self.sync_credentials()
        
        # Verifica se paramiko è disponibile
        if not PARAMIKO_AVAILABLE:
            messagebox.showwarning(
                "Libreria mancante",
                "La libreria 'paramiko' non è installata.\n\n"
                "Per testare la connessione SSH, installa paramiko:\n"
                "pip install paramiko\n\n"
                "Parametri configurati:\n"
                f"Jump Server: {self.ssh_host.get()}:{self.ssh_port.get()}\n"
                f"Target Server: {self.target_host.get()}\n"
                f"Metodo: {'Chiave SSH' if self.use_key.get() else 'Password'}"
            )
            return
        
        # Test della connessione SSH a due hop
        jump_ssh = None
        target_ssh = None
        
        try:
            # Step 1: Connessione al jump server
            jump_ssh = paramiko.SSHClient()
            jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.use_key.get():
                jump_ssh.connect(
                    hostname=self.ssh_host.get(),
                    port=int(self.ssh_port.get()),
                    username=self.ssh_username.get(),
                    key_filename=self.ssh_key_path.get(),
                    timeout=10
                )
            else:
                jump_ssh.connect(
                    hostname=self.ssh_host.get(),
                    port=int(self.ssh_port.get()),
                    username=self.ssh_username.get(),
                    password=self.ssh_password.get(),
                    timeout=10
                )
            
            # Step 2: Connessione al target server tramite jump server
            # Crea un canale SSH attraverso il jump server
            jump_transport = jump_ssh.get_transport()
            dest_addr = (self.target_host.get(), 22)
            local_addr = (self.ssh_host.get(), int(self.ssh_port.get()))
            channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr)
            
            # Connessione al target server usando il canale
            target_ssh = paramiko.SSHClient()
            target_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            target_ssh.connect(
                hostname=self.target_host.get(),
                username=self.target_username.get(),
                password=self.target_password.get(),
                sock=channel,
                timeout=10
            )
            
            # Step 3: Verifica la cartella di lavoro
            folder_status = self.check_folder_path(target_ssh)
            
            # Se arriviamo qui, la connessione è riuscita
            messagebox.showinfo(
                "✓ Connessione Accettata",
                f"Connessione SSH a due hop stabilita con successo!\n\n"
                f"Jump Server: {self.ssh_host.get()}:{self.ssh_port.get()}\n"
                f"  └─ Utente: {self.ssh_username.get()}\n"
                f"  └─ Metodo: {'Chiave SSH' if self.use_key.get() else 'Password'}\n\n"
                f"Target Server: {self.target_host.get()}\n"
                f"  └─ Utente: {self.target_username.get()}\n\n"
                f"{folder_status['message']}"
            )
            
            # Se la cartella non esiste ma può essere creata, chiedi all'utente
            if folder_status['status'] == 'not_exists' and folder_status['can_create']:
                create = messagebox.askyesno(
                    "Crea Cartella?",
                    f"La cartella di lavoro non esiste:\n{self.working_folder.get()}\n\n"
                    f"Vuoi crearla ora?"
                )
                
                if create:
                    success, msg = self.create_folder(target_ssh, self.working_folder.get())
                    if success:
                        messagebox.showinfo("Successo", msg)
                    else:
                        messagebox.showerror("Errore", msg)
            
        except paramiko.AuthenticationException as e:
            messagebox.showerror(
                "✗ Connessione Rifiutata",
                f"Autenticazione fallita!\n\n"
                f"Errore: {str(e)}\n\n"
                "Verifica le credenziali (username e password) per entrambi i server."
            )
        except paramiko.SSHException as e:
            messagebox.showerror(
                "✗ Connessione Rifiutata",
                f"Errore SSH:\n{str(e)}\n\n"
                "Verifica i parametri di connessione."
            )
        except TimeoutError:
            messagebox.showerror(
                "✗ Connessione Rifiutata",
                f"Timeout di connessione!\n\n"
                f"Il server non risponde.\n"
                "Verifica che gli host siano corretti e raggiungibili."
            )
        except Exception as e:
            messagebox.showerror(
                "✗ Connessione Rifiutata",
                f"Errore di connessione:\n{str(e)}\n\n"
                "Impossibile stabilire la connessione al server."
            )
        finally:
            if target_ssh:
                try:
                    target_ssh.close()
                except:
                    pass
            if jump_ssh:
                try:
                    jump_ssh.close()
                except:
                    pass
    
    def save_config(self):
        """Salva la configurazione"""
        # Validazione
        if not self.ssh_host.get():
            messagebox.showerror("Errore", "Inserisci l'host del jump server!")
            return
        
        if not self.ssh_username.get():
            messagebox.showerror("Errore", "Inserisci il nome utente per il jump server!")
            return
        
        if not self.target_host.get():
            messagebox.showerror("Errore", "Inserisci l'host del target server!")
            return
        
        if not self.same_credentials.get():
            # Solo se usa credenziali diverse
            if not self.target_username.get():
                messagebox.showerror("Errore", "Inserisci il nome utente per il target server!")
                return
        
        if not self.working_folder.get():
            messagebox.showerror("Errore", "Inserisci la cartella di lavoro!")
            return
        
        try:
            # Crea la configurazione
            config = {
                # Jump Server
                'ssh_host': self.ssh_host.get(),
                'ssh_port': self.ssh_port.get(),
                'ssh_username': self.ssh_username.get(),
                'use_key': self.use_key.get(),
                'ssh_key_path': self.ssh_key_path.get() if self.use_key.get() else '',
                # Target Server
                'target_host': self.target_host.get(),
                'target_username': self.target_username.get(),
                'same_credentials': self.same_credentials.get(),
                # Working folder
                'working_folder': self.working_folder.get()
            }
            
            # Salva il file
            config_file = self.temp_dir / "farm_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo(
                "Successo",
                "Configurazione Farm salvata correttamente!"
            )
            
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror(
                "Errore",
                f"Errore durante il salvataggio della configurazione:\n{str(e)}"
            )
