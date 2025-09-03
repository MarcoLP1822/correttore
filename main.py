#!/usr/bin/env python3
"""
Correttore di Testi Italiani - Enterprise Edition
Launcher principale con interfaccia web integrata

Comportamento predefinito: avvia l'interfaccia web su http://localhost:5000
Per usare la CLI: python main.py --cli
"""

import sys
import os

# Aggiungi la root del progetto al path per permettere import relativi
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    """Entry point principale - gestisce CLI e web interface"""
    
    # Se non ci sono argomenti, avvia web interface
    if len(sys.argv) == 1:
        print("🌐 Avvio interfaccia web...")
        print("📊 Dashboard disponibile su: http://localhost:5000")
        try:
            from src.interfaces.web_interface import main as web_main
            web_main()
        except ImportError as e:
            print(f"❌ Errore importando web interface: {e}")
            print("💡 Prova: python -m src.interfaces.web_interface")
            return 1
    
    # Se viene passato --cli esplicitamente, avvia la CLI
    elif len(sys.argv) > 1 and sys.argv[1] in ['--cli', '--command', 'cli', 'command']:
        print("💻 Avvio interfaccia CLI...")
        from src.interfaces.cli import main as cli_main
        cli_main()
    
    # Se c'è un file come primo argomento, avvia CLI in modalità diretta
    elif len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        print("� Avvio correzione diretta...")
        from src.interfaces.cli import main as cli_main
        cli_main()
    
    # Altrimenti avvia CLI per gestire gli argomenti
    else:
        print("💻 Avvio interfaccia CLI...")
        from src.interfaces.cli import main as cli_main
        cli_main()

if __name__ == "__main__":
    main()
