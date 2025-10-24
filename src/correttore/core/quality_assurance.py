# core/quality_assurance.py
"""
Sistema di Quality Assurance per il correttore.
Gestisce validazione qualità, metriche e controlli automatici.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from difflib import SequenceMatcher

from docx.text.paragraph import Paragraph

logger = logging.getLogger(__name__)

@dataclass
class QualityMetric:
    """Singola metrica di qualità"""
    name: str
    value: float
    weight: float
    description: str
    threshold: float = 0.85

@dataclass
class QualityReport:
    """Report completo di qualità"""
    overall_score: float
    metrics: List[QualityMetric] = field(default_factory=list)
    issues_found: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    passed: bool = False
    
    def __post_init__(self):
        self.passed = self.overall_score >= 0.85

class QualityAssurance:
    """
    Sistema di Quality Assurance per validazione completa delle correzioni.
    Integra multiple metriche per garantire alta qualità del risultato.
    """
    
    def __init__(self, quality_threshold: float = 0.85):
        self.quality_threshold = quality_threshold
        self.metrics_weights = {
            "content_preservation": 0.40,
            "grammar_improvement": 0.25,
            "style_preservation": 0.20,
            "safety_score": 0.15
        }
    
    def assess_correction(self, original: str, corrected: str, context: Dict[str, Any] = None) -> QualityReport:
        """
        Valuta la qualità di una correzione con analisi multidimensionale.
        
        Args:
            original: Testo originale
            corrected: Testo corretto
            context: Contesto aggiuntivo per valutazione
            
        Returns:
            QualityReport: Report completo della qualità
        """
        context = context or {}
        metrics = []
        issues = []
        recommendations = []
        
        # 1. Content Preservation (40% peso)
        content_score = self._assess_content_preservation(original, corrected)
        metrics.append(QualityMetric(
            name="content_preservation",
            value=content_score,
            weight=self.metrics_weights["content_preservation"],
            description="Preservazione del contenuto originale",
            threshold=0.90
        ))
        
        if content_score < 0.90:
            issues.append(f"Content preservation low: {content_score:.2f}")
            recommendations.append("Review for content loss or major changes")
        
        # 2. Grammar Improvement (25% peso)
        grammar_score = self._assess_grammar_improvement(original, corrected)
        metrics.append(QualityMetric(
            name="grammar_improvement", 
            value=grammar_score,
            weight=self.metrics_weights["grammar_improvement"],
            description="Miglioramento grammaticale",
            threshold=0.80
        ))
        
        if grammar_score < 0.80:
            issues.append(f"Grammar improvement insufficient: {grammar_score:.2f}")
            recommendations.append("Consider additional grammar checks")
        
        # 3. Style Preservation (20% peso)
        style_score = self._assess_style_preservation(original, corrected)
        metrics.append(QualityMetric(
            name="style_preservation",
            value=style_score,
            weight=self.metrics_weights["style_preservation"], 
            description="Preservazione dello stile",
            threshold=0.85
        ))
        
        if style_score < 0.85:
            issues.append(f"Style preservation compromised: {style_score:.2f}")
            recommendations.append("Verify style consistency maintained")
        
        # 4. Safety Score (15% peso)
        safety_score = self._assess_safety(original, corrected)
        metrics.append(QualityMetric(
            name="safety_score",
            value=safety_score,
            weight=self.metrics_weights["safety_score"],
            description="Sicurezza della correzione",
            threshold=0.95
        ))
        
        if safety_score < 0.95:
            issues.append(f"Safety concerns detected: {safety_score:.2f}")
            recommendations.append("Manual review recommended")
        
        # Calcolo score complessivo
        overall_score = sum(
            metric.value * metric.weight 
            for metric in metrics
        )
        
        # Aggiunta raccomandazioni generali
        if overall_score < self.quality_threshold:
            recommendations.append("Overall quality below threshold - consider rejection")
        elif overall_score > 0.95:
            recommendations.append("Excellent quality correction")
        
        return QualityReport(
            overall_score=overall_score,
            metrics=metrics,
            issues_found=issues,
            recommendations=recommendations
        )
    
    def _assess_content_preservation(self, original: str, corrected: str) -> float:
        """Valuta preservazione del contenuto"""
        if not original.strip() or not corrected.strip():
            return 0.0
        
        # 1. Similarità generale del testo
        similarity = SequenceMatcher(None, original.lower(), corrected.lower()).ratio()
        
        # 2. Preservazione lunghezza (penalità per cambi drastici)
        length_ratio = min(len(corrected), len(original)) / max(len(corrected), len(original))
        length_penalty = max(0.0, 1.0 - abs(1.0 - length_ratio) * 2)
        
        # 3. Preservazione parole chiave
        original_words = set(re.findall(r'\b\w+\b', original.lower()))
        corrected_words = set(re.findall(r'\b\w+\b', corrected.lower()))
        
        if original_words:
            word_preservation = len(original_words & corrected_words) / len(original_words)
        else:
            word_preservation = 1.0
        
        # Score combinato con pesi
        content_score = (
            similarity * 0.5 +
            length_penalty * 0.2 + 
            word_preservation * 0.3
        )
        
        return min(1.0, content_score)
    
    def _assess_grammar_improvement(self, original: str, corrected: str) -> float:
        """Valuta miglioramento grammaticale"""
        # Indicatori di miglioramento grammaticale
        improvements = 0
        total_checks = 0
        
        # 1. Correzione apostrofi
        original_apostrophes = original.count("'") + original.count("`")
        corrected_apostrophes = corrected.count("'") + corrected.count("'")
        if original_apostrophes > 0:
            total_checks += 1
            if corrected_apostrophes > original_apostrophes * 0.8:
                improvements += 1
        
        # 2. Correzione accenti (molto comune in italiano)
        accent_errors_original = len(re.findall(r'\b(e|a|i|o|u)\'', original, re.IGNORECASE))
        accent_errors_corrected = len(re.findall(r'\b(e|a|i|o|u)\'', corrected, re.IGNORECASE))
        if accent_errors_original > 0:
            total_checks += 1
            if accent_errors_corrected < accent_errors_original:
                improvements += 1
        
        # 3. Punteggiatura migliorata
        original_punct_errors = original.count(',,') + original.count('..') + original.count(' ,') + original.count(' .')
        corrected_punct_errors = corrected.count(',,') + corrected.count('..') + corrected.count(' ,') + corrected.count(' .')
        if original_punct_errors > 0:
            total_checks += 1
            if corrected_punct_errors < original_punct_errors:
                improvements += 1
        
        # 4. Controllo maiuscole inizio frase
        original_caps = len(re.findall(r'\. [a-z]', original))
        corrected_caps = len(re.findall(r'\. [a-z]', corrected))
        if original_caps > 0:
            total_checks += 1
            if corrected_caps < original_caps:
                improvements += 1
        
        # Se nessun controllo applicabile, considera neutro
        if total_checks == 0:
            return 0.85  # Score neutro
        
        improvement_ratio = improvements / total_checks
        
        # Score base più bonus per miglioramenti
        base_score = 0.7
        improvement_bonus = improvement_ratio * 0.3
        
        return min(1.0, base_score + improvement_bonus)
    
    def _assess_style_preservation(self, original: str, corrected: str) -> float:
        """Valuta preservazione dello stile"""
        if not original.strip():
            return 1.0
        
        style_scores = []
        
        # 1. Preservazione struttura frasi
        original_sentences = len(re.findall(r'[.!?]+', original))
        corrected_sentences = len(re.findall(r'[.!?]+', corrected))
        
        if original_sentences > 0:
            sentence_preservation = min(corrected_sentences, original_sentences) / max(corrected_sentences, original_sentences)
            style_scores.append(sentence_preservation)
        
        # 2. Preservazione tono (esclamazioni, domande)
        original_exclamations = original.count('!')
        corrected_exclamations = corrected.count('!')
        original_questions = original.count('?')
        corrected_questions = corrected.count('?')
        
        tone_preservation = 1.0
        if original_exclamations > 0:
            tone_preservation *= min(1.0, corrected_exclamations / original_exclamations + 0.2)
        if original_questions > 0:
            tone_preservation *= min(1.0, corrected_questions / original_questions + 0.2)
        
        style_scores.append(tone_preservation)
        
        # 3. Preservazione formattazione implicita (maiuscole, abbreviazioni)
        original_caps = sum(1 for c in original if c.isupper())
        corrected_caps = sum(1 for c in corrected if c.isupper())
        
        if original_caps > 0:
            caps_preservation = min(corrected_caps, original_caps) / max(corrected_caps, original_caps)
            style_scores.append(caps_preservation)
        
        return sum(style_scores) / len(style_scores) if style_scores else 0.85
    
    def _assess_safety(self, original: str, corrected: str) -> float:
        """Valuta sicurezza della correzione"""
        safety_checks = []
        
        # 1. No truncation (molto importante)
        if len(corrected.strip()) < len(original.strip()) * 0.5:
            safety_checks.append(0.0)  # Grave truncation
        else:
            safety_checks.append(1.0)
        
        # 2. No duplication detection
        # Cerca pattern ripetitivi sospetti
        words = corrected.split()
        duplicates = 0
        for i in range(len(words) - 2):
            if i + 2 < len(words) and words[i] == words[i + 1]:
                duplicates += 1
        
        if duplicates > len(words) * 0.1:  # Più del 10% duplicati
            safety_checks.append(0.5)
        else:
            safety_checks.append(1.0)
        
        # 3. Preservazione nomi propri
        original_names = set(re.findall(r'\b[A-Z][a-z]+\b', original))
        corrected_names = set(re.findall(r'\b[A-Z][a-z]+\b', corrected))
        
        if original_names:
            name_preservation = len(original_names & corrected_names) / len(original_names)
            safety_checks.append(name_preservation)
        else:
            safety_checks.append(1.0)
        
        # 4. No inversione senso (controllo semantico base)
        # Controllo polarità con parole chiave
        positive_words = {'bene', 'buono', 'ottimo', 'eccellente', 'perfetto', 'sì', 'giusto'}
        negative_words = {'male', 'cattivo', 'pessimo', 'terribile', 'sbagliato', 'no', 'errore'}
        
        original_positive = sum(1 for word in positive_words if word in original.lower())
        original_negative = sum(1 for word in negative_words if word in original.lower())
        corrected_positive = sum(1 for word in positive_words if word in corrected.lower())
        corrected_negative = sum(1 for word in negative_words if word in corrected.lower())
        
        # Se c'è stata inversione significativa di polarità
        if (original_positive > original_negative and corrected_negative > corrected_positive) or \
           (original_negative > original_positive and corrected_positive > corrected_negative):
            safety_checks.append(0.7)  # Possibile inversione
        else:
            safety_checks.append(1.0)
        
        return sum(safety_checks) / len(safety_checks) if safety_checks else 0.85

    def assess_document_quality(self, paragraphs: List[Paragraph], corrections_applied: int) -> QualityReport:
        """
        Valuta la qualità complessiva di un documento dopo correzione.
        
        Args:
            paragraphs: Lista dei paragrafi del documento
            corrections_applied: Numero di correzioni applicate
            
        Returns:
            QualityReport: Report della qualità del documento
        """
        metrics = []
        issues = []
        recommendations = []
        
        total_chars = sum(len(p.text) for p in paragraphs)
        total_paragraphs = len(paragraphs)
        
        # 1. Completezza del documento
        if total_paragraphs > 0 and total_chars > 0:
            completeness_score = 1.0
        else:
            completeness_score = 0.0
            issues.append("Document appears empty or corrupted")
        
        metrics.append(QualityMetric(
            name="document_completeness",
            value=completeness_score,
            weight=0.3,
            description="Completezza del documento"
        ))
        
        # 2. Densità di correzioni
        if total_chars > 0:
            correction_density = corrections_applied / (total_chars / 1000)  # Per ogni 1000 caratteri
            # Normalizza tra 0 e 1 (10 correzioni per 1000 char = score 1.0)
            density_score = min(1.0, correction_density / 10.0)
        else:
            density_score = 0.0
        
        metrics.append(QualityMetric(
            name="correction_density",
            value=density_score,
            weight=0.2,
            description="Densità delle correzioni applicate"
        ))
        
        # 3. Coerenza formattazione
        formatting_score = self._assess_document_formatting(paragraphs)
        metrics.append(QualityMetric(
            name="formatting_consistency",
            value=formatting_score,
            weight=0.25,
            description="Coerenza della formattazione"
        ))
        
        # 4. Leggibilità
        readability_score = self._assess_readability(paragraphs)
        metrics.append(QualityMetric(
            name="readability",
            value=readability_score,
            weight=0.25,
            description="Leggibilità del testo"
        ))
        
        # Score complessivo
        overall_score = sum(metric.value * metric.weight for metric in metrics)
        
        # Raccomandazioni basate sui risultati
        if overall_score < 0.7:
            recommendations.append("Document quality is low - manual review required")
        elif overall_score > 0.9:
            recommendations.append("Document quality is excellent")
        
        if corrections_applied == 0:
            recommendations.append("No corrections were applied - verify document needs processing")
        elif correction_density > 20:
            recommendations.append("High correction density - verify accuracy")
        
        return QualityReport(
            overall_score=overall_score,
            metrics=metrics,
            issues_found=issues,
            recommendations=recommendations
        )
    
    def _assess_document_formatting(self, paragraphs: List[Paragraph]) -> float:
        """Valuta coerenza della formattazione del documento"""
        if not paragraphs:
            return 0.0
        
        # Controlla coerenza degli stili
        style_counts = {}
        for para in paragraphs:
            style_name = para.style.name if para.style else "Normal"
            style_counts[style_name] = style_counts.get(style_name, 0) + 1
        
        # Penalizza troppi stili diversi (indica inconsistenza)
        num_styles = len(style_counts)
        if num_styles <= 5:
            style_score = 1.0
        elif num_styles <= 10:
            style_score = 0.8
        else:
            style_score = 0.6
        
        return style_score
    
    def _assess_readability(self, paragraphs: List[Paragraph]) -> float:
        """Valuta leggibilità del testo"""
        if not paragraphs:
            return 0.0
        
        text = " ".join(p.text for p in paragraphs if p.text.strip())
        if not text.strip():
            return 0.0
        
        # Metriche semplici di leggibilità per italiano
        words = re.findall(r'\b\w+\b', text)
        sentences = re.findall(r'[.!?]+', text)
        
        if not words or not sentences:
            return 0.5
        
        # Lunghezza media delle frasi
        avg_sentence_length = len(words) / len(sentences)
        
        # Lunghezza media delle parole
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Score basato su metriche ottimali per italiano
        # Frasi ideali: 15-20 parole, parole ideali: 4-6 caratteri
        sentence_score = 1.0 - abs(avg_sentence_length - 17.5) / 17.5
        word_score = 1.0 - abs(avg_word_length - 5.0) / 5.0
        
        readability = (sentence_score * 0.6 + word_score * 0.4)
        return max(0.0, min(1.0, readability))

def create_quality_assurance(quality_threshold: float = 0.85) -> QualityAssurance:
    """Factory function per creare QualityAssurance configurato"""
    return QualityAssurance(quality_threshold)
