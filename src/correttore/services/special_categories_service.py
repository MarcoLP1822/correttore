"""
Service per la gestione delle categorie speciali di correzione.

Questo modulo gestisce:
- Rilevamento parole straniere (inglese, latino, francese, etc.)
- Rilevamento parole potenzialmente imbarazzanti/sensibili
- Popolamento automatico nomi propri da Named Entity Recognition
- Integrazione con sistema report per tabs dedicate

Author: Sistema di Correzione Avanzato
Date: 27 Ottobre 2025
Phase: FASE 7 - Categorie Speciali
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ForeignWord:
    """Parola straniera rilevata"""
    word: str
    language: str  # english, latin, french, etc.
    context: str  # Frase contenente la parola
    position: int  # Posizione nel testo
    count: int = 1  # Numero occorrenze
    
    
@dataclass
class SensitiveWord:
    """Parola potenzialmente imbarazzante"""
    word: str
    category: str  # anatomia, parolacce, violenza, etc.
    context: str
    position: int
    count: int = 1


@dataclass
class ProperNoun:
    """Nome proprio rilevato"""
    name: str
    entity_type: str  # PER, LOC, ORG
    entity_label: str  # Persona, Luogo, Organizzazione
    context: str
    position: int
    count: int = 1


class SpecialCategoriesService:
    """
    Service per rilevamento categorie speciali nel testo.
    
    Features:
    - Carica dizionari parole straniere e sensibili
    - Rileva automaticamente parole straniere in testo italiano
    - Rileva parole potenzialmente imbarazzanti
    - Integra NER per nomi propri
    - Case-insensitive matching
    - Word boundary detection
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern per evitare caricamenti multipli"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inizializza service e carica dizionari"""
        if self._initialized:
            return
            
        # Percorso data directory - cerca dalla posizione del file o dalla root
        file_dir = Path(__file__).parent.parent.parent  # Da src/correttore/services/ alla root
        
        # Prova diverse possibilità per trovare data/
        possible_paths = [
            file_dir / "data",  # Standard: dalla root del progetto
            Path.cwd() / "data",  # Alternative: dalla directory corrente
            file_dir.parent / "data",  # Se siamo in una sottocartella
        ]
        
        data_dir: Optional[Path] = None
        for path in possible_paths:
            if path.exists():
                data_dir = path
                break
        
        if data_dir is None:
            logger.warning(f"Data directory not found. Tried: {possible_paths}")
            data_dir = Path.cwd() / "data"  # Fallback
        
        self.data_dir: Path = data_dir  # Type hint definitivo
        logger.debug(f"Using data directory: {self.data_dir}")
        
        # Dizionari
        self.foreign_words: Dict[str, List[str]] = {}
        self.sensitive_words: Dict[str, List[str]] = {}
        
        # Cache per performance
        self._foreign_words_set: Set[str] = set()
        self._sensitive_words_set: Set[str] = set()
        self._word_to_language: Dict[str, str] = {}
        self._word_to_category: Dict[str, str] = {}
        
        # Carica dizionari
        self._load_foreign_words()
        self._load_sensitive_words()
        
        self._initialized = True
        
        logger.info(
            f"✅ SpecialCategoriesService initialized: "
            f"{len(self._foreign_words_set)} foreign words, "
            f"{len(self._sensitive_words_set)} sensitive words"
        )
    
    def _load_foreign_words(self):
        """Carica dizionario parole straniere"""
        try:
            file_path = self.data_dir / "foreign_words" / "common_foreign.json"
            
            if not file_path.exists():
                logger.warning(f"Foreign words dictionary not found: {file_path}")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Escludi metadata
            languages = {k: v for k, v in data.items() if k != 'metadata'}
            
            for language, info in languages.items():
                if isinstance(info, dict) and 'words' in info:
                    words = info['words']
                    self.foreign_words[language] = words
                    
                    # Aggiungi a set per ricerca veloce
                    for word in words:
                        word_lower = word.lower()
                        self._foreign_words_set.add(word_lower)
                        self._word_to_language[word_lower] = language
            
            logger.info(
                f"✅ Loaded {len(self._foreign_words_set)} foreign words "
                f"from {len(self.foreign_words)} languages"
            )
            
        except Exception as e:
            logger.error(f"Error loading foreign words: {e}")
    
    def _load_sensitive_words(self):
        """Carica dizionario parole sensibili"""
        try:
            file_path = self.data_dir / "sensitive_words" / "imbarazzanti.json"
            
            if not file_path.exists():
                logger.warning(f"Sensitive words dictionary not found: {file_path}")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Escludi metadata e note
            categories = {k: v for k, v in data.items() 
                         if k not in ['metadata', 'note']}
            
            for category, info in categories.items():
                if isinstance(info, dict) and 'words' in info:
                    words = info['words']
                    self.sensitive_words[category] = words
                    
                    # Aggiungi a set per ricerca veloce
                    for word in words:
                        word_lower = word.lower()
                        self._sensitive_words_set.add(word_lower)
                        self._word_to_category[word_lower] = category
            
            logger.info(
                f"✅ Loaded {len(self._sensitive_words_set)} sensitive words "
                f"from {len(self.sensitive_words)} categories"
            )
            
        except Exception as e:
            logger.error(f"Error loading sensitive words: {e}")
    
    def detect_foreign_words(
        self, 
        text: str, 
        min_occurrences: int = 1
    ) -> List[ForeignWord]:
        """
        Rileva parole straniere nel testo.
        
        Args:
            text: Testo da analizzare
            min_occurrences: Numero minimo occorrenze per includere
            
        Returns:
            Lista di ForeignWord rilevate
        """
        results: Dict[str, ForeignWord] = {}
        
        # Tokenizza (split su spazi e punteggiatura)
        words = re.findall(r'\b\w+\b', text, re.UNICODE)
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            
            if word_lower in self._foreign_words_set:
                language = self._word_to_language[word_lower]
                
                # Trova contesto (frase contenente la parola)
                context = self._extract_context(text, word, i)
                
                # Trova posizione nel testo originale
                position = text.lower().find(word_lower)
                
                # Aggrega occorrenze
                key = f"{word_lower}:{language}"
                if key in results:
                    results[key].count += 1
                else:
                    results[key] = ForeignWord(
                        word=word,
                        language=language,
                        context=context,
                        position=position,
                        count=1
                    )
        
        # Filtra per numero minimo occorrenze
        filtered = [fw for fw in results.values() if fw.count >= min_occurrences]
        
        # Ordina per frequenza decrescente
        filtered.sort(key=lambda x: x.count, reverse=True)
        
        logger.debug(f"Detected {len(filtered)} foreign words in text")
        
        return filtered
    
    def detect_sensitive_words(
        self, 
        text: str,
        min_occurrences: int = 1
    ) -> List[SensitiveWord]:
        """
        Rileva parole potenzialmente imbarazzanti nel testo.
        
        Args:
            text: Testo da analizzare
            min_occurrences: Numero minimo occorrenze per includere
            
        Returns:
            Lista di SensitiveWord rilevate
        """
        results: Dict[str, SensitiveWord] = {}
        
        # Tokenizza
        words = re.findall(r'\b\w+\b', text, re.UNICODE)
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            
            if word_lower in self._sensitive_words_set:
                category = self._word_to_category[word_lower]
                
                # Trova contesto
                context = self._extract_context(text, word, i)
                
                # Trova posizione
                position = text.lower().find(word_lower)
                
                # Aggrega occorrenze
                key = f"{word_lower}:{category}"
                if key in results:
                    results[key].count += 1
                else:
                    results[key] = SensitiveWord(
                        word=word,
                        category=category,
                        context=context,
                        position=position,
                        count=1
                    )
        
        # Filtra per numero minimo occorrenze
        filtered = [sw for sw in results.values() if sw.count >= min_occurrences]
        
        # Ordina per frequenza decrescente
        filtered.sort(key=lambda x: x.count, reverse=True)
        
        logger.debug(f"Detected {len(filtered)} sensitive words in text")
        
        return filtered
    
    def extract_proper_nouns_from_ner(
        self, 
        text: str,
        lemmatization_service=None
    ) -> List[ProperNoun]:
        """
        Estrae nomi propri usando Named Entity Recognition.
        
        Requires: LemmatizationService (FASE 5)
        
        Args:
            text: Testo da analizzare
            lemmatization_service: Istanza di LemmatizationService (opzionale)
            
        Returns:
            Lista di ProperNoun rilevati
        """
        if lemmatization_service is None:
            try:
                from src.correttore.services.lemmatization_service import (
                    LemmatizationService
                )
                lemmatization_service = LemmatizationService()
            except ImportError:
                logger.warning(
                    "LemmatizationService not available. "
                    "Cannot extract proper nouns."
                )
                return []
        
        try:
            # Usa NER per estrarre entità nominate
            entities = lemmatization_service.get_named_entities(text)
            
            results: Dict[str, ProperNoun] = {}
            
            for entity in entities:
                # Aggrega occorrenze dello stesso nome
                key = f"{entity.text}:{entity.label}"
                if key in results:
                    results[key].count += 1
                else:
                    results[key] = ProperNoun(
                        name=entity.text,
                        entity_type=entity.label,
                        entity_label=entity.label_description,
                        context=entity.context,
                        position=entity.start_char,
                        count=1
                    )
            
            # Converti a lista e ordina per frequenza
            proper_nouns = list(results.values())
            proper_nouns.sort(key=lambda x: x.count, reverse=True)
            
            logger.debug(f"Extracted {len(proper_nouns)} proper nouns via NER")
            
            return proper_nouns
            
        except Exception as e:
            logger.error(f"Error extracting proper nouns: {e}")
            return []
    
    def _extract_context(
        self, 
        text: str, 
        word: str, 
        word_index: int,
        context_words: int = 5
    ) -> str:
        """
        Estrae contesto (frase o n parole attorno alla parola).
        
        Args:
            text: Testo completo
            word: Parola target
            word_index: Indice parola nella lista
            context_words: Numero parole prima/dopo da includere
            
        Returns:
            Stringa con contesto
        """
        # Trova la frase contenente la parola
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            if word.lower() in sentence.lower():
                return sentence.strip()
        
        # Fallback: usa n parole attorno
        words = re.findall(r'\b\w+\b', text, re.UNICODE)
        start = max(0, word_index - context_words)
        end = min(len(words), word_index + context_words + 1)
        
        context_words_list = words[start:end]
        return " ".join(context_words_list)
    
    def get_statistics(
        self,
        foreign_words: List[ForeignWord],
        sensitive_words: List[SensitiveWord],
        proper_nouns: List[ProperNoun]
    ) -> Dict:
        """
        Genera statistiche sulle categorie speciali rilevate.
        
        Returns:
            Dizionario con statistiche
        """
        # Raggruppa parole straniere per lingua
        foreign_by_language: Dict[str, int] = {}
        for fw in foreign_words:
            foreign_by_language[fw.language] = (
                foreign_by_language.get(fw.language, 0) + fw.count
            )
        
        # Raggruppa parole sensibili per categoria
        sensitive_by_category: Dict[str, int] = {}
        for sw in sensitive_words:
            sensitive_by_category[sw.category] = (
                sensitive_by_category.get(sw.category, 0) + sw.count
            )
        
        # Raggruppa nomi propri per tipo
        nouns_by_type: Dict[str, int] = {}
        for pn in proper_nouns:
            nouns_by_type[pn.entity_label] = (
                nouns_by_type.get(pn.entity_label, 0) + pn.count
            )
        
        return {
            'foreign_words': {
                'total_unique': len(foreign_words),
                'total_occurrences': sum(fw.count for fw in foreign_words),
                'by_language': foreign_by_language,
                'top_5': [
                    {'word': fw.word, 'language': fw.language, 'count': fw.count}
                    for fw in foreign_words[:5]
                ]
            },
            'sensitive_words': {
                'total_unique': len(sensitive_words),
                'total_occurrences': sum(sw.count for sw in sensitive_words),
                'by_category': sensitive_by_category,
                'top_5': [
                    {'word': sw.word, 'category': sw.category, 'count': sw.count}
                    for sw in sensitive_words[:5]
                ]
            },
            'proper_nouns': {
                'total_unique': len(proper_nouns),
                'total_occurrences': sum(pn.count for pn in proper_nouns),
                'by_type': nouns_by_type,
                'top_5': [
                    {'name': pn.name, 'type': pn.entity_label, 'count': pn.count}
                    for pn in proper_nouns[:5]
                ]
            }
        }


# Singleton helper
def get_special_categories_service() -> SpecialCategoriesService:
    """
    Ottiene istanza singleton del service.
    
    Returns:
        SpecialCategoriesService instance
    """
    return SpecialCategoriesService()
