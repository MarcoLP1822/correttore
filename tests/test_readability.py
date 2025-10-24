"""
Test per il modulo di analisi della leggibilità (indice Gulpease).
"""

import pytest
from correttore.utils.readability import ReadabilityAnalyzer, calculate_gulpease, analyze_readability


class TestReadabilityAnalyzer:
    """Test per la classe ReadabilityAnalyzer."""
    
    def setup_method(self):
        """Inizializza l'analyzer per ogni test."""
        self.analyzer = ReadabilityAnalyzer()
    
    def test_count_letters(self):
        """Test conteggio lettere."""
        text = "Ciao, mondo! 123"
        assert self.analyzer.count_letters(text) == 9  # "Ciaomondo" (senza virgola/spazi)
        
        text = "Test123"
        assert self.analyzer.count_letters(text) == 4  # "Test"
    
    def test_count_words(self):
        """Test conteggio parole."""
        text = "Questa è una frase di prova."
        assert self.analyzer.count_words(text) == 6
        
        text = "Una parola"
        assert self.analyzer.count_words(text) == 2
        
        text = ""
        assert self.analyzer.count_words(text) == 0
    
    def test_count_sentences(self):
        """Test conteggio frasi."""
        text = "Prima frase. Seconda frase! Terza frase?"
        assert self.analyzer.count_sentences(text) == 3
        
        text = "Una sola frase."
        assert self.analyzer.count_sentences(text) == 1
        
        # Almeno 1 frase anche senza punteggiatura
        text = "Testo senza punto"
        assert self.analyzer.count_sentences(text) >= 1
    
    def test_calculate_gulpease_simple(self):
        """Test calcolo Gulpease su testo semplice."""
        # Testo molto semplice: parole corte, frasi brevi
        text = "Il cane è buono. Il gatto è bello."
        gulpease = self.analyzer.calculate_gulpease(text)
        
        assert gulpease is not None
        assert 0 <= gulpease <= 100
        # Testo semplice dovrebbe avere punteggio alto
        assert gulpease > 50
    
    def test_calculate_gulpease_complex(self):
        """Test calcolo Gulpease su testo complesso."""
        # Testo complesso: parole lunghe, frasi lunghe
        text = """
        L'implementazione dell'algoritmo necessita di considerazioni 
        metodologiche particolarmente sofisticate per garantire 
        l'ottimizzazione delle performance computazionali.
        """
        gulpease = self.analyzer.calculate_gulpease(text)
        
        assert gulpease is not None
        assert 0 <= gulpease <= 100
        # Testo complesso dovrebbe avere punteggio più basso
        assert gulpease < 70
    
    def test_calculate_gulpease_empty(self):
        """Test calcolo Gulpease su testo vuoto."""
        assert self.analyzer.calculate_gulpease("") is None
        assert self.analyzer.calculate_gulpease("   ") is None
    
    def test_calculate_gulpease_reference_text(self):
        """Test su testo di riferimento dall'articolo Gulpease."""
        text = """
        L'indice Gulpease è una formula di leggibilità tarata sulla lingua italiana.
        La formula è stata determinata verificando con una serie di test la reale
        comprensibilità di un corpus di testi. La verifica è stata fatta su tre categorie
        di lettore. Accanto alla determinazione della formula è stata definita una scala
        d'interpretazione dei valori restituiti dalla formula stessa.
        """
        gulpease = self.analyzer.calculate_gulpease(text)
        
        assert gulpease is not None
        assert 0 <= gulpease <= 100
        # Testo tecnico ma non eccessivamente difficile
        assert 40 <= gulpease <= 70
    
    def test_interpret_gulpease(self):
        """Test interpretazione punteggio Gulpease."""
        # Punteggio alto = facile
        interpretation = self.analyzer.interpret_gulpease(80, 'licenza_elementare')
        assert 'Facile' in interpretation or 'facile' in interpretation.lower()
        
        # Punteggio basso = difficile
        interpretation = self.analyzer.interpret_gulpease(20, 'diploma_superiore')
        assert 'Difficile' in interpretation or 'difficile' in interpretation.lower()
    
    def test_interpret_gulpease_different_levels(self):
        """Test interpretazione per diversi livelli di scolarizzazione."""
        score = 50
        
        elem = self.analyzer.interpret_gulpease(score, 'licenza_elementare')
        media = self.analyzer.interpret_gulpease(score, 'licenza_media')
        diploma = self.analyzer.interpret_gulpease(score, 'diploma_superiore')
        
        # Tutti dovrebbero restituire una valutazione
        assert elem
        assert media
        assert diploma
        
        # La difficoltà dovrebbe essere relativa al livello
        # (un testo facile per diplomati può essere difficile per elementari)
    
    def test_analyze_complete(self):
        """Test analisi completa."""
        text = "Questo è un test. Ha due frasi."
        stats = self.analyzer.analyze(text)
        
        assert 'letters' in stats
        assert 'words' in stats
        assert 'sentences' in stats
        assert 'gulpease' in stats
        assert 'avg_word_length' in stats
        assert 'avg_sentence_length' in stats
        assert 'difficulty' in stats
        
        assert stats['words'] > 0
        assert stats['sentences'] == 2
        assert stats['gulpease'] is not None
        
        # Verifica interpretazioni
        assert 'licenza_elementare' in stats['difficulty']
        assert 'licenza_media' in stats['difficulty']
        assert 'diploma_superiore' in stats['difficulty']
    
    def test_analyze_empty(self):
        """Test analisi su testo vuoto."""
        stats = self.analyzer.analyze("")
        
        assert stats['letters'] == 0
        assert stats['words'] == 0
        assert stats['sentences'] == 0
        assert stats['gulpease'] is None
    
    def test_format_report(self):
        """Test formattazione report."""
        text = "Il gatto dorme. Il cane gioca."
        stats = self.analyzer.analyze(text)
        report = self.analyzer.format_report(stats)
        
        assert isinstance(report, str)
        assert len(report) > 0
        assert 'GULPEASE' in report
        assert 'Lettere' in report or 'lettere' in report.lower()
        assert 'Parole' in report or 'parole' in report.lower()
    
    def test_format_report_empty(self):
        """Test formattazione report per testo vuoto."""
        stats = self.analyzer.analyze("")
        report = self.analyzer.format_report(stats)
        
        assert isinstance(report, str)
        assert len(report) > 0


class TestUtilityFunctions:
    """Test per le funzioni di utilità."""
    
    def test_calculate_gulpease_function(self):
        """Test funzione rapida calculate_gulpease."""
        text = "Test di leggibilità."
        gulpease = calculate_gulpease(text)
        
        assert gulpease is not None
        assert 0 <= gulpease <= 100
    
    def test_analyze_readability_function(self):
        """Test funzione rapida analyze_readability."""
        text = "Test di analisi rapida."
        stats = analyze_readability(text)
        
        assert 'gulpease' in stats
        assert stats['gulpease'] is not None


class TestEdgeCases:
    """Test per casi limite."""
    
    def setup_method(self):
        """Inizializza l'analyzer per ogni test."""
        self.analyzer = ReadabilityAnalyzer()
    
    def test_single_word(self):
        """Test con una sola parola."""
        gulpease = self.analyzer.calculate_gulpease("Ciao")
        assert gulpease is not None
    
    def test_very_long_sentence(self):
        """Test con frase molto lunga."""
        # Frase lunga senza punteggiatura intermedia
        text = " ".join(["parola"] * 100)
        gulpease = self.analyzer.calculate_gulpease(text)
        
        assert gulpease is not None
        # Frasi lunghe dovrebbero abbassare il punteggio
        assert gulpease < 80
    
    def test_very_short_sentences(self):
        """Test con frasi molto corte."""
        text = "Io. Tu. Lui. Lei. Noi. Voi."
        gulpease = self.analyzer.calculate_gulpease(text)
        
        assert gulpease is not None
        # Frasi corte dovrebbero alzare il punteggio
        assert gulpease > 60
    
    def test_numbers_and_symbols(self):
        """Test con numeri e simboli."""
        text = "Il prezzo è 100€. L'anno è 2024. Il codice è ABC123."
        gulpease = self.analyzer.calculate_gulpease(text)
        
        assert gulpease is not None
        assert 0 <= gulpease <= 100
    
    def test_mixed_punctuation(self):
        """Test con punteggiatura mista."""
        text = "Davvero? Sì! No. Forse... Probabilmente."
        stats = self.analyzer.analyze(text)
        
        assert stats['gulpease'] is not None
        assert stats['sentences'] > 0


class TestGulpeaseFormula:
    """Test specifici per verificare la formula Gulpease."""
    
    def setup_method(self):
        """Inizializza l'analyzer."""
        self.analyzer = ReadabilityAnalyzer()
    
    def test_formula_components(self):
        """Test che verifica i componenti della formula."""
        text = "Il sole splende luminoso nel cielo azzurro."
        
        letters = self.analyzer.count_letters(text)
        words = self.analyzer.count_words(text)
        sentences = self.analyzer.count_sentences(text)
        
        # Calcola manualmente
        lp = (letters * 100) / words
        fr = (sentences * 100) / words
        expected_gulpease = 89 - (lp / 10) + (fr * 3)
        
        # Confronta con il calcolo automatico
        calculated_gulpease = self.analyzer.calculate_gulpease(text)
        
        assert calculated_gulpease is not None
        assert abs(calculated_gulpease - expected_gulpease) < 0.01
    
    def test_gulpease_range(self):
        """Test che il Gulpease rimanga nel range 0-100."""
        # Testo estremamente semplice
        simple_text = ". ".join(["A"] * 50)
        simple_gulpease = self.analyzer.calculate_gulpease(simple_text)
        
        # Testo estremamente complesso
        complex_words = ["complessificazione"] * 20
        complex_text = " ".join(complex_words) + "."
        complex_gulpease = self.analyzer.calculate_gulpease(complex_text)
        
        assert simple_gulpease is not None
        assert complex_gulpease is not None
        assert 0 <= simple_gulpease <= 100
        assert 0 <= complex_gulpease <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
