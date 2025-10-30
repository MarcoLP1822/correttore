"""
Configurazione comune per tutti i test pytest.

Questo file viene automaticamente caricato da pytest e fornisce:
- Fixtures comuni a tutti i test
- Configurazioni globali
- Hook per personalizzare l'esecuzione dei test
"""

import pytest
import sys
import os
from pathlib import Path

# Aggiungi src al path per gli import
_project_root = Path(__file__).parent
sys.path.insert(0, str(_project_root / "src"))


# =============================================================================
# FIXTURES COMUNI
# =============================================================================

@pytest.fixture
def project_root():
    """Ritorna il path root del progetto."""
    return Path(__file__).parent


@pytest.fixture
def test_data_dir(project_root):
    """Ritorna il path della directory test data."""
    return project_root / "tests" / "fixtures"


@pytest.fixture
def temp_output_dir(tmp_path):
    """Crea una directory temporanea per output di test."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def sample_text():
    """Testo di esempio per i test."""
    return (
        "Il gatto è un animale domestico molto apprezzato. "
        "Molti persone hanno gatti come animali da compagnia. "
        "I gatti sono animali molto indipendenti e affascinanti."
    )


@pytest.fixture
def sample_text_with_errors():
    """Testo con errori intenzionali per i test."""
    return (
        "C'era una vlta un principe che viveva in un castello. "
        "U giorno decise di visitare la bottaga del falegname. "
        "Il falegname alfredo preparò un ottimo sugu per la cena."
    )


# =============================================================================
# MARKERS
# =============================================================================

def pytest_configure(config):
    """Configura markers personalizzati."""
    config.addinivalue_line(
        "markers", "unit: Test unitari per componenti individuali"
    )
    config.addinivalue_line(
        "markers", "integration: Test di integrazione tra componenti"
    )
    config.addinivalue_line(
        "markers", "performance: Test di performance e ottimizzazione"
    )
    config.addinivalue_line(
        "markers", "slow: Test che richiedono più tempo (>1s)"
    )
    config.addinivalue_line(
        "markers", "api: Test che richiedono chiamate API esterne"
    )
    config.addinivalue_line(
        "markers", "requires_openai: Test che richiedono OpenAI API key"
    )
    config.addinivalue_line(
        "markers", "requires_languagetool: Test che richiedono LanguageTool server"
    )


# =============================================================================
# HOOK: SKIP TEST SE MANCANO DIPENDENZE
# =============================================================================

def pytest_runtest_setup(item):
    """
    Hook eseguito prima di ogni test.
    Salta i test che richiedono dipendenze non disponibili.
    """
    # Skip se richiede OpenAI ma non è disponibile
    if "requires_openai" in [mark.name for mark in item.iter_markers()]:
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("Test richiede OPENAI_API_KEY")
    
    # Skip se richiede LanguageTool ma non è disponibile
    if "requires_languagetool" in [mark.name for mark in item.iter_markers()]:
        # Verifica se LanguageTool è raggiungibile
        # TODO: implementare check LanguageTool
        pass


# =============================================================================
# HOOK: REPORT PERSONALIZZATO
# =============================================================================

def pytest_report_header(config):
    """Aggiunge informazioni all'header del report."""
    return [
        f"Project: Correttore Automatico",
        f"Test Root: {_project_root}",
        f"Python: {sys.version.split()[0]}",
    ]


# =============================================================================
# FIXTURES PER MOCK
# =============================================================================

@pytest.fixture
def mock_openai_response():
    """Mock di una risposta OpenAI tipica."""
    return {
        "choices": [
            {
                "message": {
                    "content": "Testo corretto dal mock."
                }
            }
        ],
        "usage": {
            "total_tokens": 100
        }
    }


@pytest.fixture
def mock_languagetool_response():
    """Mock di una risposta LanguageTool tipica."""
    return {
        "matches": [
            {
                "message": "Possibile errore di ortografia",
                "shortMessage": "Errore ortografia",
                "offset": 10,
                "length": 5,
                "replacements": [
                    {"value": "correzione1"},
                    {"value": "correzione2"}
                ],
                "rule": {
                    "id": "RULE_ID",
                    "category": {
                        "id": "TYPOS",
                        "name": "Errori di ortografia"
                    }
                }
            }
        ]
    }


# =============================================================================
# CLEANUP
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_files(project_root):
    """Pulisce file temporanei creati durante i test."""
    yield
    
    # Cleanup dopo ogni test
    test_output = project_root / "test_output"
    if test_output.exists():
        # Non rimuoviamo la directory, solo i file vecchi
        # per evitare di cancellare output utili per debug
        pass
