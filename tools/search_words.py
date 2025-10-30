import pdfplumber

pdf = pdfplumber.open(r'correttore files\nuovovocabolariodibase.pdf')

search_words = ['avere', 'essere', 'andare', 'potere', 'volere', 'sapere']

for i, page in enumerate(pdf.pages, 1):
    text = page.extract_text()
    for word in search_words:
        if word in text.lower():
            print(f"Pagina {i}: trovato '{word}'")
            # Mostra contesto
            idx = text.lower().find(word)
            context = text[max(0, idx-50):idx+50]
            print(f"  Contesto: ...{context}...")
            print()

pdf.close()
