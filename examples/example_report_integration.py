"""
Esempio di integrazione del Report HTML nel workflow di correzione.

Questo esempio mostra come generare automaticamente un report HTML
durante il processo di correzione del documento.

Author: Sistema di Correzione Avanzato
Date: 24 Ottobre 2025
"""

import sys
from pathlib import Path

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from datetime import datetime
from correttore.models import CorrectionRecord, CorrectionCategory, CorrectionSource
from correttore.core.correction_collector import CorrectionCollector
from correttore.utils.html_report_generator import generate_orthography_report


def simula_correzione_documento(testo: str) -> CorrectionCollector:
    """
    Simula il processo di correzione di un documento.
    
    In un caso reale, questo sarebbe fatto da:
    - LanguageTool Service
    - OpenAI Service
    - Safe Correction Engine
    
    Args:
        testo: Testo da correggere
        
    Returns:
        CorrectionCollector con tutte le correzioni identificate
    """
    
    collector = CorrectionCollector()
    collector.start_tracking()
    
    # Simula analisi LanguageTool
    print("🔍 Analisi con LanguageTool...")
    
    # Esempio: errore di concordanza
    if "molti persone" in testo.lower():
        idx = testo.lower().find("molti persone")
        collector.add_correction(CorrectionRecord(
            category=CorrectionCategory.ERRORI_RICONOSCIUTI,
            original_text="persone",
            corrected_text="persone",
            context=testo[max(0, idx-20):min(len(testo), idx+50)],
            position=idx,
            paragraph_index=0,
            sentence_index=0,
            source=CorrectionSource.LANGUAGETOOL,
            confidence_score=0.95,
            rule_id="AGREEMENT_ERROR",
            message="Errore di concordanza: 'molti' richiede sostantivo maschile",
            suggestions=["molte persone", "molti uomini"],
            timestamp=datetime.now()
        ))
    
    # Esempio: accento errato
    if "perchè" in testo:
        idx = testo.find("perchè")
        collector.add_correction(CorrectionRecord(
            category=CorrectionCategory.ERRORI_RICONOSCIUTI,
            original_text="perchè",
            corrected_text="perché",
            context=testo[max(0, idx-20):min(len(testo), idx+50)],
            position=idx,
            paragraph_index=0,
            sentence_index=0,
            source=CorrectionSource.LANGUAGETOOL,
            confidence_score=0.99,
            rule_id="ACCENT_ERROR",
            message="Accento errato: usare 'perché' con accento acuto",
            suggestions=["perché"],
            timestamp=datetime.now()
        ))
    
    # Simula analisi GPT
    print("🤖 Analisi con GPT...")
    
    # Esempio: parola sospetta
    if "abbattuta" in testo and "vittoria" in testo:
        idx = testo.find("abbattuta")
        collector.add_correction(CorrectionRecord(
            category=CorrectionCategory.SOSPETTE,
            original_text="abbattuta",
            corrected_text="imbattuta",
            context=testo[max(0, idx-20):min(len(testo), idx+50)],
            position=idx,
            paragraph_index=0,
            sentence_index=0,
            source=CorrectionSource.OPENAI_GPT,
            confidence_score=0.7,
            rule_id="CONTEXT_SUSPICIOUS",
            message="Parola corretta ma sospetta nel contesto. Intendevi 'imbattuta'?",
            suggestions=["imbattuta", "esaltata"],
            timestamp=datetime.now()
        ))
    
    # Simula controllo vocabolario base
    print("📚 Controllo Vocabolario di Base...")
    
    # Parola non nel VdB
    parole_difficili = ["felino", "veterinario", "notturno"]
    for parola in parole_difficili:
        if parola in testo.lower():
            idx = testo.lower().find(parola)
            collector.add_correction(CorrectionRecord(
                category=CorrectionCategory.SCONOSCIUTE,
                original_text=parola,
                corrected_text="",
                context=testo[max(0, idx-20):min(len(testo), idx+50)],
                position=idx,
                paragraph_index=0,
                sentence_index=0,
                source=CorrectionSource.VOCABOLARIO_BASE,
                confidence_score=0.6,
                rule_id="NOT_IN_VDB",
                message=f"Parola '{parola}' non nel Vocabolario di Base",
                suggestions=["gatto" if parola == "felino" else ""],
                timestamp=datetime.now()
            ))
    
    collector.stop_tracking()
    
    print(f"✅ Analisi completata: {collector.get_statistics().total_corrections} correzioni")
    return collector


def main():
    """Esempio principale."""
    
    print("=" * 70)
    print("📝 ESEMPIO: Integrazione Report HTML nel Workflow")
    print("=" * 70)
    print()
    
    # Testo di esempio da correggere
    testo_esempio = """
    Il gatto è un animale domestico molto apprezzato. Molti persone hanno gatti 
    come animali da compagnia perchè sono indipendenti. Il felino è un animale 
    notturno che dorme durante il giorno. La squadra è abbattuta dopo la vittoria 
    nel campionato. Il veterinario ha controllato il gatto.
    """
    
    print("📄 Testo da correggere:")
    print("-" * 70)
    print(testo_esempio.strip())
    print("-" * 70)
    print()
    
    # STEP 1: Correzione documento
    print("🔧 STEP 1: Analisi e correzione documento")
    print()
    
    collector = simula_correzione_documento(testo_esempio)
    
    # Mostra statistiche
    stats = collector.get_statistics()
    print()
    print(f"📊 Statistiche:")
    print(f"   • Correzioni totali: {stats.total_corrections}")
    print(f"   • Tempo elaborazione: {stats.processing_time:.2f}s")
    print(f"   • Per categoria:")
    for cat, count in stats.by_category.items():
        print(f"     - {cat.display_name}: {count}")
    print()
    
    # STEP 2: Generazione report HTML
    print("🔨 STEP 2: Generazione report HTML")
    print()
    
    output_dir = Path("examples") / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = output_dir / "esempio_report.html"
    
    try:
        result = generate_orthography_report(
            collector=collector,
            output_path=str(report_path),
            document_name="Esempio Integrazione",
            standalone=True,
            show_feedback_buttons=False
        )
        
        print(f"✅ Report generato con successo!")
        print(f"   📄 File: {result}")
        print(f"   📊 Dimensione: {Path(result).stat().st_size / 1024:.1f} KB")
        print()
        
    except Exception as e:
        print(f"❌ Errore generazione report: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # STEP 3: Informazioni finali
    print("=" * 70)
    print("✅ WORKFLOW COMPLETATO")
    print("=" * 70)
    print()
    print("📂 Output generati:")
    print(f"   1. Report HTML: {report_path}")
    print()
    print("🌐 Per visualizzare il report:")
    print(f"   • Apri il file in un browser")
    print(f"   • Oppure esegui: python -m webbrowser {report_path}")
    print()
    print("💡 Prossimi passi:")
    print("   • Integrare nel CorrectionEngine")
    print("   • Aggiungere alla Web Interface")
    print("   • Implementare FASE 3: Leggibilità")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
