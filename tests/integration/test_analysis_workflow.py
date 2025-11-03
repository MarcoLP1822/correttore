"""
Integration tests per Analysis Workflow - FASE 7
Test integrazione tra correzione, analisi e interfacce
"""

import unittest
import sys
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from correttore.core.document_analyzer import DocumentAnalyzer
from correttore.core.correction_engine import CorrectionEngine
from correttore.interfaces.cli import CorrectionMode


class TestCorrectionThenAnalysis(unittest.TestCase):
    """Test workflow: correzione → analisi automatica"""
    
    def setUp(self):
        """Setup test environment"""
        self.test_doc_path = Path(__file__).parent.parent / "fixtures" / "test_document.docx"
        
        if not self.test_doc_path.exists():
            uploads_dir = Path(__file__).parent.parent.parent / "uploads"
            if uploads_dir.exists():
                docs = list(uploads_dir.glob("*.docx"))
                if docs:
                    self.test_doc_path = docs[0]
                else:
                    self.skipTest("Nessun documento di test disponibile")
            else:
                self.skipTest("Directory uploads non trovata")
        
        # Crea directory temporanea per output
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Cleanup"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @unittest.skipIf(not os.getenv('OPENAI_API_KEY'), "Richiede OPENAI_API_KEY")
    def test_correction_with_post_analysis_enabled(self):
        """Test correzione con analisi automatica post-correzione"""
        # Crea engine con post-analysis abilitato
        engine = CorrectionEngine(
            enable_tracking=True,
            enable_post_analysis=True
        )
        
        # Copia documento in temp dir
        test_copy = self.temp_dir / self.test_doc_path.name
        shutil.copy(self.test_doc_path, test_copy)
        
        # Esegui correzione
        result = engine.correct_document(
            test_copy,
            output_path=self.temp_dir / f"{test_copy.stem}_corretto.docx"
        )
        
        # Verifica che correzione sia completata
        self.assertTrue(result.success)
        
        # L'analisi post-correzione viene eseguita automaticamente
        # ma non viene restituita nel CorrectionResult
        # Qui verifichiamo solo che non ci siano errori
        self.assertIsNotNone(result.document)
    
    @unittest.skipIf(not os.getenv('OPENAI_API_KEY'), "Richiede OPENAI_API_KEY")
    def test_correction_with_post_analysis_disabled(self):
        """Test correzione senza analisi automatica"""
        # Crea engine con post-analysis disabilitato
        engine = CorrectionEngine(
            enable_tracking=True,
            enable_post_analysis=False
        )
        
        # Copia documento in temp dir
        test_copy = self.temp_dir / self.test_doc_path.name
        shutil.copy(self.test_doc_path, test_copy)
        
        # Esegui correzione
        result = engine.correct_document(
            test_copy,
            output_path=self.temp_dir / f"{test_copy.stem}_corretto.docx"
        )
        
        # Verifica che correzione sia completata
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)


class TestStandaloneAnalysis(unittest.TestCase):
    """Test analisi standalone senza correzione"""
    
    def setUp(self):
        """Setup test environment"""
        self.test_doc_path = Path(__file__).parent.parent / "fixtures" / "test_document.docx"
        
        if not self.test_doc_path.exists():
            uploads_dir = Path(__file__).parent.parent.parent / "uploads"
            if uploads_dir.exists():
                docs = list(uploads_dir.glob("*.docx"))
                if docs:
                    self.test_doc_path = docs[0]
                else:
                    self.skipTest("Nessun documento di test disponibile")
            else:
                self.skipTest("Directory uploads non trovata")
        
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Cleanup"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_analyze_without_correction(self):
        """Test analisi standalone di documento originale"""
        analyzer = DocumentAnalyzer(
            enable_languagetool=False,  # Velocizza test
            enable_readability=True,
            enable_special_categories=True
        )
        
        result = analyzer.analyze_document(
            self.test_doc_path,
            output_report=True,
            output_dir=self.temp_dir
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.report_path)
        if result.report_path:  # Type guard per Pylance
            self.assertTrue(result.report_path.exists())
        self.assertGreater(result.total_words, 0)
    
    def test_analyze_multiple_documents(self):
        """Test analisi di più documenti"""
        analyzer = DocumentAnalyzer(
            enable_languagetool=False,
            enable_readability=True,
            enable_special_categories=False
        )
        
        # Trova tutti i documenti disponibili
        uploads_dir = Path(__file__).parent.parent.parent / "uploads"
        if not uploads_dir.exists():
            self.skipTest("Directory uploads non trovata")
        
        docs = list(uploads_dir.glob("*.docx"))[:3]  # Max 3 per velocità
        
        if len(docs) == 0:
            self.skipTest("Nessun documento disponibile")
        
        results = []
        for doc in docs:
            result = analyzer.analyze_document(
                doc,
                output_report=False
            )
            results.append(result)
        
        # Verifica che tutti siano stati analizzati
        self.assertEqual(len(results), len(docs))
        for result in results:
            self.assertTrue(result.success)
            self.assertGreater(result.total_words, 0)


class TestCLIAnalyzeCommand(unittest.TestCase):
    """Test comando CLI analyze"""
    
    def setUp(self):
        """Setup test environment"""
        self.test_doc_path = Path(__file__).parent.parent / "fixtures" / "test_document.docx"
        
        if not self.test_doc_path.exists():
            uploads_dir = Path(__file__).parent.parent.parent / "uploads"
            if uploads_dir.exists():
                docs = list(uploads_dir.glob("*.docx"))
                if docs:
                    self.test_doc_path = docs[0]
                else:
                    self.skipTest("Nessun documento di test disponibile")
            else:
                self.skipTest("Directory uploads non trovata")
        
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Cleanup"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_cli_analyze_basic(self):
        """Test comando analyze via CLI (simulato)"""
        from correttore.interfaces.cli import CorrettoreCLI
        
        cli = CorrettoreCLI()
        
        # Chiama metodo analyze_document
        success = cli.analyze_document(
            self.test_doc_path,
            output_dir=self.temp_dir
        )
        
        self.assertTrue(success)
        
        # Verifica che report sia stato generato
        reports = list(self.temp_dir.glob("*_analysis_*.html"))
        self.assertGreater(len(reports), 0)


class TestAnalysisReportContent(unittest.TestCase):
    """Test contenuto report generati"""
    
    def setUp(self):
        """Setup test environment"""
        self.test_doc_path = Path(__file__).parent.parent / "fixtures" / "test_document.docx"
        
        if not self.test_doc_path.exists():
            uploads_dir = Path(__file__).parent.parent.parent / "uploads"
            if uploads_dir.exists():
                docs = list(uploads_dir.glob("*.docx"))
                if docs:
                    self.test_doc_path = docs[0]
                else:
                    self.skipTest("Nessun documento di test disponibile")
            else:
                self.skipTest("Directory uploads non trovata")
        
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Cleanup"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_report_html_structure(self):
        """Test che report HTML abbia struttura corretta"""
        analyzer = DocumentAnalyzer(
            enable_languagetool=False,
            enable_readability=True,
            enable_special_categories=False
        )
        
        result = analyzer.analyze_document(
            self.test_doc_path,
            output_report=True,
            output_dir=self.temp_dir
        )
        
        self.assertIsNotNone(result.report_path)
        
        # Leggi contenuto report con type guard
        assert result.report_path is not None  # Type narrowing per Pylance
        content = result.report_path.read_text(encoding='utf-8')
        
        # Verifica elementi chiave
        self.assertIn('<!DOCTYPE html>', content)
        self.assertIn('<html', content)
        self.assertIn('</html>', content)
        # Verifica che contenga "analisi" in qualche forma (case-insensitive)
        self.assertTrue(
            'analisi' in content.lower() or 'analysis' in content.lower(),
            "Report should contain 'analisi' or 'analysis'"
        )
    
    def test_report_contains_stats(self):
        """Test che report contenga statistiche"""
        analyzer = DocumentAnalyzer(
            enable_languagetool=False,
            enable_readability=True,
            enable_special_categories=False
        )
        
        result = analyzer.analyze_document(
            self.test_doc_path,
            output_report=True,
            output_dir=self.temp_dir
        )
        
        assert result.report_path is not None  # Type narrowing per Pylance
        content = result.report_path.read_text(encoding='utf-8')
        
        # Dovrebbe contenere statistiche sulla qualità del documento
        self.assertTrue(
            'statistic' in content.lower() or 
            'qualità' in content.lower(),
            "Report should contain statistics or quality metrics"
        )


def run_tests():
    """Esegue tutti i test di integrazione"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Aggiungi test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCorrectionThenAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestStandaloneAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestCLIAnalyzeCommand))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalysisReportContent))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit(run_tests())
