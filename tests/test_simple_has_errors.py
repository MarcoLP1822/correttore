import os
import sys
os.chdir('C:\\Users\\Youcanprint1\\Desktop\\AI\\Correttore\\src\\core')
sys.path.insert(0, '.')

from precheck import has_errors

print('=== TEST FUNZIONE has_errors ===')

# Errori che NON sono stati corretti
errori_non_corretti = [
    "vlta",
    "borggo", 
    "ansiano",
    "carezzzzavano",
    "Acondroplasiaaa",
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
    try:
        risultato = has_errors(errore)
        status = "RILEVATO" if risultato else "NON RILEVATO"
        print(f'{i:2d}. "{errore}" -> {status}')
    except Exception as e:
        print(f'{i:2d}. "{errore}" -> ERROR: {e}')

print('\n--- ERRORI CORRETTI (per confronto) ---')
for i, errore in enumerate(errori_corretti, 1):
    try:
        risultato = has_errors(errore)
        status = "RILEVATO" if risultato else "NON RILEVATO"
        print(f'{i:2d}. "{errore}" -> {status}')
    except Exception as e:
        print(f'{i:2d}. "{errore}" -> ERROR: {e}')
