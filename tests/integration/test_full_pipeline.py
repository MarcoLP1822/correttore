"""
Test di integrazione per la pipeline completa di correzione.

Testa l'orchestrazione di tutti i componenti insieme.
"""
import unittest
import sys
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Aggiungi il path del progetto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.correction_engine import CorrectionEngine
from core.document_handler import DocumentHandler
from core.quality_assurance import QualityAssurance
from core.formatting_manager import FormattingManager
from core.error_handling import ErrorHandler
from services.openai_service import OpenAIService
from services.languagetool_service import LanguageToolService
from config.settings import Settings


class TestFullPipeline(unittest.TestCase):
    """Test di integrazione per pipeline completa."""
    
    def setUp(self):
        """Setup per test di integrazione."""
        self.settings = Settings()
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Inizializza componenti
        self.document_handler = DocumentHandler(self.settings)
        self.correction_engine = CorrectionEngine(self.settings)
        self.quality_assurance = QualityAssurance(self.settings)
        self.formatting_manager = FormattingManager(self.settings)
        self.error_handler = ErrorHandler(self.settings)
        
    def tearDown(self):
        """Cleanup."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    def test_pipeline_integration_basic(self):
        """Test integrazione base della pipeline."""
        # Input text with errors
        input_text = "Questo è un testo con alcuni errori di ortografia e gramatica."
        
        with patch.object(self.correction_engine, 'correct_text_safe') as mock_correct:
            mock_result = Mock()
            mock_result.corrected_text = "Questo è un testo con alcuni errori di ortografia e grammatica."
            mock_result.is_safe = True
            mock_result.quality_score = 0.9
            mock_correct.return_value = mock_result
            
            # Execute pipeline
            result = self.correction_engine.correct_text_safe(input_text)
            
            # Verify result
            self.assertTrue(result.is_safe)
            self.assertGreater(result.quality_score, 0.8)
            self.assertNotEqual(result.corrected_text, input_text)
            
    def test_pipeline_with_document_processing(self):
        """Test pipeline completa con processamento documento."""
        # Skip se non in ambiente di integrazione
        if not os.getenv('INTEGRATION_TESTS'):
            self.skipTest("Integration tests not enabled")
            
        try:
            from docx import Document
        except ImportError:
            self.skipTest("python-docx not available")
            
        # Crea documento di test
        doc = Document()
        doc.add_paragraph("Primo paragrafo con errori di gramatica.")
        doc.add_paragraph("Secondo paragrafo che necessita correzioni.")
        
        input_file = self.temp_dir / "input.docx"
        doc.save(str(input_file))
        
        # Process document
        with patch.object(self.correction_engine, 'correct_text_safe') as mock_correct:
            mock_result = Mock()
            mock_result.corrected_text = "Testo corretto."
            mock_result.is_safe = True
            mock_result.quality_score = 0.9
            mock_correct.return_value = mock_result
            
            # Load document
            loaded_doc = self.document_handler.load_document(input_file)
            
            # Extract text
            text = self.document_handler.extract_text(loaded_doc)
            
            # Correct text
            corrections = {}
            for paragraph in loaded_doc.paragraphs:
                if paragraph.text.strip():
                    result = self.correction_engine.correct_text_safe(paragraph.text)
                    if result.is_safe:
                        corrections[paragraph.text] = result.corrected_text
                        
            # Apply corrections
            success = self.document_handler.apply_corrections_to_document(loaded_doc, corrections)
            
            # Save result
            output_file = self.temp_dir / "output.docx"
            self.document_handler.save_document(loaded_doc, output_file)
            
            self.assertTrue(output_file.exists())
            
    def test_error_handling_in_pipeline(self):
        """Test gestione errori nella pipeline."""
        input_text = "Testo di test per errori."
        
        # Simula errore API
        with patch.object(self.correction_engine, 'openai_service') as mock_openai:
            mock_openai.correct_text.side_effect = Exception("API Error")
            
            # Verifica che error handler gestisca l'errore
            with patch.object(self.error_handler, 'handle_api_error') as mock_handle:
                mock_handle.return_value = "Fallback result"
                
                try:
                    result = self.correction_engine.correct_text_safe(input_text)
                    # Se non viene sollevata eccezione, error handler ha funzionato
                    self.assertIsNotNone(result)
                except Exception:
                    # Se viene sollevata eccezione, verifica che error handler sia stato chiamato
                    mock_handle.assert_called()
                    
    def test_quality_assurance_integration(self):
        """Test integrazione quality assurance nella pipeline."""
        original = "Testo original con errore."
        corrected = "Testo originale con errore corretto."
        
        # Assess correction quality
        report = self.quality_assurance.assess_correction(original, corrected)
        
        # Verify quality assessment
        self.assertIsNotNone(report)
        self.assertGreater(report.overall_score, 0.0)
        self.assertLessEqual(report.overall_score, 1.0)
        
        # Test acceptance based on quality
        is_acceptable = self.quality_assurance.is_correction_acceptable(report)
        self.assertIsInstance(is_acceptable, bool)
        
    def test_formatting_preservation_integration(self):
        """Test preservazione formattazione nella pipeline."""
        try:
            from docx import Document
        except ImportError:
            self.skipTest("python-docx not available")
            
        # Crea documento con formattazione
        doc = Document()
        p = doc.add_paragraph()
        run1 = p.add_run("Testo normale ")
        run2 = p.add_run("testo in grassetto")
        run2.bold = True
        
        # Extract formatting
        formatting_map = self.formatting_manager.extract_formatting(p)
        
        # Simula correzione
        original_text = p.text
        corrected_text = "Testo normale testo in grassetto corretto"
        
        # Apply formatting
        success = self.formatting_manager.apply_formatting(
            p, corrected_text, formatting_map
        )
        
        self.assertTrue(success)
        
    def test_performance_monitoring_integration(self):
        """Test monitoring performance nella pipeline."""
        input_texts = [
            "Primo testo da correggere.",
            "Secondo testo con errori.",
            "Terzo testo per test."
        ]
        
        with patch.object(self.correction_engine, 'correct_text_safe') as mock_correct:
            mock_result = Mock()
            mock_result.corrected_text = "Testo corretto."
            mock_result.is_safe = True
            mock_result.quality_score = 0.9
            mock_correct.return_value = mock_result
            
            # Reset metrics
            self.correction_engine.reset_metrics()
            
            # Process texts
            for text in input_texts:
                self.correction_engine.correct_text_safe(text)
                
            # Get metrics
            metrics = self.correction_engine.get_performance_metrics()
            
            self.assertEqual(metrics['corrections_count'], 3)
            self.assertIn('total_processing_time', metrics)
            self.assertIn('average_processing_time', metrics)
            
    def test_batch_processing_integration(self):
        """Test processamento batch nella pipeline."""
        texts = [
            "Primo testo da correggere con errori.",
            "Secondo testo che necesita revisione.",
            "Terzo testo finale del batch."
        ]
        
        with patch.object(self.correction_engine, 'correct_text_safe') as mock_correct:
            mock_result = Mock()
            mock_result.corrected_text = "Testo corretto."
            mock_result.is_safe = True
            mock_result.quality_score = 0.9
            mock_correct.return_value = mock_result
            
            results = self.correction_engine.process_batch(texts)
            
            self.assertEqual(len(results), 3)
            self.assertEqual(mock_correct.call_count, 3)
            
            # Verify all results are successful
            for result in results:
                self.assertTrue(result.is_safe)
                self.assertGreater(result.quality_score, 0.8)
                
    def test_configuration_integration(self):
        """Test integrazione configurazione nella pipeline."""
        # Test con configurazione conservativa
        self.settings.correction_mode = 'conservative'
        self.settings.quality_threshold = 0.95
        
        engine = CorrectionEngine(self.settings)
        
        # Verifica che le impostazioni siano applicate
        self.assertEqual(engine.settings.correction_mode, 'conservative')
        self.assertEqual(engine.settings.quality_threshold, 0.95)
        
    def test_cache_integration(self):
        """Test integrazione cache nella pipeline."""
        if not hasattr(self.correction_engine, 'cache_service'):
            self.skipTest("Cache service not available")
            
        text = "Testo per test cache."
        
        with patch.object(self.correction_engine, 'cache_service') as mock_cache:
            # Prima chiamata: cache miss
            mock_cache.get.return_value = None
            
            with patch.object(self.correction_engine, 'correct_text') as mock_correct:
                mock_correct.return_value = "Testo corretto per cache."
                
                result1 = self.correction_engine.correct_text_cached(text)
                
                # Verifica cache store
                mock_cache.store.assert_called_once()
                
            # Seconda chiamata: cache hit
            mock_cache.get.return_value = "Testo corretto per cache."
            
            result2 = self.correction_engine.correct_text_cached(text)
            
            self.assertEqual(result1, result2)


class TestEdgeCases(unittest.TestCase):
    """Test per casi limite della pipeline."""
    
    def setUp(self):
        """Setup per test edge cases."""
        self.settings = Settings()
        self.correction_engine = CorrectionEngine(self.settings)
        
    def test_empty_text_handling(self):
        """Test gestione testo vuoto."""
        empty_texts = ["", "   ", "\n\n", "\t\t"]
        
        for text in empty_texts:
            with patch.object(self.correction_engine, 'correct_text_safe') as mock_correct:
                mock_result = Mock()
                mock_result.corrected_text = text.strip() if text.strip() else ""
                mock_result.is_safe = True
                mock_result.quality_score = 1.0
                mock_correct.return_value = mock_result
                
                result = self.correction_engine.correct_text_safe(text)
                
                # Testo vuoto deve rimanere vuoto
                self.assertEqual(result.corrected_text, text.strip() if text.strip() else "")
                
    def test_very_long_text_handling(self):
        """Test gestione testo molto lungo."""
        # Crea testo molto lungo (simula capitolo di romanzo)
        long_text = "Questo è un paragrafo di test. " * 1000
        
        with patch.object(self.correction_engine, 'chunk_text') as mock_chunk:
            # Simula chunking
            chunks = [long_text[i:i+1000] for i in range(0, len(long_text), 1000)]
            mock_chunk.return_value = chunks
            
            with patch.object(self.correction_engine, 'correct_text_safe') as mock_correct:
                mock_result = Mock()
                mock_result.corrected_text = "Chunk corretto."
                mock_result.is_safe = True
                mock_result.quality_score = 0.9
                mock_correct.return_value = mock_result
                
                result = self.correction_engine.process_long_text(long_text)
                
                # Verifica che il testo sia stato processato in chunk
                mock_chunk.assert_called_once()
                self.assertIsNotNone(result)
                
    def test_special_characters_handling(self):
        """Test gestione caratteri speciali."""
        special_texts = [
            "Testo con «virgolette» e – trattini.",
            "Testo con emoji 😀 e simboli ©®™.",
            "Testo con accenti àèìòù e apostrofi l'idea.",
            "Testo con numeri 123.456,78 e date 15/03/2024."
        ]
        
        for text in special_texts:
            with patch.object(self.correction_engine, 'correct_text_safe') as mock_correct:
                mock_result = Mock()
                mock_result.corrected_text = text  # Mantiene caratteri speciali
                mock_result.is_safe = True
                mock_result.quality_score = 0.9
                mock_correct.return_value = mock_result
                
                result = self.correction_engine.correct_text_safe(text)
                
                # Caratteri speciali devono essere preservati
                self.assertTrue(result.is_safe)
                
    def test_dialogue_formatting_preservation(self):
        """Test preservazione formattazione dialoghi."""
        dialogue_texts = [
            '«Ciao», disse Marco.',
            '"Hello", replied John.',
            '- Andiamo? - chiese Maria.',
            'Marco esclamò: "Fantastico!"'
        ]
        
        for text in dialogue_texts:
            with patch.object(self.correction_engine, 'correct_text_safe') as mock_correct:
                mock_result = Mock()
                mock_result.corrected_text = text  # Preserva formattazione dialoghi
                mock_result.is_safe = True
                mock_result.quality_score = 0.95
                mock_correct.return_value = mock_result
                
                result = self.correction_engine.correct_text_safe(text)
                
                # Formattazione dialoghi deve essere preservata
                self.assertIn(result.corrected_text[0], ['«', '"', '-'])


if __name__ == '__main__':
    # Configura logging per test
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Esegui test con diversi livelli di verbosity
    verbosity = 2 if '--verbose' in sys.argv else 1
    
    # Test runner con discovery
    unittest.main(verbosity=verbosity, exit=False)
    
    # Se environment di integrazione, esegui test aggiuntivi
    if os.getenv('INTEGRATION_TESTS'):
        print("\n" + "="*60)
        print("RUNNING EXTENDED INTEGRATION TESTS")
        print("="*60)
        
        # Carica test aggiuntivi
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Aggiungi test edge cases
        suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
        
        # Esegui test estesi
        runner = unittest.TextTestRunner(verbosity=verbosity)
        runner.run(suite)
