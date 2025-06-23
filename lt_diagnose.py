# lt_diagnose.py
import os, json, pprint, textwrap, shutil, tempfile, subprocess
import language_tool_python as lt
import requests, psutil         # psutil è già dipendenza di language_tool_python

# ───────────────────────────────────────────────────────────────────────────────
# 1) mostriamo dove LT *pensa* di trovare i .jar
# ───────────────────────────────────────────────────────────────────────────────
print("\n### PATH dei .jar (da env):")
print("LTP_JAR_DIR_PATH =", os.getenv("LTP_JAR_DIR_PATH") or "(non impostata)")

# ───────────────────────────────────────────────────────────────────────────────
# 2) avviamo una istanza locale (LanguageTool scaricherà automaticamente
#    la **distribuzione completa** se nella cartella indicata non la trova).
# ───────────────────────────────────────────────────────────────────────────────
tool = lt.LanguageTool('it-IT')       # ‘it’ va bene, ma essere espliciti non guasta
print("\n### Endpoint HTTP interno:", tool._url)

# 3) leggiamo il PID del processo Java per curiosità
java_pid = getattr(tool, "_server_pid", None)

if java_pid and java_pid > 0:
    print(f"### PID processo Java    : {java_pid} (vivo = {psutil.pid_exists(java_pid)})")
else:
    print("### PID processo Java    : (nessun PID registrato)")

# 4) interroghiamo direttamente l’endpoint “/v2/info” che elenca tutte le regole
info_url = tool._url.rsplit("/v2/", 1)[0] + "/v2/info"
info     = requests.get(info_url, params={"language": "it"}).json()

all_rules      = [r["id"] for r in info.get("rules", [])]
enabled_rules  = [r["id"] for r in info.get("rules", []) if not r.get("defaultOff")]

print("\n### Totale regole viste  :", len(all_rules))
print("### Regole abilitate ora  :", len(enabled_rules))
print("   (prime 20) →", enabled_rules[:20])

# ───────────────────────────────────────────────────────────────────────────────
# 5) facciamo un test rapido di correzione
# ───────────────────────────────────────────────────────────────────────────────
bad = "quando gli e l'hanno diagnostico"
matches = tool.check(bad)
print("\n### Match per la frase di test:")
for m in matches:
    print(f" {m.ruleId:<20} » {m.message}  |  Suggerimenti: {m.replacements}")

tool.close()
