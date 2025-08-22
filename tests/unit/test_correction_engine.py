"""
Test unitari per CorrectionEngine.

Testa la business logic di orchestrazione delle correzioni.
"""
import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Aggiungi il path del progetto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.correction_engine import CorrectionEngine
from core.quality_assurance import QualityReport, QualityAssurance
from core.error_handling import CorrectionError, APITimeoutError
from config.settings import Settings


class TestCorrectionEngine(unittest.TestCase):
    """Test suite per CorrectionEngine."""
    
    def setUp(self):
        """Setup per ogni test."""
        self.settings = Settings()
        self.engine = CorrectionEngine(self.settings)
        
    def test_engine_initialization(self):
        """Test inizializzazione engine."""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.settings)
        self.assertIsNotNone(self.engine.openai_service)
        self.assertIsNotNone(self.engine.languagetool_service)
        
    @patch('core.correction_engine.OpenAIService')
    def test_correct_text_basic(self, mock_openai):
        """Test correzione testo base."""
        # Setup mock
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        mock_openai_instance.correct_text.return_value = "Testo corretto."
        
        engine = CorrectionEngine(self.settings)
        result = engine.correct_text("Testo da coregere.")
        
        self.assertEqual(result, "Testo corretto.")
        mock_openai_instance.correct_text.assert_called_once()
        
    @patch('core.correction_engine.OpenAIService')
    def test_correct_text_with_quality_check(self, mock_openai):
        """Test correzione con controllo qualità."""
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        mock_openai_instance.correct_text.return_value = "Testo corretto."
        
        engine = CorrectionEngine(self.settings)
        
        with patch.object(engine, 'quality_assurance') as mock_qa:
            mock_qa.assess_correction.return_value = QualityReport(
                overall_score=0.9,
                content_preservation=0.95,
                grammar_improvement=0.85,
                style_preservation=0.9,
                safety_score=0.95,
                issues=[],
                recommendations=[]
            )
            
            result = engine.correct_text_safe("Testo da coregere.")
            
            self.assertEqual(result.corrected_text, "Testo corretto.")
            self.assertTrue(result.is_safe)
            mock_qa.assess_correction.assert_called_once()
            
    def test_chunk_text(self):
        """Test chunking del testo."""
        long_text = "Paragrafo 1.\n\nParagrafo 2.\n\nParagrafo 3.\n\nParagrafo 4.\n\nParagrafo 5."
        
        chunks = self.engine.chunk_text(long_text, max_paragraphs=2)
        
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk.split('\n\n')), 2)
            
    def test_merge_corrections(self):
        """Test merge di correzioni multiple."""
        corrections = [
            ("Primo pezzo", "Primo pezzo corretto"),
            ("Secondo pezzo", "Secondo pezzo corretto"),
            ("Terzo pezzo", "Terzo pezzo corretto")
        ]
        
        result = self.engine.merge_corrections(corrections)
        expected = "Primo pezzo corretto\n\nSecondo pezzo corretto\n\nTerzo pezzo corretto"
        
        self.assertEqual(result, expected)
        
    @patch('core.correction_engine.OpenAIService')
    def test_error_handling_api_timeout(self, mock_openai):
        """Test gestione timeout API."""
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        mock_openai_instance.correct_text.side_effect = APITimeoutError("Timeout")
        
        engine = CorrectionEngine(self.settings)
        
        with self.assertRaises(APITimeoutError):
            engine.correct_text("Testo da correggere.")
            
    def test_pipeline_sequential_corrections(self):
        """Test pipeline sequenziale correzioni."""
        text = "Testo con errori di gramatica e ortografia."
        
        with patch.object(self.engine, 'spellcheck_service') as mock_spell, \
             patch.object(self.engine, 'languagetool_service') as mock_grammar, \
             patch.object(self.engine, 'openai_service') as mock_ai:
            
            mock_spell.correct.return_value = "Testo con errori di grammatica e ortografia."
            mock_grammar.correct.return_value = "Testo con errori di grammatica e ortografia."
            mock_ai.correct_text.return_value = "Testo senza errori di grammatica e ortografia."
            
            result = self.engine.correct_text_pipeline(text)
            
            self.assertEqual(result, "Testo senza errori di grammatica e ortografia.")
            
    def test_quality_threshold_rejection(self):
        """Test rifiuto correzione sotto soglia qualità."""
        with patch.object(self.engine, 'quality_assurance') as mock_qa:
            mock_qa.assess_correction.return_value = QualityReport(
                overall_score=0.5,  # Sotto soglia
                content_preservation=0.6,
                grammar_improvement=0.4,
                style_preservation=0.5,
                safety_score=0.6,
                issues=["Low quality correction"],
                recommendations=["Consider manual review"]
            )
            
            result = self.engine.correct_text_safe("Testo originale.")
            
            self.assertFalse(result.is_safe)
            self.assertEqual(result.corrected_text, "Testo originale.")  # Non modificato
            
    def test_batch_processing(self):
        """Test processamento batch di testi."""
        texts = [
            "Primo testo da coregere.",
            "Secondo testo da coregere.",
            "Terzo testo da coregere."
        ]
        
        with patch.object(self.engine, 'correct_text_safe') as mock_correct:
            mock_correct.return_value = Mock(
                corrected_text="Testo corretto.", 
                is_safe=True,
                quality_score=0.9
            )
            
            results = self.engine.process_batch(texts)
            
            self.assertEqual(len(results), 3)
            self.assertEqual(mock_correct.call_count, 3)
            
    def test_performance_metrics_tracking(self):
        """Test tracking metriche performance."""
        with patch.object(self.engine, 'correct_text') as mock_correct:
            mock_correct.return_value = "Testo corretto."
            
            # Reset metrics
            self.engine.reset_metrics()
            
            # Process some text
            self.engine.correct_text("Test text.")
            
            metrics = self.engine.get_performance_metrics()
            
            self.assertEqual(metrics['corrections_count'], 1)
            self.assertIn('total_processing_time', metrics)
            self.assertIn('average_processing_time', metrics)


class TestCorrectionEngineIntegration(unittest.TestCase):
    """Test di integrazione per CorrectionEngine con servizi reali."""
    
    def setUp(self):
        """Setup per test di integrazione."""
        self.settings = Settings()
        self.engine = CorrectionEngine(self.settings)
        
    def test_real_correction_simple(self):
        """Test correzione semplice con servizi reali."""
        text = "Questo è un testo con alcuni errori."
        
        # Questo test richiede configurazione reale dei servizi
        # Skippa se non in ambiente di integrazione
        if not os.getenv('INTEGRATION_TESTS'):
            self.skipTest("Integration tests not enabled")
            
        result = self.engine.correct_text_safe(text)
        
        self.assertIsNotNone(result)
        self.assertNotEqual(result.corrected_text, text)  # Deve essere cambiato
        
    def test_quality_assurance_real(self):
        """Test quality assurance con testo reale."""
        original = "Questo testo contiene errori di ortografia e gramatica."
        corrected = "Questo testo contiene errori di ortografia e grammatica."
        
        qa = QualityAssurance()
        report = qa.assess_correction(original, corrected)
        
        self.assertGreater(report.overall_score, 0.8)
        self.assertGreater(report.grammar_improvement, 0.7)
        

if __name__ == '__main__':
    # Run con diversi livelli di verbosity
    verbosity = 2 if '--verbose' in sys.argv else 1
    
    # Suite di test unitari
    unittest.main(verbosity=verbosity, exit=False)
    
    # Se abilitati, esegui anche test di integrazione
    if os.getenv('INTEGRATION_TESTS'):
        print("\n" + "="*50)
        print("RUNNING INTEGRATION TESTS")
        print("="*50)
        
        suite = unittest.TestLoader().loadTestsFromTestCase(TestCorrectionEngineIntegration)
        unittest.TextTestRunner(verbosity=verbosity).run(suite)
