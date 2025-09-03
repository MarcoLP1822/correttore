#!/usr/bin/env python3
"""
LanguageTool Manager - Gestione unificata di LanguageTool
Sostituisce simple_lt_starter.py e languagetool_launcher.py
"""

import subprocess
import requests
import time
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def is_languagetool_running(port=8081):
    """Controlla se LanguageTool HTTP server è in esecuzione"""
    try:
        response = requests.get(f"http://localhost:{port}/v2/languages", timeout=2)
        return response.status_code == 200
    except:
        return False

def check_languagetool_python():
    """Verifica se LanguageTool Python è disponibile"""
    try:
        import language_tool_python
        return True
    except ImportError:
        return False

def start_languagetool_simple():
    """
    Avvia o verifica LanguageTool usando il metodo più semplice disponibile.
    Priorità: 1) Server HTTP se già attivo, 2) Libreria Python
    """
    try:
        print("🔍 Verifica disponibilità LanguageTool...")
        
        # Prima prova con server HTTP se già attivo
        if is_languagetool_running():
            print("✅ LanguageTool HTTP server già disponibile")
            return True
        
        # Test con installazione automatica Python
        if check_languagetool_python():
            print("🔄 Inizializzazione LanguageTool locale...")
            import language_tool_python as lt
            
            # Test funzionamento veloce
            tool = lt.LanguageTool("it")
            test_result = tool.check("Test.")
            tool.close()
            
            print("✅ LanguageTool locale funzionante")
            print("   Modalità: Installazione automatica language-tool-python")
            return True
        
        print("❌ LanguageTool non disponibile")
        print("💡 Prova: pip install --upgrade language-tool-python")
        return False
        
    except Exception as e:
        logger.error(f"Errore LanguageTool: {e}")
        print(f"❌ Errore LanguageTool: {e}")
        return False

def ensure_languagetool_running(port=8081) -> bool:
    """Assicura che LanguageTool sia attivo (alias per compatibilità)"""
    return start_languagetool_simple()

# Compatibilità con i vecchi import
check_languagetool_server = is_languagetool_running

def start_languagetool_fallback():
    """Fallback usando libreria Python (alias per compatibilità)"""
    return check_languagetool_python()

if __name__ == "__main__":
    success = start_languagetool_simple()
    exit(0 if success else 1)
