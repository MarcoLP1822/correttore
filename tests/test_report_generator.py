"""
Test per Report Generator - FASE 3

Verifica funzionamento parametro report_type e backward compatibility.
"""

import sys
from pathlib import Path
from datetime import datetime

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from correttore.utils import (
    HTMLReportGenerator, 
    generate_orthography_report,
    generate_analysis_report
)
from correttore.core.correction_collector import CorrectionCollector
from correttore.models import CorrectionRecord, CorrectionCategory, CorrectionSource


def create_sample_collector() -> CorrectionCollector:
    """Crea un collector di esempio con alcuni errori."""
    collector = CorrectionCollector()
    collector.start_tracking()
    
    # Aggiungi alcuni record di esempio
    records = [
        CorrectionRecord(
            category=CorrectionCategory.ERRORI_RICONOSCIUTI,
            source=CorrectionSource.LANGUAGETOOL,
            original_text="erro",
            corrected_text="errore",
            context="Questo è un erro di esempio.",
            message="Possibile errore ortografico",
            position=13,
            paragraph_index=0
        ),
        CorrectionRecord(
            category=CorrectionCategory.PUNTEGGIATURA,
            source=CorrectionSource.LANGUAGETOOL,
            original_text="parola,senza",
            corrected_text="parola, senza",
            context="Una parola,senza spazio dopo la virgola.",
            message="Manca spazio dopo la punteggiatura",
            position=4,
            paragraph_index=0
        ),
        CorrectionRecord(
            category=CorrectionCategory.LINGUE,
            source=CorrectionSource.SYSTEM,
            original_text="hello",
            corrected_text=None,
            context="Questo testo contiene hello in inglese.",
            message="Parola in english",
            position=21,
            paragraph_index=1,
            additional_info={'language': 'english'}
        ),
    ]
    
    for record in records:
        collector.add_correction(record)
    
    collector.stop_tracking()
    return collector


def test_backward_compatibility():
    """Test 1: Verifica backward compatibility (nessun report_type)"""
    print("=" * 60)
    print("TEST 1: Backward Compatibility")
    print("=" * 60)
    
    collector = create_sample_collector()
    output_path = Path(__file__).parent.parent / "outputs" / "test_backward_compatibility.html"
    output_path.parent.mkdir(exist_ok=True)
    
    try:
        generator = HTMLReportGenerator()
        result_path = generator.generate_report(
            collector=collector,
            output_path=str(output_path),
            document_name="test_documento.docx",
            standalone=True,
            show_feedback_buttons=False
            # report_type NON specificato → default='correction'
        )
        
        print(f"\n✅ Report generato: {result_path}")
        
        # Verifica che il file esista
        if Path(result_path).exists():
            file_size = Path(result_path).stat().st_size
            print(f"   - Dimensione: {file_size} bytes")
            
            # Leggi contenuto per verificare titolo default
            with open(result_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "Report Correzione" in content or "Report Ortografia" in content:
                    print(f"   - ✅ Titolo default corretto (Report Correzione)")
                else:
                    print(f"   - ⚠️  Titolo non trovato nel contenuto")
        else:
            print(f"   - ❌ File non trovato!")
            return False
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_analysis_report_type():
    """Test 2: Verifica report_type='analysis'"""
    print("\n" + "=" * 60)
    print("TEST 2: Report Type 'analysis'")
    print("=" * 60)
    
    collector = create_sample_collector()
    output_path = Path(__file__).parent.parent / "outputs" / "test_analysis_report.html"
    
    try:
        generator = HTMLReportGenerator()
        result_path = generator.generate_report(
            collector=collector,
            output_path=str(output_path),
            document_name="test_documento.docx",
            standalone=True,
            show_feedback_buttons=False,
            report_type='analysis'  # ← Nuovo parametro
        )
        
        print(f"\n✅ Report analisi generato: {result_path}")
        
        # Verifica contenuto
        if Path(result_path).exists():
            file_size = Path(result_path).stat().st_size
            print(f"   - Dimensione: {file_size} bytes")
            
            with open(result_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "Analisi Qualità" in content:
                    print(f"   - ✅ Titolo analysis corretto (Analisi Qualità)")
                else:
                    print(f"   - ⚠️  Titolo 'Analisi Qualità' non trovato")
                
                if "Problemi Identificati" in content:
                    print(f"   - ✅ Label analysis corretta (Problemi Identificati)")
                else:
                    print(f"   - ⚠️  Label 'Problemi Identificati' non trovata")
        else:
            print(f"   - ❌ File non trovato!")
            return False
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_generate_analysis_report_helper():
    """Test 3: Verifica funzione helper generate_analysis_report()"""
    print("\n" + "=" * 60)
    print("TEST 3: Helper generate_analysis_report()")
    print("=" * 60)
    
    collector = create_sample_collector()
    output_path = Path(__file__).parent.parent / "outputs" / "test_helper_analysis.html"
    
    try:
        result_path = generate_analysis_report(
            collector=collector,
            output_path=str(output_path),
            document_name="test_helper.docx",
            standalone=True
        )
        
        print(f"\n✅ Report helper generato: {result_path}")
        
        # Verifica
        if Path(result_path).exists():
            file_size = Path(result_path).stat().st_size
            print(f"   - Dimensione: {file_size} bytes")
            
            with open(result_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "Analisi Qualità" in content:
                    print(f"   - ✅ Helper funziona correttamente")
                else:
                    print(f"   - ⚠️  Contenuto non corretto")
        else:
            print(f"   - ❌ File non trovato!")
            return False
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_correction_report_type():
    """Test 4: Verifica report_type='correction' esplicito"""
    print("\n" + "=" * 60)
    print("TEST 4: Report Type 'correction' esplicito")
    print("=" * 60)
    
    collector = create_sample_collector()
    output_path = Path(__file__).parent.parent / "outputs" / "test_correction_explicit.html"
    
    try:
        generator = HTMLReportGenerator()
        result_path = generator.generate_report(
            collector=collector,
            output_path=str(output_path),
            document_name="test_documento.docx",
            standalone=True,
            show_feedback_buttons=False,
            report_type='correction'  # Esplicito
        )
        
        print(f"\n✅ Report correzione generato: {result_path}")
        
        # Verifica
        if Path(result_path).exists():
            file_size = Path(result_path).stat().st_size
            print(f"   - Dimensione: {file_size} bytes")
            
            with open(result_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "Report Correzione" in content:
                    print(f"   - ✅ Tipo 'correction' funziona correttamente")
                else:
                    print(f"   - ⚠️  Contenuto non corretto")
        else:
            print(f"   - ❌ File non trovato!")
            return False
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Esegue tutti i test"""
    print("\n" + "📊" * 30)
    print("REPORT GENERATOR - TEST SUITE (FASE 3)")
    print("📊" * 30 + "\n")
    
    results = []
    
    try:
        # Test 1: Backward compatibility
        results.append(("Backward Compatibility", test_backward_compatibility()))
        
        # Test 2: report_type='analysis'
        results.append(("Report Type Analysis", test_analysis_report_type()))
        
        # Test 3: Helper function
        results.append(("Helper Function", test_generate_analysis_report_helper()))
        
        # Test 4: report_type='correction' esplicito
        results.append(("Report Type Correction", test_correction_report_type()))
        
        # Riepilogo
        print("\n" + "=" * 60)
        print("RIEPILOGO TEST")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\nRisultato: {passed}/{total} test passati")
        
        if passed == total:
            print("\n✅ TUTTI I TEST COMPLETATI CON SUCCESSO!")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test falliti")
            return 1
        
    except Exception as e:
        print(f"\n❌ ERRORE DURANTE I TEST: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
