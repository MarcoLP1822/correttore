"""
Test unitari per QualityAssurance.

Testa il sistema di valutazione qualità delle correzioni.
"""
import unittest
import sys
from pathlib import Path

# Aggiungi il path del progetto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.quality_assurance import QualityAssurance, QualityReport
from config.settings import Settings


class TestQualityAssurance(unittest.TestCase):
    """Test suite per QualityAssurance."""
    
    def setUp(self):
        """Setup per ogni test."""
        self.settings = Settings()
        self.qa = QualityAssurance(self.settings)
        
    def test_assess_correction_improvement(self):
        """Test valutazione correzione che migliora il testo."""
        original = "Questo testo contiene errori di ortografia e gramatica."
        corrected = "Questo testo contiene errori di ortografia e grammatica."
        
        report = self.qa.assess_correction(original, corrected)
        
        self.assertIsInstance(report, QualityReport)
        self.assertGreater(report.overall_score, 0.8)
        self.assertGreater(report.grammar_improvement, 0.7)
        self.assertGreater(report.content_preservation, 0.9)
        
    def test_assess_correction_degradation(self):
        """Test valutazione correzione che peggiora il testo."""
        original = "Questo è un testo corretto e ben scritto."
        corrected = "Qsto è txt crrt e bn scrt."
        
        report = self.qa.assess_correction(original, corrected)
        
        self.assertLess(report.overall_score, 0.5)
        self.assertLess(report.content_preservation, 0.7)
        self.assertLess(report.style_preservation, 0.6)
        
    def test_assess_correction_no_change(self):
        """Test valutazione quando non ci sono modifiche."""
        text = "Questo testo è già perfetto."
        
        report = self.qa.assess_correction(text, text)
        
        self.assertGreater(report.overall_score, 0.95)
        self.assertEqual(report.content_preservation, 1.0)
        self.assertEqual(report.style_preservation, 1.0)
        
    def test_content_preservation_calculation(self):
        """Test calcolo preservazione contenuto."""
        original = "Questa è una frase di test molto lunga con molte parole."
        
        # Caso: rimozione parole (perdita contenuto)
        truncated = "Questa è una frase di test."
        score_truncated = self.qa._calculate_content_preservation(original, truncated)
        self.assertLess(score_truncated, 0.8)
        
        # Caso: aggiunta parole (possibile miglioramento)
        expanded = "Questa è una frase di test molto lunga e dettagliata con molte parole."
        score_expanded = self.qa._calculate_content_preservation(original, expanded)
        self.assertGreater(score_expanded, 0.8)
        
    def test_grammar_improvement_detection(self):
        """Test rilevamento miglioramenti grammaticali."""
        # Caso: correzione errore grammaticale
        original = "Gli studenti à studiato molto."
        corrected = "Gli studenti hanno studiato molto."
        
        score = self.qa._calculate_grammar_improvement(original, corrected)
        self.assertGreater(score, 0.7)
        
        # Caso: introduzione errore grammaticale
        good_original = "Gli studenti hanno studiato molto."
        bad_corrected = "Gli studenti à studiato molto."
        
        score_bad = self.qa._calculate_grammar_improvement(good_original, bad_corrected)
        self.assertLess(score_bad, 0.5)
        
    def test_style_preservation(self):
        """Test preservazione dello stile."""
        original = "Marco disse: «Andiamo subito!» con tono deciso."
        
        # Buona preservazione: mantiene dialoghi e punteggiatura
        good_corrected = "Marco disse: «Andiamo immediatamente!» con tono deciso."
        score_good = self.qa._calculate_style_preservation(original, good_corrected)
        self.assertGreater(score_good, 0.8)
        
        # Cattiva preservazione: perde formato dialoghi
        bad_corrected = "Marco disse andiamo subito con tono deciso"
        score_bad = self.qa._calculate_style_preservation(original, bad_corrected)
        self.assertLess(score_bad, 0.6)
        
    def test_safety_score_calculation(self):
        """Test calcolo safety score."""
        original = "Il protagonista vive a Milano in via Roma 25."
        
        # Sicuro: mantiene info essenziali
        safe_corrected = "Il protagonista vive a Milano in via Roma 25."
        score_safe = self.qa._calculate_safety_score(original, safe_corrected)
        self.assertGreater(score_safe, 0.9)
        
        # Non sicuro: cambia info importanti
        unsafe_corrected = "Il protagonista vive a Napoli in via Garibaldi 12."
        score_unsafe = self.qa._calculate_safety_score(original, unsafe_corrected)
        self.assertLess(score_unsafe, 0.5)
        
    def test_detect_critical_issues(self):
        """Test rilevamento problemi critici."""
        original = "Capitolo 1\n\nEra una giornata splendida quando Marco decise di partire."
        
        # Caso: truncation
        truncated = "Capitolo 1\n\nEra una giornata splendida quando"
        issues = self.qa._detect_critical_issues(original, truncated)
        self.assertTrue(any("truncation" in issue.lower() for issue in issues))
        
        # Caso: duplicazione
        duplicated = "Capitolo 1\n\nEra una giornata splendida quando Marco decise di partire. Era una giornata splendida quando Marco decise di partire."
        issues = self.qa._detect_critical_issues(original, duplicated)
        self.assertTrue(any("duplicat" in issue.lower() for issue in issues))
        
    def test_assess_document_quality(self):
        """Test valutazione qualità documento completo."""
        paragraphs = [
            "Primo paragrafo del documento.",
            "Secondo paragrafo con contenuto interessante.",
            "Terzo paragrafo finale."
        ]
        corrections_count = 5
        
        report = self.qa.assess_document_quality(paragraphs, corrections_count)
        
        self.assertIsInstance(report, QualityReport)
        self.assertIsNotNone(report.overall_score)
        self.assertIsInstance(report.recommendations, list)
        
    def test_quality_thresholds(self):
        """Test soglie di qualità configurabili."""
        # Test con soglia alta
        self.qa.settings.quality_threshold = 0.95
        
        original = "Testo con piccol errore."
        corrected = "Testo con piccolo errore."
        
        report = self.qa.assess_correction(original, corrected)
        is_acceptable = self.qa.is_correction_acceptable(report)
        
        # Con soglia alta, piccole correzioni potrebbero non essere sufficienti
        self.assertIsInstance(is_acceptable, bool)
        
    def test_custom_weights(self):
        """Test pesi personalizzati per le metriche."""
        # Configura pesi custom
        original_weights = self.qa.weights.copy()
        
        # Priorità alta su safety
        self.qa.weights = {
            'content_preservation': 0.5,
            'grammar_improvement': 0.1,
            'style_preservation': 0.1,
            'safety_score': 0.3
        }
        
        original = "Nome: Mario Rossi, Password: 123456"
        corrected = "Nome: Luigi Verdi, Password: abcdef"  # Cambio info sensibili
        
        report = self.qa.assess_correction(original, corrected)
        
        # Con peso alto su safety, il score dovrebbe essere basso
        self.assertLess(report.overall_score, 0.6)
        
        # Ripristina pesi originali
        self.qa.weights = original_weights
        
    def test_readability_analysis(self):
        """Test analisi leggibilità testo italiano."""
        # Testo semplice
        simple_text = "Mario va a scuola. È contento. Studia molto."
        simple_score = self.qa._analyze_readability(simple_text)
        
        # Testo complesso
        complex_text = "L'epistemologia contemporanea, caratterizzata da una metodologia interdisciplinare che incorpora paradigmi ermeneutici postmoderni, evidenzia le contraddizioni intrinseche del paradigma cartesiano."
        complex_score = self.qa._analyze_readability(complex_text)
        
        # Il testo semplice dovrebbe essere più leggibile
        self.assertGreater(simple_score, complex_score)
        
    def test_language_specific_rules(self):
        """Test regole specifiche per l'italiano."""
        # Test apostrofi
        original = "Un'amica mi ha detto di venire."
        wrong = "Un amica mi ha detto di venire."
        
        report = self.qa.assess_correction(wrong, original)
        self.assertGreater(report.grammar_improvement, 0.7)
        
        # Test accenti
        original_accent = "Perché è importante."
        wrong_accent = "Perche e importante."
        
        report_accent = self.qa.assess_correction(wrong_accent, original_accent)
        self.assertGreater(report_accent.grammar_improvement, 0.7)
        

class TestQualityReportGeneration(unittest.TestCase):
    """Test per generazione report di qualità."""
    
    def setUp(self):
        """Setup per test report."""
        self.qa = QualityAssurance()
        
    def test_quality_report_structure(self):
        """Test struttura del report di qualità."""
        original = "Testo originale con errori."
        corrected = "Testo originale senza errori."
        
        report = self.qa.assess_correction(original, corrected)
        
        # Verifica struttura report
        self.assertIsInstance(report.overall_score, float)
        self.assertIsInstance(report.content_preservation, float)
        self.assertIsInstance(report.grammar_improvement, float)
        self.assertIsInstance(report.style_preservation, float)
        self.assertIsInstance(report.safety_score, float)
        self.assertIsInstance(report.issues, list)
        self.assertIsInstance(report.recommendations, list)
        
        # Verifica range valori
        self.assertGreaterEqual(report.overall_score, 0.0)
        self.assertLessEqual(report.overall_score, 1.0)
        
    def test_report_serialization(self):
        """Test serializzazione report."""
        original = "Test text."
        corrected = "Test text corrected."
        
        report = self.qa.assess_correction(original, corrected)
        
        # Test conversione a dict
        report_dict = report.to_dict()
        self.assertIsInstance(report_dict, dict)
        self.assertIn('overall_score', report_dict)
        
        # Test conversione a JSON
        import json
        json_str = json.dumps(report_dict)
        self.assertIsInstance(json_str, str)
        
        # Test ricostruzione da dict
        reconstructed = QualityReport.from_dict(report_dict)
        self.assertEqual(report.overall_score, reconstructed.overall_score)


if __name__ == '__main__':
    unittest.main(verbosity=2)
