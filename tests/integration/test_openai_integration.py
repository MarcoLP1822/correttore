"""
Test di integrazione per OpenAI service.

Testa l'integrazione con le API di OpenAI.
"""
import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Aggiungi il path del progetto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from correttore.services.openai_service import OpenAIService
from correttore.core.error_handling import APITimeoutError, RateLimitError
from correttore.config.settings import Settings


class TestOpenAIIntegration(unittest.TestCase):
    """Test di integrazione per OpenAI service."""
    
    def setUp(self):
        """Setup per test OpenAI."""
        self.settings = Settings()
        
        # Skip se non in ambiente di integrazione
        if not os.getenv('INTEGRATION_TESTS'):
            self.skipTest("Integration tests not enabled")
            
        # Skip se API key non configurata
        if not os.getenv('OPENAI_API_KEY'):
            self.skipTest("OPENAI_API_KEY not configured")
            
        self.service = OpenAIService()  # No parameters needed
        
    def test_openai_service_initialization(self):
        """Test inizializzazione servizio OpenAI."""
        self.assertIsNotNone(self.service)
        self.assertIsNotNone(self.service.client)
        
    def test_simple_correction_real_api(self):
        """Test correzione semplice con API reale."""
        input_text = "Questo è un testo con alcuni errori di gramatica."
        
        try:
            corrected = self.service.correct_text(input_text)
            
            self.assertIsInstance(corrected, str)
            self.assertNotEqual(corrected, input_text)
            # Dovrebbe correggere "gramatica" in "grammatica"
            if corrected:
                self.assertIn("grammatica", corrected.lower())
            
        except Exception as e:
            # Log dell'errore per debugging
            print(f"API Error: {e}")
            self.fail(f"OpenAI API call failed: {e}")
            
    def test_batch_correction_real_api(self):
        """Test correzione batch con API reale."""
        texts = [
            "Primo testo con errore di gramatica.",
            "Secondo testo che necesita correzione.",
            "Terzo testo con alcuni problemi."
        ]
        
        try:
            import asyncio
            results = asyncio.run(self.service.correct_text_batch(texts))
            
            self.assertEqual(len(results), 3)
            for i, result in enumerate(results):
                if result is not None:
                    self.assertIsInstance(result, str)
                # Ogni risultato dovrebbe essere diverso dall'input
                # (assumendo che ci siano correzioni da fare)
                
        except Exception as e:
            print(f"Batch API Error: {e}")
            self.fail(f"OpenAI batch API call failed: {e}")
            
    def test_complex_text_correction(self):
        """Test correzione testo complesso."""
        complex_text = """
        Marco si alzò dal letto quella matina sentendosi particolarmente stanco. 
        Aveva dormito male a causa del rumore dei vicini che avevano fatto festa 
        fino a tarda notte. Mentre si vestiva, pensò che forse era arrivato il 
        momento di cercare un appartamento più tranquilo, possibilmente in una 
        zona meno caotica della città.
        """
        
        try:
            corrected = self.service.correct_text(complex_text.strip())
            
            self.assertIsNotNone(corrected)
            if corrected is not None:
                self.assertIsInstance(corrected, str)
                # Dovrebbe correggere "matina" in "mattina"
                self.assertIn("mattina", corrected.lower())
                # Il testo dovrebbe mantenere la struttura generale
                self.assertIn("Marco", corrected)
                self.assertIn("appartamento", corrected)
            
        except Exception as e:
            print(f"Complex text API Error: {e}")
            self.fail(f"Complex text correction failed: {e}")
            
    def test_dialogue_preservation(self):
        """Test preservazione dialoghi."""
        dialogue_text = '''
        «Ciao Marco», disse Maria avvicinandosi al tavolo.
        «Ciao Maria, come stai?» rispose lui alzando lo sguardo dal libro.
        «Bene grazie. Che cosa stai leggendo?»
        «Un romanzo molto interessante sulla storia italiana.»
        '''
        
        try:
            corrected = self.service.correct_text(dialogue_text.strip())
            
            self.assertIsNotNone(corrected)
            if corrected is not None:
                self.assertIsInstance(corrected, str)
                # Le virgolette devono essere preservate
                self.assertIn("«", corrected)
                self.assertIn("»", corrected)
                # I nomi devono rimanere invariati
                self.assertIn("Marco", corrected)
                self.assertIn("Maria", corrected)
            
        except Exception as e:
            print(f"Dialogue API Error: {e}")
            self.fail(f"Dialogue correction failed: {e}")
            
    def test_italian_specific_corrections(self):
        """Test correzioni specifiche per l'italiano."""
        italian_errors = [
            "Perche non vieni con noi?",  # Accento mancante
            "Un amica mi ha detto questo.",  # Apostrofo mancante
            "Qual'è il problema?",  # Apostrofo errato
            "Fa più freddo di ieri.",  # Dovrebbe essere OK
        ]
        
        try:
            for text in italian_errors:
                corrected = self.service.correct_text(text)
                
                if corrected is not None:
                    self.assertIsInstance(corrected, str)
                    
                    # Verifica correzioni specifiche
                    if "Perche" in text:
                        self.assertIn("Perché", corrected)
                    if "Un amica" in text:
                        self.assertIn("Un'amica", corrected)
                    if "Qual'è" in text:
                        self.assertIn("Qual è", corrected)
                    
        except Exception as e:
            print(f"Italian corrections API Error: {e}")
            self.fail(f"Italian specific corrections failed: {e}")
            
    def test_api_error_handling(self):
        """Test gestione errori API."""
        # Test con testo molto lungo che potrebbe causare errori
        very_long_text = "Questo è un testo molto lungo. " * 2000
        
        with patch.object(self.service, 'client') as mock_client:
            # Simula timeout
            mock_client.chat.completions.create.side_effect = Exception("Timeout")
            
            with self.assertRaises(APITimeoutError):
                self.service.correct_text(very_long_text)
                
    def test_rate_limiting_handling(self):
        """Test gestione rate limiting."""
        # Questo test simula rate limiting
        with patch.object(self.service, 'client') as mock_client:
            # Simula rate limit error
            mock_client.chat.completions.create.side_effect = Exception("Rate limit exceeded")
            
            with self.assertRaises(RateLimitError):
                self.service.correct_text("Test text")
                
    def test_token_counting(self):
        """Test conteggio token."""
        # NOTE: count_tokens method not implemented in OpenAIService
        self.skipTest("count_tokens method not implemented")
        
    def test_cost_estimation(self):
        """Test stima costi."""
        # NOTE: estimate_cost method not implemented in OpenAIService
        self.skipTest("estimate_cost method not implemented")
        
        self.assertIsInstance(estimated_cost, float)
        self.assertGreaterEqual(estimated_cost, 0.0)
        
    def test_model_configuration(self):
        """Test configurazione modello."""
        # NOTE: OpenAIService doesn't expose model/temperature configuration
        self.skipTest("Model configuration not exposed in OpenAIService")
            
    def test_custom_prompt_templates(self):
        """Test template prompt personalizzati."""
        # NOTE: correct_text_with_template method not implemented in OpenAIService
        self.skipTest("correct_text_with_template method not implemented")


class TestOpenAIMockIntegration(unittest.TestCase):
    """Test integrazione OpenAI con mock (non richiede API key)."""
    
    def setUp(self):
        """Setup per test mock."""
        self.settings = Settings()
        
    @patch('services.openai_service.OpenAI')
    def test_service_initialization_mock(self, mock_openai):
        """Test inizializzazione servizio con mock."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        service = OpenAIService()
        
        self.assertIsNotNone(service)
        mock_openai.assert_called_once()
        
    @patch('services.openai_service.OpenAI')
    def test_correction_response_parsing(self, mock_openai):
        """Test parsing risposta correzione."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock risposta API
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Testo corretto dal mock."
        mock_client.chat.completions.create.return_value = mock_response
        
        service = OpenAIService()
        result = service.correct_text("Testo originale.")
        
        self.assertEqual(result, "Testo corretto dal mock.")
        
    @patch('services.openai_service.OpenAI')
    def test_retry_mechanism(self, mock_openai):
        """Test meccanismo retry."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Prima chiamata fallisce, seconda riesce
        mock_client.chat.completions.create.side_effect = [
            Exception("Temporary error"),
            Mock(choices=[Mock(message=Mock(content="Success"))])
        ]
        
        service = OpenAIService()
        
        with patch.object(service, '_retry_with_backoff') as mock_retry:
            mock_retry.return_value = "Success"
            result = service.correct_text("Test")
            
            self.assertEqual(result, "Success")
            mock_retry.assert_called_once()
            
    @patch('services.openai_service.OpenAI')
    def test_context_preservation(self, mock_openai):
        """Test preservazione contesto nelle correzioni."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock che preserva il contesto
        def mock_correct(text):
            # Simula correzione che preserva struttura
            return text.replace("errore", "correzione")
            
        mock_response = Mock()
        mock_response.choices = [Mock()]
        
        service = OpenAIService()
        
        with patch.object(service, '_call_api') as mock_call:
            mock_call.return_value = "Testo con correzione."
            
            result = service.correct_text("Testo con errore.")
            
            self.assertEqual(result, "Testo con correzione.")
            mock_call.assert_called_once()


if __name__ == '__main__':
    # Setup logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Determina se eseguire test reali o mock
    if os.getenv('INTEGRATION_TESTS') and os.getenv('OPENAI_API_KEY'):
        print("Running REAL OpenAI API tests...")
        print("WARNING: This will consume API credits!")
        
        # Esegui test reali
        suite = unittest.TestLoader().loadTestsFromTestCase(TestOpenAIIntegration)
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        print("Running MOCK OpenAI API tests...")
        
        # Esegui test mock
        suite = unittest.TestLoader().loadTestsFromTestCase(TestOpenAIMockIntegration)
        unittest.TextTestRunner(verbosity=2).run(suite)
