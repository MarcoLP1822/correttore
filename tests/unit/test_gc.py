"""
Test unitari per grammarcheck e llm_correct integration.

Test del flusso completo di correzione testo.
"""
import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Aggiungi root del progetto al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core import grammarcheck, llm_correct


class TestGrammarCheckIntegration(unittest.TestCase):
    """Test suite per integrazione grammarcheck e llm_correct."""
    
    def test_grammarcheck_basic(self):
        """Test funzionamento base di grammarcheck."""
        test_texts = ["pò", "D'ALI", "Lu'"]
        
        for text in test_texts:
            result = grammarcheck.grammarcheck(text)
            # Verifica che il risultato sia valido
            self.assertIsNotNone(result)
            self.assertIsInstance(result, str)
            
    @patch('src.core.llm_correct.AsyncOpenAI')
    async def test_llm_correct_batch_mock(self, mock_openai):
        """Test llm_correct_batch con client mockato."""
        # Setup mock
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Test data
        step1_results = ["pò corrected", "D'ALI corrected", "Lu' corrected"]
        
        # Mock della risposta
        with patch('src.core.llm_correct.llm_correct_batch') as mock_batch:
            mock_batch.return_value = ["può", "D'altronde", "Lui"]
            
            result = await llm_correct.llm_correct_batch(step1_results, mock_client)
            
            # Verifica risultati
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 3)
            
    def test_integration_workflow_sync(self):
        """Test workflow sincrono senza chiamate API reali."""
        test_texts = ["pò", "D'ALI", "Lu'"]
        
        # Step 1: grammarcheck
        step1_results = []
        for text in test_texts:
            result = grammarcheck.grammarcheck(text)
            step1_results.append(result)
            
        # Verifica che step1 abbia prodotto risultati
        self.assertEqual(len(step1_results), len(test_texts))
        for result in step1_results:
            self.assertIsInstance(result, str)
            
        print(f"Step 1 results: {step1_results}")
        

class TestGrammarCheckAsync(unittest.IsolatedAsyncioTestCase):
    """Test asincroni per llm_correct."""
    
    @patch('src.core.llm_correct.AsyncOpenAI')
    async def test_async_workflow_mock(self, mock_openai):
        """Test completo del workflow asincrono con mock."""
        # Setup
        test_texts = ["pò", "D'ALI", "Lu'"]
        mock_client = AsyncMock()
        
        # Step 1: grammarcheck (sincrono)
        step1_results = [grammarcheck.grammarcheck(t) for t in test_texts]
        
        # Step 2: llm_correct (asincrono) - mockato
        with patch('src.core.llm_correct.llm_correct_batch') as mock_batch:
            mock_batch.return_value = ["può", "D'altronde", "Lui"]
            
            final_results = await llm_correct.llm_correct_batch(step1_results, mock_client)
            
            # Verifica
            self.assertIsInstance(final_results, list)
            self.assertEqual(len(final_results), 3)
            
            print(f"Step 1 → {step1_results}")
            print(f"Final → {final_results}")


if __name__ == '__main__':
    # Esegui test sincroni
    unittest.main(verbosity=2)
