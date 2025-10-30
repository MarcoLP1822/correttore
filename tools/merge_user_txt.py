import json
import re

# Carica il mio vocabolario attuale
with open('data/vocabolario/nvdb_parole.json', 'r', encoding='utf-8') as f:
    mio_vocabolario = set(json.load(f))

print(f"Parole nel mio vocabolario: {len(mio_vocabolario)}")

# Leggi il file TXT dell'utente
with open('correttore files/nuovovocabolariodibase.txt', 'r', encoding='utf-8') as f:
    testo_utente = f.read()

# Estrai tutti i lemmi dal testo dell'utente
# Pattern: cerca parole prima di indicatori grammaticali o virgole
# Esempi: "abbaiare v.intr.", "casa s.f.", "andare v.tr."
pattern = r'\b([a-zàèéìòù]+(?:\'[a-zàèéìòù]+)?)\s+(?:v\.|s\.|agg\.|avv\.|prep\.|pron\.|art\.|cong\.|inter\.|p\.)'

lemmi_utente = set(re.findall(pattern, testo_utente.lower()))

# Aggiungi anche pattern per lemmi standalone con "a s.f." tipo formato
pattern2 = r'^([a-zàèéìòù]+(?:\'[a-zàèéìòù]+)?)\s+(?:s\.|agg|avv|prep|pron|art|cong|inter|v\.)'
lemmi_utente.update(re.findall(pattern2, testo_utente.lower(), re.MULTILINE))

print(f"Lemmi nel TXT dell'utente: {len(lemmi_utente)}")

# Trova quelli mancanti
mancanti = lemmi_utente - mio_vocabolario

print(f"\nParole mancanti da aggiungere: {len(mancanti)}")

if mancanti:
    print(f"\nPrime 50 parole mancanti:")
    for word in sorted(mancanti)[:50]:
        print(f"  {word}")
    
    # Carica JSON completo
    with open('data/vocabolario/nvdb_completo.json', 'r', encoding='utf-8') as f:
        nvdb_completo = json.load(f)
    
    # Aggiungi le parole mancanti
    for word in mancanti:
        if word not in nvdb_completo['vocabolario']:
            nvdb_completo['vocabolario'][word] = {
                'livello': None,
                'note': 'Aggiunto da TXT utente'
            }
    
    # Aggiorna metadata
    nvdb_completo['metadata']['totale_parole'] = len(nvdb_completo['vocabolario'])
    
    # Salva JSON completo
    with open('data/vocabolario/nvdb_completo.json', 'w', encoding='utf-8') as f:
        json.dump(nvdb_completo, f, ensure_ascii=False, indent=2)
    
    # Salva JSON semplificato
    parole_ordinate = sorted(nvdb_completo['vocabolario'].keys())
    with open('data/vocabolario/nvdb_parole.json', 'w', encoding='utf-8') as f:
        json.dump(parole_ordinate, f, ensure_ascii=False, indent=2)
    
    # Salva TXT
    with open('data/vocabolario/nvdb_parole.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(parole_ordinate))
    
    print(f"\n✓ Aggiunte {len(mancanti)} parole mancanti")
    print(f"✓ Nuovo totale: {len(nvdb_completo['vocabolario'])} parole")
else:
    print("\n✓ Nessuna parola mancante, il vocabolario è già completo!")
