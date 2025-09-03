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
        
        # Pulisci file zip
        zip_file.unlink()
        
        print("✅ LanguageTool installato con successo!")
        print(f"📁 Directory: {extracted_dir}")
        print("🚀 Per avviare LanguageTool usa l'interfaccia web o CLI del correttore")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante installazione: {e}")
        return False

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
        print("1. Avvia il correttore con: python main.py")
        print("2. LanguageTool verrà avviato automaticamente quando necessario")
    else:
        print("❌ Installazione fallita")
        sys.exit(1)

if __name__ == "__main__":
    main()
