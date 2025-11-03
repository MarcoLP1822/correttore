"""
Benchmark startup time e memoria
"""

import time
import psutil
import os
import sys

def measure_import_time(module_name: str):
    """Misura tempo di import di un modulo"""
    start = time.time()
    __import__(module_name)
    elapsed = time.time() - start
    return elapsed

def get_memory_usage():
    """Ottieni uso memoria corrente in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB

def benchmark_startup():
    """Benchmark completo startup time"""
    
    print("=" * 60)
    print("STARTUP TIME BENCHMARK")
    print("=" * 60)
    
    # Memoria iniziale
    initial_memory = get_memory_usage()
    print(f"\n📊 Initial memory: {initial_memory:.1f} MB")
    
    # Test import principali
    modules = [
        'correttore.core.document_analyzer',
        'correttore.core.correction_engine',
        'correttore.services.languagetool_service',
        'correttore.services.special_categories_service',
        'correttore.utils.readability',
    ]
    
    print("\n🔍 Import times:")
    print("-" * 60)
    
    total_time = 0
    for module in modules:
        t = measure_import_time(module)
        total_time += t
        print(f"  {module:<50} {t*1000:>6.1f}ms")
    
    print("-" * 60)
    print(f"  {'TOTAL':<50} {total_time*1000:>6.1f}ms")
    
    # Memoria finale
    final_memory = get_memory_usage()
    memory_increase = final_memory - initial_memory
    
    print(f"\n📊 Final memory: {final_memory:.1f} MB")
    print(f"📈 Memory increase: {memory_increase:.1f} MB")
    
    # Test creazione oggetti
    print("\n" + "=" * 60)
    print("OBJECT CREATION BENCHMARK")
    print("=" * 60)
    
    from correttore.core.document_analyzer import DocumentAnalyzer
    
    # Con tutti i servizi
    print("\n🔧 With all services:")
    start = time.time()
    analyzer_full = DocumentAnalyzer(
        enable_languagetool=True,
        enable_readability=True,
        enable_special_categories=True
    )
    time_full = time.time() - start
    mem_full = get_memory_usage() - final_memory
    print(f"  Time: {time_full*1000:.1f}ms")
    print(f"  Memory: +{mem_full:.1f}MB")
    
    # Minimo (solo readability)
    print("\n⚡ Minimal (readability only):")
    start = time.time()
    analyzer_min = DocumentAnalyzer(
        enable_languagetool=False,
        enable_readability=True,
        enable_special_categories=False
    )
    time_min = time.time() - start
    mem_min = get_memory_usage() - final_memory - mem_full
    print(f"  Time: {time_min*1000:.1f}ms")
    print(f"  Memory: +{mem_min:.1f}MB")
    
    print("\n✨ Optimization potential:")
    print(f"  Time saved: {(time_full - time_min)*1000:.1f}ms ({(1-time_min/time_full)*100:.0f}%)")
    print(f"  Memory saved: {mem_full - mem_min:.1f}MB ({(1-mem_min/mem_full)*100:.0f}%)")

if __name__ == "__main__":
    benchmark_startup()
