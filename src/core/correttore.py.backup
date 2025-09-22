#correttore.py
"""
Corregge grammatica e ortografia in **qualsiasi** parte di un documento word (.docx) e produce un report Markdown con tutte le modifiche.

* testo normale, anche in tabelle nidificate
* header & footer
* testo delle note a piè di pagina (footnotes)
* caselle di testo / forme (<w:txbxContent>)

Mantiene corsivi, grassetti, sottolineature, riferimenti di nota, ecc.
Richiede **python-docx ≥ 0.8.11**.
"""

from __future__ import annotations

# ——— Standard library ————————————————————————————————
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)

import asyncio
import aiofiles
import collections
import json
import os
import re
import shutil
import time
import zipfile
from pathlib import Path
from copy import deepcopy
from datetime import datetime
from src.core.precheck import has_errors
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional, Tuple
from pprint import pprint

# ——— Third-party ————————————————————————————————
import tiktoken
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio
from docx import Document  # type: ignore[import]
from docx.oxml.ns import qn

# ——— Correzione immediata premium ————————————————————————
try:
    from instant_fixer import InstantFixer
    instant_fixer = InstantFixer()
    logger.info("✅ Sistema di correzione immediata caricato")
except ImportError:
    instant_fixer = None
    logger.warning("⚠️  Sistema di correzione immediata non disponibile")

# ——— Monitoring e Qualità - FASE 4 ————————————————————————————————
from tools.monitoring import get_monitor
from src.core.validation import DocumentValidator
from src.core.safe_correction import SafeCorrector
from services.intelligent_cache import get_cache
from services.parallel_processor import get_parallel_corrector, ProcessingTask
from docx.text.paragraph import Paragraph
from lxml import etree  # type: ignore[import]
from lxml.etree import XMLSyntaxError
from openai import AsyncOpenAI, OpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


# Carica le variabili d'ambiente dal file .env.local
load_dotenv('.env.local')

# ——— Local modules ————————————————————————————————
from src.utils.reports import write_glossary_report, write_markdown_report
from src.utils.token_utils import tokenize, token_starts, count_tokens
from config.settings import OPENAI_MODEL, MAX_TOKENS
from src.services.openai_client import get_async_client
from src.utils.utils_openai import get_corrections_async, build_messages
from src.core.spellfix import spellfix_paragraph
from src.core.grammarcheck import grammarcheck
from src.core.llm_correct import llm_correct, llm_correct_batch

# ——— New safety and validation modules ————————————————————
from src.core.validation import DocumentValidator, ValidationResult, create_backup, validate_document, validate_correction
from core.formatting_manager import FormattingManager
from src.core.safe_correction import SafeCorrector, CorrectionResult, QualityScore

LT_POOL = ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 1) - 1))

# ───────────────────────── CONFIGURAZIONE ────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

try:
    ENC = tiktoken.encoding_for_model(OPENAI_MODEL)
except KeyError:
    # fallback universale, compatibile con GPT-4/3.5
    ENC = tiktoken.get_encoding("cl100k_base")
# ─────────────────────────────────────────────────────────────────────

from src.utils.token_utils import NAME_RE, WORD_RE

GLOSSARY_STOP = {
    "CAPITOLO", "CAPITOLI", "PROLOGO", "EPILOGO",
    "INDICE", "RINGRAZIAMENTI", "DEDICA", "DEDICHE", "PREFAZIONE", "PREFAZIONI",
}
# ─────────────────── Pandoc: ODT/DOC → DOCX ──────────────────────────
import win32com.client as win32

def convert_to_docx(src: Path) -> Path:
    if src.suffix.lower() == ".docx":
        return src

    dst = src.with_suffix(".docx")
    word = win32.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(src))
        doc.SaveAs(str(dst), FileFormat=16)   # 16 = wdFormatDocumentDefault
        doc.Close()
    finally:
        word.Quit()
    return dst

# ──────────────────────────────────────────────────────────────────────

# ╭─────────────────────────── Note a piè di pagina ▾──────────────────────────╮
from collections import defaultdict

async def correggi_footnotes_xml_async(docx_path: Path,
                                       async_client: AsyncOpenAI,
                                       glossary: set[str] | None = None) -> None:

    """
    Corregge le note a piè di pagina contenute in word/footnotes.xml
    (refusi, ortografia, punteggiatura) preservando la formattazione
    run-per-run del documento Word.
    """
    glossary = glossary or set()           # se None, usa set vuoto
    tmp_dir = "_tmp_docx_unzipped"

    # 1) Estrai il .docx in una cartella temporanea --------------------
    with zipfile.ZipFile(docx_path, "r") as zf:
        zf.extractall(tmp_dir)

    footnotes_file = os.path.join(tmp_dir, "word", "footnotes.xml")
    if not os.path.exists(footnotes_file):
        shutil.rmtree(tmp_dir)
        return                              # documento senza note
    
    # Se il file esiste ma è vuoto, non ci sono note → esci
    if os.path.getsize(footnotes_file) == 0:
        shutil.rmtree(tmp_dir)
        return

    # Prova a fare il parse; se fallisce, esci comunque in sicurezza
    try:
        ns   = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        tree = etree.parse(footnotes_file)
    except XMLSyntaxError:
        shutil.rmtree(tmp_dir)
        return

    ns   = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    tree = etree.parse(footnotes_file)
    footnotes = tree.xpath(
        "//w:footnote[not(@w:type='separator')]",
        namespaces=ns
    )

# 3) Ciclo con barra di avanzamento ------------------------------------
    for foot in tqdm(
            footnotes,
            desc="Note a piè di pagina",
            total=len(footnotes)
    ):
        txt_nodes = foot.xpath(".//w:t", namespaces=ns)
        full_text = "".join(n.text or "" for n in txt_nodes)

        if not full_text.strip():
            continue                             # nota vuota → salta

    # 3a) Chiamata OpenAI (async) --------------------------------------
        raw = await get_corrections_async(
            payload_json=json.dumps(
                [{"id": 0, "txt": full_text}],
                ensure_ascii=False
            ),
            client=async_client,
            glossary=glossary,
            context="",
        )
        if isinstance(raw, list):
            corr_list = raw 
        elif isinstance(raw, dict) and "corr" in raw:
            corr_list = raw["corr"]
        else:
            raise TypeError(
                f"Formato inatteso da get_corrections_async(): {type(raw)} – {raw!r}"
        )

        corrected = corr_list[0]["txt"]

        if corrected == full_text:
            continue                             # nessuna correzione

    # 3b) Redistribuzione token nei nodi <w:t> ... (resto del tuo codice)
    # ------------------------------------------------------------------


        # 2b) Redistribuisci token corretti nei singoli <w:t> ----------
        orig_tok   = tokenize(full_text)
        corr_tok   = tokenize(corrected)
        mapping    = align_tokens(orig_tok, corr_tok)
        starts_orig = token_starts(orig_tok)

        # mappa carattere→indice nodo
        char2node = []
        for idx, n in enumerate(txt_nodes):
            char2node.extend([idx] * len(n.text or ""))

        tok_per_node = defaultdict(list)
        for ref_idx, tok in mapping:
            if ref_idx is None or ref_idx >= len(starts_orig):
                node_idx = 0
            else:
                char_pos = starts_orig[ref_idx]
                node_idx = char2node[min(char_pos, len(char2node) - 1)]
            tok_per_node[node_idx].append(tok)

        # scrivi il testo nei nodi preservando la partizione originale
        for idx, n in enumerate(txt_nodes):
            n.text = "".join(tok_per_node.get(idx, []))

        # 2c) Se si perde la formattazione del primo run, ristabiliscila
        first_with_txt = next((n for n in txt_nodes if n.text and n.text.strip()), None)
        if first_with_txt is not None:
            run_first       = first_with_txt.getparent()
            has_rPr_first   = run_first.find("./w:rPr", namespaces=ns)
            has_bold_first  = run_first.xpath("./w:rPr/w:b", namespaces=ns)

            if not has_bold_first:
                for n2 in txt_nodes:
                    if n2 is first_with_txt or not (n2.text and n2.text.strip()):
                        continue
                    rPr_other = n2.getparent().find("./w:rPr", namespaces=ns)
                    if rPr_other is not None and list(rPr_other):
                        if has_rPr_first is None:
                            has_rPr_first = etree.SubElement(run_first, qn("w:rPr"))
                        for child in rPr_other:
                            has_rPr_first.append(deepcopy(child))
                        break   # una sola copia è sufficiente

    # 3) Salva il nuovo footnotes.xml e ricompatta il .docx -------------
    async with aiofiles.open(footnotes_file, "wb") as f:
        await f.write(etree.tostring(tree,
                           xml_declaration=True,
                           encoding="utf-8"))

    tmp_docx = docx_path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp_docx, "w") as zf:
        for root, _, files in os.walk(tmp_dir):
            for f in files:
                fullpath = os.path.join(root, f)
                arcname  = os.path.relpath(fullpath, tmp_dir)
                zf.write(fullpath, arcname)

    shutil.move(tmp_docx, docx_path)        # sovrascrive l'originale
    shutil.rmtree(tmp_dir)
    logger.info("✏️  Note a piè di pagina corrette")
# ╭─────────────────────────── Data-model modifiche ▾────────────────────╮
@dataclass
class Modification:
    par_id: int
    original: str
    corrected: str
# ╰──────────────────────────────────────────────────────────────────────╯
# ───────────────────── NEW universal chunker ──────────────────────
def chunk_paragraphs_all(
    paragraphs: List[Paragraph],
    max_tokens: int = 3_000,
    max_pars:   int = 5,
) -> List[List[Paragraph]]:
    """
    Divide *tutti* i paragrafi in blocchi:
      • al massimo `max_pars` paragrafi
      • e al massimo `max_tokens` token complessivi
    Ritorna una lista di chunk (liste di Paragraph).
    """
    chunks: List[List[Paragraph]] = []
    current, current_tok = [], 0
    for p in paragraphs:
        tok = count_tokens(p.text)
        # se il singolo paragrafo supera il limite token, lo isolo
        if tok > max_tokens:
            if current:
                chunks.append(current)
                current, current_tok = [], 0
            chunks.append([p])
            continue
        # se aggiungerlo sfora i limiti → chiudi chunk e apri nuovo
        if (current and
            (current_tok + tok > max_tokens or len(current) >= max_pars)):
            chunks.append(current)
            current, current_tok = [], 0
        current.append(p)
        current_tok += tok
    if current:
        chunks.append(current)
    return chunks
# ───────────────────────────────────────────────────────────────────

# ╭─────────────────────────── Chunking ▾────────────────────────────────╮
#def chunk_paragraph_objects(
#    paragraphs: List[Paragraph],
#    max_tokens: int = MAX_TOKENS,
#) -> List[List[Paragraph]]:
#    """Dividi la lista di oggetti Paragraph in blocchi < max_tokens."""
#    chunks: List[List[Paragraph]] = []
#    current: List[Paragraph] = []
#    current_tokens = 0

#    for p in paragraphs:
#        para_tokens = count_tokens(p.text)

        # 1) se il singolo paragrafo sfora il limite, isolalo
#        if para_tokens > max_tokens:
#            if current:                     # salva il chunk in corso
#                chunks.append(current)
#                current, current_tokens = [], 0
#            chunks.append([p])              # paragrafo “oversize” da solo
#            continue                        # salta al paragrafo successivo

#        # 2) comportamento normale
#        if current and current_tokens + para_tokens > max_tokens:
#            chunks.append(current)
#            current = [p]
#            current_tokens = para
#        else:
#            current.append(p)
#            current_tokens += para_tokens

#    if current:
#        chunks.append(current)
#    return chunks
# ╰──────────────────────────────────────────────────────────────────────╯

# ╭─────────────────────────── Diff token-level ▾────────────────────────╮
def align_tokens(orig: List[str], corr: List[str]) -> List[Tuple[Optional[int], str]]:
    sm = SequenceMatcher(a=orig, b=corr, autojunk=False)
    out: List[Tuple[Optional[int], str]] = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                out.append((i1 + k, corr[j1 + k]))
        elif op == "replace":
            inherit = i1 if i1 < len(orig) else None
            for k in range(j2 - j1):
                out.append((inherit, corr[j1 + k]))
        elif op == "insert":
            inherit = i1 - 1 if i1 > 0 else None
            for k in range(j1, j2):
                out.append((inherit, corr[k]))
    return out
# ╰──────────────────────────────────────────────────────────────────────╯

# ╭─────────────────────────── Helpers copy RUN ▾────────────────────────╮
def copy_rPr(src_rPr, dest_run):
    if src_rPr is None:
        return
    dest = dest_run._r.get_or_add_rPr()
    dest.clear()
    for child in src_rPr:
        dest.append(deepcopy(child))


def clone_run(src_run, paragraph):
    new_run = paragraph.add_run("")
    copy_rPr(src_run._r.rPr, new_run)
    for child in src_run._r:
        if child.tag != qn("w:t"):
            new_run._r.append(deepcopy(child))
    return new_run
# ╰──────────────────────────────────────────────────────────────────────╯

# ───────────────── helper “quanto è diverso?” ────────────────────────
# ─────────────────────────────────────────────────────────────────────
def _too_much_cut(orig: str, corr: str,
                  lost_thresh: float = 0.15) -> bool:
    """
    True **solo** se l’output:
      • perde >10 % dei token **e**
      • ha meno frasi dell’originale
    (Quasi impossibile in una correzione normale)
    """
    tok_orig = tokenize(orig)
    tok_corr = tokenize(corr)
    lost = (len(tok_orig) - len(tok_corr)) / max(1, len(tok_orig))
    if lost <= lost_thresh:
        return False                         # taglio contenuto: ok

    # conteggio frasi
    sent = lambda s: len([t for t in re.split(r"[.!?…]", s) if t.strip()])
    return sent(corr) < sent(orig)

_DUP_PUNCT_RE = re.compile(r'([.!?])\s*\1(?!\1)')
#  • ([.!?])   → cattura il primo . ! o ?
#  • \s*       → permette spazi/tab fra i due segni
#  • \1        → stesso segno ripetuto
#  • (?!\1)    → ma *non* se ce n’è un terzo subito dopo (salva i “…”, “!!!”)

def _remove_duplicate_punct(text: str) -> str:
    """
    Collassa sequenze duplicate di segni di fine frase introdotte dal merge
    dei token (es. '..', '??', '!!').  
    Mantiene i puntini di sospensione '...' e ripetizioni intenzionali ≥3.
    """
    return _DUP_PUNCT_RE.sub(r'\1', text)

# ╭──────────────────────── Nuova versione step-safe ───────────────────╮
def _run_map(paragraph: Paragraph) -> list[int]:
    """Mappa ogni carattere al run di provenienza (es. [0,0,0,1,1,2,…])."""
    m = []
    for idx, r in enumerate(paragraph.runs):
        m.extend([idx] * len(r.text))
    return m

def apply_correction_to_paragraph(
    p: Paragraph,
    corrected: str,
    mods: list[Modification],
    par_id: int,
    glossary: set[str],
):
    """
    Aggiorna il paragrafo Word `p` con il testo `corrected`,
    preservando la formattazione dei run e registrando la modifica.
    Passaggi principali:
    1. Normalizza virgolette + a-capo
    2. Rimuove a-capo interni superflui
    3. Elimina doppi segni di punteggiatura (.?,!)
    4. Filtro di sicurezza (_too_much_cut)
    5. Diff token-level → mapping token/run
    6. Scrive i token nei run corrispondenti
    7. Fix post-processing su virgolette e <w:br/>
    8. Aggiorna il glossario dinamico
    """
    original = p.text

    # 1. Normalizza virgolette + line-break
    corrected = re.sub(r'([«“"”])\s*[\r\n]+\s*', r'\1 ', corrected)  # quote\n → quote␠
    corrected = re.sub(r'[\r\n]+\s*([«“"”])', r' \1', corrected)     # \nquote → ␠quote

    # 2. Se l’originale non aveva a-capo interni, sostituiscili con spazi
    if ("\n" in corrected or "\r" in corrected) and ("\n" not in original and "\r" not in original):
        corrected = corrected.replace("\r", " ").replace("\n", " ")

    # 3. Elimina eventuali doppi . ! ? prodotti dal merge dei token
    corrected = _remove_duplicate_punct(corrected)

    # Se dopo le normalizzazioni il testo è identico, termina
    if corrected == original:
        return

    # 4. Scudo anti-tagli eccessivi
    if _too_much_cut(original, corrected):
        return

    # 5. Diff token-level
    orig_tok = tokenize(original)
    corr_tok = tokenize(corrected)
    mapping  = align_tokens(orig_tok, corr_tok)
    if all(a == b for a, b in zip(orig_tok, corr_tok)):
        return  # cambi minimi → ignora

    mods.append(Modification(par_id, original, corrected))

    # 6. Mappa token → run Word
    char2run = _run_map(p)
    tok_per_run: dict[int, list[str]] = defaultdict(list)
    starts_orig = token_starts(orig_tok)

    last_idx = 0
    for ref_idx, tok in mapping:
        run_idx = last_idx if ref_idx is None else char2run[min(starts_orig[ref_idx], len(char2run) - 1)]
        tok_per_run[run_idx].append(tok)
        last_idx = run_idx

    for idx, run in enumerate(p.runs):
        if idx in tok_per_run:
            run.text = "".join(tok_per_run[idx])

    # 7. Post-fix: gestisci run-virgoletta e <w:br/>
    orphan_quotes = {'"', '«', '“', '”'}
    runs = list(p.runs)
    for i, run in enumerate(runs):
        t = (run.text or "").strip()
        if t in orphan_quotes and i + 1 < len(runs) and (runs[i + 1].text or "").strip():
            runs[i + 1].text = run.text + runs[i + 1].text
            run.text = ""  # svuota la virgoletta “orfana”

    runs = list(p.runs)  # aggiorna lista
    open_quotes = orphan_quotes | {'‘', '’'}
    for i in range(len(runs) - 1):
        prev_txt = (runs[i].text or "")
        next_txt = (runs[i + 1].text or "")
        has_only_br = not next_txt.strip() and runs[i + 1]._r.xpath("./w:br")
        if prev_txt and prev_txt[-1] in open_quotes and has_only_br:
            runs[i + 1]._r.getparent().remove(runs[i + 1]._r)

    # 8. Glossario dinamico
    for name in NAME_RE.findall(corrected):
        if name.upper() not in GLOSSARY_STOP:
            glossary.add(name)
# ╰─────────────────────────────────────────────────────────────────────╯

async def grammarcheck_async(text: str) -> str:
    """
    Esegue grammarcheck() in un thread del pool,
    così possiamo processare paragrafi in parallelo.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(LT_POOL, grammarcheck, text)

def _minor_change(a: str, b: str) -> bool:
    import unicodedata, re
    norm = lambda s: re.sub(r"\W+", "", unicodedata.normalize("NFD", s).lower())
    return norm(a) == norm(b)

# ─────────── Pipeline locale + batch GPT multiparagrafo ───────────

# ─────────────────────────── correct_paragraph_group ──────────────────────────
async def correct_paragraph_group(
    paragraphs:   list[Paragraph],
    all_paras:    list[Paragraph],   # non usato qui, ma lasciato per compatibilità
    start_par_id: int,
    client:       AsyncOpenAI,
    glossary:     set[str],
    mods:         list[Modification],
    context_size: int = 3,
    safe_corrector: Optional[SafeCorrector] = None,
):
    """
    Pipeline di correzione sicura e controllata con CACHE INTELLIGENTE - FASE 4:
    • Cache check preliminare per ogni paragrafo
    • Step 1: Spell-check sicuro con rollback
    • Step 2: Grammar-check sicuro con rollback  
    • Step 3: AI correction batch con validazione e caching
    • Ogni step è validato prima dell'applicazione
    • Log dettagliati e statistiche per monitoring
    """
    logger = logging.getLogger("SAFE-PAR-GROUP")
    logger.debug("Safe chunk START (FASE 4) paragrafi=%d  start_id=%d", len(paragraphs), start_par_id)

    # Inizializza corrector e cache se non forniti (usa quello già configurato con quality threshold)
    if safe_corrector is None:
        # Fallback con threshold di default solo se non viene passato
        safe_corrector = SafeCorrector(conservative_mode=True, quality_threshold=0.85)
    
    cache = get_cache()
    formatting_manager = FormattingManager()  # Gestisce preservazione formattazione

    # Statistiche del chunk con cache
    chunk_stats = {
        'cache_hits': 0,
        'spellcheck_applied': 0,
        'grammar_applied': 0,
        'ai_applied': 0,
        'rollbacks': 0,
        'no_changes': 0
    }

    # Liste per i paragrafi che richiedono AI correction
    pending_idx: list[int] = []
    pending_txt: list[str] = []

    # ── Pipeline di correzione sicura per ogni paragrafo con CACHE ─────────────
    for idx, p in enumerate(paragraphs):
        original = p.text
        if not original.strip():
            chunk_stats['no_changes'] += 1
            continue

        par_id = start_par_id + idx
        
        # 🚀 CORREZIONI IMMEDIATE PREMIUM - STEP 0: Correggi errori evidenti PRIMA della cache
        if instant_fixer and original.strip():
            fixed_text, instant_corrections = instant_fixer.fix_text_instant(original)
            if instant_corrections:
                logger.info(f"🚀 Applicate {len(instant_corrections)} correzioni immediate a paragrafo {par_id}:")
                for correction in instant_corrections:
                    logger.info(f"   ✅ {correction}")
                
                # Applica le correzioni immediate
                if fixed_text != original:
                    try:
                        # Aggiorna il paragrafo con le correzioni immediate
                        p.text = fixed_text
                        
                        # Registra la modifica
                        mods.append(Modification(par_id, original, fixed_text))
                        
                        # Aggiorna le statistiche
                        chunk_stats['instant_fixes'] = chunk_stats.get('instant_fixes', 0) + len(instant_corrections)
                        
                        # Aggiorna la variabile original per i passi successivi
                        original = fixed_text
                        
                        logger.info(f"✅ Correzioni immediate applicate al paragrafo {par_id}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️  Errore applicando correzioni immediate al paragrafo {par_id}: {e}")
        
        # ═══ CACHE CHECK PRELIMINARE - FASE 4 ═══
        cached_entry = cache.get_with_similarity(original, threshold=0.98)
        if cached_entry and cached_entry.quality_score >= 0.85:
            # Usa risultato dalla cache
            formatting_manager.preserve_formatting_in_correction(p, original, cached_entry.corrected_text)
            chunk_stats['cache_hits'] += 1
            
            # Registra la modifica
            if cached_entry.corrected_text != original:
                mods.append(Modification(par_id, original, cached_entry.corrected_text))
                
                # Aggiorna glossario
                for name in NAME_RE.findall(cached_entry.corrected_text):
                    if name.upper() not in GLOSSARY_STOP:
                        glossary.add(name)
                        
            logger.debug(f"💾 Cache HIT for paragraph {par_id} (quality: {cached_entry.quality_score:.3f})")
            continue

        current_text = original
        
        # ═══ STEP 1: SPELLCHECK SICURO ═══
        def spellcheck_func(text):
            return spellfix_paragraph(text, glossary)
        
        spellcheck_result = safe_corrector.correct_with_rollback(
            p, spellcheck_func, "spellcheck"
        )
        
        if spellcheck_result.applied:
            current_text = spellcheck_result.corrected_text
            chunk_stats['spellcheck_applied'] += 1
            logger.debug(f"✅ Spellcheck applied to paragraph {par_id}")
        elif spellcheck_result.rollback_reason:
            chunk_stats['rollbacks'] += 1
            logger.debug(f"🔄 Spellcheck rolled back for paragraph {par_id}: {spellcheck_result.rollback_reason}")

        # ═══ STEP 2: GRAMMAR CHECK SICURO ═══
        async def grammar_func(text):
            return await grammarcheck_async(text)
        
        # Per il grammar check usiamo una versione sincrona
        grammar_corrected = await grammarcheck_async(current_text)
        
        # Validazione manuale della correzione grammaticale
        if grammar_corrected != current_text:
            if validate_correction(current_text, grammar_corrected):
                # Applica la correzione grammaticale direttamente se supera la validazione base
                formatting_manager.preserve_formatting_in_correction(p, current_text, grammar_corrected)
                current_text = grammar_corrected
                chunk_stats['grammar_applied'] += 1
                
                # Registra la modifica
                mods.append(Modification(par_id, original, current_text))
                
                # Aggiorna glossario
                for name in NAME_RE.findall(current_text):
                    if name.upper() not in GLOSSARY_STOP:
                        glossary.add(name)
                        
                logger.debug(f"✅ Grammar correction applied to paragraph {par_id}")
            else:
                chunk_stats['rollbacks'] += 1
                logger.debug(f"🔄 Grammar correction rolled back for paragraph {par_id}: validation failed")

        # ═══ STEP 3: AI CORRECTION (se necessario) ═══
        # Se abbiamo già fatto correzioni significative, potremmo non aver bisogno di AI
        if current_text == original or _minor_change(original, current_text):
            # Aggiunge alla lista per AI batch processing
            pending_idx.append(idx)
            pending_txt.append(current_text)
        else:
            # Già corretto sufficientemente
            chunk_stats['no_changes'] += 1 if current_text == original else 0

    # ═══ BATCH AI CORRECTION CON CACHE - FASE 4 ═══
    logger.info(
        "Safe chunk %d (FASE 4): cache=%d spell=%d grammar=%d rollbacks=%d pending_ai=%d",
        start_par_id,
        chunk_stats['cache_hits'],
        chunk_stats['spellcheck_applied'],
        chunk_stats['grammar_applied'], 
        chunk_stats['rollbacks'],
        len(pending_idx)
    )

    # Se nulla richiede AI, termina
    if not pending_txt:
        logger.debug("Safe chunk %d completed (no AI needed).", start_par_id)
        return

    # AI batch processing con validazione e caching
    try:
        start_time = time.time()
        corrected_list = await llm_correct_batch(pending_txt, client)
        processing_time = time.time() - start_time
        
        # Applica le correzioni AI con validazione e caching
        for local_i, ai_corrected in zip(pending_idx, corrected_list):
            p = paragraphs[local_i]
            original_para_text = p.text
            
            # 🚀 CORREZIONI IMMEDIATE PREMIUM - applica prima dell'AI
            if instant_fixer and original_para_text.strip():
                fixed_text, instant_corrections = instant_fixer.fix_text_instant(original_para_text)
                if instant_corrections:
                    logger.info(f"🚀 Applicate {len(instant_corrections)} correzioni immediate a par {start_par_id + local_i}:")
                    for correction in instant_corrections:
                        logger.info(f"   ✅ {correction}")
                    
                    # Applica le correzioni immediate al paragrafo
                    if fixed_text != original_para_text:
                        par_id = start_par_id + local_i
                        mods.append(Modification(par_id, original_para_text, fixed_text))
                        
                        # Aggiorna il testo del paragrafo per ulteriori processing
                        try:
                            p.text = fixed_text
                            chunk_stats['instant_fixes'] = chunk_stats.get('instant_fixes', 0) + len(instant_corrections)
                        except Exception as e:
                            logger.warning(f"⚠️  Errore applicando correzione immediata: {e}")
            
            if ai_corrected != original_para_text:
                # Validazione della correzione AI
                if validate_correction(original_para_text, ai_corrected):
                    formatting_manager.preserve_formatting_in_correction(p, original_para_text, ai_corrected)
                    par_id = start_par_id + local_i
                    
                    # Registra la modifica
                    mods.append(Modification(par_id, original_para_text, ai_corrected))
                    
                    # Aggiorna glossario
                    for name in NAME_RE.findall(ai_corrected):
                        if name.upper() not in GLOSSARY_STOP:
                            glossary.add(name)
                    
                    # ═══ CACHE IL RISULTATO AI - FASE 4 ═══
                    # Calcola quality score approssimativo
                    quality_score = 0.9  # Alto per correzioni AI validate
                    if len(ai_corrected) > len(original_para_text) * 1.2:
                        quality_score = 0.7  # Penalizza espansioni eccessive
                    elif len(ai_corrected) < len(original_para_text) * 0.8:
                        quality_score = 0.75  # Penalizza riduzioni eccessive
                    
                    cache.cache_with_metadata(
                        text=original_para_text,
                        correction=ai_corrected,
                        quality=quality_score,
                        correction_type="ai",
                        processing_time=processing_time / len(pending_txt),  # Tempo per paragrafo
                        token_count=len(original_para_text.split()) + len(ai_corrected.split())
                    )
                    
                    chunk_stats['ai_applied'] += 1
                    logger.debug(f"✅ AI correction applied and cached for paragraph {par_id} (quality: {quality_score:.3f})")
                else:
                    chunk_stats['rollbacks'] += 1
                    logger.warning(f"🔄 AI correction rolled back for paragraph {par_id}: validation failed")
                    
    except Exception as e:
        logger.error(f"❌ AI batch processing failed for chunk {start_par_id}: {e}")
        # Continua senza AI correction - i paragrafi mantengono le correzioni precedenti

    # Log finale del chunk con cache stats
    logger.info(
        "Safe chunk %d completed (FASE 4): cache=%d spell=%d grammar=%d ai=%d rollbacks=%d",
        start_par_id,
        chunk_stats['cache_hits'],
        chunk_stats['spellcheck_applied'],
        chunk_stats['grammar_applied'],
        chunk_stats['ai_applied'],
        chunk_stats['rollbacks']
    )
    
    logger.debug("Safe chunk END %d", start_par_id)
# ───────────────────────────────────────────────────────────────────────────────

# ╭─────────────────── Funzione generica di correzione ─────────────────╮
#async def correct_paragraph_group(
#    paragraphs:   list[Paragraph],
#    all_paras:    list[Paragraph],
#    start_par_id: int,
#    client:       AsyncOpenAI,
#    glossary:     set[str],
#    mods:         list[Modification],
#    context_size: int = 3,
#):
#    sem = asyncio.Semaphore(10)  # max 10 chiamate in parallelo

#    async def process_one(par_id: int, p: Paragraph) -> tuple[Paragraph, str]:
#        original_text = p.text
#        if not original_text.strip():
#            return p, original_text

#        step1 = spellfix_paragraph(original_text, glossary)
#        step2 = await grammarcheck_async(step1)

        # Solo se spellfix+grammarcheck NON hanno cambiato nulla → LLM
#            if step2 == original_text:
#                async with sem:
#                    final = await llm_correct(step2, client)
#            else:
#                final = step2


#            return p, final

#        tasks = [
#            asyncio.create_task(process_one(start_par_id + i, p))
#            for i, p in enumerate(paragraphs)
#        ]

#        results = await asyncio.gather(*tasks)

#        for i, (p, corrected_text) in enumerate(results):
#            if corrected_text != p.text:
#                apply_correction_to_paragraph(
#                    p,
#                    corrected_text,
#                    mods,
#                    start_par_id + i,
#                    glossary,
#                )
# ╰──────────────────────────────────────────────────────────────────────╯
# ╭──────────────────── Wrapper: corpo principale ─────────────────────╮
async def fix_body_chunks(
    async_client: AsyncOpenAI,
    all_paras:    list[Paragraph],
    para_chunks:  list[list[Paragraph]],
    start_id:     int,
    mods:         list[Modification],
    glossary:     set[str],
    safe_corrector: Optional[SafeCorrector] = None,
):
    """
    Scorre tutti i chunk creati da `chunk_paragraph_objects`, lancia
    in parallelo `correct_paragraph_group` con sistema di correzione sicura
    e mostra una progress-bar che avanza quando ciascun chunk è completato.
    """
    
    # Inizializza corrector se non fornito (usa quello già configurato con quality threshold)
    if safe_corrector is None:
        # Fallback con threshold di default solo se non viene passato
        safe_corrector = SafeCorrector(conservative_mode=True, quality_threshold=0.85)
    
    tasks: list[asyncio.Task] = []
    par_id = start_id

    # Costruisci la lista dei task mantenendo l'ID di paragrafo corretto
    for chunk in para_chunks:
        task = asyncio.create_task(correct_paragraph_group(
            paragraphs   = chunk,
            all_paras    = all_paras,
            start_par_id = par_id,
            client       = async_client,
            glossary     = glossary,
            mods         = mods,
            safe_corrector = safe_corrector,
        ))
        tasks.append(task)
        par_id += len(chunk)

    # Progress-bar: si aggiorna al termine di ogni task
    await tqdm_asyncio.gather(
        *tasks,
        total=len(tasks),
        desc="Correzione chunk"
    )
# ╰──────────────────────────────────────────────────────────────────────╯

# ╭─────────────────────────── Map char→run ▾────────────────────────────╮
def char_to_run_map(paragraph) -> List[int]:
    mapping: List[int] = []
    for idx, run in enumerate(paragraph.runs):
        mapping.extend([idx] * len(run.text))
    return mapping
# ╰──────────────────────────────────────────────────────────────────────╯
# ───────────────────── Detect equazioni OMML ──────────────────────────
def has_math(paragraph: Paragraph) -> bool:
    """
    Ritorna True se il <w:p> contiene almeno un elemento <m:oMath>
    o <m:oMathPara> (= equazioni Word).
    """
    return bool(
        paragraph._p.xpath(
            ".//*[local-name()='oMath' or local-name()='oMathPara']"
        )
    )
# ──────────────────────────────────────────────────────────────────────
# ───────────────────────── traversal del documento ─────────────────────────────
def iter_body_paragraphs(container) -> Iterable[Paragraph]:
    for para in container.paragraphs:
        yield para
    for tbl in getattr(container, "tables", []):
        for row in tbl.rows:
            for cell in row.cells:
                yield from iter_body_paragraphs(cell)


def iter_footnote_paragraphs(doc: Document) -> Iterable[Paragraph]:  # type: ignore[type-arg]
    fpart = getattr(doc.part, "footnotes_part", None)
    if fpart:
        for footnote in fpart.footnotes:
            for para in footnote.paragraphs:
                yield para


def iter_header_footer_paragraphs(doc: Document) -> Iterable[Paragraph]:  # type: ignore[type-arg]
    for sect in doc.sections:
        for hf in (sect.header, sect.footer):
            if hf:
                yield from iter_body_paragraphs(hf)


def iter_textbox_paragraphs(doc: Document) -> Iterable[Paragraph]:  # type: ignore[type-arg]
    parts = [doc.part]
    for sect in doc.sections:
        parts.extend([sect.header.part, sect.footer.part])
    fpart = getattr(doc.part, "footnotes_part", None)
    if fpart:
        parts.append(fpart)
    for part in parts:
        root = part._element
        for txbx in root.xpath('.//*[local-name()="txbxContent"]'):
            for p_el in txbx.xpath('.//*[local-name()="p"]'):
                yield Paragraph(p_el, part)


def iter_all_paragraphs(doc: Document) -> Iterable[Paragraph]:  # type: ignore[type-arg]
    yield from iter_body_paragraphs(doc)
    yield from iter_footnote_paragraphs(doc)
    yield from iter_header_footer_paragraphs(doc)
    yield from iter_textbox_paragraphs(doc)
# ──────────────────────────────────────────────────────────────────────

# ───────────────── Helper: verifica se C è interamente contenuto in A ─────────
def _is_clone(text_a: str, text_c: str, threshold: float = 0.95) -> bool:
    """
    True se C è quasi uguale (≥95 %) alla coda di A.
    Usa SequenceMatcher per maggiore robustezza.
    """
    norm = lambda s: " ".join(s.split()).lower()
    return SequenceMatcher(None, norm(text_a), norm(text_c)).ratio() >= threshold
# ───────────────────────────────────────────────────────────────────────────────

# ───────────────── FINE DEGLI HELPER ────────────────
# ───────────────── Deduplica paragrafi clonati dopo un sectPr ────────────────
def remove_duplicate_after_sectpr(document: Document) -> None:  # type: ignore[type-arg]
    """
    Se trova la sequenza:
        A = paragrafo con testo
        B = paragrafo VUOTO con <w:sectPr>
        C = paragrafo la cui *intera* stringa è già contenuta in coda ad A
    elimina C ma mantiene B (così l’interruzione di sezione resta).
    """
    paras = list(iter_body_paragraphs(document))
    for i in range(len(paras) - 2, 0, -1):
        A, B, C = paras[i - 1], paras[i], paras[i + 1]
        if B.text.strip():                       # B deve essere vuoto
            continue
        if not B._p.xpath("./w:pPr/w:sectPr"):   # B deve avere <w:sectPr>
            continue
        text_a = A.text.strip()
        text_c = C.text.strip()
        if text_c and _is_clone(text_a, text_c):
            C._p.getparent().remove(C._p)
# ─────────────────────────────────────────────────────────────────────────────

# ───────────────────────── entry-point con logging ────────────────────
def process_doc(inp: Path, out: Path, quality_threshold: float = 0.85):
    """
    Processo principale di correzione del documento con validazione e backup integrati.
    """
    
    # ===== FASE 1: VALIDAZIONE E BACKUP =====
    logger.info("🔍 Starting document validation and backup...")
    
    # 1.1 Validazione preliminare del documento
    validation_result = validate_document(inp)
    if not validation_result.is_valid:
        critical_issues = [issue for issue in validation_result.issues 
                          if any(word in issue.lower() for word in ['error', 'cannot', 'failed', 'invalid'])]
        if critical_issues:
            logger.error("❌ Document validation failed with critical issues:")
            for issue in critical_issues:
                logger.error(f"   • {issue}")
            raise RuntimeError(f"Cannot process document due to validation errors: {critical_issues}")
        else:
            logger.warning("⚠️  Document has minor validation issues but proceeding:")
            for issue in validation_result.issues:
                logger.warning(f"   • {issue}")
    
    logger.info(f"✅ Document validated: {validation_result.paragraph_count} paragraphs, {validation_result.character_count} characters")
    
    # 1.2 Backup automatico del documento originale
    backup_path = create_backup(inp)
    logger.info(f"💾 Backup created: {backup_path.name}")
    
    # 1.3 Inizializza sistema di correzione sicura con soglia qualità personalizzata
    logger.info(f"🎯 Quality threshold impostata al {quality_threshold*100:.0f}%")
    safe_corrector = SafeCorrector(conservative_mode=True, quality_threshold=quality_threshold)
    
    # ===== FASE 2: CARICAMENTO E ANALISI =====
    try:
        doc = Document(str(inp))
    except Exception as e:
        logger.error(f"❌ Failed to load document: {e}")
        raise RuntimeError(f"Cannot load document: {e}")

    # ===== FASE 4: INIZIALIZZAZIONE CACHE E PROCESSAMENTO PARALLELO =====
    logger.info("🚀 Initializing intelligent cache and parallel processing...")
    
    # Inizializza cache intelligente
    cache = get_cache()
    cache_stats_before = cache.get_cache_stats()
    logger.info(f"💾 Cache status: {cache_stats_before.total_entries} entries, hit rate: {cache_stats_before.hit_rate:.2%}")
    
    # Inizializza processatore parallelo con stima ottimale workers
    total_chars = sum(len(p.text) for p in iter_all_paragraphs(doc))
    estimated_tokens = int(total_chars * 1.3)  # Stima approssimativa
    parallel_corrector = get_parallel_corrector(max_concurrent=5)
    optimal_workers = parallel_corrector.estimate_optimal_workers(estimated_tokens, target_time_minutes=5)
    logger.info(f"⚡ Parallel processing initialized: {optimal_workers} optimal workers for {estimated_tokens:,} tokens")

    # 1. Raccoglie tutti i paragrafi del documento (corpo, intestazioni, piè di pagina, note, caselle di testo)
    all_paras = list(iter_all_paragraphs(doc))
    paras_to_fix = [
        p
        for p in all_paras
        if has_errors(p.text) and not has_math(p)
    ]

    # Log statistiche documento
    logger.info(f"📊 Document analysis:")
    logger.info(f"   • Total paragraphs: {len(all_paras)}")
    logger.info(f"   • Paragraphs needing correction: {len(paras_to_fix)}")
    logger.info(f"   • Total characters: {sum(len(p.text) for p in all_paras):,}")
    logger.info(f"   • Cache entries available: {cache_stats_before.total_entries}")

    # 2. Crea un glossario iniziale con i nomi ricorrenti (apparsi almeno 2 volte)
    name_counts = collections.Counter(
        n for p in all_paras for n in NAME_RE.findall(p.text)
        if n.upper() not in GLOSSARY_STOP
    )
    glossary = {w for w, c in name_counts.items() if c >= 2}

    # 3. Suddivide il corpo del documento in chunk, rispettando il limite di token
    para_chunks = chunk_paragraphs_all(all_paras, max_tokens=3_000, max_pars=5)
    total_chunks = len(para_chunks)
    logger.info("🔍  Rilevati %s chunk universali (≤5 paragrafi, ≤3000 token).", total_chunks)

    # 4. Lista per raccogliere tutte le modifiche da riportare nel diff finale
    mods: list[Modification] = []

    # 5. Definisce la coroutine che gestisce l'intero flusso asincrono (corpo + note)
    async def handle_all(doc: Document, out_path: Path):  # type: ignore[type-arg]
        async_client = get_async_client()

        # 5.1 Corregge il corpo del documento (in parallelo, chunk per chunk)
        await fix_body_chunks(
            async_client=async_client,
            all_paras=all_paras,
            para_chunks=para_chunks,
            start_id=1,
            mods=mods,
            glossary=glossary,
            safe_corrector=safe_corrector,
        )
        # Deduplica cloni post-correzione ma conserva l'interruzione di sezione
        remove_duplicate_after_sectpr(doc)  

        # 5.2 Salva il documento corretto prima di correggere le note (serve file .docx completo)
        doc.save(out_path)
        logger.info("💾  Documento salvato: %s", out_path.name)

        # 5.3 Corregge le note a piè di pagina in parallelo
        await correggi_footnotes_xml_async(
            docx_path=out_path,
            async_client=async_client,
            glossary=glossary,
        )

    # 6. Avvia l'evento asincrono completo
    asyncio.run(handle_all(doc, out))

    # ===== FASE 3: VALIDAZIONE POST-CORREZIONE =====
    # 7.1 Validazione finale del documento corretto
    logger.info("🔍 Validating corrected document...")
    final_validation = validate_document(out)
    
    if not final_validation.is_valid:
        logger.error("❌ Corrected document validation failed!")
        logger.info("♻️  Attempting to restore from backup...")
        validator = DocumentValidator()
        if validator.restore_from_backup(backup_path, out):
            logger.info("✅ Document restored from backup")
        else:
            logger.error("❌ Failed to restore from backup!")
            raise RuntimeError("Correction failed and backup restoration failed")
    else:
        logger.info("✅ Corrected document validation passed")
    
    # 7.2 Statistiche finali delle correzioni
    correction_stats = safe_corrector.get_correction_stats()
    logger.info("📊 Final correction statistics:")
    logger.info(f"   • Total correction attempts: {correction_stats['total_attempts']}")
    logger.info(f"   • Successful corrections: {correction_stats['successful_corrections']}")
    logger.info(f"   • Rollbacks: {correction_stats['rollbacks']}")
    if correction_stats['total_attempts'] > 0:
        logger.info(f"   • Success rate: {correction_stats.get('success_rate', 0):.1%}")
        logger.info(f"   • Rollback rate: {correction_stats.get('rollback_rate', 0):.1%}")

    # 7.3 Statistiche cache e performance - FASE 4
    cache_stats_after = cache.get_cache_stats()
    parallel_stats = parallel_corrector.get_parallel_stats()
    
    logger.info("🚀 FASE 4 - Performance Optimization Results:")
    logger.info(f"💾 Cache Performance:")
    logger.info(f"   • Entries: {cache_stats_after.total_entries} (+{cache_stats_after.total_entries - cache_stats_before.total_entries})")
    logger.info(f"   • Hit rate: {cache_stats_after.hit_rate:.2%}")
    logger.info(f"   • Performance gain: {cache_stats_after.performance_gain:.1f}s saved")
    logger.info(f"   • Average quality: {cache_stats_after.avg_quality:.3f}")
    
    logger.info(f"⚡ Parallel Processing:")
    logger.info(f"   • Total tasks: {parallel_stats.total_tasks}")
    logger.info(f"   • Completed: {parallel_stats.completed_tasks}")
    logger.info(f"   • Cached results: {parallel_stats.cached_results}")
    logger.info(f"   • Throughput: {parallel_stats.throughput_per_minute:.1f} tasks/min")
    logger.info(f"   • Efficiency: {parallel_stats.parallelism_efficiency:.1%}")
    
    # Cleanup cache se richiesto
    if cache_stats_after.expired_count > 100:
        optimization_stats = cache.optimize_cache()
        logger.info(f"🧹 Cache optimized: removed {optimization_stats['total_removed']} entries")
    
    # Shutdown parallel corrector
    parallel_corrector.shutdown()

    # 7.3 Genera i due report Markdown (diff + glossario)
    write_markdown_report(mods, out)  # type: ignore[arg-type]
    write_glossary_report(glossary, all_paras, out)


# ───────────────────────────────────────────────────────────────────────
def find_latest_docx(folder: Path) -> Path:
    """
    Cerca il file più recente con estensione .docx, .odt o .doc (esclude i
    file di lock ~$.docx). Se non è già .docx lo converte con Pandoc.
    """
    candidates = [
        p for p in folder.iterdir()
        if p.is_file()
        and not p.name.startswith("~$")
        and p.suffix.lower() in (".docx", ".odt", ".doc")
    ]
    if not candidates:
        raise RuntimeError("Nessun documento .docx/.odt/.doc trovato nella cartella")

    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    return convert_to_docx(latest)


if __name__ == "__main__":
    # marca inizio
    start_time = time.perf_counter()
    
    # Inizializza monitoring
    monitor = get_monitor()

    here = Path(__file__).resolve().parent
    src = find_latest_docx(here)
    dst = src.with_stem(src.stem + "_corretto")
    logger.info("📝  Correggo %s → %s …", src.name, dst.name)
    
    # Ottieni info documento pre-processamento
    doc = Document(str(src))
    original_text = "\n".join([p.text for p in doc.paragraphs])
    char_count = len(original_text)
    
    process_doc(src, dst)

    # tempo impiegato e registrazione metriche
    elapsed = time.perf_counter() - start_time
    
    # Registra processamento nel monitor
    monitor.record_document_processing(
        document_path=src,
        processing_time=elapsed,
        characters_processed=char_count,
        corrections_made=0,  # TODO: aggiungere conteggio correzioni da process_doc
        quality_score=0.9   # TODO: aggiungere quality assessment
    )
    
    logger.info("✨  Fatto in %.2f secondi!", elapsed)
    
    # Genera report di monitoring se richiesto
    if os.getenv('GENERATE_MONITORING_REPORT'):
        from src.interfaces.dashboard import generate_dashboard
        generate_dashboard(here / "monitoring_dashboard.html")
        logger.info("📊  Dashboard di monitoring generata: monitoring_dashboard.html")