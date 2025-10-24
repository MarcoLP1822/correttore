# validation.py
"""
Sistema di validazione e backup robusto per garantire l'integrità dei documenti
durante il processo di correzione. Previene perdita di contenuto, duplicazioni
e corruzione della formattazione.
"""

import hashlib
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Risultato della validazione di un documento"""
    is_valid: bool
    file_size: int
    paragraph_count: int
    character_count: int
    issues: List[str]
    checksum: str

@dataclass
class ContentIssue:
    """Rappresenta un problema rilevato nel contenuto"""
    type: str  # 'truncation', 'duplication', 'loss', 'formatting'
    severity: str  # 'critical', 'warning', 'info'
    description: str
    paragraph_id: Optional[int] = None
    original_text: Optional[str] = None
    corrected_text: Optional[str] = None

class DocumentValidator:
    """Validatore principale per documenti Word e correzioni"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
    def validate_before_processing(self, doc_path: Path) -> ValidationResult:
        """
        Valida un documento prima del processamento per assicurarsi
        che sia in uno stato consistente e processabile.
        """
        logger.info(f"🔍 Validating document: {doc_path.name}")
        
        issues = []
        
        # 1. Verifica esistenza e leggibilità file
        if not doc_path.exists():
            issues.append("File does not exist")
            return ValidationResult(False, 0, 0, 0, issues, "")
            
        if not doc_path.is_file():
            issues.append("Path is not a file")
            return ValidationResult(False, 0, 0, 0, issues, "")
            
        # 2. Verifica estensione supportata
        if doc_path.suffix.lower() not in ['.docx', '.doc', '.odt']:
            issues.append(f"Unsupported file extension: {doc_path.suffix}")
            
        # 3. Verifica dimensione file (max 100MB)
        file_size = doc_path.stat().st_size
        if file_size > 100 * 1024 * 1024:  # 100MB
            issues.append(f"File too large: {file_size / (1024*1024):.1f}MB (max 100MB)")
            
        if file_size == 0:
            issues.append("File is empty")
            return ValidationResult(False, file_size, 0, 0, issues, "")
            
        # 4. Calcola checksum per integrità
        checksum = self._calculate_checksum(doc_path)
        
        # 5. Prova ad aprire il documento per validazione strutturale
        try:
            from docx import Document
            doc = Document(str(doc_path))
            
            # Conta paragrafi e caratteri
            paragraph_count = 0
            character_count = 0
            
            from correttore.core.correttore import iter_all_paragraphs
            for para in iter_all_paragraphs(doc):
                paragraph_count += 1
                character_count += len(para.text)
                
            # Verifica minima struttura del documento
            if paragraph_count == 0:
                issues.append("Document contains no paragraphs")
                
            logger.info(f"✅ Document validation complete: {paragraph_count} paragraphs, {character_count} characters")
            
        except Exception as e:
            issues.append(f"Cannot open document: {str(e)}")
            return ValidationResult(False, file_size, 0, 0, issues, checksum)
            
        is_valid = len([i for i in issues if 'error' in i.lower() or 'cannot' in i.lower()]) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            file_size=file_size,
            paragraph_count=paragraph_count,
            character_count=character_count,
            issues=issues,
            checksum=checksum
        )
    
    def validate_paragraph_integrity(self, original: str, corrected: str) -> bool:
        """
        Valida che la correzione di un paragrafo mantenga l'integrità del contenuto.
        Controlla lunghezza, struttura e coerenza semantica di base.
        """
        if not original.strip() and not corrected.strip():
            return True  # Entrambi vuoti = OK
            
        if not original.strip():
            return bool(corrected.strip())  # Originale vuoto, corretto non vuoto = possibile
            
        if not corrected.strip():
            logger.warning("⚠️  Paragraph became empty after correction")
            return False  # Originale con contenuto, corretto vuoto = PROBLEMA
            
        # 1. Controllo lunghezza (±40% massimo consentito per correzioni semantiche)
        len_change = abs(len(corrected) - len(original)) / max(len(original), 1)
        if len_change > 0.40:  # 40% di tolleranza per correzioni semantiche
            logger.warning(f"⚠️  Large length change: {len_change:.1%}")
            return False
            
        # 2. Controllo struttura frasi (numero frasi simile)
        original_sentences = self._count_sentences(original)
        corrected_sentences = self._count_sentences(corrected)
        
        if abs(corrected_sentences - original_sentences) > max(1, original_sentences * 0.3):
            logger.warning(f"⚠️  Sentence count changed significantly: {original_sentences} → {corrected_sentences}")
            return False
            
        # 3. Controllo similarità semantica di base (usando SequenceMatcher)
        similarity = SequenceMatcher(None, original.lower(), corrected.lower()).ratio()
        if similarity < 0.3:  # 30% similarità minima - molto permissivo per correzioni semantiche
            logger.warning(f"⚠️  Very low semantic similarity: {similarity:.1%}")
            return False
            
        return True
    
    def detect_content_loss(self, before: List[str], after: List[str]) -> List[ContentIssue]:
        """
        Rileva perdite di contenuto confrontando liste di paragrafi
        prima e dopo la correzione.
        """
        issues = []
        
        # 1. Controllo numero paragrafi
        if len(after) < len(before):
            issues.append(ContentIssue(
                type='loss',
                severity='critical',
                description=f'Lost {len(before) - len(after)} paragraphs ({len(before)} → {len(after)})'
            ))
            
        elif len(after) > len(before):
            issues.append(ContentIssue(
                type='duplication',
                severity='warning',
                description=f'Added {len(after) - len(before)} paragraphs ({len(before)} → {len(after)})'
            ))
            
        # 2. Controllo contenuto totale
        before_text = '\n'.join(before)
        after_text = '\n'.join(after)
        
        before_chars = len(before_text)
        after_chars = len(after_text)
        
        if after_chars < before_chars * 0.6:  # Perdita >40% - più permissivo per correzioni semantiche
            issues.append(ContentIssue(
                type='truncation',
                severity='critical',
                description=f'Significant content loss: {before_chars} → {after_chars} chars ({(before_chars-after_chars)/before_chars:.1%})'
            ))
            
        # 3. Controllo duplicazioni specifiche
        duplicates = self._find_duplicates(after)
        for dup_text, count in duplicates.items():
            if count > 1:
                issues.append(ContentIssue(
                    type='duplication',
                    severity='warning',
                    description=f'Duplicated content found {count} times: "{dup_text[:50]}..."'
                ))
                
        # 4. Controllo frasi troncate
        truncated = self._find_truncated_sentences(after)
        for para_idx, truncated_text in truncated:
            issues.append(ContentIssue(
                type='truncation',
                severity='critical',
                description=f'Truncated sentence in paragraph {para_idx}: "{truncated_text}"',
                paragraph_id=para_idx
            ))
            
        return issues
    
    def backup_document(self, doc_path: Path) -> Path:
        """
        Crea un backup timestampato del documento prima della correzione.
        Ritorna il path del file di backup creato.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{doc_path.stem}_{timestamp}_backup{doc_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        # Crea il backup
        shutil.copy2(doc_path, backup_path)
        
        # Salva metadati del backup
        metadata = {
            "original_file": str(doc_path),
            "backup_created": timestamp,
            "original_size": doc_path.stat().st_size,
            "original_checksum": self._calculate_checksum(doc_path)
        }
        
        metadata_path = backup_path.with_suffix('.backup.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        logger.info(f"💾 Backup created: {backup_path.name}")
        return backup_path
    
    def restore_from_backup(self, backup_path: Path, target_path: Path) -> bool:
        """
        Ripristina un documento da un backup.
        """
        try:
            if not backup_path.exists():
                logger.error(f"❌ Backup file not found: {backup_path}")
                return False
                
            shutil.copy2(backup_path, target_path)
            logger.info(f"♻️  Document restored from backup: {backup_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to restore from backup: {e}")
            return False
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calcola checksum SHA-256 di un file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _count_sentences(self, text: str) -> int:
        """Conta approssimativamente il numero di frasi in un testo"""
        import re
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    def _find_duplicates(self, paragraphs: List[str]) -> Dict[str, int]:
        """Trova paragrafi duplicati"""
        from collections import Counter
        # Normalizza e conta
        normalized = [p.strip().lower() for p in paragraphs if p.strip()]
        counts = Counter(normalized)
        return {text: count for text, count in counts.items() if count > 1}
    
    def _find_truncated_sentences(self, paragraphs: List[str]) -> List[Tuple[int, str]]:
        """Trova frasi probabilmente troncate (terminano senza punteggiatura)"""
        import re
        truncated = []
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
                
            # Cerca frasi che finiscono bruscamente senza punteggiatura
            if len(para) > 20 and not re.search(r'[.!?…]$', para):
                # Ulteriore controllo: non dovrebbe essere un titolo o lista
                if not re.match(r'^(CAPITOLO|PARTE|SEZIONE|\d+\.)', para.upper()):
                    truncated.append((i, para[-50:] if len(para) > 50 else para))
                    
        return truncated


# Funzioni di utilità per integrazione facile
def validate_document(doc_path: Path) -> ValidationResult:
    """Funzione di utilità per validazione rapida"""
    validator = DocumentValidator()
    return validator.validate_before_processing(doc_path)

def create_backup(doc_path: Path) -> Path:
    """Funzione di utilità per backup rapido"""
    validator = DocumentValidator()
    return validator.backup_document(doc_path)

def validate_correction(original: str, corrected: str) -> bool:
    """Funzione di utilità per validazione correzione"""
    validator = DocumentValidator()
    return validator.validate_paragraph_integrity(original, corrected)
