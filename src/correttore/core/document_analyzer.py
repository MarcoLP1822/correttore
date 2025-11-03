"""
Modulo per l'analisi qualità dei documenti.

Questo modulo fornisce la classe DocumentAnalyzer che analizza documenti
per identificare problemi residui SENZA applicare correzioni.

Differenze chiave rispetto a CorrectionEngine:
- NON modifica il documento
- SOLO analisi e reporting
- Può analizzare qualsiasi documento (non solo da correggere)

Author: Sistema di Correzione Avanzato
Date: 31 Ottobre 2025
Phase: FASE 2 - Document Quality Analyzer
"""

import logging
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..models import (
    CorrectionRecord,
    CorrectionCategory,
    CorrectionSource,
    DocumentAnalysisResult,
    AnalysisConfig,
)
from ..services.languagetool_service import LanguageToolService, LanguageToolError
from ..services.special_categories_service import SpecialCategoriesService
from ..utils.readability import ReadabilityAnalyzer, SentenceReadability
from ..core.correction_collector import CorrectionCollector
from ..core.document_handler import DocumentHandler
from ..core.language_classifier import ForeignWordFilter, Language
# Import lazy di HTMLReportGenerator per evitare import circolare
# from ..utils.html_report_generator import HTMLReportGenerator

logger = logging.getLogger(__name__)


class AnalysisCache:
    """
    Cache per risultati di analisi basata su hash del file.
    Evita ri-analisi di documenti non modificati.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Inizializza cache.
        
        Args:
            max_size: Numero massimo di risultati in cache
        """
        self._cache: Dict[str, DocumentAnalysisResult] = {}
        self._max_size = max_size
        self._access_times: Dict[str, float] = {}
        logger.info(f"📦 Analysis cache initialized (max_size={max_size})")
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Calcola SHA256 hash del file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # Leggi in chunk per file grandi
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def get(self, file_path: Path) -> Optional[DocumentAnalysisResult]:
        """
        Recupera risultato dalla cache se presente e valido.
        
        Args:
            file_path: Path del documento
            
        Returns:
            DocumentAnalysisResult se in cache, None altrimenti
        """
        try:
            file_hash = self._compute_file_hash(file_path)
            
            if file_hash in self._cache:
                # Aggiorna access time
                self._access_times[file_hash] = time.time()
                logger.info(f"✅ Cache HIT for {file_path.name}")
                return self._cache[file_hash]
            
            logger.debug(f"❌ Cache MISS for {file_path.name}")
            return None
            
        except Exception as e:
            logger.warning(f"⚠️  Cache lookup failed: {e}")
            return None
    
    def put(self, file_path: Path, result: DocumentAnalysisResult) -> None:
        """
        Salva risultato in cache.
        
        Args:
            file_path: Path del documento
            result: Risultato da cachare
        """
        try:
            file_hash = self._compute_file_hash(file_path)
            
            # Evict se cache piena (LRU)
            if len(self._cache) >= self._max_size and file_hash not in self._cache:
                # Rimuovi elemento meno recentemente usato
                lru_hash = min(self._access_times.keys(), 
                              key=lambda k: self._access_times[k])
                del self._cache[lru_hash]
                del self._access_times[lru_hash]
                logger.debug(f"🗑️  Cache eviction (LRU)")
            
            self._cache[file_hash] = result
            self._access_times[file_hash] = time.time()
            logger.debug(f"💾 Cached result for {file_path.name}")
            
        except Exception as e:
            logger.warning(f"⚠️  Cache storage failed: {e}")
    
    def clear(self) -> None:
        """Svuota cache."""
        self._cache.clear()
        self._access_times.clear()
        logger.info("🗑️  Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Ritorna statistiche cache."""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "utilization": len(self._cache) / self._max_size if self._max_size > 0 else 0
        }


class DocumentAnalyzer:
    """
    Analizza documenti per identificare problemi di qualità.
    
    NON applica correzioni, solo analisi e reporting.
    
    Features:
    - Analisi grammaticale (LanguageTool)
    - Analisi leggibilità (Gulpease, parole fuori VdB)
    - Categorie speciali (lingue straniere, nomi propri, parole sensibili)
    - Generazione report HTML dedicato
    - Cache intelligente per evitare ri-analisi (FASE 9)
    
    Usage:
        analyzer = DocumentAnalyzer()
        result = analyzer.analyze_document("documento.docx")
        print(result.get_summary())
    """
    
    # Cache condivisa tra tutte le istanze
    _cache = AnalysisCache(max_size=100)
    
    def __init__(
        self,
        config: Optional[AnalysisConfig] = None,
        enable_languagetool: bool = True,
        enable_readability: bool = True,
        enable_special_categories: bool = True,
        enable_cache: bool = True
    ):
        """
        Inizializza DocumentAnalyzer con servizi configurabili.
        
        Args:
            config: Configurazione analisi (opzionale)
            enable_languagetool: Abilita analisi grammaticale
            enable_readability: Abilita analisi leggibilità
            enable_special_categories: Abilita rilevamento categorie speciali
            enable_cache: Abilita cache risultati (default: True)
        """
        # Usa config se fornita, altrimenti usa parametri individuali
        if config is not None:
            self.enable_languagetool = config.enable_languagetool
            self.enable_readability = config.enable_readability
            self.enable_special_categories = config.enable_special_categories
            self.generate_report = config.generate_report
            self.report_standalone = config.report_standalone
            self.enable_cache = getattr(config, 'enable_cache', True)
        else:
            self.enable_languagetool = enable_languagetool
            self.enable_readability = enable_readability
            self.enable_special_categories = enable_special_categories
            self.generate_report = True
            self.report_standalone = True
            self.enable_cache = enable_cache
            self.enable_special_categories = enable_special_categories
            self.generate_report = True
            self.report_standalone = True
        
        # Inizializza servizi
        self.document_handler = DocumentHandler()
        self.collector: Optional[CorrectionCollector] = None
        self.foreign_word_filter = ForeignWordFilter()
        
        # Servizi opzionali
        self.languagetool_service = None
        if self.enable_languagetool:
            try:
                self.languagetool_service = LanguageToolService()
                logger.info("✅ LanguageTool service initialized")
            except Exception as e:
                logger.warning(f"⚠️  LanguageTool not available: {e}")
                self.enable_languagetool = False
        
        self.readability_analyzer = None
        if self.enable_readability:
            try:
                self.readability_analyzer = ReadabilityAnalyzer()
                logger.info("✅ Readability analyzer initialized")
            except Exception as e:
                logger.warning(f"⚠️  Readability analyzer not available: {e}")
                self.enable_readability = False
        
        self.special_categories_service = None
        if self.enable_special_categories:
            try:
                self.special_categories_service = SpecialCategoriesService()
                logger.info("✅ Special categories service initialized")
            except Exception as e:
                logger.warning(f"⚠️  Special categories service not available: {e}")
                self.enable_special_categories = False
        
        logger.info(f"🔍 DocumentAnalyzer initialized (LT={self.enable_languagetool}, "
                   f"Read={self.enable_readability}, Special={self.enable_special_categories}, "
                   f"Cache={self.enable_cache})")
    
    def analyze_document(
        self,
        document_path: str | Path,
        output_report: bool = True,
        output_dir: Optional[Path] = None,
        use_cache: bool = True
    ) -> DocumentAnalysisResult:
        """
        Analizza un documento completo con caching intelligente.
        
        Workflow:
        1. Check cache (se abilitata)
        2. Carica documento
        3. Estrai testo completo
        4. Analisi LanguageTool (errori grammaticali/ortografici)
        5. Analisi leggibilità (Gulpease, parole fuori VdB)
        6. Analisi categorie speciali (lingue, nomi, sensibili)
        7. Genera report HTML
        8. Salva in cache
        
        Args:
            document_path: Path del documento da analizzare
            output_report: Se True, genera report HTML
            output_dir: Directory di output per i report (opzionale)
            use_cache: Se True, usa cache (default: True)
            output_dir: Directory di output per i report (opzionale)
        
        Returns:
            DocumentAnalysisResult con tutti i dati raccolti
        """
        start_time = time.time()
        document_path = Path(document_path)
        
        # Salva output_dir per usarlo in _generate_analysis_report
        self._output_dir = output_dir
        
        # Check cache prima di analizzare
        if self.enable_cache and use_cache:
            cached_result = self._cache.get(document_path)
            if cached_result is not None:
                # Rigenera report se richiesto con nuovo output_dir
                if output_report:
                    # Salva temporaneamente per _generate_analysis_report
                    old_output_dir = self._output_dir
                    self._output_dir = output_dir
                    cached_result.report_path = self._generate_analysis_report(document_path)
                    self._output_dir = old_output_dir
                    
                logger.info(f"⚡ Analysis completed from cache in {time.time() - start_time:.2f}s")
                return cached_result
        
        logger.info(f"🔍 Starting fresh analysis: {document_path.name}")
        
        try:
            # 1. Carica documento
            logger.info("📁 Loading document...")
            document, doc_info = self.document_handler.load_document(
                document_path,
                create_backup_copy=False  # Non serve backup per sola analisi
            )
            
            # 2. Estrai testo completo
            logger.info("📝 Extracting text...")
            full_text = self._extract_full_text(document)
            
            if not full_text.strip():
                logger.warning("⚠️  Document is empty!")
                return DocumentAnalysisResult(
                    success=False,
                    document_path=document_path,
                    analysis_timestamp=datetime.now(),
                    error_message="Document is empty"
                )
            
            # ⏱️ Profiling: Extraction complete
            t1 = time.time()
            logger.info(f"⏱️  [PROFILING] Document extraction: {t1-start_time:.2f}s")
            
            # 3. Analisi grammaticale
            grammar_errors = []
            if self.enable_languagetool and self.languagetool_service:
                logger.info("🔍 Running grammar analysis...")
                logger.info(f"   Text preview (first 200 chars): {full_text[:200]}")
                logger.info(f"   Text length: {len(full_text)} chars")
                logger.info(f"   Newlines in text: {full_text.count(chr(10))}")
                grammar_errors = self._analyze_grammar(full_text)
                logger.info(f"   Found {len(grammar_errors)} potential issues")
            
            # ⏱️ Profiling: Grammar complete
            t2 = time.time()
            logger.info(f"⏱️  [PROFILING] Grammar analysis: {t2-t1:.2f}s ({len(grammar_errors)} errors)")
            
            # 4. Analisi leggibilità
            readability_data = {}
            if self.enable_readability and self.readability_analyzer:
                logger.info("📊 Running readability analysis...")
                readability_data = self._analyze_readability(full_text)
                logger.info(f"   Gulpease score: {readability_data.get('gulpease_score', 0):.1f}")
            
            # ⏱️ Profiling: Readability complete
            t3 = time.time()
            logger.info(f"⏱️  [PROFILING] Readability analysis: {t3-t2:.2f}s")
            
            # 5. Analisi categorie speciali
            special_categories = {}
            if self.enable_special_categories and self.special_categories_service:
                logger.info("🌐 Running special categories analysis...")
                special_categories = self._analyze_special_categories(document)
                total_special = sum(len(v) for v in special_categories.values())
                logger.info(f"   Found {total_special} special category items")
            
            # ⏱️ Profiling: Special categories complete
            t4 = time.time()
            logger.info(f"⏱️  [PROFILING] Special categories: {t4-t3:.2f}s")
            
            # 6. Popola collector per report
            self.collector = CorrectionCollector()
            self.collector.start_tracking()
            
            logger.info(f"🔧 About to call _populate_collector with {len(grammar_errors)} grammar_errors")
            try:
                self._populate_collector(grammar_errors, special_categories)
            except Exception as e:
                logger.error(f"❌ Error in _populate_collector: {e}", exc_info=True)
            
            self.collector.stop_tracking()
            
            # DEBUG: Verifica cosa c'è nel collector
            all_corrections = self.collector.get_all_corrections()
            logger.info(f"📦 Collector populated: {len(all_corrections)} total corrections")
            if all_corrections:
                by_category = {}
                for corr in all_corrections:
                    cat_name = corr.category.value
                    by_category[cat_name] = by_category.get(cat_name, 0) + 1
                logger.info(f"   By category: {by_category}")
            
            # ⏱️ Profiling: Collector population complete
            t5 = time.time()
            logger.info(f"⏱️  [PROFILING] Collector population: {t5-t4:.2f}s")
            
            # 7. Genera report HTML
            report_path = None
            if output_report and self.generate_report:
                logger.info("📄 Generating analysis report...")
                report_path = self._generate_analysis_report(document_path, readability_data)
                logger.info(f"   Report saved: {report_path}")
            
            # ⏱️ Profiling: Report generation complete
            t6 = time.time()
            logger.info(f"⏱️  [PROFILING] Report generation: {t6-t5:.2f}s")
            
            # 8. Costruisci risultato
            processing_time = time.time() - start_time
            
            # ⏱️ Profiling: Summary
            logger.info(f"⏱️  [PROFILING] ═══════════════════════════════")
            logger.info(f"⏱️  [PROFILING] TOTAL TIME: {processing_time:.2f}s")
            logger.info(f"⏱️  [PROFILING] Breakdown:")
            logger.info(f"⏱️  [PROFILING]   - Extraction: {t1-start_time:.2f}s ({(t1-start_time)/processing_time*100:.1f}%)")
            logger.info(f"⏱️  [PROFILING]   - Grammar: {t2-t1:.2f}s ({(t2-t1)/processing_time*100:.1f}%)")
            logger.info(f"⏱️  [PROFILING]   - Readability: {t3-t2:.2f}s ({(t3-t2)/processing_time*100:.1f}%)")
            logger.info(f"⏱️  [PROFILING]   - Categories: {t4-t3:.2f}s ({(t4-t3)/processing_time*100:.1f}%)")
            logger.info(f"⏱️  [PROFILING]   - Collector: {t5-t4:.2f}s ({(t5-t4)/processing_time*100:.1f}%)")
            logger.info(f"⏱️  [PROFILING]   - Report: {t6-t5:.2f}s ({(t6-t5)/processing_time*100:.1f}%)")
            logger.info(f"⏱️  [PROFILING] ═══════════════════════════════")
            
            result = DocumentAnalysisResult(
                success=True,
                document_path=document_path,
                analysis_timestamp=datetime.now(),
                total_errors=len(grammar_errors),
                errors_by_category=self._count_by_category(grammar_errors),
                readability_score=readability_data.get('gulpease_score', 0.0),
                readability_level=readability_data.get('difficulty_level', 'unknown'),
                sentences_analysis=readability_data.get('sentences_analysis', []),
                foreign_words=special_categories.get('foreign_words', []),
                proper_nouns=special_categories.get('proper_nouns', []),
                sensitive_words=special_categories.get('sensitive_words', []),
                total_words=len(full_text.split()),
                total_paragraphs=doc_info.total_paragraphs,
                processing_time=processing_time,
                report_path=report_path
            )
            
            logger.info(f"✅ Analysis complete in {processing_time:.2f}s")
            
            # Salva in cache
            if self.enable_cache and use_cache:
                self._cache.put(document_path, result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}", exc_info=True)
            return DocumentAnalysisResult(
                success=False,
                document_path=document_path,
                analysis_timestamp=datetime.now(),
                processing_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analizza un frammento di testo senza generare report.
        
        Utile per analisi veloci o integrazioni API.
        
        Args:
            text: Testo da analizzare
        
        Returns:
            Dizionario con risultati analisi
        """
        results = {}
        
        # Analisi grammaticale
        if self.enable_languagetool and self.languagetool_service:
            grammar_errors = self._analyze_grammar(text)
            results['grammar_errors'] = len(grammar_errors)
            results['grammar_details'] = [
                {
                    'message': err.message,
                    'offset': err.offset,
                    'length': err.length,
                    'replacements': err.replacements[:3]  # Prime 3 sostituzioni
                }
                for err in self.languagetool_service.check_text(text)[:10]  # Max 10 errori
            ]
        
        # Analisi leggibilità
        if self.enable_readability and self.readability_analyzer:
            readability_data = self._analyze_readability(text)
            results['readability_score'] = readability_data.get('gulpease_score', 0)
            results['readability_level'] = readability_data.get('difficulty_level', 'unknown')
            results['total_words'] = len(text.split())
        
        return results
    
    def analyze_batch(
        self,
        document_paths: List[Path],
        output_report: bool = False,
        output_dir: Optional[Path] = None,
        use_cache: bool = True,
        max_workers: int = 3
    ) -> List[DocumentAnalysisResult]:
        """
        Analizza multipli documenti in parallelo con caching.
        
        Ottimizzazioni:
        - Processing parallelo (ThreadPool)
        - Cache shared tra workers
        - Progress tracking
        
        Args:
            document_paths: Lista di path documenti
            output_report: Genera report HTML per ogni documento
            output_dir: Directory output
            use_cache: Usa cache
            max_workers: Thread paralleli (default: 3)
        
        Returns:
            Lista di DocumentAnalysisResult
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        logger.info(f"📦 Starting batch analysis: {len(document_paths)} documents")
        logger.info(f"🔧 Configuration: workers={max_workers}, cache={use_cache}")
        
        results = []
        start_time = time.time()
        
        # Progress tracking
        completed = 0
        total = len(document_paths)
        
        def analyze_single(doc_path: Path) -> DocumentAnalysisResult:
            """Worker function per analisi singola"""
            try:
                return self.analyze_document(
                    doc_path,
                    output_report=output_report,
                    output_dir=output_dir,
                    use_cache=use_cache
                )
            except Exception as e:
                logger.error(f"❌ Failed to analyze {doc_path.name}: {e}")
                return DocumentAnalysisResult(
                    success=False,
                    document_path=doc_path,
                    analysis_timestamp=datetime.now(),
                    error_message=str(e)
                )
        
        # Processing parallelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(analyze_single, path): path 
                for path in document_paths
            }
            
            # Collect results as completed
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                completed += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    status = "✅" if result.success else "❌"
                    logger.info(f"{status} [{completed}/{total}] {path.name}")
                    
                except Exception as e:
                    logger.error(f"❌ [{completed}/{total}] {path.name}: {e}")
                    results.append(DocumentAnalysisResult(
                        success=False,
                        document_path=path,
                        analysis_timestamp=datetime.now(),
                        error_message=str(e)
                    ))
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.success)
        
        logger.info(f"✅ Batch analysis complete: {successful}/{total} successful in {total_time:.2f}s")
        logger.info(f"📊 Average time per document: {total_time/total:.2f}s")
        
        # Cache stats
        if use_cache:
            stats = self.get_cache_stats()
            logger.info(f"📦 Cache stats: {stats['size']}/{stats['max_size']} ({stats['utilization']*100:.0f}%)")
        
        return results
    
    # ========================================================================
    # METODI PRIVATI - Analisi Specifiche
    # ========================================================================
    
    def _analyze_grammar(self, text: str) -> List[CorrectionRecord]:
        """
        Analizza errori grammaticali usando LanguageTool.
        Converte LanguageToolError in CorrectionRecord.
        
        Args:
            text: Testo da analizzare
        
        Returns:
            Lista di CorrectionRecord con errori trovati
        """
        if not self.languagetool_service:
            return []
        
        logger.info(f"🔍 _analyze_grammar called with text length: {len(text)}")
        logger.info(f"   First 150 chars: {text[:150]}")
        
        lt_errors = self.languagetool_service.check_text(text, use_cache=False)  # DISABILITA CACHE
        logger.info(f"🔍 _analyze_grammar: LanguageTool returned {len(lt_errors)} errors")
        records = []
        filtered_count = 0
        reclassified_count = 0
        
        for error in lt_errors:
            # Mappa categoria LanguageTool a CorrectionCategory
            category = self._map_lt_error_to_category(error)
            
            # Estrai testo originale
            original_text = text[error.offset:error.offset + error.length] if error.offset < len(text) else ""
            
            # SKIP errori con caratteri di controllo (newline, tab) che indicano parole spezzate
            if '\n' in original_text or '\r' in original_text or '\t' in original_text:
                logger.debug(f"   Skipping error with control chars: '{original_text}'")
                filtered_count += 1
                continue
            
            # SKIP errori che sono solo spazi o punteggiatura
            if not original_text.strip() or not any(c.isalnum() for c in original_text):
                logger.debug(f"   Skipping non-word error: '{original_text}'")
                filtered_count += 1
                continue
            
            # === FILTRO INTELLIGENTE PER PAROLE STRANIERE ===
            # Applica filtro solo per errori di ortografia (categoria X)
            if category == CorrectionCategory.ERRORI_RICONOSCIUTI:
                # Estrai contesto (100 chars prima e dopo)
                context_start = max(0, error.offset - 100)
                context_end = min(len(text), error.offset + error.length + 100)
                context = text[context_start:context_end]
                
                should_filter, detected_lang, reason = self.foreign_word_filter.should_filter_error(
                    word=original_text,
                    context=context,
                    rule_id=error.rule_id
                )
                
                if should_filter:
                    if reason == "proper_noun":
                        # Nomi propri -> ignora completamente
                        logger.debug(f"   🚫 Filtered proper noun: '{original_text}'")
                        filtered_count += 1
                        continue
                    elif reason == "technical_term":
                        # Termini tecnici -> ignora completamente
                        logger.debug(f"   🚫 Filtered technical term: '{original_text}'")
                        filtered_count += 1
                        continue
                    elif reason.startswith("foreign_language_"):
                        # Parola straniera -> riclassifica come LINGUE
                        lang_name = detected_lang.value if detected_lang else "unknown"
                        logger.debug(f"   🌍 Reclassified '{original_text}' as foreign ({lang_name})")
                        category = CorrectionCategory.LINGUE
                        reclassified_count += 1
                    elif reason == "truncated_word":
                        # Parola troncata (OCR error) -> ignora
                        logger.debug(f"   ✂️ Filtered truncated word: '{original_text}'")
                        filtered_count += 1
                        continue
            
            # Prima sostituzione suggerita (se disponibile)
            corrected_text = error.replacements[0] if error.replacements else None
            
            # Estrai contesto esteso (60 caratteri prima e dopo) usando offset/length corretti
            context_start = max(0, error.offset - 60)
            context_end = min(len(text), error.offset + error.length + 60)
            context = text[context_start:context_end]
            
            logger.info(f"   Creating record: {category.value} - '{original_text[:30]}'")
            
            # Crea record
            record = CorrectionRecord(
                category=category,
                source=CorrectionSource.LANGUAGETOOL,
                original_text=original_text,
                corrected_text=corrected_text,
                context=context,  # Usa il nostro contesto estratto correttamente
                message=error.message,  # Campo corretto: message, non explanation
                position=error.offset,
                paragraph_index=0,  # Non abbiamo info paragrafo in analisi testo completo
                is_applied=False,  # Solo analisi, nessuna correzione applicata
                confidence_score=self._map_severity_to_confidence(error.severity),  # Campo corretto: confidence_score
                rule_id=error.rule_id,
                suggestions=error.replacements[:5],  # Prime 5 sostituzioni
                severity=error.severity,
                additional_info={
                    'lt_category': error.category,
                    'short_message': error.short_message,
                }
            )
            records.append(record)
        
        logger.info(f"✅ _analyze_grammar: Created {len(records)} CorrectionRecords")
        logger.info(f"   📊 Filtering stats: {filtered_count} filtered, {reclassified_count} reclassified as foreign")
        logger.info(f"   📝 Final count: {len(lt_errors)} raw errors → {len(records)} valid records")
        return records
    
    def _analyze_readability(self, text: str) -> Dict[str, Any]:
        """
        Analizza leggibilità usando ReadabilityAnalyzer.
        Calcola Gulpease e identifica parole fuori VdB.
        
        Args:
            text: Testo da analizzare
        
        Returns:
            Dizionario con dati leggibilità
        """
        if not self.readability_analyzer:
            return {}
        
        # Calcolo Gulpease globale
        gulpease = self.readability_analyzer.calculate_gulpease(text)
        
        # Gestisci caso None
        if gulpease is None:
            gulpease = 0.0
        
        # Determina livello difficoltà
        difficulty_level = self._map_gulpease_to_level(gulpease)
        
        # Analisi per frase (opzionale, può essere pesante)
        sentences_analysis = []
        try:
            # Split in frasi per analisi dettagliata
            sentences = self.readability_analyzer.split_into_sentences(text)
            for idx, sentence in enumerate(sentences[:50]):  # Max 50 frasi per performance
                if not sentence.strip():
                    continue
                
                sentence_gulpease = self.readability_analyzer.calculate_gulpease(sentence)
                # Gestisci caso None
                if sentence_gulpease is None:
                    sentence_gulpease = 0.0
                
                sentence_obj = SentenceReadability(
                    text=sentence,
                    gulpease_score=sentence_gulpease,
                    difficulty_level=self._map_gulpease_to_level(sentence_gulpease),
                    word_count=self.readability_analyzer.count_words(sentence),
                    letter_count=self.readability_analyzer.count_letters(sentence),
                    sentence_index=idx
                )
                sentences_analysis.append(sentence_obj)
        except Exception as e:
            logger.warning(f"⚠️  Sentence analysis failed: {e}")
        
        return {
            'gulpease_score': gulpease,
            'difficulty_level': difficulty_level,
            'sentences_analysis': sentences_analysis,
            'total_sentences': len(sentences_analysis)
        }
    
    def _analyze_special_categories(self, document) -> Dict[str, List[CorrectionRecord]]:
        """
        Analizza categorie speciali (lingue, nomi, sensibili).
        Riutilizza SpecialCategoriesService.
        
        Args:
            document: Documento docx.Document
        
        Returns:
            Dizionario con liste di CorrectionRecord per categoria
        """
        results = {
            'foreign_words': [],
            'proper_nouns': [],
            'sensitive_words': []
        }
        
        if not self.special_categories_service:
            return results
        
        # Estrai tutti i paragrafi
        all_paragraphs = list(self.document_handler.extract_all_paragraphs(document))
        
        for idx, para in enumerate(all_paragraphs):
            text = para.text
            if not text.strip():
                continue
            
            # Parole straniere
            try:
                foreign = self.special_categories_service.detect_foreign_words(text)
                for fw in foreign:  # fw è ForeignWord object
                    record = CorrectionRecord(
                        category=CorrectionCategory.LINGUE,
                        source=CorrectionSource.SYSTEM,
                        original_text=fw.word,
                        corrected_text=None,  # Nessuna correzione, solo segnalazione
                        context=text[:100],  # Primi 100 char come contesto
                        message=f"Parola in {fw.language}",
                        position=text.find(fw.word),
                        paragraph_index=idx,
                        is_applied=False,
                        additional_info={'language': fw.language}
                    )
                    results['foreign_words'].append(record)
            except Exception as e:
                logger.debug(f"Foreign words detection failed: {e}")
            
            # Parole sensibili
            try:
                sensitive = self.special_categories_service.detect_sensitive_words(text)
                for sw in sensitive:  # sw è SensitiveWord object
                    record = CorrectionRecord(
                        category=CorrectionCategory.IMBARAZZANTI,
                        source=CorrectionSource.SYSTEM,
                        original_text=sw.word,
                        corrected_text=None,
                        context=text[:100],
                        message=f"Parola potenzialmente sensibile ({sw.category})",
                        position=text.find(sw.word),
                        paragraph_index=idx,
                        is_applied=False,
                        additional_info={'sensitive_category': sw.category}
                    )
                    results['sensitive_words'].append(record)
            except Exception as e:
                logger.debug(f"Sensitive words detection failed: {e}")
            
            # Nomi propri (via NER se disponibile)
            # TODO: Implementare quando NER sarà disponibile
            # Per ora saltiamo questa parte
        
        return results
    
    # ========================================================================
    # METODI PRIVATI - Helper e Utility
    # ========================================================================
    
    def _extract_full_text(self, document) -> str:
        """
        Estrae tutto il testo dal documento.
        
        Args:
            document: Documento docx.Document
        
        Returns:
            Testo completo del documento (con spazi invece di newline tra paragrafi)
        """
        all_paragraphs = self.document_handler.extract_all_paragraphs(document)
        # Usa spazio invece di \n per evitare che LanguageTool spezzi le parole
        # I paragrafi sono già unità logiche separate
        return " ".join(p.text for p in all_paragraphs if p.text.strip())
    
    def _populate_collector(
        self,
        grammar_errors: List[CorrectionRecord],
        special_categories: Dict[str, List[CorrectionRecord]]
    ) -> None:
        """
        Popola CorrectionCollector con tutti i risultati per report generation.
        
        Args:
            grammar_errors: Errori grammaticali
            special_categories: Dizionario con categorie speciali
        """
        # Verifica che il collector esista (non usare "if not self.collector" perché __len__ può essere 0)
        if self.collector is None:
            logger.warning("⚠️  _populate_collector: Collector is None!")
            return
        
        # Log input
        logger.info(f"📝 _populate_collector: Received {len(grammar_errors)} grammar errors")
        logger.info(f"📝 _populate_collector: Received {len(special_categories)} special category types")
        
        # Aggiungi errori grammaticali
        added_count = 0
        for error in grammar_errors:
            logger.info(f"   Adding: {error.category.value} - '{error.original_text[:30]}'")
            self.collector.add_correction(error)
            added_count += 1
        
        logger.info(f"✅ Added {added_count} grammar errors to collector")
        
        # Aggiungi categorie speciali
        for category_list in special_categories.values():
            for record in category_list:
                self.collector.add_correction(record)
    
    def _generate_analysis_report(self, document_path: Path, readability_data: Optional[Dict] = None) -> Optional[Path]:
        """
        Genera report HTML per analisi qualità.
        
        Args:
            document_path: Path del documento originale
            readability_data: Dati di leggibilità (opzionale)
        
        Returns:
            Path del report generato o None se fallito
        """
        if self.collector is None:
            logger.warning("No collector available for report generation")
            return None
        
        try:
            # Import lazy per evitare import circolare
            from ..utils.html_report_generator import HTMLReportGenerator
            
            # Determina output path
            if hasattr(self, '_output_dir') and self._output_dir:
                output_dir = Path(self._output_dir)
            else:
                output_dir = document_path.parent / "outputs"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"{document_path.stem}_analysis_{timestamp}.html"
            report_path = output_dir / report_name
            
            # Genera report MODERNO
            generator = HTMLReportGenerator()
            
            # Prepara dati di leggibilità per report moderno
            readability_info = readability_data if readability_data else {}
            
            # Usa nuovo metodo con design moderno (default: True)
            generator.generate_report(
                collector=self.collector,
                output_path=str(report_path),
                document_name=document_path.name,
                standalone=self.report_standalone,
                show_feedback_buttons=False,
                report_type='analysis',
                use_modern_ui=True  # 🎨 Abilita design moderno!
            )
            
            return report_path
            
        except Exception as e:
            logger.error(f"Failed to generate analysis report: {e}")
            return None
    
    def _map_lt_error_to_category(self, error: LanguageToolError) -> CorrectionCategory:
        """
        Mappa categoria LanguageTool a CorrectionCategory.
        
        Args:
            error: Errore LanguageTool
        
        Returns:
            CorrectionCategory appropriata
        """
        category_lower = error.category.lower()
        
        # Mapping basato su category di LanguageTool
        if 'typography' in category_lower or 'punctuation' in category_lower:
            return CorrectionCategory.PUNTEGGIATURA
        elif 'grammar' in category_lower:
            return CorrectionCategory.ERRORI_RICONOSCIUTI
        elif 'spelling' in category_lower or 'misspelling' in category_lower:
            # IMPORTANTE: Gli errori di spelling devono passare per il filtro intelligente
            return CorrectionCategory.ERRORI_RICONOSCIUTI
        elif 'style' in category_lower:
            return CorrectionCategory.MIGLIORABILI
        elif 'confused' in category_lower:
            return CorrectionCategory.SOSPETTE
        else:
            return CorrectionCategory.ERRORI_RICONOSCIUTI
    
    def _map_severity_to_confidence(self, severity: str) -> float:
        """
        Mappa severity di LanguageTool a confidence score.
        
        Args:
            severity: Livello severity ('error', 'warning', 'info')
        
        Returns:
            Confidence score (0.0-1.0)
        """
        severity_map = {
            'error': 0.95,
            'warning': 0.75,
            'info': 0.50
        }
        return severity_map.get(severity.lower(), 0.70)
    
    def _map_gulpease_to_level(self, gulpease_score: float) -> str:
        """
        Mappa punteggio Gulpease a livello di difficoltà.
        
        Args:
            gulpease_score: Punteggio Gulpease (0-100)
        
        Returns:
            Livello difficoltà ('Molto Facile', 'Facile', 'Difficile', 'Molto Difficile')
        """
        if gulpease_score >= 80:
            return "Molto Facile"
        elif gulpease_score >= 60:
            return "Facile"
        elif gulpease_score >= 40:
            return "Difficile"
        else:
            return "Molto Difficile"
    
    def _count_by_category(self, records: List[CorrectionRecord]) -> Dict[CorrectionCategory, int]:
        """
        Conta record per categoria.
        
        Args:
            records: Lista di CorrectionRecord
        
        Returns:
            Dizionario con conteggi per categoria
        """
        counts: Dict[CorrectionCategory, int] = {}
        for record in records:
            counts[record.category] = counts.get(record.category, 0) + 1
        return counts
    
    @classmethod
    def clear_cache(cls) -> None:
        """Svuota la cache condivisa."""
        cls._cache.clear()
        logger.info("🗑️  Analysis cache cleared")
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """
        Ottieni statistiche cache.
        
        Returns:
            Dict con size, max_size, utilization
        """
        return cls._cache.get_stats()
