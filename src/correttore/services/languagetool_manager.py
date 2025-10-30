#!/usr/bin/env python3
"""
Gestore automatico LanguageTool per applicazione enterprise
Avvia, controlla e gestisce automaticamente il server LanguageTool
"""

import subprocess
import requests
import time
import os
import signal
import logging
from pathlib import Path
from typing import Optional
import threading
import atexit

class LanguageToolManager:
    """Gestore automatico per LanguageTool server"""
    
    def __init__(self, port: int = 8081, timeout: int = 60):
        self.port = port
        self.timeout = timeout
        self.server_process: Optional[subprocess.Popen] = None
        self.server_url = f"http://localhost:{port}"
        self.lt_dir = None
        self.logger = logging.getLogger(__name__)
        
        # Registra cleanup all'uscita
        atexit.register(self.stop_server)
    
    def find_languagetool_installation(self) -> Optional[Path]:
        """Trova l'installazione di LanguageTool"""
        possible_locations = [
            Path("languagetool"),
            Path("LanguageTool-6.3"),
            Path("languagetool/LanguageTool-6.3"),
            Path.home() / "languagetool",
            Path("C:/languagetool"),
            Path("C:/Program Files/LanguageTool"),
        ]
        
        for location in possible_locations:
            if location.exists():
                # Cerca il jar file
                jar_files = list(location.glob("**/*languagetool-server*.jar"))
                if jar_files:
                    self.logger.info(f"✅ LanguageTool trovato in: {location}")
                    return location
        
        return None
    
    def is_server_running(self) -> bool:
        """Controlla se il server LanguageTool è già in esecuzione"""
        try:
            response = requests.get(f"{self.server_url}/v2/languages", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def start_server(self) -> bool:
        """Avvia il server LanguageTool"""
        if self.is_server_running():
            self.logger.info(f"✅ LanguageTool già in esecuzione su {self.server_url}")
            return True
        
        # Trova l'installazione
        self.lt_dir = self.find_languagetool_installation()
        if not self.lt_dir:
            self.logger.error("❌ LanguageTool non trovato. Installo automaticamente...")
            return self.auto_install_and_start()
        
        # Trova il jar file
        jar_files = list(self.lt_dir.glob("**/*languagetool-server*.jar"))
        if not jar_files:
            self.logger.error(f"❌ File jar non trovato in {self.lt_dir}")
            return False
        
        jar_file = jar_files[0]
        # La working directory deve essere quella del jar file per evitare i warning
        jar_dir = jar_file.parent
        
        try:
            # Su Windows, usa un batch file wrapper per evitare problemi di processo
            if os.name == 'nt':
                # Crea un batch file temporaneo
                project_root = Path(__file__).parent.parent.parent.parent
                batch_file = project_root / "start_lt_temp.bat"
                
                with open(batch_file, 'w') as f:
                    f.write(f'@echo off\n')
                    f.write(f'cd /d "{jar_dir}"\n')
                    f.write(f'java -cp "{jar_file.name}" org.languagetool.server.HTTPServer --port {self.port} --allow-origin "*" --public\n')
                
                cmd = [str(batch_file)]
            else:
                # Unix/Linux: comando diretto
                cmd = [
                    "java",
                    "-cp", str(jar_file),
                    "org.languagetool.server.HTTPServer",
                    "--port", str(self.port),
                    "--allow-origin", "*",
                    "--public"
                ]
            
            self.logger.info(f"🚀 Avvio LanguageTool server...")
            
            # Avvia il processo senza finestra visibile
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            self.server_process = subprocess.Popen(
                cmd,
                cwd=jar_dir if os.name != 'nt' else None,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo
            )
            
            # Aspetta che il server sia pronto
            return self.wait_for_server()
            
        except Exception as e:
            self.logger.error(f"❌ Errore avvio LanguageTool: {e}")
            return False
    
    def wait_for_server(self) -> bool:
        """Aspetta che il server sia pronto"""
        self.logger.info(f"⏳ Attendo che LanguageTool sia pronto su {self.server_url}...")
        
        for i in range(self.timeout):
            try:
                if self.is_server_running():
                    self.logger.info(f"✅ LanguageTool pronto dopo {i+1} secondi")
                    return True
                time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("❌ Avvio interrotto dall'utente")
                self.stop_server()
                return False
        
        self.logger.error(f"❌ Timeout: LanguageTool non è diventato disponibile in {self.timeout} secondi")
        self.stop_server()
        return False
    
    def auto_install_and_start(self) -> bool:
        """Installa automaticamente LanguageTool e lo avvia"""
        try:
            self.logger.info("📥 Installazione automatica LanguageTool...")
            
            # Usa lo script di installazione esistente
            if os.path.exists("install_languagetool.py"):
                result = subprocess.run(["python", "install_languagetool.py"], 
                                      capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    self.logger.info("✅ LanguageTool installato automaticamente")
                    # Riprova a trovare l'installazione
                    self.lt_dir = self.find_languagetool_installation()
                    if self.lt_dir:
                        return self.start_server()
                else:
                    self.logger.error(f"❌ Errore installazione: {result.stderr}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Errore installazione automatica: {e}")
            return False
    
    def stop_server(self):
        """Ferma il server LanguageTool"""
        if self.server_process:
            try:
                self.logger.info("🛑 Arresto LanguageTool server...")
                
                if os.name == 'nt':  # Windows
                    self.server_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:  # Unix/Linux
                    self.server_process.terminate()
                
                # Aspetta che si chiuda
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.server_process.kill()
                
                self.server_process = None
                self.logger.info("✅ LanguageTool server arrestato")
                
            except Exception as e:
                self.logger.error(f"❌ Errore arresto server: {e}")
    
    def ensure_running(self) -> bool:
        """Assicura che il server sia in esecuzione"""
        if not self.is_server_running():
            return self.start_server()
        return True
    
    def get_status(self) -> dict:
        """Restituisce lo stato del server"""
        running = self.is_server_running()
        return {
            "running": running,
            "url": self.server_url,
            "port": self.port,
            "installation_found": self.lt_dir is not None,
            "process_active": self.server_process is not None and self.server_process.poll() is None
        }

# Singleton instance
_lt_manager = None

def get_languagetool_manager() -> LanguageToolManager:
    """Restituisce l'istanza singleton del manager"""
    global _lt_manager
    if _lt_manager is None:
        _lt_manager = LanguageToolManager()
    return _lt_manager

def start_languagetool_automatically() -> bool:
    """Avvia LanguageTool automaticamente"""
    manager = get_languagetool_manager()
    return manager.ensure_running()

def stop_languagetool():
    """Ferma LanguageTool"""
    manager = get_languagetool_manager()
    manager.stop_server()

if __name__ == "__main__":
    # Test standalone
    logging.basicConfig(level=logging.INFO)
    
    manager = LanguageToolManager()
    print("🧪 Test LanguageTool Manager")
    
    if manager.start_server():
        print("✅ Server avviato con successo")
        status = manager.get_status()
        print(f"Status: {status}")
        
        input("Premi Enter per fermare il server...")
        manager.stop_server()
    else:
        print("❌ Impossibile avviare il server")
