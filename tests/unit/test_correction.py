#!/usr/bin/env python3
"""
Test del sistema di correzione
"""

from pathlib import Path
from correttore.core.correttore import process_doc

def test_correction():
    input_file = Path('test_input.docx')
    output_file = Path('test_output.docx')
    
    print(f'🚀 Processing {input_file} -> {output_file}')
    
    if not input_file.exists():
        print(f'❌ File di input non trovato: {input_file}')
        return False
    
    try:
        process_doc(input_file, output_file)
        print(f'✅ Processing completed successfully')
        print(f'📁 Output file exists: {output_file.exists()}')
        if output_file.exists():
            print(f'📊 Output file size: {output_file.stat().st_size} bytes')
        return True
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_correction()
