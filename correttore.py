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
from precheck import has_errors
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional, Tuple
from pprint import pprint

# ——— Third-party ————————————————————————————————
import tiktoken
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio
from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from lxml import etree
from lxml.etree import XMLSyntaxError
from openai import AsyncOpenAI, OpenAI
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env.local
load_dotenv('.env.local')

# ——— Local modules ————————————————————————————————
from reports import write_glossary_report, write_markdown_report
from token_utils import tokenize, token_starts, count_tokens
from utils_openai import (
    _OPENAI_MODEL as OPENAI_MODEL,
    get_corrections_async,
    get_corrections_sync,
)

# ───────────────────────── CONFIGURAZIONE ────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Lunghezza massima di contesto (in token) accettata in un singolo prompt
MAX_TOKENS_GPT4O_MINI = 10000

try:
    ENC = tiktoken.encoding_for_model(OPENAI_MODEL)
except KeyError:
    # fallback universale, compatibile con GPT-4/3.5
    ENC = tiktoken.get_encoding("cl100k_base")
# ─────────────────────────────────────────────────────────────────────

WORD_RE = re.compile(r"\w+|\W+")
# 👇 NUOVO: riconosce parole in PascalCase o TUTTO MAIUSCOLO ≥ 3 lettere
NAME_RE = re.compile(r"\b(?:[A-Z][a-z]{2,}|[A-Z]{2,})\w*\b")

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
    print("✏️  Note a piè di pagina corrette e formattazione preservata")
# ╭─────────────────────────── Data-model modifiche ▾────────────────────╮
@dataclass
class Modification:
    par_id: int
    original: str
    corrected: str
# ╰──────────────────────────────────────────────────────────────────────╯

# ╭─────────────────────────── Chunking ▾────────────────────────────────╮
def chunk_paragraph_objects(
    paragraphs: List[Paragraph],
    max_tokens: int = MAX_TOKENS_GPT4O_MINI,
) -> List[List[Paragraph]]:
    """Dividi la lista di oggetti Paragraph in blocchi < max_tokens."""
    chunks: List[List[Paragraph]] = []
    current: List[Paragraph] = []
    current_tokens = 0

    for p in paragraphs:
        para_tokens = count_tokens(p.text)

        # 1) se il singolo paragrafo sfora il limite, isolalo
        if para_tokens > max_tokens:
            if current:                     # salva il chunk in corso
                chunks.append(current)
                current, current_tokens = [], 0
            chunks.append([p])              # paragrafo “oversize” da solo
            continue                        # salta al paragrafo successivo

        # 2) comportamento normale
        if current and current_tokens + para_tokens > max_tokens:
            chunks.append(current)
            current = [p]
            current_tokens = para_tokens
        else:
            current.append(p)
            current_tokens += para_tokens

    if current:
        chunks.append(current)
    return chunks
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

# ─────────────────────────── NUOVO BLOCCO paragrafi multipli ──────────────────────────────
def apply_correction_to_paragraph(
    p: Paragraph,
    corrected: str,
    mods: List[Modification],
    par_id: int,
    glossary: set[str],
):
    """
    Sovrascrive il paragrafo `p` con il testo già corretto
    preservandone la formattazione run-per-run.
    """
    original = p.text
    if corrected == original:
        return

    mods.append(Modification(par_id, original, corrected))

    # === ricostruzione dei run (stessa logica di prima) ===============
    orig_tok  = tokenize(original)
    corr_tok  = tokenize(corrected)
    mapping   = align_tokens(orig_tok, corr_tok)
    starts    = token_starts(orig_tok)
    char_run  = char_to_run_map(p)

    tokens_per_run: Dict[int, List[str]] = defaultdict(list)
    last_run_idx: Optional[int] = None
    for ref_idx, tok in mapping:
        if not char_run:
            run_idx = 0
        elif ref_idx is None:
            run_idx = last_run_idx if last_run_idx is not None else char_run[0]
        else:
            pos     = starts[ref_idx]
            run_idx = char_run[pos] if pos < len(char_run) else char_run[-1]
        last_run_idx = run_idx
        tokens_per_run[run_idx].append(tok)

    old_runs = list(p.runs)
    p._p.clear_content()

    for idx, run in enumerate(old_runs):
        toks = tokens_per_run.get(idx, [])
        if run.text:
            if not toks:
                continue
            new_run = clone_run(run, p)
            # 💥 work-around: se add_run ha restituito None rigenera il run
            if new_run is None:
                new_run = p.add_run("")
            new_run.text = "".join(toks)
        else:
            p._p.append(deepcopy(run._r))
                # --- aggiorna dinamicamente il glossario -------------------------
    for name in NAME_RE.findall(corrected):
        glossary.add(name)


# ╭─────────────────── Funzione generica di correzione ─────────────────╮
async def correct_paragraph_group(
    paragraphs:   list[Paragraph],
    all_paras:    list[Paragraph],
    start_par_id: int,
    client:       AsyncOpenAI,
    glossary:     set[str],
    mods:         list[Modification],
    context_size: int = 3,          # quanti paragrafi di contesto ricavare
):
    """
    Corregge un gruppo di Paragraph mantenendo formattazione e glossario.

    · paragraphs   : la "sezione" da correggere (chunk, note, header…)
    · all_paras    : lista completa per calcolare il contesto
    · start_par_id : id del primo paragrafo nel documento (1-based)
    · client       : istanza AsyncOpenAI condivisa
    · glossary     : set globale dei nomi canonici
    · mods         : lista in cui accumulare le modifiche per il report
    """

    # 1.  CONTEXTO – ultimi `context_size` paragrafi prima di questo blocco
    ctx_start = max(0, start_par_id - context_size - 1)
    context = "\n".join(p.text for p in all_paras[ctx_start : start_par_id - 1])

    # 2.  PAYLOAD JSON
    payload = [{"id": i, "txt": p.text} for i, p in enumerate(paragraphs)]
    payload_json = json.dumps(payload, ensure_ascii=False)

    # 3.  MESSAGGI
    messages = build_messages(context, payload_json, glossary)

    # 4. CHIAMATA OpenAI (ora delegata alla utility)
    raw = await get_corrections_async(
        payload_json = payload_json,   # JSON già costruito al punto 2
        client       = client,         # l'istanza AsyncOpenAI passata alla funzione
        glossary     = glossary,       # il set di nomi canonici
        context      = context,        # le righe di contesto calcolate al punto 1
    )
    if isinstance(raw, list):
        corr_list = raw 
    elif isinstance(raw, dict) and "corr" in raw:
        corr_list = raw["corr"]
    else:
        raise TypeError(
            f"Formato inatteso da get_corrections_async(): {type(raw)} – {raw!r}"
    )

    # 5.  APPLICA LE CORREZIONI  ─────────────────────────────────────────
    corr_by_id = {d["id"]: d["txt"] for d in corr_list}

    def _too_much_cut(orig: str, corr: str, thresh: float = 0.02) -> bool:
        """
        True se il testo corretto ha perso > thresh (2 %) dei token
        **oppure** se contiene meno frasi dell'originale.
        """
        tok_orig = tokenize(orig)
        tok_corr = tokenize(corr)
        if len(tok_orig) and (len(tok_orig) - len(tok_corr)) / len(tok_orig) > thresh:
            return True

        def _count_sent(txt: str) -> int:
            return len([s for s in re.split(r"[.!?…]", txt) if s.strip()])

        return _count_sent(corr) < _count_sent(orig)

    for local_id, p in enumerate(paragraphs):
        original_text  = p.text                              # copia intatta
        corrected_text = corr_by_id.get(local_id, original_text)

        # ─── Safety check ────────────────────────────────────────────
        if _too_much_cut(original_text, corrected_text):
            # ↓↓↓ A) fallback minimo: tieni l'originale  ↓↓↓
            corrected_text = original_text

            # --- B) oppure: ritenta con un modello "maggiore"  -------
            # corr_retry = await get_corrections_async(
            #     payload_json=json.dumps([{"id": 0, "txt": original_text}],
            #                            ensure_ascii=False),
            #     client=client_big,          # istanza GPT-4
            #     glossary=glossary,
            #     context=context,
            # )
            # corrected_text = corr_retry[0]["txt"]

        # se supera i controlli, o dopo l'eventuale retry, applica
        apply_correction_to_paragraph(
            p,
            corrected_text,
            mods,
            start_par_id + local_id,
            glossary,
        )

# ╰──────────────────────────────────────────────────────────────────────╯
# ╭──────────────────── Wrapper: corpo principale ─────────────────────╮
async def fix_body_chunks(
    async_client: AsyncOpenAI,
    all_paras:    list[Paragraph],
    para_chunks:  list[list[Paragraph]],
    start_id:     int,
    mods:         list[Modification],
    glossary:     set[str],
):
    """
    Scorre tutti i chunk creati da `chunk_paragraph_objects`, lancia
    in parallelo `correct_paragraph_group` e mostra una progress-bar
    che avanza quando ciascun chunk è realmente completato.
    """
    tasks: list[asyncio.Task] = []
    par_id = start_id

    # Costruisci la lista dei task mantenendo l'ID di paragrafo corretto
    for chunk in para_chunks:
        tasks.append(
            correct_paragraph_group(
                paragraphs   = chunk,
                all_paras    = all_paras,
                start_par_id = par_id,
                client       = async_client,
                glossary     = glossary,
                mods         = mods,
            )
        )
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

# ───────────────────────── traversal del documento ─────────────────────────────
def iter_body_paragraphs(container) -> Iterable[Paragraph]:
    for para in container.paragraphs:
        yield para
    for tbl in getattr(container, "tables", []):
        for row in tbl.rows:
            for cell in row.cells:
                yield from iter_body_paragraphs(cell)


def iter_footnote_paragraphs(doc: Document) -> Iterable[Paragraph]:
    fpart = getattr(doc.part, "footnotes_part", None)
    if fpart:
        for footnote in fpart.footnotes:
            for para in footnote.paragraphs:
                yield para


def iter_header_footer_paragraphs(doc: Document) -> Iterable[Paragraph]:
    for sect in doc.sections:
        for hf in (sect.header, sect.footer):
            if hf:
                yield from iter_body_paragraphs(hf)


def iter_textbox_paragraphs(doc: Document) -> Iterable[Paragraph]:
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


def iter_all_paragraphs(doc: Document) -> Iterable[Paragraph]:
    yield from iter_body_paragraphs(doc)
    yield from iter_footnote_paragraphs(doc)
    yield from iter_header_footer_paragraphs(doc)
    yield from iter_textbox_paragraphs(doc)
# ──────────────────────────────────────────────────────────────────────

# ───────────────────────── entry-point con logging ────────────────────
def process_doc(inp: Path, out: Path):
    doc = Document(inp)

    # 1. Raccoglie tutti i paragrafi del documento (corpo, intestazioni, piè di pagina, note, caselle di testo)
    all_paras = list(iter_all_paragraphs(doc))
    paras_to_fix = [p for p in all_paras if has_errors(p.text)]

    # 2. Crea un glossario iniziale con i nomi ricorrenti (apparsi almeno 2 volte)
    global GLOSSARY
    name_counts = collections.Counter(
        name
        for p in all_paras
        for name in NAME_RE.findall(p.text)
    )
    GLOSSARY = {w for w, c in name_counts.items() if c >= 2}

    # 3. Suddivide il corpo del documento in chunk, rispettando il limite di token
    para_chunks = chunk_paragraph_objects(paras_to_fix, max_tokens=4_000)
    total_chunks = len(para_chunks)

    print(f"🔍  Rilevati {total_chunks} chunk (limite {MAX_TOKENS_GPT4O_MINI} token).")

    # 4. Lista per raccogliere tutte le modifiche da riportare nel diff finale
    mods: list[Modification] = []

    # 5. Definisce la coroutine che gestisce l'intero flusso asincrono (corpo + note)
    async def handle_all(doc: Document, out_path: Path):
        async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

        # 5.1 Corregge il corpo del documento (in parallelo, chunk per chunk)
        await fix_body_chunks(
            async_client=async_client,
            all_paras=all_paras,
            para_chunks=para_chunks,
            start_id=1,
            mods=mods,
            glossary=GLOSSARY,
        )

        # 5.2 Salva il documento corretto prima di correggere le note (serve file .docx completo)
        doc.save(out_path)
        print(f"💾  Documento salvato: {out_path.name}")

        # 5.3 Corregge le note a piè di pagina in parallelo
        await correggi_footnotes_xml_async(
            docx_path=out_path,
            async_client=async_client,
            glossary=GLOSSARY,
        )

    # 6. Avvia l'evento asincrono completo
    asyncio.run(handle_all(doc, out))

    # 7. Genera i due report Markdown (diff + glossario)
    write_markdown_report(mods, out)
    write_glossary_report(GLOSSARY, all_paras, out)


# ───────────────────────────────────────────────────────────────────────

# ╭────────────────────────── Prompt & builder messaggi ─────────────────────────╮
SYSTEM_MSG_BASE = """
Sei un correttore di bozze madrelingua italiano con decenni di esperienza.

• Correggi **solo** refusi, errori ortografici / grammaticali e punteggiatura.  
• Non eliminare, spostare o accorciare parole, frasi o capoversi.  
• Non riformulare lo stile; se una parte è già corretta, lasciala invariata.

NOMI / TERMINI FANTASY ↓  
Se trovi varianti ortografiche dei nomi presenti nell'elenco seguente,
uniforma la grafia a quella esatta dell'elenco.

OUTPUT: restituisci **SOLO JSON** con la chiave `'corr'`
( lista di {id:int, txt:str} ) — niente testo extra.
"""

def build_messages(context: str, payload_json: str, glossary: set[str]) -> list[dict]:
    """
    Crea i tre messaggi da mandare a OpenAI:
        1. system    → vincoli + lista dei nomi "canonici"
        2. assistant → contesto di righe precedenti (NON va modificato)
        3. user      → JSON dei paragrafi da correggere
    """
    system_msg = SYSTEM_MSG_BASE + "\nLista: " + ", ".join(sorted(glossary))

    return [
        {"role": "system",    "content": system_msg},
        {"role": "assistant", "content": "Contesto (NON modificare):\n" + context},
        {"role": "user",      "content": payload_json},
    ]
# ╰──────────────────────────────────────────────────────────────────────────────╯

def find_latest_docx(folder: Path) -> Path:
    files = list(folder.glob("*.docx"))
    if not files:
        raise RuntimeError("Nessun .docx trovato nella cartella")
    return max(files, key=lambda p: p.stat().st_mtime)

if __name__ == "__main__":
    # marca inizio
    start_time = time.perf_counter()

    here = Path(__file__).resolve().parent
    src = find_latest_docx(here)
    dst = src.with_stem(src.stem + "_corretto")
    print(f"📝  Correggo {src.name} → {dst.name} …")
    process_doc(src, dst)

    # tempo impiegato
    elapsed = time.perf_counter() - start_time
    print(f"✨  Fatto in {elapsed:.2f} secondi!")