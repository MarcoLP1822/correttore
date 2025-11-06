# utils/report_generator.py
"""
Generatore di report avanzati per il sistema di correzione.
Crea report dettagliati in Markdown, HTML e JSON per analisi complete.
Supporta categorizzazione secondo lo standard Corrige.it.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta

from correttore.utils.diff_engine import DocumentDiff, ParagraphDiff
from correttore.core.safe_correction import CorrectionResult, QualityScore
from correttore.core.quality_assurance import QualityReport
from correttore.utils.corrige_categorizer import (
    CorrigeCategorizer, 
    CorrectionContext, 
    CategorizedCorrection,
    CorrigeCategory,
    create_corrige_categorizer
)

logger = logging.getLogger(__name__)

@dataclass
class ReportSection:
    """Sezione di un report"""
    title: str
    content: str
    level: int = 2  # Livello heading (1-6)
    metadata: Optional[Dict[str, Any]] = None

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
    Include categorizzazione secondo standard Corrige.it.
    """
    
    def __init__(self):
        self.report_templates = {
            "standard": self._standard_template,
            "detailed": self._detailed_template,
            "summary": self._summary_template,
            "corrige": self._corrige_template  # Nuovo template Corrige-style
        }
        self.categorizer = create_corrige_categorizer()
    
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
    
    def _corrige_template(self, document_diff: DocumentDiff,
                         correction_stats: CorrectionStats,
                         quality_reports: List[QualityReport]) -> List[ReportSection]:
        """
        Template secondo lo standard Corrige.it.
        Organizza il report nelle categorie standard del resoconto ortografia.
        """
        sections = []
        
        # Estrai e categorizza tutte le correzioni dal document_diff
        categorized = self._categorize_all_corrections(document_diff)
        stats = self.categorizer.generate_statistics(categorized)
        
        # Header principale
        sections.append(ReportSection(
            title=f"Resoconto Ortografia - {document_diff.document_name}",
            content=self._generate_corrige_header(document_diff, correction_stats),
            level=1
        ))
        
        # Quadro di sintesi
        sections.append(ReportSection(
            title="Quadro di sintesi",
            content=self._generate_corrige_sintesi(document_diff, correction_stats, stats),
            level=2
        ))
        
        # Sezioni per categoria (solo se hanno contenuti)
        category_order = [
            CorrigeCategory.ERRORI,
            CorrigeCategory.SCONOSCIUTE,
            CorrigeCategory.SOSPETTE,
            CorrigeCategory.MIGLIORABILI,
            CorrigeCategory.PUNTEGGIATURA,
            CorrigeCategory.IMBARAZZANTI,
            CorrigeCategory.VARIANTI,
            CorrigeCategory.NOMI_SIGLE,
            CorrigeCategory.LINGUE,
            CorrigeCategory.CON_INFO
        ]
        
        for category in category_order:
            corrections = categorized.get(category, [])
            if corrections:
                sections.append(ReportSection(
                    title=category.value,
                    content=self._generate_corrige_category_content(category, corrections),
                    level=2,
                    metadata={'count': len(corrections), 'category': category.name}
                ))
        
        return sections
    
    def _categorize_all_corrections(self, document_diff: DocumentDiff) -> Dict[CorrigeCategory, List[CategorizedCorrection]]:
        """Estrae e categorizza tutte le correzioni dal document diff"""
        contexts = []
        
        for para_diff in document_diff.paragraph_diffs:
            if para_diff.diff_result.total_changes > 0:
                # Estrai ogni singola modifica come CorrectionContext
                for change in para_diff.diff_result.changes:
                    if change.change_type in ['replace', 'delete', 'insert']:
                        context = CorrectionContext(
                            original_text=change.original_text if change.change_type != 'insert' else '',
                            corrected_text=change.modified_text if change.change_type != 'delete' else '',
                            paragraph_context=para_diff.original[:200],  # Prime 200 char come contesto
                            position=0,  # Position not directly available from ChangeSegment
                            correction_type='diff_based',
                            message=para_diff.change_summary
                        )
                        contexts.append(context)
        
        return self.categorizer.categorize_corrections(contexts)
    
    def _generate_corrige_header(self, document_diff: DocumentDiff, 
                                correction_stats: CorrectionStats) -> str:
        """Genera header in stile Corrige.it"""
        return f"""
Documento controllato il {document_diff.generation_time.strftime('%d/%m/%Y alle %H:%M')}

Il presente resoconto è organizzato per categorie di segnalazione secondo lo standard professionale di correzione ortografica e grammaticale.
"""
    
    def _generate_corrige_sintesi(self, document_diff: DocumentDiff,
                                 correction_stats: CorrectionStats,
                                 stats: Dict[str, Any]) -> str:
        """Genera quadro di sintesi in stile Corrige.it"""
        total_words = sum(len(pd.original.split()) for pd in document_diff.paragraph_diffs)
        
        content = f"""
**Informazioni Generali:**

| Informazione | Valore |
|--------------|--------|
| **Paragrafi controllati** | {correction_stats.paragraphs_processed:,} |
| **Parole totali (stima)** | {total_words:,} |
| **Segnalazioni totali** | {stats['totale_segnalazioni']:,} |
| **Modifiche applicate** | {correction_stats.corrections_applied:,} |
| **Tempo elaborazione** | {correction_stats.processing_time:.1f}s |

**Distribuzione Segnalazioni per Categoria:**

"""
        
        # Tabella categorie
        if stats['per_categoria']:
            content += "| Categoria | Segnalazioni | % sul totale |\n"
            content += "|-----------|--------------|-------------|\n"
            for cat_name, cat_stats in stats['per_categoria'].items():
                content += f"| **{cat_name}** | {cat_stats['count']:,} | {cat_stats['percentuale']:.1f}% |\n"
        else:
            content += "*Nessuna segnalazione rilevata.*\n"
        
        content += "\n"
        
        # Note e avvisi
        if correction_stats.rollbacks_performed > 0:
            content += f"\n⚠️ **Nota:** {correction_stats.rollbacks_performed} correzioni sono state annullate per preservare la qualità del testo.\n"
        
        return content
    
    def _generate_corrige_category_content(self, category: CorrigeCategory, 
                                          corrections: List[CategorizedCorrection]) -> str:
        """Genera contenuto per una specifica categoria Corrige"""
        
        # Descrizione della categoria
        descriptions = {
            CorrigeCategory.ERRORI: "Questa lista presenta errori in sé, come \"errrore\", ed errori nel contesto, come \"ditali\" / \"di tali\", \"fragranza\" / \"flagranza\". "
            "In genere le parole ed espressioni evidenziate in questa sezione sono il risultato di un errore di battitura o del mancato rispetto di norme redazionali.",
            
            CorrigeCategory.SCONOSCIUTE: "Questa sezione segnala parole non riconosciute. Si tratta soprattutto di errori di battitura che producono parole inesistenti "
            "e, in alcuni casi, possono essere anche parole valide ma sconosciute (nomi di località minori, termini tecnico-specialistici, ecc.).",
            
            CorrigeCategory.SOSPETTE: "Questa sezione segnala parole in sé corrette ma che potrebbero essere un errore rispetto al contesto e che vale la pena controllare. "
            "Si tratta di indicazioni molto utili nella correzione finale, perché controllando qualche parola in più si possono evitare errori subdoli.",
            
            CorrigeCategory.MIGLIORABILI: "Questa sezione segnala parole ed espressioni che è possibile migliorare rispetto alle norme redazionali correnti: "
            "usi linguistici o grafici che è possibile rendere più adatti a contesti formali o di editoria professionale.",
            
            CorrigeCategory.PUNTEGGIATURA: "Questa sezione elenca i casi nei quali l'uso della punteggiatura potrebbe essere sbagliato dal punto di vista formale. "
            "Si tratta di segnalazioni da valutare caso per caso, poiché la punteggiatura si può presentare in moltissimi modi, validi in determinati contesti ma errati in altri.",
            
            CorrigeCategory.IMBARAZZANTI: "Questa sezione segnala parole ed espressioni potenzialmente imbarazzanti o volgari. "
            "Queste parole sono in sé valide ma, se fossero presenti per errore, potrebbero avere effetti imbarazzanti.",
            
            CorrigeCategory.VARIANTI: "Questa sezione aiuta a verificare la coerenza ortografica all'interno del testo. "
            "In un testo ben scritto, le parole che possono presentare varianti grafiche dovrebbero essere scritte usando una sola delle varianti.",
            
            CorrigeCategory.NOMI_SIGLE: "Questa sezione elenca le parole riconosciute o riconoscibili come nome proprio, sigla, acronimo ecc.",
            
            CorrigeCategory.LINGUE: "Questa sezione elenca le parole del testo che appartengono ad altre lingue. "
            "La lista serve a verificare l'uso di parole non italiane e le eventuali varianti tra di esse.",
            
            CorrigeCategory.CON_INFO: "Questa sezione elenca parole e contesti per i quali sono disponibili informazioni terminologiche o enciclopediche utili."
        }
        
        content = f"*{descriptions.get(category, '')}*\n\n"
        content += f"**{len(corrections)} {'errore' if len(corrections) == 1 else 'errori'} nell'uso di {len(set(c.original_word.lower() for c in corrections))} {'parola' if len(set(c.original_word.lower() for c in corrections)) == 1 else 'parole'}**\n\n"
        
        # Legenda per categorie interattive
        if category in [CorrigeCategory.SCONOSCIUTE, CorrigeCategory.SOSPETTE]:
            content += "**Info:** altri errori potrebbero essere presenti tra le parole. Accanto a ogni segnalazione puoi usare i bottoni **Corretta** ed **Errore** "
            content += "per segnalare la soluzione per il caso segnalato.\n\n"
        
        content += "---\n\n"
        
        # Lista delle correzioni
        # Raggruppa per parola originale
        by_word = {}
        for correction in corrections:
            word_key = correction.original_word.lower()
            if word_key not in by_word:
                by_word[word_key] = []
            by_word[word_key].append(correction)
        
        # Ordina per frequenza (più frequenti prima)
        sorted_words = sorted(by_word.items(), key=lambda x: len(x[1]), reverse=True)
        
        for word, word_corrections in sorted_words:
            count = len(word_corrections)
            first_correction = word_corrections[0]
            
            # Titolo: parola originale
            content += f"### {first_correction.original_word}"
            if count > 1:
                content += f" *({count} occorrenze)*"
            content += "\n\n"
            
            # Correzione suggerita (se disponibile)
            if first_correction.corrected_word:
                if first_correction.is_suggestion:
                    content += f"**Suggerimento:** {first_correction.corrected_word}\n\n"
                else:
                    content += f"**Correzione:** {first_correction.corrected_word}\n\n"
            
            # Spiegazione
            if first_correction.explanation:
                content += f"*{first_correction.explanation}*\n\n"
            
            # Varianti (per categoria VARIANTI)
            if first_correction.variants:
                content += f"**Varianti disponibili:** {', '.join(first_correction.variants)}\n\n"
            
            # Lingua (per categoria LINGUE)
            if first_correction.language:
                content += f"**Lingua:** {first_correction.language}\n\n"
            
            # Link info (se disponibile)
            if first_correction.info_link:
                content += f"ℹ️ [Maggiori informazioni]({first_correction.info_link})\n\n"
            
            # Contesti (mostra max 3 esempi)
            if count <= 3:
                content += "**Contesto:**\n"
                for corr in word_corrections:
                    content += f"- ...{corr.context}...\n"
            else:
                content += f"**Primi 3 contesti** (su {count} totali):\n"
                for corr in word_corrections[:3]:
                    content += f"- ...{corr.context}...\n"
            
            content += "\n"
            
            # Bottoni interattivi (simulati come testo)
            if category in [CorrigeCategory.SCONOSCIUTE, CorrigeCategory.SOSPETTE]:
                content += "[ Corretta ] [ Errore ]\n"
            
            content += "\n---\n\n"
        
        return content
    
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
        
        # Controlla se è un report Corrige-style dalle metadata
        is_corrige_style = any(
            s.metadata and s.metadata.get('category') 
            for s in sections if s.metadata
        )
        
        if is_corrige_style:
            return self._render_html_corrige(sections)
        else:
            return self._render_html_standard(sections)
    
    def _render_html_standard(self, sections: List[ReportSection]) -> str:
        """Renderizza HTML standard"""
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
    
    def _render_html_corrige(self, sections: List[ReportSection]) -> str:
        """Renderizza HTML in stile Corrige.it"""
        html = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resoconto Ortografia</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f9f9f9;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            margin: -30px -30px 30px -30px;
            border-radius: 8px 8px 0 0;
        }
        
        header h1 {
            font-size: 2em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        header .subtitle {
            opacity: 0.9;
            font-size: 0.95em;
        }
        
        nav {
            background: #f5f5f5;
            padding: 15px;
            margin: 20px -30px;
            border-left: 4px solid #667eea;
        }
        
        nav h2 {
            font-size: 1.2em;
            margin-bottom: 10px;
            color: #667eea;
        }
        
        nav ul {
            list-style: none;
            column-count: 2;
            column-gap: 20px;
        }
        
        nav li {
            margin: 5px 0;
            break-inside: avoid;
        }
        
        nav a {
            color: #555;
            text-decoration: none;
            transition: color 0.2s;
        }
        
        nav a:hover {
            color: #667eea;
        }
        
        nav .count {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            margin-left: 5px;
            min-width: 25px;
            text-align: center;
        }
        
        section {
            margin: 40px 0;
            padding: 20px 0;
            border-top: 2px solid #eee;
        }
        
        section:first-of-type {
            border-top: none;
        }
        
        h2 {
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 15px;
            font-weight: 400;
        }
        
        h3 {
            color: #764ba2;
            font-size: 1.3em;
            margin: 25px 0 10px 0;
            font-weight: 500;
        }
        
        .category-description {
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #667eea;
            margin: 15px 0;
            font-style: italic;
            color: #555;
        }
        
        .correction-item {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
            transition: box-shadow 0.2s;
        }
        
        .correction-item:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .word-header {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .original-word {
            font-size: 1.4em;
            font-weight: 600;
            color: #d63031;
            margin-right: 10px;
        }
        
        .occurrence-count {
            background: #ffe5e5;
            color: #d63031;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.85em;
        }
        
        .corrected-word {
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        
        .corrected-word strong {
            color: #28a745;
        }
        
        .suggestion {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        
        .explanation {
            color: #666;
            font-style: italic;
            margin: 10px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .variants {
            margin: 10px 0;
            padding: 10px;
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            border-radius: 4px;
        }
        
        .context {
            margin: 15px 0;
        }
        
        .context-title {
            font-weight: 600;
            color: #555;
            margin-bottom: 8px;
        }
        
        .context-text {
            background: #f8f9fa;
            padding: 12px;
            border-left: 3px solid #ccc;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            color: #444;
            line-height: 1.5;
            margin: 5px 0;
        }
        
        .buttons {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 8px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.2s;
        }
        
        .btn-correct {
            background: #28a745;
            color: white;
        }
        
        .btn-correct:hover {
            background: #218838;
        }
        
        .btn-error {
            background: #dc3545;
            color: white;
        }
        
        .btn-error:hover {
            background: #c82333;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background: #667eea;
            color: white;
            font-weight: 500;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .stats-box {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .stat-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }
        
        .stat-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-size: 1.8em;
            font-weight: 600;
            color: #667eea;
        }
        
        .info-link {
            display: inline-block;
            margin: 10px 0;
            color: #2196F3;
            text-decoration: none;
        }
        
        .info-link:hover {
            text-decoration: underline;
        }
        
        hr {
            border: none;
            border-top: 1px solid #eee;
            margin: 30px 0;
        }
        
        @media print {
            body { background: white; padding: 0; }
            .container { box-shadow: none; padding: 20px; }
            header { background: #667eea; }
            .correction-item { break-inside: avoid; }
        }
    </style>
</head>
<body>
    <div class="container">
"""
        
        # Aggiungi header
        if sections:
            first_section = sections[0]
            html += f"""
        <header>
            <h1>{first_section.title}</h1>
            <div class="subtitle">{self._markdown_to_text(first_section.content[:200])}</div>
        </header>
"""
        
        # Crea indice di navigazione
        html += """
        <nav>
            <h2>📑 Indice delle Categorie</h2>
            <ul>
"""
        for section in sections[1:]:  # Salta il header
            if section.metadata and 'count' in section.metadata:
                count = section.metadata['count']
                anchor = section.title.lower().replace(' ', '-').replace(',', '')
                html += f'                <li><a href="#{anchor}">{section.title} <span class="count">{count}</span></a></li>\n'
        
        html += """
            </ul>
        </nav>
"""
        
        # Aggiungi sezioni
        for section in sections[1:]:  # Salta il header già renderizzato
            anchor = section.title.lower().replace(' ', '-').replace(',', '')
            html += f'\n        <section id="{anchor}">\n'
            html += f'            <h2>{section.title}</h2>\n'
            
            # Converti il contenuto markdown in HTML
            html_content = self._markdown_to_html_enhanced(section.content)
            html += html_content
            
            html += '        </section>\n'
        
        html += """
    </div>
</body>
</html>
"""
        return html
    
    def _markdown_to_text(self, markdown: str) -> str:
        """Estrae testo pulito da markdown"""
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', markdown)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'`(.*?)`', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        return text.strip()
    
    def _markdown_to_html_enhanced(self, markdown_text: str) -> str:
        """Conversione avanzata Markdown → HTML per stile Corrige"""
        html = markdown_text
        
        # Descrizione categoria (testo in italic all'inizio)
        html = re.sub(r'^\*([^*]+)\*\n', r'<div class="category-description">\1</div>\n', html, flags=re.MULTILINE)
        
        # Titoli h3 (###)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        
        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        
        # Italic
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Code
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        
        # Links
        html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" class="info-link">ℹ️ \1</a>', html)
        
        # Tabelle
        lines = html.split('\n')
        in_table = False
        processed_lines = []
        
        for i, line in enumerate(lines):
            if '|' in line and i + 1 < len(lines) and '|---' in lines[i + 1]:
                # Inizio tabella
                if not in_table:
                    processed_lines.append('<table>')
                    in_table = True
                # Header
                cells = [c.strip() for c in line.split('|')[1:-1]]
                processed_lines.append('<thead><tr>')
                for cell in cells:
                    processed_lines.append(f'<th>{cell}</th>')
                processed_lines.append('</tr></thead><tbody>')
            elif '|---' in line:
                # Salta la linea di separazione
                continue
            elif '|' in line and in_table:
                # Riga dati
                cells = [c.strip() for c in line.split('|')[1:-1]]
                processed_lines.append('<tr>')
                for cell in cells:
                    processed_lines.append(f'<td>{cell}</td>')
                processed_lines.append('</tr>')
            else:
                if in_table and '|' not in line:
                    processed_lines.append('</tbody></table>')
                    in_table = False
                processed_lines.append(line)
        
        if in_table:
            processed_lines.append('</tbody></table>')
        
        html = '\n'.join(processed_lines)
        
        # Liste
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*?</li>\n)+', lambda m: '<ul>\n' + m.group(0) + '</ul>\n', html, flags=re.DOTALL)
        
        # Paragrafi (linee vuote = nuovo paragrafo)
        paragraphs = html.split('\n\n')
        processed = []
        for para in paragraphs:
            para = para.strip()
            if para and not para.startswith('<'):
                processed.append(f'<p>{para}</p>')
            else:
                processed.append(para)
        html = '\n\n'.join(processed)
        
        # Bottoni interattivi
        html = html.replace('[ Corretta ] [ Errore ]', 
                          '<div class="buttons"><button class="btn btn-correct">✓ Corretta</button><button class="btn btn-error">✗ Errore</button></div>')
        
        # Line breaks
        html = html.replace('\n', '<br>\n')
        
        # Pulisci <br> in eccesso
        html = re.sub(r'(<br>\s*){3,}', '<br><br>', html)
        
        return html
    
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
