# utils/diff_engine.py
"""
Motore per generazione di diff dettagliati e analisi delle modifiche.
Crea report granulari delle correzioni applicate ai documenti.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from difflib import SequenceMatcher, unified_diff
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ChangeSegment:
    """Singolo segmento di modifica"""
    change_type: str  # 'insert', 'delete', 'replace', 'unchanged'
    original_text: str
    modified_text: str
    start_pos: int
    end_pos: int
    confidence: float = 1.0

@dataclass
class DiffResult:
    """Risultato di un'analisi diff"""
    original_text: str
    modified_text: str
    changes: List[ChangeSegment] = field(default_factory=list)
    similarity_ratio: float = 0.0
    total_changes: int = 0
    insertions: int = 0
    deletions: int = 0
    replacements: int = 0

@dataclass
class ParagraphDiff:
    """Diff di un singolo paragrafo"""
    paragraph_id: int
    original: str
    corrected: str
    diff_result: DiffResult
    change_summary: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class DocumentDiff:
    """Diff completo di un documento"""
    document_name: str
    total_paragraphs: int
    modified_paragraphs: int
    paragraph_diffs: List[ParagraphDiff] = field(default_factory=list)
    global_stats: Dict[str, Any] = field(default_factory=dict)
    generation_time: datetime = field(default_factory=datetime.now)

class DiffEngine:
    """
    Motore per analisi dettagliata delle differenze tra testi.
    Genera report comprensibili delle modifiche applicate.
    """
    
    def __init__(self):
        self.word_regex = re.compile(r'\b\w+\b|\W+')
        self.sentence_regex = re.compile(r'[.!?]+')
    
    def analyze_text_diff(self, original: str, modified: str, 
                         granularity: str = "word") -> DiffResult:
        """
        Analizza differenze tra due testi con granularità configurabile.
        
        Args:
            original: Testo originale
            modified: Testo modificato
            granularity: "char", "word", o "sentence"
            
        Returns:
            DiffResult: Analisi dettagliata delle differenze
        """
        if granularity == "char":
            return self._analyze_char_diff(original, modified)
        elif granularity == "word":
            return self._analyze_word_diff(original, modified)
        elif granularity == "sentence":
            return self._analyze_sentence_diff(original, modified)
        else:
            raise ValueError(f"Unsupported granularity: {granularity}")
    
    def _analyze_word_diff(self, original: str, modified: str) -> DiffResult:
        """Analizza differenze a livello di parole"""
        original_words = self.word_regex.findall(original)
        modified_words = self.word_regex.findall(modified)
        
        matcher = SequenceMatcher(None, original_words, modified_words)
        similarity_ratio = matcher.ratio()
        
        changes = []
        original_pos = 0
        modified_pos = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            original_segment = ''.join(original_words[i1:i2])
            modified_segment = ''.join(modified_words[j1:j2])
            
            if tag == 'equal':
                change = ChangeSegment(
                    change_type='unchanged',
                    original_text=original_segment,
                    modified_text=modified_segment,
                    start_pos=original_pos,
                    end_pos=original_pos + len(original_segment)
                )
            elif tag == 'delete':
                change = ChangeSegment(
                    change_type='delete',
                    original_text=original_segment,
                    modified_text='',
                    start_pos=original_pos,
                    end_pos=original_pos + len(original_segment)
                )
            elif tag == 'insert':
                change = ChangeSegment(
                    change_type='insert',
                    original_text='',
                    modified_text=modified_segment,
                    start_pos=original_pos,
                    end_pos=original_pos
                )
            elif tag == 'replace':
                change = ChangeSegment(
                    change_type='replace',
                    original_text=original_segment,
                    modified_text=modified_segment,
                    start_pos=original_pos,
                    end_pos=original_pos + len(original_segment)
                )
            
            changes.append(change)
            original_pos += len(original_segment)
        
        # Conta tipi di modifiche
        insertions = sum(1 for c in changes if c.change_type == 'insert')
        deletions = sum(1 for c in changes if c.change_type == 'delete')
        replacements = sum(1 for c in changes if c.change_type == 'replace')
        total_changes = insertions + deletions + replacements
        
        return DiffResult(
            original_text=original,
            modified_text=modified,
            changes=changes,
            similarity_ratio=similarity_ratio,
            total_changes=total_changes,
            insertions=insertions,
            deletions=deletions,
            replacements=replacements
        )
    
    def _analyze_char_diff(self, original: str, modified: str) -> DiffResult:
        """Analizza differenze a livello di caratteri"""
        matcher = SequenceMatcher(None, original, modified)
        similarity_ratio = matcher.ratio()
        
        changes = []
        original_pos = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            original_segment = original[i1:i2]
            modified_segment = modified[j1:j2]
            
            change = ChangeSegment(
                change_type=tag if tag != 'equal' else 'unchanged',
                original_text=original_segment,
                modified_text=modified_segment,
                start_pos=i1,
                end_pos=i2
            )
            changes.append(change)
        
        # Conta modifiche
        insertions = sum(1 for c in changes if c.change_type == 'insert')
        deletions = sum(1 for c in changes if c.change_type == 'delete')
        replacements = sum(1 for c in changes if c.change_type == 'replace')
        total_changes = insertions + deletions + replacements
        
        return DiffResult(
            original_text=original,
            modified_text=modified,
            changes=changes,
            similarity_ratio=similarity_ratio,
            total_changes=total_changes,
            insertions=insertions,
            deletions=deletions,
            replacements=replacements
        )
    
    def _analyze_sentence_diff(self, original: str, modified: str) -> DiffResult:
        """Analizza differenze a livello di frasi"""
        original_sentences = self.sentence_regex.split(original)
        modified_sentences = self.sentence_regex.split(modified)
        
        matcher = SequenceMatcher(None, original_sentences, modified_sentences)
        similarity_ratio = matcher.ratio()
        
        changes = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            original_segment = ' '.join(original_sentences[i1:i2])
            modified_segment = ' '.join(modified_sentences[j1:j2])
            
            change = ChangeSegment(
                change_type=tag if tag != 'equal' else 'unchanged',
                original_text=original_segment,
                modified_text=modified_segment,
                start_pos=0,  # Posizione approssimativa per frasi
                end_pos=len(original_segment)
            )
            changes.append(change)
        
        # Conta modifiche
        insertions = sum(1 for c in changes if c.change_type == 'insert')
        deletions = sum(1 for c in changes if c.change_type == 'delete')
        replacements = sum(1 for c in changes if c.change_type == 'replace')
        total_changes = insertions + deletions + replacements
        
        return DiffResult(
            original_text=original,
            modified_text=modified,
            changes=changes,
            similarity_ratio=similarity_ratio,
            total_changes=total_changes,
            insertions=insertions,
            deletions=deletions,
            replacements=replacements
        )
    
    def create_paragraph_diff(self, paragraph_id: int, original: str, 
                            corrected: str) -> ParagraphDiff:
        """
        Crea diff dettagliato per un singolo paragrafo.
        """
        diff_result = self.analyze_text_diff(original, corrected, granularity="word")
        
        # Genera summary leggibile
        change_summary = self._generate_change_summary(diff_result)
        
        return ParagraphDiff(
            paragraph_id=paragraph_id,
            original=original,
            corrected=corrected,
            diff_result=diff_result,
            change_summary=change_summary
        )
    
    def _generate_change_summary(self, diff_result: DiffResult) -> str:
        """Genera un riassunto leggibile delle modifiche"""
        if diff_result.total_changes == 0:
            return "Nessuna modifica"
        
        parts = []
        
        if diff_result.replacements > 0:
            parts.append(f"{diff_result.replacements} sostituzioni")
        if diff_result.insertions > 0:
            parts.append(f"{diff_result.insertions} inserimenti")
        if diff_result.deletions > 0:
            parts.append(f"{diff_result.deletions} rimozioni")
        
        summary = ", ".join(parts)
        similarity_pct = diff_result.similarity_ratio * 100
        
        return f"{summary} (similarità: {similarity_pct:.1f}%)"
    
    def create_document_diff(self, document_name: str, 
                           paragraph_diffs: List[ParagraphDiff]) -> DocumentDiff:
        """
        Crea diff completo per un documento.
        """
        total_paragraphs = len(paragraph_diffs)
        modified_paragraphs = sum(1 for diff in paragraph_diffs 
                                if diff.diff_result.total_changes > 0)
        
        # Statistiche globali
        total_changes = sum(diff.diff_result.total_changes for diff in paragraph_diffs)
        total_similarity = sum(diff.diff_result.similarity_ratio for diff in paragraph_diffs)
        avg_similarity = total_similarity / max(total_paragraphs, 1)
        
        global_stats = {
            "total_changes": total_changes,
            "average_similarity": avg_similarity,
            "modification_rate": modified_paragraphs / max(total_paragraphs, 1),
            "changes_per_paragraph": total_changes / max(total_paragraphs, 1)
        }
        
        return DocumentDiff(
            document_name=document_name,
            total_paragraphs=total_paragraphs,
            modified_paragraphs=modified_paragraphs,
            paragraph_diffs=paragraph_diffs,
            global_stats=global_stats
        )
    
    def generate_unified_diff(self, original: str, modified: str, 
                            filename: str = "document") -> str:
        """
        Genera diff in formato unified (come git diff).
        """
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff_lines = list(unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"{filename}_original",
            tofile=f"{filename}_corrected",
            lineterm=""
        ))
        
        return ''.join(diff_lines)
    
    def generate_html_diff(self, diff_result: DiffResult) -> str:
        """
        Genera diff visualizzabile in HTML con colori.
        """
        html_parts = ["<div class='diff-container'>"]
        
        for change in diff_result.changes:
            if change.change_type == 'unchanged':
                html_parts.append(f"<span class='unchanged'>{self._escape_html(change.original_text)}</span>")
            elif change.change_type == 'delete':
                html_parts.append(f"<span class='deleted'>{self._escape_html(change.original_text)}</span>")
            elif change.change_type == 'insert':
                html_parts.append(f"<span class='inserted'>{self._escape_html(change.modified_text)}</span>")
            elif change.change_type == 'replace':
                html_parts.append(f"<span class='deleted'>{self._escape_html(change.original_text)}</span>")
                html_parts.append(f"<span class='inserted'>{self._escape_html(change.modified_text)}</span>")
        
        html_parts.append("</div>")
        
        # Aggiungi CSS
        css = """
        <style>
        .diff-container { font-family: monospace; line-height: 1.4; }
        .unchanged { color: #333; }
        .deleted { background-color: #ffdddd; text-decoration: line-through; color: #d73a49; }
        .inserted { background-color: #ddffdd; color: #28a745; }
        </style>
        """
        
        return css + ''.join(html_parts)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def export_diff_to_markdown(self, document_diff: DocumentDiff, 
                              output_path: Path) -> None:
        """
        Esporta diff completo in formato Markdown.
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Diff Report: {document_diff.document_name}\n\n")
            f.write(f"**Generato il:** {document_diff.generation_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Statistiche globali
            f.write("## Statistiche Globali\n\n")
            f.write(f"- **Paragrafi totali:** {document_diff.total_paragraphs}\n")
            f.write(f"- **Paragrafi modificati:** {document_diff.modified_paragraphs}\n")
            f.write(f"- **Tasso di modifica:** {document_diff.global_stats['modification_rate']:.1%}\n")
            f.write(f"- **Similarità media:** {document_diff.global_stats['average_similarity']:.1%}\n")
            f.write(f"- **Modifiche totali:** {document_diff.global_stats['total_changes']}\n\n")
            
            # Dettagli per paragrafo
            f.write("## Modifiche per Paragrafo\n\n")
            
            for para_diff in document_diff.paragraph_diffs:
                if para_diff.diff_result.total_changes > 0:
                    f.write(f"### Paragrafo {para_diff.paragraph_id}\n\n")
                    f.write(f"**Riassunto:** {para_diff.change_summary}\n\n")
                    
                    f.write("**Originale:**\n")
                    f.write(f"```\n{para_diff.original}\n```\n\n")
                    
                    f.write("**Corretto:**\n")
                    f.write(f"```\n{para_diff.corrected}\n```\n\n")
                    
                    # Diff dettagliato
                    f.write("**Modifiche dettagliate:**\n")
                    for change in para_diff.diff_result.changes:
                        if change.change_type != 'unchanged':
                            f.write(f"- **{change.change_type.upper()}:** ")
                            if change.change_type == 'replace':
                                f.write(f"`{change.original_text}` → `{change.modified_text}`\n")
                            elif change.change_type == 'delete':
                                f.write(f"~~`{change.original_text}`~~\n")
                            elif change.change_type == 'insert':
                                f.write(f"++`{change.modified_text}`++\n")
                    f.write("\n---\n\n")
    
    def get_diff_statistics(self, document_diff: DocumentDiff) -> Dict[str, Any]:
        """
        Ottiene statistiche dettagliate del diff.
        """
        modification_types = {"replace": 0, "insert": 0, "delete": 0}
        
        for para_diff in document_diff.paragraph_diffs:
            for change in para_diff.diff_result.changes:
                if change.change_type in modification_types:
                    modification_types[change.change_type] += 1
        
        return {
            "document_name": document_diff.document_name,
            "total_paragraphs": document_diff.total_paragraphs,
            "modified_paragraphs": document_diff.modified_paragraphs,
            "modification_rate": document_diff.global_stats["modification_rate"],
            "average_similarity": document_diff.global_stats["average_similarity"],
            "total_changes": document_diff.global_stats["total_changes"],
            "changes_by_type": modification_types,
            "generation_time": document_diff.generation_time.isoformat()
        }

def create_diff_engine() -> DiffEngine:
    """Factory function per creare DiffEngine"""
    return DiffEngine()
