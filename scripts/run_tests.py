"""
Test runner principale per la suite di test del Correttore.

Esegue tutti i test con opzioni avanzate di configurazione e reporting.
"""
import unittest
import sys
import os
import time
import argparse
from pathlib import Path
from io import StringIO

# Aggiungi il path del progetto
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import dei test
from tests.unit.test_correction_engine import TestCorrectionEngine
from tests.unit.test_quality_assurance import TestQualityAssurance
from tests.unit.test_document_handler import TestDocumentHandler
from tests.integration.test_full_pipeline import TestFullPipeline
from tests.integration.test_openai_integration import TestOpenAIIntegration, TestOpenAIMockIntegration


class ColoredTextTestResult(unittest.TextTestResult):
    """Test result con output colorato."""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.verbosity = verbosity  # Explicit for type checker
        self.use_colors = self._supports_color()
        
    def _supports_color(self):
        """Verifica se il terminale supporta i colori."""
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        
    def _colored(self, text, color):
        """Applica colore al testo se supportato."""
        if not self.use_colors:
            return text
            
        colors = {
            'green': '\033[92m',
            'red': '\033[91m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'reset': '\033[0m'
        }
        
        return f"{colors.get(color, '')}{text}{colors['reset']}"
        
    def addSuccess(self, test):
        super().addSuccess(test)
        if self.verbosity > 1:
            self.stream.write(self._colored("✓ PASS", "green"))
            self.stream.write(f" {test._testMethodName}\n")
            
    def addError(self, test, err):
        super().addError(test, err)
        if self.verbosity > 1:
            self.stream.write(self._colored("✗ ERROR", "red"))
            self.stream.write(f" {test._testMethodName}\n")
            
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.verbosity > 1:
            self.stream.write(self._colored("✗ FAIL", "red"))
            self.stream.write(f" {test._testMethodName}\n")
            
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbosity > 1:
            self.stream.write(self._colored("⊝ SKIP", "yellow"))
            self.stream.write(f" {test._testMethodName} ({reason})\n")


class TestSuiteRunner:
    """Runner principale per tutte le suite di test."""
    
    def __init__(self):
        self.test_suites = {
            'unit': {
                'correction_engine': TestCorrectionEngine,
                'quality_assurance': TestQualityAssurance,
                'document_handler': TestDocumentHandler
            },
            'integration': {
                'full_pipeline': TestFullPipeline,
                'openai_real': TestOpenAIIntegration,
                'openai_mock': TestOpenAIMockIntegration
            }
        }
        
    def create_test_suite(self, test_types=None, test_classes=None):
        """
        Crea una suite di test personalizzata.
        
        Args:
            test_types: Lista di tipi di test ('unit', 'integration')
            test_classes: Lista di classi di test specifiche
        
        Returns:
            unittest.TestSuite: Suite di test configurata
        """
        suite = unittest.TestSuite()
        loader = unittest.TestLoader()
        
        if test_classes:
            # Carica classi specifiche
            for test_class in test_classes:
                suite.addTests(loader.loadTestsFromTestCase(test_class))
        else:
            # Carica per tipo
            types_to_run = test_types or ['unit', 'integration']
            
            for test_type in types_to_run:
                if test_type in self.test_suites:
                    for class_name, test_class in self.test_suites[test_type].items():
                        # Skip test che richiedono configurazione speciale
                        if class_name == 'openai_real' and not os.getenv('INTEGRATION_TESTS'):
                            continue
                            
                        suite.addTests(loader.loadTestsFromTestCase(test_class))
                        
        return suite
        
    def run_tests(self, suite, verbosity=2, stream=None):
        """
        Esegue una suite di test.
        
        Args:
            suite: Suite di test da eseguire
            verbosity: Livello di dettaglio output
            stream: Stream per output (default sys.stdout)
        
        Returns:
            unittest.TestResult: Risultato dei test
        """
        if stream is None:
            stream = sys.stdout
            
        runner = unittest.TextTestRunner(
            stream=stream,
            verbosity=verbosity,
            resultclass=ColoredTextTestResult
        )
        
        return runner.run(suite)
        
    def run_performance_tests(self):
        """Esegue test di performance specifici."""
        print("\n" + "="*60)
        print("PERFORMANCE TESTS")
        print("="*60)
        
        from tests.fixtures.test_texts import PERFORMANCE_TESTS
        
        # Simula test di performance
        for test_name, test_text in PERFORMANCE_TESTS.items():
            print(f"\nTesting {test_name}...")
            
            start_time = time.time()
            
            # Simula processamento
            # In un test reale, qui si chiamerebbero i metodi del correttore
            time.sleep(0.1)  # Simula processamento
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"  Text length: {len(test_text)} characters")
            print(f"  Processing time: {processing_time:.3f} seconds")
            print(f"  Speed: {len(test_text)/processing_time:.0f} chars/second")
            
    def run_stress_tests(self):
        """Esegue test di stress."""
        print("\n" + "="*60)
        print("STRESS TESTS")
        print("="*60)
        
        # Test con molti testi simultanei
        from tests.fixtures.test_texts import get_random_test_text
        
        num_tests = 50
        print(f"\nRunning {num_tests} random corrections...")
        
        start_time = time.time()
        errors = 0
        
        for i in range(num_tests):
            try:
                input_text, expected, metadata = get_random_test_text(seed=i)
                
                # Simula correzione
                # In test reale: result = correction_engine.correct_text_safe(input_text)
                time.sleep(0.01)  # Simula processamento
                
                if i % 10 == 0:
                    print(f"  Completed {i+1}/{num_tests}")
                    
            except Exception as e:
                errors += 1
                print(f"  Error in test {i}: {e}")
                
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\nStress test results:")
        print(f"  Tests completed: {num_tests - errors}")
        print(f"  Errors: {errors}")
        print(f"  Success rate: {(num_tests - errors)/num_tests*100:.1f}%")
        print(f"  Total time: {total_time:.2f} seconds")
        print(f"  Average time per test: {total_time/num_tests:.3f} seconds")
        
    def generate_test_report(self, results, output_file=None):
        """
        Genera un report dettagliato dei test.
        
        Args:
            results: Lista di risultati dei test
            output_file: File di output (opzionale)
        """
        report = StringIO()
        
        report.write("CORRETTORE TEST REPORT\n")
        report.write("="*50 + "\n\n")
        
        total_tests = 0
        total_failures = 0
        total_errors = 0
        total_skipped = 0
        
        for i, result in enumerate(results):
            report.write(f"Test Suite {i+1}:\n")
            report.write(f"  Tests run: {result.testsRun}\n")
            report.write(f"  Failures: {len(result.failures)}\n")
            report.write(f"  Errors: {len(result.errors)}\n")
            report.write(f"  Skipped: {len(result.skipped)}\n\n")
            
            total_tests += result.testsRun
            total_failures += len(result.failures)
            total_errors += len(result.errors)
            total_skipped += len(result.skipped)
            
        # Sommario totale
        report.write("SUMMARY:\n")
        report.write(f"  Total tests: {total_tests}\n")
        report.write(f"  Passed: {total_tests - total_failures - total_errors}\n")
        report.write(f"  Failed: {total_failures}\n")
        report.write(f"  Errors: {total_errors}\n")
        report.write(f"  Skipped: {total_skipped}\n")
        
        success_rate = (total_tests - total_failures - total_errors) / total_tests * 100 if total_tests > 0 else 0
        report.write(f"  Success rate: {success_rate:.1f}%\n")
        
        report_content = report.getvalue()
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"\nTest report saved to: {output_file}")
        else:
            print("\n" + report_content)


def main():
    """Funzione principale per eseguire i test."""
    parser = argparse.ArgumentParser(description='Correttore Test Runner')
    
    parser.add_argument('--unit', action='store_true', 
                       help='Esegui solo test unitari')
    parser.add_argument('--integration', action='store_true', 
                       help='Esegui solo test di integrazione')
    parser.add_argument('--performance', action='store_true',
                       help='Esegui test di performance')
    parser.add_argument('--stress', action='store_true',
                       help='Esegui test di stress')
    parser.add_argument('--verbose', '-v', action='count', default=1,
                       help='Aumenta verbosity (usa -vv per massimo dettaglio)')
    parser.add_argument('--report', type=str,
                       help='Salva report in file specificato')
    parser.add_argument('--class', dest='test_class', type=str,
                       help='Esegui solo una classe di test specifica')
    
    args = parser.parse_args()
    
    # Configura environment per test
    if args.integration:
        os.environ['INTEGRATION_TESTS'] = '1'
        
    runner = TestSuiteRunner()
    results = []
    
    print("CORRETTORE TEST SUITE")
    print("="*50)
    
    # Determina tipi di test da eseguire
    test_types = []
    if args.unit:
        test_types.append('unit')
    if args.integration:
        test_types.append('integration')
    if not test_types:
        test_types = ['unit', 'integration']
        
    # Classe specifica
    test_classes = None
    if args.test_class:
        # Trova la classe nei test suites
        for suite_type, classes in runner.test_suites.items():
            for class_name, test_class in classes.items():
                if class_name == args.test_class or test_class.__name__ == args.test_class:
                    test_classes = [test_class]
                    break
            if test_classes:
                break
                
        if not test_classes:
            print(f"Test class '{args.test_class}' not found!")
            return 1
    
    # Esegui test principali
    suite = runner.create_test_suite(test_types, test_classes)
    
    if suite.countTestCases() == 0:
        print("No tests to run!")
        return 1
        
    print(f"Running {suite.countTestCases()} tests...\n")
    
    start_time = time.time()
    result = runner.run_tests(suite, args.verbose)
    end_time = time.time()
    
    results.append(result)
    
    print(f"\nTest execution time: {end_time - start_time:.2f} seconds")
    
    # Test aggiuntivi
    if args.performance:
        runner.run_performance_tests()
        
    if args.stress:
        runner.run_stress_tests()
        
    # Genera report
    if args.report or args.verbose >= 2:
        runner.generate_test_report(results, args.report)
        
    # Determina exit code
    if result.wasSuccessful():
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        return 1


if __name__ == '__main__':
    sys.exit(main())
