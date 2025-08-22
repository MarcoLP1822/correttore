# utils/text_processing.py
"""
Utilities per elaborazione testo: tokenization, chunking, normalizzazione.
Funzioni pure senza side effects per massima testabilità e riusabilità.
"""

import re
import logging
from typing import List, Tuple, Dict, Any, Optional, Iterator
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ChunkStrategy(Enum):
    """Strategie di chunking del testo"""
    SENTENCE_BASED = "sentence"
    PARAGRAPH_BASED = "paragraph"
    TOKEN_BASED = "token"
    FIXED_SIZE = "fixed"

@dataclass
class TextChunk:
    """Chunk di testo con metadati"""
    text: str
    start_offset: int
    end_offset: int
    chunk_index: int
    strategy: ChunkStrategy
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TextStatistics:
    """Statistiche di un testo"""
    character_count: int
    word_count: int
    sentence_count: int
    paragraph_count: int
    avg_sentence_length: float
    avg_word_length: float
    readability_score: float = 0.0

class TextProcessor:
    """
    Processore di testo con funzioni di analisi, chunking e normalizzazione.
    Tutte le funzioni sono stateless per massima affidabilità.
    """
    
    # Pattern regex precompilati per performance
    SENTENCE_PATTERN = re.compile(r'(?<=[.!?])\s+(?=[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ])')
    WORD_PATTERN = re.compile(r'\b\w+\b')
    PARAGRAPH_PATTERN = re.compile(r'\n\s*\n')
    WHITESPACE_PATTERN = re.compile(r'\s+')
    PUNCTUATION_SPACING_PATTERN = re.compile(r'([.!?:;,])\s*([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ])')
    
    @staticmethod
    def split_into_sentences(text: str, preserve_boundaries: bool = True) -> List[str]:
        """
        Suddivide testo in frasi preservando punteggiatura e spaziatura.
        
        Args:
            text: Testo da suddividere
            preserve_boundaries: Se preservare spazi e confini originali
            
        Returns:
            List[str]: Lista di frasi
        """
        if not text.strip():
            return []
        
        # Split base per frasi
        sentences = TextProcessor.SENTENCE_PATTERN.split(text.strip())
        
        if not preserve_boundaries:
            return [s.strip() for s in sentences if s.strip()]
        
        # Ricostruisci preservando spazi originali
        result = []
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                result.append(sentence)
        
        return result
    
    @staticmethod
    def split_into_words(text: str, include_positions: bool = False) -> List[str] | List[Tuple[str, int, int]]:
        """
        Estrae parole dal testo con posizioni opzionali.
        
        Args:
            text: Testo da analizzare
            include_positions: Se includere posizioni start/end
            
        Returns:
            Lista di parole o tuple (parola, start, end)
        """
        if include_positions:
            words_with_pos = []
            for match in TextProcessor.WORD_PATTERN.finditer(text):
                words_with_pos.append((match.group(), match.start(), match.end()))
            return words_with_pos
        else:
            return TextProcessor.WORD_PATTERN.findall(text)
    
    @staticmethod
    def split_into_paragraphs(text: str, min_length: int = 10) -> List[str]:
        """
        Suddivide testo in paragrafi filtrati per lunghezza minima.
        
        Args:
            text: Testo da suddividere
            min_length: Lunghezza minima paragrafo
            
        Returns:
            List[str]: Lista di paragrafi
        """
        paragraphs = TextProcessor.PARAGRAPH_PATTERN.split(text)
        return [p.strip() for p in paragraphs if len(p.strip()) >= min_length]
    
    @staticmethod
    def chunk_text(text: str, 
                   strategy: ChunkStrategy = ChunkStrategy.SENTENCE_BASED,
                   max_size: int = 1000,
                   overlap: int = 50) -> List[TextChunk]:
        """
        Suddivide testo in chunk secondo strategia specificata.
        
        Args:
            text: Testo da dividere
            strategy: Strategia di chunking
            max_size: Dimensione massima chunk (caratteri o token)
            overlap: Sovrapposizione tra chunk (caratteri)
            
        Returns:
            List[TextChunk]: Lista di chunk
        """
        if not text.strip():
            return []
        
        if strategy == ChunkStrategy.SENTENCE_BASED:
            return TextProcessor._chunk_by_sentences(text, max_size, overlap)
        elif strategy == ChunkStrategy.PARAGRAPH_BASED:
            return TextProcessor._chunk_by_paragraphs(text, max_size)
        elif strategy == ChunkStrategy.TOKEN_BASED:
            return TextProcessor._chunk_by_tokens(text, max_size, overlap)
        elif strategy == ChunkStrategy.FIXED_SIZE:
            return TextProcessor._chunk_by_fixed_size(text, max_size, overlap)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
    
    @staticmethod
    def normalize_whitespace(text: str, preserve_paragraphs: bool = True) -> str:
        """
        Normalizza spazi bianchi nel testo.
        
        Args:
            text: Testo da normalizzare
            preserve_paragraphs: Se preservare separatori paragrafo
            
        Returns:
            str: Testo normalizzato
        """
        if preserve_paragraphs:
            # Preserva paragrafi ma normalizza spazi interni
            paragraphs = text.split('\n\n')
            normalized_paragraphs = []
            
            for para in paragraphs:
                # Normalizza spazi dentro il paragrafo
                normalized = TextProcessor.WHITESPACE_PATTERN.sub(' ', para.strip())
                if normalized:
                    normalized_paragraphs.append(normalized)
            
            return '\n\n'.join(normalized_paragraphs)
        else:
            # Normalizzazione globale
            return TextProcessor.WHITESPACE_PATTERN.sub(' ', text.strip())
    
    @staticmethod
    def fix_punctuation_spacing(text: str) -> str:
        """
        Corregge spaziatura dopo punteggiatura.
        
        Args:
            text: Testo da correggere
            
        Returns:
            str: Testo con spaziatura corretta
        """
        # Correggi spazio dopo punteggiatura
        fixed = TextProcessor.PUNCTUATION_SPACING_PATTERN.sub(r'\1 \2', text)
        
        # Correggi spazi multipli
        fixed = TextProcessor.WHITESPACE_PATTERN.sub(' ', fixed)
        
        return fixed.strip()
    
    @staticmethod
    def calculate_statistics(text: str) -> TextStatistics:
        """
        Calcola statistiche dettagliate del testo.
        
        Args:
            text: Testo da analizzare
            
        Returns:
            TextStatistics: Statistiche complete
        """
        if not text.strip():
            return TextStatistics(0, 0, 0, 0, 0.0, 0.0, 0.0)
        
        # Conteggi base
        char_count = len(text)
        words = TextProcessor.split_into_words(text)
        word_count = len(words)
        sentences = TextProcessor.split_into_sentences(text)
        sentence_count = len(sentences)
        paragraphs = TextProcessor.split_into_paragraphs(text)
        paragraph_count = len(paragraphs)
        
        # Medie
        avg_sentence_length = char_count / sentence_count if sentence_count > 0 else 0.0
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0.0
        
        # Punteggio di leggibilità semplificato (basato su lunghezza frasi e parole)
        readability = TextProcessor._calculate_readability_score(sentences, words)
        
        return TextStatistics(
            character_count=char_count,
            word_count=word_count,
            sentence_count=sentence_count,
            paragraph_count=paragraph_count,
            avg_sentence_length=avg_sentence_length,
            avg_word_length=avg_word_length,
            readability_score=readability
        )
    
    @staticmethod
    def extract_special_elements(text: str) -> Dict[str, List[str]]:
        """
        Estrae elementi speciali dal testo (date, numeri, email, URL, etc).
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Dict[str, List[str]]: Elementi speciali categorizzati
        """
        patterns = {
            'dates': r'\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b',
            'times': r'\b\d{1,2}:\d{2}(?::\d{2})?\b',
            'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'urls': r'https?://[^\s]+',
            'numbers': r'\b\d+(?:[.,]\d+)?\b',
            'phone_numbers': r'\b(?:\+39)?[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
            'currencies': r'€\s*\d+(?:[.,]\d+)?|\d+(?:[.,]\d+)?\s*€',
        }
        
        results = {}
        for category, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            results[category] = list(set(matches))  # Rimuovi duplicati
        
        return results
    
    @staticmethod
    def find_repeated_patterns(text: str, min_length: int = 10) -> List[Tuple[str, int]]:
        """
        Trova pattern ripetuti nel testo (possibile indicatore di errori).
        
        Args:
            text: Testo da analizzare
            min_length: Lunghezza minima pattern
            
        Returns:
            List[Tuple[str, int]]: Lista di (pattern, occorrenze)
        """
        words = text.split()
        patterns = {}
        
        # Cerca pattern di lunghezza variabile
        for i in range(len(words)):
            for length in range(min_length, min(len(words) - i + 1, 50)):  # Max 50 parole
                pattern = ' '.join(words[i:i + length])
                
                if len(pattern) >= min_length:
                    patterns[pattern] = patterns.get(pattern, 0) + 1
        
        # Filtra solo pattern ripetuti (>1 occorrenza)
        repeated = [(pattern, count) for pattern, count in patterns.items() if count > 1]
        
        # Ordina per numero di occorrenze
        repeated.sort(key=lambda x: x[1], reverse=True)
        
        return repeated[:20]  # Top 20 pattern ripetuti
    
    # Metodi privati di supporto
    
    @staticmethod
    def _chunk_by_sentences(text: str, max_size: int, overlap: int) -> List[TextChunk]:
        """Chunking basato su frasi"""
        sentences = TextProcessor.split_into_sentences(text, preserve_boundaries=True)
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for sentence in sentences:
            # Se aggiungere la frase supera max_size e abbiamo già contenuto
            if len(current_chunk + sentence) > max_size and current_chunk:
                # Crea chunk corrente
                chunk_end = current_start + len(current_chunk)
                chunks.append(TextChunk(
                    text=current_chunk.strip(),
                    start_offset=current_start,
                    end_offset=chunk_end,
                    chunk_index=chunk_index,
                    strategy=ChunkStrategy.SENTENCE_BASED
                ))
                
                # Inizia nuovo chunk con overlap
                overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
                current_chunk = overlap_text + sentence
                current_start = chunk_end - len(overlap_text)
                chunk_index += 1
            else:
                current_chunk += sentence
        
        # Aggiungi ultimo chunk se non vuoto
        if current_chunk.strip():
            chunks.append(TextChunk(
                text=current_chunk.strip(),
                start_offset=current_start,
                end_offset=current_start + len(current_chunk),
                chunk_index=chunk_index,
                strategy=ChunkStrategy.SENTENCE_BASED
            ))
        
        return chunks
    
    @staticmethod
    def _chunk_by_paragraphs(text: str, max_size: int) -> List[TextChunk]:
        """Chunking basato su paragrafi"""
        paragraphs = TextProcessor.split_into_paragraphs(text)
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for paragraph in paragraphs:
            if len(current_chunk + paragraph) > max_size and current_chunk:
                # Crea chunk corrente
                chunk_end = current_start + len(current_chunk)
                chunks.append(TextChunk(
                    text=current_chunk.strip(),
                    start_offset=current_start,
                    end_offset=chunk_end,
                    chunk_index=chunk_index,
                    strategy=ChunkStrategy.PARAGRAPH_BASED
                ))
                
                current_chunk = paragraph
                current_start = chunk_end
                chunk_index += 1
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Aggiungi ultimo chunk
        if current_chunk.strip():
            chunks.append(TextChunk(
                text=current_chunk.strip(),
                start_offset=current_start,
                end_offset=current_start + len(current_chunk),
                chunk_index=chunk_index,
                strategy=ChunkStrategy.PARAGRAPH_BASED
            ))
        
        return chunks
    
    @staticmethod
    def _chunk_by_tokens(text: str, max_tokens: int, overlap: int) -> List[TextChunk]:
        """Chunking basato su token (approssimazione con parole)"""
        words = text.split()
        chunks = []
        chunk_index = 0
        
        i = 0
        while i < len(words):
            # Prendi max_tokens parole
            chunk_words = words[i:i + max_tokens]
            chunk_text = ' '.join(chunk_words)
            
            # Calcola offset nel testo originale (approssimativo)
            start_offset = len(' '.join(words[:i]))
            if start_offset > 0:
                start_offset += 1  # Spazio prima
            
            chunks.append(TextChunk(
                text=chunk_text,
                start_offset=start_offset,
                end_offset=start_offset + len(chunk_text),
                chunk_index=chunk_index,
                strategy=ChunkStrategy.TOKEN_BASED
            ))
            
            # Avanza con overlap
            i += max_tokens - overlap
            chunk_index += 1
        
        return chunks
    
    @staticmethod
    def _chunk_by_fixed_size(text: str, size: int, overlap: int) -> List[TextChunk]:
        """Chunking a dimensione fissa con overlap"""
        chunks = []
        chunk_index = 0
        
        i = 0
        while i < len(text):
            chunk_text = text[i:i + size]
            
            chunks.append(TextChunk(
                text=chunk_text,
                start_offset=i,
                end_offset=i + len(chunk_text),
                chunk_index=chunk_index,
                strategy=ChunkStrategy.FIXED_SIZE
            ))
            
            i += size - overlap
            chunk_index += 1
        
        return chunks
    
    @staticmethod
    def _calculate_readability_score(sentences: List[str], words: List[str]) -> float:
        """Calcola punteggio di leggibilità semplificato"""
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Formula semplificata: più frasi corte e parole corte = più leggibile
        # Punteggio 0-100 (100 = molto leggibile)
        readability = max(0, 100 - (avg_sentence_length * 2) - (avg_word_length * 5))
        
        return min(100, readability)


# Funzioni di utilità standalone

def merge_chunks(chunks: List[TextChunk], separator: str = " ") -> str:
    """Riunisce una lista di chunk in un unico testo"""
    return separator.join(chunk.text for chunk in chunks)

def find_chunk_overlaps(chunks: List[TextChunk]) -> List[Tuple[int, int, int]]:
    """Trova sovrapposizioni tra chunk adiacenti"""
    overlaps = []
    
    for i in range(len(chunks) - 1):
        current = chunks[i]
        next_chunk = chunks[i + 1]
        
        if current.end_offset > next_chunk.start_offset:
            overlap_size = current.end_offset - next_chunk.start_offset
            overlaps.append((i, i + 1, overlap_size))
    
    return overlaps

def estimate_processing_time(text: str, words_per_minute: int = 1000) -> float:
    """Stima tempo di elaborazione basato su lunghezza testo"""
    word_count = len(TextProcessor.split_into_words(text))
    return word_count / words_per_minute * 60  # secondi
