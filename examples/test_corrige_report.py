# examples/test_corrige_report.py
"""
Script di test per il nuovo sistema di report in stile Corrige.it
Dimostra la categorizzazione e generazione di report secondo lo standard Corrige.
"""

import sys
from pathlib import Path

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from correttore.utils.report_generator import ReportGenerator, ReportSection, CorrectionStats
from correttore.utils.diff_engine import DocumentDiff, ParagraphDiff, DiffResult, ChangeSegment
from correttore.core.quality_assurance import QualityReport
from datetime import datetime


def create_sample_document_diff():
    """Crea un esempio di DocumentDiff con vari tipi di errori"""
    
    # Crea alcuni paragrafi con correzioni di vario tipo
    paragraph_diffs = []
    
    # Esempio 1: Errore riconosciuto (ortografia)
    changes1 = [
        ChangeSegment(
            change_type='replace',
            original_text='errrore',
            modified_text='errore',
            start_pos=12,
            end_pos=19,
            confidence=1.0
        )
    ]
    diff1 = DiffResult(
        original_text='Questo è un errrore di battitura nel testo.',
        modified_text='Questo è un errore di battitura nel testo.',
        changes=changes1,
        total_changes=1,
        similarity_ratio=0.98,
        replacements=1
    )
    para1 = ParagraphDiff(
        paragraph_id=1,
        original='Questo è un errrore di battitura nel testo.',
        corrected='Questo è un errore di battitura nel testo.',
        diff_result=diff1,
        change_summary='Corretto errore ortografico: errrore → errore'
    )
    paragraph_diffs.append(para1)
    
    # Esempio 2: Parola sospetta
    changes2 = [
        ChangeSegment(
            change_type='replace',
            original_text='ditali',
            modified_text='di tali',
            start_pos=15,
            end_pos=21,
            confidence=0.8
        )
    ]
    diff2 = DiffResult(
        original_text='Non sono sicuro ditali argomenti da trattare nella riunione.',
        modified_text='Non sono sicuro di tali argomenti da trattare nella riunione.',
        changes=changes2,
        total_changes=1,
        similarity_ratio=0.97,
        replacements=1
    )
    para2 = ParagraphDiff(
        paragraph_id=2,
        original='Non sono sicuro ditali argomenti da trattare nella riunione.',
        corrected='Non sono sicuro di tali argomenti da trattare nella riunione.',
        diff_result=diff2,
        change_summary='Possibile confusione: ditali → di tali'
    )
    paragraph_diffs.append(para2)
    
    # Esempio 3: Migliorabile (ordinale)
    changes3 = [
        ChangeSegment(
            change_type='replace',
            original_text='1a',
            modified_text='1ª',
            start_pos=10,
            end_pos=12,
            confidence=1.0
        )
    ]
    diff3 = DiffResult(
        original_text='Questa è la 1a edizione del libro.',
        modified_text='Questa è la 1ª edizione del libro.',
        changes=changes3,
        total_changes=1,
        similarity_ratio=0.99,
        replacements=1
    )
    para3 = ParagraphDiff(
        paragraph_id=3,
        original='Questa è la 1a edizione del libro.',
        corrected='Questa è la 1ª edizione del libro.',
        diff_result=diff3,
        change_summary='Miglioramento: 1a → 1ª (ordinale corretto)'
    )
    paragraph_diffs.append(para3)
    
    # Esempio 4: Punteggiatura
    changes4 = [
        ChangeSegment(
            change_type='replace',
            original_text=' ,',
            modified_text=',',
            start_pos=25,
            end_pos=27,
            confidence=1.0
        )
    ]
    diff4 = DiffResult(
        original_text='Abbiamo visitato Roma , Firenze e Venezia.',
        modified_text='Abbiamo visitato Roma, Firenze e Venezia.',
        changes=changes4,
        total_changes=1,
        similarity_ratio=0.98,
        replacements=1
    )
    para4 = ParagraphDiff(
        paragraph_id=4,
        original='Abbiamo visitato Roma , Firenze e Venezia.',
        corrected='Abbiamo visitato Roma, Firenze e Venezia.',
        diff_result=diff4,
        change_summary='Corretto spazio prima della virgola'
    )
    paragraph_diffs.append(para4)
    
    # Esempio 5: Variante
    changes5 = [
        ChangeSegment(
            change_type='replace',
            original_text='obbiettivo',
            modified_text='obiettivo',
            start_pos=15,
            end_pos=25,
            confidence=1.0
        )
    ]
    diff5 = DiffResult(
        original_text='Il nostro obbiettivo principale è la qualità.',
        modified_text='Il nostro obiettivo principale è la qualità.',
        changes=changes5,
        total_changes=1,
        similarity_ratio=0.98,
        replacements=1
    )
    para5 = ParagraphDiff(
        paragraph_id=5,
        original='Il nostro obbiettivo principale è la qualità.',
        corrected='Il nostro obiettivo principale è la qualità.',
        diff_result=diff5,
        change_summary='Variante ortografica: obbiettivo → obiettivo'
    )
    paragraph_diffs.append(para5)
    
    # Esempio 6: Nome proprio
    para6 = ParagraphDiff(
        paragraph_id=6,
        original='Il documento è stato firmato da Mario Rossi.',
        corrected='Il documento è stato firmato da Mario Rossi.',
        diff_result=DiffResult(
            original_text='Il documento è stato firmato da Mario Rossi.',
            modified_text='Il documento è stato firmato da Mario Rossi.',
            changes=[],
            total_changes=0,
            similarity_ratio=1.0
        ),
        change_summary='Nessuna modifica'
    )
    paragraph_diffs.append(para6)
    
    # Esempio 7: Parola straniera
    para7 = ParagraphDiff(
        paragraph_id=7,
        original='Utilizziamo best practices nel nostro workflow.',
        corrected='Utilizziamo best practices nel nostro workflow.',
        diff_result=DiffResult(
            original_text='Utilizziamo best practices nel nostro workflow.',
            modified_text='Utilizziamo best practices nel nostro workflow.',
            changes=[],
            total_changes=0,
            similarity_ratio=1.0
        ),
        change_summary='Nessuna modifica (parole inglesi presenti)'
    )
    paragraph_diffs.append(para7)
    
    # Crea DocumentDiff
    doc_diff = DocumentDiff(
        document_name='Documento di Test Corrige',
        total_paragraphs=7,
        modified_paragraphs=5,
        paragraph_diffs=paragraph_diffs,
        global_stats={
            'modification_rate': 5/7,
            'total_changes': 5,
            'average_similarity': 0.98
        },
        generation_time=datetime.now()
    )
    
    return doc_diff


def create_sample_stats():
    """Crea statistiche di esempio"""
    return CorrectionStats(
        total_paragraphs=7,
        paragraphs_processed=7,
        corrections_applied=5,
        corrections_rejected=1,
        rollbacks_performed=0,
        processing_time=12.5,
        success_rate=0.95,
        average_quality_score=0.92,
        total_tokens_used=2500,
        api_calls_made=10,
        cache_hits=3
    )


def create_sample_quality_reports():
    """Crea quality reports di esempio"""
    reports = []
    
    for i in range(1, 8):
        report = QualityReport(
            overall_score=0.95 if i != 2 else 0.72,
            passed=True if i != 2 else False,  # Para 2 sotto soglia
            issues_found=[] if i != 2 else ["Confidence: bassa affidabilità"],
            recommendations=["Ottima qualità"] if i != 2 else ["Qualità sotto soglia"]
        )
        reports.append(report)
    
    return reports


def main():
    """Test principale"""
    print("🧪 Test del Sistema di Report Corrige.it\n")
    print("=" * 60)
    
    # Crea dati di esempio
    print("\n1️⃣ Creazione dati di test...")
    doc_diff = create_sample_document_diff()
    stats = create_sample_stats()
    quality_reports = create_sample_quality_reports()
    print("✅ Dati creati")
    
    # Crea report generator
    print("\n2️⃣ Inizializzazione ReportGenerator...")
    generator = ReportGenerator()
    print("✅ Generator pronto")
    
    # Genera report in stile Corrige
    print("\n3️⃣ Generazione report Corrige-style...")
    
    # Output directory
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    # Genera HTML
    output_html = output_dir / 'test_corrige_report.html'
    try:
        result_html = generator.generate_correction_report(
            document_diff=doc_diff,
            correction_stats=stats,
            quality_reports=quality_reports,
            output_path=output_html,
            template='corrige',
            format_type='html'
        )
        print(f"✅ Report HTML generato: {result_html}")
    except Exception as e:
        print(f"❌ Errore generazione HTML: {e}")
        import traceback
        traceback.print_exc()
    
    # Genera Markdown
    output_md = output_dir / 'test_corrige_report.md'
    try:
        result_md = generator.generate_correction_report(
            document_diff=doc_diff,
            correction_stats=stats,
            quality_reports=quality_reports,
            output_path=output_md,
            template='corrige',
            format_type='markdown'
        )
        print(f"✅ Report Markdown generato: {result_md}")
    except Exception as e:
        print(f"❌ Errore generazione Markdown: {e}")
        import traceback
        traceback.print_exc()
    
    # Genera JSON
    output_json = output_dir / 'test_corrige_report.json'
    try:
        result_json = generator.generate_correction_report(
            document_diff=doc_diff,
            correction_stats=stats,
            quality_reports=quality_reports,
            output_path=output_json,
            template='corrige',
            format_type='json'
        )
        print(f"✅ Report JSON generato: {result_json}")
    except Exception as e:
        print(f"❌ Errore generazione JSON: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✨ Test completato!")
    print(f"\n📂 I report sono stati salvati in: {output_dir.absolute()}")
    print("\n💡 Apri il file HTML in un browser per vedere il resoconto in stile Corrige.it")


if __name__ == '__main__':
    main()
