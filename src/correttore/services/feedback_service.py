"""
Servizio per gestione feedback utente e apprendimento automatico (FASE 6).
Coordina feedback database, apprendimento da pattern, export custom corrections.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from correttore.utils.database import get_feedback_database, FeedbackDatabase

logger = logging.getLogger(__name__)


class FeedbackService:
    """
    Servizio coordinamento feedback utente con apprendimento automatico.
    """
    
    def __init__(self, db_path: Optional[Path] = None, min_consensus: int = 3):
        """
        Inizializza FeedbackService.
        
        Args:
            db_path: Percorso database (default: data/feedback.db)
            min_consensus: Numero minimo feedback concordanti per apprendimento (default: 3)
        """
        self.db = get_feedback_database(db_path)
        self.min_consensus = min_consensus
        
        # Path per custom corrections
        project_root = Path(__file__).parent.parent.parent.parent
        self.custom_corrections_path = project_root / "data" / "custom_corrections.txt"
        self.custom_whitelist_path = project_root / "data" / "custom_whitelist.txt"
        
        logger.info("✅ FeedbackService initialized")
    
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
        Salva feedback e triggera apprendimento automatico se necessario.
        
        Args:
            correction_id: ID univoco della correzione
            original_text: Testo originale
            feedback_type: 'corretta' o 'errore'
            corrected_text: Testo corretto
            category: Categoria correzione
            document_name: Nome documento
            rule_id: ID regola
            context: Contesto frase
            
        Returns:
            ID feedback salvato
        """
        # Salva in database
        feedback_id = self.db.save_feedback(
            correction_id=correction_id,
            original_text=original_text,
            feedback_type=feedback_type,
            corrected_text=corrected_text,
            category=category,
            document_name=document_name,
            rule_id=rule_id,
            context=context
        )
        
        # Check se triggerare apprendimento automatico
        feedback_list = self.db.get_feedback_for_correction(correction_id)
        
        if len(feedback_list) >= self.min_consensus:
            # Verifica consenso
            feedbacks = [f['feedback'] for f in feedback_list]
            corretta_count = feedbacks.count('corretta')
            errore_count = feedbacks.count('errore')
            
            # Se consenso forte (almeno 75%), apprendi
            total = len(feedbacks)
            if corretta_count / total >= 0.75:
                self._learn_as_correct(original_text, feedback_list)
                logger.info(f"🎓 Auto-learned: '{original_text}' → WHITELIST (corretta)")
            elif errore_count / total >= 0.75:
                self._learn_as_error(original_text, corrected_text, feedback_list)
                logger.info(f"🎓 Auto-learned: '{original_text}' → AUTO-CORRECT")
        
        return feedback_id
    
    def _learn_as_correct(self, original_text: str, feedback_list: List[Dict]):
        """
        Apprende una parola come corretta (whitelist).
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO learned_corrections
                (original_word, correction_type, feedback_count, confidence_score, last_updated, notes)
                VALUES (?, 'whitelist', ?, ?, ?, ?)
            """, (
                original_text.lower(),
                len(feedback_list),
                min(len(feedback_list) / 5.0, 1.0),  # Confidence score
                datetime.now().isoformat(),
                f"Auto-learned from {len(feedback_list)} 'corretta' feedbacks"
            ))
        
        # Aggiungi a whitelist file
        self._update_whitelist_file(original_text)
    
    def _learn_as_error(self, original_text: str, corrected_text: Optional[str], feedback_list: List[Dict]):
        """
        Apprende una correzione come da applicare automaticamente.
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO learned_corrections
                (original_word, correction_type, suggested_correction, feedback_count, confidence_score, last_updated, notes)
                VALUES (?, 'auto_correct', ?, ?, ?, ?, ?)
            """, (
                original_text.lower(),
                corrected_text,
                len(feedback_list),
                min(len(feedback_list) / 5.0, 1.0),
                datetime.now().isoformat(),
                f"Auto-learned from {len(feedback_list)} 'errore' feedbacks"
            ))
        
        # Aggiungi a custom corrections file
        if corrected_text:
            self._update_corrections_file(original_text, corrected_text)
    
    def _update_whitelist_file(self, word: str):
        """Aggiunge parola a custom_whitelist.txt"""
        self.custom_whitelist_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Leggi esistenti
        existing = set()
        if self.custom_whitelist_path.exists():
            existing = set(self.custom_whitelist_path.read_text(encoding='utf-8').splitlines())
        
        # Aggiungi nuova
        existing.add(word.lower())
        
        # Scrivi
        self.custom_whitelist_path.write_text(
            '\n'.join(sorted(existing)) + '\n',
            encoding='utf-8'
        )
        logger.info(f"✅ Added to whitelist: {word}")
    
    def _update_corrections_file(self, original: str, corrected: str):
        """Aggiunge correzione a custom_corrections.txt"""
        self.custom_corrections_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Formato: original -> corrected
        correction_line = f"{original.lower()} -> {corrected.lower()}"
        
        # Leggi esistenti
        existing = set()
        if self.custom_corrections_path.exists():
            existing = set(self.custom_corrections_path.read_text(encoding='utf-8').splitlines())
        
        # Aggiungi nuova
        existing.add(correction_line)
        
        # Scrivi
        self.custom_corrections_path.write_text(
            '\n'.join(sorted(existing)) + '\n',
            encoding='utf-8'
        )
        logger.info(f"✅ Added to custom corrections: {correction_line}")
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """
        Restituisce statistiche aggregate sui feedback.
        
        Returns:
            Dizionario con statistiche complete
        """
        return self.db.get_feedback_stats()
    
    def get_learned_corrections(self) -> List[Dict[str, Any]]:
        """
        Recupera tutte le correzioni apprese automaticamente.
        
        Returns:
            Lista di correzioni apprese
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM learned_corrections
                ORDER BY confidence_score DESC, feedback_count DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_corrections_by_feedback(
        self,
        feedback_type: Optional[str] = None,
        category: Optional[str] = None,
        document_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query feedback con filtri opzionali.
        
        Args:
            feedback_type: Filtra per 'corretta' o 'errore'
            category: Filtra per categoria
            document_name: Filtra per documento
            limit: Numero massimo risultati
            
        Returns:
            Lista di feedback matchanti
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Costruisci query dinamica
            query = "SELECT * FROM feedback WHERE 1=1"
            params = []
            
            if feedback_type:
                query += " AND feedback = ?"
                params.append(feedback_type)
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if document_name:
                query += " AND document_name = ?"
                params.append(document_name)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def auto_learn_from_feedback(self, force: bool = False) -> Dict[str, int]:
        """
        Processa tutti i feedback e apprende pattern con consenso.
        
        Args:
            force: Se True, forza apprendimento anche con consenso minore
            
        Returns:
            {
                'whitelist_added': int,
                'corrections_added': int,
                'total_processed': int
            }
        """
        min_feedback = 1 if force else self.min_consensus
        consensus = self.db.get_corrections_by_consensus(min_feedback=min_feedback)
        
        whitelist_added = 0
        corrections_added = 0
        
        for corr_id, data in consensus.items():
            original = data['original_text']
            consensus_type = data['consensus']
            confidence = data['confidence']
            
            # Skip se confidence troppo bassa (< 60%)
            if confidence < 0.6 and not force:
                continue
            
            feedback_list = self.db.get_feedback_for_correction(corr_id)
            
            if consensus_type == 'corretta':
                self._learn_as_correct(original, feedback_list)
                whitelist_added += 1
            elif consensus_type == 'errore':
                # Cerca la correzione più comune
                corrected_texts = [f['corrected_text'] for f in feedback_list if f['corrected_text']]
                if corrected_texts:
                    # Usa la correzione più frequente
                    most_common = max(set(corrected_texts), key=corrected_texts.count)
                    self._learn_as_error(original, most_common, feedback_list)
                    corrections_added += 1
        
        logger.info(f"🎓 Auto-learning complete: {whitelist_added} whitelist, {corrections_added} corrections")
        
        return {
            'whitelist_added': whitelist_added,
            'corrections_added': corrections_added,
            'total_processed': len(consensus)
        }
    
    def export_feedback_to_json(self, output_path: Optional[Path] = None) -> Path:
        """
        Esporta tutti i feedback in JSON.
        
        Args:
            output_path: Percorso output (default: data/feedback_export.json)
            
        Returns:
            Path del file esportato
        """
        import json
        
        if output_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            output_path = project_root / "data" / "feedback_export.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        feedback_data = self.db.export_to_json()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Feedback exported to {output_path} ({len(feedback_data)} entries)")
        
        return output_path
    
    def get_contested_corrections(self, threshold: int = 2) -> List[Dict[str, Any]]:
        """
        Trova correzioni con feedback contrastanti (sia corretta che errore).
        
        Args:
            threshold: Numero minimo feedback per lato
            
        Returns:
            Lista di correzioni contestate
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    correction_id,
                    original_text,
                    SUM(CASE WHEN feedback = 'corretta' THEN 1 ELSE 0 END) as corretta_count,
                    SUM(CASE WHEN feedback = 'errore' THEN 1 ELSE 0 END) as errore_count
                FROM feedback
                GROUP BY correction_id
                HAVING corretta_count >= ? AND errore_count >= ?
                ORDER BY (corretta_count + errore_count) DESC
            """, (threshold, threshold))
            
            contested = []
            for row in cursor.fetchall():
                contested.append({
                    'correction_id': row[0],
                    'original_text': row[1],
                    'corretta_count': row[2],
                    'errore_count': row[3],
                    'total': row[2] + row[3],
                    'split_ratio': f"{row[2]}:{row[3]}"
                })
            
            return contested


def get_feedback_service(db_path: Optional[Path] = None) -> FeedbackService:
    """
    Factory function per ottenere istanza FeedbackService singleton.
    
    Args:
        db_path: Percorso database opzionale
        
    Returns:
        FeedbackService instance
    """
    if not hasattr(get_feedback_service, '_instance'):
        get_feedback_service._instance = FeedbackService(db_path)
    return get_feedback_service._instance


# Test rapido
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n🧪 Testing FeedbackService...\n")
    
    service = get_feedback_service()
    
    # Test 1: Save feedback
    print("Test 1: Save feedback")
    for i in range(4):
        service.save_feedback(
            correction_id="test_vlta",
            original_text="vlta",
            feedback_type="errore",
            corrected_text="volta",
            category="SEMANTIC",
            document_name="test_doc.docx"
        )
    print(f"✅ Saved 4 feedback for 'vlta'\n")
    
    # Test 2: Stats
    print("Test 2: Get stats")
    stats = service.get_feedback_stats()
    print(f"   Total feedback: {stats['total']}")
    print(f"   Corretta: {stats['corretta']} ({stats['percentage_correct']:.1f}%)")
    print(f"   Errore: {stats['errore']}\n")
    
    # Test 3: Learned corrections
    print("Test 3: Learned corrections")
    learned = service.get_learned_corrections()
    for item in learned:
        print(f"   • {item['original_word']} → {item['correction_type']} (confidence: {item['confidence_score']:.1%})")
    print()
    
    # Test 4: Auto-learn
    print("Test 4: Auto-learn from feedback")
    result = service.auto_learn_from_feedback()
    print(f"   Whitelist added: {result['whitelist_added']}")
    print(f"   Corrections added: {result['corrections_added']}")
    print(f"   Total processed: {result['total_processed']}\n")
    
    # Test 5: Export
    print("Test 5: Export feedback")
    export_path = service.export_feedback_to_json()
    print(f"   Exported to: {export_path}\n")
    
    print("✅ All FeedbackService tests passed!")
