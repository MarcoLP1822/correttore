"""
Script di test per il generatore di report HTML.

Genera un report di esempio con dati di test per tutte le categorie
per verificare la corretta visualizzazione.

Author: Sistema di Correzione Avanzato
Date: 24 Ottobre 2025
"""

import sys
from pathlib import Path

# Aggiungi path src per import
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from datetime import datetime
from correttore.models import CorrectionRecord, CorrectionCategory, CorrectionSource
from correttore.core.correction_collector import CorrectionCollector
from correttore.utils.html_report_generator import generate_orthography_report


def create_sample_corrections() -> CorrectionCollector:
    """Crea un collector con dati di esempio."""
    
    collector = CorrectionCollector()
    collector.start_tracking()
    
    # Testo di esempio
    sample_text = (
        "Il gatto è un animale domestico molto apprezzato. "
        "Molti persone hanno gatti come animali da compagnia. "
        "I gatti sono animali molto indipendenti e affascinanti."
    )
    
    # ERRORI RICONOSCIUTI
    collector.add_correction(CorrectionRecord(
        id="err_001",
        category=CorrectionCategory.ERRORI_RICONOSCIUTI,
        original_text="persone",
        corrected_text="persone",
        context="Molti persone hanno gatti come animali da compagnia.",
        position=6,
        paragraph_index=0,
        sentence_index=1,
        source=CorrectionSource.LANGUAGETOOL,
        confidence_score=0.95,
        rule_id="AGREEMENT_ERROR",
        message="Errore di concordanza: 'Molti' richiede il sostantivo maschile plurale 'molti'.",
        suggestions=["molte persone", "molti uomini"],
        timestamp=datetime.now()
    ))
    
    collector.add_correction(CorrectionRecord(
        id="err_002",
        category=CorrectionCategory.ERRORI_RICONOSCIUTI,
        original_text="perchè",
        corrected_text="perché",
        context="Non so perchè i gatti dormono così tanto.",
        position=8,
        paragraph_index=1,
        sentence_index=0,
        source=CorrectionSource.LANGUAGETOOL,
        confidence_score=0.98,
        rule_id="ACCENT_ERROR",
        message="Accento errato: 'perchè' dovrebbe essere scritto 'perché' con accento acuto.",
        suggestions=["perché"],
        timestamp=datetime.now()
    ))
    
    collector.add_correction(CorrectionRecord(
        id="err_003",
        category=CorrectionCategory.ERRORI_RICONOSCIUTI,
        original_text="qual'è",
        corrected_text="qual è",
        context="Qual'è il tuo gatto preferito?",
        position=0,
        paragraph_index=2,
        sentence_index=0,
        source=CorrectionSource.LANGUAGETOOL,
        confidence_score=0.99,
        rule_id="APOSTROPHE_ERROR",
        message="Apostrofo errato: 'qual è' si scrive senza apostrofo.",
        suggestions=["qual è"],
        timestamp=datetime.now()
    ))
    
    # SCONOSCIUTE
    collector.add_correction(CorrectionRecord(
        id="unk_001",
        category=CorrectionCategory.SCONOSCIUTE,
        original_text="Micio",
        corrected_text="",
        context="Micio è il nome del mio gatto.",
        position=0,
        paragraph_index=3,
        sentence_index=0,
        source=CorrectionSource.CUSTOM_RULES,
        confidence_score=0.5,
        rule_id="UNKNOWN_WORD",
        message="Parola non nel dizionario. Potrebbe essere un nome proprio.",
        suggestions=[],
        timestamp=datetime.now()
    ))
    
    collector.add_correction(CorrectionRecord(
        id="unk_002",
        category=CorrectionCategory.SCONOSCIUTE,
        original_text="felino",
        corrected_text="",
        context="Il felino si avvicinò lentamente.",
        position=3,
        paragraph_index=4,
        sentence_index=0,
        source=CorrectionSource.CUSTOM_RULES,
        confidence_score=0.6,
        rule_id="UNKNOWN_WORD",
        message="Parola non riconosciuta nel vocabolario base.",
        suggestions=["gatto", "animale"],
        timestamp=datetime.now()
    ))
    
    # SOSPETTE
    collector.add_correction(CorrectionRecord(
        id="susp_001",
        category=CorrectionCategory.SOSPETTE,
        original_text="abbattuta",
        corrected_text="imbattuta",
        context="La squadra è abbattuta dopo la vittoria.",
        position=15,
        paragraph_index=5,
        sentence_index=0,
        source=CorrectionSource.OPENAI_GPT,
        confidence_score=0.7,
        rule_id="CONTEXT_SUSPICIOUS",
        message="Parola corretta ma contestualmente sospetta. Forse intendevi 'imbattuta'?",
        suggestions=["imbattuta", "esaltata"],
        timestamp=datetime.now()
    ))
    
    # MIGLIORABILI
    collector.add_correction(CorrectionRecord(
        id="imp_001",
        category=CorrectionCategory.MIGLIORABILI,
        original_text="ad esempio",
        corrected_text="ad esempio",
        context="I gatti, ad esempio, sono animali notturni.",
        position=9,
        paragraph_index=6,
        sentence_index=0,
        source=CorrectionSource.OPENAI_GPT,
        confidence_score=0.8,
        rule_id="STYLE_IMPROVEMENT",
        message="Espressione migliorabile per stile.",
        suggestions=["come ad esempio", "per esempio"],
        timestamp=datetime.now()
    ))
    
    collector.add_correction(CorrectionRecord(
        id="imp_002",
        category=CorrectionCategory.MIGLIORABILI,
        original_text="degli dei",
        corrected_text="dei",
        context="Il numero degli dei errori è diminuito.",
        position=11,
        paragraph_index=7,
        sentence_index=0,
        source=CorrectionSource.OPENAI_GPT,
        confidence_score=0.75,
        rule_id="REDUNDANCY",
        message="Forma ridondante. Si può semplificare.",
        suggestions=["dei"],
        timestamp=datetime.now()
    ))
    
    # PUNTEGGIATURA
    collector.add_correction(CorrectionRecord(
        id="punct_001",
        category=CorrectionCategory.PUNTEGGIATURA,
        original_text=",",
        corrected_text="",
        context="Il gatto , dorme sul divano.",
        position=8,
        paragraph_index=8,
        sentence_index=0,
        source=CorrectionSource.LANGUAGETOOL,
        confidence_score=0.9,
        rule_id="SPACE_BEFORE_COMMA",
        message="Spazio prima della virgola non necessario.",
        suggestions=["rimuovi spazio"],
        timestamp=datetime.now()
    ))
    
    collector.add_correction(CorrectionRecord(
        id="punct_002",
        category=CorrectionCategory.PUNTEGGIATURA,
        original_text="!",
        corrected_text=".",
        context="Che bello!",
        position=9,
        paragraph_index=9,
        sentence_index=0,
        source=CorrectionSource.LANGUAGETOOL,
        confidence_score=0.6,
        rule_id="EXCLAMATION_INFORMAL",
        message="Punto esclamativo potrebbe essere informale in contesti professionali.",
        suggestions=["."],
        timestamp=datetime.now()
    ))
    
    # IMBARAZZANTI
    collector.add_correction(CorrectionRecord(
        id="emb_001",
        category=CorrectionCategory.IMBARAZZANTI,
        original_text="culo",
        corrected_text="",
        context="Il gatto si è seduto sul culo.",
        position=26,
        paragraph_index=10,
        sentence_index=0,
        source=CorrectionSource.CUSTOM_RULES,
        confidence_score=0.8,
        rule_id="POTENTIALLY_EMBARRASSING",
        message="Parola potenzialmente imbarazzante. Considerare alternative più formali.",
        suggestions=["sedere", "posteriore"],
        timestamp=datetime.now()
    ))
    
    # VARIANTI
    collector.add_correction(CorrectionRecord(
        id="var_001",
        category=CorrectionCategory.VARIANTI,
        original_text="edotto",
        corrected_text="istruito",
        context="Ho edotto il cliente sulla situazione.",
        position=3,
        paragraph_index=11,
        sentence_index=0,
        source=CorrectionSource.CUSTOM_RULES,
        confidence_score=0.7,
        rule_id="VARIANT_FORM",
        message="Forma corretta ma esistono varianti più comuni.",
        suggestions=["informato", "istruito", "avvisato"],
        timestamp=datetime.now()
    ))
    
    # NOMI/SIGLE
    collector.add_correction(CorrectionRecord(
        id="name_001",
        category=CorrectionCategory.NOMI_SIGLE,
        original_text="Marco",
        corrected_text="",
        context="Marco ha un gatto bellissimo.",
        position=0,
        paragraph_index=12,
        sentence_index=0,
        source=CorrectionSource.CUSTOM_RULES,
        confidence_score=0.95,
        rule_id="PROPER_NOUN",
        message="Nome proprio riconosciuto.",
        suggestions=[],
        timestamp=datetime.now()
    ))
    
    collector.add_correction(CorrectionRecord(
        id="name_002",
        category=CorrectionCategory.NOMI_SIGLE,
        original_text="NASA",
        corrected_text="",
        context="La NASA studia anche i gatti nello spazio.",
        position=3,
        paragraph_index=13,
        sentence_index=0,
        source=CorrectionSource.CUSTOM_RULES,
        confidence_score=0.99,
        rule_id="ACRONYM",
        message="Sigla riconosciuta.",
        suggestions=[],
        timestamp=datetime.now()
    ))
    
    # LINGUE
    collector.add_correction(CorrectionRecord(
        id="lang_001",
        category=CorrectionCategory.LINGUE,
        original_text="meeting",
        corrected_text="riunione",
        context="Abbiamo un meeting domani.",
        position=10,
        paragraph_index=14,
        sentence_index=0,
        source=CorrectionSource.CUSTOM_RULES,
        confidence_score=0.85,
        rule_id="FOREIGN_WORD",
        message="Parola inglese. Considerare traduzione italiana.",
        suggestions=["riunione", "incontro"],
        timestamp=datetime.now()
    ))
    
    collector.add_correction(CorrectionRecord(
        id="lang_002",
        category=CorrectionCategory.LINGUE,
        original_text="déjà vu",
        corrected_text="",
        context="Ho avuto un déjà vu guardando il gatto.",
        position=12,
        paragraph_index=15,
        sentence_index=0,
        source=CorrectionSource.CUSTOM_RULES,
        confidence_score=0.8,
        rule_id="FOREIGN_EXPRESSION",
        message="Espressione francese.",
        suggestions=["già visto"],
        timestamp=datetime.now()
    ))
    
    # CON INFO
    collector.add_correction(CorrectionRecord(
        id="info_001",
        category=CorrectionCategory.CON_INFO,
        original_text="veterinario",
        corrected_text="",
        context="Il veterinario ha visitato il gatto.",
        position=3,
        paragraph_index=16,
        sentence_index=0,
        source=CorrectionSource.CUSTOM_RULES,
        confidence_score=0.9,
        rule_id="ADDITIONAL_INFO",
        message="Info: termine tecnico professionale riconosciuto.",
        suggestions=[],
        timestamp=datetime.now()
    ))
    
    collector.stop_tracking()
    return collector


def main():
    """Funzione principale."""
    
    print("🧪 Test Generatore Report HTML")
    print("=" * 60)
    
    # Crea dati di test
    print("\n📝 Creazione dati di esempio...")
    collector = create_sample_corrections()
    
    stats = collector.get_statistics()
    print(f"✅ Creati {stats.total_corrections} correzioni di test")
    print(f"   Categorie: {stats.by_category}")
    
    # Genera report
    print("\n🔨 Generazione report HTML...")
    output_path = "test_output/report_test.html"
    
    try:
        result_path = generate_orthography_report(
            collector=collector,
            output_path=output_path,
            document_name="Documento di Test",
            standalone=True,
            show_feedback_buttons=True
        )
        
        print(f"✅ Report generato con successo!")
        print(f"   📄 File: {result_path}")
        print(f"\n🌐 Apri il file nel browser per visualizzare il report.")
        
    except Exception as e:
        print(f"❌ Errore nella generazione: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 60)
    print("✅ Test completato!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
