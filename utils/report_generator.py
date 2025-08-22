# utils/report_generator.py
"""
Generatore di report avanzati per il sistema di correzione.
Crea report dettagliati in Markdown, HTML e JSON per analisi complete.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta

from utils.diff_engine import DocumentDiff, ParagraphDiff
from src.core.safe_correction import CorrectionResult, QualityScore
from core.quality_assurance import QualityReport

logger = logging.getLogger(__name__)

@dataclass
class ReportSection:
    """Sezione di un report"""
    title: str
    content: str
    level: int = 2  # Livello heading (1-6)
    metadata: Dict[str, Any] = None

@dataclass
class CorrectionStats:
    """Statistiche complete di una sessione di correzione"""
    total_paragraphs: int
    paragraphs_processed: int
    corrections_applied: int
    corrections_rejected: int
    rollbacks_performed: int
    processing_time: float
    success_rate: float
    average_quality_score: float
    total_tokens_used: int = 0
    api_calls_made: int = 0
    cache_hits: int = 0

class ReportGenerator:
    """
    Generatore di report completi per sessioni di correzione.
    Supporta formati multipli e personalizzazione avanzata.
    """
    
    def __init__(self):
        self.report_templates = {
            "standard": self._standard_template,
            "detailed": self._detailed_template,
            "summary": self._summary_template
        }
    
    def generate_correction_report(self, 
                                 document_diff: DocumentDiff,
                                 correction_stats: CorrectionStats,
                                 quality_reports: List[QualityReport],
                                 output_path: Path,
                                 template: str = "standard",
                                 format_type: str = "markdown") -> Path:
        """
        Genera report completo di correzione.
        
        Args:
            document_diff: Diff del documento
            correction_stats: Statistiche correzione
            quality_reports: Report di qualità
            output_path: Path di output
            template: Tipo template ("standard", "detailed", "summary")
            format_type: Formato output ("markdown", "html", "json")
            
        Returns:
            Path: Path del file generato
        """
        logger.info(f"📊 Generating {template} report in {format_type} format...")
        
        # Seleziona template
        template_func = self.report_templates.get(template, self._standard_template)
        
        # Genera contenuto
        sections = template_func(document_diff, correction_stats, quality_reports)
        
        # Applica formato
        if format_type == "markdown":
            content = self._render_markdown(sections)
            final_path = output_path.with_suffix('.md')
        elif format_type == "html":
            content = self._render_html(sections)
            final_path = output_path.with_suffix('.html')
        elif format_type == "json":
            content = self._render_json(sections, document_diff, correction_stats, quality_reports)
            final_path = output_path.with_suffix('.json')
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        # Scrivi file
        with open(final_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"✅ Report generated: {final_path.name}")
        return final_path
    
    def _standard_template(self, document_diff: DocumentDiff, 
                          correction_stats: CorrectionStats,
                          quality_reports: List[QualityReport]) -> List[ReportSection]:
        """Template standard per report di correzione"""
        sections = []
        
        # Header
        sections.append(ReportSection(
            title=f"Report di Correzione - {document_diff.document_name}",
            content=self._generate_header_content(document_diff, correction_stats),
            level=1
        ))
        
        # Executive Summary
        sections.append(ReportSection(
            title="Riassunto Esecutivo",
            content=self._generate_executive_summary(document_diff, correction_stats, quality_reports),
            level=2
        ))
        
        # Statistiche
        sections.append(ReportSection(
            title="Statistiche di Correzione",
            content=self._generate_stats_content(correction_stats),
            level=2
        ))
        
        # Qualità
        sections.append(ReportSection(
            title="Analisi Qualità",
            content=self._generate_quality_content(quality_reports),
            level=2
        ))
        
        # Modifiche Principali
        sections.append(ReportSection(
            title="Modifiche Principali",
            content=self._generate_main_changes_content(document_diff),
            level=2
        ))
        
        return sections
    
    def _detailed_template(self, document_diff: DocumentDiff,
                          correction_stats: CorrectionStats, 
                          quality_reports: List[QualityReport]) -> List[ReportSection]:
        """Template dettagliato con tutte le informazioni"""
        sections = self._standard_template(document_diff, correction_stats, quality_reports)
        
        # Aggiungi sezioni dettagliate
        sections.append(ReportSection(
            title="Modifiche Dettagliate per Paragrafo",
            content=self._generate_detailed_changes_content(document_diff),
            level=2
        ))
        
        sections.append(ReportSection(
            title="Metriche di Performance",
            content=self._generate_performance_content(correction_stats),
            level=2
        ))
        
        sections.append(ReportSection(
            title="Analisi Errori e Rollback",
            content=self._generate_errors_content(document_diff, correction_stats),
            level=2
        ))
        
        return sections
    
    def _summary_template(self, document_diff: DocumentDiff,
                         correction_stats: CorrectionStats,
                         quality_reports: List[QualityReport]) -> List[ReportSection]:
        """Template riassuntivo per quick overview"""
        return [
            ReportSection(
                title=f"Riassunto - {document_diff.document_name}",
                content=self._generate_summary_content(document_diff, correction_stats, quality_reports),
                level=1
            )
        ]
    
    def _generate_header_content(self, document_diff: DocumentDiff, 
                               correction_stats: CorrectionStats) -> str:
        """Genera contenuto header"""
        return f"""
**Documento:** {document_diff.document_name}  
**Data Generazione:** {document_diff.generation_time.strftime('%Y-%m-%d %H:%M:%S')}  
**Tempo di Elaborazione:** {correction_stats.processing_time:.1f} secondi  
**Paragrafi Elaborati:** {correction_stats.paragraphs_processed}/{correction_stats.total_paragraphs}  
**Tasso di Successo:** {correction_stats.success_rate:.1%}  
"""
    
    def _generate_executive_summary(self, document_diff: DocumentDiff,
                                  correction_stats: CorrectionStats, 
                                  quality_reports: List[QualityReport]) -> str:
        """Genera riassunto esecutivo"""
        avg_quality = correction_stats.average_quality_score
        quality_verdict = "Eccellente" if avg_quality > 0.95 else "Buona" if avg_quality > 0.85 else "Sufficiente" if avg_quality > 0.75 else "Da Rivedere"
        
        processing_rate = correction_stats.paragraphs_processed / max(correction_stats.processing_time / 60, 0.1)  # par/min
        
        return f"""
Il documento **{document_diff.document_name}** è stato elaborato con successo.

**Risultati Principali:**
- ✅ **{correction_stats.corrections_applied}** correzioni applicate con successo
- 🔄 **{correction_stats.rollbacks_performed}** rollback per protezione qualità  
- 📊 **Qualità Media:** {avg_quality:.1%} ({quality_verdict})
- ⚡ **Velocità Elaborazione:** {processing_rate:.1f} paragrafi/minuto
- 💾 **Modifiche al Documento:** {document_diff.modified_paragraphs}/{document_diff.total_paragraphs} paragrafi ({document_diff.global_stats['modification_rate']:.1%})

**Raccomandazioni:**
{self._generate_recommendations(correction_stats, quality_reports)}
"""
    
    def _generate_recommendations(self, correction_stats: CorrectionStats, 
                                quality_reports: List[QualityReport]) -> str:
        """Genera raccomandazioni basate sui risultati"""
        recommendations = []
        
        if correction_stats.success_rate < 0.8:
            recommendations.append("- ⚠️ Tasso di successo basso - rivedere configurazione qualità")
        
        if correction_stats.rollbacks_performed > correction_stats.corrections_applied * 0.2:
            recommendations.append("- 🔄 Molti rollback - considerare modalità più conservativa")
        
        if correction_stats.average_quality_score > 0.95:
            recommendations.append("- ✨ Qualità eccellente - documento pronto per pubblicazione")
        elif correction_stats.average_quality_score < 0.75:
            recommendations.append("- 📝 Qualità da migliorare - revisione manuale consigliata")
        
        # Analizza quality reports
        low_quality_count = sum(1 for qr in quality_reports if not qr.passed)
        if low_quality_count > 0:
            recommendations.append(f"- 🔍 {low_quality_count} paragrafi sotto soglia qualità - revisione richiesta")
        
        return "\n".join(recommendations) if recommendations else "- ✅ Nessuna raccomandazione particolare - risultati ottimali"
    
    def _generate_stats_content(self, correction_stats: CorrectionStats) -> str:
        """Genera contenuto statistiche"""
        rejection_rate = correction_stats.corrections_rejected / max(correction_stats.corrections_applied + correction_stats.corrections_rejected, 1)
        
        return f"""
| Metrica | Valore |
|---------|--------|
| **Paragrafi Totali** | {correction_stats.total_paragraphs:,} |
| **Paragrafi Elaborati** | {correction_stats.paragraphs_processed:,} |
| **Correzioni Applicate** | {correction_stats.corrections_applied:,} |
| **Correzioni Rifiutate** | {correction_stats.corrections_rejected:,} |
| **Rollback Eseguiti** | {correction_stats.rollbacks_performed:,} |
| **Tasso Successo** | {correction_stats.success_rate:.1%} |
| **Tasso Rifiuto** | {rejection_rate:.1%} |
| **Qualità Media** | {correction_stats.average_quality_score:.3f} |
| **Tempo Elaborazione** | {correction_stats.processing_time:.1f}s |
| **Token Utilizzati** | {correction_stats.total_tokens_used:,} |
| **Chiamate API** | {correction_stats.api_calls_made:,} |
| **Cache Hits** | {correction_stats.cache_hits:,} |
"""
    
    def _generate_quality_content(self, quality_reports: List[QualityReport]) -> str:
        """Genera contenuto analisi qualità"""
        if not quality_reports:
            return "Nessun report di qualità disponibile."
        
        passed_count = sum(1 for qr in quality_reports if qr.passed)
        avg_score = sum(qr.overall_score for qr in quality_reports) / len(quality_reports)
        
        content = f"""
**Risultati Generali:**
- ✅ **Paragrafi Passati:** {passed_count}/{len(quality_reports)} ({passed_count/len(quality_reports):.1%})
- 📊 **Score Medio:** {avg_score:.3f}

**Distribuzione Qualità:**
"""
        
        # Distribuzione per score ranges
        ranges = [(0.95, 1.0, "Eccellente"), (0.85, 0.95, "Buona"), (0.75, 0.85, "Sufficiente"), (0.0, 0.75, "Da Rivedere")]
        
        for min_score, max_score, label in ranges:
            count = sum(1 for qr in quality_reports if min_score <= qr.overall_score < max_score)
            percentage = count / len(quality_reports) * 100
            content += f"- **{label}:** {count} paragrafi ({percentage:.1f}%)\n"
        
        # Issues più comuni
        all_issues = []
        for qr in quality_reports:
            all_issues.extend(qr.issues_found)
        
        if all_issues:
            issue_counts = {}
            for issue in all_issues:
                issue_type = issue.split(':')[0] if ':' in issue else issue
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
            
            content += "\n**Issues Più Frequenti:**\n"
            for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                content += f"- {issue_type}: {count} occorrenze\n"
        
        return content
    
    def _generate_main_changes_content(self, document_diff: DocumentDiff) -> str:
        """Genera contenuto modifiche principali"""
        if not document_diff.paragraph_diffs:
            return "Nessuna modifica significativa rilevata."
        
        # Trova i paragrafi con più modifiche
        significant_changes = [
            pd for pd in document_diff.paragraph_diffs 
            if pd.diff_result.total_changes >= 3  # Soglia per modifiche significative
        ]
        
        significant_changes.sort(key=lambda x: x.diff_result.total_changes, reverse=True)
        
        content = f"**Paragrafi con Modifiche Significative:** {len(significant_changes)}\n\n"
        
        # Mostra top 5 modifiche
        for i, para_diff in enumerate(significant_changes[:5], 1):
            content += f"**{i}. Paragrafo {para_diff.paragraph_id}**\n"
            content += f"   - {para_diff.change_summary}\n"
            content += f"   - Similarità: {para_diff.diff_result.similarity_ratio:.1%}\n"
            
            # Mostra preview del cambiamento
            if len(para_diff.original) > 100:
                preview_orig = para_diff.original[:100] + "..."
            else:
                preview_orig = para_diff.original
            
            if len(para_diff.corrected) > 100:
                preview_corr = para_diff.corrected[:100] + "..."
            else:
                preview_corr = para_diff.corrected
            
            content += f"   - **Prima:** {preview_orig}\n"
            content += f"   - **Dopo:** {preview_corr}\n\n"
        
        return content
    
    def _generate_detailed_changes_content(self, document_diff: DocumentDiff) -> str:
        """Genera contenuto modifiche dettagliate"""
        content = ""
        
        for para_diff in document_diff.paragraph_diffs:
            if para_diff.diff_result.total_changes > 0:
                content += f"### Paragrafo {para_diff.paragraph_id}\n\n"
                content += f"**Riassunto:** {para_diff.change_summary}\n\n"
                
                content += "**Testo Originale:**\n"
                content += f"```\n{para_diff.original}\n```\n\n"
                
                content += "**Testo Corretto:**\n"
                content += f"```\n{para_diff.corrected}\n```\n\n"
                
                # Dettagli modifiche
                if para_diff.diff_result.changes:
                    content += "**Modifiche Applicate:**\n"
                    for change in para_diff.diff_result.changes:
                        if change.change_type != 'unchanged':
                            if change.change_type == 'replace':
                                content += f"- 🔄 **Sostituito:** `{change.original_text}` → `{change.modified_text}`\n"
                            elif change.change_type == 'delete':
                                content += f"- ❌ **Rimosso:** `{change.original_text}`\n"
                            elif change.change_type == 'insert':
                                content += f"- ➕ **Aggiunto:** `{change.modified_text}`\n"
                
                content += "\n---\n\n"
        
        return content or "Nessuna modifica dettagliata da mostrare."
    
    def _generate_performance_content(self, correction_stats: CorrectionStats) -> str:
        """Genera contenuto performance"""
        paragraphs_per_second = correction_stats.paragraphs_processed / max(correction_stats.processing_time, 0.1)
        tokens_per_second = correction_stats.total_tokens_used / max(correction_stats.processing_time, 0.1)
        
        return f"""
**Metriche di Performance:**

| Metrica | Valore |
|---------|--------|
| **Paragrafi/Secondo** | {paragraphs_per_second:.2f} |
| **Token/Secondo** | {tokens_per_second:.0f} |
| **Tempo Medio per Paragrafo** | {correction_stats.processing_time / max(correction_stats.paragraphs_processed, 1):.2f}s |
| **Cache Hit Rate** | {correction_stats.cache_hits / max(correction_stats.api_calls_made, 1):.1%} |
| **Chiamate API/Minuto** | {correction_stats.api_calls_made / max(correction_stats.processing_time / 60, 0.1):.1f} |

**Efficienza:**
- 💰 **Token per Correzione:** {correction_stats.total_tokens_used / max(correction_stats.corrections_applied, 1):.0f}
- ⚡ **Throughput:** {(correction_stats.corrections_applied / correction_stats.processing_time * 3600):.0f} correzioni/ora
"""
    
    def _generate_errors_content(self, document_diff: DocumentDiff, 
                               correction_stats: CorrectionStats) -> str:
        """Genera contenuto errori e rollback"""
        rollback_rate = correction_stats.rollbacks_performed / max(correction_stats.corrections_applied + correction_stats.rollbacks_performed, 1)
        
        content = f"""
**Analisi Rollback e Errori:**

- 🔄 **Rollback Eseguiti:** {correction_stats.rollbacks_performed}
- 📊 **Tasso Rollback:** {rollback_rate:.1%}
- ❌ **Correzioni Rifiutate:** {correction_stats.corrections_rejected}

"""
        
        if rollback_rate > 0.1:  # >10% rollback
            content += "⚠️ **Attenzione:** Alto tasso di rollback rilevato. Possibili cause:\n"
            content += "- Soglia qualità troppo alta\n"
            content += "- Testo particolarmente complesso\n"
            content += "- Necessità di tuning parametri\n\n"
        
        return content
    
    def _generate_summary_content(self, document_diff: DocumentDiff,
                                correction_stats: CorrectionStats,
                                quality_reports: List[QualityReport]) -> str:
        """Genera contenuto riassuntivo"""
        return f"""
**{document_diff.document_name}** - Elaborazione completata il {document_diff.generation_time.strftime('%Y-%m-%d %H:%M')}

📊 **Risultati:**
- Paragrafi: {correction_stats.paragraphs_processed}/{correction_stats.total_paragraphs}
- Correzioni: {correction_stats.corrections_applied} applicate, {correction_stats.corrections_rejected} rifiutate
- Qualità: {correction_stats.average_quality_score:.1%} (media)
- Tempo: {correction_stats.processing_time:.1f}s

🎯 **Outcome:** {correction_stats.success_rate:.1%} successo - {"✅ OTTIMO" if correction_stats.success_rate > 0.9 else "⚠️ DA RIVEDERE" if correction_stats.success_rate < 0.8 else "🟡 BUONO"}
"""
    
    def _render_markdown(self, sections: List[ReportSection]) -> str:
        """Renderizza sezioni in Markdown"""
        content = []
        
        for section in sections:
            # Header con livello appropriato
            header = "#" * section.level + " " + section.title
            content.append(header)
            content.append("")  # Riga vuota
            content.append(section.content)
            content.append("")  # Riga vuota
        
        return "\n".join(content)
    
    def _render_html(self, sections: List[ReportSection]) -> str:
        """Renderizza sezioni in HTML"""
        html_parts = ["""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Report di Correzione</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }
        table { border-collapse: collapse; width: 100%; margin: 1em 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f5f5f5; }
        code { background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
        pre { background-color: #f8f8f8; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .error { color: #dc3545; }
    </style>
</head>
<body>
"""]
        
        for section in sections:
            # Converte Markdown a HTML basilare
            html_content = self._markdown_to_html(section.content)
            html_parts.append(f"<h{section.level}>{section.title}</h{section.level}>")
            html_parts.append(html_content)
        
        html_parts.append("</body></html>")
        return "\n".join(html_parts)
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """Conversione basilare Markdown → HTML"""
        html = markdown_text
        
        # Bold
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Code
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        
        # Lists
        html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        
        # Line breaks
        html = html.replace('\n', '<br>\n')
        
        return html
    
    def _render_json(self, sections: List[ReportSection], 
                    document_diff: DocumentDiff, 
                    correction_stats: CorrectionStats,
                    quality_reports: List[QualityReport]) -> str:
        """Renderizza in formato JSON strutturato"""
        report_data = {
            "metadata": {
                "document_name": document_diff.document_name,
                "generation_time": document_diff.generation_time.isoformat(),
                "generator": "ReportGenerator v1.0"
            },
            "correction_stats": asdict(correction_stats),
            "document_diff": {
                "total_paragraphs": document_diff.total_paragraphs,
                "modified_paragraphs": document_diff.modified_paragraphs,
                "global_stats": document_diff.global_stats
            },
            "quality_summary": {
                "total_reports": len(quality_reports),
                "passed_count": sum(1 for qr in quality_reports if qr.passed),
                "average_score": sum(qr.overall_score for qr in quality_reports) / max(len(quality_reports), 1)
            },
            "sections": [asdict(section) for section in sections]
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False, default=str)

def create_report_generator() -> ReportGenerator:
    """Factory function per creare ReportGenerator"""
    return ReportGenerator()
