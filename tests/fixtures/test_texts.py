"""
Sample text fixtures per test del correttore.

Contiene testi di esempio con errori tipici per testare le funzionalità.
"""

# Testi con errori di ortografia
SPELLING_ERRORS = {
    "simple": {
        "input": "Questo è un esempio di testo con alcuni errori di ortografia.",
        "expected": "Questo è un esempio di testo con alcuni errori di ortografia."
    },
    "accents": {
        "input": "Perche non vieni con noi stasera? E molto importante.",
        "expected": "Perché non vieni con noi stasera? È molto importante."
    },
    "apostrophes": {
        "input": "Un amica mi ha detto che qual e il problema piu grave.",
        "expected": "Un'amica mi ha detto che qual è il problema più grave."
    },
    "double_consonants": {
        "input": "Oggi vado al colegi per studiare matematica e italiano.",
        "expected": "Oggi vado al collegio per studiare matematica e italiano."
    }
}

# Testi con errori grammaticali
GRAMMAR_ERRORS = {
    "verb_agreement": {
        "input": "I ragazzi va a scuola ogni giorno e studia molto.",
        "expected": "I ragazzi vanno a scuola ogni giorno e studiano molto."
    },
    "article_agreement": {
        "input": "La grande casa è molto bella e il piccola giardino è curato.",
        "expected": "La grande casa è molto bella e il piccolo giardino è curato."
    },
    "prepositions": {
        "input": "Vado a casa con la macchina di mio padre.",
        "expected": "Vado a casa con la macchina di mio padre."
    },
    "auxiliaries": {
        "input": "Marco è andato al cinema e ha guardato un film.",
        "expected": "Marco è andato al cinema e ha guardato un film."
    }
}

# Testi con dialoghi
DIALOGUE_TEXTS = {
    "simple_dialogue": {
        "input": '«Ciao Marco», disse Maria. «Come stai?»\n«Bene grazie», rispose lui.',
        "expected": '«Ciao Marco», disse Maria. «Come stai?»\n«Bene grazie», rispose lui.'
    },
    "mixed_quotes": {
        "input": '"Andiamo al cinema?" chiese Sara. «Si, buona idea!» rispose Luca.',
        "expected": '«Andiamo al cinema?» chiese Sara. «Sì, buona idea!» rispose Luca.'
    },
    "dialogue_with_errors": {
        "input": '«Perche non vieni?» chiese. «Non ho tempo» rispose.',
        "expected": '«Perché non vieni?» chiese. «Non ho tempo» rispose.'
    }
}

# Testi complessi (paragrafi di romanzo)
COMPLEX_TEXTS = {
    "narrative_paragraph": {
        "input": """Marco si svegliò quella matina con una strana sensazione. 
        Il sole filtrava attraverso le persiane creando strisce di luce dorata 
        sul pavimento della sua camera. Aveva fatto un sogno molto vivido, 
        ma non riusciva a ricordare i dettagli. Si alzò lentamente dal letto 
        e si diresse verso la finestra per aprire le tende.""",
        "expected": """Marco si svegliò quella mattina con una strana sensazione. 
        Il sole filtrava attraverso le persiane creando strisce di luce dorata 
        sul pavimento della sua camera. Aveva fatto un sogno molto vivido, 
        ma non riusciva a ricordare i dettagli. Si alzò lentamente dal letto 
        e si diresse verso la finestra per aprire le tende."""
    },
    "descriptive_paragraph": {
        "input": """La vecchia villa si ergeva maestosa sulla collina, 
        circondata da un giardino che un tempo doveva essere stato magnifico. 
        Ora però le siepi erano cresciute selvaggie e i viali erano invasi 
        dalle erbacce. Le finestre, molte delle quali avevano i vetri rotti, 
        guardavano come occhi spenti verso la valle sottostante.""",
        "expected": """La vecchia villa si ergeva maestosa sulla collina, 
        circondata da un giardino che un tempo doveva essere stato magnifico. 
        Ora però le siepi erano cresciute selvagge e i viali erano invasi 
        dalle erbacce. Le finestre, molte delle quali avevano i vetri rotti, 
        guardavano come occhi spenti verso la valle sottostante."""
    }
}

# Testi con caratteri speciali
SPECIAL_CHARACTER_TEXTS = {
    "punctuation": {
        "input": "Questo testo contiene vari segni: virgole, punti, punti e virgola; punti esclamativi! E punti interrogativi?",
        "expected": "Questo testo contiene vari segni: virgole, punti, punti e virgola; punti esclamativi! E punti interrogativi?"
    },
    "dashes_and_quotes": {
        "input": "Il protagonista — un uomo di mezza età — disse: «Non è possibile!»",
        "expected": "Il protagonista — un uomo di mezza età — disse: «Non è possibile!»"
    },
    "numbers_and_dates": {
        "input": "Il 15 marzo 2024, alle ore 14:30, iniziò la riunione importante.",
        "expected": "Il 15 marzo 2024, alle ore 14:30, iniziò la riunione importante."
    }
}

# Casi di test per preservazione formattazione
FORMATTING_TESTS = {
    "italics": {
        "input": "Il libro 'Guerra e Pace' è molto lungo.",
        "formatting": {"'Guerra e Pace'": "italic"},
        "expected": "Il libro 'Guerra e pace' è molto lungo."
    },
    "bold": {
        "input": "ATTENZIONE: questo è molto importante!",
        "formatting": {"ATTENZIONE": "bold"},
        "expected": "ATTENZIONE: questo è molto importante!"
    },
    "mixed_formatting": {
        "input": "Il titolo del libro è 'Il nome della rosa' e l'autore è Umberto Eco.",
        "formatting": {"'Il nome della rosa'": "italic", "Umberto Eco": "bold"},
        "expected": "Il titolo del libro è 'Il nome della rosa' e l'autore è Umberto Eco."
    }
}

# Test per edge cases
EDGE_CASES = {
    "empty_text": {
        "input": "",
        "expected": ""
    },
    "whitespace_only": {
        "input": "   \n\n\t\t   ",
        "expected": ""
    },
    "single_word": {
        "input": "ciao",
        "expected": "ciao"
    },
    "very_long_word": {
        "input": "pneumonoultramicroscopicsilicovolcanoconiosisupercalifragilisticexpialidocious",
        "expected": "pneumonoultramicroscopicsilicovolcanoconiosisupercalifragilisticexpialidocious"
    },
    "mixed_languages": {
        "input": "Questo testo contiene parole in English e français.",
        "expected": "Questo testo contiene parole in English e français."
    }
}

# Testi per test di performance
PERFORMANCE_TESTS = {
    "short_text": "Questo è un testo breve per test di performance.",
    "medium_text": """Questo è un testo di lunghezza media per testare le performance
    del sistema di correzione. Contiene diversi paragrafi e frasi di varia
    lunghezza per simulare un documento reale. Il testo include anche alcuni
    errori intenzionali per verificare che le correzioni funzionino correttamente
    anche quando il sistema è sotto carico.""",
    "long_text": """Questo è un testo molto lungo per testare le performance del sistema
    con documenti di grandi dimensioni. """ * 100  # Ripete 100 volte
}

# Testi problematici che in passato hanno causato errori
PROBLEMATIC_TEXTS = {
    "truncation_prone": {
        "input": """Questo è un paragrafo che storicamente ha causato problemi
        di truncation durante la correzione. Il testo continua con molte frasi
        e dettagli che devono essere preservati integralmente per evitare la
        perdita di contenuto importante per la comprensione del contesto.""",
        "issues": ["truncation", "content_loss"]
    },
    "duplication_prone": {
        "input": "Marco andò a casa. Maria rimase in ufficio. Carlo partì per il viaggio.",
        "issues": ["duplication", "repetition"]
    },
    "formatting_loss": {
        "input": '«Questo dialogo», disse Marco, «deve mantenere la formattazione.»',
        "issues": ["formatting_loss", "quote_corruption"]
    }
}

# Dizionario master con tutti i test
ALL_TEST_TEXTS = {
    "spelling": SPELLING_ERRORS,
    "grammar": GRAMMAR_ERRORS,
    "dialogues": DIALOGUE_TEXTS,
    "complex": COMPLEX_TEXTS,
    "special_chars": SPECIAL_CHARACTER_TEXTS,
    "formatting": FORMATTING_TESTS,
    "edge_cases": EDGE_CASES,
    "performance": PERFORMANCE_TESTS,
    "problematic": PROBLEMATIC_TEXTS
}


def get_test_texts(category=None):
    """
    Restituisce i testi di test per una categoria specifica.
    
    Args:
        category: Categoria di test ("spelling", "grammar", etc.)
                 Se None, restituisce tutti i test.
    
    Returns:
        dict: Dizionario con i testi di test
    """
    if category is None:
        return ALL_TEST_TEXTS
    
    return ALL_TEST_TEXTS.get(category, {})


def get_random_test_text(category=None, seed=None):
    """
    Restituisce un testo di test casuale.
    
    Args:
        category: Categoria specifica o None per tutte
        seed: Seed per riproducibilità
    
    Returns:
        tuple: (input_text, expected_output, metadata)
    """
    import random
    
    if seed:
        random.seed(seed)
    
    texts = get_test_texts(category)
    
    # Appiattisci la struttura per selezione casuale
    all_tests = []
    for cat, tests in texts.items():
        for test_name, test_data in tests.items():
            if isinstance(test_data, dict) and 'input' in test_data:
                all_tests.append((
                    test_data['input'],
                    test_data.get('expected', test_data['input']),
                    {'category': cat, 'name': test_name}
                ))
    
    if not all_tests:
        return "", "", {}
    
    return random.choice(all_tests)


if __name__ == "__main__":
    # Test del modulo fixtures
    print("=== TEST FIXTURES MODULE ===\n")
    
    # Mostra statistiche
    total_tests = 0
    for category, tests in ALL_TEST_TEXTS.items():
        count = len(tests)
        total_tests += count
        print(f"{category.upper()}: {count} test cases")
    
    print(f"\nTOTALE: {total_tests} test cases disponibili")
    
    # Mostra esempi casuali
    print("\n=== ESEMPI CASUALI ===")
    for i in range(3):
        input_text, expected, metadata = get_random_test_text(seed=i)
        print(f"\nEsempio {i+1} ({metadata['category']}/{metadata['name']}):")
        print(f"Input: {input_text[:100]}{'...' if len(input_text) > 100 else ''}")
        print(f"Expected: {expected[:100]}{'...' if len(expected) > 100 else ''}")
