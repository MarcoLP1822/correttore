"""
Script per estrarre il Nuovo Vocabolario di Base (NVdB) dal PDF.
Crea un file JSON con struttura pronta per la classificazione futura.
"""

import PyPDF2
import re
import json
from pathlib import Path

def extract_words_from_pdf(pdf_path):
    """Estrae tutte le parole dal PDF del NVdB."""
    print(f"Apertura PDF: {pdf_path}")
    
    try:
        import pdfplumber
        use_pdfplumber = True
    except ImportError:
        use_pdfplumber = False
        print("⚠ pdfplumber non disponibile, uso PyPDF2 (meno accurato)")
    
    if use_pdfplumber:
        pdf = pdfplumber.open(pdf_path)
        total_pages = len(pdf.pages)
        print(f"Pagine totali: {total_pages}")
        
        all_text = ""
        for i, page in enumerate(pdf.pages, 1):
            print(f"Elaborazione pagina {i}/{total_pages}...", end="\r")
            all_text += " " + page.extract_text()
        
        pdf.close()
    else:
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(reader.pages)
            print(f"Pagine totali: {total_pages}")
            
            all_text = ""
            for i, page in enumerate(reader.pages, 1):
                print(f"Elaborazione pagina {i}/{total_pages}...", end="\r")
                all_text += " " + page.extract_text()
    
    print(f"\nEstrazione testo completata")
    
    # Pattern migliorato: cerca parole seguite da indicatori grammaticali
    # Formato tipico: "parola v.tr." oppure "parola s.m." oppure "parola agg."
    # Questo cattura i lemmi reali del vocabolario
    pattern = r'\b([a-zàèéìòù]+(?:\'[a-zàèéìòù]+)?)\s+(?:v\.|s\.|agg|avv|prep|pron|art|cong|inter|p\.)'
    lemma_matches = re.findall(pattern, all_text.lower())
    
    # Aggiungi anche parole seguite da virgola o standalone
    # Pattern alternativo per catturare più parole
    pattern2 = r'\b([a-zàèéìòù]{3,}(?:\'[a-zàèéìòù]+)?)\b'
    all_words = re.findall(pattern2, all_text.lower())
    
    # Combina i lemmi trovati con pattern grammaticale + parole comuni
    words_set = set(lemma_matches) | set(all_words)
    
    # Filtra parole spurie (header, numeri, abbreviazioni, ecc.)
    stop_words = {
        # Abbreviazioni grammaticali
        'agg', 'avv', 'intr', 'prep', 'pres', 'pass', 'pers', 'inter', 'poss',
        'inv', 'pl', 'plur', 'sing', 'fem', 'masc',
        'intr', 'pass', 'pres', 'fut', 'cond', 'cong', 'imper',
        'art', 'det', 'indef', 'dim', 'accr', 'vezz',
        # Parole del header
        'neretto', 'tondo', 'indica', 'parole', 'fondamentali', 'chiaro',
        'corsivo', 'uso', 'disponibilità', 'nuovo',
        'vocabolario', 'base', 'lingua', 'italiana', 'tullio', 'mauro',
        'internazionale', 'dizionario', 'nuovovocabolariodiba',
        'dic', 'cura', 'della', 'dicembre'
    }
    
    # Parole da includere forzatamente (lemmi comuni che potrebbero essere filtrati)
    force_include = {
        'essere', 'avere', 'fare', 'dire', 'andare', 'potere', 'volere', 'sapere',
        'venire', 'dovere', 'stare', 'dare', 'vedere', 'capire', 'sentire',
        'il', 'lo', 'la', 'le', 'gli', 'uno', 'una', 'dei', 'delle',
        'di', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra',
        'che', 'chi', 'cui', 'quale', 'quanto',
        'io', 'tu', 'egli', 'ella', 'noi', 'voi', 'essi', 'esse',
        'mio', 'tuo', 'suo', 'nostro', 'vostro', 'loro',
        'questo', 'quello', 'stesso', 'altro', 'tale', 'tanto', 'molto', 'poco',
        'tutto', 'ogni', 'qualche', 'alcuno', 'nessuno',
        'uno', 'due', 'tre', 'quattro', 'cinque', 'sei', 'sette', 'otto', 'nove', 'dieci',
        'primo', 'secondo', 'terzo',
        'sì', 'no', 'non', 'né', 'anche', 'ancora', 'già', 'mai', 'sempre', 'mai',
        'qui', 'qua', 'lì', 'là', 'dove', 'quando', 'come', 'perché'
    }
    
    clean_words = set()
    for word in words_set:
        # Forza inclusione di parole comuni
        if word in force_include:
            clean_words.add(word)
            continue
            
        # Filtra stop words e parole troppo corte
        if (word in stop_words 
            or len(word) < 2 
            or word.isdigit()
            or not (word.isalpha() or "'" in word)):
            continue
        
        clean_words.add(word)
    
    return sorted(clean_words)

def create_nvdb_structure(words):
    """
    Crea la struttura JSON del vocabolario con classificazione futura.
    
    Struttura:
    {
        "metadata": {...},
        "vocabolario": {
            "parola": {
                "livello": null,  # Da classificare: "fondamentale", "alto_uso", "alta_disponibilita"
                "note": ""
            }
        }
    }
    """
    vocabolario = {}
    
    for word in words:
        vocabolario[word] = {
            "livello": None,  # null = non ancora classificato
            "note": ""
        }
    
    structure = {
        "metadata": {
            "nome": "Nuovo Vocabolario di Base della lingua italiana",
            "autore": "Tullio De Mauro",
            "anno": 2016,
            "fonte": "nuovovocabolariodibase.pdf",
            "data_estrazione": "2025-10-24",
            "totale_parole": len(words),
            "livelli": {
                "fondamentale": {
                    "descrizione": "Parole più frequenti in assoluto",
                    "count": 0
                },
                "alto_uso": {
                    "descrizione": "Parole ancora molto frequenti",
                    "count": 0
                },
                "alta_disponibilita": {
                    "descrizione": "Parole comuni nel parlato ma rare nello scritto",
                    "count": 0
                },
                "non_classificato": {
                    "descrizione": "Parole estratte ma non ancora classificate",
                    "count": len(words)
                }
            },
            "note": "Il livello 'null' indica parole non ancora classificate. Per classificare manualmente, modificare il campo 'livello' con: 'fondamentale', 'alto_uso' o 'alta_disponibilita'"
        },
        "vocabolario": vocabolario
    }
    
    return structure

def save_formats(nvdb_structure, output_dir):
    """Salva il vocabolario in diversi formati."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 1. JSON completo (con metadata e struttura per classificazione)
    json_path = output_dir / "nvdb_completo.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(nvdb_structure, f, ensure_ascii=False, indent=2)
    print(f"✓ Salvato JSON completo: {json_path}")
    
    # 2. JSON semplificato (solo lista parole per uso veloce)
    json_simple_path = output_dir / "nvdb_parole.json"
    words_list = sorted(nvdb_structure["vocabolario"].keys())
    with open(json_simple_path, 'w', encoding='utf-8') as f:
        json.dump(words_list, f, ensure_ascii=False, indent=2)
    print(f"✓ Salvato JSON semplificato: {json_simple_path}")
    
    # 3. TXT (una parola per riga, per editing manuale facile)
    txt_path = output_dir / "nvdb_parole.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(words_list))
    print(f"✓ Salvato TXT: {txt_path}")
    
    # 4. Template per classificazione manuale (CSV-like)
    csv_path = output_dir / "nvdb_da_classificare.txt"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("# Formato: parola|livello\n")
        f.write("# livello può essere: fondamentale, alto_uso, alta_disponibilita\n")
        f.write("# Lasciare vuoto se non si conosce il livello\n\n")
        for word in words_list[:50]:  # Prime 50 come esempio
            f.write(f"{word}|\n")
    print(f"✓ Salvato template classificazione: {csv_path}")

def main():
    # Path del PDF
    pdf_path = Path("correttore files/nuovovocabolariodibase.pdf")
    
    if not pdf_path.exists():
        print(f"❌ Errore: PDF non trovato in {pdf_path}")
        return
    
    print("=" * 60)
    print("ESTRAZIONE NUOVO VOCABOLARIO DI BASE (NVdB)")
    print("=" * 60)
    
    # Estrai parole
    words = extract_words_from_pdf(pdf_path)
    print(f"\n✓ Parole estratte e pulite: {len(words)}")
    print(f"\nPrime 30 parole: {words[:30]}")
    print(f"Ultime 30 parole: {words[-30:]}")
    
    # Crea struttura
    print("\nCreazione struttura dati...")
    nvdb_structure = create_nvdb_structure(words)
    
    # Salva in vari formati
    print("\nSalvataggio file...")
    save_formats(nvdb_structure, "data/vocabolario")
    
    print("\n" + "=" * 60)
    print("ESTRAZIONE COMPLETATA!")
    print("=" * 60)
    print(f"\nFile creati in: data/vocabolario/")
    print("\nPer usare il vocabolario nel correttore:")
    print("  → nvdb_parole.json (lista semplice, veloce da caricare)")
    print("  → nvdb_completo.json (struttura completa con metadata)")
    print("\nPer classificare manualmente:")
    print("  → Modifica nvdb_completo.json cambiando 'livello': null")
    print("  → oppure usa nvdb_da_classificare.txt come riferimento")

if __name__ == "__main__":
    main()
