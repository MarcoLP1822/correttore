import json

# Carica vocabolario
with open('data/vocabolario/nvdb_completo.json', 'r', encoding='utf-8') as f:
    nvdb = json.load(f)

# Parole funzionali comuni che potrebbero mancare
parole_funzionali = [
    'è', 'nel', 'della', 'dello', 'dell', 'nella', 'nello', 'nelle', 'negli',
    'al', 'allo', 'alla', 'ai', 'agli', 'alle',
    'dal', 'dallo', 'dalla', 'dai', 'dagli', 'dalle',
    'sul', 'sullo', 'sulla', 'sui', 'sugli', 'sulle',
    'col', 'coi',
    'c', 'v', 'd', 'l', 's', 't', 'm', 'n',  # lettere singole usate
]

aggiunte = 0
for parola in parole_funzionali:
    if parola not in nvdb['vocabolario']:
        nvdb['vocabolario'][parola] = {
            'livello': 'fondamentale',  # Queste sono tutte fondamentali
            'note': 'Parola funzionale - aggiunta manualmente'
        }
        aggiunte += 1
        print(f"+ Aggiunto: {parola}")

# Aggiorna metadata
nvdb['metadata']['totale_parole'] = len(nvdb['vocabolario'])

# Ricalcola conteggio fondamentali
fondamentali = sum(1 for v in nvdb['vocabolario'].values() if v.get('livello') == 'fondamentale')
nvdb['metadata']['livelli']['fondamentale']['count'] = fondamentali

# Salva
with open('data/vocabolario/nvdb_completo.json', 'w', encoding='utf-8') as f:
    json.dump(nvdb, f, ensure_ascii=False, indent=2)

with open('data/vocabolario/nvdb_parole.json', 'w', encoding='utf-8') as f:
    json.dump(sorted(nvdb['vocabolario'].keys()), f, ensure_ascii=False, indent=2)

with open('data/vocabolario/nvdb_parole.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(sorted(nvdb['vocabolario'].keys())))

print(f"\n✓ Aggiunte {aggiunte} parole funzionali")
print(f"✓ Nuovo totale: {len(nvdb['vocabolario'])} parole")
print(f"✓ Parole fondamentali: {fondamentali}")
