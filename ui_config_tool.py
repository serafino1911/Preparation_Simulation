"""
UI Tool per la configurazione delle procedure di simulazione
Autore: GitHub Copilot
Data: 2025-12-30
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from pathlib import Path

Required_FOLDERS = ["Outputs", "temp_config"]

class ConfiguratorApp:
    """Applicazione principale per la configurazione delle simulazioni"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Configuratore Simulazioni - PM_TEN")
        self.root.geometry("400x300")
        
        # Directory per i file temporanei
        self.temp_dir = Path("temp_config")
        self.temp_dir.mkdir(exist_ok=True)
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
        
        # Bottone Definisci Dominio
        define_domain_btn = ttk.Button(
            main_frame,
            text="Definisci Dominio",
            command=self.open_domain_window,
            width=30
        )
        define_domain_btn.grid(row=1, column=0, pady=10)
        
        # Bottone Orografia e Uso Terreno
        orography_btn = ttk.Button(
            main_frame,
            text="Orografia e Uso Terreno",
            command=self.open_orography_window,
            width=30
        )
        orography_btn.grid(row=2, column=0, pady=10)

        # Bottone Esci
        exit_btn = ttk.Button(
            main_frame,
            text="Esci",
            command=self.root.quit,
            width=30
        )
        exit_btn.grid(row=3, column=0, pady=10)
        
        # Configura il grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
    
    def open_domain_window(self):
        """Apre la finestra per definire il dominio geografico"""
        from domain_window import DomainWindow
        DomainWindow(self.root, self.temp_dir)
    
    def open_orography_window(self):
        """Apre la finestra per orografia e uso terreno"""
        from orography_window import OrographyWindow
        OrographyWindow(self.root, self.temp_dir)


def main():
    """Funzione principale"""
    root = tk.Tk()
    app = ConfiguratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
