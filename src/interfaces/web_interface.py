#!/usr/bin/env python3
"""
Web Interface per il Correttore di Testi Italiani
Interfaccia web enterprise-grade per upload, processamento e monitoring

Features:
- Upload documenti via drag & drop
- Dashboard real-time processing
- Preview delif __name__ == '__main__':
    print("Correttore Web Interface")
    print("Sistema enterprise-grade per correzione documenti italiani")
    print("")
    print("Avvio su: http://localhost:5000")
    print("Dashboard: http://localhost:5000/dashboard")
    print("")
    print("Features:")
    print("- Upload documenti drag & drop")
    print("- Processamento real-time")
    print("- Monitoring integrato")
    print("- Download risultati")
    print("")
    
    # Avvio automatico LanguageTool
    print("Inizializzazione servizi...")
    
    try:
        if start_languagetool_simple():
            print("✓ LanguageTool avviato automaticamente")
            print("✓ Modalità PRODUCTION attiva (con LanguageTool)")
        else:
            print("! LanguageTool non disponibile - modalità limitata")
            print("! Alcune funzionalità potrebbero essere ridotte")
    except Exception as e:
        print(f"! Errore avvio LanguageTool: {e}")
        print("! Modalità limitata attiva")
    
    print("")
    print("Server web pronto!")
    app.run(debug=True, host='0.0.0.0', port=5000) Download risultati
- Monitoring integrato
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
import shutil
import time
import json
from pathlib import Path
from datetime import datetime
from simple_lt_starter import start_languagetool_simple, is_languagetool_running
from threading import Thread

# Import moduli correttore
from src.interfaces.cli import CorrettoreCLI, CLIOptions, CorrectionMode

app = Flask(__name__)
app.config['SECRET_KEY'] = 'correttore-enterprise-2024'
app.config['UPLOAD_FOLDER'] = Path('uploads')
app.config['OUTPUT_FOLDER'] = Path('outputs')
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
    """Processa documento in background"""
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

@app.route('/')
def index():
    """Pagina principale"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Gestisce upload documenti"""
    global job_counter
    
    print(f"DEBUG - Files in request: {list(request.files.keys())}")
    print(f"DEBUG - Form data: {dict(request.form)}")
    
    if 'file' not in request.files:
        print("DEBUG - Nessun file nella request")
        return jsonify({'error': 'Nessun file selezionato'}), 400
    
    file = request.files['file']
    print(f"DEBUG - File object: {file}")
    print(f"DEBUG - Filename: {file.filename}")
    
    if not file.filename or file.filename == '':
        print("DEBUG - Filename vuoto")
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
    
    # Opzioni da form
    selected_mode = request.form.get('mode', 'balanced')
    
    # Per modalità historical, usa parametri fissi e glossario storico
    if selected_mode == 'historical':
        quality_threshold = 0.90  # Fisso per modalità storica
        print(f"🏛️ Modalità STORICA attivata - soglia fissa al 90%")
        
        # Carica automaticamente il glossario storico
        if os.path.exists("glossario_storico.txt"):
            shutil.copy("glossario_storico.txt", "glossario.txt")
            print(f"📚 Glossario storico caricato automaticamente")
        else:
            print(f"⚠️  Glossario storico non trovato, usando quello standard")
    else:
        quality_threshold = float(request.form.get('quality_threshold', 0.85))
    
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

if __name__ == '__main__':
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

� Modalità PRODUCTION attiva (con LanguageTool)
""")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
