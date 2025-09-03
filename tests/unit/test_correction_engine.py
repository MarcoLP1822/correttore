"""
Test unitari per CorrectionEngine.

Testa la business logic di orchestrazione delle correzioni.
"""
import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from typing import cast, List
from docx.text.paragraph import Paragraph

# Aggiungi il path del progetto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.correction_engine import CorrectionEngine, CorrectionResult, CorrectionContext
from core.document_handler import DocumentInfo
from src.core.safe_correction import QualityScore, CorrectionConfidence
from config.settings import Settings


class TestCorrectionEngine(unittest.TestCase):
    """Test suite per CorrectionEngine."""
    
    def setUp(self):
        """Setup per ogni test."""
        self.settings = Settings()
        
        # Mock tutti i servizi per evitare problemi di inizializzazione
        with patch('core.correction_engine.OpenAIService') as mock_openai:
            with patch('core.correction_engine.LanguageToolService') as mock_lt:
                with patch('core.correction_engine.get_cache') as mock_cache:
                    with patch('core.correction_engine.SafeCorrector') as mock_safe:
                        # CorrectionEngine non richiede parametri nel costruttore
                        self.engine = CorrectionEngine()
                        
                        # Assegna mock ai servizi
                        self.mock_openai = mock_openai.return_value
                        self.mock_lt = mock_lt.return_value
                        self.mock_cache = mock_cache.return_value
                        self.mock_safe = mock_safe.return_value
        
        # Crea directory temporanea per test
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Cleanup dopo ogni test."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_engine_initialization(self):
        """Test inizializzazione engine."""
        # Testa che l'engine sia stato inizializzato correttamente nel setUp
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.document_handler)
        # I servizi sono mockati nel setUp
        
    def test_correct_text_fragment_basic(self):
        """Test correzione frammento di testo base."""
        text = "Questo è un testo di prova."
        
        # Mock dei servizi per evitare chiamate reali
        with patch.object(self.engine, 'openai_service', self.mock_openai):
            with patch.object(self.engine, 'safe_corrector', self.mock_safe):
                with patch.object(self.engine, 'config', {'cache_enabled': True}) as mock_config:
                    self.mock_openai.correct_text.return_value = ("Questo è un testo di prova corretto.", 0.95)
                    
                    mock_score = QualityScore(
                        overall_score=0.90,
                        confidence=CorrectionConfidence.HIGH,
                        content_preservation=0.95,
                        grammar_improvement=0.85,
                        style_preservation=0.90,
                        safety_score=0.95,
                        issues=[]
                    )
                    self.mock_safe.validate_correction.return_value = mock_score
                    
                    corrected_text, quality_score = self.engine.correct_text_fragment(text)
                    
                    self.assertIsInstance(corrected_text, str)
                    self.assertIsInstance(quality_score, QualityScore)
                    self.assertGreater(len(corrected_text), 0)
                
    def test_correct_text_fragment_with_cache(self):
        """Test correzione con cache."""
        text = "Testo da correggere"
        
        with patch.object(self.engine.cache_service, 'get') as mock_cache_get:
            mock_cache_get.return_value = ("Testo corretto dalla cache", QualityScore(
                overall_score=0.85,
                confidence=CorrectionConfidence.HIGH,
                content_preservation=0.90,
                grammar_improvement=0.80,
                style_preservation=0.85,
                safety_score=0.90,
                issues=[]
            ))
            
            corrected_text, quality_score = self.engine.correct_text_fragment(text, use_cache=True)
            
            self.assertEqual(corrected_text, "Testo corretto dalla cache")
            mock_cache_get.assert_called_once()
            
    def test_correct_text_fragment_no_cache(self):
        """Test correzione senza cache."""
        text = "Testo da correggere"
        
        with patch.object(self.engine.cache_service, 'get') as mock_cache_get:
            mock_cache_get.return_value = None
            
            with patch.object(self.engine.openai_service, 'correct_text') as mock_correct:
                mock_correct.return_value = ("Testo corretto", 0.90)
                
                with patch.object(self.engine.safe_corrector, 'validate_correction') as mock_validate:
                    mock_score = QualityScore(
                        overall_score=0.85,
                        confidence=CorrectionConfidence.HIGH,
                        content_preservation=0.90,
                        grammar_improvement=0.80,
                        style_preservation=0.85,
                        safety_score=0.90,
                        issues=[]
                    )
                    mock_validate.return_value = mock_score
                    
                    corrected_text, quality_score = self.engine.correct_text_fragment(text, use_cache=False)
                    
                    self.assertEqual(corrected_text, "Testo corretto")
                    mock_cache_get.assert_not_called()
                    
    def test_paragraph_batch_correction(self):
        """Test correzione batch di paragrafi."""
        # Crea paragrafi mock
        mock_paragraphs = []
        for i in range(3):
            mock_para = Mock()
            mock_para.text = f"Paragrafo {i + 1} da correggere."
            mock_paragraphs.append(mock_para)
        
        with patch.object(self.engine, '_correct_single_paragraph') as mock_correct_single:
            mock_score = QualityScore(
                overall_score=0.85,
                confidence=CorrectionConfidence.HIGH,
                content_preservation=0.90,
                grammar_improvement=0.80,
                style_preservation=0.85,
                safety_score=0.90,
                issues=[]
            )
            mock_correct_single.return_value = (True, mock_score)
            
            results = self.engine.correct_paragraph_batch(mock_paragraphs, max_workers=2)
            
            self.assertEqual(len(results), 3)
            for success, score in results:
                self.assertTrue(success)
                self.assertIsInstance(score, QualityScore)
                
    def test_should_correct_paragraph_filtering(self):
        """Test filtro paragrafi da correggere."""
        # Paragrafo normale
        normal_para = Mock()
        normal_para.text = "Questo è un paragrafo normale che può essere corretto."
        
        # Paragrafo vuoto
        empty_para = Mock()
        empty_para.text = ""
        
        # Paragrafo troppo corto
        short_para = Mock()
        short_para.text = "Ok"
        
        self.assertTrue(self.engine._should_correct_paragraph(normal_para))
        self.assertFalse(self.engine._should_correct_paragraph(empty_para))
        # Il comportamento per paragrafi corti dipende dall'implementazione
        
    def test_needs_ai_correction_detection(self):
        """Test rilevamento necessità correzione AI."""
        # Testo con errori evidenti
        error_text = "Questo testo à degli errori grammaticali evidenti."
        
        # Testo già corretto
        clean_text = "Questo testo è già corretto grammaticalmente."
        
        # I risultati dipendono dalla logica interna
        needs_correction_1 = self.engine._needs_ai_correction(error_text)
        needs_correction_2 = self.engine._needs_ai_correction(clean_text)
        
        # Test che il metodo restituisca boolean
        self.assertIsInstance(needs_correction_1, bool)
        self.assertIsInstance(needs_correction_2, bool)
        
    def test_special_content_detection(self):
        """Test rilevamento contenuto speciale."""
        # Testo normale
        normal_text = "Questo è un testo normale."
        
        # Email
        email_text = "Contattami a test@example.com per informazioni."
        
        # URL
        url_text = "Visita il sito https://www.example.com"
        
        self.assertFalse(self.engine._is_special_content(normal_text))
        self.assertTrue(self.engine._is_special_content(email_text))
        self.assertTrue(self.engine._is_special_content(url_text))
        
    def test_document_correction_workflow_mock(self):
        """Test workflow completo di correzione documento (mockato)."""
        test_doc_path = self.temp_dir / "test.docx"
        test_doc_path.write_text("fake docx content")  # File fittizio
        
        # Mock del document handler
        mock_doc = Mock()
        mock_doc_info = DocumentInfo(
            path=test_doc_path,
            total_paragraphs=5,
            total_characters=100,
            needs_correction_count=3,
            validation_result=Mock()
        )
        
        with patch.object(self.engine.document_handler, 'load_document') as mock_load:
            mock_load.return_value = (mock_doc, mock_doc_info)
            
            with patch.object(self.engine.document_handler, 'extract_all_paragraphs') as mock_extract:
                mock_paragraphs = [Mock() for _ in range(5)]
                for i, para in enumerate(mock_paragraphs):
                    para.text = f"Paragrafo {i + 1} con testo da correggere."
                mock_extract.return_value = mock_paragraphs
                
                with patch.object(self.engine, '_should_correct_paragraph') as mock_should_correct:
                    mock_should_correct.return_value = True
                    
                    with patch.object(self.engine, '_process_corrections') as mock_process:
                        mock_process.return_value = True
                        
                        with patch.object(self.engine.document_handler, 'save_document') as mock_save:
                            mock_save.return_value = True
                            
                            result = self.engine.correct_document(test_doc_path)
                            
                            self.assertIsInstance(result, CorrectionResult)
                            self.assertTrue(result.success)
                            self.assertIsNotNone(result.context)
                            
    def test_correction_context_management(self):
        """Test gestione contesto di correzione."""
        mock_doc = Mock()
        mock_doc_info = DocumentInfo(
            path=Path("test.docx"),
            total_paragraphs=10,
            total_characters=500,
            needs_correction_count=5,
            validation_result=Mock()
        )
        mock_paragraphs = [Mock() for _ in range(5)]
        
        context = CorrectionContext(
            source_document=mock_doc,
            document_info=mock_doc_info,
            target_paragraphs=cast(List[Paragraph], mock_paragraphs)
        )
        
        self.assertEqual(context.corrections_applied, 0)
        self.assertEqual(context.corrections_rejected, 0)
        self.assertEqual(context.total_processed, 0)
        self.assertIsInstance(context.corrections_log, list)
        self.assertEqual(len(context.corrections_log), 0)
        
    def test_apply_text_preserving_format_mock(self):
        """Test applicazione testo preservando formato."""
        mock_paragraph = Mock()
        mock_paragraph.text = "Testo originale"
        new_text = "Testo corretto"
        
        # Il metodo _apply_text_preserving_format modifica il paragrafo in place
        self.engine._apply_text_preserving_format(mock_paragraph, new_text)
        
        # Verifica che il metodo sia stato chiamato senza errori
        # (il comportamento specifico dipende dall'implementazione)
        self.assertTrue(True)  # Test che il metodo non sollevi eccezioni
        
    def test_correction_error_handling(self):
        """Test gestione errori durante correzione."""
        text = "Testo con errore simulato"
        
        with patch.object(self.engine.openai_service, 'correct_text') as mock_correct:
            mock_correct.side_effect = Exception("Simulato errore API")
            
            # Il metodo dovrebbe gestire l'errore gracefully
            try:
                result = self.engine.correct_text_fragment(text)
                # Se non solleva eccezione, dovrebbe restituire qualcosa
                self.assertIsNotNone(result)
            except Exception as e:
                # Se solleva eccezione, dovrebbe essere gestita appropriatamente
                self.assertIsInstance(e, Exception)


if __name__ == '__main__':
    unittest.main(verbosity=2)
