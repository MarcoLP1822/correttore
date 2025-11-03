"""
Modello dati per i risultati dell'analisi qualità documento.

Questo modulo definisce le strutture dati per tracciare i risultati dell'analisi
post-correzione, che identifica problemi residui nel documento corretto senza
applicare modifiche.

Author: Sistema di Correzione Avanzato
Date: 31 Ottobre 2025
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .correction_tracking import CorrectionCategory, CorrectionRecord


@dataclass
class DocumentAnalysisResult:
    """
    Risultato dell'analisi qualità su un documento.
    
    Contiene tutte le informazioni raccolte durante l'analisi post-correzione:
    - Errori residui identificati
    - Metriche di leggibilità
    - Categorie speciali (lingue straniere, nomi propri, parole sensibili)
    - Statistiche del documento
    
    Attributes:
        success: Indica se l'analisi è stata completata con successo
        document_path: Path del documento analizzato
        analysis_timestamp: Timestamp dell'analisi
        total_errors: Numero totale di errori residui identificati
        errors_by_category: Dizionario con conteggio errori per categoria
        readability_score: Punteggio di leggibilità (es. Gulpease)
        readability_level: Livello di difficoltà del testo (es. "Facile", "Medio")
        sentences_analysis: Lista di analisi per singola frase
        foreign_words: Lista di parole in lingue straniere identificate
        proper_nouns: Lista di nomi propri e sigle identificati
        sensitive_words: Lista di parole potenzialmente sensibili
        total_words: Numero totale di parole nel documento
        total_paragraphs: Numero totale di paragrafi
        processing_time: Tempo impiegato per l'analisi (secondi)
        report_path: Path del report HTML generato (se disponibile)
        error_message: Messaggio di errore se success=False
    """
    
    success: bool
    document_path: Path
    analysis_timestamp: datetime
    
    # Errori residui
    total_errors: int = 0
    errors_by_category: Dict[CorrectionCategory, int] = field(default_factory=dict)
    
    # Leggibilità
    readability_score: float = 0.0
    readability_level: str = "unknown"
    sentences_analysis: List[Any] = field(default_factory=list)  # List[SentenceReadability]
    
    # Categorie speciali
    foreign_words: List[CorrectionRecord] = field(default_factory=list)
    proper_nouns: List[CorrectionRecord] = field(default_factory=list)
    sensitive_words: List[CorrectionRecord] = field(default_factory=list)
    
    # Statistiche
    total_words: int = 0
    total_paragraphs: int = 0
    processing_time: float = 0.0
    
    # Report
    report_path: Optional[Path] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte il risultato in un dizionario serializzabile.
        
        Returns:
            Dizionario con tutti i campi del risultato
        """
        return {
            "success": self.success,
            "document_path": str(self.document_path),
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "total_errors": self.total_errors,
            "errors_by_category": {
                category.value: count 
                for category, count in self.errors_by_category.items()
            },
            "readability_score": self.readability_score,
            "readability_level": self.readability_level,
            "foreign_words_count": len(self.foreign_words),
            "proper_nouns_count": len(self.proper_nouns),
            "sensitive_words_count": len(self.sensitive_words),
            "total_words": self.total_words,
            "total_paragraphs": self.total_paragraphs,
            "processing_time": self.processing_time,
            "report_path": str(self.report_path) if self.report_path else None,
            "error_message": self.error_message,
        }
    
    def get_summary(self) -> str:
        """
        Genera un riepilogo testuale conciso del risultato.
        
        Returns:
            Stringa con il riepilogo dell'analisi
        """
        if not self.success:
            return f"❌ Analisi fallita: {self.error_message}"
        
        lines = [
            f"✅ Analisi completata in {self.processing_time:.2f}s",
            f"📄 Documento: {self.document_path.name}",
            f"📊 Statistiche: {self.total_words} parole, {self.total_paragraphs} paragrafi",
            f"❌ Errori residui: {self.total_errors}",
            f"📈 Leggibilità: {self.readability_score:.1f} ({self.readability_level})",
        ]
        
        if self.foreign_words:
            lines.append(f"🌐 Parole straniere: {len(self.foreign_words)}")
        
        if self.proper_nouns:
            lines.append(f"👤 Nomi propri: {len(self.proper_nouns)}")
        
        if self.sensitive_words:
            lines.append(f"😳 Parole sensibili: {len(self.sensitive_words)}")
        
        if self.report_path:
            lines.append(f"📋 Report: {self.report_path}")
        
        return "\n".join(lines)
    
    def get_errors_by_type(self) -> Dict[str, int]:
        """
        Raggruppa gli errori distinguendo tra errori veri e informazioni.
        
        Returns:
            Dizionario con "errors" (errori veri) e "info" (segnalazioni informative)
        """
        errors_count = 0
        info_count = 0
        
        for category, count in self.errors_by_category.items():
            if category.is_error_category:
                errors_count += count
            else:
                info_count += count
        
        return {
            "errors": errors_count,
            "info": info_count,
            "total": errors_count + info_count
        }
    
    def has_critical_issues(self, threshold: int = 10) -> bool:
        """
        Verifica se ci sono problemi critici che richiedono attenzione.
        
        Args:
            threshold: Soglia minima di errori per considerare il documento critico
        
        Returns:
            True se ci sono problemi critici
        """
        error_types = self.get_errors_by_type()
        return error_types["errors"] >= threshold
    
    def get_quality_rating(self) -> str:
        """
        Calcola un rating di qualità basato su errori e leggibilità.
        
        Returns:
            Rating: "Eccellente", "Buona", "Sufficiente", "Scarsa"
        """
        if not self.success:
            return "N/A"
        
        # Calcola score composito
        error_types = self.get_errors_by_type()
        errors_per_100_words = (error_types["errors"] / max(self.total_words, 1)) * 100
        
        # Rating basato su densità errori e leggibilità
        if errors_per_100_words < 0.5 and self.readability_score >= 60:
            return "Eccellente"
        elif errors_per_100_words < 1.5 and self.readability_score >= 50:
            return "Buona"
        elif errors_per_100_words < 3.0 and self.readability_score >= 40:
            return "Sufficiente"
        else:
            return "Scarsa"


@dataclass
class AnalysisConfig:
    """
    Configurazione per il DocumentAnalyzer.
    
    Permette di abilitare/disabilitare componenti specifici dell'analisi.
    
    Attributes:
        enable_languagetool: Abilita analisi grammaticale con LanguageTool
        enable_readability: Abilita analisi di leggibilità
        enable_special_categories: Abilita rilevamento categorie speciali
        generate_report: Genera report HTML al termine dell'analisi
        report_standalone: Report HTML standalone (CSS inline)
    """
    
    enable_languagetool: bool = True
    enable_readability: bool = True
    enable_special_categories: bool = True
    generate_report: bool = True
    report_standalone: bool = True
