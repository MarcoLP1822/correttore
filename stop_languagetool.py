#!/usr/bin/env python3
"""
Script per fermare LanguageTool
"""

import sys
from pathlib import Path

# Aggiungi la root del progetto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from correttore.services.languagetool_manager import get_languagetool_manager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("🛑 Arresto LanguageTool...")
    print("=" * 50)
    
    manager = get_languagetool_manager()
    
    if not manager.is_server_running():
        print("⚠️  LanguageTool non è in esecuzione")
        sys.exit(0)
    
    manager.stop_server()
    print("✅ LanguageTool arrestato con successo")
