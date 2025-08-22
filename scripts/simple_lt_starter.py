#!/usr/bin/env python3
"""
Auto-starter semplice per LanguageTool
Avvia LanguageTool solo quando necessario, senza timeout complessi
"""

import subprocess
import requests
import time
import os
from pathlib import Path

def is_languagetool_running(port=8081):
    """Controlla velocemente se LanguageTool è in esecuzione"""
    try:
        response = requests.get(f"http://localhost:{port}/v2/languages", timeout=2)
        return response.status_code == 200
    except:
        return False

def find_languagetool_jar():
    """Trova il jar di LanguageTool"""
    possible_locations = [
        Path("languagetool"),
        Path("LanguageTool-6.3"),
        Path("languagetool/LanguageTool-6.3"),
        Path("languagetool/LanguageTool-6.4"),
        Path("C:/LanguageTool-6.3"),
        Path("C:/LanguageTool-6.4"),
    ]
    
    for location in possible_locations:
        if location.exists():
            jar_files = list(location.glob("**/*languagetool-server*.jar"))
            if jar_files:
                return jar_files[0], location
    return None, None

def start_languagetool_simple():
    """
    Verifica che LanguageTool sia disponibile tramite libreria Python.
    Non avvia più server HTTP (che ha problemi), usa fallback automatico.
    """
    try:
        # Test che LanguageTool funzioni tramite libreria Python
        import language_tool_python as lt
        
        print("🔍 Verifica disponibilità LanguageTool...")
        
        # Prima prova con server HTTP se già attivo
        try:
            import requests
            response = requests.get("http://localhost:8081/v2/languages", timeout=2)
            if response.status_code == 200:
                print("✅ LanguageTool HTTP server già disponibile")
                return True
        except:
            pass
        
        # Test con installazione automatica
        print("🔄 Inizializzazione LanguageTool locale...")
        tool = lt.LanguageTool("it")
        
        # Test funzionamento
        test_result = tool.check("Questo è un test.")
        tool.close()
        
        print("✅ LanguageTool locale funzionante")
        print("   Modalità: Installazione automatica language-tool-python")
        return True
        
    except Exception as e:
        print(f"❌ Errore LanguageTool: {e}")
        print("💡 Prova: pip install --upgrade language-tool-python")
        return False

if __name__ == "__main__":
    start_languagetool_simple()
