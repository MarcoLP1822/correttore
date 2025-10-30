# readability.py
"""
Modulo per il calcolo degli indici di leggibilità.
Implementa l'indice Gulpease, formula di leggibilità tarata sulla lingua italiana.

Riferimenti:
- Lucisano-Piemontese 1988: "GULPEASE: una formula per la predizione della 
  difficoltà dei testi in lingua italiana", in «Scuola e città», 3, 31, marzo 1988
"""

import re
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass, field


@dataclass
class SentenceReadability:
    """Analisi leggibilità singola frase"""
    text: str
    gulpease_score: float
    difficulty_level: str  # facile/media/difficile
    word_count: int
    letter_count: int
    sentence_index: int
    words_not_in_vdb: List[str] = field(default_factory=list)
    technical_terms: List[str] = field(default_factory=list)
    vocabulary_breakdown: Dict[str, int] = field(default_factory=dict)  # Fase 4: fondamentale, alto_uso, alta_disponibilita, fuori_vdb
    
    def get_difficulty_color(self) -> str:
        """Restituisce il colore associato al livello di difficoltà"""
        if self.gulpease_score >= 80:
            return '#2d5016'  # Verde scuro - molto facile
        elif self.gulpease_score >= 60:
            return '#4a7c2c'  # Verde chiaro - facile
        elif self.gulpease_score >= 40:
            return '#f39c12'  # Giallo - difficile
        else:
            return '#c0392b'  # Rosso - molto difficile
    
    def get_difficulty_emoji(self) -> str:
        """Restituisce l'emoji associata al livello di difficoltà"""
        if self.gulpease_score >= 80:
            return '📗'  # Verde scuro
        elif self.gulpease_score >= 60:
            return '📘'  # Verde chiaro
        elif self.gulpease_score >= 40:
            return '📙'  # Giallo
        else:
            return '📕'  # Rosso


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
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Divide il testo in frasi individuali.
        
        Args:
            text: Il testo da dividere
            
        Returns:
            Lista di frasi
        """
        # Gestisce abbreviazioni comuni
        text_temp = text
        abbreviations = ['dott.', 'prof.', 'sig.', 'sig.ra', 'dr.', 'ecc.', 'es.', 'pag.', 'tel.', 'n.', 'art.', 'cfr.']
        
        # Proteggi le abbreviazioni temporaneamente
        for i, abbr in enumerate(abbreviations):
            text_temp = text_temp.replace(abbr, f'ABBR{i}ABBR')
        
        # Dividi in frasi usando il pattern di regex
        sentences = self.SENTENCE_END_RE.split(text_temp)
        
        # Ripristina le abbreviazioni e filtra frasi vuote
        result = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # Ripristina abbreviazioni
                for i, abbr in enumerate(abbreviations):
                    sentence = sentence.replace(f'ABBR{i}ABBR', abbr)
                result.append(sentence)
        
        return result if result else [text]
    
    def analyze_by_sentence(self, text: str, vocabulary_service=None) -> List[SentenceReadability]:
        """
        Analizza il testo frase per frase calcolando il GULPEASE di ogni frase.
        
        Args:
            text: Il testo da analizzare
            vocabulary_service: Servizio opzionale per verificare parole nel VdB
            
        Returns:
            Lista di SentenceReadability con analisi per ogni frase
        """
        if not text or not text.strip():
            return []
        
        sentences = self.split_into_sentences(text)
        results = []
        
        for idx, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            
            # Calcola statistiche per la frase
            letters = self.count_letters(sentence)
            words = self.count_words(sentence)
            gulpease = self.calculate_gulpease(sentence)
            
            if gulpease is None:
                continue
            
            # Determina difficoltà
            difficulty = self.interpret_gulpease(gulpease, 'licenza_media')
            
            # Analisi vocabolario avanzata (Fase 4)
            words_not_in_vdb = []
            technical_terms = []
            vocab_breakdown = {'fondamentale': 0, 'alto_uso': 0, 'alta_disponibilita': 0, 'fuori_vdb': 0}
            
            if vocabulary_service:
                word_list = re.findall(r'\b\w+\b', sentence.lower())
                
                for word in word_list:
                    if not vocabulary_service.is_in_vocabulary(word):
                        words_not_in_vdb.append(word)
                        vocab_breakdown['fuori_vdb'] += 1
                    else:
                        # Ottieni livello parola
                        level = vocabulary_service.get_word_level(word)
                        if level in vocab_breakdown:
                            vocab_breakdown[level] += 1
                
                # Classifica termini tecnici
                technical_terms = vocabulary_service.classify_technical_terms(word_list)
            
            sentence_analysis = SentenceReadability(
                text=sentence,
                gulpease_score=round(gulpease, 2),
                difficulty_level=difficulty,
                word_count=words,
                letter_count=letters,
                sentence_index=idx + 1,
                words_not_in_vdb=words_not_in_vdb,
                technical_terms=technical_terms,
                vocabulary_breakdown=vocab_breakdown
            )
            
            results.append(sentence_analysis)
        
        return results
    
    def get_difficult_sentences(self, sentences: List[SentenceReadability], threshold: float = 60) -> List[SentenceReadability]:
        """
        Filtra le frasi difficili da leggere.
        
        Args:
            sentences: Lista di SentenceReadability da filtrare
            threshold: Soglia Gulpease sotto la quale una frase è considerata difficile
            
        Returns:
            Lista di frasi difficili
        """
        return [s for s in sentences if s.gulpease_score < threshold]
    
    def get_sentence_statistics(self, sentences: List[SentenceReadability]) -> Dict[str, Any]:
        """
        Calcola statistiche aggregate sulle frasi analizzate.
        
        Args:
            sentences: Lista di SentenceReadability
            
        Returns:
            Dizionario con statistiche
        """
        if not sentences:
            return {
                'total_sentences': 0,
                'avg_gulpease': 0,
                'easy_sentences': 0,
                'medium_sentences': 0,
                'difficult_sentences': 0,
                'very_difficult_sentences': 0,
                'avg_words_per_sentence': 0,
                'distribution': {}
            }
        
        easy = sum(1 for s in sentences if s.gulpease_score >= 60)
        difficult = sum(1 for s in sentences if 40 <= s.gulpease_score < 60)
        very_difficult = sum(1 for s in sentences if s.gulpease_score < 40)
        
        avg_gulpease = sum(s.gulpease_score for s in sentences) / len(sentences)
        avg_words = sum(s.word_count for s in sentences) / len(sentences)
        
        return {
            'total_sentences': len(sentences),
            'avg_gulpease': round(avg_gulpease, 2),
            'easy_sentences': easy,
            'medium_sentences': 0,  # Non usato nella scala standard
            'difficult_sentences': difficult,
            'very_difficult_sentences': very_difficult,
            'avg_words_per_sentence': round(avg_words, 2),
            'distribution': {
                'very_easy': sum(1 for s in sentences if s.gulpease_score >= 80),
                'easy': sum(1 for s in sentences if 60 <= s.gulpease_score < 80),
                'difficult': sum(1 for s in sentences if 40 <= s.gulpease_score < 60),
                'very_difficult': sum(1 for s in sentences if s.gulpease_score < 40)
            }
        }
    
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


def main_cli():
    """Entry point CLI per analisi leggibilità"""
    import sys
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(
        description="Analizza la leggibilità di documenti usando l'indice Gulpease"
    )
    parser.add_argument('file', help='File da analizzare (.txt o .docx)')
    parser.add_argument('--export', help='Esporta report in file')
    
    args = parser.parse_args()
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"❌ File non trovato: {file_path}")
        sys.exit(1)
    
    # Estrai testo
    if file_path.suffix == '.docx':
        try:
            from docx import Document
            doc = Document(str(file_path))
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        except Exception as e:
            print(f"❌ Errore leggendo .docx: {e}")
            sys.exit(1)
    else:
        try:
            text = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"❌ Errore leggendo file: {e}")
            sys.exit(1)
    
    # Analizza
    analyzer = ReadabilityAnalyzer()
    stats = analyzer.analyze(text)
    report = analyzer.format_report(stats)
    
    # Output
    print(report)
    
    if args.export:
        Path(args.export).write_text(report, encoding='utf-8')
        print(f"\n✓ Report esportato in: {args.export}")


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
