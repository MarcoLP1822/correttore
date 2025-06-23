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
_SAFE_RULES: set[str] = {
    # Apostrofi / accenti
    "IT_ACCENTI", "E_APOSTROPHE", "UN_ALTRO", "CHE_E", "E_ACUTE_APOSTROPHE",
    # Maiuscola a inizio frase
    "UPPERCASE_SENTENCE_START",
    # Battitura articoli (gli / l…)
    "GLI_E_L", "GLI_E_LA", "GLI_E_LI", "GLI_E_LE", "GLI_E_APOSTROPHE"
    # D-eufonica, puntini, doppia ! / ?
    "APOCOPI_VOCALICHE", "DEUFONICA_RIMUOVI_ED",
    "MULTIPLE_EXCLAMATION_MARK", "MULTIPLE_QUESTION_MARK",
    "FOUR_POINTS", "ELLIPSIS_SPACE",
    # Sigle societarie
    "ITALIAN_SPA", "ITALIAN_SRL", "ITALIAN_SAS",
    # a / ha – da / dà – ai / hai
    "ER_01_001", "ER_01_002", "ER_01_003", "ER_02_005",
    # Date e numeri impossibili
    "ANNO20011_2011", "NUMBER_DAYS_MONTH",
    # Doppia parola (stile)
    "ST_03_002_DUPLICATE_WORD",
    # Controllo ortografico (spell-check)
    "HUNSPELL_RULE", "MORFOLOGIA_IT", "MORFOLOGIK_RULE_IT_IT",
    "GR_02_001",      # Articoli corretti (sing/plur, m/f)
    "GR_04_002",      # Elisioni (un’/un, di → d’, ecc.)
    "GR_10_001",      # Concordanza tempi coordinate
}

def _get_tool() -> lt.LanguageTool:
    """Istanza LT per il thread + attivazione regole whitelist."""
    tool = getattr(_THREAD_LOCAL, "tool", None)
    if tool is None:
        tool = lt.LanguageTool(
            "it",
            remote_server=None,
            config={"cacheSize": 200_000_000},
        )
        # CORREZIONE: Assegniamo il nostro set di regole come l'UNICO set attivo.
        # Questo garantisce che vengano eseguite solo le regole della nostra whitelist.
        tool.enabled_rules = _SAFE_RULES
        _THREAD_LOCAL.tool = tool
    return tool

###############################################################################
# 2) Correzione prudente
###############################################################################
_WORD_RE = re.compile(r"[\w’]+")

def _single_words(lst: list[str]) -> bool:
    """True se tutti gli elementi sono singole parole."""
    return all(_WORD_RE.fullmatch(w) for w in lst)

def grammarcheck(text: str) -> str:
    """
    • Gira LT sul testo originale (senza cambiare gli apostrofi).
    • Applica solo sostituzioni «sicure» (whitelist, 1 suggerimento o
      spell-check con soli suggerimenti parola-singola).
    • Poi converte gli apostrofi dritti in tipografici.
    """
    original = text

    try:
        matches = _get_tool().check(original)
    except Exception as exc:
        logging.getLogger("LanguageTool").warning(
            "LanguageTool error: %s – testo lasciato invariato", exc
        )
        return original.replace("'", "’")

    # Applichiamo le correzioni partendo dalla fine
    corrected = original
    for m in reversed(matches):
        apply = False

        # Logica semplificata:
        # Se la regola è nella nostra whitelist, è sicura per definizione.
        # Questo include lo spell-check.
        if m.ruleId in _SAFE_RULES:
            apply = True
        # Altrimenti, applichiamo solo se c'è un suggerimento unico
        # o un massimo di 3 suggerimenti composti da parole singole.
        elif len(m.replacements) == 1:
            apply = True
        elif (1 < len(m.replacements) <= 3 and _single_words(m.replacements)):
            apply = True

        if apply and m.replacements:
            repl = m.replacements[0]
            corrected = (
                corrected[:m.offset] + repl +
                corrected[m.offset + m.errorLength :]
            )

    # Solo adesso normalizziamo l’apostrofo
    return corrected.replace("'", "’")
# ───────────────────────────────────────────────────────────────────────────────