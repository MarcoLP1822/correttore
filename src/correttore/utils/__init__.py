"""Correttore - Italian Text Correction System"""

from .html_report_generator import (
    HTMLReportGenerator,
    generate_orthography_report,
    generate_analysis_report
)

__all__ = [
    "HTMLReportGenerator",
    "generate_orthography_report",
    "generate_analysis_report"
]
