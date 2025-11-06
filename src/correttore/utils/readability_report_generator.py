# readability_report_generator.py
"""
Generatore di report HTML per l'analisi di leggibilità frase per frase.
Implementa la visualizzazione avanzata con statistiche, grafici e tabelle interattive.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .readability import ReadabilityAnalyzer, SentenceReadability


class ReadabilityReportGenerator:
    """Generatore di report HTML per analisi di leggibilità avanzata"""
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Inizializza il generatore di report.
        
        Args:
            template_dir: Directory dei template (default: templates/)
        """
        self.template_dir = template_dir or Path(__file__).parent.parent.parent.parent / "templates"
        self.analyzer = ReadabilityAnalyzer()
    
    def generate_report(
        self,
        text: str,
        output_path: str,
        vocabulary_service=None,
        document_title: str = "Documento"
    ) -> str:
        """
        Genera un report HTML completo di leggibilità.
        
        Args:
            text: Il testo da analizzare
            output_path: Percorso del file HTML di output
            vocabulary_service: Servizio opzionale per verificare parole nel VdB
            document_title: Titolo del documento analizzato
            
        Returns:
            Percorso del file HTML generato
        """
        # Analisi globale
        global_stats = self.analyzer.analyze(text)
        
        # Analisi frase per frase
        sentences = self.analyzer.analyze_by_sentence(text, vocabulary_service)
        sentence_stats = self.analyzer.get_sentence_statistics(sentences)
        
        # Raccogli parole non nel VdB
        words_not_in_vdb = self._collect_vocabulary_words(sentences)
        
        # Analisi vocabolario avanzata (Fase 4)
        vocab_breakdown = None
        if vocabulary_service:
            vocab_breakdown = vocabulary_service.get_vocabulary_breakdown(text)
        
        # Genera HTML
        html_content = self._generate_html(
            global_stats=global_stats,
            sentences=sentences,
            sentence_stats=sentence_stats,
            words_not_in_vdb=words_not_in_vdb,
            vocab_breakdown=vocab_breakdown,
            document_title=document_title
        )
        
        # Salva file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html_content, encoding='utf-8')
        
        return str(output_file)
    
    def _collect_vocabulary_words(self, sentences: List[SentenceReadability]) -> Dict[str, int]:
        """
        Raccoglie tutte le parole non nel VdB con la loro frequenza.
        
        Args:
            sentences: Lista di analisi delle frasi
            
        Returns:
            Dizionario {parola: frequenza}
        """
        word_freq = {}
        for sentence in sentences:
            for word in sentence.words_not_in_vdb:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Ordina per frequenza decrescente
        return dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True))
    
    def _generate_html(
        self,
        global_stats: Dict[str, Any],
        sentences: List[SentenceReadability],
        sentence_stats: Dict[str, Any],
        words_not_in_vdb: Dict[str, int],
        vocab_breakdown: Optional[Dict[str, Any]],
        document_title: str
    ) -> str:
        """
        Genera il contenuto HTML completo del report.
        
        Args:
            global_stats: Statistiche globali del documento
            sentences: Lista analisi frasi
            sentence_stats: Statistiche aggregate sulle frasi
            words_not_in_vdb: Parole non nel vocabolario di base
            vocab_breakdown: Breakdown dettagliato vocabolario per livello (Fase 4)
            document_title: Titolo del documento
            
        Returns:
            Contenuto HTML completo
        """
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Report Leggibilità - {document_title}</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1>📊 Report di Leggibilità</h1>
            <div class="document-info">
                <h2>{document_title}</h2>
                <p class="timestamp">Generato il {timestamp}</p>
            </div>
        </header>
        
        <nav class="tabs">
            <button class="tab-button active" data-tab="sintesi">Sintesi</button>
            <button class="tab-button" data-tab="frasi">Analisi Frasi</button>
            <button class="tab-button" data-tab="vocabolario">Vocabolario</button>
            <button class="tab-button" data-tab="grafici">Grafici</button>
        </nav>
        
        <div class="tab-content active" id="tab-sintesi">
            {self._generate_summary_section(global_stats, sentence_stats)}
        </div>
        
        <div class="tab-content" id="tab-frasi">
            {self._generate_sentences_section(sentences)}
        </div>
        
        <div class="tab-content" id="tab-vocabolario">
            {self._generate_vocabulary_section(words_not_in_vdb, global_stats, vocab_breakdown)}
        </div>
        
        <div class="tab-content" id="tab-grafici">
            {self._generate_charts_section(sentence_stats, sentences, vocab_breakdown)}
        </div>
    </div>
    
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>"""
        
        return html
    
    def _generate_summary_section(
        self,
        global_stats: Dict[str, Any],
        sentence_stats: Dict[str, Any]
    ) -> str:
        """Genera la sezione sintesi"""
        gulpease = global_stats.get('gulpease', 0)
        difficulty_color = self._get_difficulty_color(gulpease)
        
        distribution = sentence_stats.get('distribution', {})
        total_sentences = sentence_stats.get('total_sentences', 0)
        
        return f"""
        <section class="summary-section">
            <div class="big-score" style="border-color: {difficulty_color};">
                <div class="score-value" style="color: {difficulty_color};">{gulpease:.1f}</div>
                <div class="score-label">Indice GULPEASE</div>
                <div class="score-difficulty">{self._get_difficulty_label(gulpease)}</div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">📝</div>
                    <div class="stat-value">{global_stats['words']:,}</div>
                    <div class="stat-label">Parole Totali</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-icon">📄</div>
                    <div class="stat-value">{total_sentences}</div>
                    <div class="stat-label">Frasi Totali</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-icon">📏</div>
                    <div class="stat-value">{sentence_stats.get('avg_words_per_sentence', 0):.1f}</div>
                    <div class="stat-label">Parole/Frase (Media)</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-icon">🔤</div>
                    <div class="stat-value">{global_stats['avg_word_length']:.1f}</div>
                    <div class="stat-label">Lettere/Parola (Media)</div>
                </div>
            </div>
            
            <div class="distribution-summary">
                <h3>Distribuzione Difficoltà Frasi</h3>
                <div class="distribution-bars">
                    {self._generate_distribution_bar("Molto Facili", distribution.get('very_easy', 0), total_sentences, '#2d5016')}
                    {self._generate_distribution_bar("Facili", distribution.get('easy', 0), total_sentences, '#4a7c2c')}
                    {self._generate_distribution_bar("Difficili", distribution.get('difficult', 0), total_sentences, '#f39c12')}
                    {self._generate_distribution_bar("Molto Difficili", distribution.get('very_difficult', 0), total_sentences, '#c0392b')}
                </div>
            </div>
            
            <div class="interpretation-box">
                <h3>Interpretazione secondo Scolarizzazione</h3>
                <table class="interpretation-table">
                    <thead>
                        <tr>
                            <th>Livello di Scolarizzazione</th>
                            <th>Difficoltà</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Licenza Elementare</td>
                            <td><strong>{global_stats['difficulty'].get('licenza_elementare', 'N/A')}</strong></td>
                        </tr>
                        <tr>
                            <td>Licenza Media</td>
                            <td><strong>{global_stats['difficulty'].get('licenza_media', 'N/A')}</strong></td>
                        </tr>
                        <tr>
                            <td>Diploma Superiore</td>
                            <td><strong>{global_stats['difficulty'].get('diploma_superiore', 'N/A')}</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>
        """
    
    def _generate_distribution_bar(self, label: str, count: int, total: int, color: str) -> str:
        """Genera una barra di distribuzione"""
        percentage = (count / total * 100) if total > 0 else 0
        return f"""
        <div class="distribution-item">
            <div class="distribution-label">
                <span>{label}</span>
                <span class="distribution-count">{count} ({percentage:.1f}%)</span>
            </div>
            <div class="distribution-bar-bg">
                <div class="distribution-bar-fill" style="width: {percentage}%; background-color: {color};"></div>
            </div>
        </div>
        """
    
    def _generate_sentences_section(self, sentences: List[SentenceReadability]) -> str:
        """Genera la sezione analisi frasi"""
        if not sentences:
            return "<p>Nessuna frase da analizzare.</p>"
        
        rows = []
        for sentence in sentences:
            color = sentence.get_difficulty_color()
            emoji = sentence.get_difficulty_emoji()
            
            # Evidenzia parole difficili nel testo
            text_html = self._highlight_difficult_words(sentence.text, sentence.words_not_in_vdb)
            
            rows.append(f"""
            <tr>
                <td class="sentence-num">{sentence.sentence_index}</td>
                <td class="sentence-text">{text_html}</td>
                <td class="sentence-score" style="color: {color}; font-weight: bold;">
                    {emoji} {sentence.gulpease_score:.1f}
                </td>
                <td class="sentence-difficulty">{sentence.difficulty_level}</td>
                <td class="sentence-words">{sentence.word_count}</td>
                <td class="sentence-vdb">{len(sentence.words_not_in_vdb)}</td>
            </tr>
            """)
        
        return f"""
        <section class="sentences-section">
            <div class="section-header">
                <h2>Analisi Frase per Frase</h2>
                <div class="filter-controls">
                    <label>Filtra: </label>
                    <button class="filter-btn active" data-filter="all">Tutte</button>
                    <button class="filter-btn" data-filter="easy">Facili</button>
                    <button class="filter-btn" data-filter="difficult">Difficili</button>
                    <button class="filter-btn" data-filter="very-difficult">Molto Difficili</button>
                </div>
            </div>
            
            <div class="table-wrapper">
                <table class="sentences-table" id="sentences-table">
                    <thead>
                        <tr>
                            <th class="sortable" data-sort="index"># Frase</th>
                            <th>Testo</th>
                            <th class="sortable" data-sort="score">GULPEASE</th>
                            <th>Difficoltà</th>
                            <th class="sortable" data-sort="words">Parole</th>
                            <th class="sortable" data-sort="vdb">Parole non-VdB</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows)}
                    </tbody>
                </table>
            </div>
            
            <div class="legend">
                <h4>Legenda Difficoltà:</h4>
                <span class="legend-item">📗 Molto Facile (80-100)</span>
                <span class="legend-item">📘 Facile (60-79)</span>
                <span class="legend-item">📙 Difficile (40-59)</span>
                <span class="legend-item">📕 Molto Difficile (0-39)</span>
            </div>
        </section>
        """
    
    def _highlight_difficult_words(self, text: str, difficult_words: List[str]) -> str:
        """Evidenzia le parole difficili nel testo"""
        if not difficult_words:
            return text
        
        highlighted = text
        for word in difficult_words:
            # Usa word boundary per evitare match parziali
            import re
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            highlighted = pattern.sub(f'<mark class="difficult-word">{word}</mark>', highlighted)
        
        return highlighted
    
    def _generate_vocabulary_section(
        self,
        words_not_in_vdb: Dict[str, int],
        global_stats: Dict[str, Any],
        vocab_breakdown: Optional[Dict[str, Any]] = None
    ) -> str:
        """Genera la sezione vocabolario con analisi avanzata (Fase 4 + Sprint 2)"""
        total_words = global_stats.get('words', 0)
        unique_difficult = len(words_not_in_vdb)
        total_difficult = sum(words_not_in_vdb.values())
        
        coverage = ((total_words - total_difficult) / total_words * 100) if total_words > 0 else 0
        
        # Analizza parole con VocabularyService per ottenere alternative (Sprint 2)
        word_details = self._analyze_difficult_words_with_alternatives(
            words_not_in_vdb, 
            vocab_breakdown
        )
        
        # Statistiche avanzate VdB (Fase 4)
        vdb_stats_html = ""
        if vocab_breakdown:
            fondamentale = vocab_breakdown.get('fondamentale', {})
            alto_uso = vocab_breakdown.get('alto_uso', {})
            alta_disp = vocab_breakdown.get('alta_disponibilita', {})
            non_classificato = vocab_breakdown.get('non_classificato', {})
            fuori_vdb = vocab_breakdown.get('fuori_vdb', {})
            
            vdb_stats_html = f"""
            <div class="vdb-breakdown">
                <h3>📊 Distribuzione per Livello Vocabolario di Base</h3>
                <div class="vdb-breakdown-grid">
                    <div class="vdb-level-card" style="border-left-color: #2ecc71;">
                        <div class="vdb-level-name">📗 Fondamentali</div>
                        <div class="vdb-level-count">{fondamentale.get('count', 0)} parole</div>
                        <div class="vdb-level-percentage">{fondamentale.get('percentage', 0):.1f}%</div>
                        <div class="vdb-level-description">Parole di base, comprensibili da tutti</div>
                    </div>
                    <div class="vdb-level-card" style="border-left-color: #3498db;">
                        <div class="vdb-level-name">📘 Alto Uso</div>
                        <div class="vdb-level-count">{alto_uso.get('count', 0)} parole</div>
                        <div class="vdb-level-percentage">{alto_uso.get('percentage', 0):.1f}%</div>
                        <div class="vdb-level-description">Parole comuni nella lingua scritta</div>
                    </div>
                    <div class="vdb-level-card" style="border-left-color: #f39c12;">
                        <div class="vdb-level-name">📙 Alta Disponibilità</div>
                        <div class="vdb-level-count">{alta_disp.get('count', 0)} parole</div>
                        <div class="vdb-level-percentage">{alta_disp.get('percentage', 0):.1f}%</div>
                        <div class="vdb-level-description">Parole note ma meno frequenti</div>
                    </div>
                    <div class="vdb-level-card" style="border-left-color: #95a5a6;">
                        <div class="vdb-level-name">📒 Non Classificate</div>
                        <div class="vdb-level-count">{non_classificato.get('count', 0)} parole</div>
                        <div class="vdb-level-percentage">{non_classificato.get('percentage', 0):.1f}%</div>
                        <div class="vdb-level-description">Nel vocabolario ma senza livello assegnato</div>
                    </div>
                    <div class="vdb-level-card" style="border-left-color: #e74c3c;">
                        <div class="vdb-level-name">📕 Fuori VdB</div>
                        <div class="vdb-level-count">{fuori_vdb.get('count', 0)} parole</div>
                        <div class="vdb-level-percentage">{fuori_vdb.get('percentage', 0):.1f}%</div>
                        <div class="vdb-level-description">Parole specialistiche o rare</div>
                    </div>
                </div>
                
                <div class="vdb-chart-container">
                    <canvas id="vdb-pie-chart" width="400" height="400"></canvas>
                </div>
            </div>
            """
        
        if not words_not_in_vdb:
            word_rows = "<tr><td colspan='4'>Tutte le parole sono nel Vocabolario di Base!</td></tr>"
        else:
            word_rows = []
            for word_info in word_details[:50]:  # Primi 50
                word = word_info['word']
                freq = word_info['frequency']
                difficulty = word_info['difficulty_score']
                alternatives = word_info.get('alternatives', [])
                
                # Formatta alternative
                if alternatives:
                    alt_html = ', '.join([f"<span class='alternative-word'>{alt}</span>" for alt in alternatives[:3]])
                else:
                    alt_html = "<span class='no-alternatives'>-</span>"
                
                # Colore difficoltà
                difficulty_color = self._get_difficulty_color_from_score(difficulty)
                
                word_rows.append(f"""
                <tr>
                    <td class="vocab-word">{word}</td>
                    <td class="vocab-freq">{freq}</td>
                    <td class="vocab-difficulty">
                        <span class="difficulty-badge" style="background-color: {difficulty_color};">
                            {difficulty:.2f}
                        </span>
                    </td>
                    <td class="vocab-alternatives">{alt_html}</td>
                </tr>
                """)
            word_rows = ''.join(word_rows)
        
        return f"""
        <section class="vocabulary-section">
            <h2>Analisi Vocabolario</h2>
            
            <div class="vocab-stats">
                <div class="vocab-stat-card">
                    <div class="vocab-stat-value">{coverage:.1f}%</div>
                    <div class="vocab-stat-label">Copertura Vocabolario di Base</div>
                </div>
                <div class="vocab-stat-card">
                    <div class="vocab-stat-value">{unique_difficult}</div>
                    <div class="vocab-stat-label">Parole Uniche Difficili</div>
                </div>
                <div class="vocab-stat-card">
                    <div class="vocab-stat-value">{total_difficult}</div>
                    <div class="vocab-stat-label">Occorrenze Totali</div>
                </div>
            </div>
            
            {vdb_stats_html}
            
            <div class="vocab-explanation">
                <h3>📚 Cosa sono le parole "difficili"?</h3>
                <p>
                    Le parole difficili sono quelle che <strong>non compaiono nel Vocabolario di Base (VdB)</strong> 
                    della lingua italiana. Il VdB contiene circa 7.000 parole fondamentali che dovrebbero essere 
                    comprese dalla maggior parte dei lettori. Le parole fuori dal VdB potrebbero richiedere 
                    un livello di istruzione più elevato o una conoscenza specialistica.
                </p>
            </div>
            
            <h3>Parole non nel Vocabolario di Base (prime 50 per frequenza)</h3>
            <div class="table-wrapper">
                <table class="vocab-table">
                    <thead>
                        <tr>
                            <th>Parola</th>
                            <th>Frequenza</th>
                            <th>Difficoltà</th>
                            <th>Alternative Semplificate</th>
                        </tr>
                    </thead>
                    <tbody>
                        {word_rows}
                    </tbody>
                </table>
            </div>
        </section>
        """
    
    def _analyze_difficult_words_with_alternatives(
        self,
        words_not_in_vdb: Dict[str, int],
        vocab_breakdown: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analizza parole difficili e suggerisce alternative (Sprint 2, Task 2.5).
        
        Args:
            words_not_in_vdb: Dizionario {parola: frequenza}
            vocab_breakdown: Dati vocabolario per context
            
        Returns:
            Lista di dict con: word, frequency, difficulty_score, alternatives
        """
        from correttore.services.vocabulary_service import VocabularyService
        
        vocab_service = VocabularyService()
        word_details = []
        
        for word, freq in words_not_in_vdb.items():
            analysis = vocab_service.analyze_word_detailed(word)
            
            word_details.append({
                'word': word,
                'frequency': freq,
                'difficulty_score': analysis.difficulty_score,
                'in_vdb': analysis.in_vdb,
                'level': analysis.level,
                'alternatives': analysis.suggested_alternatives,
                'is_technical': analysis.is_technical
            })
        
        # Ordina per frequenza decrescente
        word_details.sort(key=lambda x: x['frequency'], reverse=True)
        
        return word_details
    
    def _get_difficulty_color_from_score(self, difficulty_score: float) -> str:
        """
        Mappa difficulty_score (0.0-1.0) a un colore.
        
        Args:
            difficulty_score: Score da 0.0 (facile) a 1.0 (difficile)
            
        Returns:
            Codice esadecimale colore
        """
        if difficulty_score <= 0.33:
            return '#2ecc71'  # Verde (fondamentale)
        elif difficulty_score <= 0.66:
            return '#f39c12'  # Arancione (alto uso/alta disponibilità)
        else:
            return '#e74c3c'  # Rosso (fuori VdB)
    
    def _generate_charts_section(
        self,
        sentence_stats: Dict[str, Any],
        sentences: List[SentenceReadability],
        vocab_breakdown: Optional[Dict[str, Any]] = None
    ) -> str:
        """Genera la sezione grafici"""
        # Prepara dati per i grafici
        distribution = sentence_stats.get('distribution', {})
        
        # Dati per grafico a linea (GULPEASE lungo il documento)
        line_data = json.dumps([
            {'x': s.sentence_index, 'y': s.gulpease_score}
            for s in sentences
        ])
        
        # Dati per grafico a torta
        pie_data = json.dumps({
            'labels': ['Molto Facili', 'Facili', 'Difficili', 'Molto Difficili'],
            'values': [
                distribution.get('very_easy', 0),
                distribution.get('easy', 0),
                distribution.get('difficult', 0),
                distribution.get('very_difficult', 0)
            ],
            'colors': ['#2d5016', '#4a7c2c', '#f39c12', '#c0392b']
        })
        
        return f"""
        <section class="charts-section">
            <h2>Visualizzazioni</h2>
            
            <div class="chart-container">
                <h3>Distribuzione Difficoltà</h3>
                <canvas id="pie-chart" width="400" height="400"></canvas>
            </div>
            
            <div class="chart-container">
                <h3>GULPEASE lungo il Documento</h3>
                <canvas id="line-chart" width="800" height="400"></canvas>
            </div>
            
            <div class="chart-container">
                <h3>Heatmap Leggibilità</h3>
                <div id="heatmap" class="heatmap">
                    {self._generate_heatmap(sentences)}
                </div>
            </div>
        </section>
        
        <script>
            const pieData = {pie_data};
            const lineData = {line_data};
            const vdbBreakdown = {json.dumps(vocab_breakdown) if vocab_breakdown else 'null'};
            
            // Inizializza grafici quando il tab viene selezionato
            document.querySelector('[data-tab="grafici"]').addEventListener('click', function() {{
                setTimeout(() => {{
                    drawPieChart();
                    drawLineChart();
                }}, 100);
            }});
            
            // Inizializza grafico VdB quando il tab vocabolario viene selezionato
            document.querySelector('[data-tab="vocabolario"]').addEventListener('click', function() {{
                setTimeout(() => {{
                    if (vdbBreakdown) {{
                        drawVdbPieChart();
                    }}
                }}, 100);
            }});
        </script>
        """
    
    def _generate_heatmap(self, sentences: List[SentenceReadability]) -> str:
        """Genera una heatmap delle frasi"""
        if not sentences:
            return ""
        
        cells = []
        for sentence in sentences:
            color = sentence.get_difficulty_color()
            title = f"Frase {sentence.sentence_index}: {sentence.gulpease_score:.1f}"
            cells.append(f'<div class="heatmap-cell" style="background-color: {color};" title="{title}"></div>')
        
        return ''.join(cells)
    
    def _get_difficulty_color(self, gulpease: float) -> str:
        """Restituisce il colore per il livello di difficoltà"""
        if gulpease >= 80:
            return '#2d5016'
        elif gulpease >= 60:
            return '#4a7c2c'
        elif gulpease >= 40:
            return '#f39c12'
        else:
            return '#c0392b'
    
    def _get_difficulty_label(self, gulpease: float) -> str:
        """Restituisce l'etichetta per il livello di difficoltà"""
        if gulpease >= 80:
            return 'Molto Facile'
        elif gulpease >= 60:
            return 'Facile'
        elif gulpease >= 40:
            return 'Difficile'
        else:
            return 'Molto Difficile'
    
    def _get_css(self) -> str:
        """Restituisce il CSS per il report"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .report-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .report-header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .document-info h2 {
            font-size: 1.5em;
            margin-top: 20px;
            opacity: 0.95;
        }
        
        .timestamp {
            opacity: 0.8;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 2px solid #dee2e6;
            overflow-x: auto;
        }
        
        .tab-button {
            flex: 1;
            min-width: 150px;
            padding: 15px 20px;
            background: transparent;
            border: none;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
        }
        
        .tab-button:hover {
            background: #e9ecef;
        }
        
        .tab-button.active {
            background: white;
            border-bottom-color: #667eea;
            color: #667eea;
        }
        
        .tab-content {
            display: none;
            padding: 40px;
            animation: fadeIn 0.3s ease;
        }
        
        .tab-content.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .big-score {
            text-align: center;
            padding: 40px;
            margin: 0 auto 40px;
            max-width: 400px;
            border: 4px solid;
            border-radius: 20px;
            background: white;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .score-value {
            font-size: 5em;
            font-weight: bold;
            line-height: 1;
        }
        
        .score-label {
            font-size: 1.2em;
            color: #666;
            margin-top: 10px;
        }
        
        .score-difficulty {
            font-size: 1.5em;
            font-weight: 600;
            margin-top: 10px;
            color: #333;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .stat-icon {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .distribution-summary {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
        }
        
        .distribution-summary h3 {
            margin-bottom: 20px;
            color: #333;
        }
        
        .distribution-item {
            margin-bottom: 15px;
        }
        
        .distribution-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        .distribution-bar-bg {
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
        }
        
        .distribution-bar-fill {
            height: 100%;
            transition: width 0.5s ease;
            border-radius: 15px;
        }
        
        .interpretation-box {
            background: white;
            border: 2px solid #dee2e6;
            border-radius: 12px;
            padding: 30px;
        }
        
        .interpretation-box h3 {
            margin-bottom: 20px;
            color: #333;
        }
        
        .interpretation-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .interpretation-table th,
        .interpretation-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        
        .interpretation-table th {
            background: #f8f9fa;
            font-weight: 600;
        }
        
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .filter-controls {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .filter-btn {
            padding: 8px 16px;
            border: 2px solid #dee2e6;
            background: white;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .filter-btn:hover {
            border-color: #667eea;
            color: #667eea;
        }
        
        .filter-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .table-wrapper {
            overflow-x: auto;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .sentences-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        
        .sentences-table th,
        .sentences-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        
        .sentences-table th {
            background: #f8f9fa;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        .sentences-table th.sortable {
            cursor: pointer;
            user-select: none;
        }
        
        .sentences-table th.sortable:hover {
            background: #e9ecef;
        }
        
        .sentence-num {
            width: 80px;
            text-align: center;
            font-weight: 600;
        }
        
        .sentence-text {
            max-width: 600px;
        }
        
        .sentence-score {
            width: 120px;
            text-align: center;
            font-size: 1.1em;
        }
        
        .sentence-difficulty,
        .sentence-words,
        .sentence-vdb {
            width: 120px;
            text-align: center;
        }
        
        .difficult-word {
            background: #fff3cd;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: 600;
        }
        
        .legend {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 12px;
        }
        
        .legend h4 {
            margin-bottom: 15px;
        }
        
        .legend-item {
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 10px;
            padding: 5px 10px;
            background: white;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .vocabulary-section h2,
        .charts-section h2 {
            margin-bottom: 30px;
            color: #333;
        }
        
        .vocab-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .vocab-stat-card {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .vocab-stat-value {
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .vocab-stat-label {
            font-size: 1em;
            opacity: 0.95;
        }
        
        .vocab-explanation {
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 20px;
            margin: 30px 0;
            border-radius: 8px;
        }
        
        .vocab-explanation h3 {
            color: #1976D2;
            margin-bottom: 10px;
        }
        
        .vocab-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        
        .vocab-table th,
        .vocab-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        
        .vocab-table th {
            background: #f8f9fa;
            font-weight: 600;
        }
        
        .vocab-word {
            font-weight: 600;
            color: #667eea;
        }
        
        .vocab-freq {
            text-align: center;
            width: 100px;
        }
        
        .vocab-difficulty {
            text-align: center;
            width: 120px;
        }
        
        .difficulty-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            font-size: 0.9em;
        }
        
        .vocab-alternatives {
            min-width: 200px;
        }
        
        .alternative-word {
            display: inline-block;
            padding: 3px 10px;
            margin: 2px;
            background: #e3f2fd;
            color: #1976d2;
            border-radius: 8px;
            font-size: 0.9em;
            font-weight: 500;
        }
        
        .no-alternatives {
            color: #999;
            font-style: italic;
        }
        
        .vdb-breakdown {
            margin: 40px 0;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 12px;
        }
        
        .vdb-breakdown h3 {
            margin-bottom: 25px;
            color: #333;
        }
        
        .vdb-breakdown-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .vdb-level-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        
        .vdb-level-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .vdb-level-name {
            font-weight: 600;
            font-size: 1.1em;
            margin-bottom: 10px;
            color: #333;
        }
        
        .vdb-level-count {
            font-size: 1.8em;
            font-weight: bold;
            margin: 10px 0;
            color: #667eea;
        }
        
        .vdb-level-percentage {
            font-size: 1.2em;
            color: #666;
            margin-bottom: 10px;
        }
        
        .vdb-level-description {
            font-size: 0.9em;
            color: #888;
            font-style: italic;
        }
        
        .vdb-chart-container {
            display: flex;
            justify-content: center;
            padding: 20px;
            background: white;
            border-radius: 8px;
        }
        
        .chart-container {
            margin-bottom: 50px;
            padding: 30px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .chart-container h3 {
            margin-bottom: 20px;
            color: #333;
        }
        
        .chart-container canvas {
            max-width: 100%;
            height: auto !important;
        }
        
        .heatmap {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(20px, 1fr));
            gap: 5px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 12px;
        }
        
        .heatmap-cell {
            aspect-ratio: 1;
            border-radius: 4px;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        
        .heatmap-cell:hover {
            transform: scale(1.2);
            z-index: 100;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        
        @media (max-width: 768px) {
            .report-header h1 {
                font-size: 1.8em;
            }
            
            .tab-content {
                padding: 20px;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .section-header {
                flex-direction: column;
                align-items: flex-start;
            }
        }
        """
    
    def _get_javascript(self) -> str:
        """Restituisce il JavaScript per il report"""
        return """
        // Tab Navigation
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.dataset.tab;
                
                // Update buttons
                document.querySelectorAll('.tab-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                button.classList.add('active');
                
                // Update content
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                document.getElementById(`tab-${tabName}`).classList.add('active');
            });
        });
        
        // Filter sentences
        document.querySelectorAll('.filter-btn').forEach(button => {
            button.addEventListener('click', () => {
                const filter = button.dataset.filter;
                
                // Update active button
                document.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                button.classList.add('active');
                
                // Filter rows
                const rows = document.querySelectorAll('.sentences-table tbody tr');
                rows.forEach(row => {
                    const score = parseFloat(row.querySelector('.sentence-score').textContent.match(/[0-9.]+/)[0]);
                    let show = true;
                    
                    if (filter === 'easy' && score < 60) show = false;
                    if (filter === 'difficult' && (score < 40 || score >= 60)) show = false;
                    if (filter === 'very-difficult' && score >= 40) show = false;
                    
                    row.style.display = show ? '' : 'none';
                });
            });
        });
        
        // Sort table
        let sortDirection = {};
        document.querySelectorAll('.sortable').forEach(header => {
            sortDirection[header.dataset.sort] = 1;
            
            header.addEventListener('click', () => {
                const sortBy = header.dataset.sort;
                const tbody = document.querySelector('.sentences-table tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                
                rows.sort((a, b) => {
                    let aVal, bVal;
                    
                    switch(sortBy) {
                        case 'index':
                            aVal = parseInt(a.querySelector('.sentence-num').textContent);
                            bVal = parseInt(b.querySelector('.sentence-num').textContent);
                            break;
                        case 'score':
                            aVal = parseFloat(a.querySelector('.sentence-score').textContent.match(/[0-9.]+/)[0]);
                            bVal = parseFloat(b.querySelector('.sentence-score').textContent.match(/[0-9.]+/)[0]);
                            break;
                        case 'words':
                            aVal = parseInt(a.querySelector('.sentence-words').textContent);
                            bVal = parseInt(b.querySelector('.sentence-words').textContent);
                            break;
                        case 'vdb':
                            aVal = parseInt(a.querySelector('.sentence-vdb').textContent);
                            bVal = parseInt(b.querySelector('.sentence-vdb').textContent);
                            break;
                    }
                    
                    return (aVal - bVal) * sortDirection[sortBy];
                });
                
                sortDirection[sortBy] *= -1;
                
                rows.forEach(row => tbody.appendChild(row));
            });
        });
        
        // Simple charts using canvas
        function drawPieChart() {
            const canvas = document.getElementById('pie-chart');
            if (!canvas || !pieData) return;
            
            const ctx = canvas.getContext('2d');
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const radius = Math.min(centerX, centerY) - 50;
            
            const total = pieData.values.reduce((a, b) => a + b, 0);
            if (total === 0) return;
            
            let currentAngle = -Math.PI / 2;
            
            pieData.values.forEach((value, i) => {
                const sliceAngle = (value / total) * 2 * Math.PI;
                
                ctx.fillStyle = pieData.colors[i];
                ctx.beginPath();
                ctx.moveTo(centerX, centerY);
                ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
                ctx.closePath();
                ctx.fill();
                
                // Label
                if (value > 0) {
                    const labelAngle = currentAngle + sliceAngle / 2;
                    const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
                    const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);
                    
                    ctx.fillStyle = 'white';
                    ctx.font = 'bold 16px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(value, labelX, labelY);
                }
                
                currentAngle += sliceAngle;
            });
            
            // Legend
            let legendY = 20;
            pieData.labels.forEach((label, i) => {
                ctx.fillStyle = pieData.colors[i];
                ctx.fillRect(10, legendY, 20, 20);
                
                ctx.fillStyle = '#333';
                ctx.font = '14px Arial';
                ctx.textAlign = 'left';
                ctx.fillText(`${label}: ${pieData.values[i]}`, 40, legendY + 15);
                
                legendY += 30;
            });
        }
        
        function drawLineChart() {
            const canvas = document.getElementById('line-chart');
            if (!canvas || !lineData || lineData.length === 0) return;
            
            const ctx = canvas.getContext('2d');
            const padding = 60;
            const chartWidth = canvas.width - padding * 2;
            const chartHeight = canvas.height - padding * 2;
            
            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Draw axes
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(padding, padding);
            ctx.lineTo(padding, canvas.height - padding);
            ctx.lineTo(canvas.width - padding, canvas.height - padding);
            ctx.stroke();
            
            // Labels
            ctx.fillStyle = '#333';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('Numero Frase', canvas.width / 2, canvas.height - 20);
            
            ctx.save();
            ctx.translate(20, canvas.height / 2);
            ctx.rotate(-Math.PI / 2);
            ctx.fillText('GULPEASE', 0, 0);
            ctx.restore();
            
            // Draw line
            const maxY = 100;
            const minY = 0;
            const maxX = Math.max(...lineData.map(d => d.x));
            
            ctx.strokeStyle = '#667eea';
            ctx.lineWidth = 3;
            ctx.beginPath();
            
            lineData.forEach((point, i) => {
                const x = padding + (point.x / maxX) * chartWidth;
                const y = canvas.height - padding - ((point.y - minY) / (maxY - minY)) * chartHeight;
                
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            
            ctx.stroke();
            
            // Draw points
            lineData.forEach(point => {
                const x = padding + (point.x / maxX) * chartWidth;
                const y = canvas.height - padding - ((point.y - minY) / (maxY - minY)) * chartHeight;
                
                const color = point.y >= 80 ? '#2d5016' : 
                             point.y >= 60 ? '#4a7c2c' : 
                             point.y >= 40 ? '#f39c12' : '#c0392b';
                
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(x, y, 5, 0, 2 * Math.PI);
                ctx.fill();
            });
            
            // Draw reference lines
            ctx.strokeStyle = '#ccc';
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            
            [40, 60, 80].forEach(value => {
                const y = canvas.height - padding - ((value - minY) / (maxY - minY)) * chartHeight;
                ctx.beginPath();
                ctx.moveTo(padding, y);
                ctx.lineTo(canvas.width - padding, y);
                ctx.stroke();
                
                ctx.fillStyle = '#666';
                ctx.textAlign = 'right';
                ctx.fillText(value, padding - 10, y + 5);
            });
            
            ctx.setLineDash([]);
        }
        
        function drawVdbPieChart() {
            const canvas = document.getElementById('vdb-pie-chart');
            if (!canvas || !vdbBreakdown) return;
            
            // Dati VdB dal vocab_breakdown
            const vdbData = {
                labels: ['Fondamentali', 'Alto Uso', 'Alta Disponibilità', 'Non Classificate', 'Fuori VdB'],
                values: [
                    vdbBreakdown.fondamentale?.count || 0,
                    vdbBreakdown.alto_uso?.count || 0,
                    vdbBreakdown.alta_disponibilita?.count || 0,
                    vdbBreakdown.non_classificato?.count || 0,
                    vdbBreakdown.fuori_vdb?.count || 0
                ],
                colors: ['#2ecc71', '#3498db', '#f39c12', '#95a5a6', '#e74c3c']
            };
            
            const ctx = canvas.getContext('2d');
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const radius = Math.min(centerX, centerY) - 50;
            
            const total = vdbData.values.reduce((a, b) => a + b, 0);
            if (total === 0) return;
            
            let currentAngle = -Math.PI / 2;
            
            vdbData.values.forEach((value, i) => {
                const sliceAngle = (value / total) * 2 * Math.PI;
                
                ctx.fillStyle = vdbData.colors[i];
                ctx.beginPath();
                ctx.moveTo(centerX, centerY);
                ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
                ctx.closePath();
                ctx.fill();
                
                // Label
                if (value > 0) {
                    const labelAngle = currentAngle + sliceAngle / 2;
                    const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
                    const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);
                    
                    ctx.fillStyle = 'white';
                    ctx.font = 'bold 16px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(value, labelX, labelY);
                }
                
                currentAngle += sliceAngle;
            });
            
            // Legend
            let legendY = 20;
            vdbData.labels.forEach((label, i) => {
                ctx.fillStyle = vdbData.colors[i];
                ctx.fillRect(10, legendY, 20, 20);
                
                ctx.fillStyle = '#333';
                ctx.font = '14px Arial';
                ctx.textAlign = 'left';
                ctx.fillText(`${label}: ${vdbData.values[i]}`, 40, legendY + 15);
                
                legendY += 30;
            });
        }
        
        // Print functionality
        function printReport() {
            window.print();
        }
        
        console.log('Report Leggibilità caricato con successo!');
        """


def generate_readability_report(
    text: str,
    output_path: str,
    vocabulary_service=None,
    document_title: str = "Documento"
) -> str:
    """
    Funzione helper per generare rapidamente un report di leggibilità.
    
    Args:
        text: Il testo da analizzare
        output_path: Percorso del file HTML di output
        vocabulary_service: Servizio opzionale per verificare parole nel VdB
        document_title: Titolo del documento analizzato
        
    Returns:
        Percorso del file HTML generato
    """
    generator = ReadabilityReportGenerator()
    return generator.generate_report(text, output_path, vocabulary_service, document_title)


if __name__ == "__main__":
    # Test del generatore
    test_text = """
    L'intelligenza artificiale sta rivoluzionando il mondo della tecnologia.
    Gli algoritmi di machine learning sono sempre più sofisticati.
    Le applicazioni pratiche sono innumerevoli e continuano a crescere.
    Tuttavia, è importante considerare anche le implicazioni etiche.
    La trasparenza e la responsabilità sono fondamentali per lo sviluppo futuro.
    """
    
    output = "test_readability_report.html"
    generate_readability_report(test_text, output, document_title="Testo di Test")
    print(f"✅ Report generato: {output}")
