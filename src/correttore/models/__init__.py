"""
Modelli di dati per il sistema di correzione.

Questo pacchetto contiene tutti i modelli di dati utilizzati dal sistema,
inclusi i modelli per il tracking delle correzioni e le statistiche.
"""

from .correction_tracking import (
    CorrectionCategory,
    CorrectionSource,
    CorrectionRecord,
    CorrectionStatistics,
)

__all__ = [
    "CorrectionCategory",
    "CorrectionSource",
    "CorrectionRecord",
    "CorrectionStatistics",
]
