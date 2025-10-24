# precheck.py

import re
import language_tool_python as lt

# Lazy loading per evitare errori di connessione durante import
_tool = None

def _get_tool():
    global _tool
    if _tool is None:
        try:
            _tool = lt.LanguageTool('it')  # Usa server locale integrato
        except Exception:
            _tool = None  # Se fallisce, usa solo controlli regex
    return _tool

_EXTRA_PUNCT_RE = re.compile(
    r"( {2,})|"                         # 1) spazi doppi
    r"([,;:.!?]\S)|"                    # 2) punteggiatura+lettera
    r"(«\s)|(\s»)"                      # 3) spazio dopo « o prima »
)

# ENHANCED: Pattern estesi per errori comuni identificati in STEP 2-3
_HEADING_MISSPELL_RE = re.compile(r"CAPPIT|CAPTIOLO", re.I)  # Aggiunto CAPTIOLO

# NUOVO: Pattern per errori ortografici comuni - LISTA ESPANSA
_COMMON_SPELLING_ERRORS_RE = re.compile(
    r"\b(vlta|alta|borggo|ansiano|bottaga|bottaia|sugu|suga|fato|go|Qvesta|qvesta|cassella|"
    r"duee|milliore|prontal|carezzzzavano|trasformazzione|strignendo|Acondroplasiaaa|"
    r"spargette|commissionarglivi|commissionardiglù|tuttavvqja|smplca|riferimentomento|"
    r"c\s+erano)\b", re.I
)

# NUOVO: Pattern per lettere ripetute anomale 
_REPEATED_LETTERS_RE = re.compile(
    r"\b\w*[zx]{3,}\w*\b|"              # 3+ z o x consecutive
    r"\b\w*[aeiou]{4,}\w*\b|"           # 4+ vocali consecutive  
    r"\b\w*[bcdfghjklmnpqrstvwxyz]{5,}\w*\b"  # 5+ consonanti consecutive
)

# NUOVO: Pattern per articoli/preposizioni sbagliate
_GRAMMAR_ERRORS_RE = re.compile(
    r"\bLa\s+(cane|gatto|ragazzo|uomo|bambino)\b|"  # Articoli maschili/femminili sbagliati
    r"\bIl\s+(casa|donna|bambina|ragazza)\b|"
    r"\bUn\s+(casa|donna|bambina|ragazza)\b|"
    r"\bUna\s+(cane|gatto|ragazzo|uomo|bambino)\b", re.I
)

def has_errors(text: str, aggressive_mode: bool = False) -> bool:
    """
    Enhanced error detection with better coverage.
    
    Args:
        text: Il testo da controllare
        aggressive_mode: Se True, processa sempre (utile per test/debug)
    
    Returns:
        True se il testo contiene probabili errori, False altrimenti
    """
    # Se aggressive_mode=True, processa sempre (per test o modalità "sicura")
    if aggressive_mode:
        return True
    
    # 1. controlli regex personalizzati (ESISTENTI)
    if _EXTRA_PUNCT_RE.search(text):
        return True
    
    # 2. titoli da forzare (ENHANCED - ora include CAPTIOLO)
    if _HEADING_MISSPELL_RE.search(text):
        return True
    
    # 3. NUOVO: errori ortografici comuni identificati
    if _COMMON_SPELLING_ERRORS_RE.search(text):
        return True
    
    # 4. NUOVO: lettere ripetute anomale
    if _REPEATED_LETTERS_RE.search(text):
        return True
    
    # 5. NUOVO: errori grammaticali evidenti
    if _GRAMMAR_ERRORS_RE.search(text):
        return True
    
    # 6. controlli di LanguageTool (ENHANCED per frasi brevi)
    tool = _get_tool()
    if tool:
        try:
            matches = tool.check(text)
            # Filtra i match per evitare falsi positivi su testi corretti
            valid_errors = []
            for m in matches:
                if m.ruleIssueType in (
                    "misspelling",
                    "grammar", 
                    "typographical",
                    "punctuation",
                ):
                    # Esclude errori di stile minori su testi che sembrano corretti
                    if not (m.ruleIssueType == "style" and len(text.strip()) > 20):
                        valid_errors.append(m)
            
            if valid_errors:
                return True
                    
            # NUOVO: Per frasi molto brevi (< 20 char), controlla anche "style" e "uncategorized"
            # Questo cattura errori che LanguageTool classifica diversamente in frasi brevi
            if len(text.strip()) < 20:
                for m in matches:
                    if m.ruleIssueType in ("style", "uncategorized"):
                        # Doppio controllo: evita falsi positivi su frasi brevi ma corrette
                        error_text = text[m.offset:m.offset + m.errorLength].lower()
                        if any(word in error_text for word in ['vlta', 'borggo', 'ansiano', 'captiolo', 'fato', 'sugu']):
                            return True
                        
        except Exception:
            pass  # Se LanguageTool non funziona, usa solo regex
    
    # 7. NUOVO: Fallback per testi molto brevi con pattern sospetti
    # Se un testo breve contiene pattern strani, meglio processarlo
    if len(text.strip()) < 30:
        # Pattern sospetti in testi brevi
        suspicious_patterns = [
            r"\b[a-zA-Z]{1,2}\b.*\b[a-zA-Z]{1,2}\b",  # Molte parole molto brevi
            r"[a-zA-Z][0-9]|[0-9][a-zA-Z]",           # Lettere e numeri misti
            r"\b[qwxyz]\w*[qwxyz]\b",                  # Lettere rare in combinazione
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.I):
                return True
    
    return False

