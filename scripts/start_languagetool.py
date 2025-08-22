#!/usr/bin/env python3
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
    
    lt_dir = Path(r"languagetool\LanguageTool-6.3")
    jar_file = lt_dir / "languagetool-server.jar"
    
    if not jar_file.exists():
        print(f"❌ File JAR non trovato: {jar_file}")
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
            print("\n🛑 Arresto LanguageTool server...")
            process.terminate()
            process.wait()
            print("✅ Server arrestato")
            
    except Exception as e:
        print(f"❌ Errore avvio server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    start_languagetool()
