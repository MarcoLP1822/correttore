# precheck.py
import language_tool_python as lt

_tool = lt.LanguageTool('it')        # una sola istanza ri-usabile

def has_errors(text: str) -> bool:
    """True se LanguageTool trova errori da correggere."""
    matches = _tool.check(text)
    for m in matches:
        # Filtra i tipi che interessano davvero
        if m.ruleIssueType in ("misspelling", "grammar", "typographical",
                               "punctuation"):
            return True
    return False
