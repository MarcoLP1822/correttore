# readability.py
"""
Modulo per il calcolo degli indici di leggibilità.
Implementa l'indice Gulpease, formula di leggibilità tarata sulla lingua italiana.

Riferimenti:
- Lucisano-Piemontese 1988: "GULPEASE: una formula per la predizione della 
  difficoltà dei testi in lingua italiana", in «Scuola e città», 3, 31, marzo 1988
"""

import re
from typing import Dict, Optional, Any


class ReadabilityAnalyzer:
    """Analizzatore di leggibilità per testi in italiano."""
    
    # Pattern per identificare la fine di una frase
    SENTENCE_END_RE = re.compile(
        r'[.!?]+(?:\s+|$)|'  # Punto, punto esclamativo, interrogativo
        r'[.!?]+["\'](?:\s+|$)'  # Seguiti da virgolette
    )
    
    # Scala di interpretazione Gulpease
    GULPEASE_SCALE = {
        'licenza_elementare': {
            'molto_facile': (80, 100),
            'facile': (60, 79),
            'difficile': (40, 59),
            'molto_difficile': (0, 39)
        },
        'licenza_media': {
            'molto_facile': (70, 100),
            'facile': (50, 69),
            'difficile': (30, 49),
            'molto_difficile': (0, 29)
        },
        'diploma_superiore': {
            'molto_facile': (60, 100),
            'facile': (40, 59),
            'difficile': (20, 39),
            'molto_difficile': (0, 19)
        }
    }
    
    def __init__(self):
        """Inizializza l'analizzatore."""
        pass
    
    def count_letters(self, text: str) -> int:
        """
        Conta le lettere nel testo (solo caratteri alfabetici).
        
        Args:
            text: Il testo da analizzare
            
        Returns:
            Numero di lettere nel testo
        """
        return sum(1 for c in text if c.isalpha())
    
    def count_words(self, text: str) -> int:
        """
        Conta le parole nel testo.
        
        Args:
            text: Il testo da analizzare
            
        Returns:
            Numero di parole nel testo
        """
        # Rimuove punteggiatura e conta le parole
        words = re.findall(r'\b\w+\b', text)
        return len(words)
    
    def count_sentences(self, text: str) -> int:
        """
        Conta le frasi nel testo.
        
        Args:
            text: Il testo da analizzare
            
        Returns:
            Numero di frasi nel testo
        """
        # Trova tutti i punti di fine frase
        sentences = self.SENTENCE_END_RE.split(text)
        # Filtra frasi vuote e conta
        sentences = [s.strip() for s in sentences if s.strip()]
        return max(1, len(sentences))  # Almeno 1 frase
    
    def calculate_gulpease(self, text: str) -> Optional[float]:
        """
        Calcola l'indice Gulpease per il testo fornito.
        
        Formula: Gulpease = 89 - (LP/10) + (FR*3)
        dove:
        - LP = (lettere * 100) / totale parole
        - FR = (frasi * 100) / totale parole
        
        Args:
            text: Il testo da analizzare
            
        Returns:
            Valore dell'indice Gulpease (0-100), o None se il testo è vuoto
        """
        if not text or not text.strip():
            return None
        
        letters = self.count_letters(text)
        words = self.count_words(text)
        sentences = self.count_sentences(text)
        
        if words == 0:
            return None
        
        # Calcola LP (lunghezza parole)
        lp = (letters * 100) / words
        
        # Calcola FR (frequenza frasi)
        fr = (sentences * 100) / words
        
        # Formula Gulpease
        gulpease = 89 - (lp / 10) + (fr * 3)
        
        # Limita il valore tra 0 e 100
        return max(0, min(100, gulpease))
    
    def interpret_gulpease(self, score: float, education_level: str = 'licenza_media') -> str:
        """
        Interpreta il punteggio Gulpease secondo il livello di scolarizzazione.
        
        Args:
            score: Il punteggio Gulpease (0-100)
            education_level: Livello di scolarizzazione del lettore
                           ('licenza_elementare', 'licenza_media', 'diploma_superiore')
            
        Returns:
            Descrizione della difficoltà del testo
        """
        if education_level not in self.GULPEASE_SCALE:
            education_level = 'licenza_media'
        
        scale = self.GULPEASE_SCALE[education_level]
        
        for difficulty, (min_score, max_score) in scale.items():
            if min_score <= score <= max_score:
                return difficulty.replace('_', ' ').title()
        
        return "Non classificato"
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analizza il testo e restituisce statistiche complete di leggibilità.
        
        Args:
            text: Il testo da analizzare
            
        Returns:
            Dizionario con statistiche dettagliate:
            - letters: numero di lettere
            - words: numero di parole
            - sentences: numero di frasi
            - gulpease: indice Gulpease
            - avg_word_length: lunghezza media delle parole in lettere
            - avg_sentence_length: lunghezza media delle frasi in parole
            - difficulty: interpretazione per diversi livelli di scolarizzazione
        """
        if not text or not text.strip():
            return {
                'letters': 0,
                'words': 0,
                'sentences': 0,
                'gulpease': None,
                'avg_word_length': 0,
                'avg_sentence_length': 0,
                'difficulty': {}
            }
        
        letters = self.count_letters(text)
        words = self.count_words(text)
        sentences = self.count_sentences(text)
        gulpease = self.calculate_gulpease(text)
        
        result = {
            'letters': letters,
            'words': words,
            'sentences': sentences,
            'gulpease': round(gulpease, 2) if gulpease is not None else None,
            'avg_word_length': round(letters / words, 2) if words > 0 else 0,
            'avg_sentence_length': round(words / sentences, 2) if sentences > 0 else 0,
            'difficulty': {}
        }
        
        # Aggiungi interpretazione per tutti i livelli di scolarizzazione
        if gulpease is not None:
            for level in ['licenza_elementare', 'licenza_media', 'diploma_superiore']:
                result['difficulty'][level] = self.interpret_gulpease(gulpease, level)
        
        return result
    
    def format_report(self, stats: Dict[str, Any]) -> str:
        """
        Formatta le statistiche in un report leggibile.
        
        Args:
            stats: Dizionario con le statistiche da formattare
            
        Returns:
            Report formattato come stringa
        """
        if stats['gulpease'] is None:
            return "Testo non analizzabile (troppo breve o vuoto)."
        
        report = []
        report.append("=" * 60)
        report.append("ANALISI DI LEGGIBILITÀ - INDICE GULPEASE")
        report.append("=" * 60)
        report.append("")
        report.append(f"Lettere:               {stats['letters']:,}")
        report.append(f"Parole:                {stats['words']:,}")
        report.append(f"Frasi:                 {stats['sentences']:,}")
        report.append(f"Lunghezza media parola: {stats['avg_word_length']:.2f} lettere")
        report.append(f"Lunghezza media frase:  {stats['avg_sentence_length']:.2f} parole")
        report.append("")
        report.append(f"INDICE GULPEASE:       {stats['gulpease']:.2f}")
        report.append("")
        report.append("INTERPRETAZIONE SECONDO SCOLARIZZAZIONE:")
        report.append("-" * 60)
        
        education_labels = {
            'licenza_elementare': 'Licenza elementare',
            'licenza_media': 'Licenza media',
            'diploma_superiore': 'Diploma superiore'
        }
        
        for level, label in education_labels.items():
            difficulty = stats['difficulty'].get(level, 'N/A')
            report.append(f"  {label:20} → {difficulty}")
        
        report.append("=" * 60)
        
        return "\n".join(report)


# Funzioni di utilità per uso rapido
def calculate_gulpease(text: str) -> Optional[float]:
    """
    Calcola rapidamente l'indice Gulpease di un testo.
    
    Args:
        text: Il testo da analizzare
        
    Returns:
        Indice Gulpease o None se il testo è vuoto
    """
    analyzer = ReadabilityAnalyzer()
    return analyzer.calculate_gulpease(text)


def analyze_readability(text: str) -> Dict[str, Any]:
    """
    Analizza rapidamente la leggibilità di un testo.
    
    Args:
        text: Il testo da analizzare
        
    Returns:
        Dizionario con statistiche complete
    """
    analyzer = ReadabilityAnalyzer()
    return analyzer.analyze(text)


def print_readability_report(text: str) -> None:
    """
    Stampa un report di leggibilità formattato.
    
    Args:
        text: Il testo da analizzare
    """
    analyzer = ReadabilityAnalyzer()
    stats = analyzer.analyze(text)
    print(analyzer.format_report(stats))


if __name__ == "__main__":
    # Testo di esempio per testing
    test_text = """
    L'indice Gulpease è una formula di leggibilità tarata sulla lingua italiana.
    La formula è stata determinata verificando con una serie di test la reale
    comprensibilità di un corpus di testi. La verifica è stata fatta su tre categorie
    di lettore. Accanto alla determinazione della formula è stata definita una scala
    d'interpretazione dei valori restituiti dalla formula stessa.
    """
    
    print_readability_report(test_text)
