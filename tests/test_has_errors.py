import sys
sys.path.append('C:\\Users\\Youcanprint1\\Desktop\\AI\\Correttore\\src\\core')

from precheck import has_errors

print('=== TEST FUNZIONE has_errors ===')

# Errori che NON sono stati corretti
errori_non_corretti = [
    "vlta",
    "borggo", 
    "ansiano",
    "carezzzzavano",
    "Acondroplasiaaa",
    "C'era una vlta, in un piccolo borggo arroccato",
    "un ansiano falegname",
    "carezzzzavano il legno",
    "questa essere una",
    "te desfo",
    "lu sugu te lu calzone"
]

# Errori che SONO stati corretti
errori_corretti = [
    "CAPTIOLO",
    "bottaga", 
    "Qvesta",
    "cassella",
    "La cane"
]

print('\n--- ERRORI NON CORRETTI (dovrebbero return True) ---')
for i, errore in enumerate(errori_non_corretti, 1):
    risultato = has_errors(errore)
    status = "✅ RILEVATO" if risultato else "❌ NON RILEVATO"
    print(f'{i:2d}. "{errore}" → {status}')

print('\n--- ERRORI CORRETTI (per confronto) ---')
for i, errore in enumerate(errori_corretti, 1):
    risultato = has_errors(errore)
    status = "✅ RILEVATO" if risultato else "❌ NON RILEVATO"
    print(f'{i:2d}. "{errore}" → {status}')

print('\n--- TEST PARAGRAFI COMPLETI ---')
paragrafi_test = [
    "C'era una vlta, in un piccolo borggo arroccato tra le montagne, un ansiano falegname",
    "CAPTIOLO 1",
    "Qvesta essere una cassella di testo",
    "Come che te go fato, te desfo"
]

for i, par in enumerate(paragrafi_test, 1):
    risultato = has_errors(par)
    status = "✅ RILEVATO" if risultato else "❌ NON RILEVATO"
    print(f'{i}. "{par[:50]}..." → {status}')
