# grammarcheck.py
import language_tool_python as lt
import re

_TOOL = lt.LanguageTool('it')

# regole che vogliamo forzare anche se LT propone più di un suggerimento
_SAFE_RULES = {
    'GLI_E_L',   # gli e l’ -> gliel’
    'GLI_E_LA',  # gli e la -> gliela
    'GLI_E_LI',
    'GLI_E_LE',
}

def grammarcheck(text: str) -> str:
    """
    Applica automaticamente:
      • tutte le correzioni con UN solo suggerimento
      • le correzioni delle regole in _SAFE_RULES anche se i suggerimenti sono >1
    """
    text = re.sub(r"'", "’", text)
    matches = _TOOL.check(text)

    # scorri da destra → sinistra così gli offset restano validi
    for m in reversed(matches):
        print(m.ruleId, m.replacements[:3])
        apply = False
        if len(m.replacements) == 1:              # correzione “sicura”
            apply = True
        elif m.ruleId in _SAFE_RULES:             # regola whitelistar
            apply = True

        if apply:
            repl = m.replacements[0]              # prende il primo suggerimento
            text = text[:m.offset] + repl + text[m.offset + m.errorLength:]

    return text
