#!/usr/bin/env python3
"""
Utility per avviare automaticamente LanguageTool server
Semplifica l'utilizzo del correttore gestendo le dipendenze automaticamente
"""

import subprocess
import time
import sys
import requests
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def check_languagetool_server(host="localhost", port=8081) -> bool:
    """Verifica se LanguageTool server è attivo"""
    try:
        response = requests.get(f"http://{host}:{port}/v2/languages", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def download_languagetool():
    """Scarica LanguageTool se non presente"""
    logger.info("🔄 LanguageTool non trovato. Scaricamento in corso...")
    
    # Per ora, indica dove scaricare manualmente
    print("""
❌ LanguageTool non disponibile

📥 Download manuale richiesto:
   1. Vai su: https://languagetool.org/download/
   2. Scarica "LanguageTool Stand-alone for Desktop"
   3. Estrai in una cartella (es: C:\\languagetool\\)
   4. Riavvia il correttore

💡 Alternativa: installa via Python
   pip install --upgrade language-tool-python
   
🚀 Avvio automatico server:
   java -cp "*.jar" org.languagetool.server.HTTPServer --port 8081 --allow-origin "*"
""")
    return False

def start_languagetool_server(port=8081):
    """Avvia LanguageTool server automaticamente"""
    logger.info(f"🚀 Avvio LanguageTool server su porta {port}...")
    
    # Cerca LanguageTool in posizioni comuni
    possible_paths = [
        "languagetool-server.jar",
        "languagetool/languagetool-server.jar", 
        "C:/languagetool/languagetool-server.jar",
        "/usr/share/languagetool/languagetool-server.jar",
        "/opt/languagetool/languagetool-server.jar"
    ]
    
    jar_path = None
    for path in possible_paths:
        if Path(path).exists():
            jar_path = path
            break
    
    if not jar_path:
        return download_languagetool()
    
    try:
        # Avvia server in background
        cmd = [
            "java", "-cp", jar_path,
            "org.languagetool.server.HTTPServer",
            "--port", str(port),
            "--allow-origin", "*"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        
        # Aspetta che il server si avvii
        for i in range(30):  # Aspetta fino a 30 secondi
            if check_languagetool_server(port=port):
                logger.info(f"✅ LanguageTool server avviato su porta {port}")
                return True
            time.sleep(1)
        
        logger.error("❌ Timeout avvio LanguageTool server")
        return False
        
    except Exception as e:
        logger.error(f"❌ Errore avvio LanguageTool: {str(e)}")
        return False

def ensure_languagetool_running(port=8081) -> bool:
    """
    Assicura che LanguageTool sia disponibile.
    Prima prova server HTTP, poi fallback a libreria Python locale.
    """
    # Prova server HTTP
    if check_languagetool_server(port=port):
        logger.info("✅ LanguageTool server HTTP già attivo")
        return True
    
    # Prova con libreria Python (fallback automatico)
    try:
        from simple_lt_starter import start_languagetool_simple
        if start_languagetool_simple():
            logger.info("✅ LanguageTool disponibile tramite libreria Python")
            return True
    except Exception as e:
        logger.debug(f"Fallback libreria Python fallito: {e}")
    
    # Ultimo tentativo: avvio server HTTP tradizionale  
    logger.info("⚠️  Tentativo avvio server HTTP...")
    return start_languagetool_server(port)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if ensure_languagetool_running():
        print("✅ LanguageTool server operativo")
    else:
        print("❌ Impossibile avviare LanguageTool server")
        sys.exit(1)
