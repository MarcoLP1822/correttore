import json

nvdb = json.load(open('data/vocabolario/nvdb_parole.json', 'r', encoding='utf-8'))
verbi = ['essere', 'avere', 'fare', 'dire', 'andare', 'potere', 'volere', 'sapere']

print('Verifica verbi comuni:')
for v in verbi:
    status = "✓ presente" if v in nvdb else "✗ MANCANTE"
    print(f'  {v}: {status}')

print(f'\nTotale parole: {len(nvdb)}')
