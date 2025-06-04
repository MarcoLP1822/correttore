# token_utils.py
import re
import tiktoken

_DEFAULT_MODEL = "gpt-4o-mini"   # o quello che preferisci
try:
    ENC = tiktoken.encoding_for_model(_DEFAULT_MODEL)
except KeyError:
    ENC = tiktoken.get_encoding("cl100k_base")

WORD_RE = re.compile(r"\w+|\W+")

def tokenize(text: str):
    return WORD_RE.findall(text)

def count_tokens(text: str) -> int:
    """Conta i token reali secondo l’encoding del modello."""
    return len(ENC.encode(text or ""))
    
def token_starts(tokens):
    pos, starts = 0, []
    for tok in tokens:
        starts.append(pos)
        pos += len(tok)
    return starts