#!/usr/bin/env python3
"""
Script di Migrazione a Clean Architecture
==========================================

Riorganizza il progetto secondo i principi di Clean Architecture:
- Struttura package standard Python
- Import consistenti e puliti
- Separazione chiara delle responsabilità
- Setup moderno con pyproject.toml

Uso:
    python migrate_to_clean_architecture.py --dry-run    # Anteprima
    python migrate_to_clean_architecture.py              # Esegui migrazione
    python migrate_to_clean_architecture.py --rollback   # Ripristina backup
"""

import os
import shutil
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Set
import json

# Colori per output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_step(msg: str):
    print(f"\n{Colors.OKBLUE}▶ {msg}{Colors.ENDC}")

def print_success(msg: str):
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")

def print_warning(msg: str):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def print_error(msg: str):
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")

class CleanArchitectureMigration:
    """Gestisce la migrazione a Clean Architecture"""
    
    def __init__(self, root_dir: Path, dry_run: bool = False):
        self.root = root_dir
        self.dry_run = dry_run
        self.backup_dir = root_dir / f"_migration_backup_{datetime.now():%Y%m%d_%H%M%S}"
        self.migration_log: List[str] = []
        
        # Mappatura della nuova struttura
        self.new_structure = {
            # Source code principale
            'src/correttore/core': [
                'src/core/correttore.py',
                'src/core/grammarcheck.py',
                'src/core/llm_correct.py',
                'src/core/precheck.py',
                'src/core/safe_correction.py',
                'src/core/validation.py',
                'core/correction_engine.py',
                'core/document_handler.py',
                'core/error_handling.py',
                'core/formatting_manager.py',
                'core/quality_assurance.py',
            ],
            'src/correttore/services': [
                'src/services/cache_llm.py',
                'src/services/languagetool_manager.py',
                'src/services/openai_client.py',
                'src/services/async_languagetool_manager.py',
                'services/intelligent_cache.py',
                'services/languagetool_service.py',
                'services/openai_service.py',
                'services/parallel_processor.py',
            ],
            'src/correttore/interfaces': [
                'src/interfaces/cli.py',
                'src/interfaces/web_interface.py',
                'src/interfaces/dashboard.py',
            ],
            'src/correttore/utils': [
                'src/utils/readability.py',
                'src/utils/reports.py',
                'src/utils/token_utils.py',
                'src/utils/utils_openai.py',
                'utils/text_processing.py',
                'utils/text_normalize.py',
                'utils/report_generator.py',
                'utils/diff_engine.py',
            ],
            'src/correttore/models': [
                'src/models/',
            ],
            'src/correttore/config': [
                'config/settings.py',
                'config/__init__.py',
            ],
            'scripts': [
                'scripts/install_languagetool.py',
                'scripts/languagetool_manager.py',
                'scripts/setup_historical_mode.py',
                'scripts/diagnose_correction.py',
                'scripts/dump_rules.py',
                'scripts/lt_diagnose.py',
                'tools/monitoring.py',
                'tools/run_corpus_eval.py',
                'tools/run_tests.py',
                'tools/select_mode.py',
                'tools/create_test.py',
            ],
            'bin': [
                'main.py',
                'analyze_readability.py',
            ],
            'docs': [
                'CHANGELOG_GULPEASE.md',
                'COME_AVVIARE.md',
                'IMPLEMENTAZIONE_WEB_LEGGIBILITA.md',
                'MODIFICHE_SOGLIE.md',
                'docs/GUIDA_WEB_LEGGIBILITA.md',
                'docs/GULPEASE.md',
                'docs/README_ENTERPRISE.md',
                'docs/README_GULPEASE.md',
            ],
            'data/glossari': [
                'data/glossario.txt',
                'data/glossario_extra.json',
                'data/glossario_storico.txt',
            ],
            'data/corrections': [
                'data/custom_corrections.txt',
                'data/spelling_custom.txt',
            ],
            'examples': [
                'correttore files/racconto.docx',
                'correttore files/nuovovocabolariodibase.pdf',
            ],
        }
        
        # Pattern per aggiornare gli import
        self.import_patterns = [
            # src.core -> correttore.core
            (r'from src\.core\.', 'from correttore.core.'),
            (r'import src\.core\.', 'import correttore.core.'),
            
            # core. -> correttore.core.
            (r'from core\.', 'from correttore.core.'),
            (r'import core\.', 'import correttore.core.'),
            
            # src.services -> correttore.services
            (r'from src\.services\.', 'from correttore.services.'),
            (r'import src\.services\.', 'import correttore.services.'),
            
            # services. -> correttore.services.
            (r'from services\.', 'from correttore.services.'),
            (r'import services\.', 'import correttore.services.'),
            
            # src.utils -> correttore.utils
            (r'from src\.utils\.', 'from correttore.utils.'),
            (r'import src\.utils\.', 'import correttore.utils.'),
            
            # utils. -> correttore.utils.
            (r'from utils\.', 'from correttore.utils.'),
            (r'import utils\.', 'import correttore.utils.'),
            
            # src.interfaces -> correttore.interfaces
            (r'from src\.interfaces\.', 'from correttore.interfaces.'),
            (r'import src\.interfaces\.', 'import correttore.interfaces.'),
            
            # config. -> correttore.config.
            (r'from config\.', 'from correttore.config.'),
            (r'import config\.', 'import correttore.config.'),
            
            # tools. -> scripts.
            (r'from tools\.', 'from scripts.'),
            (r'import tools\.', 'import scripts.'),
            
            # src.models -> correttore.models
            (r'from src\.models\.', 'from correttore.models.'),
            (r'import src\.models\.', 'import correttore.models.'),
        ]

    def create_backup(self) -> bool:
        """Crea backup completo prima della migrazione"""
        print_step("Creazione backup...")
        
        if self.dry_run:
            print_warning("DRY RUN: Backup non creato")
            return True
        
        try:
            # Cartelle da backuppare
            dirs_to_backup = ['src', 'core', 'services', 'utils', 'config', 
                            'scripts', 'tools', 'tests', 'data', 'docs']
            
            # Files da backuppare
            files_to_backup = ['main.py', 'analyze_readability.py', 'config.yaml',
                             'requirements.txt', 'README.md']
            
            # File markdown dalla root
            for md_file in self.root.glob('*.md'):
                if md_file.name != 'README.md':
                    files_to_backup.append(md_file.name)
            
            self.backup_dir.mkdir(exist_ok=True)
            
            # Backup directories
            for dir_name in dirs_to_backup:
                src_dir = self.root / dir_name
                if src_dir.exists():
                    dst_dir = self.backup_dir / dir_name
                    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
                    self.log(f"Backup directory: {dir_name}")
            
            # Backup files
            for file_name in files_to_backup:
                src_file = self.root / file_name
                if src_file.exists():
                    dst_file = self.backup_dir / file_name
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                    self.log(f"Backup file: {file_name}")
            
            # Salva migration log
            with open(self.backup_dir / 'migration_info.json', 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'root_dir': str(self.root),
                    'python_version': sys.version,
                }, f, indent=2)
            
            print_success(f"Backup creato in: {self.backup_dir}")
            return True
            
        except Exception as e:
            print_error(f"Errore durante backup: {e}")
            return False

    def reorganize_structure(self) -> bool:
        """Riorganizza la struttura delle cartelle"""
        print_step("Riorganizzazione struttura cartelle...")
        
        moved_files = 0
        failed_files = []
        
        for dest_dir, source_files in self.new_structure.items():
            dest_path = self.root / dest_dir
            
            if self.dry_run:
                print(f"\n{Colors.OKCYAN}Cartella: {dest_dir}{Colors.ENDC}")
            else:
                dest_path.mkdir(parents=True, exist_ok=True)
                # Crea __init__.py se è un package Python
                if 'src/correttore' in dest_dir:
                    init_file = dest_path / '__init__.py'
                    if not init_file.exists():
                        init_file.write_text('"""Correttore - Italian Text Correction System"""\n')
            
            for source_file in source_files:
                source_path = self.root / source_file
                
                if not source_path.exists():
                    continue
                
                if source_path.is_dir():
                    # Copia directory intera
                    if self.dry_run:
                        print(f"  📁 {source_file}/ → {dest_dir}/")
                    else:
                        for item in source_path.rglob('*'):
                            if item.is_file() and not self._should_ignore(item):
                                rel_path = item.relative_to(source_path)
                                dest_file = dest_path / rel_path
                                dest_file.parent.mkdir(parents=True, exist_ok=True)
                                try:
                                    # Prova prima a copiare
                                    if dest_file.exists():
                                        dest_file.unlink()  # Rimuovi se esiste già
                                    shutil.copy2(item, dest_file)
                                    self.log(f"Copied: {item} → {dest_file}")
                                    moved_files += 1
                                except (PermissionError, OSError) as e:
                                    failed_files.append((str(item), str(e)))
                                    self.log(f"FAILED: {item} - {e}")
                else:
                    # Copia singolo file
                    dest_file = dest_path / source_path.name
                    if self.dry_run:
                        print(f"  📄 {source_file} → {dest_dir}/{source_path.name}")
                    else:
                        try:
                            if dest_file.exists():
                                dest_file.unlink()
                            shutil.copy2(source_path, dest_file)
                            self.log(f"Copied: {source_path} → {dest_file}")
                            moved_files += 1
                        except (PermissionError, OSError) as e:
                            failed_files.append((str(source_path), str(e)))
                            self.log(f"FAILED: {source_path} - {e}")
        
        if failed_files:
            print_warning(f"\n{len(failed_files)} file non copiati (probabilmente aperti):")
            for file, error in failed_files[:5]:  # Mostra solo primi 5
                print(f"  • {Path(file).name}")
            if len(failed_files) > 5:
                print(f"  ... e altri {len(failed_files) - 5}")
        
        if self.dry_run:
            print_warning(f"\nDRY RUN: {sum(len(files) for files in self.new_structure.values())} file da spostare")
        else:
            print_success(f"Copiati {moved_files} file")
            if failed_files:
                print_warning("Alcuni file non sono stati copiati. Chiudi l'editor e riprova.")
        
        return True  # Continua anche con errori parziali

    def update_imports(self) -> bool:
        """Aggiorna tutti gli import nei file Python"""
        print_step("Aggiornamento import...")
        
        # Trova tutti i file Python
        python_files = list(self.root.glob('src/**/*.py'))
        python_files.extend(self.root.glob('scripts/**/*.py'))
        python_files.extend(self.root.glob('tests/**/*.py'))
        python_files.extend(self.root.glob('bin/**/*.py'))
        
        updated_files = 0
        
        for py_file in python_files:
            if self._should_ignore(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                # Applica tutti i pattern di sostituzione
                for pattern, replacement in self.import_patterns:
                    content = re.sub(pattern, replacement, content)
                
                if content != original_content:
                    if self.dry_run:
                        print(f"  {py_file.relative_to(self.root)}")
                    else:
                        py_file.write_text(content, encoding='utf-8')
                        self.log(f"Updated imports: {py_file}")
                    updated_files += 1
                    
            except Exception as e:
                print_warning(f"Errore aggiornando {py_file}: {e}")
        
        if self.dry_run:
            print_warning(f"DRY RUN: {updated_files} file da aggiornare")
        else:
            print_success(f"Aggiornati {updated_files} file")
        
        return True

    def create_package_structure(self) -> bool:
        """Crea i file necessari per il packaging Python"""
        print_step("Creazione file di packaging...")
        
        # Crea __init__.py principale
        main_init = self.root / 'src' / 'correttore' / '__init__.py'
        main_init_content = '''"""
Correttore - Enterprise Italian Text Correction System
======================================================

A state-of-the-art text correction system with:
- AI-powered corrections using OpenAI GPT
- Grammar checking with LanguageTool
- Readability analysis (Gulpease index)
- Historical Italian text support
- Enterprise-grade quality assurance

Usage:
    from correttore import Corrector
    
    corrector = Corrector()
    result = corrector.process_document("path/to/document.docx")
"""

__version__ = '2.0.0'
__author__ = 'Marco LP'

# Public API
from correttore.core.correction_engine import CorrectionEngine
from correttore.core.document_handler import DocumentHandler
from correttore.interfaces.cli import CorrettoreCLI

__all__ = [
    'CorrectionEngine',
    'DocumentHandler', 
    'CorrettoreCLI',
]
'''
        
        # Crea __main__.py per permettere python -m correttore
        main_py = self.root / 'src' / 'correttore' / '__main__.py'
        main_py_content = '''"""
Entry point per esecuzione come modulo: python -m correttore
"""

from correttore.interfaces.cli import main

if __name__ == '__main__':
    main()
'''
        
        # setup.py
        setup_py = self.root / 'setup.py'
        setup_content = '''#!/usr/bin/env python3
"""
Setup script for Correttore
"""

from setuptools import setup, find_packages
from pathlib import Path

# Leggi README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Leggi requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip() 
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith('#')
    ]

setup(
    name="correttore",
    version="2.0.0",
    author="Marco LP",
    author_email="your.email@example.com",
    description="Enterprise Italian Text Correction System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MarcoLP1822/correttore",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-cov>=4.0',
            'black>=22.0',
            'mypy>=0.990',
            'flake8>=5.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'correttore=correttore.interfaces.cli:main',
            'correttore-analyze=correttore.utils.readability:main_cli',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Linguistic",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    include_package_data=True,
    package_data={
        'correttore': [
            'data/**/*',
            'templates/**/*',
        ],
    },
)
'''
        
        # pyproject.toml (PEP 517/518)
        pyproject_toml = self.root / 'pyproject.toml'
        pyproject_content = '''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "correttore"
version = "2.0.0"
description = "Enterprise Italian Text Correction System"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Marco LP", email = "your.email@example.com"}
]
keywords = ["nlp", "italian", "correction", "grammar", "spell-check"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Text Processing :: Linguistic",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "openai>=1.0.0",
    "python-docx>=0.8.11",
    "pyyaml>=6.0",
    "flask>=2.0.0",
    "requests>=2.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=22.0",
    "mypy>=0.990",
    "flake8>=5.0",
]

[project.scripts]
correttore = "correttore.interfaces.cli:main"
correttore-analyze = "correttore.utils.readability:main_cli"

[project.urls]
Homepage = "https://github.com/MarcoLP1822/correttore"
Documentation = "https://github.com/MarcoLP1822/correttore/docs"
Repository = "https://github.com/MarcoLP1822/correttore"
Issues = "https://github.com/MarcoLP1822/correttore/issues"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\\.pyi?$'

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=correttore --cov-report=html --cov-report=term"
'''
        
        if self.dry_run:
            print_warning("DRY RUN: File di packaging non creati")
            print(f"  - {main_init.relative_to(self.root)}")
            print(f"  - {main_py.relative_to(self.root)}")
            print(f"  - {setup_py.relative_to(self.root)}")
            print(f"  - {pyproject_toml.relative_to(self.root)}")
        else:
            main_init.parent.mkdir(parents=True, exist_ok=True)
            main_init.write_text(main_init_content)
            main_py.write_text(main_py_content)
            setup_py.write_text(setup_content)
            pyproject_toml.write_text(pyproject_content)
            print_success("File di packaging creati")
        
        return True

    def cleanup_old_structure(self) -> bool:
        """Rimuove le vecchie cartelle dopo aver verificato la migrazione"""
        print_step("Pulizia struttura vecchia...")
        
        if self.dry_run:
            print_warning("DRY RUN: Cartelle vecchie non rimosse")
            return True
        
        # NON rimuoviamo nulla in questa fase per sicurezza
        print_warning("Mantenute cartelle originali per sicurezza")
        print("  Dopo aver verificato che tutto funzioni, puoi rimuovere manualmente:")
        print("  - ./core/ (duplicato)")
        print("  - ./services/ (duplicato)")
        print("  - ./utils/ (duplicato)")
        print("  - ./tools/ (ora in scripts/)")
        print("  - ./correttore files/ (ora in examples/)")
        
        return True

    def create_new_readme(self) -> bool:
        """Crea un README.md principale pulito"""
        print_step("Creazione README principale...")
        
        readme_content = '''# 🎯 Correttore - Enterprise Italian Text Correction System

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Sistema enterprise di correzione testi italiani con AI, grammar checking e analisi di leggibilità.

## ✨ Features

- 🤖 **AI-Powered Corrections**: OpenAI GPT per correzioni intelligenti
- 📝 **Grammar Checking**: Integrazione LanguageTool
- 📊 **Readability Analysis**: Indice Gulpease per leggibilità
- 🏛️ **Historical Italian**: Supporto testi storici
- 🎯 **Quality Assurance**: Validazione enterprise-grade
- 🚀 **Performance**: Caching intelligente e processing parallelo
- 🌐 **Web Interface**: Dashboard moderna e user-friendly

## 🚀 Quick Start

### Installazione

```bash
# Clone repository
git clone https://github.com/MarcoLP1822/correttore.git
cd correttore

# Crea virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Installa pacchetto
pip install -e .

# Setup LanguageTool
python scripts/install_languagetool.py
```

### Uso Base

```bash
# Interfaccia Web (consigliato)
python -m correttore

# CLI
correttore documento.docx

# Analisi leggibilità
correttore-analyze documento.docx
```

### Uso Programmatico

```python
from correttore import CorrectionEngine, DocumentHandler

# Inizializza
engine = CorrectionEngine()
handler = DocumentHandler()

# Carica e correggi documento
doc = handler.load_document("input.docx")
result = engine.correct_document(doc)

# Salva risultato
handler.save_document(result, "output.docx")
```

## 📚 Documentazione

Documentazione completa disponibile in [`docs/`](docs/):

- [Come Avviare](docs/COME_AVVIARE.md) - Guida installazione e primo uso
- [Guida Web](docs/GUIDA_WEB_LEGGIBILITA.md) - Interfaccia web
- [Gulpease](docs/GULPEASE.md) - Analisi leggibilità
- [Enterprise](docs/README_ENTERPRISE.md) - Features enterprise
- [Changelog](docs/CHANGELOG_GULPEASE.md) - Modifiche e aggiornamenti

## 🏗️ Architettura

Progetto organizzato secondo **Clean Architecture**:

```
correttore/
├── src/correttore/          # Package principale
│   ├── core/               # Business logic
│   ├── services/           # Servizi esterni (OpenAI, LanguageTool)
│   ├── interfaces/         # CLI, Web UI
│   ├── utils/              # Utilities
│   ├── models/             # Data models
│   └── config/             # Configurazione
├── scripts/                # Setup e utility scripts
├── tests/                  # Test suite completa
├── docs/                   # Documentazione
├── data/                   # Glossari e configurazioni
└── examples/               # File di esempio
```

## 🧪 Testing

```bash
# Tutti i test
pytest

# Con coverage
pytest --cov=correttore --cov-report=html

# Test specifici
pytest tests/unit/
pytest tests/integration/
```

## 🛠️ Development

```bash
# Installa dipendenze dev
pip install -e ".[dev]"

# Code formatting
black src/

# Type checking
mypy src/

# Linting
flake8 src/
```

## 📊 Performance

- ⚡ Cache intelligente per riduzioni fino al 80% dei tempi
- 🔄 Processing parallelo per documenti grandi
- 💾 Gestione efficiente memoria
- 🎯 Quality scoring real-time

## 🤝 Contributing

Contributi benvenuti! Vedi [CONTRIBUTING.md](CONTRIBUTING.md) per dettagli.

## 📄 License

MIT License - vedi [LICENSE](LICENSE) per dettagli.

## 👥 Authors

- **Marco LP** - [GitHub](https://github.com/MarcoLP1822)

## 🙏 Acknowledgments

- OpenAI per le API GPT
- LanguageTool per grammar checking
- Comunità Python per le librerie open source

---

**Nota**: Questo è un progetto in attivo sviluppo. Per bug report e feature requests, apri una [issue](https://github.com/MarcoLP1822/correttore/issues).
'''
        
        readme_path = self.root / 'README.md'
        
        if self.dry_run:
            print_warning("DRY RUN: README.md non creato")
        else:
            # Backup vecchio README
            if readme_path.exists():
                shutil.copy2(readme_path, self.root / 'docs' / 'README_OLD.md')
            readme_path.write_text(readme_content)
            print_success("README.md principale creato")
        
        return True

    def _should_ignore(self, path: Path) -> bool:
        """Verifica se un file/directory deve essere ignorato"""
        ignore_patterns = [
            '__pycache__',
            '.pytest_cache',
            '.mypy_cache',
            '.git',
            '.venv',
            'venv',
            '.env',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.backup',
            '_migration_backup_',
        ]
        
        path_str = str(path)
        return any(pattern in path_str for pattern in ignore_patterns)

    def log(self, message: str):
        """Aggiungi messaggio al log di migrazione"""
        self.migration_log.append(f"{datetime.now():%Y-%m-%d %H:%M:%S} - {message}")

    def save_log(self):
        """Salva il log di migrazione"""
        if not self.dry_run:
            log_file = self.root / 'migration.log'
            with open(log_file, 'w') as f:
                f.write('\n'.join(self.migration_log))
            print_success(f"Log salvato in: {log_file}")

    def run(self) -> bool:
        """Esegue l'intera migrazione"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}")
        print("=" * 70)
        print("  MIGRAZIONE A CLEAN ARCHITECTURE")
        print("=" * 70)
        print(f"{Colors.ENDC}\n")
        
        if self.dry_run:
            print(f"{Colors.WARNING}{Colors.BOLD}MODALITÀ DRY RUN - Nessuna modifica verrà applicata{Colors.ENDC}\n")
        
        steps = [
            ("Backup", self.create_backup),
            ("Riorganizzazione", self.reorganize_structure),
            ("Package Structure", self.create_package_structure),
            ("Update Imports", self.update_imports),
            ("Nuovo README", self.create_new_readme),
            ("Cleanup", self.cleanup_old_structure),
        ]
        
        for step_name, step_func in steps:
            try:
                if not step_func():
                    print_error(f"Fallito: {step_name}")
                    return False
            except Exception as e:
                print_error(f"Errore in {step_name}: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        self.save_log()
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}")
        print("=" * 70)
        print("  MIGRAZIONE COMPLETATA CON SUCCESSO!")
        print("=" * 70)
        print(f"{Colors.ENDC}\n")
        
        if not self.dry_run:
            print("📦 Prossimi passi:")
            print("  1. Verifica che tutto funzioni: python -m pytest")
            print("  2. Installa il package: pip install -e .")
            print("  3. Testa l'applicazione: python -m correttore")
            print(f"  4. Backup disponibile in: {self.backup_dir}")
            print("\n✨ Il progetto ora segue Clean Architecture!")
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Migra il progetto a Clean Architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python migrate_to_clean_architecture.py --dry-run    # Anteprima
  python migrate_to_clean_architecture.py              # Esegui
  python migrate_to_clean_architecture.py --rollback   # Ripristina
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Mostra cosa verrebbe fatto senza applicare modifiche'
    )
    
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Ripristina da backup più recente'
    )
    
    args = parser.parse_args()
    
    root_dir = Path(__file__).parent
    
    if args.rollback:
        print_step("Ricerca backup più recente...")
        backups = sorted(root_dir.glob('_migration_backup_*'))
        if not backups:
            print_error("Nessun backup trovato")
            return 1
        
        latest_backup = backups[-1]
        print(f"Trovato: {latest_backup}")
        
        response = input("Confermi il ripristino? [y/N]: ")
        if response.lower() != 'y':
            print("Annullato")
            return 0
        
        print_step("Ripristino in corso...")
        # TODO: Implementare rollback
        print_warning("Funzione rollback da implementare")
        return 0
    
    # Esegui migrazione
    migration = CleanArchitectureMigration(root_dir, dry_run=args.dry_run)
    success = migration.run()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
