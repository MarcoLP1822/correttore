# services/languagetool_service.py
"""
Servizio per l'integrazione con LanguageTool.
Gestisce il controllo grammaticale locale con regole personalizzate e whitelisting.
"""

import logging
import subprocess
import tempfile
import json
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from pathlib import Path

from correttore.config.settings import get_languagetool_config
from correttore.services.intelligent_cache import get_cache
from correttore.models import (
    CorrectionRecord,
    CorrectionCategory,
    CorrectionSource,
)

logger = logging.getLogger(__name__)

@dataclass
class LanguageToolError:
    """Errore rilevato da LanguageTool"""
    message: str
    short_message: str
    offset: int
    length: int
    rule_id: str
    category: str
    replacements: List[str]
    context: str
    severity: str = "info"

@dataclass
class LanguageToolResult:
    """Risultato dell'analisi LanguageTool"""
    text: str
    errors: List[LanguageToolError]
    processing_time: float
    success: bool
    error_message: Optional[str] = None

class LanguageToolService:
    """
    Servizio per controllo grammaticale con LanguageTool.
    Supporta regole personalizzate, whitelisting e caching.
    """
    
    def __init__(self):
        self.config = get_languagetool_config()
        self.cache_service = get_cache()
        
        # Carica regole personalizzate e whitelist
        self.whitelisted_rules = self._load_whitelisted_rules()
        self.custom_rules = self._load_custom_rules()
        
        # Verifica disponibilità LanguageTool
        self._verify_languagetool_installation()
        
        logger.info(f"📝 LanguageTool Service initialized with {len(self.whitelisted_rules)} whitelisted rules")
    
    def check_text(self, text: str, use_cache: bool = True) -> List[LanguageToolError]:
        """
        Controlla un testo per errori grammaticali.
        
        Args:
            text: Testo da controllare
            use_cache: Se utilizzare la cache
            
        Returns:
            List[LanguageToolError]: Lista di errori trovati
        """
        if not text.strip():
            return []
        
        # Check cache
        cached_errors = None  # evita UnboundLocalError e salti di flusso
        if use_cache:
            cache_key = self._generate_cache_key(text)
            cached_entry = self.cache_service.get_with_similarity(text)
            if cached_entry and cached_entry.correction_type == 'languagetool':
                cached_errors = eval(cached_entry.corrected_text)  # Deserializza errori
        if cached_errors is not None:
            logger.debug("💾 Cache hit for LanguageTool check")
            return cached_errors
        
        # Esegui controllo
        result = self._run_languagetool_check(text)
        
        if result.success:
            # Filtra errori con whitelist
            filtered_errors = self._filter_whitelisted_errors(result.errors)
            
            # Cache il risultato
            if use_cache:
                # Salva risultato in cache serializzando gli errori
                self.cache_service.cache_with_metadata(
                    text=text,
                    correction=str(filtered_errors),  # Serializza come stringa
                    quality=0.8,
                    correction_type='languagetool'
                )
            
            logger.debug(f"📝 LanguageTool found {len(filtered_errors)} errors ({len(result.errors)} total, {len(result.errors) - len(filtered_errors)} whitelisted)")
            return filtered_errors
        else:
            logger.error(f"❌ LanguageTool check failed: {result.error_message}")
            return []
    
    def check_file(self, file_path: Path) -> LanguageToolResult:
        """
        Controlla un file di testo completo.
        
        Args:
            file_path: Percorso del file da controllare
            
        Returns:
            LanguageToolResult: Risultato completo del controllo
        """
        try:
            text = file_path.read_text(encoding='utf-8')
            return self._run_languagetool_check(text)
        except Exception as e:
            logger.error(f"❌ Failed to check file {file_path}: {e}")
            return LanguageToolResult(
                text="",
                errors=[],
                processing_time=0.0,
                success=False,
                error_message=str(e)
            )
    
    def suggest_corrections(self, text: str, error: LanguageToolError) -> List[str]:
        """
        Suggerisce correzioni per un errore specifico.
        
        Args:
            text: Testo originale
            error: Errore da correggere
            
        Returns:
            List[str]: Lista di possibili correzioni
        """
        # LanguageTool fornisce già suggerimenti
        suggestions = error.replacements[:3]  # Max 3 suggerimenti
        
        # Aggiungi logica personalizzata per casi specifici
        if error.rule_id in self.custom_rules:
            custom_suggestions = self._apply_custom_rule(text, error)
            suggestions.extend(custom_suggestions)
        
        return list(set(suggestions))  # Rimuovi duplicati
    
    def apply_correction(self, text: str, error: LanguageToolError, replacement: str) -> str:
        """
        Applica una correzione al testo.
        
        Args:
            text: Testo originale
            error: Errore da correggere
            replacement: Testo sostitutivo
            
        Returns:
            str: Testo corretto
        """
        if error.offset + error.length > len(text):
            logger.warning("⚠️  Error offset exceeds text length")
            return text
        
        corrected = (
            text[:error.offset] + 
            replacement + 
            text[error.offset + error.length:]
        )
        
        return corrected
    
    def get_error_categories(self, errors: List[LanguageToolError]) -> Dict[str, int]:
        """
        Raggruppa errori per categoria.
        
        Args:
            errors: Lista di errori
            
        Returns:
            Dict[str, int]: Conteggio errori per categoria
        """
        categories = {}
        for error in errors:
            category = error.category
            categories[category] = categories.get(category, 0) + 1
        
        return categories
    
    def is_rule_whitelisted(self, rule_id: str) -> bool:
        """Controlla se una regola è nella whitelist"""
        return rule_id in self.whitelisted_rules
    
    def add_to_whitelist(self, rule_id: str, reason: str = ""):
        """Aggiunge una regola alla whitelist"""
        self.whitelisted_rules.add(rule_id)
        
        # Salva la whitelist aggiornata
        self._save_whitelisted_rules(reason)
        
        logger.info(f"➕ Added rule to whitelist: {rule_id} ({reason})")
    
    def remove_from_whitelist(self, rule_id: str):
        """Rimuove una regola dalla whitelist"""
        if rule_id in self.whitelisted_rules:
            self.whitelisted_rules.remove(rule_id)
            self._save_whitelisted_rules()
            logger.info(f"➖ Removed rule from whitelist: {rule_id}")
        else:
            logger.warning(f"⚠️  Rule not in whitelist: {rule_id}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Ritorna statistiche del servizio"""
        return {
            'whitelisted_rules_count': len(self.whitelisted_rules),
            'custom_rules_count': len(self.custom_rules),
            'languagetool_available': self._check_languagetool_available(),
            'cache_stats': {
                'hits': getattr(self.cache_service, '_hits', 0),
                'misses': getattr(self.cache_service, '_misses', 0),
                'lookups': getattr(self.cache_service, '_lookups', 0)
            }
        }
    
    # Metodi privati
    
    def _run_languagetool_check(self, text: str) -> LanguageToolResult:
        """Esegue il controllo LanguageTool tramite subprocess"""
        import time
        start_time = time.time()
        
        try:
            # Crea file temporaneo
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as temp_file:
                temp_file.write(text)
                temp_file_path = temp_file.name
            
            # Comando LanguageTool
            cmd = [
                'java', '-jar', str(self.config.jar_path),
                '--language', self.config.language,
                '--json',
                '--disable', ','.join(self.whitelisted_rules) if self.whitelisted_rules else 'DUMMY',
                temp_file_path
            ]
            
            # Esegui comando
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                encoding='utf-8'
            )
            
            # Cleanup
            Path(temp_file_path).unlink(missing_ok=True)
            
            processing_time = time.time() - start_time
            
            if result.returncode == 0:
                # Parsing risultato JSON
                try:
                    json_result = json.loads(result.stdout)
                    errors = self._parse_languagetool_errors(json_result, text)
                    
                    return LanguageToolResult(
                        text=text,
                        errors=errors,
                        processing_time=processing_time,
                        success=True
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse LanguageTool JSON: {e}")
                    return LanguageToolResult(
                        text=text,
                        errors=[],
                        processing_time=processing_time,
                        success=False,
                        error_message=f"JSON parsing error: {e}"
                    )
            else:
                error_msg = result.stderr or "Unknown LanguageTool error"
                logger.error(f"❌ LanguageTool command failed: {error_msg}")
                return LanguageToolResult(
                    text=text,
                    errors=[],
                    processing_time=processing_time,
                    success=False,
                    error_message=error_msg
                )
                
        except subprocess.TimeoutExpired:
            logger.error("❌ LanguageTool timeout")
            return LanguageToolResult(
                text=text,
                errors=[],
                processing_time=time.time() - start_time,
                success=False,
                error_message="LanguageTool timeout"
            )
        except Exception as e:
            logger.error(f"❌ LanguageTool execution error: {e}")
            return LanguageToolResult(
                text=text,
                errors=[],
                processing_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    def _parse_languagetool_errors(self, json_result: Dict, full_text: str) -> List[LanguageToolError]:
        """
        Parsing degli errori dal JSON di LanguageTool.
        Corregge automaticamente offset/length per catturare parole complete.
        
        Args:
            json_result: Risultato JSON da LanguageTool
            full_text: Testo completo analizzato (necessario per fixare i confini)
        
        Returns:
            Lista di LanguageToolError con offset/length corretti
        """
        errors = []
        
        for match in json_result.get('matches', []):
            offset = match.get('offset', 0)
            length = match.get('length', 0)
            context_text = match.get('context', {}).get('text', '')
            context_offset = match.get('context', {}).get('offset', 0)
            
            # Log di debug per vedere cosa riporta LanguageTool PRIMA della correzione
            logger.debug(
                f"🔍 LT Match BEFORE fix: offset={offset}, length={length}, "
                f"text='{full_text[offset:offset+length] if offset < len(full_text) else 'OUT OF BOUNDS'}'"
            )
            
            # CORREGGI offset/length per catturare la parola completa
            if offset < len(full_text):
                fixed_offset, fixed_length = self._fix_word_boundaries(full_text, offset, length)
                
                # Log se abbiamo corretto
                if fixed_offset != offset or fixed_length != length:
                    logger.debug(
                        f"🔧 Fixed boundaries: offset {offset}→{fixed_offset}, "
                        f"length {length}→{fixed_length}, "
                        f"text '{full_text[offset:offset+length]}'→'{full_text[fixed_offset:fixed_offset+fixed_length]}'"
                    )
                
                offset = fixed_offset
                length = fixed_length
            
            error = LanguageToolError(
                message=match.get('message', ''),
                short_message=match.get('shortMessage', ''),
                offset=offset,
                length=length,
                rule_id=match.get('rule', {}).get('id', ''),
                category=match.get('rule', {}).get('category', {}).get('name', 'Unknown'),
                replacements=[r.get('value', '') for r in match.get('replacements', [])],
                context=context_text,
                severity=match.get('rule', {}).get('category', {}).get('id', 'info')
            )
            errors.append(error)
        
        return errors
    
    def _fix_word_boundaries(self, text: str, offset: int, length: int) -> tuple[int, int]:
        """
        Corregge offset e length per catturare SOLO UNA parola, escludendo punteggiatura e spazi.
        
        LanguageTool a volte riporta offset/length che:
        1. Non catturano l'intera parola (es: "ignifie" invece di "signifie")
        2. Catturano troppo (es: "interoperabili e" invece di "interoperabili")
        
        Questa funzione estrae SOLO la prima parola completa nell'intervallo.
        
        Args:
            text: Testo completo
            offset: Offset iniziale dell'errore
            length: Lunghezza dell'errore
            
        Returns:
            tuple[int, int]: (nuovo_offset, nuova_length) che cattura SOLO la prima parola
        """
        
        def is_word_char(c: str) -> bool:
            """Carattere che fa parte di una parola (lettere e numeri)"""
            return c.isalnum()
        
        def is_internal_apostrophe(pos: int) -> bool:
            """Check se apostrofo è interno alla parola (es: l'acqua, d'accordo)"""
            if pos <= 0 or pos >= len(text) - 1:
                return False
            c = text[pos]
            if c not in ("'", "'"):
                return False
            # È interno se ha lettere sia prima che dopo
            return text[pos - 1].isalnum() and text[pos + 1].isalnum()
        
        # STRATEGIA: Trova l'inizio e la fine della PRIMA parola completa
        
        # PASSO 1: Se offset punta a spazio/punteggiatura, avanza fino alla prima lettera
        start = offset
        while start < len(text) and not is_word_char(text[start]):
            start += 1
        
        if start >= len(text):
            # Nessuna parola trovata, ritorna originale
            return offset, length
        
        # PASSO 2: Ora start punta all'inizio di una parola. Espandi a SINISTRA
        while start > 0:
            prev_char = text[start - 1]
            if is_word_char(prev_char):
                start -= 1
            elif is_internal_apostrophe(start - 1):
                start -= 1
            else:
                break
        
        # PASSO 3: Trova la FINE della parola (espandi a destra da start)
        end = start
        while end < len(text):
            curr_char = text[end]
            if is_word_char(curr_char):
                end += 1
            elif is_internal_apostrophe(end):
                end += 1
            else:
                break
        
        new_length = end - start
        
        # Log se abbiamo fatto correzioni
        if start != offset or new_length != length:
            logger.debug(
                f"🔧 Fixed word boundary: '{text[offset:offset+length]}' → '{text[start:end]}' "
                f"(offset {offset}→{start}, length {length}→{new_length})"
            )
        
        return start, new_length
    
    def _filter_whitelisted_errors(self, errors: List[LanguageToolError]) -> List[LanguageToolError]:
        """Filtra errori basandosi sulla whitelist, vocabolario personalizzato e logica intelligente"""
        filtered = []
        
        # Carica vocabolario personalizzato
        custom_vocab = self._load_custom_vocabulary()
        
        for error in errors:
            # 1. Filtra regole whitelistate
            if self.is_rule_whitelisted(error.rule_id):
                logger.debug(f"🔇 Filtered whitelisted error: {error.rule_id}")
                continue
            
            # 2. NUOVO: Filtra errori ortografici se la parola è nel vocabolario personalizzato
            if error.rule_id in {"MORFOLOGIK_RULE_IT_IT", "ITALIAN_SPELLCHECK", "HUNSPELL_RULE_IT_IT",
                                 "MORFOLOGIK_SPELLER_RULE", "SPELL_RULE", "IT_SPELLING_RULE"}:
                # Estrai la parola dall'errore
                error_word = error.context[error.offset:error.offset + error.length].lower().strip()
                
                # Se la parola è nel vocabolario personalizzato, ignora l'errore
                if error_word in custom_vocab:
                    logger.debug(f"✓ Parola '{error_word}' nel vocabolario personalizzato - errore ignorato")
                    continue
            
            # 3. Filtro intelligente per GR_10_003: costruzioni participiali valide
            if error.rule_id == 'GR_10_003':
                if self._is_valid_participial_construction(error):
                    logger.debug(f"🔇 Filtered GR_10_003: valid participial construction")
                    continue
            
            filtered.append(error)
        
        return filtered
    
    def _load_custom_vocabulary(self) -> set:
        """Carica il vocabolario personalizzato dal file nvdb_parole.json"""
        if hasattr(self, '_custom_vocab_cache'):
            return self._custom_vocab_cache
        
        try:
            from pathlib import Path
            import json
            
            # Percorso al vocabolario - parte dalla directory src/correttore/services
            # quindi dobbiamo salire 3 livelli per arrivare alla root del progetto
            current_file = Path(__file__)  # .../src/correttore/services/languagetool_service.py
            project_root = current_file.parent.parent.parent.parent  # Saliamo a .../Correttore
            vocab_path = project_root / "data" / "vocabolario" / "nvdb_parole.json"
            
            if vocab_path.exists():
                with open(vocab_path, 'r', encoding='utf-8') as f:
                    parole = json.load(f)
                    self._custom_vocab_cache = set(p.lower() for p in parole)
                logger.info(f"✓ Vocabolario personalizzato caricato nel servizio: {len(self._custom_vocab_cache)} parole")
            else:
                logger.warning(f"⚠️ Vocabolario non trovato: {vocab_path}")
                self._custom_vocab_cache = set()
        except Exception as e:
            logger.error(f"❌ Errore nel caricamento vocabolario: {e}")
            self._custom_vocab_cache = set()
        
        return self._custom_vocab_cache
    
    def _is_valid_participial_construction(self, error: LanguageToolError) -> bool:
        """
        Verifica se l'errore GR_10_003 è un falso positivo per costruzione participiale.
        
        Es: "Sebbene inizialmente circoscritta" è valido (participio passato)
        Ma: "Sebbene lui va" non è valido (verbo indicativo)
        
        Returns:
            True se è una costruzione participiale valida (falso positivo)
        """
        import re
        
        # Estrai il testo segnalato dall'errore
        context = error.context.lower()
        
        # Pattern per identificare costruzioni participiali dopo congiunzioni
        # Cerca: congiunzione + (avverbi opzionali) + participio passato
        participial_pattern = re.compile(
            r'\b(sebbene|benché|nonostante|quantunque|malgrado|ancorché)\s+'  # congiunzione
            r'(?:inizialmente|originariamente|generalmente|principalmente|sostanzialmente|essenzialmente|'
            r'già|ancora|sempre|mai|spesso|raramente|talvolta|comunque|tuttavia)?\s*'  # avverbi opzionali
            r'([\w]+[ao])\b',  # parola che termina in -o/-a (probabile participio)
            re.I
        )
        
        match = participial_pattern.search(context)
        if match:
            potential_participle = match.group(2)
            
            # Lista di participi passati comuni che terminano in -a/-o/-i/-e
            # Questi sono segnali forti di costruzione participiale
            participial_endings = [
                'circoscritta', 'circoscritto', 'limitata', 'limitato',
                'considerata', 'considerato', 'ritenuta', 'ritenuto',
                'vista', 'visto', 'concepita', 'concepito',
                'pensata', 'pensato', 'ideata', 'ideato',
                'organizzata', 'organizzato', 'strutturata', 'strutturato',
                'definita', 'definito', 'delineata', 'delineato',
                'caratterizzata', 'caratterizzato', 'qualificata', 'qualificato'
            ]
            
            # Verifica se la parola segnalata è un participio passato
            if any(potential_participle.endswith(ending) for ending in participial_endings):
                return True
            
            # Pattern più generico: parole che terminano in -ato/-ata/-ito/-ita
            if re.match(r'.*[ait][ao]$', potential_participle):
                # Ulteriore verifica: NON deve contenere pronomi soggetto prima
                # "Sebbene lui va" → NON participiale
                # "Sebbene circoscritta" → participiale
                subject_pronouns = r'\b(io|tu|lui|lei|noi|voi|loro|egli|ella|essi|esse)\b'
                if not re.search(subject_pronouns, context[:50], re.I):
                    return True
        
        return False
    
    def _load_whitelisted_rules(self) -> Set[str]:
        """Carica regole whitelistate da file"""
        whitelist_file = Path(self.config.whitelist_file)
        
        if not whitelist_file.exists():
            logger.info("📝 Creating default whitelist file")
            self._create_default_whitelist(whitelist_file)
        
        try:
            rules = set()
            with open(whitelist_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        rules.add(line)
            
            logger.info(f"📝 Loaded {len(rules)} whitelisted rules")
            return rules
            
        except Exception as e:
            logger.error(f"❌ Failed to load whitelist: {e}")
            return set()
    
    def _create_default_whitelist(self, whitelist_file: Path):
        """Crea file whitelist di default"""
        default_rules = [
            "# LanguageTool Rules Whitelist",
            "# Aggiungi ID delle regole da disabilitare, una per riga",
            "# Linee che iniziano con # sono commenti",
            "",
            "# Regole comuni da disabilitare per testi italiani:",
            "UPPERCASE_SENTENCE_START",  # Maiuscole all'inizio frase
            "UNPAIRED_BRACKETS",         # Parentesi non accoppiate
            "WHITESPACE_RULE",           # Spazi multipli (gestito altrove)
            "MORFOLOGIK_RULE_IT_IT",     # Controllo ortografico base
        ]
        
        whitelist_file.parent.mkdir(parents=True, exist_ok=True)
        whitelist_file.write_text('\n'.join(default_rules), encoding='utf-8')
    
    def _save_whitelisted_rules(self, reason: str = ""):
        """Salva la whitelist corrente su file"""
        whitelist_file = Path(self.config.whitelist_file)
        
        try:
            lines = [
                "# LanguageTool Rules Whitelist",
                "# Auto-updated by LanguageToolService",
                f"# Last update reason: {reason}" if reason else "",
                ""
            ]
            
            lines.extend(sorted(self.whitelisted_rules))
            
            whitelist_file.write_text('\n'.join(lines), encoding='utf-8')
            logger.debug(f"💾 Whitelist saved with {len(self.whitelisted_rules)} rules")
            
        except Exception as e:
            logger.error(f"❌ Failed to save whitelist: {e}")
    
    def _load_custom_rules(self) -> Dict[str, Any]:
        """Carica regole personalizzate"""
        custom_rules_file = Path(self.config.custom_rules_file)
        
        if not custom_rules_file.exists():
            return {}
        
        try:
            import yaml
            with open(custom_rules_file, 'r', encoding='utf-8') as f:
                rules = yaml.safe_load(f) or {}
            
            logger.info(f"📝 Loaded {len(rules)} custom rules")
            return rules  # type: ignore
            
        except Exception as e:
            logger.error(f"❌ Failed to load custom rules: {e}")
            return {}
    
    def _apply_custom_rule(self, text: str, error: LanguageToolError) -> List[str]:
        """Applica regola personalizzata per suggerimenti aggiuntivi"""
        rule_id = error.rule_id
        
        if rule_id not in self.custom_rules:
            return []
        
        custom_rule = self.custom_rules[rule_id]
        
        # Implementazione semplificata di regole personalizzate
        if 'replacements' in custom_rule:
            return custom_rule['replacements']
        
        return []
    
    def _verify_languagetool_installation(self):
        """Verifica che LanguageTool sia disponibile"""
        if not self._check_languagetool_available():
            logger.warning(f"⚠️  LanguageTool not found at {self.config.jar_path}")
            logger.warning("   Grammar checking will be limited")
    
    def _check_languagetool_available(self) -> bool:
        """Controlla se LanguageTool è disponibile"""
        jar_path = Path(self.config.jar_path)
        return jar_path.exists() and jar_path.is_file()
    
    def _generate_cache_key(self, text: str) -> str:
        """Genera chiave cache per il testo"""
        import hashlib
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def convert_to_correction_records(
        self, 
        errors: List[LanguageToolError], 
        full_text: str
    ) -> List[CorrectionRecord]:
        """
        Converte gli errori LanguageTool in CorrectionRecord per il tracking.
        
        Args:
            errors: Lista di errori LanguageTool
            full_text: Testo completo analizzato
            
        Returns:
            Lista di CorrectionRecord
        """
        records = []
        
        for error in errors:
            # Determina la categoria basandosi sul tipo di errore
            category = self._map_error_to_category(error)
            
            # Estrai il testo originale dalla posizione (ora già corretta in _parse_languagetool_errors)
            original_text = full_text[error.offset:error.offset + error.length]
            
            # Determina il testo corretto (primo suggerimento se disponibile)
            corrected_text = error.replacements[0] if error.replacements else None
            
            # Estrai contesto esteso (60 caratteri prima e dopo)
            context_start = max(0, error.offset - 60)
            context_end = min(len(full_text), error.offset + error.length + 60)
            context = full_text[context_start:context_end]
            
            # Calcola indici paragrafo e frase (approssimativo)
            paragraph_index = full_text[:error.offset].count('\n\n')
            sentence_index = full_text[:error.offset].count('. ')
            
            # Mappa severità
            severity_map = {
                'error': 'critical',
                'warning': 'warning',
                'info': 'info',
            }
            severity = severity_map.get(error.severity.lower(), 'info')
            
            # Crea il record
            record = CorrectionRecord(
                category=category,
                source=CorrectionSource.LANGUAGETOOL,
                original_text=original_text,
                corrected_text=corrected_text,
                context=context,
                position=error.offset,  # Già corretto in _parse_languagetool_errors
                length=error.length,    # Già corretto in _parse_languagetool_errors
                paragraph_index=paragraph_index,
                sentence_index=sentence_index,
                rule_id=error.rule_id,
                rule_description=error.category,
                message=error.message,
                suggestions=error.replacements[:5],  # Max 5 suggerimenti
                confidence_score=self._calculate_confidence(error),
                severity=severity,
                additional_info={
                    'short_message': error.short_message,
                    'lt_category': error.category,
                }
            )
            
            records.append(record)
        
        return records
    
    def _map_error_to_category(self, error: LanguageToolError) -> CorrectionCategory:
        """
        Mappa un errore LanguageTool a una categoria di correzione.
        
        Args:
            error: Errore LanguageTool
            
        Returns:
            Categoria appropriata
        """
        rule_id = error.rule_id.upper()
        category_name = error.category.upper()
        
        # Regole per categorie specifiche
        
        # Punteggiatura e Tipografia (spazi, virgole, punti, ecc.)
        if any(keyword in category_name for keyword in ['PUNCTUATION', 'TYPOGRAPHY', 'TIPOGRAFIA', 'COMMA', 'WHITESPACE']):
            return CorrectionCategory.PUNTEGGIATURA
        
        if any(keyword in rule_id for keyword in ['COMMA', 'PUNCT', 'DASH', 'QUOTE', 'WHITESPACE', 'SPACE', 'PERIOD', 'COLON', 'SEMICOLON']):
            return CorrectionCategory.PUNTEGGIATURA
        
        # Parole sconosciute (errori ortografici)
        if 'MORFOLOGIK' in rule_id or 'HUNSPELL' in rule_id or 'SPELLING' in category_name:
            return CorrectionCategory.SCONOSCIUTE
        
        # Stile e miglioramenti
        if any(keyword in category_name for keyword in ['STYLE', 'REDUNDANCY', 'COLLOQUIALISM']):
            return CorrectionCategory.MIGLIORABILI
        
        if 'STYLE' in rule_id or 'REDUNDAN' in rule_id:
            return CorrectionCategory.MIGLIORABILI
        
        # Parole sospette (errori contestuali)
        if 'CONFUSION' in category_name or 'CONFUSABLE' in rule_id:
            return CorrectionCategory.SOSPETTE
        
        # Default: errori riconosciuti (grammatica, concordanze, ecc.)
        return CorrectionCategory.ERRORI_RICONOSCIUTI
    
    def _calculate_confidence(self, error: LanguageToolError) -> float:
        """
        Calcola un punteggio di confidenza per l'errore.
        
        Args:
            error: Errore LanguageTool
            
        Returns:
            Punteggio di confidenza (0.0-1.0)
        """
        # Inizia con confidenza alta per LanguageTool
        confidence = 0.85
        
        # Aumenta se ha suggerimenti
        if error.replacements:
            confidence += 0.05
            
        # Aumenta per errori ortografici chiari
        if 'MORFOLOGIK' in error.rule_id or 'SPELLING' in error.category.upper():
            confidence += 0.05
            
        # Diminuisci per errori di stile
        if 'STYLE' in error.category.upper():
            confidence -= 0.15
            
        # Limita a [0.5, 1.0]
        return max(0.5, min(1.0, confidence))


# Factory function per uso diretto
def create_languagetool_service() -> LanguageToolService:
    """Crea un'istanza del servizio LanguageTool con configurazione predefinita"""
    return LanguageToolService()
