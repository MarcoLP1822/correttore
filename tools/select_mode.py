#!/usr/bin/env python3
"""
Selettore modalità correzione
Permette di scegliere tra modalità normale e storica
"""

import shutil
import os
import sys

def show_modes():
    """Mostra le modalità disponibili"""
    print("📚 MODALITÀ DI CORREZIONE DISPONIBILI")
    print("=" * 40)
    print()
    print("1. 🔧 NORMALE (aggressive/conservative/balanced)")
    print("   • Per documenti moderni")
    print("   • Correzioni complete")
    print("   • Soglie configurabili")
    print()
    print("2. 🏛️  STORICA (historical)")
    print("   • Per libri di storia")
    print("   • Protegge nomi propri storici")
    print("   • Correzioni ultra-conservative")
    print("   • Soglia fissa 90%")
    print()

def apply_normal_mode():
    """Applica modalità normale"""
    if os.path.exists("config_optimized.yaml"):
        shutil.copy("config_optimized.yaml", "config.yaml")
        print("✅ Modalità NORMALE attivata")
        print("   • Modalità: aggressive/conservative/balanced disponibili")
        print("   • Soglie: configurabili dall'interfaccia web")
        return True
    else:
        print("❌ File config_optimized.yaml non trovato!")
        return False

def apply_historical_mode():
    """Applica modalità storica"""
    if os.path.exists("config_historical.yaml"):
        shutil.copy("config_historical.yaml", "config.yaml")
        shutil.copy("glossario_storico.txt", "glossario.txt")
        print("✅ Modalità STORICA attivata")
        print("   • Modalità: historical (fissa)")
        print("   • Soglia: 90% (fissa)")
        print("   • Glossario: nomi storici protetti")
        return True
    else:
        print("❌ File config_historical.yaml non trovato!")
        return False

def main():
    """Menu principale"""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "normal" or mode == "normale":
            apply_normal_mode()
            return
        elif mode == "historical" or mode == "storico" or mode == "storia":
            apply_historical_mode()
            return
    
    show_modes()
    
    while True:
        try:
            choice = input("\nScegli modalità (1=normale, 2=storica, q=quit): ").strip().lower()
            
            if choice == 'q' or choice == 'quit':
                print("👋 Uscita")
                break
            elif choice == '1' or choice == 'normale' or choice == 'normal':
                if apply_normal_mode():
                    break
            elif choice == '2' or choice == 'storica' or choice == 'historical':
                if apply_historical_mode():
                    break
            else:
                print("❌ Scelta non valida")
                
        except KeyboardInterrupt:
            print("\n👋 Uscita")
            break

if __name__ == "__main__":
    main()
