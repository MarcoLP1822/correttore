#!/usr/bin/env python3
"""
Test per l'endpoint API di analisi leggibilità.
Verifica che il server web risponda correttamente all'analisi.
"""

import requests
import time
from pathlib import Path


def test_readability_api():
    """Testa l'API di analisi leggibilità."""
    
    # URL dell'API
    api_url = "http://localhost:5000/api/readability"
    
    # File di test
    test_file = Path("test_output/documento_test_leggibilita.docx")
    
    if not test_file.exists():
        print("❌ File di test non trovato. Crealo prima con:")
        print("   python -c \"from docx import Document; d=Document(); d.save('test_output/documento_test_leggibilita.docx')\"")
        return
    
    print("🧪 Test API Analisi Leggibilità")
    print("=" * 60)
    print(f"📄 File: {test_file.name}")
    print(f"🌐 URL: {api_url}")
    print()
    
    # Verifica che il server sia attivo
    try:
        response = requests.get("http://localhost:5000", timeout=2)
        print("✅ Server attivo")
    except requests.exceptions.RequestException:
        print("❌ Server non raggiungibile. Avvialo con:")
        print("   python -m src.interfaces.web_interface")
        return
    
    print()
    print("📤 Invio richiesta...")
    
    # Invia il file per l'analisi
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            response = requests.post(api_url, files=files, timeout=10)
        
        print(f"📥 Risposta ricevuta: HTTP {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("✅ Analisi completata con successo!")
                print()
                
                stats = result['readability']
                print("📊 RISULTATI:")
                print("=" * 60)
                print(f"   Indice Gulpease:     {stats['gulpease']:.2f}/100")
                print(f"   Parole:              {stats['words']}")
                print(f"   Frasi:               {stats['sentences']}")
                print(f"   Lungh. media parola: {stats['avg_word_length']:.2f} lettere")
                print(f"   Lungh. media frase:  {stats['avg_sentence_length']:.2f} parole")
                print()
                print("👥 Difficoltà per livello:")
                print(f"   📚 Licenza elementare: {stats['difficulty']['licenza_elementare']}")
                print(f"   🎓 Licenza media:      {stats['difficulty']['licenza_media']}")
                print(f"   🎯 Diploma superiore:  {stats['difficulty']['diploma_superiore']}")
                print("=" * 60)
                print()
                print("✅ Test completato con successo!")
            else:
                print(f"❌ Errore nell'analisi: {result.get('error', 'Errore sconosciuto')}")
        else:
            print(f"❌ Errore HTTP: {response.status_code}")
            try:
                error = response.json()
                print(f"   Dettagli: {error.get('error', 'Nessun dettaglio')}")
            except:
                print(f"   Risposta: {response.text[:200]}")
    
    except requests.exceptions.Timeout:
        print("❌ Timeout: il server non ha risposto in tempo")
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore nella richiesta: {e}")
    except Exception as e:
        print(f"❌ Errore imprevisto: {e}")


def test_with_curl():
    """Mostra il comando curl equivalente."""
    print()
    print("💡 Comando curl equivalente:")
    print("-" * 60)
    print("curl -X POST \\")
    print("  -F 'file=@test_output/documento_test_leggibilita.docx' \\")
    print("  http://localhost:5000/api/readability")
    print("-" * 60)


if __name__ == "__main__":
    test_readability_api()
    test_with_curl()
