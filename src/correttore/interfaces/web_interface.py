#!/usr/bin/env python3
"""
Web Interface per il Correttore di Testi Italiani
Interfaccia web enterprise-grade per upload, processamento e monitoring

Features:
- Upload documenti via drag & drop
- Dashboard real-time processing
- Preview e download risultati
- Monitoring integrato
"""

import sys
import os
from pathlib import Path

# Aggiungi root del progetto al path
# __file__ è in src/correttore/interfaces/web_interface.py
# Quindi parent.parent.parent ci porta alla root del progetto
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
import shutil
import time
import json
from pathlib import Path
from datetime import datetime

# Import LanguageTool starter con gestione semplificata
def load_languagetool_functions():
    """Carica le funzioni LanguageTool in modo sicuro."""
    try:
        from correttore.services.languagetool_manager import get_languagetool_manager
        
        def start_languagetool_simple() -> bool:
            """Avvia LanguageTool usando il manager."""
            manager = get_languagetool_manager()
            return manager.ensure_running()
        
        def is_languagetool_running() -> bool:
            """Verifica se LanguageTool è in esecuzione."""
            manager = get_languagetool_manager()
            return manager.is_server_running()
        
        return start_languagetool_simple, is_languagetool_running
        
    except Exception:
        # Funzioni dummy per demo mode
        def start_languagetool_simple() -> bool:
            return False
        def is_languagetool_running() -> bool:
            return False
            
        return start_languagetool_simple, is_languagetool_running

# Carica le funzioni
start_languagetool_simple, is_languagetool_running = load_languagetool_functions()
        
from threading import Thread

# Import moduli correttore
from correttore.interfaces.cli import CorrettoreCLI, CLIOptions, CorrectionMode

# Configurazione Flask con template path corretto
template_dir = project_root / 'templates'
app = Flask(__name__, template_folder=str(template_dir))
app.config['SECRET_KEY'] = 'correttore-enterprise-2024'
app.config['UPLOAD_FOLDER'] = project_root / 'uploads'
app.config['OUTPUT_FOLDER'] = project_root / 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Crea directory se non esistono
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
app.config['OUTPUT_FOLDER'].mkdir(exist_ok=True)

# Aggiungi filtro strftime per Jinja2
@app.template_filter('strftime')
def strftime_filter(value, format='%Y-%m-%d %H:%M:%S'):
    """Filtro per formattare date in template"""
    if value == "now":
        return datetime.now().strftime(format)
    elif isinstance(value, datetime):
        return value.strftime(format)
    else:
        return value

# Storage in memoria per job status (in produzione usare database)
job_status = {}
job_counter = 0

ALLOWED_EXTENSIONS = {'docx', 'doc', 'odt'}

def allowed_file(filename):
    """Verifica se il file è supportato"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_document_async(job_id: str, input_path: Path, options: CLIOptions):
    """Processa documento in background con configurazione italiana ottimizzata"""
    global job_status
    
    try:
        job_status[job_id]['status'] = 'processing'
        job_status[job_id]['progress'] = 10
        
        # Inizializza CLI
        cli = CorrettoreCLI()
        
        # Output path
        output_path = app.config['OUTPUT_FOLDER'] / (input_path.stem + "_corretto" + input_path.suffix)
        
        job_status[job_id]['progress'] = 30
        
        # Processa documento
        success = cli.process_single_document(input_path, output_path, options)
        
        job_status[job_id]['progress'] = 90

        # Controllo che il file corretto sia stato creato
        if success and output_path.exists():
            job_status[job_id]['status'] = 'completed'
            job_status[job_id]['output_file'] = str(output_path)
            job_status[job_id]['download_url'] = f"/download/{output_path.name}"
            
            # Aggiungi link ai report HTML se esistono
            report_html = output_path.parent / f"{output_path.stem}_report.html"
            if report_html.exists():
                job_status[job_id]['report_url'] = f"/download/{report_html.name}"
                print(f"✅ Report HTML trovato: {report_html.name}")
            
            # Cerca altri report (diff, glossario, etc.)
            diff_report = output_path.parent / f"{output_path.stem}_diff.html"
            if diff_report.exists():
                job_status[job_id]['diff_report_url'] = f"/download/{diff_report.name}"
            
            glossario_report = output_path.parent / f"{output_path.stem}_glossario.html"
            if glossario_report.exists():
                job_status[job_id]['glossario_report_url'] = f"/download/{glossario_report.name}"
        else:
            job_status[job_id]['status'] = 'failed'
            job_status[job_id]['error'] = f"Errore: file corretto non creato ({output_path})"
            print(f"[ERRORE] File corretto non trovato: {output_path}")

        job_status[job_id]['progress'] = 100
        job_status[job_id]['completed_at'] = datetime.now().isoformat()
        
    except Exception as e:
        job_status[job_id]['status'] = 'failed'
        job_status[job_id]['error'] = str(e)
        job_status[job_id]['progress'] = 100
        print(f"[ERRORE] Errore durante elaborazione: {e}")
    
    finally:
        # Ripristina sempre la configurazione normale
        from pathlib import Path
        
        config_dir = Path(".")
        current_config = config_dir / "config.yaml"
        backup_config = config_dir / "config_web_backup.yaml"
        
        if backup_config.exists():
            shutil.copy(backup_config, current_config)
            print(f"🔄 Configurazione normale ripristinata")

@app.route('/')
def index():
    """Pagina principale"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Gestisce upload documenti"""
    global job_counter
    
    if 'file' not in request.files:
        return jsonify({'error': 'Nessun file selezionato'}), 400
    
    file = request.files['file']
    
    if not file.filename or file.filename == '':
        return jsonify({'error': 'Nessun file selezionato'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Formato file non supportato. Usare .docx, .doc o .odt'}), 400
    
    # Salva file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{filename}"
    file_path = app.config['UPLOAD_FOLDER'] / unique_filename
    file.save(str(file_path))
    
    # Assicura che LanguageTool sia disponibile prima del processamento
    if not is_languagetool_running():
        print("⚠️  LanguageTool non attivo, avvio automatico...")
        start_languagetool_simple()
    else:
        print("✅ LanguageTool verificato e pronto")
    
    # Crea job
    job_counter += 1
    job_id = f"job_{job_counter}"
    
    # Opzioni semplificate - usa sempre configurazione ottimizzata per italiano
    language_check = request.form.get('language_check', 'true').lower() == 'true'
    ai_enhancement = request.form.get('ai_enhancement', 'true').lower() == 'true'
    
    # Carica configurazione ottimizzata per italiano
    from pathlib import Path
    import shutil
    
    config_dir = Path(".")
    italian_config = config_dir / "config_italiano_ottimizzato.yaml"
    current_config = config_dir / "config.yaml"
    backup_config = config_dir / "config_web_backup.yaml"
    
    if italian_config.exists():
        # Backup della config attuale
        if current_config.exists():
            shutil.copy(current_config, backup_config)
        # Applica config italiana ottimizzata
        shutil.copy(italian_config, current_config)
        print(f"🇮🇹 Configurazione italiana ottimizzata applicata")
    
    # Modalità fissa ottimizzata per italiano
    selected_mode = "aggressive"  # Usa sempre modalità aggressiva con config ottimizzata
    quality_threshold = 0.55      # Soglia abbassata per correggere più errori
    
    print(f"🇮🇹 Correzione italiana professionale attivata")
    print(f"📝 LanguageTool: {'✅ Abilitato' if language_check else '❌ Disabilitato'}")
    print(f"🤖 Miglioramento AI: {'✅ Abilitato' if ai_enhancement else '❌ Disabilitato'}")
    print(f"🎯 Soglia qualità: {quality_threshold*100:.0f}% (ottimizzata)")
    
    options = CLIOptions(
        input_files=[file_path],
        mode=CorrectionMode(selected_mode),
        quality_threshold=quality_threshold,
        backup=request.form.get('backup', 'true').lower() == 'true',
        demo_mode=False,  # Usa correttore reale
        dry_run=False,
        preview=False,
        batch=False,
        verbose=False,
        quiet=True,
        generate_report=True,
        dashboard=False
    )
    
    # Inizializza job status
    job_status[job_id] = {
        'status': 'queued',
        'progress': 0,
        'filename': filename,
        'created_at': datetime.now().isoformat(),
        'options': {
            'mode': options.mode.value,
            'quality_threshold': options.quality_threshold,
            'backup': options.backup
        }
    }
    
    # Avvia processamento in background
    thread = Thread(target=process_document_async, args=(job_id, file_path, options))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'queued',
        'message': 'File caricato e accodato per processamento'
    })

@app.route('/status/<job_id>')
def get_job_status(job_id):
    """Restituisce status di un job"""
    if job_id not in job_status:
        return jsonify({'error': 'Job non trovato'}), 404
    
    return jsonify(job_status[job_id])

@app.route('/api/languagetool/status')
def languagetool_status():
    """Restituisce lo stato di LanguageTool"""
    running = is_languagetool_running()
    return jsonify({
        "running": running,
        "url": "http://localhost:8081",
        "port": 8081
    })

@app.route('/api/languagetool/restart', methods=['POST'])
def restart_languagetool():
    """Riavvia LanguageTool"""
    try:
        success = start_languagetool_simple()
        return jsonify({
            'success': success,
            'message': 'LanguageTool avviato' if success else 'Errore nell\'avvio'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore: {str(e)}'
        }), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download file processato"""
    file_path = app.config['OUTPUT_FOLDER'] / filename
    if not file_path.exists():
        return jsonify({'error': 'File non trovato'}), 404
    
    return send_file(str(file_path), as_attachment=True)

@app.route('/dashboard')
def dashboard():
    """Dashboard monitoring"""
    # Statistiche job
    total_jobs = len(job_status)
    completed_jobs = sum(1 for job in job_status.values() if job['status'] == 'completed')
    failed_jobs = sum(1 for job in job_status.values() if job['status'] == 'failed')
    processing_jobs = sum(1 for job in job_status.values() if job['status'] in ['queued', 'processing'])
    
    stats = {
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'failed_jobs': failed_jobs,
        'processing_jobs': processing_jobs,
        'success_rate': (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
    }
    
    return render_template('dashboard.html', stats=stats, jobs=job_status)

@app.route('/api/jobs')
def api_jobs():
    """API per lista job"""
    return jsonify(job_status)

@app.route('/api/stats')
def api_stats():
    """API per statistiche"""
    total_jobs = len(job_status)
    completed_jobs = sum(1 for job in job_status.values() if job['status'] == 'completed')
    failed_jobs = sum(1 for job in job_status.values() if job['status'] == 'failed')
    processing_jobs = sum(1 for job in job_status.values() if job['status'] in ['queued', 'processing'])
    
    return jsonify({
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'failed_jobs': failed_jobs,
        'processing_jobs': processing_jobs,
        'success_rate': (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
    })

@app.route('/api/readability', methods=['POST'])
def analyze_readability():
    """Analizza la leggibilità di un documento"""
    try:
        # Verifica che ci sia un file
        if 'file' not in request.files:
            return jsonify({'error': 'Nessun file caricato'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nessun file selezionato'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Formato file non supportato. Usa .docx'}), 400
        
        # Salva il file temporaneamente
        filename = secure_filename(file.filename or 'document.docx')
        temp_path = app.config['UPLOAD_FOLDER'] / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file.save(str(temp_path))
        
        # Estrai il testo dal documento
        from docx import Document
        doc = Document(temp_path)
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        
        # Analizza la leggibilità
        from correttore.utils.readability import ReadabilityAnalyzer
        analyzer = ReadabilityAnalyzer()
        stats = analyzer.analyze(text)
        
        # Rimuovi il file temporaneo
        temp_path.unlink()
        
        # Restituisci i risultati
        return jsonify({
            'success': True,
            'filename': filename,
            'readability': stats
        })
        
    except Exception as e:
        # Pulisci file temporaneo in caso di errore
        if 'temp_path' in locals() and temp_path.exists():
            temp_path.unlink()
        
        return jsonify({
            'success': False,
            'error': f'Errore nell\'analisi: {str(e)}'
        }), 500

def main():
    """Avvia l'interfaccia web."""
    print("""
🌐 Correttore Web Interface
📚 Sistema enterprise-grade per correzione documenti italiani

🚀 Avvio su: http://localhost:5000
📊 Dashboard: http://localhost:5000/dashboard

Features:
- Upload documenti drag & drop
- Processamento real-time
- Monitoring integrato  
- Download risultati

💡 Modalità PRODUCTION attiva (con LanguageTool)
""")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
