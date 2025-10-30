"""
Modello dati per il tracking e la classificazione delle correzioni.

Questo modulo definisce le strutture dati per tracciare tutte le correzioni
identificate dal sistema, classificandole in categorie compatibili con il
sistema di report avanzato simile a Corrige.it.

Author: Sistema di Correzione Avanzato
Date: 24 Ottobre 2025
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4


class CorrectionCategory(Enum):
    """
    Categorie di correzione basate sul sistema Corrige.it.
    
    Divise in due macro-categorie:
    1. Segnalazioni di correzione (errori veri)
    2. Segnalazioni d'informazione (non errori)
    """
    
    # ═══════════════════════════════════════════════════════════
    # SEGNALAZIONI DI CORREZIONE (Errori veri)
    # ═══════════════════════════════════════════════════════════
    
    ERRORI_RICONOSCIUTI = "X"
    """Errori ortografici/grammaticali certi (icona: X)"""
    
    SCONOSCIUTE = "?"
    """Parole non presenti nel database (icona: ?)"""
    
    SOSPETTE = "!"
    """Parole corrette ma contestualmente sospette (icona: !)"""
    
    MIGLIORABILI = "æ"
    """Espressioni migliorabili per stile/professionalità (icona: æ)"""
    
    PUNTEGGIATURA = ";"
    """Errori di punteggiatura e convenzioni tipografiche (icona: ;)"""
    
    # ═══════════════════════════════════════════════════════════
    # SEGNALAZIONI D'INFORMAZIONE (Non errori)
    # ═══════════════════════════════════════════════════════════
    
    IMBARAZZANTI = "¿"
    """Parole valide ma potenzialmente imbarazzanti/volgari (icona: ¿)"""
    
    VARIANTI = "≈"
    """Forme alternative accettabili, varianti regionali (icona: ≈)"""
    
    NOMI_SIGLE = "N"
    """Nomi propri, sigle, acronimi riconosciuti (icona: N)"""
    
    LINGUE = "L"
    """Parole in lingue straniere riconosciute (icona: L)"""
    
    CON_INFO = "ⓘ"
    """Segnalazioni con informazioni aggiuntive (icona: ⓘ)"""
    
    LINK = "@"
    """Link e riferimenti web (icona: @)"""
    
    @property
    def is_error_category(self) -> bool:
        """Verifica se la categoria è un errore vero o solo informazione."""
        error_categories = {
            CorrectionCategory.ERRORI_RICONOSCIUTI,
            CorrectionCategory.SCONOSCIUTE,
            CorrectionCategory.SOSPETTE,
            CorrectionCategory.MIGLIORABILI,
            CorrectionCategory.PUNTEGGIATURA,
        }
        return self in error_categories
    
    @property
    def display_name(self) -> str:
        """Nome visualizzato per l'interfaccia utente."""
        names = {
            CorrectionCategory.ERRORI_RICONOSCIUTI: "Errori Riconosciuti",
            CorrectionCategory.SCONOSCIUTE: "Sconosciute",
            CorrectionCategory.SOSPETTE: "Sospette",
            CorrectionCategory.MIGLIORABILI: "Migliorabili",
            CorrectionCategory.PUNTEGGIATURA: "Punteggiatura",
            CorrectionCategory.IMBARAZZANTI: "Imbarazzanti",
            CorrectionCategory.VARIANTI: "Varianti",
            CorrectionCategory.NOMI_SIGLE: "Nomi/Sigle",
            CorrectionCategory.LINGUE: "Lingue",
            CorrectionCategory.CON_INFO: "Con Altre Informazioni",
            CorrectionCategory.LINK: "Link",
        }
        return names.get(self, self.value)
    
    @property
    def color_code(self) -> str:
        """Codice colore per la visualizzazione nel report."""
        colors = {
            CorrectionCategory.ERRORI_RICONOSCIUTI: "#ff4444",  # Rosso
            CorrectionCategory.SCONOSCIUTE: "#ffcc00",          # Giallo
            CorrectionCategory.SOSPETTE: "#ffcc00",             # Giallo
            CorrectionCategory.MIGLIORABILI: "#66cc66",         # Verde
            CorrectionCategory.PUNTEGGIATURA: "#ffcc00",        # Giallo
            CorrectionCategory.IMBARAZZANTI: "#ff9966",         # Arancione chiaro
            CorrectionCategory.VARIANTI: "#99ccff",             # Azzurro
            CorrectionCategory.NOMI_SIGLE: "#cccccc",           # Grigio chiaro
            CorrectionCategory.LINGUE: "#cc99ff",               # Viola chiaro
            CorrectionCategory.CON_INFO: "#99ffcc",             # Verde acqua
            CorrectionCategory.LINK: "#9999ff",                 # Blu chiaro
        }
        return colors.get(self, "#ffffff")


class CorrectionSource(Enum):
    """Fonte che ha generato la correzione."""
    
    LANGUAGETOOL = "languagetool"
    """LanguageTool (regole grammaticali e ortografiche)"""
    
    OPENAI_GPT = "openai_gpt"
    """OpenAI GPT (correzioni AI avanzate)"""
    
    CUSTOM_RULES = "custom_rules"
    """Regole personalizzate utente"""
    
    GLOSSARIO = "glossario"
    """Glossario personalizzato"""
    
    VOCABOLARIO_BASE = "vocabolario_base"
    """Vocabolario di Base per leggibilità"""
    
    SYSTEM = "system"
    """Sistema interno (formattazione, punteggiatura)"""


@dataclass
class CorrectionRecord:
    """
    Record dettagliato di una singola correzione identificata.
    
    Questo è il modello principale che contiene tutte le informazioni
    necessarie per tracciare, classificare e visualizzare una correzione
    nel report finale.
    """
    
    # ═══════════════════════════════════════════════════════════
    # IDENTIFICAZIONE
    # ═══════════════════════════════════════════════════════════
    
    id: str = field(default_factory=lambda: str(uuid4()))
    """ID univoco della correzione"""
    
    category: CorrectionCategory = CorrectionCategory.ERRORI_RICONOSCIUTI
    """Categoria della correzione"""
    
    source: CorrectionSource = CorrectionSource.SYSTEM
    """Fonte che ha generato la correzione"""
    
    # ═══════════════════════════════════════════════════════════
    # CONTENUTO TESTUALE
    # ═══════════════════════════════════════════════════════════
    
    original_text: str = ""
    """Testo originale (parola/frase con errore)"""
    
    corrected_text: Optional[str] = None
    """Testo corretto proposto (None se non applicabile)"""
    
    context: str = ""
    """Contesto completo (frase o paragrafo contenente l'errore)"""
    
    # ═══════════════════════════════════════════════════════════
    # POSIZIONAMENTO NEL DOCUMENTO
    # ═══════════════════════════════════════════════════════════
    
    position: int = 0
    """Offset carattere nel documento (posizione assoluta)"""
    
    length: int = 0
    """Lunghezza del testo originale in caratteri"""
    
    paragraph_index: int = 0
    """Indice del paragrafo (0-based)"""
    
    sentence_index: int = 0
    """Indice della frase all'interno del paragrafo (0-based)"""
    
    line_number: Optional[int] = None
    """Numero di riga nel documento (se applicabile)"""
    
    # ═══════════════════════════════════════════════════════════
    # ANALISI E CLASSIFICAZIONE
    # ═══════════════════════════════════════════════════════════
    
    rule_id: str = ""
    """ID della regola che ha triggato la correzione"""
    
    rule_description: str = ""
    """Descrizione della regola in linguaggio umano"""
    
    message: str = ""
    """Messaggio descrittivo dell'errore"""
    
    suggestions: List[str] = field(default_factory=list)
    """Lista di suggerimenti alternativi ordinati per rilevanza"""
    
    confidence_score: float = 1.0
    """Punteggio di confidenza (0.0-1.0)"""
    
    severity: str = "info"
    """Severità: 'critical', 'warning', 'info', 'suggestion'"""
    
    # ═══════════════════════════════════════════════════════════
    # METADATI ELABORAZIONE
    # ═══════════════════════════════════════════════════════════
    
    timestamp: datetime = field(default_factory=datetime.now)
    """Timestamp di quando è stata identificata la correzione"""
    
    is_applied: bool = False
    """Flag che indica se la correzione è stata applicata al documento"""
    
    is_ignored: bool = False
    """Flag che indica se la correzione è stata ignorata dall'utente"""
    
    user_feedback: Optional[str] = None
    """Feedback dell'utente ('correct', 'incorrect', 'unsure')"""
    
    # ═══════════════════════════════════════════════════════════
    # INFORMAZIONI AGGIUNTIVE
    # ═══════════════════════════════════════════════════════════
    
    additional_info: Dict[str, Any] = field(default_factory=dict)
    """Dizionario per informazioni specifiche della categoria/fonte"""
    
    url_references: List[str] = field(default_factory=list)
    """Link a risorse esterne (regole, documentazione)"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte il record in dizionario per serializzazione."""
        return {
            "id": self.id,
            "category": self.category.value,
            "category_name": self.category.display_name,
            "source": self.source.value,
            "original_text": self.original_text,
            "corrected_text": self.corrected_text,
            "context": self.context,
            "position": self.position,
            "length": self.length,
            "paragraph_index": self.paragraph_index,
            "sentence_index": self.sentence_index,
            "line_number": self.line_number,
            "rule_id": self.rule_id,
            "rule_description": self.rule_description,
            "message": self.message,
            "suggestions": self.suggestions,
            "confidence_score": self.confidence_score,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "is_applied": self.is_applied,
            "is_ignored": self.is_ignored,
            "user_feedback": self.user_feedback,
            "additional_info": self.additional_info,
            "url_references": self.url_references,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CorrectionRecord':
        """Crea un record da dizionario."""
        # Converti enum da stringa
        data['category'] = CorrectionCategory(data['category'])
        data['source'] = CorrectionSource(data['source'])
        
        # Converti timestamp
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        # Rimuovi campi non nel dataclass
        data.pop('category_name', None)
        
        return cls(**data)
    
    def get_context_with_highlight(self, 
                                   before_tag: str = "<mark>",
                                   after_tag: str = "</mark>") -> str:
        """
        Restituisce il contesto con il testo originale evidenziato.
        
        Args:
            before_tag: Tag/marcatore da inserire prima del testo
            after_tag: Tag/marcatore da inserire dopo il testo
            
        Returns:
            Stringa con il contesto e il testo evidenziato
        """
        # Trova la posizione relativa nel contesto
        try:
            idx = self.context.lower().find(self.original_text.lower())
            if idx >= 0:
                return (
                    self.context[:idx] +
                    before_tag +
                    self.context[idx:idx+len(self.original_text)] +
                    after_tag +
                    self.context[idx+len(self.original_text):]
                )
        except Exception:
            pass
        
        # Fallback: restituisci il contesto normale
        return self.context


@dataclass
class CorrectionStatistics:
    """
    Statistiche aggregate sulle correzioni per il report sintesi.
    """
    
    total_corrections: int = 0
    """Numero totale di correzioni identificate"""
    
    total_words_checked: int = 0
    """Numero totale di parole controllate"""
    
    total_contexts: int = 0
    """Numero totale di contesti verificati"""
    
    processing_time: float = 0.0
    """Tempo totale di elaborazione in secondi"""
    
    by_category: Dict[CorrectionCategory, int] = field(default_factory=dict)
    """Conteggio correzioni per categoria"""
    
    by_source: Dict[CorrectionSource, int] = field(default_factory=dict)
    """Conteggio correzioni per fonte"""
    
    unique_words: int = 0
    """Numero di parole uniche con correzioni"""
    
    applied_corrections: int = 0
    """Numero di correzioni applicate"""
    
    ignored_corrections: int = 0
    """Numero di correzioni ignorate"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte le statistiche in dizionario."""
        return {
            "total_corrections": self.total_corrections,
            "total_words_checked": self.total_words_checked,
            "total_contexts": self.total_contexts,
            "processing_time": self.processing_time,
            "by_category": {
                cat.value: count for cat, count in self.by_category.items()
            },
            "by_source": {
                src.value: count for src, count in self.by_source.items()
            },
            "unique_words": self.unique_words,
            "applied_corrections": self.applied_corrections,
            "ignored_corrections": self.ignored_corrections,
        }
