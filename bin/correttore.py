#!/usr/bin/env python3
"""
Correttore - Launcher principale
================================

Entry point principale per il sistema di correzione.
Avvia l'interfaccia web di default, CLI se richiesta.

Usage:
    python bin/correttore.py                    # Web interface
    python bin/correttore.py --cli              # CLI
    python bin/correttore.py documento.docx     # Correzione diretta
"""

import sys
from pathlib import Path

# Aggiungi src/ al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

def main():
    """Entry point principale"""
    try:
        # Prova nuovo import path
        from correttore.interfaces.cli import main as cli_main
        from correttore.interfaces.web_interface import main as web_main
    except ImportError:
        # Fallback a vecchio import path per compatibilità
        from src.interfaces.cli import main as cli_main
        from src.interfaces.web_interface import main as web_main
    
    # Se non ci sono argomenti, avvia web interface
    if len(sys.argv) == 1:
        print("🌐 Avvio interfaccia web...")
        print("📊 Dashboard disponibile su: http://localhost:5000")
        web_main()
    
    # Se viene passato --cli esplicitamente, avvia la CLI
    elif len(sys.argv) > 1 and sys.argv[1] in ['--cli', '--command', 'cli', 'command']:
        print("💻 Avvio interfaccia CLI...")
        cli_main()
    
    # Se c'è un file come primo argomento, avvia CLI in modalità diretta
    elif len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        print("📝 Avvio correzione diretta...")
        cli_main()
    
    # Altrimenti avvia CLI per gestire gli argomenti
    else:
        print("💻 Avvio interfaccia CLI...")
        cli_main()

if __name__ == "__main__":
    main()
