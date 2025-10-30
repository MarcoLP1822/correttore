import json

# Carica vocabolario
with open('data/vocabolario/nvdb_completo.json', 'r', encoding='utf-8') as f:
    nvdb = json.load(f)

# Verbi comuni che potrebbero mancare
verbi_comuni = [
    'essere', 'avere', 'andare', 'potere', 'volere', 'sapere', 
    'venire', 'dovere', 'uscire', 'morire', 'nascere', 'vivere',
    'credere', 'pensare', 'parlare', 'chiamare', 'trovare', 'lasciare',
    'mettere', 'prendere', 'tenere', 'portare', 'guardare', 'passare',
    'cadere', 'rimanere', 'sedere', 'salire', 'scendere', 'correre'
]

aggiunti = 0
for verbo in verbi_comuni:
    if verbo not in nvdb['vocabolario']:
        nvdb['vocabolario'][verbo] = {
            'livello': None,
            'note': 'Aggiunto manualmente - verbo comune fondamentale'
        }
        aggiunti += 1
        print(f"+ Aggiunto: {verbo}")

# Aggiorna totale
nvdb['metadata']['totale_parole'] = len(nvdb['vocabolario'])

# Salva JSON completo
with open('data/vocabolario/nvdb_completo.json', 'w', encoding='utf-8') as f:
    json.dump(nvdb, f, ensure_ascii=False, indent=2)

# Salva JSON semplificato
with open('data/vocabolario/nvdb_parole.json', 'w', encoding='utf-8') as f:
    json.dump(sorted(nvdb['vocabolario'].keys()), f, ensure_ascii=False, indent=2)

# Salva TXT
with open('data/vocabolario/nvdb_parole.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(sorted(nvdb['vocabolario'].keys())))

print(f"\n✓ Aggiunti {aggiunti} verbi")
print(f"✓ Totale parole nel vocabolario: {len(nvdb['vocabolario'])}")
