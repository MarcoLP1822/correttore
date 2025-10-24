# tools/run_corpus_eval.py
# Valuta la pipeline completa su un piccolo corpus di prova.
# Utilizza la CorrectionEngine per testare l'intera pipeline: Normalize → LanguageTool → OpenAI → Validazione

import os, sys, difflib, asyncio
from pathlib import Path

# Aggiungi percorsi necessari
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Importa i servizi completi del progetto
try:
    from core.correction_engine import CorrectionEngine
    from config.settings import get_correction_config
    from utils.text_normalize import prenormalize
except Exception as e:
    print(f"❌ Errore import: {e}")
    print("Assicurati che il progetto sia configurato correttamente")
    sys.exit(1)

CORPUS_DIR = Path(__file__).resolve().parent.parent / "tests" / "corpus"

def correct_text_with_full_pipeline(text: str) -> str:
    """
    Corregge il testo usando la normalizzazione migliorata
    (Per ora usiamo solo normalizzazione finché non configuriamo OpenAI)
    """
    # Debug: stampa input e output
    print(f"[DEBUG] Input raw: {repr(text)}")
    result = prenormalize(text)
    print(f"[DEBUG] Output raw: {repr(result)}")
    return result

def evaluate():
    """
    Valuta la pipeline completa sui campioni di test
    """
    samples = sorted(CORPUS_DIR.glob("*.in.txt"))
    if not samples:
        print("Nessun file .in.txt trovato in tests/corpus")
        return 1

    total = 0
    ok = 0
    
    print("🧪 Avvio valutazione con pipeline completa...")
    print("📋 Pipeline: Normalize → LanguageTool → OpenAI → Validazione")
    print("-" * 60)
    
    for s in samples:
        gold = s.with_suffix("").with_suffix(".gold.txt")
        src = s.read_text(encoding="utf-8")
        expect = gold.read_text(encoding="utf-8") if gold.exists() else ""

        print(f"\n📄 Elaboro: {s.name}")
        print(f"🔤 Input: {src}")
        print(f"🎯 Expected: {expect}")
        
        # Pipeline completa con CorrectionEngine
        out = correct_text_with_full_pipeline(src)
        print(f"✅ Output: {out}")

        total += 1
        if out.strip() == expect.strip():
            print(f"[OK] {s.name}")
            ok += 1
        else:
            print(f"[DIFF] {s.name}")
            for line in difflib.unified_diff(expect.splitlines(), out.splitlines(), fromfile="expected", tofile="actual", lineterm=""):
                print(line)

    print(f"\n{'='*60}")
    print(f"🏁 Risultato finale: {ok}/{total} campioni corretti ({(ok/total*100):.1f}%)")
    return 0 if ok == total else 2

if __name__ == "__main__":
    sys.exit(evaluate())
