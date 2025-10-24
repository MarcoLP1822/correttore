#!/usr/bin/env python3
"""
Analyze Readability - Tool per analisi leggibilità
=================================================

Analizza la leggibilità di documenti usando l'indice Gulpease.

Usage:
    python bin/analyze.py documento.docx
    python bin/analyze.py testo.txt
    python bin/analyze.py documento.docx --export report.txt
"""

import sys
from pathlib import Path

# Aggiungi src/ al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

def main():
    """Entry point per analisi leggibilità"""
    try:
        from correttore.utils.readability import main_cli
    except ImportError:
        # Fallback
        from src.utils.readability import main_cli
    
    main_cli()

if __name__ == "__main__":
    main()
