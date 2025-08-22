#!/usr/bin/env python3
"""
Script per configurare il sistema in modalità "Libri di Storia"
Ottimizzato per documenti storici con protezione nomi propri
"""

import shutil
import os
from pathlib import Path

def setup_historical_mode():
    """Configura il sistema per la modalità Libri di Storia"""
    
    print("🏛️  Configurazione Modalità LIBRI DI STORIA")
    print("=" * 50)
    
    # 1. Backup configurazione corrente
    if os.path.exists("config.yaml"):
        backup_name = "config_backup_before_historical.yaml"
        shutil.copy("config.yaml", backup_name)
        print(f"✅ Backup creato: {backup_name}")
    
    # 2. Applica configurazione storica
    if os.path.exists("config_historical.yaml"):
        shutil.copy("config_historical.yaml", "config.yaml")
        print("✅ Configurazione storica applicata")
    else:
        print("❌ File config_historical.yaml non trovato!")
        return False
    
    # 3. Aggiorna glossario
    if os.path.exists("glossario_storico.txt"):
        shutil.copy("glossario_storico.txt", "glossario.txt")
        print("✅ Glossario storico applicato")
    else:
        print("❌ File glossario_storico.txt non trovato!")
        return False
    
    print("\n🎉 Modalità LIBRI DI STORIA configurata!")
    print("\n📋 Caratteristiche attive:")
    print("   • Modalità: HISTORICAL")
    print("   • Soglia qualità: 90% (molto sicura)")
    print("   • Protezione nomi propri storici")
    print("   • Batch size ridotto (15)")
    print("   • Temperature bassa (0.1)")
    print("   • Glossario nomi storici esteso")
    
    print("\n🚀 Per avviare la correzione:")
    print("   python web_interface.py")
    print("\n⚠️  IMPORTANTE:")
    print("   - Usa questa modalità SOLO per libri di storia")
    print("   - I nomi nel glossario sono protetti dalle correzioni")
    print("   - Le correzioni saranno molto conservative")
    
    return True

def restore_previous_config():
    """Ripristina la configurazione precedente"""
    backup_file = "config_backup_before_historical.yaml"
    if os.path.exists(backup_file):
        shutil.copy(backup_file, "config.yaml")
        print("✅ Configurazione precedente ripristinata")
        return True
    else:
        print("❌ Nessun backup trovato!")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--restore":
        restore_previous_config()
    else:
        setup_historical_mode()
