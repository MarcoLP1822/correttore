#!/usr/bin/env python3
"""
Script di diagnostica per il sistema di correzione
Analizza log e suggerisce ottimizzazioni
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import statistics

class CorrectionLogAnalyzer:
    """Analizzatore dei log di correzione"""
    
    def __init__(self, log_content: str):
        self.log_content = log_content
        self.analysis_results = {}
    
    def analyze_quality_scores(self) -> Dict:
        """Analizza i punteggi di qualità dai rollback"""
        
        rollback_pattern = r"Quality score too low: ([\d.]+)% < ([\d.]+)%"
        matches = re.findall(rollback_pattern, self.log_content)
        
        if not matches:
            return {"error": "Nessun rollback trovato nel log"}
        
        scores = [float(match[0]) for match in matches]
        thresholds = [float(match[1]) for match in matches]
        
        return {
            "total_rollbacks": len(matches),
            "min_score": min(scores),
            "max_score": max(scores),
            "avg_score": statistics.mean(scores),
            "median_score": statistics.median(scores),
            "current_threshold": thresholds[0] if thresholds else None,
            "suggested_threshold": max(min(scores) - 1, 75),  # 1% sotto il minimo
            "scores_distribution": {
                "80-81%": len([s for s in scores if 80 <= s < 81]),
                "81-82%": len([s for s in scores if 81 <= s < 82]),
                "82-83%": len([s for s in scores if 82 <= s < 83]),
                "83-84%": len([s for s in scores if 83 <= s < 84]),
                "84-85%": len([s for s in scores if 84 <= s < 85]),
            }
        }
    
    def analyze_ai_failures(self) -> Dict:
        """Analizza i fallimenti del processamento AI"""
        
        failure_pattern = r"AI batch processing failed for chunk (\d+): (\d+)"
        matches = re.findall(failure_pattern, self.log_content)
        
        if not matches:
            return {"error": "Nessun fallimento AI trovato"}
        
        failed_chunks = [int(match[0]) for match in matches]
        error_codes = [int(match[1]) for match in matches]
        
        return {
            "total_failures": len(matches),
            "failed_chunks": failed_chunks[:10],  # Primi 10
            "unique_chunks": len(set(failed_chunks)),
            "error_codes": list(set(error_codes)),
            "failure_rate": len(set(failed_chunks)) / 866 * 100  # Assumendo 866 chunk totali
        }
    
    def analyze_progress(self) -> Dict:
        """Analizza il progresso della correzione"""
        
        progress_pattern = r"Correzione chunk:\s+(\d+)%\|.*?\|\s+(\d+)/(\d+)"
        matches = re.findall(progress_pattern, self.log_content)
        
        if not matches:
            return {"error": "Nessun progresso trovato"}
        
        last_match = matches[-1]
        
        return {
            "final_percentage": int(last_match[0]),
            "completed_chunks": int(last_match[1]),
            "total_chunks": int(last_match[2]),
            "completed": int(last_match[1]) == int(last_match[2])
        }
    
    def analyze_languagetool_status(self) -> Dict:
        """Analizza lo stato di LanguageTool"""
        
        lt_not_available = "LanguageTool non disponibile" in self.log_content
        lt_warnings = len(re.findall(r"LanguageTool.*?limitata", self.log_content))
        
        return {
            "available": not lt_not_available,
            "warnings_count": lt_warnings,
            "needs_installation": lt_not_available
        }
    
    def generate_recommendations(self) -> List[str]:
        """Genera raccomandazioni basate sull'analisi"""
        
        recommendations = []
        
        # Analizza qualità
        quality_analysis = self.analyze_quality_scores()
        if "suggested_threshold" in quality_analysis:
            current = quality_analysis.get("current_threshold", 85)
            suggested = quality_analysis["suggested_threshold"]
            recommendations.append(
                f"🎯 Riduci soglia qualità da {current}% a {suggested}% per ridurre rollback"
            )
        
        # Analizza LanguageTool
        lt_analysis = self.analyze_languagetool_status()
        if not lt_analysis["available"]:
            recommendations.append(
                "🔧 Installa LanguageTool: python install_languagetool.py"
            )
        
        # Analizza fallimenti AI
        ai_analysis = self.analyze_ai_failures()
        if "failure_rate" in ai_analysis and ai_analysis["failure_rate"] > 10:
            recommendations.append(
                f"⚠️  Alto tasso di fallimenti AI ({ai_analysis['failure_rate']:.1f}%) - considera di ridurre batch_size"
            )
        
        # Analizza progresso
        progress_analysis = self.analyze_progress()
        if "final_percentage" in progress_analysis and progress_analysis["final_percentage"] < 50:
            recommendations.append(
                "🔄 Processo interrotto prematuramente - verifica risorse sistema"
            )
        
        return recommendations
    
    def generate_report(self) -> str:
        """Genera report completo"""
        
        report = []
        report.append("📊 ANALISI LOG CORREZIONE")
        report.append("=" * 50)
        
        # Progresso
        progress = self.analyze_progress()
        if "error" not in progress:
            report.append(f"\n🎯 PROGRESSO:")
            report.append(f"   Completamento: {progress['final_percentage']}%")
            report.append(f"   Chunk: {progress['completed_chunks']}/{progress['total_chunks']}")
        
        # Qualità
        quality = self.analyze_quality_scores()
        if "error" not in quality:
            report.append(f"\n📈 QUALITÀ:")
            report.append(f"   Rollback totali: {quality['total_rollbacks']}")
            report.append(f"   Punteggio medio: {quality['avg_score']:.1f}%")
            report.append(f"   Soglia corrente: {quality['current_threshold']}%")
            report.append(f"   Soglia suggerita: {quality['suggested_threshold']}%")
        
        # LanguageTool
        lt_status = self.analyze_languagetool_status()
        report.append(f"\n🔧 LANGUAGETOOL:")
        report.append(f"   Disponibile: {'✅' if lt_status['available'] else '❌'}")
        
        # Fallimenti AI
        ai_failures = self.analyze_ai_failures()
        if "error" not in ai_failures:
            report.append(f"\n🤖 AI:")
            report.append(f"   Fallimenti: {ai_failures['total_failures']}")
            report.append(f"   Tasso fallimento: {ai_failures['failure_rate']:.1f}%")
        
        # Raccomandazioni
        recommendations = self.generate_recommendations()
        if recommendations:
            report.append(f"\n💡 RACCOMANDAZIONI:")
            for rec in recommendations:
                report.append(f"   {rec}")
        
        return "\n".join(report)

def analyze_log_file(log_file_path: Optional[str] = None) -> str:
    """Analizza file di log specificato o l'ultimo nel terminal"""
    
    if log_file_path and Path(log_file_path).exists():
        with open(log_file_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
    else:
        # Usa il log fornito dall'utente come esempio
        log_content = """
        # Il log verrebbe letto da file o terminal output
        """
        print("⚠️  Nessun file di log specificato, usa: python diagnose_correction.py path/to/log.txt")
        return "Nessun log da analizzare"
    
    analyzer = CorrectionLogAnalyzer(log_content)
    return analyzer.generate_report()

def suggest_optimal_config() -> Dict:
    """Suggerisce configurazione ottimale basata sui pattern comuni"""
    
    return {
        "correction": {
            "mode": "aggressive",
            "quality_threshold": 0.78,  # Ridotta per evitare rollback
            "safety_threshold": 0.75,
            "batch_size": 30,  # Ridotto per maggiore stabilità
            "max_workers": 3
        },
        "openai": {
            "model": "gpt-4o-mini",
            "temperature": 0.3,  # Più deterministica
            "max_retries": 3,
            "timeout": 45
        },
        "languagetool": {
            "timeout": 15,
            "enabled": True
        }
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
        report = analyze_log_file(log_file)
        print(report)
    else:
        print("📊 Configurazione Ottimale Suggerita:")
        print("=" * 40)
        
        config = suggest_optimal_config()
        print(json.dumps(config, indent=2))
        
        print("\n💡 Per analizzare un log specifico:")
        print("python diagnose_correction.py percorso/al/log.txt")
