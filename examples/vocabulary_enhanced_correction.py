"""
Esempio di integrazione del Vocabolario di Base nel flusso di correzione.
Dimostra come usare il vocabolario per migliorare la qualità della correzione.
"""

from typing import List, Dict
from services.vocabulary_service import get_vocabulary_service
from src.utils.readability import ReadabilityAnalyzer


class VocabularyEnhancedCorrector:
    """
    Esempio di correttore potenziato con analisi vocabolario.
    Può essere integrato nel CorrectionEngine esistente.
    """
    
    def __init__(self):
        self.vocab_service = get_vocabulary_service()
        self.readability_analyzer = ReadabilityAnalyzer(use_vocabulary=True)
    
    def validate_correction(self, original_word: str, suggested_word: str) -> Dict:
        """
        Valida una correzione suggerita usando il vocabolario.
        
        Args:
            original_word: Parola originale (potenzialmente errata)
            suggested_word: Parola suggerita come correzione
            
        Returns:
            Dict con valutazione della correzione
        """
        original_in_vocab = self.vocab_service.is_in_vocabulary(original_word)
        suggested_in_vocab = self.vocab_service.is_in_vocabulary(suggested_word)
        
        # Se originale è nel vocabolario, probabile falso positivo
        if original_in_vocab and not suggested_in_vocab:
            return {
                'recommendation': 'reject',
                'confidence': 0.8,
                'reason': 'Parola originale nel vocabolario, suggerimento no'
            }
        
        # Se suggerimento è nel vocabolario, probabilmente corretto
        if suggested_in_vocab and not original_in_vocab:
            return {
                'recommendation': 'accept',
                'confidence': 0.9,
                'reason': 'Suggerimento nel vocabolario, originale no'
            }
        
        # Entrambi nel vocabolario o entrambi fuori
        return {
            'recommendation': 'review',
            'confidence': 0.5,
            'reason': 'Necessaria revisione manuale'
        }
    
    def analyze_document_readability(self, text: str) -> Dict:
        """
        Analisi completa leggibilità documento con vocabolario.
        
        Args:
            text: Testo del documento
            
        Returns:
            Report completo con metriche GULPEASE e NVdB
        """
        analysis = self.readability_analyzer.analyze(text)
        
        report = {
            'gulpease_score': analysis.get('gulpease'),
            'word_count': analysis.get('words'),
            'sentence_count': analysis.get('sentences'),
            'readability_level': analysis.get('difficulty', {}).get('licenza_media', 'N/A')
        }
        
        # Aggiungi metriche vocabolario
        if analysis.get('vocabulary'):
            vocab = analysis['vocabulary']
            report['vocabulary_coverage'] = vocab['coverage_percentage']
            report['lexical_quality'] = vocab['lexical_quality']
            report['difficult_words_count'] = vocab['difficult_words_count']
            report['difficult_words'] = vocab['difficult_words_sample'][:20]
            
            # Flag di allerta
            report['alerts'] = []
            if vocab['coverage_percentage'] < 80:
                report['alerts'].append({
                    'type': 'low_vocabulary_coverage',
                    'message': f"Copertura vocabolario bassa ({vocab['coverage_percentage']:.1f}%)",
                    'suggestion': 'Considerare semplificazione del lessico'
                })
            
            if vocab['difficult_words_count'] > 50:
                report['alerts'].append({
                    'type': 'many_difficult_words',
                    'message': f"{vocab['difficult_words_count']} parole tecniche/specialistiche",
                    'suggestion': 'Valutare se il target può comprendere tutti i termini'
                })
        
        return report
    
    def suggest_simplifications(self, text: str) -> List[Dict]:
        """
        Suggerisce semplificazioni per migliorare l'accessibilità.
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Lista di suggerimenti per semplificare il testo
        """
        stats = self.vocab_service.analyze_text(text)
        suggestions = []
        
        # Se copertura < 85%, suggerisci revisione
        if stats.percentage_in_nvdb < 85:
            suggestions.append({
                'priority': 'high',
                'type': 'lexical_complexity',
                'message': f'Il testo usa molte parole fuori dal vocabolario di base ({stats.not_in_nvdb} parole)',
                'action': 'Considera di semplificare o spiegare i termini tecnici',
                'difficult_words': stats.difficult_words[:10]
            })
        
        return suggestions
    
    def compare_versions(self, original: str, corrected: str) -> Dict:
        """
        Confronta qualità lessicale tra originale e versione corretta.
        
        Args:
            original: Testo originale
            corrected: Testo dopo correzione
            
        Returns:
            Report comparativo
        """
        stats_original = self.vocab_service.analyze_text(original)
        stats_corrected = self.vocab_service.analyze_text(corrected)
        
        coverage_diff = stats_corrected.percentage_in_nvdb - stats_original.percentage_in_nvdb
        difficult_diff = len(stats_original.difficult_words) - len(stats_corrected.difficult_words)
        
        return {
            'original_coverage': stats_original.percentage_in_nvdb,
            'corrected_coverage': stats_corrected.percentage_in_nvdb,
            'coverage_improvement': coverage_diff,
            'difficult_words_removed': difficult_diff,
            'assessment': self._assess_improvement(coverage_diff, difficult_diff)
        }
    
    def _assess_improvement(self, coverage_diff: float, difficult_diff: int) -> str:
        """Valuta il miglioramento della correzione"""
        if coverage_diff > 5 or difficult_diff > 5:
            return 'Miglioramento significativo della leggibilità'
        elif coverage_diff > 0 or difficult_diff > 0:
            return 'Leggero miglioramento della leggibilità'
        elif coverage_diff == 0 and difficult_diff == 0:
            return 'Nessun impatto sulla leggibilità'
        else:
            return 'Attenzione: la correzione potrebbe aver ridotto la leggibilità'


def demo():
    """Dimostrazione uso del correttore potenziato"""
    corrector = VocabularyEnhancedCorrector()
    
    # Test 1: Validazione correzione
    print("\n" + "=" * 70)
    print("TEST 1: Validazione Correzione")
    print("=" * 70)
    
    test_cases = [
        ("casa", "kasa"),  # Originale corretto, suggerimento sbagliato
        ("algoritmo", "algoritmi"),  # Entrambi tecnici
        ("xyzabc", "esempio"),  # Originale sbagliato, suggerimento ok
    ]
    
    for original, suggested in test_cases:
        result = corrector.validate_correction(original, suggested)
        print(f"\n'{original}' → '{suggested}'")
        print(f"  Raccomandazione: {result['recommendation']}")
        print(f"  Confidenza: {result['confidence']}")
        print(f"  Motivo: {result['reason']}")
    
    # Test 2: Analisi documento
    print("\n" + "=" * 70)
    print("TEST 2: Analisi Documento")
    print("=" * 70)
    
    test_doc = """
    La casa è grande e bella. Il sole brilla nel cielo azzurro.
    I bambini giocano felici nel parco con i loro amici.
    """
    
    report = corrector.analyze_document_readability(test_doc)
    print(f"\nGulpease: {report['gulpease_score']}")
    print(f"Parole: {report['word_count']}")
    print(f"Copertura NVdB: {report.get('vocabulary_coverage', 'N/A')}%")
    print(f"Qualità lessicale: {report.get('lexical_quality', 'N/A')}")
    
    if report.get('alerts'):
        print("\n⚠ Avvisi:")
        for alert in report['alerts']:
            print(f"  - {alert['message']}")
            print(f"    {alert['suggestion']}")
    
    # Test 3: Confronto versioni
    print("\n" + "=" * 70)
    print("TEST 3: Confronto Versioni")
    print("=" * 70)
    
    original_text = "L'implementazione dell'algoritmo richiede un'analisi approfondita."
    corrected_text = "La realizzazione del metodo richiede uno studio attento."
    
    comparison = corrector.compare_versions(original_text, corrected_text)
    print(f"\nCopertura originale: {comparison['original_coverage']:.1f}%")
    print(f"Copertura corretta: {comparison['corrected_coverage']:.1f}%")
    print(f"Miglioramento: {comparison['coverage_improvement']:+.1f}%")
    print(f"Parole difficili rimosse: {comparison['difficult_words_removed']}")
    print(f"Valutazione: {comparison['assessment']}")


if __name__ == "__main__":
    demo()
