"""
Language Classifier Module
==========================

Classificatore intelligente per rilevare e gestire contenuti multilingua.
Implementa pattern matching avanzato e analisi statistica per identificare
citazioni in lingue straniere, nomi propri e termini tecnici.

Architecture: Clean separation of concerns
- LanguagePattern: Pattern definitions per lingua
- LanguageClassifier: Core classification engine  
- ForeignWordFilter: Integration with correction system
"""

import re
import logging
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

logger = logging.getLogger(__name__)


class Language(Enum):
    """Lingue supportate dal classificatore."""
    ITALIAN = "it"
    LATIN = "la"
    ENGLISH = "en"
    FRENCH = "fr"
    GERMAN = "de"
    GREEK = "el"
    UNKNOWN = "unknown"


@dataclass
class LanguagePattern:
    """Pattern per identificare una lingua specifica."""
    language: Language
    common_words: Set[str]
    suffixes: Set[str]
    prefixes: Set[str]
    special_chars: Set[str]
    min_confidence: float = 0.6


class LanguagePatterns:
    """Database di pattern linguistici."""
    
    LATIN = LanguagePattern(
        language=Language.LATIN,
        common_words={
            # Parole latine comuni
            'cum', 'vel', 'ut', 'et', 'est', 'sunt', 'quod', 'qui', 'quae', 'quibus',
            'ad', 'in', 'de', 'ex', 'per', 'pro', 'sine', 'inter', 'contra', 'super',
            # Terminazioni tipiche
            'deo', 'dei', 'deus', 'domini', 'dominus',
            # Verbi comuni
            'dicimus', 'trahit', 'sunt', 'est', 'sit', 'fuit', 'erit',
            # Sostantivi comuni
            'populus', 'civium', 'legis', 'legislator', 'imperium', 'papatus',
            'potestatum', 'originem', 'finibus', 'iustitiam', 'felicitatem',
            # Aggettivi
            'aeternam', 'temporalem', 'legitimer', 'praefiniti',
            # Altri termini frequenti
            'sive', 'igitur', 'scilicet', 'capitulo', 'efficiens', 'valientior',
            'pars', 'electionem', 'suam', 'voluntatem', 'generaliter', 'expressam',
            'iubens', 'aliquid', 'actus', 'humanos', 'civiles', 'poena',
            'duobus', 'veritate', 'aristotelis', 'politicis', 'perducat',
            'pontifex', 'doctrinam', 'evangelicam', 'divisio', 'homines',
            'dignitate', 'hominis', 'oratio', 'secretum',
            # AGGIUNTE dal documento analizzato
            'eius', 'corpus', 'civitas', 'princeps', 'ius', 'lex', 'rex',
        },
        suffixes={'um', 'us', 'is', 'em', 'am', 'ae', 'as', 'os', 'ibus', 'arum', 'orum', 'orum', 'em', 'ens'},
        prefixes=set(),
        special_chars=set(),
        min_confidence=0.35  # Soglia più bassa per latino (exact match = 0.4)
    )
    
    ENGLISH = LanguagePattern(
        language=Language.ENGLISH,
        common_words={
            # Articoli e pronomi
            'the', 'a', 'an', 'this', 'that', 'these', 'those',
            # Verbi ausiliari
            'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did',
            'can', 'could', 'will', 'would', 'shall', 'should', 'may', 'might', 'must',
            # Preposizioni comuni
            'of', 'in', 'on', 'at', 'to', 'for', 'with', 'from', 'by',
            # Congiunzioni
            'and', 'or', 'but', 'if', 'when', 'where', 'while',
            # Parole comuni
            'right', 'wrong', 'between', 'justice', 'power', 'make', 'lose',
            # Termini tecnici/business
            'governance', 'checks', 'balances', 'asset', 'welfare', 'check',
            'their', 'names', 'system',
        },
        suffixes={'ing', 'ed', 'ly', 'ness', 'ment', 'tion', 'sion', 's'},
        prefixes={'un', 'in', 're', 'pre', 'post'},
        special_chars=set(),
        min_confidence=0.4  # Soglia più bassa per termini tecnici isolati
    )
    
    FRENCH = LanguagePattern(
        language=Language.FRENCH,
        common_words={
            # Articoli
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de',
            # Preposizioni
            'à', 'au', 'aux', 'dans', 'pour', 'par', 'avec', 'sans', 'sur',
            # Pronomi
            'qui', 'que', 'dont', 'où',
            # Verbi comuni
            'est', 'sont', 'être', 'avoir',
        },
        suffixes={'tion', 'ment', 'eur', 'ité', 'age'},
        prefixes=set(),
        special_chars={'é', 'è', 'ê', 'à', 'ù', 'ô', 'î', 'ç', 'û', 'ë', 'ï', 'œ'}
    )
    
    GERMAN = LanguagePattern(
        language=Language.GERMAN,
        common_words={
            # Articoli
            'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einem', 'eines',
            # Preposizioni
            'für', 'mit', 'von', 'zu', 'in', 'an', 'auf', 'bei',
            # Congiunzioni
            'und', 'oder', 'aber', 'wenn', 'dass', 'weil',
            # Parole comuni
            'ist', 'sind', 'sein', 'war', 'waren',
        },
        suffixes={'ung', 'keit', 'heit', 'schaft', 'tum'},
        prefixes={'ge', 'be', 'er', 'ver', 'zer', 'ent'},
        special_chars={'ä', 'ö', 'ü', 'ß'}
    )
    
    GREEK = LanguagePattern(
        language=Language.GREEK,
        common_words={'zōon', 'politikon', 'polis', 'demos', 'kratos'},
        suffixes={'on', 'os', 'is'},
        prefixes=set(),
        special_chars={'ō', 'ē'}
    )


class LanguageClassifier:
    """
    Classificatore intelligente per rilevare la lingua di un testo.
    
    Utilizza analisi statistica basata su:
    - Pattern matching con dizionari linguistici
    - Analisi morfologica (suffissi/prefissi)
    - Caratteri speciali tipici
    - Contesto (parole circostanti)
    """
    
    def __init__(self):
        self.patterns = {
            Language.LATIN: LanguagePatterns.LATIN,
            Language.ENGLISH: LanguagePatterns.ENGLISH,
            Language.FRENCH: LanguagePatterns.FRENCH,
            Language.GERMAN: LanguagePatterns.GERMAN,
            Language.GREEK: LanguagePatterns.GREEK,
        }
    
    @lru_cache(maxsize=10000)
    def _classify_word_cached(self, word: str, context_hash: Optional[int] = None) -> Tuple[Language, float]:
        """
        Versione cached della classificazione parola.
        Usa context_hash invece di context string per rendere hashable.
        
        Args:
            word: Parola da classificare (lowercase)
            context_hash: Hash del contesto per cache key
            
        Returns:
            Tupla (lingua, confidenza)
        """
        # Ricostruisce contesto da hash (solo per compatibilità, in realtà non usato)
        return self._classify_word_impl(word, None)
    
    def classify_word(self, word: str, context: Optional[str] = None) -> Tuple[Language, float]:
        """
        Classifica una singola parola (con caching).
        
        Args:
            word: Parola da classificare
            context: Contesto circostante (opzionale, migliora accuratezza)
            
        Returns:
            Tupla (lingua, confidenza) dove confidenza è 0.0-1.0
        """
        word_lower = word.lower().strip()
        
        if not word_lower:
            return Language.UNKNOWN, 0.0
        
        # Calcola hash del contesto per cache
        context_hash = hash(context) if context else None
        
        # Prima prova con cache
        try:
            return self._classify_word_cached(word_lower, context_hash)
        except:
            # Fallback a implementazione diretta
            return self._classify_word_impl(word_lower, context)
    
    def _classify_word_impl(self, word_lower: str, context: Optional[str] = None) -> Tuple[Language, float]:
        """
        Implementazione reale della classificazione.
        Separata per permettere caching.
        
        Args:
            word_lower: Parola già lowercased
            context: Contesto opzionale
            
        Returns:
            Tupla (lingua, confidenza)
        """
        
        # Analizza contesto se disponibile
        context_scores = {}
        if context:
            context_lower = context.lower()
            for lang, pattern in self.patterns.items():
                context_words = set(context_lower.split())
                matches = context_words & pattern.common_words
                context_scores[lang] = len(matches) / max(len(context_words), 1)
        
        # Calcola punteggi per ogni lingua
        scores: Dict[Language, float] = {}
        
        for lang, pattern in self.patterns.items():
            score = 0.0
            factors = 0
            
            # 1. Match esatto con parole comuni (peso: 40%)
            if word_lower in pattern.common_words:
                score += 0.4
                factors += 1
            
            # 2. Suffissi (peso: 30%)
            suffix_match = False
            for suffix in pattern.suffixes:
                if len(word_lower) > len(suffix) + 2 and word_lower.endswith(suffix):
                    score += 0.3
                    suffix_match = True
                    factors += 1
                    break
            
            # 3. Prefissi (peso: 15%)
            if not suffix_match:  # Evita doppio conteggio
                for prefix in pattern.prefixes:
                    if len(word_lower) > len(prefix) + 2 and word_lower.startswith(prefix):
                        score += 0.15
                        factors += 1
                        break
            
            # 4. Caratteri speciali (peso: 15%)
            word_chars = set(word_lower)
            if pattern.special_chars & word_chars:
                score += 0.15
                factors += 1
            
            # 5. Bonus contesto (peso: 20% se disponibile)
            if lang in context_scores and context_scores[lang] > 0:
                score += context_scores[lang] * 0.2
                factors += 1
            
            # Normalizza score
            if factors > 0:
                scores[lang] = score
        
        # Trova lingua con score più alto
        if not scores:
            return Language.UNKNOWN, 0.0
        
        best_lang = max(scores.keys(), key=lambda lang: scores[lang])
        confidence = scores[best_lang]
        
        # Se confidenza troppo bassa, marca come UNKNOWN
        if confidence < self.patterns[best_lang].min_confidence:
            return Language.UNKNOWN, confidence
        
        return best_lang, confidence
    
    def classify_phrase(self, phrase: str) -> Tuple[Language, float]:
        """
        Classifica una frase intera analizzando tutte le parole.
        
        Args:
            phrase: Frase da classificare
            
        Returns:
            Tupla (lingua, confidenza media)
        """
        words = phrase.split()
        if not words:
            return Language.UNKNOWN, 0.0
        
        # Classifica ogni parola con contesto
        classifications = []
        for i, word in enumerate(words):
            # Estrai contesto (3 parole prima + 3 dopo)
            context_start = max(0, i - 3)
            context_end = min(len(words), i + 4)
            context = ' '.join(words[context_start:context_end])
            
            lang, conf = self.classify_word(word, context)
            if lang != Language.UNKNOWN:
                classifications.append((lang, conf))
        
        if not classifications:
            return Language.UNKNOWN, 0.0
        
        # Trova lingua predominante
        lang_counts: Dict[Language, List[float]] = {}
        for lang, conf in classifications:
            if lang not in lang_counts:
                lang_counts[lang] = []
            lang_counts[lang].append(conf)
        
        # Calcola score pesato per lingua
        best_lang = max(lang_counts, key=lambda l: sum(lang_counts[l]) / len(lang_counts[l]))
        avg_confidence = sum(lang_counts[best_lang]) / len(lang_counts[best_lang])
        
        return best_lang, avg_confidence


class ForeignWordFilter:
    """
    Filtro intelligente per gestire parole straniere nelle correzioni.
    
    Si integra con DocumentAnalyzer per:
    - Verificare parole nel Vocabolario di Base italiano
    - Riclassificare errori di ortografia come parole straniere
    - Spostare citazioni nella categoria "Lingue"
    - Mantenere nomi propri nella categoria corretta
    """
    
    def __init__(self):
        self.classifier = LanguageClassifier()
        
        # Prova a caricare VocabularyService
        self.vocabulary_service = None
        try:
            from correttore.services.vocabulary_service import VocabularyService
            self.vocabulary_service = VocabularyService()
            logger.info("✅ VocabularyService integrato in ForeignWordFilter")
        except Exception as e:
            logger.warning(f"⚠️  VocabularyService non disponibile: {e}")
        
        # Carica liste da file esterni
        self.known_proper_nouns = self._load_proper_nouns()
        self.technical_terms = self._load_technical_terms()
    
    def _load_proper_nouns(self) -> set:
        """Carica nomi propri da file esterno"""
        base_set = {
            'poddighe', 'westfalia', 'jean', 'bodin', 'weber', 'arendt',
            'dugin', 'bauman', 'hardt', 'negri', 'beck', 'rousseau',
            'hobbes', 'locke', 'foucault', 'deleuze', 'aristotele',
            'petrarca', 'dante', 'boccaccio', 'machiavelli',
            # Aggiunte per testi politici/filosofici
            'marsilio', 'padova', 'marsilius', 'tomaso', 'aquino',
            'westfaliano', 'trump', 'biden', 'kant', 'hegel', 'marx',
        }
        
        try:
            from pathlib import Path
            file_path = Path(__file__).parent.parent.parent.parent / "data" / "vocabolario" / "nomi_propri_comuni.txt"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip().lower()
                        if line and not line.startswith('#'):
                            base_set.add(line)
                logger.info(f"📚 Caricati {len(base_set)} nomi propri")
        except Exception as e:
            logger.debug(f"Impossibile caricare nomi propri da file: {e}")
        
        return base_set
    
    def _load_technical_terms(self) -> set:
        """Carica termini tecnici da file esterno"""
        base_set = {
            'governance', 'asset', 'welfare', 'accountability', 'check',
            'balance', 'intelligence', 'privacy', 'copyright', 'royalty',
            'transfer', 'pricing', 'patent', 'flat', 'tax', 'smart',
            'contract', 'wallet', 'exchange', 'blockchain', 'crypto',
            'gamer', 'streamer', 'creator', 'multiplayer', 'esport',
            # Aggiunte per testi accademici/politici
            'trumpismo', 'populismo', 'sovranismo', 'globalismo',
        }
        
        try:
            from pathlib import Path
            file_path = Path(__file__).parent.parent.parent.parent / "data" / "vocabolario" / "termini_tecnici.txt"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip().lower()
                        if line and not line.startswith('#'):
                            base_set.add(line)
                logger.info(f"📚 Caricati {len(base_set)} termini tecnici")
        except Exception as e:
            logger.debug(f"Impossibile caricare termini tecnici da file: {e}")
        
        return base_set
    
    def is_proper_noun(self, word: str) -> bool:
        """Verifica se una parola è un nome proprio."""
        word_lower = word.lower()
        
        # Nome proprio se:
        # 1. In lista conosciuta
        if word_lower in self.known_proper_nouns:
            return True
        
        # 2. Inizia con maiuscola e non è inizio frase (gestito dal chiamante)
        if word[0].isupper() and len(word) > 1:
            return True
        
        return False
    
    def is_technical_term(self, word: str) -> bool:
        """Verifica se è un termine tecnico accettato."""
        return word.lower() in self.technical_terms
    
    def should_filter_error(
        self, 
        word: str, 
        context: Optional[str] = None,
        rule_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Language], str]:
        """
        Determina se un errore dovrebbe essere filtrato e come classificarlo.
        
        NUOVO FLUSSO CON VOCABOLARIO DI BASE:
        1. Verifica se la parola è nel Vocabolario di Base italiano → NON è errore
        2. Verifica nomi propri
        3. Verifica termini tecnici
        4. Classifica lingua straniera
        
        Args:
            word: Parola segnalata come errore
            context: Contesto circostante
            rule_id: ID della regola LanguageTool che ha generato l'errore
            
        Returns:
            Tupla (should_filter, language, reason):
            - should_filter: True se l'errore va filtrato/riclassificato
            - language: Lingua rilevata (None se nome proprio/termine tecnico)
            - reason: Motivo del filtraggio
        """
        word_lower = word.lower()
        
        # 0. PRIORITÀ: Verifica nel Vocabolario di Base
        if self.vocabulary_service:
            if self.vocabulary_service.is_in_vocabulary(word_lower):
                logger.debug(f"✅ '{word}' trovata nel Vocabolario di Base → NON è errore")
                return True, None, "in_vocabulary_base"
        
        # 1. Verifica nomi propri
        if self.is_proper_noun(word):
            return True, None, "proper_noun"
        
        # 2. Verifica termini tecnici
        if self.is_technical_term(word):
            return True, None, "technical_term"
        
        # 3. Classifica lingua
        lang, confidence = self.classifier.classify_word(word, context)
        
        # Soglia dinamica basata sulla lingua
        # Latino: soglia più bassa (0.35) perché parole singole hanno score più basso
        # Altre lingue: soglia standard (0.6)
        threshold = 0.35 if lang == Language.LATIN else 0.6
        
        if lang != Language.UNKNOWN and confidence > threshold:
            return True, lang, f"foreign_language_{lang.value}"
        
        # 4. Se è una parola molto corta e troncata, probabilmente è OCR sbagliato
        if len(word) <= 3 and word.endswith(' '):
            return True, None, "truncated_word"
        
        return False, None, "no_filter"
    
    def analyze_quote_block(self, text: str, start: int, end: int) -> Optional[Language]:
        """
        Analizza un blocco di testo per determinare se è una citazione in lingua straniera.
        
        Args:
            text: Testo completo
            start: Indice inizio blocco
            end: Indice fine blocco
            
        Returns:
            Lingua rilevata o None
        """
        quote = text[start:end]
        lang, confidence = self.classifier.classify_phrase(quote)
        
        # Soglia più alta per blocchi (70%)
        if lang != Language.UNKNOWN and confidence > 0.7:
            return lang
        
        return None


# Esempio di utilizzo
if __name__ == "__main__":
    classifier = LanguageClassifier()
    filter_system = ForeignWordFilter()
    
    # Test classificazione
    test_words = [
        ("governance", "La governance multilivello"),
        ("populus", "legislator sive causa efficiens primaria legis est populus"),
        ("checks", "sistema di checks and balances"),
        ("Westfalia", "il trattato di Westfalia"),
    ]
    
    print("=== Test Classificazione ===")
    for word, context in test_words:
        lang, conf = classifier.classify_word(word, context)
        should_filter, detected_lang, reason = filter_system.should_filter_error(word, context)
        print(f"{word:15} -> {lang.value:10} (conf: {conf:.2f}) | Filter: {should_filter} ({reason})")
