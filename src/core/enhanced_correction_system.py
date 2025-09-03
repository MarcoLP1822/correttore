# enhanced_correction_system.py
"""
Sistema di correzione multi-livello per italiano con alta precisione.
Combina: dizionario italiano + LanguageTool + AI intelligente + validazione
"""

import re
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from pathlib import Path
import json
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

@dataclass
class CorrectionLevel:
    """Livello di correzione con confidenza"""
    name: str
    confidence: float
    corrections: List[Tuple[str, str]]  # (originale, corretto)
    reason: str

class EnhancedCorrectionSystem:
    """Sistema di correzione multi-livello per italiano"""
    
    def __init__(self):
        self.italian_dictionary = self._load_italian_corrections()
        self.common_errors = self._load_common_errors()
        self.space_patterns = self._load_space_patterns()
        
    def _load_italian_corrections(self) -> Dict[str, str]:
        """Carica dizionario di correzioni italiane comuni"""
        return {
            # Errori tipografici comuni
            "bottaga": "bottega",
            "ansiano": "anziano", 
            "fallegname": "falegname",
            "vlta": "volta",
            "borggo": "borgo",
            "milliore": "migliore",
            "trasformazzione": "trasformazione",
            "strignendo": "stringendo",
            "cassella": "casella",
            "carezzzzavano": "carezzavano",
            "prontal": "pronta",
            "ringrazio": "ringraziò",
            "fato": "fatto",
            "sugu": "suga",
            "desfo": "disfo",
            
            # Errori di accenti
            "pò": "po'",
            "è": "e",  # quando sbagliato nel contesto
            "perchè": "perché",
            "perche": "perché",
            "finchè": "finché",
            "finche": "finché",
            "poichè": "poiché",
            "poiche": "poiché",
            
            # Articoli e preposizioni
            "qual'è": "qual è",
            "quell'altro": "quell'altro",
            "un'altro": "un altro",
            "un'ultima": "un'ultima",
            
            # Doppie consonanti
            "abilità": "abilità",
            "addosso": "addosso",
            "affatto": "affatto",
            "aggettivo": "aggettivo",
            "allora": "allora",
            "ammazzare": "ammazzare",
            "annullare": "annullare",
            "appunto": "appunto",
            "attraversare": "attraversare",
            "avvolgere": "avvolgere",
            "baccello": "baccello",
            "bellezza": "bellezza",
            "bello": "bello",
            "cappotto": "cappotto",
            "cattivo": "cattivo",
            "collina": "collina",
            "corridoio": "corridoio",
            "davvero": "davvero",
            "dottore": "dottore",
            "effetto": "effetto",
            "femmina": "femmina",
            "gatto": "gatto",
            "ghiaccio": "ghiaccio",
            "giallo": "giallo",
            "governo": "governo",
            "letto": "letto",
            "mamma": "mamma",
            "mattina": "mattina",
            "occhio": "occhio",
            "pezzo": "pezzo",
            "possibile": "possibile",
            "rosso": "rosso",
            "settimana": "settimana",
            "soprattutto": "soprattutto",
            "successo": "successo",
            "terra": "terra",
            "ufficio": "ufficio",
            "vetro": "vetro",
            "villa": "villa",
        }
    
    def _load_common_errors(self) -> Dict[str, str]:
        """Carica errori grammaticali comuni"""
        return {
            # Errori di concordanza
            "la cane": "il cane",
            "il tavola": "la tavola", 
            "un'uomo": "un uomo",
            "una uomo": "un uomo",
            "gli donna": "la donna",
            "le uomo": "l'uomo",
            
            # H nel verbo avere
            "o fatto": "ho fatto",
            "o detto": "ho detto",
            "o visto": "ho visto",
            "a fatto": "ha fatto",
            "a detto": "ha detto",
            "a visto": "ha visto",
            "anno fatto": "hanno fatto",
            "anno detto": "hanno detto",
            
            # GLI vs LE
            "gli ho detto": "le ho detto",  # a una donna
            "le ho detto": "gli ho detto",  # a un uomo (context dependent)
            
            # Essere/Stare
            "sto bene": "sto bene",  # corretto
            "sono bene": "sto bene",
            
            # Futuro
            "avrò": "avrò",
            "andrò": "andrò",
            "sarò": "sarò",
        }
    
    def _load_space_patterns(self) -> List[Tuple[str, str]]:
        """Carica pattern per correggere spazi"""
        return [
            # Spazi mancanti
            (r'\bU\s+([aeiouAEIOU])', r'Un \1'),  # "U giorno" → "Un giorno"
            (r'\bU([aeiouAEIOU])', r'Un \1'),      # "Ugiorno" → "Un giorno"
            (r'\bun\s*([aeiouAEIOU])', r"un'\1"),  # "un amore" → "un amore" (no change) o "un'amore" se necessario
            (r'\bUn\s*([aeiouAEIOU])', r"Un '\1"), # Pattern con apostrofo se necessario
            
            # Spazi doppi
            (r'\s{2,}', ' '),  # spazi multipli → spazio singolo
            
            # Punteggiatura
            (r'([a-zA-Z])([.!?])', r'\1 \2'),      # "ciao.come" → "ciao. come"
            (r'([.!?])([A-Z])', r'\1 \2'),         # "ciao.Come" → "ciao. Come"
            (r'([a-zA-Z]),([a-zA-Z])', r'\1, \2'), # "ciao,come" → "ciao, come"
            
            # Apostrofi
            (r"(\w)'(\w)", r"\1'\2"),              # apostrofo tipografico
            (r"(\w) '(\w)", r"\1'\2"),             # rimuovi spazio prima apostrofo
        ]
    
    async def correct_text_multilevel(self, text: str, client: AsyncOpenAI) -> Tuple[str, List[CorrectionLevel]]:
        """
        Correzione multi-livello:
        1. Dizionario italiano (alta confidenza)
        2. Pattern spazi/punteggiatura (alta confidenza)
        3. Errori grammaticali comuni (media confidenza)
        4. AI intelligente per casi complessi (media-bassa confidenza)
        """
        if not text.strip():
            return text, []
            
        original_text = text
        current_text = text
        correction_levels = []
        
        # LIVELLO 1: Dizionario italiano (confidenza 95%)
        level1_text, level1_corrections = self._apply_dictionary_corrections(current_text)
        if level1_corrections:
            correction_levels.append(CorrectionLevel(
                name="Dizionario Italiano",
                confidence=0.95,
                corrections=level1_corrections,
                reason="Correzioni ortografiche da dizionario"
            ))
            current_text = level1_text
            
        # LIVELLO 2: Pattern spazi (confidenza 90%)
        level2_text, level2_corrections = self._apply_space_corrections(current_text)
        if level2_corrections:
            correction_levels.append(CorrectionLevel(
                name="Correzione Spazi",
                confidence=0.90,
                corrections=level2_corrections,
                reason="Correzione spazi e punteggiatura"
            ))
            current_text = level2_text
            
        # LIVELLO 3: Errori grammaticali comuni (confidenza 85%)
        level3_text, level3_corrections = self._apply_grammar_corrections(current_text)
        if level3_corrections:
            correction_levels.append(CorrectionLevel(
                name="Grammatica Comune",
                confidence=0.85,
                corrections=level3_corrections,
                reason="Correzioni grammaticali comuni"
            ))
            current_text = level3_text
            
        # LIVELLO 4: AI per casi complessi (confidenza 75%)
        if self._needs_ai_correction(original_text, current_text):
            level4_text, level4_corrections = await self._apply_ai_corrections(current_text, client)
            if level4_corrections:
                correction_levels.append(CorrectionLevel(
                    name="AI Intelligente", 
                    confidence=0.75,
                    corrections=level4_corrections,
                    reason="Correzioni AI per casi complessi"
                ))
                current_text = level4_text
        
        return current_text, correction_levels
    
    def _apply_dictionary_corrections(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        """Applica correzioni da dizionario italiano"""
        corrections = []
        current_text = text
        
        # Ordina per lunghezza decrescente per evitare sostituzioni parziali
        sorted_corrections = sorted(self.italian_dictionary.items(), key=lambda x: len(x[0]), reverse=True)
        
        for wrong, correct in sorted_corrections:
            # Cerca parole intere, non parti di parole
            pattern = r'\b' + re.escape(wrong) + r'\b'
            match = re.search(pattern, current_text, re.IGNORECASE)
            if match:
                original_word = match.group()
                # Mantieni la capitalizzazione originale
                if original_word.isupper():
                    correct_word = correct.upper()
                elif original_word.istitle():
                    correct_word = correct.title()
                else:
                    correct_word = correct
                    
                new_text = re.sub(pattern, correct_word, current_text, flags=re.IGNORECASE)
                if new_text != current_text:
                    corrections.append((original_word, correct_word))
                    current_text = new_text
                    logger.info(f"📖 Dizionario: '{original_word}' → '{correct_word}'")
        
        return current_text, corrections
    
    def _apply_space_corrections(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        """Applica correzioni di spazi e punteggiatura"""
        corrections = []
        current_text = text
        
        for pattern, replacement in self.space_patterns:
            matches = re.finditer(pattern, current_text)
            for match in matches:
                original = match.group()
                corrected = re.sub(pattern, replacement, original)
                if original != corrected:
                    corrections.append((original, corrected))
                    logger.info(f"📏 Spazi: '{original}' → '{corrected}'")
            
            current_text = re.sub(pattern, replacement, current_text)
        
        return current_text, corrections
    
    def _apply_grammar_corrections(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        """Applica correzioni grammaticali comuni"""
        corrections = []
        current_text = text
        
        for wrong, correct in self.common_errors.items():
            if wrong in current_text:
                current_text = current_text.replace(wrong, correct)
                corrections.append((wrong, correct))
                logger.info(f"📝 Grammatica: '{wrong}' → '{correct}'")
        
        return current_text, corrections
    
    def _needs_ai_correction(self, original: str, current: str) -> bool:
        """Determina se serve correzione AI aggiuntiva"""
        # Controlla se ci sono ancora potenziali errori
        potential_errors = [
            r'\b\w*[zx]{2,}\w*\b',  # lettere ripetute anomale
            r'\b\w*[aeiou]{3,}\w*\b',  # vocali consecutive anomale
            r'\b[bcdfghjklmnpqrstvwxyz]{4,}\b',  # troppe consonanti
            r'\b\w{20,}\b',  # parole troppo lunghe
        ]
        
        for pattern in potential_errors:
            if re.search(pattern, current, re.IGNORECASE):
                return True
        
        # Se il testo è cambiato poco, potrebbe servire AI
        similarity = len(set(original.split()) & set(current.split())) / max(len(original.split()), 1)
        return similarity > 0.8  # Se è ancora molto simile, prova AI
    
    async def _apply_ai_corrections(self, text: str, client: AsyncOpenAI) -> Tuple[str, List[Tuple[str, str]]]:
        """Applica correzioni AI per casi complessi"""
        corrections = []
        
        # Prompt specializzato per errori residui
        enhanced_prompt = f"""
Sei un esperto correttore italiano. Il seguente testo è già stato corretto per errori basici.
Cerca SOLO errori sottili che rimangono:

1. Refusi complessi non standard
2. Errori di battitura creativi
3. Problemi di concordanza verbale
4. Errori di tempi verbali

NON modificare:
- Stile dell'autore
- Punteggiatura se è accettabile
- Parole che potrebbero essere corrette ma non sono errori

TESTO: {text}

Rispondi SOLO con JSON:
{{"corretto": "TESTO_CORRETTO"}}
"""

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,  # Leggermente più creativo per refusi
                messages=[
                    {"role": "system", "content": "Sei un correttore di bozze esperto per l'italiano."},
                    {"role": "user", "content": enhanced_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                data = json.loads(content)
                corrected_text = data.get("corretto", text)
                
                if corrected_text != text:
                    corrections.append((text, corrected_text))
                    logger.info(f"🤖 AI: Correzione applicata")
                    return corrected_text, corrections
                    
        except Exception as e:
            logger.error(f"Errore AI: {e}")
            
        return text, corrections
    
    def get_correction_summary(self, levels: List[CorrectionLevel]) -> Dict:
        """Genera riassunto delle correzioni"""
        total_corrections = sum(len(level.corrections) for level in levels)
        avg_confidence = sum(level.confidence for level in levels) / max(len(levels), 1)
        
        return {
            "total_corrections": total_corrections,
            "average_confidence": avg_confidence,
            "levels_applied": len(levels),
            "details": [
                {
                    "level": level.name,
                    "confidence": level.confidence,
                    "corrections_count": len(level.corrections),
                    "reason": level.reason
                }
                for level in levels
            ]
        }
