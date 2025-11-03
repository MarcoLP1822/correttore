"""
Servizio per il Nuovo Vocabolario di Base (NVdB) della lingua italiana.
Fornisce controllo vocabolario e analisi lessicale avanzata.
"""

import json
import logging
from pathlib import Path
from typing import Set, Dict, Optional, List, Tuple, Any
from dataclasses import dataclass, field
from functools import lru_cache

logger = logging.getLogger(__name__)

# Import opzionale per lemmatizzazione (Fase 5)
try:
    from correttore.services.lemmatization_service import get_lemmatization_service
    LEMMATIZATION_AVAILABLE = True
except ImportError:
    LEMMATIZATION_AVAILABLE = False
    logger.debug("Lemmatization service non disponibile")


@dataclass
class WordAnalysis:
    """Analisi dettagliata di una parola - FASE 4"""
    word: str
    in_vdb: bool
    level: Optional[str]  # fondamentale, alto_uso, alta_disponibilita, None se fuori VdB
    difficulty_score: float  # 0.0 = facile, 1.0 = difficile
    lemma: Optional[str] = None  # forma base (con lemmatizzazione - futuro Fase 5)
    is_technical: bool = False  # termine tecnico riconosciuto
    suggested_alternatives: List[str] = field(default_factory=list)  # alternative più semplici
    frequency_rank: Optional[int] = None  # rank di frequenza nel VdB
    
    def get_level_label(self) -> str:
        """Restituisce etichetta leggibile del livello"""
        if not self.in_vdb:
            return "Fuori VdB"
        if self.level == 'fondamentale':
            return "Fondamentale"
        if self.level == 'alto_uso':
            return "Alto Uso"
        if self.level == 'alta_disponibilita':
            return "Alta Disponibilità"
        return "Non classificato"
    
    def get_difficulty_color(self) -> str:
        """Restituisce colore associato al livello di difficoltà"""
        if self.difficulty_score <= 0.25:
            return '#2ecc71'  # Verde - fondamentale
        elif self.difficulty_score <= 0.5:
            return '#3498db'  # Blu - alto uso
        elif self.difficulty_score <= 0.75:
            return '#f39c12'  # Arancione - alta disponibilità
        else:
            return '#e74c3c'  # Rosso - fuori VdB


@dataclass
class VocabularyStats:
    """Statistiche sull'uso del vocabolario in un testo"""
    total_words: int
    in_nvdb: int
    not_in_nvdb: int
    percentage_in_nvdb: float
    difficult_words: List[str]
    
    @property
    def coverage(self) -> float:
        """Percentuale di copertura del vocabolario"""
        return self.percentage_in_nvdb


@dataclass
class WordInfo:
    """Informazioni su una parola del vocabolario"""
    word: str
    level: Optional[str]  # fondamentale, alto_uso, alta_disponibilita
    in_vocabulary: bool
    note: str = ""
    
    @property
    def is_fundamental(self) -> bool:
        return self.level == 'fondamentale'
    
    @property
    def is_high_use(self) -> bool:
        return self.level == 'alto_uso'
    
    @property
    def is_high_availability(self) -> bool:
        return self.level == 'alta_disponibilita'
    
    @property
    def difficulty_score(self) -> int:
        """Score di difficoltà: 0=facile, 3=difficile"""
        if not self.in_vocabulary:
            return 3
        if self.level == 'fondamentale':
            return 0
        if self.level == 'alto_uso':
            return 1
        if self.level == 'alta_disponibilita':
            return 2
        return 2  # non classificato


class VocabularyService:
    """
    Servizio per gestione Nuovo Vocabolario di Base.
    Singleton pattern per evitare caricamenti multipli.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._vocabulary: Set[str] = set()
            self._vocabulary_full: Dict[str, Dict] = {}
            self._lemmatization_service = None  # Lazy loading
            self._load_vocabulary()
            VocabularyService._initialized = True
    
    def _load_vocabulary(self) -> None:
        """Carica il vocabolario dai file JSON"""
        try:
            # Percorso relativo alla root del progetto - CORRETTO per nuova posizione
            base_path = Path(__file__).parent.parent.parent.parent / "data" / "vocabolario"
            
            # Carica vocabolario completo per le informazioni sui livelli
            full_path = base_path / "nvdb_completo.json"
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._vocabulary_full = data.get('vocabolario', {})
                    self._vocabulary = set(self._vocabulary_full.keys())
                    
                    metadata = data.get('metadata', {})
                    total = metadata.get('totale_parole', len(self._vocabulary))
                    
                    logger.info(f"✓ Vocabolario NVdB caricato: {total} parole")
                    logger.info(f"  - Fondamentali: {metadata.get('livelli', {}).get('fondamentale', {}).get('count', 0)}")
                    logger.info(f"  - Alto uso: {metadata.get('livelli', {}).get('alto_uso', {}).get('count', 0)}")
                    logger.info(f"  - Alta disponibilità: {metadata.get('livelli', {}).get('alta_disponibilita', {}).get('count', 0)}")
            else:
                # Fallback: carica solo lista semplice
                simple_path = base_path / "nvdb_parole.json"
                if simple_path.exists():
                    with open(simple_path, 'r', encoding='utf-8') as f:
                        words = json.load(f)
                        self._vocabulary = set(words)
                        logger.info(f"✓ Vocabolario NVdB caricato (versione semplice): {len(self._vocabulary)} parole")
                else:
                    logger.warning("⚠ File vocabolario NVdB non trovato")
                    
        except Exception as e:
            logger.error(f"❌ Errore caricamento vocabolario NVdB: {e}")
    
    def is_in_vocabulary(self, word: str) -> bool:
        """Verifica se una parola è nel vocabolario"""
        return word.lower() in self._vocabulary
    
    def is_in_vocabulary_with_lemma(self, word: str, use_lemmatization: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Verifica se una parola (o il suo lemma) è nel vocabolario.
        
        Args:
            word: Parola da verificare
            use_lemmatization: Se True, prova anche la forma lemmatizzata
            
        Returns:
            Tupla (è_nel_vocabolario, lemma_usato)
            
        Example:
            >>> service.is_in_vocabulary_with_lemma("mangiato")
            (True, "mangiare")
        """
        word_lower = word.lower()
        
        # Prima prova la parola esatta
        if word_lower in self._vocabulary:
            return (True, word_lower)
        
        # Se non trovata e lemmatizzazione disponibile, prova il lemma
        if use_lemmatization and LEMMATIZATION_AVAILABLE:
            if self._lemmatization_service is None:
                try:
                    self._lemmatization_service = get_lemmatization_service()
                except Exception as e:
                    logger.debug(f"Impossibile caricare lemmatization service: {e}")
                    return (False, None)
            
            try:
                lemma = self._lemmatization_service.lemmatize_word(word_lower)
                if lemma and lemma != word_lower and lemma in self._vocabulary:
                    return (True, lemma)
            except Exception as e:
                logger.debug(f"Errore lemmatizzazione per '{word}': {e}")
        
        return (False, None)
    
    def get_word_info(self, word: str) -> WordInfo:
        """Ottiene informazioni dettagliate su una parola"""
        word_lower = word.lower()
        
        if word_lower in self._vocabulary_full:
            data = self._vocabulary_full[word_lower]
            return WordInfo(
                word=word_lower,
                level=data.get('livello'),
                in_vocabulary=True,
                note=data.get('note', '')
            )
        else:
            return WordInfo(
                word=word_lower,
                level=None,
                in_vocabulary=False,
                note='Parola non presente nel Vocabolario di Base'
            )
    
    def analyze_text(self, text: str, use_lemmatization: bool = True) -> VocabularyStats:
        """
        Analizza un testo rispetto al vocabolario di base.
        Con lemmatizzazione (Fase 5), riduce drasticamente i falsi positivi.
        
        Args:
            text: Testo da analizzare
            use_lemmatization: Se True, usa lemmatizzazione per confronto VdB
            
        Returns:
            Statistiche sull'uso del vocabolario
        """
        import re
        
        # Estrai parole (solo lettere, gestisce apostrofi)
        words = re.findall(r"\b[a-zàèéìòùA-ZÀÈÉÌÒÙ]+(?:'[a-zàèéìòù]+)?\b", text)
        words_lower = [w.lower() for w in words]
        
        if not words_lower:
            return VocabularyStats(
                total_words=0,
                in_nvdb=0,
                not_in_nvdb=0,
                percentage_in_nvdb=0.0,
                difficult_words=[]
            )
        
        # Conta parole nel vocabolario (con o senza lemmatizzazione)
        in_vocabulary = 0
        difficult = []
        
        for word in words_lower:
            is_in, _ = self.is_in_vocabulary_with_lemma(word, use_lemmatization)
            if is_in:
                in_vocabulary += 1
            else:
                if word not in difficult:
                    difficult.append(word)
        
        not_in_vocabulary = len(words_lower) - in_vocabulary
        percentage = (in_vocabulary / len(words_lower)) * 100
        
        return VocabularyStats(
            total_words=len(words_lower),
            in_nvdb=in_vocabulary,
            not_in_nvdb=not_in_vocabulary,
            percentage_in_nvdb=round(percentage, 2),
            difficult_words=sorted(difficult)
        )
    
    def get_word_level(self, word: str) -> Optional[str]:
        """Ottiene il livello di una parola (fondamentale, alto_uso, alta_disponibilita)"""
        word_lower = word.lower()
        if word_lower in self._vocabulary_full:
            return self._vocabulary_full[word_lower].get('livello')
        return None
    
    def suggest_simpler_alternatives(self, word: str) -> List[str]:
        """
        Suggerisce alternative più semplici per una parola difficile.
        (Placeholder per futura implementazione con thesaurus)
        """
        # TODO: Implementare con dizionario sinonimi
        return []
    
    def analyze_word_detailed(self, word: str, use_lemmatization: bool = True) -> WordAnalysis:
        """
        Analizza una parola in dettaglio restituendo tutte le informazioni disponibili.
        Con lemmatizzazione (Fase 5), confronta anche la forma base.
        
        Args:
            word: Parola da analizzare
            use_lemmatization: Se True, usa lemmatizzazione per confronto VdB
            
        Returns:
            WordAnalysis con informazioni complete
        """
        word_lower = word.lower()
        
        # Verifica con lemmatizzazione
        in_vdb, lemma_found = self.is_in_vocabulary_with_lemma(word_lower, use_lemmatization)
        
        # Se trovato il lemma, usa quello per recuperare le info
        lookup_word = lemma_found if lemma_found else word_lower
        
        # Ottieni livello e informazioni
        level = None
        frequency_rank = None
        
        if lookup_word in self._vocabulary_full:
            data = self._vocabulary_full[lookup_word]
            level = data.get('livello')
            frequency_rank = data.get('rank')
        
        # Calcola difficulty score
        difficulty_score = self._calculate_difficulty_score(level, in_vdb)
        
        # Suggerimenti alternativi
        alternatives = self.suggest_simpler_alternatives(word)
        
        # Verifica se è termine tecnico
        is_technical = self._is_technical_term(word_lower)
        
        return WordAnalysis(
            word=word_lower,
            in_vdb=in_vdb,
            level=level,
            difficulty_score=difficulty_score,
            lemma=lemma_found,  # Fase 5: lemma trovato
            is_technical=is_technical,
            suggested_alternatives=alternatives,
            frequency_rank=frequency_rank
        )
    
    def _calculate_difficulty_score(self, level: Optional[str], in_vdb: bool) -> float:
        """
        Calcola uno score di difficoltà da 0.0 (facile) a 1.0 (difficile).
        
        Args:
            level: Livello VdB della parola
            in_vdb: Se la parola è nel vocabolario
            
        Returns:
            Score di difficoltà
        """
        if not in_vdb:
            return 1.0  # Massima difficoltà
        
        if level == 'fondamentale':
            return 0.0  # Minima difficoltà
        elif level == 'alto_uso':
            return 0.33
        elif level == 'alta_disponibilita':
            return 0.66
        else:
            return 0.75  # Non classificato ma nel VdB
    
    def _is_technical_term(self, word: str) -> bool:
        """
        Verifica se una parola è un termine tecnico.
        Implementazione base - sarà estesa in Fase 5.
        
        Args:
            word: Parola da verificare
            
        Returns:
            True se è termine tecnico
        """
        # Lista base di suffissi tecnici
        technical_suffixes = [
            'logia', 'grafia', 'metria', 'scopio', 'crazia',
            'tomia', 'patia', 'fobia', 'filia', 'zione'
        ]
        
        # Verifica suffissi
        for suffix in technical_suffixes:
            if word.endswith(suffix):
                return True
        
        return False
    
    def classify_technical_terms(self, words: List[str]) -> List[str]:
        """
        Classifica una lista di parole identificando i termini tecnici.
        
        Args:
            words: Lista di parole da classificare
            
        Returns:
            Lista di parole identificate come termini tecnici
        """
        technical = []
        
        for word in words:
            word_lower = word.lower()
            if self._is_technical_term(word_lower):
                technical.append(word_lower)
        
        return technical
    
    def get_vocabulary_breakdown(self, text: str) -> Dict[str, Any]:
        """
        Analizza un testo e restituisce statistiche dettagliate per livello VdB.
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Dizionario con statistiche per livello
        """
        import re
        
        # Estrai parole
        words = re.findall(r"\b[a-zàèéìòùA-ZÀÈÉÌÒÙ]+(?:'[a-zàèéìòù]+)?\b", text)
        words_lower = [w.lower() for w in words]
        
        if not words_lower:
            return {
                'total_words': 0,
                'fondamentale': {'count': 0, 'percentage': 0.0},
                'alto_uso': {'count': 0, 'percentage': 0.0},
                'alta_disponibilita': {'count': 0, 'percentage': 0.0},
                'fuori_vdb': {'count': 0, 'percentage': 0.0, 'words': []}
            }
        
        # Conta per livello
        counts = {
            'fondamentale': 0,
            'alto_uso': 0,
            'alta_disponibilita': 0,
            'fuori_vdb': 0
        }
        
        fuori_vdb_words = []
        
        for word in words_lower:
            if word in self._vocabulary_full:
                level = self._vocabulary_full[word].get('livello')
                if level in counts:
                    counts[level] += 1
                else:
                    counts['fuori_vdb'] += 1
            else:
                counts['fuori_vdb'] += 1
                if word not in fuori_vdb_words:
                    fuori_vdb_words.append(word)
        
        total = len(words_lower)
        
        return {
            'total_words': total,
            'fondamentale': {
                'count': counts['fondamentale'],
                'percentage': round((counts['fondamentale'] / total) * 100, 2)
            },
            'alto_uso': {
                'count': counts['alto_uso'],
                'percentage': round((counts['alto_uso'] / total) * 100, 2)
            },
            'alta_disponibilita': {
                'count': counts['alta_disponibilita'],
                'percentage': round((counts['alta_disponibilita'] / total) * 100, 2)
            },
            'fuori_vdb': {
                'count': counts['fuori_vdb'],
                'percentage': round((counts['fuori_vdb'] / total) * 100, 2),
                'words': sorted(set(fuori_vdb_words))
            }
        }
    
    @property
    def vocabulary_size(self) -> int:
        """Numero totale di parole nel vocabolario"""
        return len(self._vocabulary)
    
    @property
    def is_loaded(self) -> bool:
        """Verifica se il vocabolario è stato caricato"""
        return len(self._vocabulary) > 0


# Singleton instance
@lru_cache(maxsize=1)
def get_vocabulary_service() -> VocabularyService:
    """Factory function per ottenere l'istanza singleton del servizio"""
    return VocabularyService()
