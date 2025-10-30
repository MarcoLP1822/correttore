"""
Servizio di lemmatizzazione per italiano usando spaCy.

Fornisce funzionalità di:
- Lemmatizzazione (riduzione alla forma base)
- POS tagging (classificazione parti del discorso)
- Named Entity Recognition (riconoscimento entità nominate)
"""

import spacy
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class Token:
    """Informazioni complete su un token analizzato"""
    text: str
    lemma: str
    pos: str  # Part of Speech (NOUN, VERB, ADJ, etc.)
    tag: str  # Fine-grained POS tag
    is_stop: bool  # Parola funzionale (il, la, di, ecc.)
    is_alpha: bool  # Solo caratteri alfabetici


@dataclass
class NamedEntity:
    """Entità nominata riconosciuta nel testo"""
    text: str
    label: str  # PER, LOC, ORG, etc.
    label_description: str  # Descrizione in italiano
    start_char: int
    end_char: int
    context: str  # Frase contenente l'entità


class LemmatizationService:
    """
    Servizio singleton per lemmatizzazione e analisi NLP con spaCy.
    
    Utilizzo:
        service = LemmatizationService()
        lemma = service.lemmatize_word("mangiato")  # -> "mangiare"
        tokens = service.lemmatize("Il gatto mangia il topo")
    """
    
    _instance = None
    _nlp = None
    
    # Mappatura etichette entità in italiano
    ENTITY_LABELS = {
        'PER': 'Persona',
        'LOC': 'Luogo',
        'ORG': 'Organizzazione',
        'GPE': 'Entità Geopolitica',
        'DATE': 'Data',
        'TIME': 'Ora',
        'MONEY': 'Denaro',
        'PERCENT': 'Percentuale',
        'CARDINAL': 'Numero Cardinale',
        'ORDINAL': 'Numero Ordinale',
        'QUANTITY': 'Quantità',
        'EVENT': 'Evento',
        'PRODUCT': 'Prodotto',
        'WORK_OF_ART': 'Opera',
        'LAW': 'Legge',
        'LANGUAGE': 'Lingua',
        'NORP': 'Nazionalità/Gruppo',
        'FAC': 'Edificio/Struttura'
    }
    
    # Mappatura POS tags in italiano
    POS_LABELS = {
        'NOUN': 'Nome',
        'VERB': 'Verbo',
        'ADJ': 'Aggettivo',
        'ADV': 'Avverbio',
        'PRON': 'Pronome',
        'DET': 'Determinante',
        'ADP': 'Preposizione',
        'CONJ': 'Congiunzione',
        'NUM': 'Numero',
        'PART': 'Particella',
        'INTJ': 'Interiezione',
        'PROPN': 'Nome Proprio',
        'AUX': 'Ausiliare',
        'PUNCT': 'Punteggiatura',
        'SYM': 'Simbolo',
        'X': 'Altro'
    }
    
    def __new__(cls):
        """Implementazione singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inizializza il modello spaCy (una sola volta)"""
        if LemmatizationService._nlp is None:
            print("🔄 Caricamento modello spaCy it_core_news_lg...")
            try:
                LemmatizationService._nlp = spacy.load("it_core_news_lg")
                print("✅ Modello spaCy caricato con successo!")
            except OSError:
                print("❌ Modello it_core_news_lg non trovato!")
                print("📦 Installalo con: python -m spacy download it_core_news_lg")
                raise
    
    @property
    def nlp(self):
        """Accesso al modello spaCy"""
        if LemmatizationService._nlp is None:
            raise RuntimeError("Modello spaCy non inizializzato correttamente")
        return LemmatizationService._nlp
    
    def lemmatize_word(self, word: str) -> str:
        """
        Lemmatizza una singola parola.
        
        Args:
            word: Parola da lemmatizzare
            
        Returns:
            Forma lemmatizzata (minuscola)
            
        Example:
            >>> service.lemmatize_word("mangiato")
            'mangiare'
            >>> service.lemmatize_word("case")
            'casa'
        """
        if not word or not word.strip():
            return ""
        
        doc = self.nlp(word.strip())
        if len(doc) > 0:
            return doc[0].lemma_.lower()
        return word.lower()
    
    def lemmatize(self, text: str) -> List[Tuple[str, str]]:
        """
        Lemmatizza un testo completo.
        
        Args:
            text: Testo da lemmatizzare
            
        Returns:
            Lista di tuple (parola_originale, lemma)
            
        Example:
            >>> service.lemmatize("I gatti mangiano i topi")
            [('I', 'il'), ('gatti', 'gatto'), ('mangiano', 'mangiare'), 
             ('i', 'il'), ('topi', 'topo')]
        """
        doc = self.nlp(text)
        return [(token.text, token.lemma_.lower()) for token in doc if token.is_alpha]
    
    def get_tokens(self, text: str) -> List[Token]:
        """
        Analizza un testo e restituisce informazioni dettagliate per ogni token.
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Lista di oggetti Token con informazioni complete
        """
        doc = self.nlp(text)
        tokens = []
        
        for token in doc:
            tokens.append(Token(
                text=token.text,
                lemma=token.lemma_.lower(),
                pos=token.pos_,
                tag=token.tag_,
                is_stop=token.is_stop,
                is_alpha=token.is_alpha
            ))
        
        return tokens
    
    def get_pos_tags(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Ottiene i POS tags per ogni parola.
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Lista di tuple (parola, POS_tag, descrizione_italiana)
            
        Example:
            >>> service.get_pos_tags("Il gatto mangia")
            [('Il', 'DET', 'Determinante'), 
             ('gatto', 'NOUN', 'Nome'),
             ('mangia', 'VERB', 'Verbo')]
        """
        doc = self.nlp(text)
        result = []
        
        for token in doc:
            if token.is_alpha:
                pos_desc = self.POS_LABELS.get(token.pos_, token.pos_)
                result.append((token.text, token.pos_, pos_desc))
        
        return result
    
    def get_named_entities(self, text: str) -> List[NamedEntity]:
        """
        Riconosce le entità nominate nel testo (Named Entity Recognition).
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Lista di NamedEntity con informazioni complete
            
        Example:
            >>> service.get_named_entities("Mario Rossi vive a Roma")
            [NamedEntity(text='Mario Rossi', label='PER', label_description='Persona', ...),
             NamedEntity(text='Roma', label='LOC', label_description='Luogo', ...)]
        """
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            label_desc = self.ENTITY_LABELS.get(ent.label_, ent.label_)
            
            entities.append(NamedEntity(
                text=ent.text,
                label=ent.label_,
                label_description=label_desc,
                start_char=ent.start_char,
                end_char=ent.end_char,
                context=ent.sent.text.strip()
            ))
        
        return entities
    
    def get_named_entities_by_type(self, text: str) -> Dict[str, List[str]]:
        """
        Raggruppa le entità nominate per tipo.
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Dizionario {tipo: [entità1, entità2, ...]}
            
        Example:
            >>> service.get_named_entities_by_type("Mario Rossi e Luigi Bianchi vivono a Roma e Milano")
            {
                'PER': ['Mario Rossi', 'Luigi Bianchi'],
                'LOC': ['Roma', 'Milano']
            }
        """
        entities = self.get_named_entities(text)
        result = {}
        
        for entity in entities:
            if entity.label not in result:
                result[entity.label] = []
            
            # Evita duplicati
            if entity.text not in result[entity.label]:
                result[entity.label].append(entity.text)
        
        return result
    
    def get_proper_nouns(self, text: str) -> List[str]:
        """
        Estrae tutti i nomi propri dal testo.
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Lista di nomi propri (senza duplicati)
            
        Example:
            >>> service.get_proper_nouns("Mario e Luigi vanno a Roma")
            ['Mario', 'Luigi', 'Roma']
        """
        doc = self.nlp(text)
        proper_nouns = []
        
        for token in doc:
            if token.pos_ == 'PROPN' and token.text not in proper_nouns:
                proper_nouns.append(token.text)
        
        return proper_nouns
    
    def lemmatize_for_vocabulary(self, text: str) -> List[str]:
        """
        Lemmatizza un testo e restituisce solo i lemmi delle parole significative
        (esclude punteggiatura, numeri, parole funzionali).
        
        Utile per confronto con Vocabolario di Base.
        
        Args:
            text: Testo da lemmatizzare
            
        Returns:
            Lista di lemmi (forme base) delle parole significative
            
        Example:
            >>> service.lemmatize_for_vocabulary("I gatti neri mangiano i topi")
            ['gatto', 'nero', 'mangiare', 'topo']
        """
        doc = self.nlp(text)
        lemmas = []
        
        for token in doc:
            # Solo parole alfabetiche, non stop words, non punteggiatura
            if token.is_alpha and not token.is_stop and token.pos_ not in ['PUNCT', 'SYM', 'X']:
                lemmas.append(token.lemma_.lower())
        
        return lemmas
    
    def analyze_text_complete(self, text: str) -> Dict:
        """
        Analisi completa di un testo con tutte le informazioni NLP disponibili.
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Dizionario con:
            - tokens: Lista di Token
            - lemmas: Lista di tuple (parola, lemma)
            - pos_tags: Lista di tuple (parola, POS, descrizione)
            - named_entities: Lista di NamedEntity
            - entities_by_type: Dizionario entità raggruppate per tipo
            - proper_nouns: Lista nomi propri
            - statistics: Statistiche generali
        """
        doc = self.nlp(text)
        
        # Tokens
        tokens = self.get_tokens(text)
        
        # Lemmas
        lemmas = [(t.text, t.lemma) for t in tokens if t.is_alpha]
        
        # POS tags
        pos_tags = self.get_pos_tags(text)
        
        # Named entities
        named_entities = self.get_named_entities(text)
        entities_by_type = self.get_named_entities_by_type(text)
        
        # Proper nouns
        proper_nouns = self.get_proper_nouns(text)
        
        # Statistics
        word_tokens = [t for t in tokens if t.is_alpha]
        pos_distribution = {}
        for token in word_tokens:
            pos = token.pos
            pos_distribution[pos] = pos_distribution.get(pos, 0) + 1
        
        statistics = {
            'total_tokens': len(tokens),
            'word_tokens': len(word_tokens),
            'unique_lemmas': len(set(t.lemma for t in word_tokens)),
            'named_entities_count': len(named_entities),
            'proper_nouns_count': len(proper_nouns),
            'pos_distribution': pos_distribution,
            'sentences': len(list(doc.sents))
        }
        
        return {
            'tokens': tokens,
            'lemmas': lemmas,
            'pos_tags': pos_tags,
            'named_entities': named_entities,
            'entities_by_type': entities_by_type,
            'proper_nouns': proper_nouns,
            'statistics': statistics
        }


# Singleton globale per import facile
_lemmatization_service_instance = None


def get_lemmatization_service() -> LemmatizationService:
    """Factory function per ottenere l'istanza singleton del servizio"""
    global _lemmatization_service_instance
    if _lemmatization_service_instance is None:
        _lemmatization_service_instance = LemmatizationService()
    return _lemmatization_service_instance
