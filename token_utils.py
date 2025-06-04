# token_utils.py
import re
import tiktoken

DEFAULT_MODEL = "gpt-4o-mini"
try:
    ENC = tiktoken.encoding_for_model(DEFAULT_MODEL)
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