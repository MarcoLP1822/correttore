import os
import sys
os.chdir('C:\\Users\\Youcanprint1\\Desktop\\AI\\Correttore\\src\\core')
sys.path.insert(0, '.')

from precheck import has_errors

print('=== ANALISI DETTAGLIATA PARAGRAFI PROCESSATI ===')

# Testi dei paragrafi dal file originale
paragrafi_originali = [
    "CAPTIOLO 1",
    "C'era una vlta, in un piccolo borggo arroccato tra le montagne, un ansiano falegname di nome Alfredo. Ogni mattina apriva la sua bottega alle prime luci dell'alba e si metteva a lavorare sul suo vecchio banco di legno. Le sue mani callose carezzzzavano il legno come fossero pagine di un libro prezioso, e da quelle tavole nascevano oggetti ricchi di storie, intrise dell'amore con cui li creava.",
    "Nel tempo, la fama del talento di Alfredo si spargette oltre i confini del borgo. Viaggiatori, mercanti e nobili cominciarono a percorrere lunghe distanze per commissionarglivi manufatti unici. Lui, però, non abbandonò mai la sua piccola bottaga, e lavorò con la stessa passione di sempre, intagliando ricordi è speranze nel legno.",
    "Come che te go fato, te desfo", 
    "La cane",
    "Qvesta essere una cassella di testo",
    "Acondroplasiaaa"
]

print('\\n--- VERIFICA QUALI PARAGRAFI VENGONO PROCESSATI ---')
for i, par in enumerate(paragrafi_originali, 1):
    try:
        risultato = has_errors(par)
        status = "PROCESSATO" if risultato else "SALTATO"
        print(f'{i}. "{par[:60]}..." -> {status}')
        if not risultato:
            print(f'   ⚠️  QUESTO PARAGRAFO NON VIENE PROCESSATO MA HA ERRORI!')
    except Exception as e:
        print(f'{i}. "{par[:60]}..." -> ERROR: {e}')

print('\\n--- CONTROLLO SPECIFICO REGEX ---')
import re

# Test delle regex specifiche
_EXTRA_PUNCT_RE = re.compile(
    r"( {2,})|"                         # 1) spazi doppi
    r"([,;:.!?]\\S)|"                    # 2) punteggiatura+lettera
    r"(«\\s)|(\\s»)"                      # 3) spazio dopo « o prima »
)

_HEADING_MISSPELL_RE = re.compile(r"CAPPIT", re.I)

test_cases = [
    "CAPTIOLO 1",
    "vlta",
    "borggo"
]

for case in test_cases:
    punct_match = _EXTRA_PUNCT_RE.search(case)
    heading_match = _HEADING_MISSPELL_RE.search(case)
    print(f'"{case}":')
    print(f'  - EXTRA_PUNCT_RE: {bool(punct_match)}')
    print(f'  - HEADING_MISSPELL_RE: {bool(heading_match)}')
    print(f'  - has_errors total: {has_errors(case)}')
