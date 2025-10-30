"""
Collector centralizzato per le correzioni.

Questo modulo fornisce una classe per raccogliere, organizzare e aggregare
tutte le correzioni identificate dai vari servizi (LanguageTool, OpenAI, ecc.)
per la generazione del report finale.

Author: Sistema di Correzione Avanzato
Date: 24 Ottobre 2025
"""

from collections import defaultdict
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
import json

from ..models import (
    CorrectionRecord,
    CorrectionCategory,
    CorrectionSource,
    CorrectionStatistics,
)


class CorrectionCollector:
    """
    Raccoglie e organizza tutte le correzioni per il report.
    
    Questa classe è il punto centrale per:
    - Raccogliere correzioni da tutti i servizi
    - Organizzare per categoria, parola, posizione
    - Generare statistiche aggregate
    - Esportare dati per il report HTML
    """
    
    def __init__(self):
        """Inizializza il collector con strutture dati vuote."""
        self._corrections: List[CorrectionRecord] = []
        self._corrections_by_id: Dict[str, CorrectionRecord] = {}
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
        
    def start_tracking(self) -> None:
        """Inizia il tracking del tempo di elaborazione."""
        self._start_time = datetime.now()
        
    def stop_tracking(self) -> None:
        """Ferma il tracking del tempo di elaborazione."""
        self._end_time = datetime.now()
        
    def add_correction(self, record: CorrectionRecord) -> None:
        """
        Aggiunge una correzione al collector.
        
        Args:
            record: Record di correzione da aggiungere
        """
        self._corrections.append(record)
        self._corrections_by_id[record.id] = record
        
    def add_corrections(self, records: List[CorrectionRecord]) -> None:
        """
        Aggiunge multiple correzioni al collector.
        
        Args:
            records: Lista di record di correzione
        """
        for record in records:
            self.add_correction(record)
            
    def get_correction_by_id(self, correction_id: str) -> Optional[CorrectionRecord]:
        """
        Recupera una correzione per ID.
        
        Args:
            correction_id: ID della correzione
            
        Returns:
            Record di correzione o None se non trovato
        """
        return self._corrections_by_id.get(correction_id)
        
    def get_all_corrections(self) -> List[CorrectionRecord]:
        """
        Restituisce tutte le correzioni.
        
        Returns:
            Lista di tutti i record di correzione
        """
        return self._corrections.copy()
        
    def get_by_category(self, category: CorrectionCategory) -> List[CorrectionRecord]:
        """
        Filtra le correzioni per categoria.
        
        Args:
            category: Categoria da filtrare
            
        Returns:
            Lista di correzioni della categoria specificata
        """
        return [c for c in self._corrections if c.category == category]
        
    def get_by_source(self, source: CorrectionSource) -> List[CorrectionRecord]:
        """
        Filtra le correzioni per fonte.
        
        Args:
            source: Fonte da filtrare
            
        Returns:
            Lista di correzioni dalla fonte specificata
        """
        return [c for c in self._corrections if c.source == source]
        
    def get_by_word(self) -> Dict[str, List[CorrectionRecord]]:
        """
        Raggruppa le correzioni per parola originale.
        
        Returns:
            Dizionario parola -> lista di correzioni
        """
        by_word = defaultdict(list)
        for correction in self._corrections:
            word = correction.original_text.lower().strip()
            by_word[word].append(correction)
        return dict(by_word)
        
    def get_by_category_grouped(self) -> Dict[CorrectionCategory, List[CorrectionRecord]]:
        """
        Raggruppa tutte le correzioni per categoria.
        
        Returns:
            Dizionario categoria -> lista di correzioni
        """
        by_category = defaultdict(list)
        for correction in self._corrections:
            by_category[correction.category].append(correction)
        return dict(by_category)
        
    def get_error_corrections(self) -> List[CorrectionRecord]:
        """
        Restituisce solo le correzioni di tipo errore.
        
        Returns:
            Lista di correzioni che sono errori veri
        """
        return [
            c for c in self._corrections 
            if c.category.is_error_category
        ]
        
    def get_info_corrections(self) -> List[CorrectionRecord]:
        """
        Restituisce solo le segnalazioni informative.
        
        Returns:
            Lista di correzioni che sono segnalazioni informative
        """
        return [
            c for c in self._corrections 
            if not c.category.is_error_category
        ]
        
    def get_applied_corrections(self) -> List[CorrectionRecord]:
        """
        Restituisce le correzioni che sono state applicate.
        
        Returns:
            Lista di correzioni applicate
        """
        return [c for c in self._corrections if c.is_applied]
        
    def get_ignored_corrections(self) -> List[CorrectionRecord]:
        """
        Restituisce le correzioni che sono state ignorate.
        
        Returns:
            Lista di correzioni ignorate
        """
        return [c for c in self._corrections if c.is_ignored]
        
    def get_unique_words(self) -> Set[str]:
        """
        Restituisce l'insieme di parole uniche con correzioni.
        
        Returns:
            Set di parole uniche (lowercase)
        """
        return {
            c.original_text.lower().strip() 
            for c in self._corrections
        }
        
    def get_statistics(self) -> CorrectionStatistics:
        """
        Genera statistiche aggregate su tutte le correzioni.
        
        Returns:
            Oggetto CorrectionStatistics con i dati aggregati
        """
        # Conteggi per categoria
        by_category = defaultdict(int)
        for correction in self._corrections:
            by_category[correction.category] += 1
            
        # Conteggi per fonte
        by_source = defaultdict(int)
        for correction in self._corrections:
            by_source[correction.source] += 1
            
        # Calcola tempo di elaborazione
        processing_time = 0.0
        if self._start_time and self._end_time:
            processing_time = (self._end_time - self._start_time).total_seconds()
            
        # Crea statistiche
        stats = CorrectionStatistics(
            total_corrections=len(self._corrections),
            total_words_checked=0,  # Da calcolare esternamente
            total_contexts=len(self._corrections),  # Ogni correzione ha un contesto
            processing_time=processing_time,
            by_category=dict(by_category),
            by_source=dict(by_source),
            unique_words=len(self.get_unique_words()),
            applied_corrections=len(self.get_applied_corrections()),
            ignored_corrections=len(self.get_ignored_corrections()),
        )
        
        return stats
        
    def get_category_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Genera un sommario per categoria con conteggi e statistiche.
        
        Returns:
            Dizionario con info per ogni categoria presente
        """
        summary = {}
        
        for category in CorrectionCategory:
            corrections = self.get_by_category(category)
            if not corrections:
                continue
                
            # Conta parole e contesti unici
            unique_words = {c.original_text.lower() for c in corrections}
            
            summary[category.value] = {
                "category": category.value,
                "display_name": category.display_name,
                "color": category.color_code,
                "is_error": category.is_error_category,
                "total_corrections": len(corrections),
                "unique_words": len(unique_words),
                "contexts": len(corrections),
            }
            
        return summary
        
    def export_for_report(self) -> Dict[str, Any]:
        """
        Esporta tutti i dati in formato strutturato per il report HTML.
        
        Returns:
            Dizionario con tutti i dati necessari per generare il report
        """
        # Ottieni statistiche
        stats = self.get_statistics()
        
        # Raggruppa per categoria
        by_category_grouped = {}
        for category, corrections in self.get_by_category_grouped().items():
            # Per ogni categoria, raggruppa per parola
            by_word = defaultdict(list)
            for correction in corrections:
                word = correction.original_text.lower().strip()
                by_word[word].append(correction.to_dict())
                
            by_category_grouped[category.value] = {
                "display_name": category.display_name,
                "color": category.color_code,
                "is_error": category.is_error_category,
                "by_word": dict(by_word),
                "total": len(corrections),
            }
            
        # Costruisci export completo
        export_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "processing_time": stats.processing_time,
                "total_corrections": stats.total_corrections,
                "total_words_checked": stats.total_words_checked,
                "unique_words": stats.unique_words,
            },
            "statistics": stats.to_dict(),
            "category_summary": self.get_category_summary(),
            "corrections_by_category": by_category_grouped,
            "all_corrections": [c.to_dict() for c in self._corrections],
        }
        
        return export_data
        
    def export_to_json(self, filepath: str, pretty: bool = True) -> None:
        """
        Esporta i dati in un file JSON.
        
        Args:
            filepath: Percorso del file di output
            pretty: Se True, formatta il JSON con indentazione
        """
        data = self.export_for_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)
                
    def clear(self) -> None:
        """Pulisce tutte le correzioni raccolte."""
        self._corrections.clear()
        self._corrections_by_id.clear()
        self._start_time = None
        self._end_time = None
        
    def update_correction(self, 
                         correction_id: str, 
                         is_applied: Optional[bool] = None,
                         is_ignored: Optional[bool] = None,
                         user_feedback: Optional[str] = None) -> bool:
        """
        Aggiorna lo stato di una correzione.
        
        Args:
            correction_id: ID della correzione da aggiornare
            is_applied: Se True, marca come applicata
            is_ignored: Se True, marca come ignorata
            user_feedback: Feedback dell'utente
            
        Returns:
            True se l'aggiornamento è riuscito, False altrimenti
        """
        correction = self.get_correction_by_id(correction_id)
        if not correction:
            return False
            
        if is_applied is not None:
            correction.is_applied = is_applied
        if is_ignored is not None:
            correction.is_ignored = is_ignored
        if user_feedback is not None:
            correction.user_feedback = user_feedback
            
        return True
        
    def __len__(self) -> int:
        """Restituisce il numero totale di correzioni."""
        return len(self._corrections)
        
    def __repr__(self) -> str:
        """Rappresentazione stringa del collector."""
        return (
            f"CorrectionCollector("
            f"corrections={len(self._corrections)}, "
            f"categories={len(self.get_category_summary())}, "
            f"unique_words={len(self.get_unique_words())})"
        )
