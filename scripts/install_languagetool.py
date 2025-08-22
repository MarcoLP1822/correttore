#!/usr/bin/env python3
"""
Script per installare e configurare LanguageTool automaticamente
"""

import os
import sys
import requests
import zipfile
import subprocess
from pathlib import Path
import shutil

def install_languagetool():
    """Installa LanguageTool automaticamente"""
    
    print("🔧 Installazione LanguageTool...")
    
    # Directory di installazione
    install_dir = Path("languagetool")
    install_dir.mkdir(exist_ok=True)
    
    # URL di download (versione stabile)
    lt_version = "6.3"
    download_url = f"https://languagetool.org/download/LanguageTool-{lt_version}.zip"
    zip_file = install_dir / f"LanguageTool-{lt_version}.zip"
    
    try:
        # Download
        print(f"📥 Scaricando LanguageTool {lt_version}...")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        with open(zip_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("✅ Download completato")
        
        # Estrazione
        print("📦 Estrazione in corso...")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(install_dir)
        
        # Trova la directory estratta
        extracted_dir = None
        for item in install_dir.iterdir():
            if item.is_dir() and item.name.startswith("LanguageTool"):
                extracted_dir = item
                break
        
        if not extracted_dir:
            raise Exception("Directory LanguageTool non trovata dopo estrazione")
        
        # Crea script di avvio
        create_launcher_script(extracted_dir)
        
        # Pulisci file zip
        zip_file.unlink()
        
        print("✅ LanguageTool installato con successo!")
        print(f"📁 Directory: {extracted_dir}")
        print("🚀 Per avviare: python start_languagetool.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante installazione: {e}")
        return False

def create_launcher_script(lt_dir):
    """Crea script per avviare LanguageTool"""
    
    launcher_content = f'''#!/usr/bin/env python3
"""
Script per avviare LanguageTool server
"""

import subprocess
import sys
from pathlib import Path
import time
import requests

def start_languagetool():
    """Avvia LanguageTool server"""
    
    lt_dir = Path(r"{lt_dir}")
    jar_file = lt_dir / "languagetool-server.jar"
    
    if not jar_file.exists():
        print(f"❌ File JAR non trovato: {{jar_file}}")
        return False
    
    print("🚀 Avvio LanguageTool server...")
    print("   Porta: 8081")
    print("   URL: http://localhost:8081")
    print("   Premi Ctrl+C per fermare")
    
    try:
        # Avvia il server
        cmd = [
            "java", "-cp", str(jar_file),
            "org.languagetool.server.HTTPServer",
            "--port", "8081",
            "--allow-origin", "*",
            "--languageModel", str(lt_dir / "org")
        ]
        
        process = subprocess.Popen(
            cmd,
            cwd=str(lt_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Attendi avvio
        time.sleep(3)
        
        # Test connessione
        try:
            response = requests.get("http://localhost:8081/v2/check", timeout=5)
            print("✅ LanguageTool server avviato correttamente!")
        except:
            print("⚠️  Server avviato, in attesa di essere pronto...")
        
        # Mantieni il server in esecuzione
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\\n🛑 Arresto LanguageTool server...")
            process.terminate()
            process.wait()
            print("✅ Server arrestato")
            
    except Exception as e:
        print(f"❌ Errore avvio server: {{e}}")
        return False
    
    return True

if __name__ == "__main__":
    start_languagetool()
'''
    
    script_path = Path("start_languagetool.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(launcher_content)
    
    print(f"📝 Script di avvio creato: {script_path}")

def check_java():
    """Verifica se Java è installato"""
    try:
        result = subprocess.run(["java", "-version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Java trovato")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Java non trovato!")
    print("   Installa Java 8+ da: https://www.oracle.com/java/technologies/downloads/")
    return False

def main():
    """Funzione principale"""
    print("🔧 Setup LanguageTool per Correttore")
    print("=" * 40)
    
    # Verifica Java
    if not check_java():
        sys.exit(1)
    
    # Installa LanguageTool
    if install_languagetool():
        print("\\n🎉 Installazione completata!")
        print("\\nProssimi passi:")
        print("1. Avvia LanguageTool: python start_languagetool.py")
        print("2. In un altro terminale, avvia il correttore: python web_interface.py")
    else:
        print("❌ Installazione fallita")
        sys.exit(1)

if __name__ == "__main__":
    main()
