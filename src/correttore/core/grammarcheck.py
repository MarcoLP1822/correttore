# grammarcheck.py - LanguageTool integration with enhanced rules
import re
import threading
import logging
from typing import cast
import language_tool_python as lt

###############################################################################
# 1) Istanza di LanguageTool dedicata a ogni thread
###############################################################################
_THREAD_LOCAL = threading.local()

# Regole che vogliamo SEMPRE far girare - ESPANSE PER CORREZIONE COMPLETA
_SAFE_RULES = {
    # Regole ortografiche fondamentali
    "MORFOLOGIK_RULE_IT_IT",      # Dizionario morfologico italiano (vlta→volta, ansiano→anziano)
    "ITALIAN_SPELLCHECK",          # Controllo ortografico generale
    "HUNSPELL_RULE_IT_IT",        # Hunspell dizionario italiano
    
    # Regole grammaticali essenziali
    "IT_ACCENTI",                 # Accenti corretti (ò/ó, po'/pò, ecc.)
    "E_APOSTROPHE", "WRONG_APOSTROPHE",  # Apostrofi corretti
    "UPPERCASE_SENTENCE_START",    # Maiuscole dopo punto
    "PRON_GLI_E_L",               # Pronomi gli/le corretti
    
    # Punteggiatura e spazi
    "WHITESPACE_RULE",            # Spazi doppi/mancanti (U giorno → Un giorno)
    "COMMA_WHITESPACE",           # Spazi corretti dopo virgole
    "PERIOD_WHITESPACE",          # Spazi corretti dopo punti
    "COLON_WHITESPACE",           # Spazi dopo due punti
    "SEMICOLON_WHITESPACE",       # Spazi dopo punto e virgola
    
    # Errori di duplicazione e punteggiatura
    "MULTIPLE_EXCLAMATION_MARK", "MULTIPLE_QUESTION_MARK",  # !!! → !
    "WORD_REPEAT_RULE",           # Parole duplicate consecutive
    "UNPAIRED_BRACKETS",          # Parentesi non chiuse
    "DOUBLE_PUNCTUATION",         # Punteggiatura doppia
    
    # Concordanze e articoli
    "IT_AGREEMENT",               # Concordanze italiano
    "AGREEMENT_SENT_START",       # Accordi inizio frase
    "ITALIAN_WORD_COHERENCY"      # Coerenza lessicale italiana
}

def _get_tool() -> lt.LanguageTool:
    tool = getattr(_THREAD_LOCAL, "tool", None)
    if tool is None:
        # Prima prova con server locale, poi fallback a installazione locale
        try:
            # Prova server HTTP se disponibile
            import requests
            requests.get("http://localhost:8081/v2/languages", timeout=2)
            tool = lt.LanguageTool(
                "it",
                remote_server="http://localhost:8081"
            )
            logging.info("✓ LanguageTool: usando server HTTP localhost:8081")
        except:
            # Fallback: usa JAR locale se server non disponibile
            jar_path = None
            possible_jars = [
                r"c:\Users\Youcanprint1\Desktop\AI\Correttore\languagetool\LanguageTool-6.3\languagetool.jar",
                r"c:\Users\Youcanprint1\Desktop\AI\Correttore\languagetool\LanguageTool-6.3\languagetool-server.jar"
            ]
            
            for jar in possible_jars:
                import os
                if os.path.exists(jar):
                    jar_path = jar
                    break
            
            if jar_path:
                # Non è possibile specificare JAR locale, usa installazione automatica
                tool = lt.LanguageTool("it")
                logging.info(f"✓ LanguageTool: usando installazione automatica (JAR locale {jar_path} disponibile ma non utilizzabile)")
            else:
                # Ultimo fallback: lascia che language-tool-python scarichi la sua versione
                tool = lt.LanguageTool("it")
                logging.info("✓ LanguageTool: usando installazione automatica")
        
        # CONFIGURAZIONE ESTESA: Abilita tutte le regole sicure
        tool.enabled_rules = _SAFE_RULES
        
        # FORZARE L'INCLUSIONE DI REGOLE SPECIFICHE
        # Assicuriamoci che le regole di spelling siano sempre attive
        additional_spelling_rules = {
            "SPELL_RULE", "SPELLER_RULE", "MORFOLOGIK_SPELLER_RULE", 
            "ITALIAN_REPLACE_RULE", "IT_SPELLING_RULE"
        }
        
        # Aggiungi regole di spelling se disponibili (try-catch per compatibilità)
        try:
            for rule_id in additional_spelling_rules:
                tool.enabled_rules.add(rule_id)
                logging.debug(f"✓ Tentativo aggiunta regola: {rule_id}")
        except Exception as e:
            logging.debug(f"⚠️ Alcune regole aggiuntive non disponibili: {e}")
        
        logging.info(f"✓ LanguageTool configurato con {len(tool.enabled_rules)} regole abilitate")
        _THREAD_LOCAL.tool = tool
    return tool

###############################################################################
# 2) Correzione prudente
###############################################################################
_WORD_RE = re.compile(r"[\w']+")

def _single_words(lst: list[str]) -> bool:
    return all(re.fullmatch(r"[\w']+", w)        # include U+2019
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
        return original.replace("'", "'")          # fallback: solo apostrofi tipografici

    # ── 2. Applichiamo le correzioni partendo dalla fine ────────────
    corrected = original
    for m in reversed(matches):

        # 2a. Scarta se la regola NON è nella whitelist
        if m.ruleId not in _SAFE_RULES:
            continue                    # ← nuovo filtro di sicurezza

        # 2b. Se non ci sono suggerimenti, non possiamo correggere
        if not m.replacements:
            continue

        # 2c. Decidiamo se accettare il suggerimento - CRITERI MIGLIORATI
        apply = False
        repl = ""  # Initialize to avoid unbound variable
        
        # Criteri di accettazione più permissivi per errori evidenti
        if len(m.replacements) == 1:
            apply = True                               # un solo suggerimento → sempre ok
            repl = m.replacements[0]
        elif len(m.replacements) <= 3 and _single_words(cast(list[str], m.replacements)):
            apply = True                               # max 3 parole singole → ok
            repl = m.replacements[0]
        elif len(m.replacements) <= 5 and m.ruleId in {"MORFOLOGIK_RULE_IT_IT", "ITALIAN_SPELLCHECK", "HUNSPELL_RULE_IT_IT"}:
            # Per regole di spelling, accetta anche fino a 5 suggerimenti se sono parole singole
            if _single_words(cast(list[str], m.replacements)):
                apply = True                           # errori di spelling evidenti → più permissivo
                repl = m.replacements[0]
            else:
                apply = False
        else:
            apply = False                              # troppi / complessi → lascio stare

        if apply:
            corrected = (
                corrected[:m.offset] + repl +
                corrected[m.offset + m.errorLength:]
            )

    # ── 3. Normalizziamo l'apostrofo tipografico ────────────────────
    if "'" in corrected:
        corrected = corrected.replace("'", "'")
    return corrected