import requests, json, language_tool_python as lt, pprint

tool = lt.LanguageTool('it')        # avvia il server embedded
base = tool._url.rsplit("/v2/", 1)[0]      # esempio: http://localhost:8081
info_url = f"{base}/v2/info"

# 1) chiedi esplicitamente le regole
params = {"language": "it", "withRules": "1"}      # << flag decisivo
resp   = requests.get(info_url, params=params, timeout=15)
data   = resp.json()

# 2) se ancora non ci sono, stampa l'intero JSON per capire cosa arriva
if "rules" not in data:
    print("### JSON ricevuto (niente chiave 'rules'):")
    pprint.pprint(data)
    raise SystemExit("\nLa tua istanza LT non fornisce l'elenco delle regole "
                     "(jar lite o flag disabilitato).")

print(f"Totale regole lette: {len(data['rules'])}\n")

for r in sorted(data["rules"], key=lambda x: x["id"]):
    print(f"{r['id']:<30}  →  {r['description']}")
