"""
Database utility per il sistema di feedback (FASE 6).
Gestisce SQLite database per memorizzare feedback utente sulle correzioni.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class FeedbackDatabase:
    """Gestione database SQLite per feedback correzioni"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Inizializza il database feedback.
        
        Args:
            db_path: Percorso database (default: data/feedback.db)
        """
        if db_path is None:
            # Default: data/feedback.db nella root del progetto
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = project_root / "data" / "feedback.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inizializza database
        self._init_database()
        logger.info(f"✅ FeedbackDatabase initialized: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager per connessioni database"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Accesso a colonne per nome
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Crea tabelle database se non esistono"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabella principale feedback
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    correction_id TEXT NOT NULL,
                    original_text TEXT NOT NULL,
                    corrected_text TEXT,
                    category TEXT,
                    feedback TEXT NOT NULL CHECK(feedback IN ('corretta', 'errore')),
                    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    document_name TEXT,
                    rule_id TEXT,
                    context TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Indici per performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_correction_id 
                ON feedback(correction_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_type 
                ON feedback(feedback)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON feedback(timestamp)
            """)
            
            # Tabella learned_corrections (apprendimento automatico)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learned_corrections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_word TEXT NOT NULL UNIQUE,
                    correction_type TEXT NOT NULL CHECK(correction_type IN ('whitelist', 'blacklist', 'auto_correct')),
                    suggested_correction TEXT,
                    confidence_score REAL DEFAULT 0.0,
                    feedback_count INTEGER DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_original_word 
                ON learned_corrections(original_word)
            """)
            
            logger.info("✅ Database tables initialized")
    
    def save_feedback(
        self,
        correction_id: str,
        original_text: str,
        feedback_type: str,
        corrected_text: Optional[str] = None,
        category: Optional[str] = None,
        document_name: Optional[str] = None,
        rule_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> int:
        """
        Salva feedback utente su una correzione.
        
        Args:
            correction_id: ID univoco della correzione
            original_text: Testo originale
            feedback_type: 'corretta' o 'errore'
            corrected_text: Testo corretto (opzionale)
            category: Categoria correzione
            document_name: Nome documento
            rule_id: ID regola LanguageTool/GPT
            context: Contesto frase
            
        Returns:
            ID del feedback salvato
        """
        if feedback_type not in ['corretta', 'errore']:
            raise ValueError(f"feedback_type deve essere 'corretta' o 'errore', ricevuto: {feedback_type}")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedback 
                (correction_id, original_text, corrected_text, category, feedback, 
                 document_name, rule_id, context, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                correction_id,
                original_text,
                corrected_text,
                category,
                feedback_type,
                document_name,
                rule_id,
                context,
                datetime.now().isoformat()
            ))
            
            feedback_id = cursor.lastrowid
            if feedback_id is None:
                raise ValueError("Failed to insert feedback")
            
            logger.info(f"✅ Feedback saved: {feedback_id} - {correction_id} = {feedback_type}")
            
            return feedback_id
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """
        Restituisce statistiche generali sui feedback.
        
        Returns:
            {
                'total': int,
                'corretta': int,
                'errore': int,
                'by_category': {...},
                'by_document': {...},
                'recent': [...]
            }
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Totali
            cursor.execute("SELECT COUNT(*) FROM feedback")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback = 'corretta'")
            corretta = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback = 'errore'")
            errore = cursor.fetchone()[0]
            
            # By category
            cursor.execute("""
                SELECT category, feedback, COUNT(*) as count
                FROM feedback
                WHERE category IS NOT NULL
                GROUP BY category, feedback
            """)
            by_category = {}
            for row in cursor.fetchall():
                cat = row[0]
                if cat not in by_category:
                    by_category[cat] = {'corretta': 0, 'errore': 0}
                by_category[cat][row[1]] = row[2]
            
            # By document
            cursor.execute("""
                SELECT document_name, feedback, COUNT(*) as count
                FROM feedback
                WHERE document_name IS NOT NULL
                GROUP BY document_name, feedback
            """)
            by_document = {}
            for row in cursor.fetchall():
                doc = row[0]
                if doc not in by_document:
                    by_document[doc] = {'corretta': 0, 'errore': 0}
                by_document[doc][row[1]] = row[2]
            
            # Recent 10
            cursor.execute("""
                SELECT id, correction_id, original_text, feedback, timestamp
                FROM feedback
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            recent = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total': total,
                'corretta': corretta,
                'errore': errore,
                'percentage_correct': (corretta / total * 100) if total > 0 else 0,
                'by_category': by_category,
                'by_document': by_document,
                'recent': recent
            }
    
    def get_feedback_for_correction(self, correction_id: str) -> List[Dict[str, Any]]:
        """
        Recupera tutti i feedback per una specifica correzione.
        
        Args:
            correction_id: ID della correzione
            
        Returns:
            Lista di feedback
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM feedback
                WHERE correction_id = ?
                ORDER BY timestamp DESC
            """, (correction_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_corrections_by_consensus(self, min_feedback: int = 3) -> Dict[str, Dict[str, Any]]:
        """
        Trova correzioni con consenso forte (3+ feedback concordanti).
        
        Args:
            min_feedback: Numero minimo feedback richiesti
            
        Returns:
            {
                correction_id: {
                    'original_text': str,
                    'consensus': 'corretta' | 'errore',
                    'count': int,
                    'confidence': float
                }
            }
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    correction_id,
                    original_text,
                    feedback,
                    COUNT(*) as count
                FROM feedback
                GROUP BY correction_id, feedback
                HAVING COUNT(*) >= ?
                ORDER BY count DESC
            """, (min_feedback,))
            
            corrections = {}
            for row in cursor.fetchall():
                corr_id = row[0]
                if corr_id not in corrections:
                    corrections[corr_id] = {
                        'original_text': row[1],
                        'consensus': row[2],
                        'count': row[3],
                        'confidence': min(row[3] / 5.0, 1.0)  # Max 5 feedback = 100%
                    }
            
            return corrections
    
    def clear_all_feedback(self):
        """Elimina tutti i feedback (con precauzione)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM feedback")
            cursor.execute("DELETE FROM learned_corrections")
            logger.warning("⚠️  All feedback cleared from database")
    
    def export_to_json(self) -> List[Dict[str, Any]]:
        """Esporta tutti i feedback in formato JSON"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM feedback ORDER BY timestamp DESC")
            return [dict(row) for row in cursor.fetchall()]


def get_feedback_database(db_path: Optional[Path] = None) -> FeedbackDatabase:
    """
    Factory function per ottenere istanza FeedbackDatabase singleton.
    
    Args:
        db_path: Percorso database opzionale
        
    Returns:
        FeedbackDatabase instance
    """
    if not hasattr(get_feedback_database, '_instance'):
        get_feedback_database._instance = FeedbackDatabase(db_path)
    return get_feedback_database._instance


# Test rapido
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n🧪 Testing FeedbackDatabase...\n")
    
    db = get_feedback_database()
    
    # Test save
    feedback_id = db.save_feedback(
        correction_id="test_001",
        original_text="pò",
        feedback_type="errore",
        corrected_text="po'",
        category="APOSTROPHE",
        document_name="test_doc.docx"
    )
    print(f"✅ Feedback saved with ID: {feedback_id}")
    
    # Test stats
    stats = db.get_feedback_stats()
    print(f"\n📊 Stats:")
    print(f"   Total: {stats['total']}")
    print(f"   Corretta: {stats['corretta']}")
    print(f"   Errore: {stats['errore']}")
    
    # Test consensus
    consensus = db.get_corrections_by_consensus(min_feedback=1)
    print(f"\n🎯 Corrections with consensus:")
    for corr_id, data in consensus.items():
        print(f"   {corr_id}: {data['consensus']} ({data['count']} votes, {data['confidence']:.1%} confidence)")
    
    print("\n✅ All tests passed!")
