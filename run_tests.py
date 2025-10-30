#!/usr/bin/env python3
"""
Script per eseguire la suite di test del Correttore Automatico.

Usage:
    python run_tests.py              # Esegue tutti i test
    python run_tests.py unit         # Solo test unitari
    python run_tests.py integration  # Solo test di integrazione
    python run_tests.py performance  # Solo test di performance
    python run_tests.py coverage     # Test con coverage report
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd: list[str]) -> int:
    """Esegue un comando e ritorna il codice di uscita."""
    print(f"\n{'='*60}")
    print(f"Eseguendo: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def main():
    """Funzione principale."""
    
    # Determina quale test eseguire
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    # Comandi base pytest
    base_cmd = ["pytest"]
    
    # Selezione test
    if test_type == "unit":
        cmd = base_cmd + ["tests/unit/", "-m", "unit or not integration and not performance"]
        print("🧪 Eseguendo TEST UNITARI...")
        
    elif test_type == "integration":
        cmd = base_cmd + ["tests/integration/", "-m", "integration"]
        print("🔗 Eseguendo TEST DI INTEGRAZIONE...")
        
    elif test_type == "performance":
        cmd = base_cmd + ["tests/performance/", "-m", "performance"]
        print("⚡ Eseguendo TEST DI PERFORMANCE...")
        
    elif test_type == "coverage":
        cmd = base_cmd + [
            "--cov=correttore",
            "--cov-report=html",
            "--cov-report=term-missing",
            "tests/"
        ]
        print("📊 Eseguendo test con COVERAGE...")
        
    elif test_type == "fast":
        cmd = base_cmd + ["tests/", "-m", "not slow and not api"]
        print("🚀 Eseguendo TEST VELOCI (no API, no slow)...")
        
    elif test_type == "quick":
        cmd = base_cmd + ["tests/unit/", "-x"]  # -x: stop al primo errore
        print("⚡ Eseguendo QUICK TEST (stop al primo errore)...")
        
    elif test_type == "all":
        cmd = base_cmd + ["tests/"]
        print("🎯 Eseguendo TUTTI I TEST...")
        
    else:
        print(f"❌ Tipo di test non riconosciuto: {test_type}")
        print("\nUso:")
        print("  python run_tests.py [unit|integration|performance|coverage|fast|quick|all]")
        return 1
    
    # Esegui i test
    exit_code = run_command(cmd)
    
    # Messaggio finale
    if exit_code == 0:
        print("\n✅ TUTTI I TEST SONO PASSATI!")
        if test_type == "coverage":
            print(f"\n📊 Report coverage disponibile in: htmlcov/index.html")
    else:
        print(f"\n❌ ALCUNI TEST SONO FALLITI (exit code: {exit_code})")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
