"""
Script helper per classificare manualmente le parole del NVdB.
Permette di aggiornare i livelli delle parole nel vocabolario.
"""

import json
from pathlib import Path

def load_nvdb():
    """Carica il vocabolario completo."""
    path = Path("data/vocabolario/nvdb_completo.json")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_nvdb(nvdb_data):
    """Salva il vocabolario aggiornato."""
    path = Path("data/vocabolario/nvdb_completo.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(nvdb_data, f, ensure_ascii=False, indent=2)

def import_classification_file(file_path):
    """
    Importa classificazioni da file di testo.
    Formato atteso: parola|livello (una per riga)
    """
    nvdb = load_nvdb()
    updated = 0
    errors = []
    
    valid_levels = ['fondamentale', 'alto_uso', 'alta_disponibilita']
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Salta commenti e linee vuote
            if not line or line.startswith('#'):
                continue
            
            # Parse formato parola|livello
            if '|' not in line:
                errors.append(f"Riga {line_num}: formato non valido (manca |)")
                continue
            
            parts = line.split('|')
            if len(parts) != 2:
                errors.append(f"Riga {line_num}: formato non valido")
                continue
            
            word, level = parts[0].strip(), parts[1].strip()
            
            # Salta se livello vuoto
            if not level:
                continue
            
            # Verifica livello valido
            if level not in valid_levels:
                errors.append(f"Riga {line_num}: livello '{level}' non valido per '{word}'")
                continue
            
            # Verifica che la parola esista
            if word not in nvdb['vocabolario']:
                errors.append(f"Riga {line_num}: parola '{word}' non trovata nel vocabolario")
                continue
            
            # Aggiorna
            nvdb['vocabolario'][word]['livello'] = level
            updated += 1
    
    # Aggiorna statistiche metadata
    update_statistics(nvdb)
    
    # Salva
    save_nvdb(nvdb)
    
    return updated, errors

def update_statistics(nvdb):
    """Aggiorna le statistiche nel metadata."""
    levels_count = {
        'fondamentale': 0,
        'alto_uso': 0,
        'alta_disponibilita': 0,
        'non_classificato': 0
    }
    
    for word_data in nvdb['vocabolario'].values():
        level = word_data['livello']
        if level:
            levels_count[level] += 1
        else:
            levels_count['non_classificato'] += 1
    
    nvdb['metadata']['livelli']['fondamentale']['count'] = levels_count['fondamentale']
    nvdb['metadata']['livelli']['alto_uso']['count'] = levels_count['alto_uso']
    nvdb['metadata']['livelli']['alta_disponibilita']['count'] = levels_count['alta_disponibilita']
    nvdb['metadata']['livelli']['non_classificato']['count'] = levels_count['non_classificato']

def classify_word(word, level, note=""):
    """Classifica una singola parola."""
    nvdb = load_nvdb()
    
    valid_levels = ['fondamentale', 'alto_uso', 'alta_disponibilita', None]
    
    if level not in valid_levels:
        print(f"❌ Livello non valido: {level}")
        print(f"   Livelli validi: fondamentale, alto_uso, alta_disponibilita")
        return False
    
    if word not in nvdb['vocabolario']:
        print(f"❌ Parola '{word}' non trovata nel vocabolario")
        return False
    
    nvdb['vocabolario'][word]['livello'] = level
    if note:
        nvdb['vocabolario'][word]['note'] = note
    
    update_statistics(nvdb)
    save_nvdb(nvdb)
    
    print(f"✓ '{word}' classificata come: {level or 'non classificato'}")
    return True

def show_statistics():
    """Mostra statistiche di classificazione."""
    nvdb = load_nvdb()
    
    print("\n" + "=" * 60)
    print("STATISTICHE VOCABOLARIO")
    print("=" * 60)
    print(f"Totale parole: {nvdb['metadata']['totale_parole']}")
    print()
    
    for level_key, level_data in nvdb['metadata']['livelli'].items():
        count = level_data['count']
        desc = level_data['descrizione']
        percentage = (count / nvdb['metadata']['totale_parole'] * 100) if nvdb['metadata']['totale_parole'] > 0 else 0
        print(f"{level_key:20s}: {count:5d} ({percentage:5.1f}%) - {desc}")

def export_by_level(output_dir="data/vocabolario/levels"):
    """Esporta parole separate per livello."""
    nvdb = load_nvdb()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    levels = {
        'fondamentale': [],
        'alto_uso': [],
        'alta_disponibilita': [],
        'non_classificato': []
    }
    
    for word, data in nvdb['vocabolario'].items():
        level = data['livello'] or 'non_classificato'
        levels[level].append(word)
    
    for level, words in levels.items():
        if words:
            file_path = output_path / f"{level}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(sorted(words)))
            print(f"✓ Esportato: {file_path} ({len(words)} parole)")

def interactive_classify():
    """Modalità interattiva per classificare parole."""
    nvdb = load_nvdb()
    
    print("\n" + "=" * 60)
    print("CLASSIFICAZIONE INTERATTIVA")
    print("=" * 60)
    print("Livelli: 1=fondamentale, 2=alto_uso, 3=alta_disponibilita, 0=annulla")
    print("Comandi: 'q' per uscire, 's' per statistiche")
    print()
    
    # Filtra solo parole non classificate
    unclassified = [(w, d) for w, d in nvdb['vocabolario'].items() if not d['livello']]
    
    if not unclassified:
        print("✓ Tutte le parole sono già classificate!")
        return
    
    print(f"Parole da classificare: {len(unclassified)}\n")
    
    levels_map = {
        '1': 'fondamentale',
        '2': 'alto_uso',
        '3': 'alta_disponibilita',
        '0': None
    }
    
    for i, (word, data) in enumerate(unclassified, 1):
        print(f"[{i}/{len(unclassified)}] Parola: {word}")
        choice = input("Livello (1/2/3/0/q/s): ").strip().lower()
        
        if choice == 'q':
            print("\nSalvataggio e uscita...")
            break
        elif choice == 's':
            show_statistics()
            continue
        elif choice in levels_map:
            level = levels_map[choice]
            if level:
                classify_word(word, level)
        else:
            print("⚠ Scelta non valida, parola saltata")
        
        print()

def main():
    import sys
    
    if len(sys.argv) == 1:
        print("\n" + "=" * 60)
        print("CLASSIFICAZIONE NVDB - Helper")
        print("=" * 60)
        print("\nComandi disponibili:")
        print("  python tools/classify_nvdb.py stats")
        print("      → Mostra statistiche classificazione")
        print()
        print("  python tools/classify_nvdb.py interactive")
        print("      → Modalità interattiva per classificare parole")
        print()
        print("  python tools/classify_nvdb.py import <file>")
        print("      → Importa classificazioni da file (formato: parola|livello)")
        print()
        print("  python tools/classify_nvdb.py export")
        print("      → Esporta parole separate per livello")
        print()
        print("  python tools/classify_nvdb.py classify <parola> <livello>")
        print("      → Classifica una singola parola")
        print()
        return
    
    command = sys.argv[1]
    
    if command == 'stats':
        show_statistics()
    
    elif command == 'interactive':
        interactive_classify()
    
    elif command == 'import' and len(sys.argv) > 2:
        file_path = sys.argv[2]
        print(f"Importazione da: {file_path}")
        updated, errors = import_classification_file(file_path)
        print(f"\n✓ Parole aggiornate: {updated}")
        if errors:
            print(f"\n⚠ Errori ({len(errors)}):")
            for error in errors[:10]:  # Mostra primi 10
                print(f"  {error}")
        show_statistics()
    
    elif command == 'export':
        export_by_level()
        print("\n✓ Esportazione completata")
    
    elif command == 'classify' and len(sys.argv) > 3:
        word = sys.argv[2]
        level = sys.argv[3]
        classify_word(word, level)
    
    else:
        print(f"❌ Comando non riconosciuto: {command}")
        print("Usa 'python tools/classify_nvdb.py' per vedere i comandi disponibili")

if __name__ == "__main__":
    main()
