# enhanced_languagetool.py
"""
Sistema LanguageTool potenziato per l'italiano con regole specializzate.
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LanguageToolError:
    """Errore rilevato da LanguageTool"""
    offset: int
    length: int
    message: str
    short_message: str
    rule_id: str
    category: str
    original_text: str
    suggested_replacements: List[str]
    confidence: float

class EnhancedLanguageTool:
    """LanguageTool potenziato per l'italiano"""
    
    def __init__(self, server_url: str = "http://localhost:8081"):
        self.server_url = server_url
        self.italian_specific_rules = self._get_italian_rules()
        
    def _get_italian_rules(self) -> Dict[str, float]:
        """Regole specifiche italiane con confidenza"""
        return {
            # Regole ad alta confidenza (errori evidenti)
            "MORFOLOGIK_RULE_IT_IT": 0.95,      # Dizionario morfologico
            "ITALIAN_SPELLCHECK": 0.95,          # Controllo ortografico
            "HUNSPELL_RULE_IT_IT": 0.95,        # Hunspell italiano
            "WRONG_APOSTROPHE": 0.95,           # po' vs pò
            "E_APOSTROPHE": 0.95,               # Apostrofi corretti
            "UPPERCASE_SENTENCE_START": 0.95,    # Maiuscole dopo punti
            
            # Regole a media confidenza
            "IT_ACCENTI": 0.85,                 # Accenti corretti
            "PRON_GLI_E_L": 0.85,              # Pronomi gli/le
            "WHITESPACE_RULE": 0.85,           # Spazi errati
            "COMMA_WHITESPACE": 0.85,          # Spazi virgole
            "PERIOD_WHITESPACE": 0.85,         # Spazi punti
            
            # Regole specifiche per errori comuni
            "IT_AGREEMENT": 0.80,              # Concordanze
            "ITALIAN_WORD_COHERENCY": 0.80,    # Coerenza lessicale
            "WORD_REPEAT_RULE": 0.90,          # Parole duplicate
            "REPEATED_WORDS": 0.90,            # Ripetizioni
            
            # Regole per punteggiatura
            "MULTIPLE_EXCLAMATION_MARK": 0.80,
            "MULTIPLE_QUESTION_MARK": 0.80,
            "DOUBLE_PUNCTUATION": 0.80,
            "UNPAIRED_BRACKETS": 0.90,
        }
    
    def check_text(self, text: str) -> List[LanguageToolError]:
        """Controlla il testo con LanguageTool"""
        if not text.strip():
            return []
            
        try:
            # Prepara la richiesta
            data = {
                'text': text,
                'language': 'it',
                'enabledRules': ','.join(self.italian_specific_rules.keys()),
                'disabledRules': 'COMMA_PARENTHESIS_WHITESPACE,TYPOGRAPHY'  # Regole problematiche
            }
            
            # Invia richiesta
            response = requests.post(
                f"{self.server_url}/v2/check",
                data=data,
                timeout=20
            )
            
            if response.status_code != 200:
                logger.warning(f"LanguageTool error: {response.status_code}")
                return []
                
            result = response.json()
            errors = []
            
            # Processa gli errori
            for match in result.get('matches', []):
                rule_id = match.get('rule', {}).get('id', '')
                confidence = self.italian_specific_rules.get(rule_id, 0.5)
                
                # Filtra errori a bassa confidenza
                if confidence < 0.7:
                    continue
                    
                error = LanguageToolError(
                    offset=match.get('offset', 0),
                    length=match.get('length', 0),
                    message=match.get('message', ''),
                    short_message=match.get('shortMessage', ''),
                    rule_id=rule_id,
                    category=match.get('rule', {}).get('category', {}).get('name', ''),
                    original_text=text[match.get('offset', 0):match.get('offset', 0) + match.get('length', 0)],
                    suggested_replacements=[r['value'] for r in match.get('replacements', [])[:3]],  # Prime 3 suggerimenti
                    confidence=confidence
                )
                
                errors.append(error)
                
            # Ordina per confidenza decrescente
            errors.sort(key=lambda x: x.confidence, reverse=True)
            
            logger.info(f"LanguageTool trovato {len(errors)} errori")
            return errors
            
        except Exception as e:
            logger.error(f"Errore LanguageTool: {e}")
            return []
    
    def apply_corrections(self, text: str, errors: List[LanguageToolError], confidence_threshold: float = 0.8) -> Tuple[str, List[Tuple[str, str]]]:
        """Applica correzioni di alta confidenza"""
        if not errors:
            return text, []
            
        corrections = []
        current_text = text
        offset_adjustment = 0
        
        # Applica correzioni dall'ultima alla prima per mantenere offset
        for error in sorted(errors, key=lambda x: x.offset, reverse=True):
            if error.confidence < confidence_threshold:
                continue
                
            if not error.suggested_replacements:
                continue
                
            # Prendi il primo suggerimento (di solito il migliore)
            replacement = error.suggested_replacements[0]
            
            # Verifica che il testo corrisponda ancora
            start = error.offset
            end = error.offset + error.length
            
            if end <= len(current_text) and current_text[start:end] == error.original_text:
                # Applica correzione
                current_text = current_text[:start] + replacement + current_text[end:]
                corrections.append((error.original_text, replacement))
                
                logger.info(f"🔧 LT[{error.confidence:.0%}]: '{error.original_text}' → '{replacement}' ({error.rule_id})")
        
        return current_text, corrections
    
    def get_specific_corrections(self, text: str) -> Dict[str, List[str]]:
        """Ottieni correzioni specifiche per categoria"""
        errors = self.check_text(text)
        
        categories = {
            "orthography": [],      # Errori ortografici
            "grammar": [],          # Errori grammaticali
            "punctuation": [],      # Punteggiatura
            "spacing": [],          # Spazi
            "style": []            # Stile
        }
        
        for error in errors:
            category_name = error.category.lower()
            
            if error.rule_id.startswith("MORFOLOGIK") or "SPELLCHECK" in error.rule_id:
                categories["orthography"].append(error.original_text + " → " + (error.suggested_replacements[0] if error.suggested_replacements else "?"))
            elif "WHITESPACE" in error.rule_id or "SPACE" in error.rule_id:
                categories["spacing"].append(error.original_text + " → " + (error.suggested_replacements[0] if error.suggested_replacements else "?"))
            elif "PUNCTUATION" in error.rule_id or error.rule_id.endswith("_MARK"):
                categories["punctuation"].append(error.original_text + " → " + (error.suggested_replacements[0] if error.suggested_replacements else "?"))
            elif "AGREEMENT" in error.rule_id or "COHERENCY" in error.rule_id:
                categories["grammar"].append(error.original_text + " → " + (error.suggested_replacements[0] if error.suggested_replacements else "?"))
            else:
                categories["style"].append(error.original_text + " → " + (error.suggested_replacements[0] if error.suggested_replacements else "?"))
                
        return categories

class ItalianSpecificCorrector:
    """Correttore specializzato per problemi specifici italiani"""
    
    def __init__(self):
        self.space_fixes = [
            # Casi specifici per "U" all'inizio
            (r'\bU\s+([aeiouAEIOU])', r'Un \1'),  # "U amore" → "Un amore"
            (r'\bU\s+giorno', 'Un giorno'),       # "U giorno" → "Un giorno"
            (r'\bU\s+uomo', 'Un uomo'),           # "U uomo" → "Un uomo"
            (r'\bU\s+([bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ])', r'Un \1'),  # "U giorno" → "Un giorno"
            
            # Altri errori di spazio
            (r'\s{2,}', ' '),  # Spazi multipli
            (r'([a-zA-Z])([.!?])([A-Z])', r'\1\2 \3'),  # Punteggiatura senza spazio
        ]
        
        self.italian_replacements = {
            # Casi come "bottaga" → "bottega" (non "bottaia")
            "bottaga": "bottega",
            "ansiano": "anziano",
            
            # Altri errori tipici
            "cera": "c'era",  # quando appropriato
            "arrocato": "arroccato",
        }
    
    def fix_specific_errors(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        """Corregge errori specifici italiani"""
        corrections = []
        current_text = text
        
        # 1. Fixes di spazio
        for pattern, replacement in self.space_fixes:
            matches = list(re.finditer(pattern, current_text))
            for match in matches:
                original = match.group()
                new_text = re.sub(pattern, replacement, current_text)
                if new_text != current_text:
                    corrected_part = new_text[match.start():match.start() + len(replacement)]
                    corrections.append((original, corrected_part))
                    current_text = new_text
                    break  # Un fix alla volta per mantenere offset
        
        # 2. Sostituzioni dirette
        for wrong, correct in self.italian_replacements.items():
            if wrong in current_text:
                current_text = current_text.replace(wrong, correct)
                corrections.append((wrong, correct))
        
        return current_text, corrections
