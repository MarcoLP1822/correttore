"""
Entry point per esecuzione come modulo: python -m correttore

Usage:
    python -m correttore                  # Avvia interfaccia web (default)
    python -m correttore file.docx        # Correggi file da CLI
    python -m correttore --web            # Avvia interfaccia web esplicita
    python -m correttore --help           # Mostra help CLI
"""

import sys

def main():
    """
    Entry point principale che decide tra web interface e CLI.
    Se non ci sono argomenti o c'è --web, avvia la web interface.
    Altrimenti usa la CLI.
    """
    # Se nessun argomento o --web, avvia web interface
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ['--web', '-w']):
        from correttore.interfaces.web_interface import main as web_main
        web_main()
    else:
        # Altrimenti usa CLI
        from correttore.interfaces.cli import main as cli_main
        cli_main()

if __name__ == '__main__':
    main()
