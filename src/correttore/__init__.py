"""
Correttore - Enterprise Italian Text Correction System
======================================================

A state-of-the-art text correction system with:
- AI-powered corrections using OpenAI GPT
- Grammar checking with LanguageTool
- Readability analysis (Gulpease index)
- Historical Italian text support
- Enterprise-grade quality assurance

Usage:
    from correttore import Corrector
    
    corrector = Corrector()
    result = corrector.process_document("path/to/document.docx")
"""

__version__ = '2.0.0'
__author__ = 'Marco LP'

# Type hints for lazy-loaded modules (helps IDEs and type checkers)
# These will be dynamically imported via __getattr__
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import only for type checking, not at runtime
    from correttore.core.correction_engine import CorrectionEngine
    from correttore.core.document_handler import DocumentHandler
    from correttore.interfaces.cli import CorrettoreCLI

# Lazy imports to avoid circular dependencies and missing optional deps
__all__ = [
    'CorrectionEngine',
    'DocumentHandler', 
    'CorrettoreCLI',
    '__version__',
]

def __getattr__(name):
    """Lazy loading of heavy modules"""
    if name == 'CorrectionEngine':
        from correttore.core.correction_engine import CorrectionEngine
        return CorrectionEngine
    elif name == 'DocumentHandler':
        from correttore.core.document_handler import DocumentHandler
        return DocumentHandler
    elif name == 'CorrettoreCLI':
        from correttore.interfaces.cli import CorrettoreCLI
        return CorrettoreCLI
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
