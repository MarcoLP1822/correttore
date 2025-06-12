# precheck.py

import re
import language_tool_python as lt

_tool = lt.LanguageTool('it')        # una sola istanza ri-usabile

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
    # 2) titoli da forzare (Capitolo sbagliato, ecc.)
    if _HEADING_MISSPELL_RE.search(text):
        return True
    # 3. controlli di LanguageTool
    matches = _tool.check(text)
    for m in matches:
        if m.ruleIssueType in (
            "misspelling",
            "grammar",
            "typographical",
            "punctuation",
        ):
            return True
    return False

