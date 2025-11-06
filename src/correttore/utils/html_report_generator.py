"""
Generatore Report HTML per Ortografia.

Questo modulo fornisce funzionalità per generare report HTML interattivi
con analisi dettagliata delle correzioni ortografiche, simile a Corrige.it.

Author: Sistema di Correzione Avanzato
Date: 24 Ottobre 2025
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
from pathlib import Path
import json

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

from ..models import CorrectionRecord, CorrectionCategory
from ..core.correction_collector import CorrectionCollector

# Setup logger
logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """
    Generatore di report HTML per analisi ortografica.
    
    Genera report interattivi con:
    - Pagina sintesi con statistiche generali
    - Tabs per ogni categoria di errore
    - Visualizzazione contesti con evidenziazione
    - Export standalone (HTML + CSS + JS inline)
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Inizializza il generatore.
        
        Args:
            templates_dir: Directory dei template Jinja2. Se None, usa default.
        """
        if not JINJA2_AVAILABLE:
            raise ImportError(
                "jinja2 è richiesto per generare report HTML. "
                "Installalo con: pip install jinja2"
            )
        
        # Determina directory templates
        if templates_dir is None:
            # Usa directory relativa al modulo
            current_dir = Path(__file__).parent.parent.parent.parent
            self.templates_dir: Path = current_dir / "templates" / "report"
        else:
            self.templates_dir: Path = Path(templates_dir)
        
        if not self.templates_dir.exists():
            raise FileNotFoundError(f"Directory templates non trovata: {self.templates_dir}")
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
    def generate_report(
        self,
        collector: CorrectionCollector,
        output_path: str,
        document_name: str = "Documento",
        standalone: bool = True,
        show_feedback_buttons: bool = False,
        report_type: str = 'correction',
        use_modern_ui: bool = True
    ) -> str:
        """
        Genera report HTML completo.
        
        Args:
            collector: CorrectionCollector con le correzioni
            output_path: Path di output per il file HTML
            document_name: Nome del documento analizzato
            standalone: Se True, include CSS e JS inline
            show_feedback_buttons: Se True, mostra pulsanti feedback
            report_type: Tipo di report - 'correction' (durante processo) 
                        o 'analysis' (post-correzione)
            use_modern_ui: Se True, usa design system moderno (default: True)
            
        Returns:
            Path del file generato
        """
        # Prepara dati per il template
        data = self._prepare_report_data(
            collector, 
            document_name, 
            show_feedback_buttons,
            report_type
        )
        
        # Carica CSS e JS se standalone
        if standalone:
            if use_modern_ui:
                data['css_content'] = self._load_modern_css()
            else:
                data['css_content'] = self._load_css()
            data['js_content'] = self._load_js()
        else:
            data['css_content'] = ''
            data['js_content'] = ''
        
        # Genera HTML usando template appropriato
        if use_modern_ui:
            html_content = self._render_modern_template(data)
        else:
            html_content = self._render_template(data)
        
        # Salva file
        output_file_path = Path(output_path)
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_file_path)
    
    def _prepare_report_data(
        self,
        collector: CorrectionCollector,
        document_name: str,
        show_feedback_buttons: bool,
        report_type: str = 'correction'
    ) -> Dict[str, Any]:
        """Prepara dizionario dati per il template."""
        
        stats = collector.get_statistics()
        
        # Tabs da mostrare (solo categorie con errori)
        tabs = self._prepare_tabs(collector)
        
        # Dati sintesi
        correction_categories = self._prepare_summary_categories(
            collector,
            is_correction=True
        )
        info_categories = self._prepare_summary_categories(
            collector,
            is_correction=False
        )
        
        # Calcola totali
        total_correction_words = sum(cat['unique_words'] for cat in correction_categories)
        total_correction_contexts = sum(cat['total_contexts'] for cat in correction_categories)
        total_info_words = sum(cat['unique_words'] for cat in info_categories)
        total_info_contexts = sum(cat['total_contexts'] for cat in info_categories)
        
        # Metadati
        processing_time = f"{stats.processing_time:.2f}s" if stats.processing_time > 0 else "N/D"
        
        # Titoli e descrizioni adattati in base al report_type
        if report_type == 'analysis':
            title = f"Analisi Qualità - {document_name}"
            report_subtitle = "Analisi qualità documento"
            summary_title = "Riepilogo Analisi"
            corrections_label = "Problemi Identificati"
            info_label = "Segnalazioni Informative"
        else:  # 'correction' (default)
            title = f"Report Correzione - {document_name}"
            report_subtitle = "Report del processo di correzione"
            summary_title = "Riepilogo Correzioni"
            corrections_label = "Correzioni Applicate"
            info_label = "Segnalazioni Informative"
        
        return {
            'title': title,
            'report_subtitle': report_subtitle,
            'summary_title': summary_title,
            'corrections_label': corrections_label,
            'info_label': info_label,
            'document_name': document_name,
            'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'generation_time': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'tabs': tabs,
            'correction_categories': correction_categories,
            'info_categories': info_categories,
            'total_correction_words': total_correction_words,
            'total_correction_contexts': total_correction_contexts,
            'total_info_words': total_info_words,
            'total_info_contexts': total_info_contexts,
            'processing_time': processing_time,
            'total_words': stats.total_words_checked,
            'total_contexts': stats.total_corrections,
            'system_info': "Correttore AI v1.0",
            'processing_date': datetime.now().strftime("%d/%m/%Y"),
            'version': "1.0.0",
            'show_feedback_buttons': show_feedback_buttons,
            'category_tabs': self._prepare_category_tabs(collector, show_feedback_buttons),
            
            # Dati per grafici
            'chart_labels': [cat['name'] for cat in correction_categories if cat['total_contexts'] > 0],
            'chart_values': [cat['total_contexts'] for cat in correction_categories if cat['total_contexts'] > 0],
            'chart_words': [cat['unique_words'] for cat in correction_categories if cat['total_contexts'] > 0],
            'chart_contexts': [cat['total_contexts'] for cat in correction_categories if cat['total_contexts'] > 0],
        }
    
    def _prepare_tabs(self, collector: CorrectionCollector) -> List[Dict[str, Any]]:
        """Prepara lista tabs da mostrare."""
        tabs = [
            {
                'id': 'sintesi',
                'icon': '📊',
                'label': 'Sintesi',
                'count': 0
            }
        ]
        
        # Mappa categorie (NOMI ESATTI da Corrige.it)
        category_map = {
            CorrectionCategory.ERRORI_RICONOSCIUTI: ('errori', '❌', 'Errori di ortografia o grammatica riconosciuti'),
            CorrectionCategory.SCONOSCIUTE: ('sconosciute', '❓', 'Sconosciute: parole non riconosciute'),
            CorrectionCategory.SOSPETTE: ('sospette', '⚠️', 'Sospette'),
            CorrectionCategory.MIGLIORABILI: ('migliorabili', '✨', 'Migliorabili'),
            CorrectionCategory.PUNTEGGIATURA: ('punteggiatura', '🔣', 'Punteggiatura'),
            CorrectionCategory.IMBARAZZANTI: ('imbarazzanti', '😳', 'Imbarazzanti'),
            CorrectionCategory.VARIANTI: ('varianti', '↔️', 'Varianti'),
            CorrectionCategory.NOMI_SIGLE: ('nomi', '👤', 'Nomi propri, sigle ecc.'),
            CorrectionCategory.LINGUE: ('lingue', '🌐', 'Parole di altre lingue'),
            CorrectionCategory.CON_INFO: ('info', 'ℹ️', 'Con info'),
        }
        
        # Aggiungi tabs per categorie con errori
        for category in CorrectionCategory:
            corrections = collector.get_by_category(category)
            if corrections:
                tab_id, icon, label = category_map.get(
                    category,
                    (category.name.lower(), '📝', category.name)
                )
                tabs.append({
                    'id': tab_id,
                    'icon': icon,
                    'label': label,
                    'count': len(corrections)
                })
        
        return tabs
    
    def _prepare_summary_categories(
        self,
        collector: CorrectionCollector,
        is_correction: bool
    ) -> List[Dict[str, Any]]:
        """Prepara dati categorie per tabella sintesi."""
        
        # Categorie di correzione vs informazione
        if is_correction:
            categories = [
                CorrectionCategory.ERRORI_RICONOSCIUTI,
                CorrectionCategory.SCONOSCIUTE,
                CorrectionCategory.SOSPETTE,
                CorrectionCategory.MIGLIORABILI,
                CorrectionCategory.PUNTEGGIATURA,
            ]
        else:
            categories = [
                CorrectionCategory.IMBARAZZANTI,
                CorrectionCategory.VARIANTI,
                CorrectionCategory.NOMI_SIGLE,
                CorrectionCategory.LINGUE,
                CorrectionCategory.CON_INFO,
            ]
        
        # Icone per categoria
        icons = {
            CorrectionCategory.ERRORI_RICONOSCIUTI: '❌',
            CorrectionCategory.SCONOSCIUTE: '❓',
            CorrectionCategory.SOSPETTE: '⚠️',
            CorrectionCategory.MIGLIORABILI: '✨',
            CorrectionCategory.PUNTEGGIATURA: '🔣',
            CorrectionCategory.IMBARAZZANTI: '😳',
            CorrectionCategory.VARIANTI: '↔️',
            CorrectionCategory.NOMI_SIGLE: '👤',
            CorrectionCategory.LINGUE: '🌐',
            CorrectionCategory.CON_INFO: 'ℹ️',
        }
        
        # Nomi user-friendly
        names = {
            CorrectionCategory.ERRORI_RICONOSCIUTI: 'Errori riconosciuti',
            CorrectionCategory.SCONOSCIUTE: 'Sconosciute',
            CorrectionCategory.SOSPETTE: 'Sospette',
            CorrectionCategory.MIGLIORABILI: 'Migliorabili',
            CorrectionCategory.PUNTEGGIATURA: 'Punteggiatura',
            CorrectionCategory.IMBARAZZANTI: 'Imbarazzanti',
            CorrectionCategory.VARIANTI: 'Varianti',
            CorrectionCategory.NOMI_SIGLE: 'Nomi/Sigle',
            CorrectionCategory.LINGUE: 'Lingue',
            CorrectionCategory.CON_INFO: 'Con altre informazioni',
        }
        
        result = []
        for category in categories:
            corrections = collector.get_by_category(category)
            
            # Conta parole uniche
            unique_words = len(set(c.original_text.lower() for c in corrections))
            
            # Raggruppa correzioni per parola
            words_dict = defaultdict(list)
            for correction in corrections:
                word = correction.original_text
                words_dict[word].append({
                    'context': correction.context or '',
                    'message': correction.message or '',
                    'suggestion': correction.corrected_text or ''
                })
            
            result.append({
                'id': category.name,
                'icon': icons.get(category, '📝'),
                'name': names.get(category, category.name),
                'unique_words': unique_words,
                'total_contexts': len(corrections),
                'words': dict(words_dict)  # Converti defaultdict a dict per template
            })
        
        return result
    
    def _prepare_category_tabs(
        self,
        collector: CorrectionCollector,
        show_feedback_buttons: bool
    ) -> List[str]:
        """Genera HTML per ogni tab categoria."""
        
        category_map = {
            CorrectionCategory.ERRORI_RICONOSCIUTI: {
                'id': 'errori',
                'icon': '❌',
                'name': 'Errori Riconosciuti',
                'description': 'Errori ortografici e grammaticali identificati con certezza.',
                'info': 'Queste segnalazioni indicano errori che devono essere corretti.'
            },
            CorrectionCategory.SCONOSCIUTE: {
                'id': 'sconosciute',
                'icon': '❓',
                'name': 'Parole Sconosciute',
                'description': 'Parole non presenti nel dizionario ma potenzialmente corrette.',
                'info': 'Potrebbero essere nomi propri, neologismi, o termini tecnici.'
            },
            CorrectionCategory.SOSPETTE: {
                'id': 'sospette',
                'icon': '⚠️',
                'name': 'Parole Sospette',
                'description': 'Parole corrette ma contestualmente insolite.',
                'info': 'Verificare se la parola usata è quella intesa.'
            },
            CorrectionCategory.MIGLIORABILI: {
                'id': 'migliorabili',
                'icon': '✨',
                'name': 'Espressioni Migliorabili',
                'description': 'Espressioni corrette ma migliorabili per stile.',
                'info': 'Suggerimenti per rendere il testo più professionale.'
            },
            CorrectionCategory.PUNTEGGIATURA: {
                'id': 'punteggiatura',
                'icon': '🔣',
                'name': 'Punteggiatura',
                'description': 'Errori o suggerimenti relativi alla punteggiatura.',
                'info': 'Include virgole, apostrofi, spazi, e altri segni.'
            },
            CorrectionCategory.IMBARAZZANTI: {
                'id': 'imbarazzanti',
                'icon': '😳',
                'name': 'Parole Imbarazzanti',
                'description': 'Parole corrette ma potenzialmente imbarazzanti.',
                'info': 'Indicazione puramente linguistica, nessun giudizio morale.'
            },
            CorrectionCategory.VARIANTI: {
                'id': 'varianti',
                'icon': '↔️',
                'name': 'Varianti',
                'description': 'Forme alternative accettabili della stessa parola.',
                'info': 'Entrambe le forme sono corrette.'
            },
            CorrectionCategory.NOMI_SIGLE: {
                'id': 'nomi',
                'icon': '👤',
                'name': 'Nomi e Sigle',
                'description': 'Nomi propri, sigle e acronimi riconosciuti.',
                'info': 'Lista di nomi propri identificati nel testo.'
            },
            CorrectionCategory.LINGUE: {
                'id': 'lingue',
                'icon': '🌐',
                'name': 'Parole Straniere',
                'description': 'Parole in altre lingue identificate nel testo.',
                'info': 'Considerare se tradurre o mantenere.'
            },
            CorrectionCategory.CON_INFO: {
                'id': 'info',
                'icon': 'ℹ️',
                'name': 'Con Altre Informazioni',
                'description': 'Segnalazioni con informazioni aggiuntive.',
                'info': 'Note e commenti vari sul testo.'
            },
        }
        
        tabs_html = []
        
        for category in CorrectionCategory:
            corrections = collector.get_by_category(category)
            if not corrections:
                continue
            
            cat_info = category_map.get(category, {
                'id': category.name.lower(),
                'icon': '📝',
                'name': category.name,
                'description': '',
                'info': ''
            })
            
            # Raggruppa per parola
            errors_by_word = self._group_by_word(corrections)
            
            # Prepara dati per template
            template_data = {
                'category_id': cat_info['id'],
                'category_icon': cat_info['icon'],
                'category_name': cat_info['name'],
                'category_description': cat_info['description'],
                'category_info': cat_info['info'],
                'unique_words': len(errors_by_word),
                'total_occurrences': len(corrections),
                'errors_by_type': errors_by_word,
                'show_feedback_buttons': show_feedback_buttons,
            }
            
            # Renderizza template categoria
            template = self.env.get_template('categoria.html')
            tab_html = template.render(**template_data)
            tabs_html.append(tab_html)
        
        return tabs_html
    
    def _group_by_word(self, corrections: List[CorrectionRecord]) -> List[Dict[str, Any]]:
        """Raggruppa correzioni per parola."""
        
        grouped = defaultdict(list)
        for correction in corrections:
            key = correction.original_text.lower()
            grouped[key].append(correction)
        
        result = []
        for word, group in sorted(grouped.items()):
            # Prendi suggerimento più comune
            suggestions = [c.corrected_text for c in group if c.corrected_text]
            main_suggestion = max(set(suggestions), key=suggestions.count) if suggestions else None
            
            # Prendi messaggio più comune
            messages = [c.message for c in group if c.message]
            main_message = max(set(messages), key=messages.count) if messages else None
            
            # Tutte le alternative
            all_suggestions = sorted(set(s for s in suggestions if s))
            
            # Prepara occorrenze
            occurrences = []
            for i, corr in enumerate(group, 1):
                # Estrai contesto prima e dopo (max 50 caratteri)
                context_before = corr.context[:corr.position][-50:] if corr.position > 0 else ""
                context_after = corr.context[corr.position + len(corr.original_text):][:50] if corr.position >= 0 else ""
                
                occurrences.append({
                    'id': corr.id,
                    'word': corr.original_text,
                    'paragraph': corr.paragraph_index + 1 if corr.paragraph_index >= 0 else '?',
                    'sentence': corr.sentence_index + 1 if corr.sentence_index >= 0 else '?',
                    'context_before': context_before,
                    'context_after': context_after,
                })
            
            result.append({
                'id': f"error_{word.replace(' ', '_')}",
                'word': word,
                'suggestion': main_suggestion,
                'message': main_message,
                'suggestions': all_suggestions,
                'count': len(group),
                'occurrences': occurrences,
            })
        
        return result
    
    def _render_template(self, data: Dict[str, Any]) -> str:
        """Renderizza template completo."""
        
        # Template base
        base_template = self.env.get_template('base.html')
        
        # Template sintesi
        sintesi_template = self.env.get_template('sintesi.html')
        sintesi_content = sintesi_template.render(**data)
        
        # Combina sintesi + tabs categorie
        all_tabs_content = sintesi_content
        for tab_html in data.get('category_tabs', []):
            all_tabs_content += tab_html
        
        # Renderizza base con tutto il contenuto
        data['content'] = all_tabs_content
        return base_template.render(**data)
    
    def _load_css(self) -> str:
        """Carica contenuto CSS."""
        css_path: Path = self.templates_dir / "assets" / "report.css"
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _load_js(self) -> str:
        """Carica contenuto JavaScript."""
        js_path: Path = self.templates_dir / "assets" / "report.js"
        if js_path.exists():
            with open(js_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def generate_modern_report(
        self,
        collector: CorrectionCollector,
        output_path: str,
        document_name: str = "Documento",
        readability_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Genera report HTML moderno con design system professionale.
        
        Args:
            collector: CorrectionCollector con le correzioni
            output_path: Path di output per il file HTML
            document_name: Nome del documento analizzato
            readability_data: Dati di leggibilità (opzionale)
            
        Returns:
            Path del file generato
        """
        try:
            # Carica template moderno
            template = self.env.get_template('analysis_modern.html')
            
            # Prepara dati
            stats = collector.get_statistics()
            
            # Raggruppa correzioni per categoria
            corrections_by_category = {}
            for category in CorrectionCategory:
                records = collector.get_by_category(category)
                if records:
                    corrections_by_category[category.value] = records
            
            # Raggruppa parole straniere per lingua
            foreign_languages = {}
            for record in collector.get_all_corrections():
                if record.category == CorrectionCategory.LINGUE:
                    lang = "Foreign Language"
                    if lang not in foreign_languages:
                        foreign_languages[lang] = []
                    foreign_languages[lang].append(record.original_text)
            
            # Dati readability
            readability = None
            if readability_data:
                readability = {
                    'score': readability_data.get('gulpease_score', 0),
                    'level': readability_data.get('difficulty_level', 'Unknown')
                }
            
            # Render template
            html_content = template.render(
                document_name=document_name,
                timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                stats={
                    'total_errors': stats.total_corrections,
                    'foreign_words': len(foreign_languages),
                    'readability_score': readability['score'] if readability else 0,
                    'total_words': stats.total_words_checked
                },
                corrections_by_category=corrections_by_category,
                foreign_languages=foreign_languages,
                readability=readability
            )
            
            # Salva file
            output_file_path = Path(output_path)
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return str(output_file_path)
            
        except Exception as e:
            # Fallback al metodo tradizionale
            return self.generate_report(
                collector=collector,
                output_path=output_path,
                document_name=document_name,
                standalone=True,
                show_feedback_buttons=False,
                report_type='analysis'
            )

    def _load_modern_css(self) -> str:
        """
        Carica CSS moderno dal design system.
        
        Returns:
            CSS concatenato (tokens + reset + components)
        """
        try:
            # Path ai file CSS moderni
            css_dir = Path(__file__).parent.parent / "web" / "styles"
            
            css_files = [
                css_dir / "tokens.css",
                css_dir / "reset.css",
                css_dir / "components.css"
            ]
            
            css_content = []
            for css_file in css_files:
                if css_file.exists():
                    with open(css_file, 'r', encoding='utf-8') as f:
                        css_content.append(f.read())
            
            return "\n\n".join(css_content)
            
        except Exception as e:
            # Fallback a CSS legacy
            return self._load_css()
    
    def _render_modern_template(self, data: Dict[str, Any]) -> str:
        """
        Renderizza template HTML con design moderno usando Jinja2.
        
        Args:
            data: Dizionario con tutti i dati del report
            
        Returns:
            HTML completo con stili moderni
        """
        try:
            # Carica template Jinja2 moderno
            template = self.env.get_template('analysis_modern.html')
            
            # Prepara statistiche per template
            stats = {
                'total_errors': data['total_correction_contexts'],
                'foreign_words': sum(1 for cat in data['info_categories'] if cat['name'] == 'Lingue'),
                'unique_words': data['total_correction_words'],
                'total_issues': data['total_contexts']
            }
            
            # Estrai parole straniere
            foreign_words = []
            for category in data['info_categories']:
                if category['name'] == 'Lingue':
                    # Raccogli tutte le parole dalla categoria Lingue
                    for word in category.get('words', {}).keys():
                        foreign_words.append(word)
            
            # Renderizza template
            html_content = template.render(
                document_name=data['document_name'],
                timestamp=data['timestamp'],
                stats=stats,
                correction_categories=data['correction_categories'],
                info_categories=data['info_categories'],
                foreign_words=foreign_words,
                css_content=data.get('css_content', ''),
                js_content=data.get('js_content', '')
            )
            
            return html_content
            
        except Exception as e:
            # Fallback: genera HTML semplice se template non disponibile
            logger.error(f"Error rendering modern template: {e}")
            return self._render_fallback_html(data)
    
    def _render_fallback_html(self, data: Dict[str, Any]) -> str:
        """Genera HTML di fallback se il template Jinja2 fallisce."""
        stats = {
            'errori': data['total_correction_contexts'],
            'lingue': sum(1 for cat in data['info_categories'] if cat['name'] == 'Lingue'),
            'parole_uniche': data['total_correction_words'],
            'totale': data['total_contexts']
        }
        
        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['title']}</title>
    <style>
        {data['css_content']}
    </style>
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1 class="report-title">{data['title']}</h1>
            <p class="report-subtitle">Generato il {data['timestamp']}</p>
        </header>
        
        {self._render_metrics_grid(stats)}
        {self._render_errors_section(data)}
        {self._render_foreign_section(data)}
        {self._render_info_section(data)}
    </div>
    
    <script>
        {data['js_content']}
    </script>
</body>
</html>"""
        
        return html
    
    def _render_metrics_grid(self, stats: Dict[str, int]) -> str:
        """Renderizza griglia metriche con stile moderno."""
        return f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Errors</div>
                <div class="metric-value error">{stats['errori']}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Foreign Words</div>
                <div class="metric-value info">{stats['lingue']}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Unique Words</div>
                <div class="metric-value warning">{stats['parole_uniche']}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Issues</div>
                <div class="metric-value">{stats['totale']}</div>
            </div>
        </div>
        """
    
    def _render_errors_section(self, data: Dict[str, Any]) -> str:
        """Renderizza sezione errori con stile moderno."""
        if not data['correction_categories']:
            return ""
        
        html_parts = ['<section class="section">']
        html_parts.append('<h2 class="section-title">📝 Corrections Applied</h2>')
        
        for category in data['correction_categories']:
            if category['total_contexts'] == 0:
                continue
            
            html_parts.append(f"""
            <div class="error-card">
                <div class="error-header">
                    <span class="error-badge error">{category['name']}</span>
                    <span class="error-location">{category['unique_words']} unique words, {category['total_contexts']} contexts</span>
                </div>
                <div class="error-message">
                    Category contains corrections for common errors in this category.
                </div>
            </div>
            """)
        
        html_parts.append('</section>')
        return "\n".join(html_parts)
    
    def _render_foreign_section(self, data: Dict[str, Any]) -> str:
        """Renderizza sezione lingue straniere con stile moderno."""
        lingue_cat = next((cat for cat in data['info_categories'] if cat['name'] == 'Lingue'), None)
        
        if not lingue_cat or lingue_cat['total_contexts'] == 0:
            return ""
        
        html = f"""
        <section class="section">
            <h2 class="section-title">🌐 Foreign Languages Detected</h2>
            <div class="foreign-group">
                <div class="foreign-header">
                    <span class="foreign-title">Foreign Words</span>
                    <span class="foreign-count">{lingue_cat['total_contexts']} words</span>
                </div>
                <p style="font-size: 0.875rem; color: #6b7280; margin-top: 0.5rem;">
                    These words were identified as foreign language terms and excluded from Italian spell checking.
                </p>
            </div>
        </section>
        """
        
        return html
    
    def _render_info_section(self, data: Dict[str, Any]) -> str:
        """Renderizza sezione informativa con stile moderno."""
        info_cats = [cat for cat in data['info_categories'] 
                     if cat['total_contexts'] > 0 and cat['name'] != 'Lingue']
        
        if not info_cats:
            return ""
        
        html_parts = ['<section class="section">']
        html_parts.append('<h2 class="section-title">ℹ️ Additional Information</h2>')
        
        for category in info_cats:
            html_parts.append(f"""
            <div class="error-card info">
                <div class="error-header">
                    <span class="error-badge warning">{category['name']}</span>
                    <span class="error-location">{category['unique_words']} unique words</span>
                </div>
            </div>
            """)
        
        html_parts.append('</section>')
        return "\n".join(html_parts)


def generate_orthography_report(
    collector: CorrectionCollector,
    output_path: str,
    document_name: str = "Documento",
    standalone: bool = True,
    show_feedback_buttons: bool = False
) -> str:
    """
    Funzione di utilità per generare report ortografia.
    
    Args:
        collector: CorrectionCollector con le correzioni
        output_path: Path di output per il file HTML
        document_name: Nome del documento analizzato
        standalone: Se True, include CSS e JS inline
        show_feedback_buttons: Se True, mostra pulsanti feedback
        
    Returns:
        Path del file generato
        
    Example:
        >>> from correttore.core.correction_collector import CorrectionCollector
        >>> collector = CorrectionCollector()
        >>> # ... aggiungi correzioni ...
        >>> path = generate_orthography_report(
        ...     collector,
        ...     "outputs/report.html",
        ...     "Il mio documento"
        ... )
    """
    generator = HTMLReportGenerator()
    return generator.generate_report(
        collector,
        output_path,
        document_name,
        standalone,
        show_feedback_buttons
    )


def generate_analysis_report(
    collector: CorrectionCollector,
    output_path: str,
    document_name: str = "Documento",
    standalone: bool = True,
    use_modern_ui: bool = True
) -> str:
    """
    Funzione di utilità per generare report di analisi qualità.
    
    Wrapper di generate_report() con report_type='analysis'.
    Usato per report post-correzione che mostrano problemi residui.
    
    Args:
        collector: CorrectionCollector con i problemi identificati
        output_path: Path di output per il file HTML
        document_name: Nome del documento analizzato
        standalone: Se True, include CSS e JS inline
        use_modern_ui: Se True, usa design system moderno (default: True)
        
    Returns:
        Path del file generato
        
    Example:
        >>> from correttore.core.correction_collector import CorrectionCollector
        >>> from correttore.core.document_analyzer import DocumentAnalyzer
        >>> 
        >>> analyzer = DocumentAnalyzer()
        >>> result = analyzer.analyze_document("documento.docx")
        >>> # Il report viene generato automaticamente
        >>> # oppure manualmente:
        >>> path = generate_analysis_report(
        ...     result.collector,
        ...     "outputs/analysis.html",
        ...     "documento.docx"
        ... )
    """
    generator = HTMLReportGenerator()
    return generator.generate_report(
        collector=collector,
        output_path=output_path,
        document_name=document_name,
        standalone=standalone,
        show_feedback_buttons=False,  # No feedback per analisi
        report_type='analysis',
        use_modern_ui=use_modern_ui
    )
