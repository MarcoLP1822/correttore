#!/usr/bin/env python3
"""
Script di avvio manuale LanguageTool
"""

import sys
from pathlib import Path

# Aggiungi la root del progetto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.languagetool_manager import get_languagetool_manager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("🚀 Avvio LanguageTool...")
    print("=" * 50)
    
    manager = get_languagetool_manager()
    
    # Controlla se già in esecuzione
    if manager.is_server_running():
        print("✅ LanguageTool è già in esecuzione!")
        status = manager.get_status()
        print(f"📍 URL: {status['url']}")
        print(f"🔌 Porta: {status['port']}")
        sys.exit(0)
    
    # Avvia il server
    print("⏳ Avvio del server in corso...")
    if manager.ensure_running():
        print("\n✅ LanguageTool avviato con successo!")
        status = manager.get_status()
        print(f"📍 URL: {status['url']}")
        print(f"🔌 Porta: {status['port']}")
        print("\n💡 Il server rimarrà attivo in background")
        print("   Per fermarlo usa: python stop_languagetool.py")
    else:
        print("\n❌ Impossibile avviare LanguageTool")
        print("   Verifica:")
        print("   1. Java è installato: java -version")
        print("   2. LanguageTool è installato nella cartella languagetool/")
        print("   3. La porta 8081 non è occupata")
        sys.exit(1)
