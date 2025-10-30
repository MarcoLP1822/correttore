#!/usr/bin/env python3
"""
Script per analizzare la leggibilità di documenti usando l'indice Gulpease.
Può analizzare file .docx o file di testo semplice.

Uso:
    python analyze_readability.py documento.docx
    python analyze_readability.py testo.txt
    python analyze_readability.py documento.docx --export report.txt
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from docx import Document
from correttore.utils.readability import ReadabilityAnalyzer


def extract_text_from_docx(file_path: Path) -> str:
    """Estrae il testo da un file .docx"""
    try:
        doc = Document(str(file_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"❌ Errore nel leggere il file .docx: {e}")
        return ""


def extract_text_from_txt(file_path: Path) -> str:
    """Estrae il testo da un file di testo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Errore nel leggere il file di testo: {e}")
        return ""


def analyze_file(file_path: Path, export_path: Optional[Path] = None) -> None:
    """
    Analizza la leggibilità di un file.
    
    Args:
        file_path: Percorso del file da analizzare
        export_path: Percorso opzionale per esportare il report
    """
    if not file_path.exists():
        print(f"❌ File non trovato: {file_path}")
        sys.exit(1)
    
    # Determina il tipo di file ed estrae il testo
    suffix = file_path.suffix.lower()
    
    if suffix == '.docx':
        text = extract_text_from_docx(file_path)
    elif suffix in ['.txt', '.md', '.text']:
        text = extract_text_from_txt(file_path)
    else:
        print(f"❌ Formato file non supportato: {suffix}")
        print("   Formati supportati: .docx, .txt, .md")
        sys.exit(1)
    
    if not text or not text.strip():
        print("❌ Il file non contiene testo analizzabile")
        sys.exit(1)
    
    # Analizza la leggibilità
    analyzer = ReadabilityAnalyzer()
    stats = analyzer.analyze(text)
    report = analyzer.format_report(stats)
    
    # Mostra il report
    print(report)
    
    # Esporta se richiesto
    if export_path:
        try:
            from datetime import datetime
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(f"ANALISI DI LEGGIBILITÀ\n")
                f.write(f"File analizzato: {file_path.name}\n")
                f.write(f"Data modifica: {file_time}\n")
                f.write("\n")
                f.write(report)
            
            print(f"\n✅ Report esportato in: {export_path}")
        except Exception as e:
            print(f"\n❌ Errore nell'esportare il report: {e}")


def analyze_text_direct(text: str) -> None:
    """Analizza direttamente una stringa di testo."""
    analyzer = ReadabilityAnalyzer()
    stats = analyzer.analyze(text)
    report = analyzer.format_report(stats)
    print(report)


def main():
    parser = argparse.ArgumentParser(
        description='Analizza la leggibilità di documenti usando l\'indice Gulpease',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  %(prog)s documento.docx
  %(prog)s testo.txt --export report_leggibilita.txt
  %(prog)s racconto.docx -e analisi.txt

L'indice Gulpease è una formula di leggibilità tarata sulla lingua italiana.
Valori più alti indicano maggiore facilità di lettura.
        """
    )
    
    parser.add_argument(
        'file',
        type=Path,
        help='File da analizzare (.docx, .txt, .md)'
    )
    
    parser.add_argument(
        '-e', '--export',
        type=Path,
        metavar='FILE',
        help='Esporta il report in un file di testo'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Mostra informazioni dettagliate'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"📄 Analizzando: {args.file}")
        print()
    
    analyze_file(args.file, args.export)


if __name__ == "__main__":
    main()
