# ── grammarcheck.py (corretto) ───────────────────────────────────────────────
import re
import threading
import logging
import language_tool_python as lt

###############################################################################
# 1) Istanza di LanguageTool dedicata a ogni thread
###############################################################################
_THREAD_LOCAL = threading.local()

# Regole che vogliamo SEMPRE far girare
_SAFE_RULES = {
    "IT_ACCENTI",              # ò/ó, po’/pò, ecc.
    "E_APOSTROPHE", "WRONG_APOSTROPHE",
    "UPPERCASE_SENTENCE_START",
    "PRON_GLI_E_L",            # gli/l’
    "MULTIPLE_EXCLAMATION_MARK", "MULTIPLE_QUESTION_MARK", "MORFOLOGIK_RULE_IT_IT"
}

def _get_tool() -> lt.LanguageTool:
    tool = getattr(_THREAD_LOCAL, "tool", None)
    if tool is None:
        tool = lt.LanguageTool(
            "it",
            remote_server="http://localhost:8081"   # ✓ usa il server
        )
        tool.enabled_rules = _SAFE_RULES            # ← resta valido
        _THREAD_LOCAL.tool = tool
    return tool

###############################################################################
# 2) Correzione prudente
###############################################################################
_WORD_RE = re.compile(r"[\w’]+")

def _single_words(lst: list[str]) -> bool:
    return all(re.fullmatch(r"[\w’]+", w)        # include U+2019
               for w in lst)

def grammarcheck(text: str) -> str:
    """
    Fa girare LanguageTool sul testo e applica soltanto correzioni
    provenienti da regole presenti in _SAFE_RULES **e** con suggerimenti
    davvero univoci/semplici.

    Criteri di applicazione:
    • la regola deve essere whitelisted (_SAFE_RULES)
    • deve esserci UN solo suggerimento   ──oppure──
      max 3 suggerimenti composti ognuno da UNA sola parola.
    Tutto il resto viene ignorato.
    """
    original = text

    # ── 1. Otteniamo i match di LT ──────────────────────────────────
    try:
        matches = _get_tool().check(original)
    except Exception as exc:
        logging.getLogger("LanguageTool").warning(
            "LanguageTool error: %s – testo lasciato invariato", exc
        )
        return original.replace("'", "’")          # fallback: solo apostrofi tipografici

    # ── 2. Applichiamo le correzioni partendo dalla fine ────────────
    corrected = original
    for m in reversed(matches):

        # 2a. Scarta se la regola NON è nella whitelist
        if m.ruleId not in _SAFE_RULES:
            continue                    # ← nuovo filtro di sicurezza

        # 2b. Se non ci sono suggerimenti, non possiamo correggere
        if not m.replacements:
            continue

        # 2c. Decidiamo se accettare il suggerimento
        apply = False
        if len(m.replacements) == 1:
            apply = True                               # un solo suggerimento → ok
            repl = m.replacements[0]
        elif len(m.replacements) <= 3 and _single_words(m.replacements):
            apply = True
            repl  = m.replacements[0]
        else:
            apply = False                              # troppi / complessi → lascio stare

        if apply:
            corrected = (
                corrected[:m.offset] + repl +
                corrected[m.offset + m.errorLength:]
            )

    # ── 3. Normalizziamo l’apostrofo tipografico ────────────────────
    if "'" in corrected:
        corrected = corrected.replace("'", "’")
    return corrected
# ───────────────────────────────────────────────────────────────────────────────