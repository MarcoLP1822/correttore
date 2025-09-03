"""
Dashboard di monitoraggio per visualizzare metriche in tempo reale.

Genera report HTML con grafici e tabelle delle performance.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from tools.monitoring import get_monitor, SystemMonitor


class MonitoringDashboard:
    """Dashboard per visualizzazione metriche."""
    
    def __init__(self, monitor: SystemMonitor):
        self.monitor = monitor
        
    def generate_html_dashboard(self, output_path: Path) -> None:
        """Genera dashboard HTML completa."""
        report = self.monitor.generate_performance_report()
        
        html_content = self._generate_html_template(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
    def _generate_html_template(self, report: Dict[str, Any]) -> str:
        """Genera template HTML."""
        return f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Correttore - Dashboard Monitoring</title>
    <style>
        {self._get_css_styles()}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Correttore - Dashboard Monitoring</h1>
            <div class="timestamp">
                Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            </div>
        </header>
        
        {self._generate_system_health_section(report['system_health'])}
        {self._generate_quality_metrics_section(report['quality_metrics'])}
        {self._generate_api_metrics_section(report['api_metrics'])}
        {self._generate_performance_section(report['performance_metrics'])}
        {self._generate_cache_metrics_section(report.get('cache_metrics', {}))}
        {self._generate_parallel_metrics_section(report.get('parallel_metrics', {}))}
        {self._generate_alerts_section(report['alerts'])}
        
        <footer>
            <p>Dashboard generata automaticamente dal Sistema di Monitoring del Correttore</p>
        </footer>
    </div>
    
    <script>
        {self._generate_javascript(report)}
    </script>
</body>
</html>
        """
        
    def _get_css_styles(self) -> str:
        """Restituisce stili CSS."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .timestamp {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .section {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .section h2 {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .metric-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #667eea;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .metric-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .health-good { border-left-color: #28a745; }
        .health-good .metric-value { color: #28a745; }
        
        .health-warning { border-left-color: #ffc107; }
        .health-warning .metric-value { color: #ffc107; }
        
        .health-error { border-left-color: #dc3545; }
        .health-error .metric-value { color: #dc3545; }
        
        .chart-container {
            position: relative;
            height: 400px;
            margin: 20px 0;
        }
        
        .alerts {
            margin-top: 20px;
        }
        
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 10px;
            border-left: 4px solid;
        }
        
        .alert-warning {
            background-color: #fff3cd;
            border-left-color: #ffc107;
            color: #856404;
        }
        
        .alert-error {
            background-color: #f8d7da;
            border-left-color: #dc3545;
            color: #721c24;
        }
        
        .alert-info {
            background-color: #d1ecf1;
            border-left-color: #17a2b8;
            color: #0c5460;
        }
        
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        
        footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .two-column {
                grid-template-columns: 1fr;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
        }
        """
        
    def _generate_system_health_section(self, health: Dict[str, Any]) -> str:
        """Genera sezione salute sistema."""
        def get_health_class(value, good_threshold, warning_threshold):
            if value >= good_threshold:
                return "health-good"
            elif value >= warning_threshold:
                return "health-warning"
            else:
                return "health-error"
                
        uptime_class = "health-good"
        accuracy_class = get_health_class(health['correction_accuracy'], 0.9, 0.8)
        api_class = get_health_class(health['api_success_rate'], 0.95, 0.85)
        quality_class = get_health_class(health['average_quality_score'], 0.85, 0.75)
        
        return f"""
        <div class="section">
            <h2>🎯 Stato Sistema</h2>
            <div class="metrics-grid">
                <div class="metric-card {uptime_class}">
                    <div class="metric-value">{health['uptime_hours']:.1f}h</div>
                    <div class="metric-label">Uptime</div>
                </div>
                <div class="metric-card {accuracy_class}">
                    <div class="metric-value">{health['correction_accuracy']:.1%}</div>
                    <div class="metric-label">Accuracy Correzioni</div>
                </div>
                <div class="metric-card {api_class}">
                    <div class="metric-value">{health['api_success_rate']:.1%}</div>
                    <div class="metric-label">API Success Rate</div>
                </div>
                <div class="metric-card {quality_class}">
                    <div class="metric-value">{health['average_quality_score']:.2f}</div>
                    <div class="metric-label">Quality Score Medio</div>
                </div>
                <div class="metric-card health-good">
                    <div class="metric-value">{health['documents_processed']}</div>
                    <div class="metric-label">Documenti Processati</div>
                </div>
                <div class="metric-card health-good">
                    <div class="metric-value">{health['processing_speed']:.0f}</div>
                    <div class="metric-label">Chars/Sec</div>
                </div>
            </div>
        </div>
        """
        
    def _generate_quality_metrics_section(self, quality: Dict[str, Any]) -> str:
        """Genera sezione metriche qualità."""
        return f"""
        <div class="section">
            <h2>📊 Metriche Qualità</h2>
            <div class="two-column">
                <div>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">{quality['correction_accuracy_24h']:.1%}</div>
                            <div class="metric-label">Accuracy 24h</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{quality['content_preservation_rate']:.1%}</div>
                            <div class="metric-label">Preservazione Contenuto</div>
                        </div>
                    </div>
                    
                    {'<div class="alert alert-warning">⚠️ Degradazione qualità rilevata</div>' if quality['quality_degradation_detected'] else ''}
                </div>
                
                <div>
                    <h3>Trend Qualità</h3>
                    <div class="chart-container">
                        <canvas id="qualityTrendChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        """
        
    def _generate_api_metrics_section(self, api: Dict[str, Any]) -> str:
        """Genera sezione metriche API."""
        return f"""
        <div class="section">
            <h2>🔌 Metriche API</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{api['success_rate']:.1%}</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{api['average_response_time']:.2f}s</div>
                    <div class="metric-label">Tempo Risposta Medio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{api['requests_per_minute']:.1f}</div>
                    <div class="metric-label">Richieste/Minuto</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{api['error_rate_1h']:.1%}</div>
                    <div class="metric-label">Error Rate (1h)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${api['total_cost']:.4f}</div>
                    <div class="metric-label">Costo Totale</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{api['tokens_used']:,}</div>
                    <div class="metric-label">Token Utilizzati</div>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Metrica</th>
                        <th>Valore</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Rate Limit Hits</td>
                        <td>{api['rate_limit_hits']}</td>
                        <td>{'⚠️ Alto' if api['rate_limit_hits'] > 5 else '✅ OK'}</td>
                    </tr>
                    <tr>
                        <td>Timeout Errors</td>
                        <td>{api['timeout_errors']}</td>
                        <td>{'⚠️ Alto' if api['timeout_errors'] > 3 else '✅ OK'}</td>
                    </tr>
                    <tr>
                        <td>Costo per Richiesta</td>
                        <td>${api['average_cost_per_request']:.6f}</td>
                        <td>{'⚠️ Alto' if api['average_cost_per_request'] > 0.01 else '✅ OK'}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
        
    def _generate_performance_section(self, perf: Dict[str, Any]) -> str:
        """Genera sezione performance."""
        return f"""
        <div class="section">
            <h2>⚡ Performance</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{perf['documents_processed']}</div>
                    <div class="metric-label">Documenti Processati</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{perf['average_time_per_document']:.1f}s</div>
                    <div class="metric-label">Tempo Medio/Documento</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{perf['processing_speed']:.0f}</div>
                    <div class="metric-label">Velocità (chars/sec)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{perf['peak_speed']:.0f}</div>
                    <div class="metric-label">Velocità Picco</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{perf['total_characters']:,}</div>
                    <div class="metric-label">Caratteri Totali</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{perf['uptime_hours']:.1f}h</div>
                    <div class="metric-label">Uptime</div>
                </div>
            </div>
        </div>
        """
        
    def _generate_cache_metrics_section(self, cache: Dict[str, Any]) -> str:
        """Genera sezione metriche cache - FASE 4."""
        if not cache:
            return """
            <div class="section">
                <h2>💾 Cache Intelligente (FASE 4)</h2>
                <div class="alert alert-info">
                    Cache non configurata o non attiva.
                </div>
            </div>
            """
            
        return f"""
        <div class="section">
            <h2>💾 Cache Intelligente (FASE 4)</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{cache.get('total_entries', 0):,}</div>
                    <div class="metric-label">Entries Totali</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{cache.get('hit_rate', 0):.1%}</div>
                    <div class="metric-label">Hit Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{cache.get('size_mb', 0):.1f} MB</div>
                    <div class="metric-label">Dimensione Cache</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{cache.get('avg_quality', 0):.3f}</div>
                    <div class="metric-label">Qualità Media</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{cache.get('performance_gain', 0):.1f}s</div>
                    <div class="metric-label">Tempo Risparmiato</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{cache.get('expired_count', 0):,}</div>
                    <div class="metric-label">Entries Scadute</div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="cacheChart"></canvas>
            </div>
        </div>
        """
    
    def _generate_parallel_metrics_section(self, parallel: Dict[str, Any]) -> str:
        """Genera sezione metriche processamento parallelo - FASE 4."""
        if not parallel:
            return """
            <div class="section">
                <h2>⚡ Processamento Parallelo (FASE 4)</h2>
                <div class="alert alert-info">
                    Processamento parallelo non configurato o non attivo.
                </div>
            </div>
            """
            
        return f"""
        <div class="section">
            <h2>⚡ Processamento Parallelo (FASE 4)</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{parallel.get('total_tasks', 0):,}</div>
                    <div class="metric-label">Task Totali</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{parallel.get('completed_tasks', 0):,}</div>
                    <div class="metric-label">Task Completati</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{parallel.get('cached_results', 0):,}</div>
                    <div class="metric-label">Risultati da Cache</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{parallel.get('throughput_per_minute', 0):.1f}</div>
                    <div class="metric-label">Throughput/min</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{parallel.get('parallelism_efficiency', 0):.1%}</div>
                    <div class="metric-label">Efficienza</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{parallel.get('avg_processing_time', 0):.2f}s</div>
                    <div class="metric-label">Tempo Medio</div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="parallelChart"></canvas>
            </div>
        </div>
        """
        
    def _generate_alerts_section(self, alerts: List[Dict[str, Any]]) -> str:
        """Genera sezione alert."""
        if not alerts:
            return f"""
            <div class="section">
                <h2>🔔 Alert</h2>
                <div class="alert alert-info">
                    ✅ Nessun alert attivo. Sistema operativo normale.
                </div>
            </div>
            """
            
        alerts_html = ""
        for alert in alerts:
            alert_class = f"alert-{alert['level']}"
            icon = "⚠️" if alert['level'] == 'warning' else "🚨" if alert['level'] == 'error' else "ℹ️"
            
            alerts_html += f"""
            <div class="alert {alert_class}">
                {icon} <strong>{alert['type'].replace('_', ' ').title()}:</strong> {alert['message']}
                <br><small>Timestamp: {alert['timestamp']}</small>
            </div>
            """
            
        return f"""
        <div class="section">
            <h2>🔔 Alert ({len(alerts)})</h2>
            {alerts_html}
        </div>
        """
        
    def _generate_javascript(self, report: Dict[str, Any]) -> str:
        """Genera JavaScript per grafici inclusi FASE 4."""
        quality_trend = report['quality_metrics']['quality_trend']
        cache_metrics = report.get('cache_metrics', {})
        parallel_metrics = report.get('parallel_metrics', {})
        
        return f"""
        // Grafico trend qualità
        const ctx = document.getElementById('qualityTrendChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {list(range(len(quality_trend)))},
                datasets: [{{
                    label: 'Quality Score',
                    data: {quality_trend},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: false,
                        min: 0.5,
                        max: 1.0
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    title: {{
                        display: true,
                        text: 'Trend Qualità (Ultime {len(quality_trend)} correzioni)'
                    }}
                }}
            }}
        }});
        
        // FASE 4: Grafico Cache Performance
        const cacheCtx = document.getElementById('cacheChart');
        if (cacheCtx) {{
            new Chart(cacheCtx, {{
                type: 'doughnut',
                data: {{
                    labels: ['Cache Hits', 'Cache Misses'],
                    datasets: [{{
                        data: [
                            {cache_metrics.get('hit_rate', 0) * 100:.1f},
                            {(1 - cache_metrics.get('hit_rate', 0)) * 100:.1f}
                        ],
                        backgroundColor: ['#28a745', '#dc3545'],
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Cache Hit Rate - Fase 4'
                        }},
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}
            }});
        }}
        
        // FASE 4: Grafico Parallel Processing
        const parallelCtx = document.getElementById('parallelChart');
        if (parallelCtx) {{
            new Chart(parallelCtx, {{
                type: 'bar',
                data: {{
                    labels: ['Task Totali', 'Completati', 'Da Cache', 'Falliti'],
                    datasets: [{{
                        label: 'Task Count',
                        data: [
                            {parallel_metrics.get('total_tasks', 0)},
                            {parallel_metrics.get('completed_tasks', 0)},
                            {parallel_metrics.get('cached_results', 0)},
                            {parallel_metrics.get('failed_tasks', 0)}
                        ],
                        backgroundColor: [
                            '#007bff',
                            '#28a745', 
                            '#ffc107',
                            '#dc3545'
                        ],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Processamento Parallelo - Fase 4'
                        }},
                        legend: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }}
                }}
            }});
        }}
            }}
        }});
        
        // Auto-refresh ogni 30 secondi (opzionale)
        // setTimeout(() => location.reload(), 30000);
        """


def generate_dashboard(output_path: Optional[Path] = None) -> None:
    """Genera dashboard HTML."""
    if output_path is None:
        output_path = Path("monitoring_dashboard.html")
        
    monitor = get_monitor()
    dashboard = MonitoringDashboard(monitor)
    
    dashboard.generate_html_dashboard(output_path)
    print(f"Dashboard generata: {output_path}")


if __name__ == "__main__":
    # Test dashboard
    from tools.monitoring import SystemMonitor
    from config.settings import Settings
    
    print("=== GENERAZIONE DASHBOARD TEST ===\n")
    
    # Crea monitor con dati di test
    settings = Settings()
    monitor = SystemMonitor(settings)
    
    # Popola con dati di esempio
    for i in range(50):
        monitor.quality_monitor.record_correction(
            text_length=100 + i * 20,
            processing_time=0.5 + i * 0.02,
            quality_score=0.8 + (i % 5) * 0.04,
            correction_type=['spell', 'grammar', 'ai'][i % 3],
            success=i % 20 != 19  # 95% success rate
        )
        
    for i in range(30):
        monitor.api_monitor.record_api_call(
            response_time=1.0 + i * 0.05,
            success=i % 15 != 14,  # 93% success rate
            tokens_used=50 + i * 5,
            cost=0.001 + i * 0.00005
        )
        
    for i in range(10):
        monitor.record_document_processing(
            document_path=Path(f"test_doc_{i}.docx"),
            processing_time=8.0 + i,
            characters_processed=4000 + i * 500,
            corrections_made=15 + i * 2,
            quality_score=0.88 + i * 0.01
        )
        
    # Genera dashboard
    dashboard = MonitoringDashboard(monitor)
    output_path = Path("test_dashboard.html")
    
    dashboard.generate_html_dashboard(output_path)
    
    print(f"Dashboard di test generata: {output_path}")
    print("Apri il file in un browser per visualizzare i risultati.")
    
    # Stampa statistiche
    report = monitor.generate_performance_report()
    print(f"\nStatistiche generate:")
    print(f"- Accuracy: {report['quality_metrics']['correction_accuracy_24h']:.1%}")
    print(f"- API Success: {report['api_metrics']['success_rate']:.1%}")
    print(f"- Documenti: {report['performance_metrics']['documents_processed']}")
    print(f"- Alert: {len(report['alerts'])}")
