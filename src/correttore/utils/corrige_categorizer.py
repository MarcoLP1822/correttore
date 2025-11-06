# utils/corrige_categorizer.py
"""
Sistema di categorizzazione errori secondo lo standard Corrige.it
Classifica le correzioni e segnalazioni nelle categorie standard del resoconto ortografia.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CorrigeCategory(Enum):
    """Categorie di segnalazione secondo Corrige.it"""
    ERRORI = "Errori di ortografia o grammatica riconosciuti"
    SCONOSCIUTE = "Sconosciute: parole non riconosciute"
    SOSPETTE = "Sospette"
    MIGLIORABILI = "Migliorabili"
    PUNTEGGIATURA = "Punteggiatura"
    IMBARAZZANTI = "Imbarazzanti"
    VARIANTI = "Varianti"
    NOMI_SIGLE = "Nomi propri, sigle ecc."
    LINGUE = "Parole di altre lingue"
    CON_INFO = "Con info"


@dataclass
class CorrectionContext:
    """Contesto di una correzione per la categorizzazione"""
    original_text: str
    corrected_text: str
    paragraph_context: str  # ~10 parole di contesto
    position: int
    correction_type: str  # tipo LanguageTool o custom
    rule_id: Optional[str] = None
    message: Optional[str] = None
    replacements: List[str] = field(default_factory=list)


@dataclass
class CategorizedCorrection:
    """Correzione categorizzata secondo Corrige.it"""
    category: CorrigeCategory
    original_word: str
    context: str
    corrected_word: Optional[str] = None
    explanation: Optional[str] = None
    info_link: Optional[str] = None
    is_suggestion: bool = False  # Per sospette/migliorabili
    variants: List[str] = field(default_factory=list)  # Per varianti
    language: Optional[str] = None  # Per lingue straniere
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario"""
        return {
            'category': self.category.value,
            'original_word': self.original_word,
            'context': self.context,
            'corrected_word': self.corrected_word,
            'explanation': self.explanation,
            'info_link': self.info_link,
            'is_suggestion': self.is_suggestion,
            'variants': self.variants,
            'language': self.language
        }


class CorrigeCategorizer:
    """
    Categorizzatore di correzioni secondo lo standard Corrige.it.
    Analizza correzioni e le classifica nelle categorie appropriate.
    """
    
    def __init__(self):
        # Parole potenzialmente imbarazzanti (lista base)
        self.imbarazzanti = {
            'cacca', 'culo', 'merda', 'cazzo', 'puttana', 'figa', 
            'minchia', 'coglione', 'stronzo', 'bastardo', 'porca'
        }
        
        # Pattern per riconoscimento nomi propri (semplificato)
        self.nome_proprio_pattern = re.compile(r'^[A-Z][a-zàèéìòù]+$')
        
        # Pattern per sigle e acronimi
        self.sigla_pattern = re.compile(r'^[A-Z]{2,}\.?$|^[A-Z]\.[A-Z]\..*$')
        
        # Pattern per punteggiatura problematica
        self.punct_patterns = {
            'spazio_prima_virgola': re.compile(r'\s+[,;:!?]'),
            'spazio_dopo_apertura': re.compile(r'[({\[]\s+'),
            'spazio_prima_chiusura': re.compile(r'\s+[)}\]]'),
            'virgolette_spazio': re.compile(r'"\s+|\s+"'),
            'doppia_punteggiatura': re.compile(r'[.,;:!?]{2,}'),
            # 'manca_punto_fine' rimosso: troppi falsi positivi
        }
        
        # Parole che possono essere varianti
        self.varianti_comuni = {
            'obiettivo': ['obbiettivo'],
            'obbiettivo': ['obiettivo'],
            'jungla': ['giungla'],
            'giungla': ['jungla'],
            'usignuolo': ['usignolo'],
            'usignolo': ['usignuolo'],
            'capostazione': ['capo-stazione'],
            'capo-stazione': ['capostazione'],
            'webcam': ['web cam', 'web-cam'],
            'email': ['e-mail', 'e mail'],
        }
        
        # Prefissi/suffissi che indicano migliorabilità
        self.migliorabili_patterns = [
            (re.compile(r'\d+a\b'), 'Usare ordinale con ª: 1ª, 2ª'),
            (re.compile(r'\d+o\b'), 'Usare ordinale con º: 1º, 2º'),
            (re.compile(r"tutt'altro"), "Preferire 'tuttaltro'"),
            (re.compile(r'ed anche\b'), "Preferire 'e anche'"),
            (re.compile(r'ad esempio\b'), "In contesto formale preferire 'per esempio'"),
        ]
        
        # Lingue riconoscibili (lista base)
        self.lingue_straniere = {
            'en': ['the', 'and', 'or', 'is', 'are', 'was', 'were', 'have', 'has', 'had',
                   'when', 'what', 'where', 'who', 'how', 'which', 'that', 'this'],
            'fr': ['le', 'la', 'les', 'et', 'ou', 'dans', 'sur', 'avec', 'pour', 'par'],
            'de': ['der', 'die', 'das', 'und', 'oder', 'ist', 'sind', 'war', 'waren'],
            'es': ['el', 'la', 'los', 'las', 'y', 'o', 'en', 'con', 'para', 'por'],
            'lat': ['et', 'vel', 'aut', 'cum', 'per', 'ad', 'de', 'in', 'ex']
        }
    
    def categorize_correction(self, context: CorrectionContext) -> CategorizedCorrection:
        """
        Categorizza una singola correzione.
        
        Args:
            context: Contesto della correzione
            
        Returns:
            CategorizedCorrection: Correzione categorizzata
        """
        original_word = context.original_text.strip()
        corrected_word = context.corrected_text.strip() if context.corrected_text else None
        
        # PRIORITÀ 0: Se abbiamo un rule_id di LanguageTool, usiamo quello per categorizzare prima
        if context.rule_id:
            rule_id = context.rule_id.upper()
            
            # Regole di punteggiatura/tipografia
            if any(keyword in rule_id for keyword in ['COMMA', 'PUNCT', 'WHITESPACE', 'SPACE', 'PERIOD', 'COLON', 'SEMICOLON', 'DASH', 'QUOTE', 'TYPOGRAPHY', 'PARENTHESIS']):
                return CategorizedCorrection(
                    category=CorrigeCategory.PUNTEGGIATURA,
                    original_word=original_word,
                    context=self._extract_context(context.paragraph_context, original_word),
                    corrected_word=corrected_word,
                    explanation=context.message or "Errore di punteggiatura o spaziatura",
                    is_suggestion=False
                )
            
            # Regole ortografiche
            if any(keyword in rule_id for keyword in ['MORFOLOGIK', 'HUNSPELL', 'SPELLING']):
                # Se c'è una correzione, è un errore; altrimenti parola sconosciuta
                if corrected_word and corrected_word != original_word:
                    return CategorizedCorrection(
                        category=CorrigeCategory.ERRORI,
                        original_word=original_word,
                        context=self._extract_context(context.paragraph_context, original_word),
                        corrected_word=corrected_word,
                        explanation=context.message or "Errore ortografico"
                    )
                else:
                    return CategorizedCorrection(
                        category=CorrigeCategory.SCONOSCIUTE,
                        original_word=original_word,
                        context=self._extract_context(context.paragraph_context, original_word),
                        explanation="Parola non riconosciuta",
                        is_suggestion=True
                    )
        
        # PRIORITÀ 1: Check se la correzione riguarda solo spazi o punteggiatura
        if corrected_word and corrected_word != original_word:
            # Rimuovi spazi e punteggiatura per confrontare
            orig_alpha_only = re.sub(r'[^\w]', '', original_word).lower()
            corr_alpha_only = re.sub(r'[^\w]', '', corrected_word).lower()
            
            # Se le lettere/numeri sono identici, è solo punteggiatura/spazi
            if orig_alpha_only == corr_alpha_only and orig_alpha_only:
                return CategorizedCorrection(
                    category=CorrigeCategory.PUNTEGGIATURA,
                    original_word=original_word,
                    context=self._extract_context(context.paragraph_context, original_word),
                    corrected_word=corrected_word,
                    explanation="Correzione di spaziatura o punteggiatura",
                    is_suggestion=False
                )
        
        # PRIORITÀ 2: Check punteggiatura con pattern
        punct_issue = self._check_punteggiatura(original_word, context.paragraph_context)
        if punct_issue:
            return CategorizedCorrection(
                category=CorrigeCategory.PUNTEGGIATURA,
                original_word=original_word,
                context=self._extract_context(context.paragraph_context, original_word),
                corrected_word=corrected_word,
                explanation=punct_issue,
                is_suggestion=True
            )
        
        # 2. Check imbarazzanti
        if self._is_imbarazzante(original_word):
            return CategorizedCorrection(
                category=CorrigeCategory.IMBARAZZANTI,
                original_word=original_word,
                context=self._extract_context(context.paragraph_context, original_word),
                explanation="Parola potenzialmente imbarazzante",
                is_suggestion=True
            )
        
        # 3. Check nomi propri e sigle
        if self._is_nome_proprio_o_sigla(original_word):
            return CategorizedCorrection(
                category=CorrigeCategory.NOMI_SIGLE,
                original_word=original_word,
                context=self._extract_context(context.paragraph_context, original_word),
                explanation=self._get_nome_info(original_word)
            )
        
        # 4. Check lingue straniere
        lingua = self._detect_lingua(original_word)
        if lingua:
            return CategorizedCorrection(
                category=CorrigeCategory.LINGUE,
                original_word=original_word,
                context=self._extract_context(context.paragraph_context, original_word),
                language=lingua,
                explanation=f"Parola in {lingua}"
            )
        
        # 5. Check varianti
        varianti = self._get_varianti(original_word)
        if varianti:
            return CategorizedCorrection(
                category=CorrigeCategory.VARIANTI,
                original_word=original_word,
                context=self._extract_context(context.paragraph_context, original_word),
                variants=varianti,
                explanation=f"Varianti disponibili: {', '.join(varianti)}",
                is_suggestion=True
            )
        
        # 6. Check migliorabili
        miglioramento = self._check_migliorabile(original_word, context.paragraph_context)
        if miglioramento:
            return CategorizedCorrection(
                category=CorrigeCategory.MIGLIORABILI,
                original_word=original_word,
                context=self._extract_context(context.paragraph_context, original_word),
                corrected_word=corrected_word,
                explanation=miglioramento,
                is_suggestion=True
            )
        
        # 7. Se c'è una correzione effettiva, determina se è errore o sospetta
        if corrected_word and corrected_word != original_word:
            # Se LanguageTool ha alta confidenza o è un errore noto → ERRORI
            if self._is_errore_riconosciuto(context):
                return CategorizedCorrection(
                    category=CorrigeCategory.ERRORI,
                    original_word=original_word,
                    context=self._extract_context(context.paragraph_context, original_word),
                    corrected_word=corrected_word,
                    explanation=context.message or "Errore riconosciuto"
                )
            else:
                # Altrimenti è sospetta
                return CategorizedCorrection(
                    category=CorrigeCategory.SOSPETTE,
                    original_word=original_word,
                    context=self._extract_context(context.paragraph_context, original_word),
                    corrected_word=corrected_word,
                    explanation=context.message or "Possibile errore da verificare",
                    is_suggestion=True
                )
        
        # 8. Parola non riconosciuta (nessuna correzione ma segnalata)
        if not corrected_word:
            return CategorizedCorrection(
                category=CorrigeCategory.SCONOSCIUTE,
                original_word=original_word,
                context=self._extract_context(context.paragraph_context, original_word),
                explanation="Parola non riconosciuta - potrebbe essere un errore o un termine specialistico",
                is_suggestion=True
            )
        
        # Default: errore generico
        return CategorizedCorrection(
            category=CorrigeCategory.ERRORI,
            original_word=original_word,
            context=self._extract_context(context.paragraph_context, original_word),
            corrected_word=corrected_word,
            explanation=context.message or "Correzione suggerita"
        )
    
    def categorize_corrections(self, contexts: List[CorrectionContext]) -> Dict[CorrigeCategory, List[CategorizedCorrection]]:
        """
        Categorizza una lista di correzioni.
        
        Args:
            contexts: Lista di contesti di correzione
            
        Returns:
            Dict[CorrigeCategory, List[CategorizedCorrection]]: Correzioni raggruppate per categoria
        """
        categorized = {cat: [] for cat in CorrigeCategory}
        
        for context in contexts:
            correction = self.categorize_correction(context)
            categorized[correction.category].append(correction)
        
        # Ordina per categoria
        for cat in categorized:
            categorized[cat].sort(key=lambda x: x.original_word.lower())
        
        logger.info(f"📊 Categorizzate {len(contexts)} correzioni in {len(CorrigeCategory)} categorie")
        for cat, corrections in categorized.items():
            if corrections:
                logger.debug(f"  - {cat.value}: {len(corrections)} elementi")
        
        return categorized
    
    def _extract_context(self, full_context: str, word: str, words_around: int = 5) -> str:
        """Estrae ~10 parole di contesto intorno alla parola"""
        words = full_context.split()
        
        # Trova posizione della parola
        try:
            word_index = next(i for i, w in enumerate(words) if word.lower() in w.lower())
        except StopIteration:
            # Se non trovata, ritorna le prime parole
            return ' '.join(words[:words_around * 2])
        
        # Estrai contesto
        start = max(0, word_index - words_around)
        end = min(len(words), word_index + words_around + 1)
        
        context_words = words[start:end]
        context = ' '.join(context_words)
        
        # Aggiungi ellissi se necessario
        if start > 0:
            context = '...' + context
        if end < len(words):
            context = context + '...'
        
        return context
    
    def _check_punteggiatura(self, word: str, context: str) -> Optional[str]:
        """Controlla problemi di punteggiatura"""
        for pattern_name, pattern in self.punct_patterns.items():
            if pattern.search(context):
                if pattern_name == 'spazio_prima_virgola':
                    return "Spazio prima della punteggiatura"
                elif pattern_name == 'spazio_dopo_apertura':
                    return "Spazio dopo parentesi/virgoletta di apertura"
                elif pattern_name == 'spazio_prima_chiusura':
                    return "Spazio prima di parentesi/virgoletta di chiusura"
                elif pattern_name == 'doppia_punteggiatura':
                    return "Punteggiatura doppia o multipla"
                elif pattern_name == 'manca_punto_fine':
                    return "Possibile mancanza di punto finale"
        return None
    
    def _is_imbarazzante(self, word: str) -> bool:
        """Controlla se la parola è potenzialmente imbarazzante"""
        word_lower = word.lower().strip('.,;:!?"\'')
        return word_lower in self.imbarazzanti
    
    def _is_nome_proprio_o_sigla(self, word: str) -> bool:
        """Controlla se è un nome proprio o una sigla"""
        word_clean = word.strip('.,;:!?"\'')
        return (self.nome_proprio_pattern.match(word_clean) is not None or
                self.sigla_pattern.match(word_clean) is not None)
    
    def _get_nome_info(self, word: str) -> str:
        """Ritorna info su nome proprio/sigla"""
        word_clean = word.strip('.,;:!?"\'')
        if self.sigla_pattern.match(word_clean):
            return f"Riconosciuto come sigla o acronimo"
        else:
            return f"Riconosciuto come possibile nome proprio"
    
    def _detect_lingua(self, word: str) -> Optional[str]:
        """Rileva se la parola appartiene a una lingua straniera"""
        word_lower = word.lower().strip('.,;:!?"\'')
        
        for lingua, parole in self.lingue_straniere.items():
            if word_lower in parole:
                lingua_names = {
                    'en': 'inglese',
                    'fr': 'francese',
                    'de': 'tedesco',
                    'es': 'spagnolo',
                    'lat': 'latino'
                }
                return lingua_names.get(lingua, lingua)
        
        return None
    
    def _get_varianti(self, word: str) -> List[str]:
        """Ottiene varianti ortografiche disponibili"""
        word_lower = word.lower().strip('.,;:!?"\'')
        return self.varianti_comuni.get(word_lower, [])
    
    def _check_migliorabile(self, word: str, context: str) -> Optional[str]:
        """Controlla se c'è un miglioramento stilistico possibile"""
        for pattern, suggestion in self.migliorabili_patterns:
            if pattern.search(context) or pattern.search(word):
                return suggestion
        return None
    
    def _is_errore_riconosciuto(self, context: CorrectionContext) -> bool:
        """
        Determina se è un errore riconosciuto con alta confidenza.
        Basato su rule_id di LanguageTool e tipo di correzione.
        """
        if not context.rule_id:
            return False
        
        # Rule ID che indicano errori certi
        errori_certi_patterns = [
            'MORFOLOGIK_RULE',  # Errori ortografici
            'IT_AGREEMENT',  # Accordo grammaticale
            'IT_VERB_AGREEMENT',  # Accordo verbi
            'UPPERCASE_SENTENCE_START',  # Maiuscola inizio frase
            'CONFUSION_RULE',  # Confusione tra parole
            'DOUBLE_PUNCTUATION',  # Punteggiatura doppia
        ]
        
        rule_id_upper = context.rule_id.upper()
        return any(pattern in rule_id_upper for pattern in errori_certi_patterns)
    
    def generate_statistics(self, categorized: Dict[CorrigeCategory, List[CategorizedCorrection]]) -> Dict[str, Any]:
        """
        Genera statistiche sulle categorie.
        
        Args:
            categorized: Correzioni categorizzate
            
        Returns:
            Dict: Statistiche per categoria
        """
        stats = {
            'totale_segnalazioni': sum(len(corrections) for corrections in categorized.values()),
            'per_categoria': {}
        }
        
        for category, corrections in categorized.items():
            if corrections:
                stats['per_categoria'][category.value] = {
                    'count': len(corrections),
                    'percentuale': 0.0,  # Calcolato dopo
                    'suggerimenti': sum(1 for c in corrections if c.is_suggestion),
                    'correzioni': sum(1 for c in corrections if not c.is_suggestion)
                }
        
        # Calcola percentuali
        total = stats['totale_segnalazioni']
        if total > 0:
            for cat_stats in stats['per_categoria'].values():
                cat_stats['percentuale'] = (cat_stats['count'] / total) * 100
        
        return stats


def create_corrige_categorizer() -> CorrigeCategorizer:
    """Factory function per creare CorrigeCategorizer"""
    return CorrigeCategorizer()
