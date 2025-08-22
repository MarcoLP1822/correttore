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

_HEADING_MISSPELL_RE = re.compile(r"CAPPIT", re.I)

def has_errors(text: str) -> bool:
    # 1. controlli regex personalizzati
    if _EXTRA_PUNCT_RE.search(text):
        return True
    # 2. titoli da forzare (Capitolo sbagliato, ecc.)
    if _HEADING_MISSPELL_RE.search(text):
        return True
    # 3. controlli di LanguageTool (se disponibile)
    tool = _get_tool()
    if tool:
        try:
            matches = tool.check(text)
            for m in matches:
                if m.ruleIssueType in (
                    "misspelling",
                    "grammar",
                    "typographical",
                    "punctuation",
                ):
                    return True
        except Exception:
            pass  # Se LanguageTool non funziona, usa solo regex
    return False

